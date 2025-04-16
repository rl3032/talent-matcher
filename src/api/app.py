"""
Talent Matcher API
This module provides API endpoints for the talent matching system.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from src.knowledge_graph.model import KnowledgeGraph
from src.knowledge_graph.matcher import KnowledgeGraphMatcher
from src.etl.data_loader import initialize_knowledge_graph
import os
import json
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import math
import datetime
import uuid
from src.config import API_PORT

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure JWT
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "default-dev-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=24)
jwt = JWTManager(app)

# Initialize knowledge graph
kg = None
matcher = None

# User class to store user information
class User:
    def __init__(self, email, password_hash, name, role, profile_id=None):
        self.email = email
        self.password_hash = password_hash
        self.name = name
        self.role = role  # 'hiring_manager' or 'candidate'
        self.profile_id = profile_id  # job_id for hiring manager, resume_id for candidate

    def to_dict(self):
        return {
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'profile_id': self.profile_id
        }
        
    @classmethod
    def find_by_email(cls, email):
        """Find a user by email in the database."""
        with kg.driver.session() as session:
            result = session.run("""
                MATCH (u:User {email: $email})
                RETURN u.email as email, u.password_hash as password_hash, 
                       u.name as name, u.role as role, u.profile_id as profile_id
            """, {"email": email})
            
            record = result.single()
            if record:
                return cls(
                    email=record["email"],
                    password_hash=record["password_hash"],
                    name=record["name"],
                    role=record["role"],
                    profile_id=record["profile_id"]
                )
            return None
    
    @classmethod
    def create(cls, email, password_hash, name, role, profile_id=None):
        """Create a new user in the database."""
        with kg.driver.session() as session:
            session.run("""
                CREATE (u:User {
                    email: $email,
                    password_hash: $password_hash,
                    name: $name,
                    role: $role,
                    profile_id: $profile_id,
                    created_at: datetime()
                })
            """, {
                "email": email,
                "password_hash": password_hash,
                "name": name,
                "role": role,
                "profile_id": profile_id
            })
            
            return cls(email, password_hash, name, role, profile_id)
    
    def update_profile_id(self, profile_id):
        """Update the user's profile_id in the database."""
        with kg.driver.session() as session:
            session.run("""
                MATCH (u:User {email: $email})
                SET u.profile_id = $profile_id
            """, {"email": self.email, "profile_id": profile_id})
            
            self.profile_id = profile_id

# User loader callback for Flask-JWT-Extended
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.find_by_email(identity)

# Helper function to format match results
def format_match_results(matches):
    """Format match results for frontend display with consistent scoring and skill data."""
    
    for match in matches:
        # SIMPLIFIED APPROACH: Recalculate the match percentage directly from components
        # This avoids any issues with existing corrupted values
        try:
            # If we have the component scores, recalculate the percentage
            skill_score = float(match.get('skillScore', 0)) 
            location_score = float(match.get('locationScore', 0))
            semantic_score = float(match.get('semanticScore', 0))
            
            # Use the same weights from the model
            weights = {
                "skills": 0.75,
                "location": 0.15,
                "semantic": 0.1
            }
            
            # Calculate total score
            total_score = (
                skill_score * weights["skills"] + 
                location_score * weights["location"] + 
                semantic_score * weights["semantic"]
            )
            
            # Normalize the score to a better range (40-95)
            # This assumes most scores currently fall in the 10-75 range
            raw_match = min(round(total_score), 100)
            
            # Apply normalization from observed range (10-75) to desired range (40-95)
            if raw_match <= 10:
                match_percentage = 40  # Minimum normalized score
            elif raw_match >= 75:
                match_percentage = 95  # Maximum normalized score
            else:
                # Linear scaling from (10-75) to (40-95)
                match_percentage = 40 + (raw_match - 10) * (95 - 40) / (75 - 10)
                
            match['match_percentage'] = int(round(match_percentage))
            match['totalScore'] = total_score
            
        except Exception as e:
            # If any error occurs, default to 0
            match['match_percentage'] = 0
            match['totalScore'] = 0
        
        # Set graph_percentage and text_percentage to the same value
        match['graph_percentage'] = match['match_percentage']
        match['text_percentage'] = match['match_percentage']
        
        # Format matching skills for frontend display
        if 'primary_matching_skills' in match:
            # Only use primary_matching_skills for matching_skills
            match['matching_skills'] = [s for s in match['primary_matching_skills'] if s.get('skill_id') is not None]
            
        # Keep secondary_matching_skills separate for the frontend
        if 'secondary_matching_skills' in match:
            # Filter out null skills
            match['secondary_matching_skills'] = [s for s in match['secondary_matching_skills'] 
                                                if s.get('skill_id') is not None]
            
            # Remove duplicate skills that are already in primary
            if 'matching_skills' in match:
                primary_skill_ids = {s.get('skill_id') for s in match.get('matching_skills', [])}
                match['secondary_matching_skills'] = [s for s in match['secondary_matching_skills'] 
                                                     if s.get('skill_id') not in primary_skill_ids]
        
        # Add placeholder values for frontend compatibility
        if 'matching_skills' not in match:
            match['matching_skills'] = []
        if 'secondary_matching_skills' not in match:
            match['secondary_matching_skills'] = []
        match['missing_skills'] = []
        
        # Round scores for display
        for score_field in ['skillScore', 'locationScore', 'semanticScore', 'totalScore']:
            if score_field in match:
                try:
                    match[score_field] = round(float(match[score_field]), 1)
                except (ValueError, TypeError):
                    match[score_field] = 0.0
                
        # Remove raw skills arrays to clean up response
        if 'primary_matching_skills' in match:
            del match['primary_matching_skills']
        # Keep secondary_matching_skills for the frontend to process
    
    return matches

# Initialize function
def init_app():
    """Initialize the knowledge graph."""
    global kg, matcher
    if kg is None:  # Only initialize if not already initialized
        kg = initialize_knowledge_graph()
        matcher = KnowledgeGraphMatcher(kg)
    return kg, matcher

# Initialize on import
init_app()

