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
from flask_jwt_extended import jwt_required, current_user
import math

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize knowledge graph
kg = None
matcher = None

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

@app.route('/api/jobs/<job_id>/candidates', methods=['GET'])
def get_job_matches(job_id):
    """Get candidates matching a job."""
    limit = request.args.get('limit', 10, type=int)
    matches = kg.find_matching_candidates(job_id, limit=limit)
    
    # Add match percentage for frontend display
    for match in matches:
        if 'matchScore' in match:
            # Convert raw score to percentage, cap at 100%
            match['match_percentage'] = min(int(match['matchScore'] * 10), 100)
    
    return jsonify(matches)

@app.route('/api/jobs/<job_id>/candidates/enhanced', methods=['GET'])
def get_job_matches_enhanced(job_id):
    """Get candidates matching a job using enhanced algorithm with location and semantic matching."""
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
    with kg.driver.session() as session:
        # Get all jobs
        result = session.run("""
            MATCH (j:Job)
            RETURN j.job_id as job_id, j.title as title, j.company as company,
                   j.location as location, j.domain as domain
            ORDER BY j.job_id
        """)
        
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
def get_all_candidates():
    """Get all available candidates."""
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
def get_candidate(resume_id):
    """Get a specific candidate by ID with comprehensive resume data."""
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) 