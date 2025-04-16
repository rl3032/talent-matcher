"""
Knowledge Graph Model for Talent Matcher
This module defines the core entities and relationships for the knowledge graph.
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Load environment variables
load_dotenv()

class KnowledgeGraph:
    """Knowledge Graph for skill matching using Neo4j."""
    
    def __init__(self, uri=None, user=None, password=None):
        """Initialize the knowledge graph with Neo4j connection."""
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self.driver = None
        
    def connect(self):
        """Connect to the Neo4j database."""
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        print("Connected to Neo4j knowledge graph database")
        
    def close(self):
        """Close the connection to Neo4j."""
        if self.driver:
            self.driver.close()
            
    def create_constraints(self):
        """Create constraints for the graph database."""
        with self.driver.session() as session:
            # Create constraints for unique IDs
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.skill_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (j:Job) REQUIRE j.job_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Candidate) REQUIRE c.resume_id IS UNIQUE")
            
    def add_skill(self, skill_data):
        """Add a skill node to the graph."""
        with self.driver.session() as session:
            session.run("""
                MERGE (s:Skill {skill_id: $skill_id})
                SET s.name = $name,
                    s.category = $category,
                    s.domain = $domain
            """, skill_data)
            
    def add_skill_relationship(self, source_id, target_id, rel_type, weight=1.0):
        """Add a relationship between two skill nodes."""
        with self.driver.session() as session:
            session.run("""
                MATCH (s1:Skill {skill_id: $source_id})
                MATCH (s2:Skill {skill_id: $target_id})
                MERGE (s1)-[r:`%s` {weight: $weight}]->(s2)
            """ % rel_type, {"source_id": source_id, "target_id": target_id, "weight": weight})
            
    def add_job(self, job_data):
        """Add a job node to the graph."""
        with self.driver.session() as session:
            session.run("""
                MERGE (j:Job {job_id: $job_id})
                SET j.title = $title,
                    j.company = $company,
                    j.domain = $domain,
                    j.location = $location,
                    j.description = $description,
                    j.responsibilities = $responsibilities,
                    j.qualifications = $qualifications
            """, {
                "job_id": job_data["job_id"],
                "title": job_data["title"],
                "company": job_data["company"],
                "domain": job_data.get("domain", ""),
                "location": job_data.get("location", ""),
                "description": job_data.get("summary", ""),
                "responsibilities": self._process_text_list(job_data.get("responsibilities", [])),
                "qualifications": self._process_text_list(job_data.get("qualifications", []))
            })
            
    def add_job_skill(self, job_id, skill_id, proficiency, importance, is_primary=True):
        """Add a skill requirement to a job."""
        rel_type = "REQUIRES_PRIMARY" if is_primary else "REQUIRES_SECONDARY"
        with self.driver.session() as session:
            session.run("""
                MATCH (j:Job {job_id: $job_id})
                MATCH (s:Skill {skill_id: $skill_id})
                MERGE (j)-[r:`%s`]->(s)
                SET r.proficiency = $proficiency,
                    r.importance = $importance
            """ % rel_type, {
                "job_id": job_id,
                "skill_id": skill_id,
                "proficiency": proficiency,
                "importance": importance
            })
            
    def add_candidate(self, resume_data):
        """Add a candidate node to the graph."""
        with self.driver.session() as session:
            session.run("""
                MERGE (c:Candidate {resume_id: $resume_id})
                SET c.name = $name,
                    c.email = $email,
                    c.title = $title,
                    c.domain = $domain,
                    c.location = $location,
                    c.summary = $summary,
                    c.education = $education
            """, {
                "resume_id": resume_data["resume_id"],
                "name": resume_data["name"],
                "email": resume_data.get("email", ""),
                "title": resume_data.get("title", ""),
                "domain": resume_data.get("domain", ""),  # Get domain directly from resume_data
                "location": resume_data.get("location", ""),
                "summary": resume_data.get("summary", ""),
                "education": self._process_education(resume_data.get("education", []))
            })
            
            # Add experience as separate nodes with relationships
            self._add_candidate_experiences(resume_data["resume_id"], resume_data.get("experience", []))
            
    def _add_candidate_experiences(self, resume_id, experiences):
        """Add experience nodes and link them to the candidate."""
        if not experiences:
            return
        
        with self.driver.session() as session:
            for i, exp in enumerate(experiences):
                # Create unique ID for the experience
                exp_id = f"{resume_id}_exp_{i}"
                
                # Create the experience node
                session.run("""
                    MERGE (e:Experience {exp_id: $exp_id})
                    SET e.job_title = $job_title,
                        e.company = $company,
                        e.start_date = $start_date,
                        e.end_date = $end_date,
                        e.description = $description
                """, {
                    "exp_id": exp_id,
                    "job_title": exp.get("job_title", ""),
                    "company": exp.get("company", ""),
                    "start_date": exp.get("start_date", ""),
                    "end_date": exp.get("end_date", "Present"),
                    "description": self._process_text_list(exp.get("description", []))
                })
                
                # Link the experience to the candidate
                session.run("""
                    MATCH (c:Candidate {resume_id: $resume_id})
                    MATCH (e:Experience {exp_id: $exp_id})
                    MERGE (c)-[r:HAS_EXPERIENCE]->(e)
                """, {
                    "resume_id": resume_id,
                    "exp_id": exp_id
                })
                
                # If there are skills used in this experience, link them
                if "skills_used" in exp and exp["skills_used"]:
                    skills_used = exp["skills_used"]
                    if isinstance(skills_used, list):
                        for skill_name in skills_used:
                            # Try to find the skill by name (case insensitive)
                            skill_result = session.run("""
                                MATCH (s:Skill)
                                WHERE toLower(s.name) = toLower($skill_name)
                                RETURN s.skill_id as skill_id
                            """, {"skill_name": skill_name})
                            
                            # If skill found, create the relationship
                            skill_record = skill_result.single()
                            if skill_record:
                                session.run("""
                                    MATCH (e:Experience {exp_id: $exp_id})
                                    MATCH (s:Skill {skill_id: $skill_id})
                                    MERGE (e)-[r:USED_SKILL]->(s)
                                """, {
                                    "exp_id": exp_id,
                                    "skill_id": skill_record["skill_id"]
                                })
                                
    def get_candidate_experiences(self, resume_id):
        """Get all experiences for a candidate with their associated skills."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})-[:HAS_EXPERIENCE]->(e:Experience)
                OPTIONAL MATCH (e)-[:USED_SKILL]->(s:Skill)
                WITH e, collect(DISTINCT {skill_id: s.skill_id, name: s.name, category: s.category}) as skills
                RETURN e.exp_id as exp_id,
                       e.job_title as job_title,
                       e.company as company,
                       e.start_date as start_date,
                       e.end_date as end_date, 
                       e.description as description,
                       skills
                ORDER BY 
                    CASE 
                        WHEN e.end_date = 'Present' THEN 1 
                        ELSE 0 
                    END DESC,
                    e.start_date DESC
            """, {"resume_id": resume_id})
            
            experiences = []
            for record in result:
                exp_data = dict(record)
                
                # Convert description back from JSON string if needed
                if exp_data["description"] and isinstance(exp_data["description"], str):
                    try:
                        import json
                        exp_data["description"] = json.loads(exp_data["description"])
                    except:
                        # If it's not valid JSON, keep as is
                        pass
                
                # Filter out any null skills (from the OPTIONAL MATCH)
                exp_data["skills"] = [s for s in exp_data["skills"] if s["skill_id"] is not None]
                experiences.append(exp_data)
                
            return experiences
            
    def add_candidate_skill(self, resume_id, skill_id, proficiency, experience_years, is_core=True):
        """Add a skill to a candidate."""
        rel_type = "HAS_CORE_SKILL" if is_core else "HAS_SECONDARY_SKILL"
        with self.driver.session() as session:
            session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})
                MATCH (s:Skill {skill_id: $skill_id})
                MERGE (c)-[r:`%s`]->(s)
                SET r.proficiency = $proficiency,
                    r.experience_years = $experience_years
            """ % rel_type, {
                "resume_id": resume_id,
                "skill_id": skill_id,
                "proficiency": proficiency,
                "experience_years": experience_years
            })
            
    def find_matching_candidates(self, job_id, limit=10):
        """Find candidates matching a job based on skill graph analysis."""
        with self.driver.session() as session:
            result = session.run("""
                // Match primary skills
                MATCH (j:Job {job_id: $job_id})-[r1:REQUIRES_PRIMARY]->(s:Skill)<-[r2:HAS_CORE_SKILL]-(c:Candidate)
                
                // Calculate primary skill match score
                WITH c, count(s) AS primaryMatchCount, 
                     sum(r1.importance * CASE r2.proficiency 
                        WHEN 'beginner' THEN 0.25
                        WHEN 'intermediate' THEN 0.5
                        WHEN 'advanced' THEN 0.75
                        WHEN 'expert' THEN 1.0
                        ELSE 0.5 END) AS primaryScore
                
                // Match secondary skills with lower weight (0.5 factor)
                OPTIONAL MATCH (j)-[r3:REQUIRES_SECONDARY]->(s2:Skill)<-[r4:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(c)
                
                WITH c, primaryMatchCount,
                     primaryScore,
                     count(s2) AS secondaryMatchCount,
                     sum(CASE
                        WHEN r3 IS NOT NULL AND r4 IS NOT NULL 
                        THEN r3.importance * 0.5 * CASE r4.proficiency 
                            WHEN 'beginner' THEN 0.25
                            WHEN 'intermediate' THEN 0.5
                            WHEN 'advanced' THEN 0.75
                            WHEN 'expert' THEN 1.0
                            ELSE 0.5 END
                        ELSE 0
                     END) AS secondaryScore
                
                // Match related skills with even lower weight (0.25 factor)
                OPTIONAL MATCH (j)-[r5:REQUIRES_PRIMARY]->(s3:Skill)-[:related_to]-(s4:Skill)<-[r6:HAS_CORE_SKILL]-(c)
                WHERE NOT (j)-[:REQUIRES_PRIMARY|REQUIRES_SECONDARY]->(s4)
                
                WITH c, primaryMatchCount, secondaryMatchCount,
                     primaryScore, secondaryScore,
                     count(DISTINCT s4) AS relatedMatchCount,
                     sum(DISTINCT CASE
                        WHEN r5 IS NOT NULL AND r6 IS NOT NULL 
                        THEN r5.importance * 0.25 * CASE r6.proficiency 
                            WHEN 'beginner' THEN 0.25
                            WHEN 'intermediate' THEN 0.5
                            WHEN 'advanced' THEN 0.75
                            WHEN 'expert' THEN 1.0
                            ELSE 0.5 END
                        ELSE 0
                     END) AS relatedScore
                
                RETURN c.resume_id AS resume_id, c.name AS name, c.title AS title, 
                       primaryMatchCount, secondaryMatchCount, relatedMatchCount,
                       primaryScore, secondaryScore, relatedScore,
                       primaryScore + secondaryScore + relatedScore AS matchScore
                ORDER BY matchScore DESC
                LIMIT $limit
            """, {"job_id": job_id, "limit": limit})
            
            return [dict(record) for record in result]
            
    def find_matching_jobs(self, resume_id, limit=10):
        """Find jobs matching a candidate based on skill graph analysis."""
        with self.driver.session() as session:
            result = session.run("""
                // Match primary skills
                MATCH (c:Candidate {resume_id: $resume_id})-[r1:HAS_CORE_SKILL]->(s:Skill)<-[r2:REQUIRES_PRIMARY]-(j:Job)
                
                // Calculate primary skill match score
                WITH j, count(s) AS primaryMatchCount, 
                     sum(r2.importance * CASE r1.proficiency 
                        WHEN 'beginner' THEN 0.25
                        WHEN 'intermediate' THEN 0.5
                        WHEN 'advanced' THEN 0.75
                        WHEN 'expert' THEN 1.0
                        ELSE 0.5 END) AS primaryScore
                
                // Match secondary skills with lower weight (0.5 factor)
                OPTIONAL MATCH (c)-[r3:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(s2:Skill)<-[r4:REQUIRES_SECONDARY]-(j)
                
                WITH j, primaryMatchCount,
                     primaryScore,
                     count(s2) AS secondaryMatchCount,
                     sum(CASE
                        WHEN r3 IS NOT NULL AND r4 IS NOT NULL 
                        THEN r4.importance * 0.5 * CASE r3.proficiency 
                            WHEN 'beginner' THEN 0.25
                            WHEN 'intermediate' THEN 0.5
                            WHEN 'advanced' THEN 0.75
                            WHEN 'expert' THEN 1.0
                            ELSE 0.5 END
                        ELSE 0
                     END) AS secondaryScore
                
                // Match related skills with even lower weight (0.25 factor)
                OPTIONAL MATCH (c)-[r5:HAS_CORE_SKILL]->(s3:Skill)-[:related_to]-(s4:Skill)<-[r6:REQUIRES_PRIMARY]-(j)
                WHERE NOT (c)-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(s4)
                
                WITH j, primaryMatchCount, secondaryMatchCount,
                     primaryScore, secondaryScore,
                     count(DISTINCT s4) AS relatedMatchCount,
                     sum(DISTINCT CASE
                        WHEN r5 IS NOT NULL AND r6 IS NOT NULL 
                        THEN r6.importance * 0.25 * CASE r5.proficiency 
                            WHEN 'beginner' THEN 0.25
                            WHEN 'intermediate' THEN 0.5
                            WHEN 'advanced' THEN 0.75
                            WHEN 'expert' THEN 1.0
                            ELSE 0.5 END
                        ELSE 0
                     END) AS relatedScore
                
                RETURN j.job_id AS job_id, j.title AS title, j.company AS company,
                       primaryMatchCount, secondaryMatchCount, relatedMatchCount,
                       primaryScore, secondaryScore, relatedScore,
                       primaryScore + secondaryScore + relatedScore AS matchScore
                ORDER BY matchScore DESC
                LIMIT $limit
            """, {"resume_id": resume_id, "limit": limit})
            
            return [dict(record) for record in result]
            
    def recommend_skills(self, resume_id, limit=5):
        """Recommend skills for a candidate to learn based on job market demands."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})-[:HAS_CORE_SKILL]->(s1:Skill)
                MATCH (s1)-[:RELATED_TO|COMPLEMENTARY_TO]->(s2:Skill)
                WHERE NOT (c)-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(s2)
                WITH s2, count(s1) as relevance
                MATCH (j:Job)-[:REQUIRES_PRIMARY]->(s2)
                RETURN s2.skill_id as skill_id, s2.name as name, count(j) as job_demand, 
                       relevance, count(j) * relevance as score
                ORDER BY score DESC
                LIMIT $limit
            """, {"resume_id": resume_id, "limit": limit})
            
            return [dict(record) for record in result]
            
    def _process_text_list(self, text_list):
        """Process a list of text items into a JSON string to preserve array structure."""
        if not text_list:
            return "[]"
        
        if isinstance(text_list, list):
            import json
            return json.dumps(text_list)
        
        # If it's not a list but a single string, convert it to a list with one item
        import json
        return json.dumps([str(text_list)])
    
    def _process_experience(self, experience_list):
        """Process experience list into a formatted string."""
        if not experience_list:
            return ""
        
        result = []
        for exp in experience_list:
            job_desc = ""
            if "description" in exp and isinstance(exp["description"], list):
                job_desc = "\n- " + "\n- ".join(exp["description"])
            elif "description" in exp:
                job_desc = "\n" + str(exp["description"])
                
            entry = f"{exp.get('job_title', 'Job')} at {exp.get('company', 'Company')} " \
                   f"({exp.get('start_date', '')} - {exp.get('end_date', 'Present')}){job_desc}"
            result.append(entry)
            
        return "\n\n".join(result)
    
    def _process_education(self, education_list):
        """Process education list into a formatted string."""
        if not education_list:
            return ""
        
        result = []
        for edu in education_list:
            entry = f"{edu.get('degree', 'Degree')} from {edu.get('institution', 'Institution')} " \
                   f"({edu.get('graduation_year', '')})"
            result.append(entry)
            
        return "\n".join(result)
    
    def generate_embeddings(self):
        """Generate and store text embeddings for experiences and job descriptions."""
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight model
        except ImportError:
            print("Error: sentence-transformers package not installed.")
            print("Please install with: pip install sentence-transformers")
            return False
        
        print("Generating embeddings for experiences and job descriptions...")
        with self.driver.session() as session:
            # Process experiences
            print("Processing experience embeddings...")
            experiences = session.run("""
                MATCH (e:Experience)
                RETURN e.exp_id as exp_id, e.description as description
            """)
            
            exp_count = 0
            for exp in experiences:
                if exp["description"]:
                    # Parse the JSON string back to a list if needed
                    desc_text = exp["description"]
                    if isinstance(desc_text, str):
                        try:
                            import json
                            desc_text = json.loads(desc_text)
                        except:
                            desc_text = [desc_text]
                    
                    # Join the description items to create a single text
                    if isinstance(desc_text, list):
                        full_text = " ".join(desc_text)
                    else:
                        full_text = str(desc_text)
                    
                    # Generate embedding
                    embedding = model.encode(full_text)
                    
                    # Store the embedding in Neo4j
                    session.run("""
                        MATCH (e:Experience {exp_id: $exp_id})
                        SET e.text_embedding = $embedding
                    """, {"exp_id": exp["exp_id"], "embedding": embedding.tolist()})
                    exp_count += 1
                    
            print(f"Generated embeddings for {exp_count} experiences")
            
            # Process jobs
            print("Processing job embeddings...")
            jobs = session.run("""
                MATCH (j:Job)
                RETURN j.job_id as job_id, j.responsibilities as responsibilities,
                       j.qualifications as qualifications, j.description as description
            """)
            
            job_count = 0
            for job in jobs:
                # Combine job text from various fields
                job_text = []
                if job["responsibilities"]:
                    job_text.extend(job["responsibilities"] if isinstance(job["responsibilities"], list) else [job["responsibilities"]])
                if job["qualifications"]:
                    job_text.extend(job["qualifications"] if isinstance(job["qualifications"], list) else [job["qualifications"]])
                if job["description"]:
                    job_text.append(job["description"] if isinstance(job["description"], str) else " ".join(job["description"]))
                
                if job_text:
                    full_text = " ".join(job_text)
                    
                    # Generate embedding
                    embedding = model.encode(full_text)
                    
                    # Store the embedding
                    session.run("""
                        MATCH (j:Job {job_id: $job_id})
                        SET j.text_embedding = $embedding
                    """, {"job_id": job["job_id"], "embedding": embedding.tolist()})
                    job_count += 1
                    
            print(f"Generated embeddings for {job_count} jobs")
            return True

    def find_matching_candidates_enhanced(self, job_id, limit=10, weights=None):
        """Find candidates matching a job with enhanced algorithm including
        skill matching, location matching, and semantic text matching."""
        
        # Default weights if not provided (domain removed)
        if weights is None:
            weights = {
                "skills": 0.75,
                "location": 0.15,
                "semantic": 0.1
            }
        
        with self.driver.session() as session:
            # Check if job exists
            job_check = session.run("""
                MATCH (j:Job {job_id: $job_id})
                RETURN COUNT(j) > 0 as exists
            """, {"job_id": job_id})
            
            if not job_check.single()["exists"]:
                return []
            
            # Run the enhanced matching query
            query = """
                // Match the job
                MATCH (j:Job {job_id: $job_id})
                
                // Match all candidates to get a starting set
                MATCH (c:Candidate)
                
                // Primary skill matching
                OPTIONAL MATCH (j)-[r1:REQUIRES_PRIMARY]->(s1:Skill)<-[r2:HAS_CORE_SKILL]-(c)
                WITH j, c, 
                     COLLECT({skill: s1.name, importance: r1.importance, proficiency: r2.proficiency}) as primaryMatches,
                     COUNT(s1) AS primaryMatchCount
                
                // Calculate primary skill score
                WITH j, c, primaryMatches, primaryMatchCount,
                     SUM(CASE 
                        WHEN primaryMatches IS NULL THEN 0
                        ELSE REDUCE(score = 0.0, match IN primaryMatches | 
                             score + (1.0 * match.importance * CASE match.proficiency 
                                                        WHEN 'beginner' THEN 0.25
                                                        WHEN 'intermediate' THEN 0.5
                                                        WHEN 'advanced' THEN 0.75
                                                        WHEN 'expert' THEN 1.0
                                                        ELSE 0.5 END))
                     END) AS primaryScore
                
                // Secondary skill matching with lower weight (0.5 factor)
                OPTIONAL MATCH (j)-[r3:REQUIRES_SECONDARY]->(s2:Skill)<-[r4:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(c)
                WITH j, c, primaryMatchCount, primaryScore,
                     COUNT(s2) AS secondaryMatchCount,
                     SUM(CASE
                        WHEN r3 IS NOT NULL AND r4 IS NOT NULL 
                        THEN 1.0 * r3.importance * 0.5 * CASE r4.proficiency 
                            WHEN 'beginner' THEN 0.25
                            WHEN 'intermediate' THEN 0.5
                            WHEN 'advanced' THEN 0.75
                            WHEN 'expert' THEN 1.0
                            ELSE 0.5 END
                        ELSE 0.0
                     END) AS secondaryScore
                
                // Calculate total skill score (normalized to 0-100)
                WITH j, c, 
                     (primaryScore + secondaryScore) * 3 as skillScore
                
                // Add location matching - improved for city/province format
                WITH j, c, skillScore,
                     CASE 
                        WHEN j.location IS NULL OR c.location IS NULL THEN 0
                        WHEN j.location = c.location THEN 100.0  // Exact match
                        // Better partial matching (checks if same city or province)
                        WHEN SPLIT(j.location, ',')[0] = SPLIT(c.location, ',')[0] THEN 80.0  // Same city
                        WHEN SIZE(SPLIT(j.location, ',')) > 1 AND SIZE(SPLIT(c.location, ',')) > 1 
                             AND TRIM(SPLIT(j.location, ',')[1]) = TRIM(SPLIT(c.location, ',')[1]) THEN 50.0  // Same province/state
                        WHEN j.location CONTAINS c.location OR c.location CONTAINS j.location THEN 30.0  // Other partial match
                        ELSE 0.0  // No match
                     END as locationScore
                
                // Semantic experience matching if embeddings exist
                WITH j, c, skillScore, locationScore,
                
                // Use Neo4j native vector functions for semantic matching
                c as candidate, j as job
                OPTIONAL MATCH (candidate)-[:HAS_EXPERIENCE]->(e:Experience)
                WHERE e.text_embedding IS NOT NULL AND job.text_embedding IS NOT NULL
                
                // Calculate cosine similarity between job and each experience
                WITH job, candidate, skillScore, locationScore, e,
                     CASE 
                        WHEN e.text_embedding IS NOT NULL AND job.text_embedding IS NOT NULL
                        THEN vector.similarity.cosine(job.text_embedding, e.text_embedding) * 100
                        ELSE 0
                     END as expSimilarity
                
                // Get the maximum similarity across all experiences
                WITH job as j, candidate as c, skillScore, locationScore,
                     CASE 
                        WHEN MAX(expSimilarity) IS NOT NULL THEN MAX(expSimilarity)
                        ELSE 0
                     END as semanticScore
                
                // Calculate weighted total score
                WITH c, 
                     skillScore * $weights.skills +
                     locationScore * $weights.location + 
                     semanticScore * $weights.semantic AS totalScore,
                     skillScore, locationScore, semanticScore,
                     j

                // Calculate match percentage with proper capping and scaling
                WITH c, totalScore, skillScore, locationScore, semanticScore, j,
                     toInteger(CASE 
                         WHEN totalScore IS NULL THEN 0
                         WHEN totalScore > 100 THEN 100
                         ELSE round(totalScore)
                     END) as match_percentage
                
                // Get actual matching skills
                OPTIONAL MATCH (j)-[:REQUIRES_PRIMARY]->(ps:Skill)<-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(c)
                WITH c, totalScore, skillScore, locationScore, semanticScore, match_percentage,
                     collect(DISTINCT {skill_id: ps.skill_id, name: ps.name, category: ps.category}) as primary_matching_skills
                     
                // Get secondary matching skills
                OPTIONAL MATCH (j)-[:REQUIRES_SECONDARY]->(ss:Skill)<-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(c)
                WITH c, totalScore, skillScore, locationScore, semanticScore, match_percentage,
                     primary_matching_skills,
                     collect(DISTINCT {skill_id: ss.skill_id, name: ss.name, category: ss.category}) as secondary_matching_skills
                
                // Return results sorted by total score
                RETURN c.resume_id AS resume_id, 
                       c.name AS name, 
                       c.title AS title,
                       c.location AS location,
                       c.domain AS domain,
                       skillScore,
                       locationScore,
                       semanticScore,
                       totalScore,
                       primary_matching_skills,
                       secondary_matching_skills,
                       match_percentage
                ORDER BY totalScore DESC
                LIMIT $limit
            """
            
            result = session.run(query, {
                "job_id": job_id, 
                "limit": limit,
                "weights": weights
            })
            
            return [dict(record) for record in result]

    def find_matching_jobs_enhanced(self, resume_id, limit=10, weights=None):
        """Find jobs matching a candidate with enhanced algorithm including
        skill matching, location matching, and semantic text matching."""
        
        # Default weights if not provided (domain removed)
        if weights is None:
            weights = {
                "skills": 0.75,
                "location": 0.15,
                "semantic": 0.1
            }
        
        with self.driver.session() as session:
            # Check if candidate exists
            candidate_check = session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})
                RETURN COUNT(c) > 0 as exists
            """, {"resume_id": resume_id})
            
            if not candidate_check.single()["exists"]:
                return []
            
            # Run the enhanced matching query (similar structure to find_matching_candidates_enhanced)
            query = """
                // Match the candidate
                MATCH (c:Candidate {resume_id: $resume_id})
                
                // Match all jobs to get a starting set
                MATCH (j:Job)
                
                // Primary skill matching
                OPTIONAL MATCH (c)-[r1:HAS_CORE_SKILL]->(s1:Skill)<-[r2:REQUIRES_PRIMARY]-(j)
                WITH j, c, 
                     COLLECT({skill: s1.name, importance: r2.importance, proficiency: r1.proficiency}) as primaryMatches,
                     COUNT(s1) AS primaryMatchCount
                
                // Calculate primary skill score
                WITH j, c, primaryMatches, primaryMatchCount,
                     SUM(CASE 
                        WHEN primaryMatches IS NULL THEN 0
                        ELSE REDUCE(score = 0.0, match IN primaryMatches | 
                             score + (1.0 * match.importance * CASE match.proficiency 
                                                        WHEN 'beginner' THEN 0.25
                                                        WHEN 'intermediate' THEN 0.5
                                                        WHEN 'advanced' THEN 0.75
                                                        WHEN 'expert' THEN 1.0
                                                        ELSE 0.5 END))
                     END) AS primaryScore
                
                // Secondary skill matching with lower weight (0.5 factor)
                OPTIONAL MATCH (c)-[r3:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(s2:Skill)<-[r4:REQUIRES_SECONDARY]-(j)
                WITH j, c, primaryMatchCount, primaryScore,
                     COUNT(s2) AS secondaryMatchCount,
                     SUM(CASE
                        WHEN r3 IS NOT NULL AND r4 IS NOT NULL 
                        THEN 1.0 * r4.importance * 0.5 * CASE r3.proficiency 
                            WHEN 'beginner' THEN 0.25
                            WHEN 'intermediate' THEN 0.5
                            WHEN 'advanced' THEN 0.75
                            WHEN 'expert' THEN 1.0
                            ELSE 0.5 END
                        ELSE 0.0
                     END) AS secondaryScore
                
                // Calculate total skill score (normalized to 0-100)
                WITH j, c, 
                     (primaryScore + secondaryScore) * 3 as skillScore
                
                // Add location matching - improved for city/province format
                WITH j, c, skillScore,
                     CASE 
                        WHEN j.location IS NULL OR c.location IS NULL THEN 0
                        WHEN j.location = c.location THEN 100.0  // Exact match
                        // Better partial matching (checks if same city or province)
                        WHEN SPLIT(j.location, ',')[0] = SPLIT(c.location, ',')[0] THEN 80.0  // Same city
                        WHEN SIZE(SPLIT(j.location, ',')) > 1 AND SIZE(SPLIT(c.location, ',')) > 1 
                             AND TRIM(SPLIT(j.location, ',')[1]) = TRIM(SPLIT(c.location, ',')[1]) THEN 50.0  // Same province/state
                        WHEN j.location CONTAINS c.location OR c.location CONTAINS j.location THEN 30.0  // Other partial match
                        ELSE 0.0  // No match
                     END as locationScore
                
                // Semantic experience matching if embeddings exist
                WITH j, c, skillScore, locationScore,
                
                // Use Neo4j native vector functions for semantic matching
                c as candidate, j as job
                OPTIONAL MATCH (candidate)-[:HAS_EXPERIENCE]->(e:Experience)
                WHERE e.text_embedding IS NOT NULL AND job.text_embedding IS NOT NULL
                
                // Calculate cosine similarity between job and each experience
                WITH job, candidate, skillScore, locationScore, e,
                     CASE 
                        WHEN e.text_embedding IS NOT NULL AND job.text_embedding IS NOT NULL
                        THEN vector.similarity.cosine(job.text_embedding, e.text_embedding) * 100
                        ELSE 0
                     END as expSimilarity
                
                // Get the maximum similarity across all experiences
                WITH job as j, candidate as c, skillScore, locationScore,
                     CASE 
                        WHEN MAX(expSimilarity) IS NOT NULL THEN MAX(expSimilarity)
                        ELSE 0
                     END as semanticScore
                
                // Calculate weighted total score
                WITH j, c, 
                     skillScore * $weights.skills +
                     locationScore * $weights.location + 
                     semanticScore * $weights.semantic AS totalScore,
                     skillScore, locationScore, semanticScore
                
                // Calculate match percentage with proper capping and scaling
                WITH j, totalScore, skillScore, locationScore, semanticScore,
                     toInteger(CASE 
                         WHEN totalScore IS NULL THEN 0
                         WHEN totalScore > 100 THEN 100
                         ELSE round(totalScore)
                     END) as match_percentage
                
                // Get primary matching skills
                OPTIONAL MATCH (c)-[:HAS_CORE_SKILL]->(ps:Skill)<-[:REQUIRES_PRIMARY]-(j)
                WITH j, totalScore, skillScore, locationScore, semanticScore, match_percentage,
                     collect(DISTINCT {skill_id: ps.skill_id, name: ps.name, category: ps.category}) as primary_matching_skills
                     
                // Get secondary matching skills
                OPTIONAL MATCH (c)-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(ss:Skill)<-[:REQUIRES_SECONDARY]-(j)
                WITH j, totalScore, skillScore, locationScore, semanticScore, match_percentage,
                     primary_matching_skills,
                     collect(DISTINCT {skill_id: ss.skill_id, name: ss.name, category: ss.category}) as secondary_matching_skills
                
                // Return results sorted by total score
                RETURN j.job_id AS job_id, 
                       j.title AS title, 
                       j.company AS company,
                       j.location AS location,
                       j.domain AS domain,
                       skillScore,
                       locationScore,
                       semanticScore,
                       totalScore,
                       primary_matching_skills,
                       secondary_matching_skills,
                       match_percentage
                ORDER BY totalScore DESC
                LIMIT $limit
            """
            
            result = session.run(query, {
                "resume_id": resume_id, 
                "limit": limit,
                "weights": weights
            })
            
            return [dict(record) for record in result] 