# Authentication routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.json
    
    # Validate required fields
    required_fields = ['email', 'password', 'name', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    email = data['email']
    password = data['password']
    name = data['name']
    role = data['role']
    
    # Validate role
    if role not in ['hiring_manager', 'candidate']:
        return jsonify({"error": "Invalid role"}), 400
    
    # Check if user already exists
    if User.find_by_email(email):
        return jsonify({"error": "User already exists"}), 409
    
    # Create new user
    password_hash = generate_password_hash(password)
    user = User.create(email, password_hash, name, role)
    
    # Create access token
    access_token = create_access_token(identity=email)
    
    return jsonify({
        "access_token": access_token,
        "user": user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Log in an existing user."""
    data = request.json
    
    # Validate required fields
    required_fields = ['email', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    email = data['email']
    password = data['password']
    
    # Check if user exists
    user = User.find_by_email(email)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Check password
    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Create access token
    access_token = create_access_token(identity=email)
    
    return jsonify({
        "access_token": access_token,
        "user": user.to_dict()
    })

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get current user profile."""
    return jsonify({"user": current_user.to_dict()})

@app.route('/api/auth/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile."""
    data = request.json
    
    # Update user profile
    if 'name' in data:
        current_user.name = data['name']
    
    # Update profile_id
    if 'profile_id' in data:
        current_user.update_profile_id(data['profile_id'])
    
    return jsonify({"user": current_user.to_dict()})

@app.route('/api/jobs/<job_id>/candidates', methods=['GET'])
@jwt_required()
def get_job_matches(job_id):
    """Get candidates matching a job."""
    # Check if the user has permission to view candidates for this job
    # Allow access if: user is an admin, or the user owns this job
    if current_user.role == 'hiring_manager':
        with kg.driver.session() as session:
            # Check if job exists and belongs to the current user
            job_result = session.run("""
                MATCH (j:Job {job_id: $job_id})
                RETURN j.owner_email as owner_email
            """, {"job_id": job_id})
            
            job = job_result.single()
            if not job:
                return jsonify({"error": f"Job with ID {job_id} not found"}), 404
            
            # Allow access only if the user is the job owner or an admin
            if job["owner_email"] != current_user.email:
                return jsonify({"error": "You do not have permission to view candidates for this job"}), 403
    
    limit = request.args.get('limit', 10, type=int)
    matches = kg.find_matching_candidates(job_id, limit=limit)
    
    # Add match percentage for frontend display
    for match in matches:
        if 'matchScore' in match:
            # Convert raw score to percentage, cap at 100%
            match['match_percentage'] = min(int(match['matchScore'] * 10), 100)
    
    return jsonify(matches)

@app.route('/api/jobs/<job_id>/candidates/enhanced', methods=['GET'])
@jwt_required()
def get_job_matches_enhanced(job_id):
    """Get candidates matching a job using enhanced algorithm with location and semantic matching."""
    # Check if the user has permission to view candidates for this job
    # Allow access if: user is an admin, or the user owns this job
    if current_user.role != 'admin':  # Admin can access any job's candidates
        if current_user.role == 'hiring_manager':
            with kg.driver.session() as session:
                # Check if job exists and belongs to the current user
                job_result = session.run("""
                    MATCH (j:Job {job_id: $job_id})
                    RETURN j.owner_email as owner_email
                """, {"job_id": job_id})
                
                job = job_result.single()
                if not job:
                    return jsonify({"error": f"Job with ID {job_id} not found"}), 404
                
                # Allow access only if the user is the job owner
                if job["owner_email"] != current_user.email:
                    return jsonify({"error": "You do not have permission to view candidates for this job"}), 403
        else:
            # Not an admin or hiring manager
            return jsonify({"error": "You do not have permission to view candidates for this job"}), 403
    
    limit = request.args.get('limit', 10, type=int)
    
    # Get optional weight parameters with better defaults for differentiation (domain removed)
    weights = {
        "skills": request.args.get('skills_weight', 0.75, type=float),
        "location": request.args.get('location_weight', 0.15, type=float),
        "semantic": request.args.get('semantic_weight', 0.1, type=float)
    }
    
    # Normalize weights to ensure they sum to 1
    total_weight = sum(weights.values())
    if total_weight > 0:  # Avoid division by zero
        for key in weights:
            weights[key] = weights[key] / total_weight
    
    matches = kg.find_matching_candidates_enhanced(job_id, limit=limit, weights=weights)
    
    # Format results for frontend
    matches = format_match_results(matches)
    
    return jsonify(matches)

@app.route('/api/candidates/<resume_id>/jobs', methods=['GET'])
def get_candidate_matches(resume_id):
    """Get jobs matching a candidate."""
    limit = request.args.get('limit', 10, type=int)
    matches = kg.find_matching_jobs(resume_id, limit=limit)
    
    return jsonify(matches)

@app.route('/api/candidates/<resume_id>/jobs/enhanced', methods=['GET'])
def get_candidate_matches_enhanced(resume_id):
    """Get jobs matching a candidate using enhanced algorithm with location and semantic matching."""
    limit = request.args.get('limit', 10, type=int)
    
    # Get optional weight parameters with better defaults for differentiation (domain removed)
    weights = {
        "skills": request.args.get('skills_weight', 0.75, type=float),
        "location": request.args.get('location_weight', 0.15, type=float),
        "semantic": request.args.get('semantic_weight', 0.1, type=float)
    }
    
    # Normalize weights to ensure they sum to 1
    total_weight = sum(weights.values())
    if total_weight > 0:  # Avoid division by zero
        for key in weights:
            weights[key] = weights[key] / total_weight
    
    matches = kg.find_matching_jobs_enhanced(resume_id, limit=limit, weights=weights)
    
    # Format results for frontend
    matches = format_match_results(matches)
    
    return jsonify(matches)

@app.route('/api/candidates/<resume_id>/jobs/<job_id>/skill-gap', methods=['GET'])
def get_skill_gap(resume_id, job_id):
    """Get skill gap analysis between a candidate and job."""
    matching_skills = matcher._get_matching_skills(resume_id, job_id)
    missing_skills = matcher._get_missing_skills(resume_id, job_id)
    exceeding_skills = matcher._get_exceeding_skills(resume_id, job_id)
    
    return jsonify({
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "exceeding_skills": exceeding_skills
    })

@app.route('/api/candidates/<resume_id>/jobs/<job_id>/recommendations', methods=['GET'])
def get_skill_recommendations(resume_id, job_id):
    """Get skill recommendations for a candidate to match a job."""
    limit = int(request.args.get('limit', 5))
    
    recommendations = matcher.recommend_skills_for_job(resume_id, job_id, limit=limit)
    return jsonify({"recommendations": recommendations})

@app.route('/api/skills/<skill_id>/related', methods=['GET'])
def get_related_skills(skill_id):
    """Get skills related to a given skill."""
    with kg.driver.session() as session:
        result = session.run("""
            MATCH (s1:Skill {skill_id: $skill_id})-[r]-(s2:Skill)
            RETURN s2.skill_id as skill_id, s2.name as name, 
                   s2.category as category, type(r) as relationship_type
        """, {"skill_id": skill_id})
        
        return jsonify({"related_skills": [dict(record) for record in result]})

@app.route('/api/skills/path', methods=['GET'])
def get_skill_path():
    """Get a path between two skills."""
    start_skill = request.args.get('start')
    end_skill = request.args.get('end')
    max_depth = int(request.args.get('max_depth', 3))
    
    if not start_skill or not end_skill:
        return jsonify({"error": "Both start and end skills are required"}), 400
        
    path = matcher.get_skill_path(start_skill, end_skill, max_depth=max_depth)
    if not path:
        return jsonify({"error": "No path found between these skills"}), 404
        
    return jsonify({"path": path})

@app.route('/api/careers/path', methods=['GET'])
def get_career_path():
    """Get a career path between two job titles."""
    current_title = request.args.get('current')
    target_title = request.args.get('target')
    
    if not current_title or not target_title:
        return jsonify({"error": "Both current and target titles are required"}), 400
        
    path = matcher.get_career_path(current_title, target_title)
    return jsonify({"path": path})

@app.route('/api/jobs', methods=['GET'])
def get_all_jobs():
    """Get all available jobs."""
    company = request.args.get('company')
    email = request.args.get('owner_email')
    
    with kg.driver.session() as session:
        # Build the query based on filters
        query = """
            MATCH (j:Job)
        """
        
        params = {}
        
        # Add filters if provided
        if company:
            query += " WHERE j.company = $company"
            params['company'] = company
            
        if email:
            query += " MATCH (u:User {email: $email})-[:CREATED]->(j)"
            params['email'] = email
            
        query += """
            RETURN j.job_id as job_id, j.title as title, j.company as company,
                   j.location as location, j.domain as domain, j.owner_email as owner_email
            ORDER BY j.job_id
        """
        
        result = session.run(query, params)
        
        jobs = [dict(record) for record in result]
        
        # Get aggregated data for filters
        filter_data = session.run("""
            MATCH (j:Job)
            WITH COLLECT(DISTINCT j.domain) AS domains, COLLECT(DISTINCT j.location) AS locations
            RETURN domains, locations
        """)
        
        filter_record = filter_data.single()
        
        return jsonify({
            "jobs": jobs,
            "filters": {
                "domains": filter_record["domains"] if filter_record else [],
                "locations": filter_record["locations"] if filter_record else []
            }
        })

@app.route('/api/candidates', methods=['GET'])
@jwt_required()
def get_all_candidates():
    """Get all available candidates."""
    # Check if the user has permission to view all candidates
    # Only hiring managers and admins can see all candidates
    if current_user.role not in ['hiring_manager', 'admin']:
        return jsonify({"error": "You do not have permission to view all candidates"}), 403
        
    with kg.driver.session() as session:
        # Get all candidates
        result = session.run("""
            MATCH (c:Candidate)
            RETURN c.resume_id as resume_id, c.name as name, c.title as title,
                   c.location as location, c.domain as domain
            ORDER BY c.resume_id
        """)
        
        candidates = [dict(record) for record in result]
        
        # Get aggregated data for filters - removed domain filter
        filter_data = session.run("""
            MATCH (c:Candidate)
            WITH COLLECT(DISTINCT c.location) AS locations,
                 COLLECT(DISTINCT c.title) AS titles
            RETURN locations, titles
        """)
        
        filter_record = filter_data.single()
        
        return jsonify({
            "candidates": candidates,
            "filters": {
                "locations": filter_record["locations"] if filter_record else [],
                "titles": filter_record["titles"] if filter_record else []
            }
        })

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get a specific job by ID with comprehensive details and required skills."""
    with kg.driver.session() as session:
        # Get job details with comprehensive data
        job_result = session.run("""
            MATCH (j:Job {job_id: $job_id})
            RETURN j.job_id as job_id, 
                   j.title as title, 
                   j.company as company,
                   j.location as location, 
                   j.domain as domain,
                   j.description as description,
                   j.responsibilities as responsibilities,
                   j.qualifications as qualifications,
                   j.salary_range as salary_range,
                   j.job_type as job_type,
                   j.employment_type as employment_type,
                   j.industry as industry
        """, {"job_id": job_id})
        
        job = job_result.single()
        if not job:
            return jsonify({"error": f"Job with ID {job_id} not found"}), 404
            
        job_data = dict(job)
        
        # Check if description is missing but there's a summary field
        if ('description' not in job_data or not job_data['description']) and 'summary' in job_data and job_data['summary']:
            job_data['description'] = job_data['summary']
            
        # Parse JSON strings into arrays for complex fields
        for field in ['responsibilities', 'qualifications']:
            if field in job_data and job_data[field]:
                try:
                    # If it's already a list, keep it as is
                    if isinstance(job_data[field], list):
                        continue
                    # If it's a string, attempt to parse it as JSON
                    elif isinstance(job_data[field], str):
                        parsed_data = json.loads(job_data[field])
                        # Handle both array format and object with numbered keys
                        if isinstance(parsed_data, dict):
                            # Convert dictionary to list (for format like {"0": "item1", "1": "item2"})
                            job_data[field] = [parsed_data[key] for key in sorted(parsed_data.keys(), key=lambda k: int(k) if k.isdigit() else k)]
                        else:
                            job_data[field] = parsed_data
                except (json.JSONDecodeError, TypeError, ValueError) as e:
                    # If the string is a single item, convert to a list with one item
                    if isinstance(job_data[field], str):
                        job_data[field] = [job_data[field]]
                    else:
                        # Initialize as empty array if parsing fails
                        job_data[field] = []
            else:
                # Ensure the field exists with an empty array if not present
                job_data[field] = []
        
        # If responsibilities is a long string, try to split it into bullet points
        if 'responsibilities' in job_data and isinstance(job_data['responsibilities'], str) and len(job_data['responsibilities']) > 100:
            text = job_data['responsibilities']
            items = []
            
            # Try to split by bullet points
            if '•' in text:
                items = [item.strip() for item in text.split('•') if item.strip()]
            # Try to split by numbered list
            elif any(f"{i}." in text for i in range(1, 10)):
                for line in text.splitlines():
                    line = line.strip()
                    if line and any(line.startswith(f"{i}.") for i in range(1, 10)):
                        items.append(line)
            
            # If we couldn't split by bullets or numbers, try to split by sentences
            if not items:
                import re
                # Split by periods followed by space and capital letter (likely sentence boundaries)
                sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
                items = [s.strip() for s in sentences if s.strip()]
                
            # If we still have only one item but it's a long paragraph, force split it
            if len(items) <= 1 and len(text) > 200:
                # Force split by periods if it's a very long text
                items = [s.strip() + '.' for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
                
            if items:
                job_data['responsibilities'] = items
                    
        # Similarly for qualifications
        if 'qualifications' in job_data and isinstance(job_data['qualifications'], str) and len(job_data['qualifications']) > 100:
            text = job_data['qualifications']
            items = []
            
            # Try to split by bullet points
            if '•' in text:
                items = [item.strip() for item in text.split('•') if item.strip()]
            # Try to split by numbered list
            elif any(f"{i}." in text for i in range(1, 10)):
                for line in text.splitlines():
                    line = line.strip()
                    if line and any(line.startswith(f"{i}.") for i in range(1, 10)):
                        items.append(line)
            
            # If we couldn't split by bullets or numbers, try to split by sentences
            if not items:
                import re
                # Split by periods followed by space and capital letter (likely sentence boundaries)
                sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
                items = [s.strip() for s in sentences if s.strip()]
                
            # If we still have only one item but it's a long paragraph, force split it
            if len(items) <= 1 and len(text) > 200:
                # Force split by periods if it's a very long text
                items = [s.strip() + '.' for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
                
            if items:
                job_data['qualifications'] = items
        
        # Get required skills - use a more general query that doesn't rely on a specific relationship type
        skills_result = session.run("""
            MATCH (j:Job {job_id: $job_id})-[r]->(s:Skill)
            RETURN s.skill_id as skill_id, s.name as name, 
                   s.category as category, r.level as level,
                   r.proficiency as original_proficiency,
                   type(r) as relationship_type
            ORDER BY r.level DESC, s.name
        """, {"job_id": job_id})
        
        skills = []
        for record in skills_result:
            skill_data = dict(record)
            # Add relationship type if not present
            if 'relationship_type' not in skill_data or not skill_data['relationship_type']:
                skill_data['relationship_type'] = 'REQUIRES'
            
            # First try to use the original proficiency from the database
            if 'original_proficiency' in skill_data and skill_data['original_proficiency']:
                skill_data['proficiency'] = skill_data['original_proficiency']
            else:
                # Fall back to calculating proficiency from level if original isn't available
                skill_level = skill_data.get('level')
                if skill_level is None:
                    skill_level = 5  # Set a default level if None
                    skill_data['level'] = skill_level
                # Now safely check the skill level  
                skill_data['proficiency'] = 'Expert' if skill_level >= 8 else 'Advanced' if skill_level >= 6 else 'Intermediate' if skill_level >= 4 else 'Beginner'
            
            skill_data['importance'] = skill_data.get('level', 5)
            skills.append(skill_data)
            
        # Format response to match frontend expectations
        return jsonify({
            "job": job_data,
            "skills": skills
        })

@app.route('/api/skills', methods=['GET'])
def get_all_skills():
    """Get all available skills."""
    with kg.driver.session() as session:
        result = session.run("""
            MATCH (s:Skill)
            RETURN s.skill_id as skill_id, s.name as name, s.category as category
            ORDER BY s.name
        """)
        
        return jsonify({"skills": [dict(record) for record in result]})

@app.route('/api/jobs/<job_id>/matches', methods=['GET'])
def get_job_matches_v2(job_id):
    """Get candidates matching a job."""
    limit = int(request.args.get('limit', 10))
    min_score = float(request.args.get('min_score', 0.0))
    
    with kg.driver.session() as session:
        # Get matching candidates with correct relationship types
        result = session.run("""
            MATCH (j:Job {job_id: $job_id})
            MATCH (c:Candidate)
            WITH j, c
            
            // Match all skills (both primary and secondary)
            MATCH (j)-[r_job:REQUIRES_PRIMARY|REQUIRES_SECONDARY]->(s:Skill)<-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(c)
            
            // Calculate scores
            WITH j, c, 
                 sum(CASE
                    WHEN type(r_job) = 'REQUIRES_PRIMARY' THEN 10.0
                    ELSE 5.0
                 END * CASE
                    WHEN exists((c)-[:HAS_CORE_SKILL]->(s)) THEN 1.0
                    ELSE 0.5
                 END) / (count(s) * 10.0) as match_score,
                 count(s) as total_matching_skills
            
            WHERE match_score >= $min_score
            
            // Get primary skills matches specifically
            OPTIONAL MATCH (j)-[:REQUIRES_PRIMARY]->(ps:Skill)<-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(c)
            WITH j, c, match_score, total_matching_skills, collect(ps) as primary_skill_nodes, count(ps) as primary_matching_count
            
            // Get secondary skills matches
            OPTIONAL MATCH (j)-[:REQUIRES_SECONDARY]->(ss:Skill)<-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(c)
            WITH j, c, match_score, total_matching_skills, primary_skill_nodes, primary_matching_count, collect(ss) as secondary_skill_nodes
            
            RETURN c.resume_id as resume_id, c.name as name, c.title as title,
                   total_matching_skills, primary_matching_count, match_score, 
                   primary_skill_nodes, secondary_skill_nodes
            ORDER BY match_score DESC
            LIMIT $limit
        """, {"job_id": job_id, "limit": limit, "min_score": min_score})
        
        matches = []
        for record in result:
            match_data = dict(record)
            # Calculate match percentage (0-100)
            match_data['match_percentage'] = int(match_data.get('match_score', 0) * 100)
            # Add placeholder values for frontend compatibility
            match_data['graph_percentage'] = match_data['match_percentage']
            match_data['text_percentage'] = match_data['match_percentage']
            
            # Extract primary matching skills
            primary_matching_skills = []
            for skill_node in match_data.get('primary_skill_nodes', []):
                skill_data = {
                    'skill_id': skill_node['skill_id'],
                    'name': skill_node['name'],
                    'category': skill_node.get('category', ''),
                }
                primary_matching_skills.append(skill_data)
            match_data['primary_matching_skills'] = primary_matching_skills
            
            # Extract secondary matching skills
            secondary_matching_skills = []
            for skill_node in match_data.get('secondary_skill_nodes', []):
                skill_data = {
                    'skill_id': skill_node['skill_id'],
                    'name': skill_node['name'],
                    'category': skill_node.get('category', ''),
                }
                secondary_matching_skills.append(skill_data)
            match_data['secondary_matching_skills'] = secondary_matching_skills
            
            # Keep the original matching_skills field for backward compatibility
            match_data['matching_skills'] = primary_matching_skills
            match_data['missing_skills'] = []
            
            # Remove skill_nodes from the response
            if 'primary_skill_nodes' in match_data:
                del match_data['primary_skill_nodes']
            if 'secondary_skill_nodes' in match_data:
                del match_data['secondary_skill_nodes']
                
            matches.append(match_data)
            
        return jsonify(matches)

@app.route('/api/candidates/<resume_id>/matches', methods=['GET'])
def get_candidate_matches_v2(resume_id):
    """Get jobs matching a candidate."""
    limit = int(request.args.get('limit', 10))
    min_score = float(request.args.get('min_score', 0.0))
    
    matches = matcher.match_candidate_to_jobs(resume_id, limit=limit, min_score=min_score)
    return jsonify(matches)

@app.route('/api/candidates/<resume_id>/recommendations/<job_id>', methods=['GET'])
def get_candidate_recommendations(resume_id, job_id):
    """Get skill recommendations for a candidate to match a job."""
    limit = int(request.args.get('limit', 5))
    
    recommendations = matcher.recommend_skills_for_job(resume_id, job_id, limit=limit)
    return jsonify(recommendations)

@app.route('/api/graph/skill/<skill_id>', methods=['GET'])
def get_skill_graph_data(skill_id):
    """Get graph data for a skill."""
    depth = int(request.args.get('depth', 2))
    
    # Limit depth to valid range (1-3)
    if depth < 1:
        depth = 1
    elif depth > 3:
        depth = 3
    
    with kg.driver.session() as session:
        # Get the central skill
        result = session.run("""
            MATCH (s:Skill {skill_id: $skill_id})
            RETURN s.skill_id as id, s.name as name, 'skill' as type
        """, {"skill_id": skill_id})
        
        nodes = [dict(record) for record in result]
        if not nodes:
            return jsonify({"error": f"Skill with ID {skill_id} not found"}), 404
            
        # Get related skills up to specified depth
        result = session.run(f"""
            MATCH path = (s:Skill {{skill_id: $skill_id}})-[r*1..{depth}]-(related:Skill)
            UNWIND nodes(path) as node
            UNWIND relationships(path) as rel
            RETURN DISTINCT 
                node.skill_id as id, 
                node.name as name, 
                'skill' as type,
                startNode(rel).skill_id as source,
                endNode(rel).skill_id as target,
                type(rel) as relationship
        """, {"skill_id": skill_id})
        
        # Process results
        nodes_dict = {nodes[0]['id']: nodes[0]}  # Add the central node
        edges = []
        
        for record in result:
            # Only process nodes with valid IDs
            if record['id'] is not None:
                # Add node if not already present
                if record['id'] not in nodes_dict:
                    nodes_dict[record['id']] = {
                        'id': record['id'],
                        'name': record['name'],
                        'type': record['type']
                    }
                
                # Only add edges with valid source and target
                if record['source'] is not None and record['target'] is not None:
                    edges.append({
                        'source': record['source'],
                        'target': record['target'],
                        'relationship': record['relationship']
                    })
        
        return jsonify({
            'nodes': list(nodes_dict.values()),
            'edges': edges
        })

@app.route('/api/candidates/<resume_id>', methods=['GET'])
@jwt_required()
def get_candidate(resume_id):
    """Get a specific candidate by ID with comprehensive resume data."""
    # Check permissions:
    # 1. Admin can view any candidate
    # 2. Hiring managers can view any candidate
    # 3. Candidates can only view their own profile
    if current_user.role == 'candidate' and current_user.profile_id != resume_id:
        return jsonify({"error": "You don't have permission to view this candidate's profile"}), 403
        
    with kg.driver.session() as session:
        # Get candidate details with more comprehensive data
        candidate_result = session.run("""
            MATCH (c:Candidate {resume_id: $resume_id})
            RETURN c.resume_id as resume_id, 
                   c.name as name, 
                   c.title as title,
                   c.location as location, 
                   c.domain as domain,
                   c.email as email,
                   c.summary as summary,
                   c.education as education,
                   c.certifications as certifications,
                   c.languages as languages
        """, {"resume_id": resume_id})
        
        candidate = candidate_result.single()
        if not candidate:
            return jsonify({"error": f"Candidate with ID {resume_id} not found"}), 404
            
        candidate_data = dict(candidate)
        
        # Parse JSON strings into arrays for complex fields
        for field in ['education', 'certifications', 'languages']:
            if field in candidate_data and candidate_data[field]:
                try:
                    if isinstance(candidate_data[field], str):
                        candidate_data[field] = json.loads(candidate_data[field])
                except (json.JSONDecodeError, TypeError):
                    # If parsing fails, initialize as an empty array
                    candidate_data[field] = []
                    
        # Get experiences from the knowledge graph
        experiences = kg.get_candidate_experiences(resume_id)
        
        # Format the experiences for the frontend
        formatted_experiences = []
        for exp in experiences:
            # Format the period string
            period = f"{exp['start_date']} - {exp['end_date']}"
            
            # Format the description (should already be a list from the knowledge graph)
            description = exp['description'] if exp['description'] else []
            
            formatted_experiences.append({
                "title": exp['job_title'],
                "company": exp['company'],
                "period": period,
                "description": description,
                "skills": exp['skills']
            })
        
        # Add experiences to the candidate data
        candidate_data['experience'] = formatted_experiences
                    
        # Get candidate skills - use a more general query that doesn't rely on a specific relationship type
        skills_result = session.run("""
            MATCH (c:Candidate {resume_id: $resume_id})-[r]->(s:Skill)
            RETURN s.skill_id as skill_id, s.name as name, 
                   s.category as category, r.level as level, r.years as years,
                   type(r) as relationship_type
            ORDER BY r.level DESC, r.years DESC, s.name
        """, {"resume_id": resume_id})
        
        skills = []
        for record in skills_result:
            skill_data = dict(record)
            # Add relationship type if not present
            if 'relationship_type' not in skill_data or not skill_data['relationship_type']:
                skill_data['relationship_type'] = 'HAS_SKILL'
            # Add proficiency level labels for frontend
            skill_level = skill_data.get('level')
            if skill_level is None:
                skill_level = 5  # Set a default level if None
                skill_data['level'] = skill_level
            # Now safely check the skill level
            if skill_level >= 8:
                skill_data['proficiency'] = 'Expert'
            elif skill_level >= 6:
                skill_data['proficiency'] = 'Advanced'
            elif skill_level >= 4:
                skill_data['proficiency'] = 'Intermediate'
            else:
                skill_data['proficiency'] = 'Beginner'
            skills.append(skill_data)
            
        return jsonify({
            "candidate": candidate_data,
            "skills": skills
        })

@app.route('/api/skills/<skill_id>', methods=['GET'])
def get_skill(skill_id):
    """Get details for a specific skill."""
    with kg.driver.session() as session:
        # Get skill details
        skill_result = session.run("""
            MATCH (s:Skill {skill_id: $skill_id})
            RETURN s.skill_id as skill_id, s.name as name, s.category as category
        """, {"skill_id": skill_id})
        
        skill = skill_result.single()
        if not skill:
            return jsonify({"error": f"Skill with ID {skill_id} not found"}), 404
            
        skill_data = dict(skill)
        
        # Get related skills
        related_result = session.run("""
            MATCH (s1:Skill {skill_id: $skill_id})-[r]-(s2:Skill)
            RETURN s2.skill_id as skill_id, s2.name as name, 
                   s2.category as category, type(r) as relationship_type
        """, {"skill_id": skill_id})
        
        related_skills = [dict(record) for record in related_result]
        
        # Get jobs requiring this skill
        jobs_result = session.run("""
            MATCH (j:Job)-[r:REQUIRES]->(s:Skill {skill_id: $skill_id})
            RETURN j.job_id as job_id, j.title as title, j.company as company,
                   r.level as required_level
            LIMIT 10
        """, {"skill_id": skill_id})
        
        jobs = [dict(record) for record in jobs_result]
        
        # Get candidates with this skill
        candidates_result = session.run("""
            MATCH (c:Candidate)-[r:HAS_SKILL]->(s:Skill {skill_id: $skill_id})
            RETURN c.resume_id as resume_id, c.name as name, c.title as title,
                   r.level as skill_level, r.years as years_experience
            LIMIT 10
        """, {"skill_id": skill_id})
        
        candidates = [dict(record) for record in candidates_result]
            
        return jsonify({
            "skill": skill_data,
            "related_skills": related_skills,
            "jobs": jobs,
            "candidates": candidates
        })

@app.route('/api/debug/jobs/<job_id>', methods=['GET'])
def get_job_debug(job_id):
    """Get raw job data for debugging."""
    with kg.driver.session() as session:
        job_result = session.run("""
            MATCH (j:Job {job_id: $job_id})
            RETURN j
        """, {"job_id": job_id})
        
        record = job_result.single()
        if not record:
            return jsonify({"error": f"Job with ID {job_id} not found"}), 404
            
        # Get all properties of the node
        job_node = record["j"]
        job_data = dict(job_node.items())
            
        return jsonify({
            "raw_job_data": job_data
        })

@app.route('/api/debug/jobs/<job_id>/text-fields', methods=['GET'])
def get_job_text_fields(job_id):
    """Get detailed debugging info for job text fields."""
    with kg.driver.session() as session:
        # Get the raw job data
        job_result = session.run("""
            MATCH (j:Job {job_id: $job_id})
            RETURN j.responsibilities as raw_resp, j.qualifications as raw_qual,
                  j.description as raw_desc
        """, {"job_id": job_id})
        
        record = job_result.single()
        if not record:
            return jsonify({"error": f"Job with ID {job_id} not found"}), 404
            
        # Extract the raw text fields
        raw_resp = record["raw_resp"]
        raw_qual = record["raw_qual"]
        raw_desc = record["raw_desc"]
        
        # Process the fields as in the main API but with more debug info
        import json
        resp_items = []
        qual_items = []
        
        # Try to parse responsibilities
        resp_debug = {
            "type": str(type(raw_resp)),
            "raw_value": raw_resp,
            "parsed_items": []
        }
        
        if raw_resp:
            # Try json parsing
            try:
                if isinstance(raw_resp, str):
                    parsed = json.loads(raw_resp)
                    if isinstance(parsed, list):
                        resp_items = parsed
                    elif isinstance(parsed, dict):
                        resp_items = [parsed[key] for key in sorted(parsed.keys(), key=lambda k: int(k) if k.isdigit() else k)]
                    resp_debug["json_parsed"] = resp_items
            except Exception as e:
                resp_debug["json_error"] = str(e)
                
            # Try sentence splitting
            if isinstance(raw_resp, str):
                import re
                sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', raw_resp)
                resp_debug["sentence_split"] = [s.strip() for s in sentences if s.strip()]
        
        # Try to parse qualifications
        qual_debug = {
            "type": str(type(raw_qual)),
            "raw_value": raw_qual,
            "parsed_items": []
        }
        
        if raw_qual:
            # Try json parsing
            try:
                if isinstance(raw_qual, str):
                    parsed = json.loads(raw_qual)
                    if isinstance(parsed, list):
                        qual_items = parsed
                    elif isinstance(parsed, dict):
                        qual_items = [parsed[key] for key in sorted(parsed.keys(), key=lambda k: int(k) if k.isdigit() else k)]
                    qual_debug["json_parsed"] = qual_items
            except Exception as e:
                qual_debug["json_error"] = str(e)
                
            # Try sentence splitting
            if isinstance(raw_qual, str):
                import re
                sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', raw_qual)
                qual_debug["sentence_split"] = [s.strip() for s in sentences if s.strip()]
            
        return jsonify({
            "responsibilities_debug": resp_debug,
            "qualifications_debug": qual_debug,
            "description": raw_desc
        })

@app.route('/api/embeddings/generate', methods=['POST'])
@jwt_required()
def generate_embeddings():
    """Generate embeddings for all jobs and experiences.
    This is an admin endpoint that requires authentication."""
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
        
    try:
        success = kg.generate_embeddings()
        if success:
            return jsonify({"message": "Embeddings generated successfully"})
        else:
            return jsonify({"error": "Failed to generate embeddings. Check server logs."}), 500
    except Exception as e:
        return jsonify({"error": f"Error generating embeddings: {str(e)}"}), 500

# Routes for job posting and resume uploads
@app.route('/api/jobs/create', methods=['POST'])
@jwt_required()
def create_job():
    """Create a new job posting."""
    # Check if user is a hiring manager
    if current_user.role != 'hiring_manager':
        return jsonify({"error": "Only hiring managers can post jobs"}), 403
    
    data = request.json
    
    # Validate required fields
    required_fields = ['title', 'company', 'location', 'summary', 'domain', 'responsibilities', 'qualifications']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Generate a unique job_id
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    
    # Prepare job data
    job_data = {
        "job_id": job_id,
        "title": data['title'],
        "company": data['company'],
        "location": data['location'],
        "domain": data['domain'],
        "job_type": data.get('job_type', 'Full-time'),
        "summary": data['summary'],
        "responsibilities": data['responsibilities'],
        "qualifications": data['qualifications'],
        "salary_range": data.get('salary_range', 'Competitive'),
        "owner_email": current_user.email,
        "skills": {
            "primary": data.get('primary_skills', []),
            "secondary": data.get('secondary_skills', [])
        }
    }
    
    # Store job in the knowledge graph
    with kg.driver.session() as session:
        # Create job node
        session.run("""
            CREATE (j:Job {
                job_id: $job_id,
                title: $title,
                company: $company,
                location: $location,
                domain: $domain,
                job_type: $job_type,
                summary: $summary,
                responsibilities: $responsibilities,
                qualifications: $qualifications,
                salary_range: $salary_range,
                owner_email: $owner_email
            })
        """, job_data)
        
        # Create relationship between user and job
        session.run("""
            MATCH (u:User {email: $email})
            MATCH (j:Job {job_id: $job_id})
            CREATE (u)-[:CREATED]->(j)
        """, {
            "email": current_user.email,
            "job_id": job_id
        })
        
        # Add primary skills
        for skill in job_data['skills']['primary']:
            session.run("""
                MATCH (s:Skill {skill_id: $skill_id})
                MATCH (j:Job {job_id: $job_id})
                CREATE (j)-[r:REQUIRES_PRIMARY {
                    level: $level,
                    proficiency: $proficiency,
                    importance: $importance
                }]->(s)
            """, {
                "job_id": job_id,
                "skill_id": skill['skill_id'],
                "level": skill.get('level', 5),
                "proficiency": skill.get('proficiency', 'Intermediate'),
                "importance": skill.get('importance', 0.7)
            })
        
        # Add secondary skills
        for skill in job_data['skills']['secondary']:
            session.run("""
                MATCH (s:Skill {skill_id: $skill_id})
                MATCH (j:Job {job_id: $job_id})
                CREATE (j)-[r:REQUIRES_SECONDARY {
                    level: $level,
                    proficiency: $proficiency,
                    importance: $importance
                }]->(s)
            """, {
                "job_id": job_id,
                "skill_id": skill['skill_id'],
                "level": skill.get('level', 3),
                "proficiency": skill.get('proficiency', 'Beginner'),
                "importance": skill.get('importance', 0.4)
            })
    
    # Update user's profile_id
    current_user.update_profile_id(job_id)
    
    return jsonify({
        "job_id": job_id,
        "message": "Job created successfully"
    }), 201

@app.route('/api/resumes/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    """Upload a new resume."""
    # Check if user is a candidate
    if current_user.role != 'candidate':
        return jsonify({"error": "Only candidates can upload resumes"}), 403
    
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'email', 'title', 'location', 'summary', 'experience', 'education', 'skills']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Generate a unique resume_id
    resume_id = f"resume_{uuid.uuid4().hex[:8]}"
    
    # Prepare resume data
    resume_data = {
        "resume_id": resume_id,
        "name": data['name'],
        "email": data['email'],
        "phone": data.get('phone', ''),
        "location": data['location'],
        "title": data['title'],
        "summary": data['summary'],
        "education": data['education'],
        "certifications": data.get('certifications', []),
        "languages": data.get('languages', []),
        "experience": data['experience'],
        "skills": {
            "core": data['skills'].get('core', []),
            "secondary": data['skills'].get('secondary', []),
            "domain": data.get('domain', 'general')
        }
    }
    
    # Store resume in the knowledge graph
    with kg.driver.session() as session:
        # Create candidate node
        session.run("""
            CREATE (c:Candidate {
                resume_id: $resume_id,
                name: $name,
                email: $email,
                phone: $phone,
                location: $location,
                title: $title,
                summary: $summary,
                education: $education,
                certifications: $certifications,
                languages: $languages,
                domain: $domain
            })
        """, {
            "resume_id": resume_id,
            "name": resume_data['name'],
            "email": resume_data['email'],
            "phone": resume_data['phone'],
            "location": resume_data['location'],
            "title": resume_data['title'],
            "summary": resume_data['summary'],
            "education": json.dumps(resume_data['education']),
            "certifications": json.dumps(resume_data['certifications']),
            "languages": json.dumps(resume_data['languages']),
            "domain": resume_data['skills']['domain']
        })
        
        # Add experiences
        for exp in resume_data['experience']:
            # Create experience node
            session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})
                CREATE (c)-[:HAS_EXPERIENCE]->(e:Experience {
                    job_title: $job_title,
                    company: $company,
                    start_date: $start_date,
                    end_date: $end_date,
                    description: $description
                })
            """, {
                "resume_id": resume_id,
                "job_title": exp['job_title'],
                "company": exp['company'],
                "start_date": exp['start_date'],
                "end_date": exp['end_date'],
                "description": json.dumps(exp['description'])
            })
        
        # Add core skills
        for skill in resume_data['skills']['core']:
            session.run("""
                MATCH (s:Skill {skill_id: $skill_id})
                MATCH (c:Candidate {resume_id: $resume_id})
                CREATE (c)-[r:HAS_CORE_SKILL {
                    level: $level,
                    years: $years,
                    proficiency: $proficiency
                }]->(s)
            """, {
                "resume_id": resume_id,
                "skill_id": skill['skill_id'],
                "level": skill.get('level', 5),
                "years": skill.get('experience_years', 0.5),
                "proficiency": skill.get('proficiency', 'Intermediate')
            })
        
        # Add secondary skills
        for skill in resume_data['skills']['secondary']:
            session.run("""
                MATCH (s:Skill {skill_id: $skill_id})
                MATCH (c:Candidate {resume_id: $resume_id})
                CREATE (c)-[r:HAS_SECONDARY_SKILL {
                    level: $level,
                    years: $years,
                    proficiency: $proficiency
                }]->(s)
            """, {
                "resume_id": resume_id,
                "skill_id": skill['skill_id'],
                "level": skill.get('level', 3),
                "years": skill.get('experience_years', 0.2),
                "proficiency": skill.get('proficiency', 'Beginner')
            })
    
    # Update user's profile_id
    current_user.update_profile_id(resume_id)
    
    return jsonify({
        "resume_id": resume_id,
        "message": "Resume uploaded successfully"
    }), 201

@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Get all users - admin function."""
    # Check if current user has admin privileges
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
        
    with kg.driver.session() as session:
        result = session.run("""
            MATCH (u:User)
            RETURN u.email as email, u.name as name, 
                   u.role as role, u.profile_id as profile_id,
                   u.created_at as created_at
        """)
        
        users = [dict(record) for record in result]
        return jsonify({"users": users})

@app.route('/api/users/<email>', methods=['GET'])
@jwt_required()
def get_user_by_email(email):
    """Get user by email."""
    # Check permissions - a user can only access their own profile unless admin
    if current_user.email != email and current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
        
    user = User.find_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify({"user": user.to_dict()})

@app.route('/api/users/<email>', methods=['PUT'])
@jwt_required()
def update_user(email):
    """Update user information."""
    # Check permissions - a user can only update their own profile unless admin
    if current_user.email != email and current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
        
    user = User.find_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    updates = {}
    
    # Fields that can be updated
    if 'name' in data:
        updates['name'] = data['name']
    
    if 'role' in data and current_user.role == 'admin':  # Only admin can change roles
        updates['role'] = data['role']
    
    if 'profile_id' in data:
        user.update_profile_id(data['profile_id'])
    
    # If we have fields to update other than profile_id
    if updates:
        with kg.driver.session() as session:
            update_query = "MATCH (u:User {email: $email}) SET "
            update_query += ", ".join(f"u.{key} = ${key}" for key in updates)
            
            params = {"email": email}
            params.update(updates)
            
            session.run(update_query, params)
            
            # Update the user object
            for key, value in updates.items():
                setattr(user, key, value)
    
    return jsonify({"user": user.to_dict()})

@app.route('/api/users/<email>', methods=['DELETE'])
@jwt_required()
def delete_user(email):
    """Delete a user account."""
    # Only admin or the user themselves can delete an account
    if current_user.email != email and current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
    
    with kg.driver.session() as session:
        # Check if user exists
        result = session.run("""
            MATCH (u:User {email: $email})
            RETURN count(u) as count
        """, {"email": email})
        
        if result.single()["count"] == 0:
            return jsonify({"error": "User not found"}), 404
        
        # Delete the user
        session.run("""
            MATCH (u:User {email: $email})
            DELETE u
        """, {"email": email})
    
    return jsonify({"message": "User deleted successfully"})

@app.route('/api/users/role/<role>', methods=['GET'])
@jwt_required()
def get_users_by_role(role):
    """Get users by role."""
    # Only admin can get all users of a certain role
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
    
    # Validate role
    if role not in ['hiring_manager', 'candidate', 'admin']:
        return jsonify({"error": "Invalid role"}), 400
    
    with kg.driver.session() as session:
        result = session.run("""
            MATCH (u:User {role: $role})
            RETURN u.email as email, u.name as name, 
                   u.role as role, u.profile_id as profile_id,
                   u.created_at as created_at
        """, {"role": role})
        
        users = [dict(record) for record in result]
        return jsonify({"users": users})

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
@jwt_required()
def delete_job(job_id):
    """Delete a job posting."""
    # Check if user is a hiring manager
    if current_user.role != 'hiring_manager':
        return jsonify({"error": "Only hiring managers can delete jobs"}), 403
    
    with kg.driver.session() as session:
        # Check if job exists and belongs to the current user
        job_result = session.run("""
            MATCH (j:Job {job_id: $job_id})
            RETURN j.owner_email as owner_email
        """, {"job_id": job_id})
        
        job = job_result.single()
        if not job:
            return jsonify({"error": f"Job with ID {job_id} not found"}), 404
            
        # Check if the current user owns this job
        if job["owner_email"] != current_user.email and current_user.role != 'admin':
            return jsonify({"error": "You do not have permission to delete this job"}), 403
        
        # Delete all relationships and the job
        session.run("""
            MATCH (j:Job {job_id: $job_id})
            OPTIONAL MATCH (j)-[r]-()
            DELETE r, j
        """, {"job_id": job_id})
    
    return jsonify({"message": "Job deleted successfully"}), 200

@app.route('/api/admin/jobs/assign-ownership', methods=['POST'])
@jwt_required()
def assign_job_ownership():
    """Assign ownership of jobs to a specific user. Admin only."""
    # Check if user is admin
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
    
    data = request.json
    
    # Validate required fields
    required_fields = ['email', 'job_ids']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    email = data['email']
    job_ids = data['job_ids']
    
    # Check if user exists
    user = User.find_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if user is a hiring manager
    if user.role != 'hiring_manager':
        return jsonify({"error": "User must be a hiring manager"}), 400
    
    # Update ownership for each job
    results = {"success": [], "failed": []}
    with kg.driver.session() as session:
        for job_id in job_ids:
            # Check if job exists
            job_result = session.run("""
                MATCH (j:Job {job_id: $job_id})
                RETURN count(j) as count
            """, {"job_id": job_id})
            
            job_exists = job_result.single()["count"] > 0
            if not job_exists:
                results["failed"].append({"job_id": job_id, "reason": "Job not found"})
                continue
            
            try:
                # Update job ownership
                session.run("""
                    MATCH (j:Job {job_id: $job_id})
                    SET j.owner_email = $email
                """, {"job_id": job_id, "email": email})
                
                # Create relationship between user and job
                session.run("""
                    MATCH (u:User {email: $email})
                    MATCH (j:Job {job_id: $job_id})
                    MERGE (u)-[:CREATED]->(j)
                """, {"email": email, "job_id": job_id})
                
                results["success"].append(job_id)
            except Exception as e:
                results["failed"].append({"job_id": job_id, "reason": str(e)})
    
    return jsonify({
        "message": f"Assigned {len(results['success'])} jobs to {email}",
        "results": results
    })

@app.route('/api/admin/users/make-admin', methods=['POST'])
@jwt_required()
def make_user_admin():
    """Promote a user to admin status. Admin only."""
    # Check if user is admin
    if not hasattr(current_user, 'role') or current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
    
    data = request.json
    
    # Validate required fields
    if 'email' not in data:
        return jsonify({"error": "Missing email field"}), 400
    
    email = data['email']
    
    # Check if user exists
    user = User.find_by_email(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Update user role to admin
    with kg.driver.session() as session:
        session.run("""
            MATCH (u:User {email: $email})
            SET u.role = 'admin'
        """, {"email": email})
    
    return jsonify({
        "message": f"User {email} promoted to admin",
        "user": {"email": email, "role": "admin"}
    })

@app.route('/api/candidates/<resume_id>/update', methods=['PUT'])
@jwt_required()
def update_candidate(resume_id):
    """Update candidate profile.
    
    This endpoint allows a candidate to update their profile information.
    Only the candidate who owns the profile can update it.
    """
    current_user_id = get_jwt_identity()
    user = User.find_by_email(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Make sure the user is the owner of the profile
    if user.profile_id != resume_id:
        return jsonify({"error": "You don't have permission to update this profile"}), 403
    
    # Get request data
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        with kg.driver.session() as session:
            # Update candidate basic information
            session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})
                SET c.name = $name,
                    c.email = $email,
                    c.phone = $phone,
                    c.location = $location,
                    c.title = $title,
                    c.summary = $summary,
                    c.domain = $domain
            """, {
                "resume_id": resume_id,
                "name": data.get('name', ''),
                "email": data.get('email', ''),
                "phone": data.get('phone', ''),
                "location": data.get('location', ''),
                "title": data.get('title', ''),
                "summary": data.get('summary', ''),
                "domain": data.get('domain', '')
            })
            
            # Remove existing skills
            session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})-[r:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(s:Skill)
                DELETE r
            """, {"resume_id": resume_id})
            
            # Add primary skills
            for skill in data.get('primary_skills', []):
                session.run("""
                    MATCH (s:Skill {skill_id: $skill_id})
                    MATCH (c:Candidate {resume_id: $resume_id})
                    CREATE (c)-[r:HAS_CORE_SKILL {
                        level: $level,
                        years: $years,
                        proficiency: $proficiency
                    }]->(s)
                """, {
                    "resume_id": resume_id,
                    "skill_id": skill.get('skill_id', ''),
                    "level": skill.get('level', 5),
                    "years": skill.get('experience_years', 1),
                    "proficiency": skill.get('proficiency', 'Intermediate')
                })
            
            # Add secondary skills
            for skill in data.get('secondary_skills', []):
                session.run("""
                    MATCH (s:Skill {skill_id: $skill_id})
                    MATCH (c:Candidate {resume_id: $resume_id})
                    CREATE (c)-[r:HAS_SECONDARY_SKILL {
                        level: $level,
                        years: $years,
                        proficiency: $proficiency
                    }]->(s)
                """, {
                    "resume_id": resume_id,
                    "skill_id": skill.get('skill_id', ''),
                    "level": skill.get('level', 3),
                    "years": skill.get('experience_years', 0.5),
                    "proficiency": skill.get('proficiency', 'Beginner')
                })
            
            # Update education
            session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})
                SET c.education = $education
            """, {
                "resume_id": resume_id,
                "education": json.dumps(data.get('education', []))
            })
            
            # Handle experience - first remove old experiences
            session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})-[r:HAS_EXPERIENCE]->(e:Experience)
                DETACH DELETE e
            """, {"resume_id": resume_id})
            
            # Add new experiences
            for exp in data.get('experience', []):
                session.run("""
                    MATCH (c:Candidate {resume_id: $resume_id})
                    CREATE (c)-[:HAS_EXPERIENCE]->(e:Experience {
                        job_title: $job_title,
                        company: $company,
                        start_date: $start_date,
                        end_date: $end_date,
                        description: $description
                    })
                """, {
                    "resume_id": resume_id,
                    "job_title": exp.get('job_title', ''),
                    "company": exp.get('company', ''),
                    "start_date": exp.get('start_date', ''),
                    "end_date": exp.get('end_date', ''),
                    "description": json.dumps(exp.get('description', []))
                })
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "resume_id": resume_id
        })
    
    except Exception as e:
        app.logger.error(f"Error updating profile: {str(e)}")
        return jsonify({"error": f"Error updating profile: {str(e)}"}), 500

@app.route('/api/jobs/<job_id>/update', methods=['PUT'])
@jwt_required()
def update_job(job_id):
    """Update job posting.
    
    This endpoint allows a hiring manager to update their job posting.
    Only the hiring manager who owns the job can update it.
    """
    current_user_id = get_jwt_identity()
    user = User.find_by_email(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Make sure the user is authorized (hiring manager or admin)
    if user.role not in ['hiring_manager', 'admin']:
        return jsonify({"error": "Only hiring managers can update job postings"}), 403
    
    # Get request data
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        with kg.driver.session() as session:
            # Check if user owns the job
            result = session.run("""
                MATCH (j:Job {job_id: $job_id})
                RETURN j.owner_email as owner_email
            """, {"job_id": job_id})
            
            record = result.single()
            if not record:
                return jsonify({"error": "Job not found"}), 404
            
            # Only job owner or admin can update
            if record["owner_email"] != user.email and user.role != 'admin':
                return jsonify({"error": "You don't have permission to update this job"}), 403
            
            # Update job basic information
            session.run("""
                MATCH (j:Job {job_id: $job_id})
                SET j.title = $title,
                    j.company = $company,
                    j.location = $location,
                    j.domain = $domain,
                    j.job_type = $job_type,
                    j.summary = $summary,
                    j.salary_range = $salary_range
            """, {
                "job_id": job_id,
                "title": data.get('title', ''),
                "company": data.get('company', ''),
                "location": data.get('location', ''),
                "domain": data.get('domain', ''),
                "job_type": data.get('job_type', ''),
                "summary": data.get('summary', ''),
                "salary_range": data.get('salary_range', '')
            })
            
            # Update responsibilities and qualifications
            session.run("""
                MATCH (j:Job {job_id: $job_id})
                SET j.responsibilities = $responsibilities,
                    j.qualifications = $qualifications
            """, {
                "job_id": job_id,
                "responsibilities": json.dumps(data.get('responsibilities', [])),
                "qualifications": json.dumps(data.get('qualifications', []))
            })
            
            # Remove existing skills
            session.run("""
                MATCH (j:Job {job_id: $job_id})-[r:REQUIRES_PRIMARY|REQUIRES_SECONDARY]->(s:Skill)
                DELETE r
            """, {"job_id": job_id})
            
            # Add primary skills
            for skill in data.get('primary_skills', []):
                session.run("""
                    MATCH (s:Skill {skill_id: $skill_id})
                    MATCH (j:Job {job_id: $job_id})
                    CREATE (j)-[r:REQUIRES_PRIMARY {
                        level: $level,
                        proficiency: $proficiency,
                        importance: $importance
                    }]->(s)
                """, {
                    "job_id": job_id,
                    "skill_id": skill.get('skill_id', ''),
                    "level": skill.get('level', 5),
                    "proficiency": skill.get('proficiency', 'Intermediate'),
                    "importance": skill.get('importance', 0.7)
                })
            
            # Add secondary skills
            for skill in data.get('secondary_skills', []):
                session.run("""
                    MATCH (s:Skill {skill_id: $skill_id})
                    MATCH (j:Job {job_id: $job_id})
                    CREATE (j)-[r:REQUIRES_SECONDARY {
                        level: $level,
                        proficiency: $proficiency,
                        importance: $importance
                    }]->(s)
                """, {
                    "job_id": job_id,
                    "skill_id": skill.get('skill_id', ''),
                    "level": skill.get('level', 3),
                    "proficiency": skill.get('proficiency', 'Beginner'),
                    "importance": skill.get('importance', 0.4)
                })
        
        return jsonify({
            "success": True,
            "message": "Job updated successfully",
            "job_id": job_id
        })
    
    except Exception as e:
        app.logger.error(f"Error updating job: {str(e)}")
        return jsonify({"error": f"Error updating job: {str(e)}"}), 500

# Skill analysis functions
def analyze_skill_gap(candidate_id, job_id):
    # Cypher query to find skills the job requires but candidate lacks
    query = """
    MATCH (j:Job {job_id: $job_id})-[:REQUIRES_PRIMARY|REQUIRES_SECONDARY]->(s:Skill)
    WHERE NOT EXISTS{
      MATCH (c:Candidate {resume_id: $candidate_id})-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(s)
    }
    RETURN DISTINCT s.name AS missing_skill, s.category AS category, 
           s.relevance AS importance
    ORDER BY s.relevance DESC
    """
    
    # Additional query to find related skills the candidate already has
    related_query = """
    MATCH (j:Job {job_id: $job_id})-[:REQUIRES_PRIMARY|REQUIRES_SECONDARY]->(target:Skill)
    MATCH (c:Candidate {resume_id: $candidate_id})-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(existing:Skill)
    MATCH (existing)-[:related_to]-(target)
    WHERE NOT EXISTS{
      MATCH (c)-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(target)
    }
    RETURN DISTINCT target.name AS target_skill, existing.name AS related_skill,
           target.relevance AS importance
    ORDER BY target.relevance DESC
    """
    
    # Execute queries and process results
    with kg.driver.session() as session:
        missing_skills = session.run(query, candidate_id=candidate_id, job_id=job_id).data()
        related_skills = session.run(related_query, candidate_id=candidate_id, job_id=job_id).data()
    
    return {
        "missing_skills": missing_skills,
        "related_skills": related_skills
    }

# API endpoints for skill analysis
@app.route('/api/analysis/skill-gap/<candidate_id>/<job_id>', methods=['GET'])
@jwt_required()
def analyze_skill_gap_endpoint(candidate_id, job_id):
    try:
        # Verify user has permission to access this data
        current_user_id = get_jwt_identity()
        user = User.find_by_email(current_user_id)
        
        # Only allow access for the candidate themselves, or hiring managers/admins
        if user.role == 'candidate' and user.profile_id != candidate_id and user.role != 'admin':
            return jsonify({"error": "Unauthorized access"}), 403
        
        result = analyze_skill_gap(candidate_id, job_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', API_PORT))
    app.run(host='0.0.0.0', port=port, debug=True) 