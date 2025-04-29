"""
Candidate Repository for Knowledge Graph
This module provides candidate-related database operations.
"""

from src.backend.repositories.base.repository import BaseRepository
import json
import uuid

class CandidateRepository(BaseRepository):
    """Repository for candidate-related operations in the knowledge graph."""
    
    def add_candidate(self, resume_data):
        """Add a candidate node to the graph.
        
        Args:
            resume_data: Dictionary containing candidate information
            
        Returns:
            resume_id of the created candidate
        """
        # Generate resume_id if not provided
        if "resume_id" not in resume_data:
            resume_data["resume_id"] = f"resume_{str(uuid.uuid4())[:8]}"
            
        query = """
            MERGE (c:Candidate {resume_id: $resume_id})
            SET c.name = $name,
                c.email = $email,
                c.title = $title,
                c.domain = $domain,
                c.location = $location,
                c.summary = $summary,
                c.education = $education
            RETURN c.resume_id as resume_id
        """
        
        parameters = {
            "resume_id": resume_data["resume_id"],
            "name": resume_data["name"],
            "email": resume_data.get("email", ""),
            "title": resume_data.get("title", ""),
            "domain": resume_data.get("domain", ""),
            "location": resume_data.get("location", ""),
            "summary": resume_data.get("summary", ""),
            "education": self._process_education(resume_data.get("education", []))
        }
        
        self.execute_write_query(query, parameters)
        
        # Add experiences as separate nodes with relationships
        if "experience" in resume_data:
            self._add_candidate_experiences(resume_data["resume_id"], resume_data["experience"])
        
        return resume_data["resume_id"]
    
    def add_candidate_experience(self, resume_id, experience_id, title, company, start_date, end_date, description, location=None):
        """Add an experience to a candidate.
        
        Args:
            resume_id: ID of the candidate
            experience_id: ID of the experience
            title: Job title
            company: Company name
            start_date: Start date of experience (datetime)
            end_date: End date of experience (datetime or 'Present')
            description: Job description
            location: Job location
            
        Returns:
            True if successful
        """
        # Format dates
        start_date_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, 'strftime') else start_date
        end_date_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, 'strftime') else end_date
        
        # Create the experience node and link to candidate in one query
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})
            MERGE (e:Experience {experience_id: $experience_id})
            SET e.title = $title,
                e.company = $company,
                e.start_date = $start_date,
                e.end_date = $end_date,
                e.description = $description,
                e.location = $location
            MERGE (c)-[r:HAS_EXPERIENCE]->(e)
        """
        
        parameters = {
            "resume_id": resume_id,
            "experience_id": experience_id,
            "title": title,
            "company": company,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "description": description,
            "location": location or ""
        }
        
        self.execute_write_query(query, parameters)
        return True
    
    def add_candidate_education(self, resume_id, education_id, institution, degree, field, start_date, end_date, gpa=None):
        """Add education to a candidate.
        
        Args:
            resume_id: ID of the candidate
            education_id: ID of the education entry
            institution: Educational institution name
            degree: Degree type
            field: Field of study
            start_date: Start date (datetime)
            end_date: End date (datetime)
            gpa: Grade Point Average (optional)
            
        Returns:
            True if successful
        """
        # Format dates
        start_date_str = start_date.strftime("%Y-%m-%d") if hasattr(start_date, 'strftime') else start_date
        end_date_str = end_date.strftime("%Y-%m-%d") if hasattr(end_date, 'strftime') else end_date
        
        # Create the education node and link to candidate in one query
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})
            MERGE (e:Education {education_id: $education_id})
            SET e.institution = $institution,
                e.degree = $degree,
                e.field = $field,
                e.start_date = $start_date,
                e.end_date = $end_date,
                e.gpa = $gpa
            MERGE (c)-[r:HAS_EDUCATION]->(e)
        """
        
        parameters = {
            "resume_id": resume_id,
            "education_id": education_id,
            "institution": institution,
            "degree": degree,
            "field": field,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "gpa": gpa
        }
        
        self.execute_write_query(query, parameters)
        return True
    
    def _add_candidate_experiences(self, resume_id, experiences):
        """Add experience nodes and link them to the candidate.
        
        Args:
            resume_id: ID of the candidate resume
            experiences: List of experience dictionaries
            
        Returns:
            True if successful
        """
        if not experiences:
            return False
        
        for i, exp in enumerate(experiences):
            # Create unique ID for the experience
            exp_id = f"{resume_id}_exp_{i}"
            
            # Create the experience node
            query = """
                MERGE (e:Experience {exp_id: $exp_id})
                SET e.job_title = $job_title,
                    e.company = $company,
                    e.start_date = $start_date,
                    e.end_date = $end_date,
                    e.description = $description
            """
            
            parameters = {
                "exp_id": exp_id,
                "job_title": exp.get("job_title", ""),
                "company": exp.get("company", ""),
                "start_date": exp.get("start_date", ""),
                "end_date": exp.get("end_date", "Present"),
                "description": self._process_text_list(exp.get("description", []))
            }
            
            self.execute_write_query(query, parameters)
            
            # Link the experience to the candidate
            link_query = """
                MATCH (c:Candidate {resume_id: $resume_id})
                MATCH (e:Experience {exp_id: $exp_id})
                MERGE (c)-[r:HAS_EXPERIENCE]->(e)
            """
            
            self.execute_write_query(link_query, {
                "resume_id": resume_id,
                "exp_id": exp_id
            })
            
            # If there are skills used in this experience, link them
            if "skills_used" in exp and exp["skills_used"]:
                self._link_experience_skills(exp_id, exp["skills_used"])
        
        return True
    
    def _link_experience_skills(self, exp_id, skills_used):
        """Link skills to an experience.
        
        Args:
            exp_id: ID of the experience
            skills_used: List of skill names or IDs
        """
        if not isinstance(skills_used, list):
            return
            
        for skill_name in skills_used:
            # Try to find the skill by name (case insensitive)
            skill_query = """
                MATCH (s:Skill)
                WHERE toLower(s.name) = toLower($skill_name)
                RETURN s.skill_id as skill_id
            """
            
            skill_results = self.execute_read_query(skill_query, {"skill_name": skill_name})
            
            # If skill found, create the relationship
            if skill_results and skill_results[0]:
                link_query = """
                    MATCH (e:Experience {exp_id: $exp_id})
                    MATCH (s:Skill {skill_id: $skill_id})
                    MERGE (e)-[r:USED_SKILL]->(s)
                """
                
                self.execute_write_query(link_query, {
                    "exp_id": exp_id,
                    "skill_id": skill_results[0]["skill_id"]
                })
    
    def add_candidate_skill(self, resume_id, skill_id, proficiency, experience_years, is_core=True):
        """Add a skill to a candidate.
        
        Args:
            resume_id: ID of the candidate
            skill_id: ID of the skill
            proficiency: Proficiency level
            experience_years: Years of experience
            is_core: Whether this is a core skill
            
        Returns:
            True if successful
        """
        rel_type = "HAS_CORE_SKILL" if is_core else "HAS_SECONDARY_SKILL"
        
        query = f"""
            MATCH (c:Candidate {{resume_id: $resume_id}})
            MATCH (s:Skill {{skill_id: $skill_id}})
            MERGE (c)-[r:`{rel_type}`]->(s)
            SET r.proficiency = $proficiency,
                r.experience_years = $experience_years
        """
        
        parameters = {
            "resume_id": resume_id,
            "skill_id": skill_id,
            "proficiency": proficiency,
            "experience_years": experience_years
        }
        
        self.execute_write_query(query, parameters)
        return True
    
    def get_candidate_experiences(self, resume_id):
        """Get all experiences for a candidate with their associated skills.
        
        Args:
            resume_id: ID of the candidate
            
        Returns:
            List of experiences with skills
        """
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})-[:HAS_EXPERIENCE]->(e:Experience)
            OPTIONAL MATCH (e)-[:USED_SKILL]->(s:Skill)
            WITH e, collect(DISTINCT {skill_id: s.skill_id, name: s.name, category: s.category}) as skills
            RETURN e.experience_id as experience_id,
                   e.title as title,
                   e.company as company,
                   e.start_date as start_date,
                   e.end_date as end_date, 
                   e.description as description,
                   e.location as location,
                   skills
            ORDER BY 
                CASE 
                    WHEN e.end_date = 'Present' THEN 1 
                    ELSE 0 
                END DESC,
                e.start_date DESC
        """
        
        results = self.execute_read_query(query, {"resume_id": resume_id})
        
        experiences = []
        for exp_data in results:
            # Convert description back from JSON string if needed
            if exp_data.get("description") and isinstance(exp_data["description"], str):
                try:
                    exp_data["description"] = json.loads(exp_data["description"])
                except:
                    # If it's not valid JSON, keep as is
                    pass
            
            # Filter out any null skills (from the OPTIONAL MATCH) if skills field exists
            if "skills" in exp_data:
                exp_data["skills"] = [s for s in exp_data["skills"] if s["skill_id"] is not None]
                
            experiences.append(exp_data)
            
        return experiences
    
    def get_candidate(self, resume_id):
        """Get a candidate by ID.
        
        Args:
            resume_id: ID of the candidate
            
        Returns:
            Candidate data as dictionary or None if not found
        """
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})
            RETURN c.resume_id as resume_id, 
                   c.name as name, 
                   c.title as title,
                   c.location as location, 
                   c.domain as domain,
                   c.email as email,
                   c.summary as summary,
                   c.education as education
        """
        
        results = self.execute_read_query(query, {"resume_id": resume_id})
        if not results:
            return None
            
        return results[0]
    
    def get_candidate_skills(self, resume_id):
        """Get skills for a candidate.
        
        Args:
            resume_id: ID of the candidate
            
        Returns:
            List of skills with relationship properties
        """
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})-[r]->(s:Skill)
            RETURN s.skill_id as skill_id, s.name as name, 
                   s.category as category, r.level as level, 
                   r.experience_years as experience_years,
                   r.years as years,
                   r.proficiency as proficiency,
                   type(r) as relationship_type
            ORDER BY COALESCE(r.level, 0) DESC, COALESCE(r.experience_years, r.years, 0) DESC, s.name
        """
        
        return self.execute_read_query(query, {"resume_id": resume_id})
    
    def get_candidate_education(self, resume_id):
        """Get education history for a candidate.
        
        Args:
            resume_id: ID of the candidate
            
        Returns:
            List of education entries
        """
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})-[:HAS_EDUCATION]->(e:Education)
            RETURN e.education_id as education_id,
                  e.institution as institution,
                  e.degree as degree,
                  e.field as field,
                  e.start_date as start_date,
                  e.end_date as end_date,
                  e.gpa as gpa
            ORDER BY e.end_date DESC
        """
        
        return self.execute_read_query(query, {"resume_id": resume_id})
    
    def find_matching_jobs(self, resume_id, limit=10):
        """Find jobs matching a candidate based on skill graph analysis.
        
        Args:
            resume_id: ID of the candidate
            limit: Maximum number of results to return
            
        Returns:
            List of job matches with scores
        """
        query = """
            // Match primary skills
            MATCH (c:Candidate {resume_id: $resume_id})-[r1:HAS_CORE_SKILL]->(s:Skill)<-[r2:REQUIRES_PRIMARY]-(j:Job)
            
            // Calculate primary skill match score
            WITH j, c, count(s) AS primaryMatchCount, 
                 sum(r2.importance * CASE r1.proficiency 
                    WHEN 'beginner' THEN 0.25
                    WHEN 'intermediate' THEN 0.5
                    WHEN 'advanced' THEN 0.75
                    WHEN 'expert' THEN 1.0
                    ELSE 0.5 END) AS primaryScore
            
            // Match secondary skills with lower weight (0.5 factor)
            OPTIONAL MATCH (c)-[r3:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(s2:Skill)<-[r4:REQUIRES_SECONDARY]-(j)
            
            WITH j, c, primaryMatchCount,
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
            
            WITH j, c, primaryMatchCount, secondaryMatchCount,
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
                   c.resume_id AS resume_id,
                   primaryMatchCount, secondaryMatchCount, relatedMatchCount,
                   primaryScore, secondaryScore, relatedScore,
                   primaryScore + secondaryScore + relatedScore AS matchScore
            ORDER BY matchScore DESC
            LIMIT $limit
        """
        
        return self.execute_read_query(query, {"resume_id": resume_id, "limit": limit})
    
    def find_matching_jobs_enhanced(self, resume_id, limit=10, weights=None):
        """Find jobs matching a candidate with enhanced algorithm including
        skill matching, location matching, and semantic text matching.
        
        Args:
            resume_id: ID of the candidate
            limit: Maximum number of results to return
            weights: Dictionary of weights for different matching aspects
            
        Returns:
            List of job matches with detailed scores
        """
        # Default weights if not provided
        if weights is None:
            weights = {
                "skills": 0.75,
                "location": 0.15,
                "semantic": 0.1
            }
        
        # First check if candidate exists
        candidate_check_query = """
            MATCH (c:Candidate {resume_id: $resume_id})
            RETURN COUNT(c) > 0 as exists
        """
        
        candidate_exists = self.execute_read_query(candidate_check_query, {"resume_id": resume_id})
        
        if not candidate_exists or not candidate_exists[0]["exists"]:
            return []
        
        # Run the enhanced matching query
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
        
        return self.execute_read_query(query, {
            "resume_id": resume_id, 
            "limit": limit,
            "weights": weights
        })
    
    def _process_text_list(self, text_list):
        """Process a list of text items into a JSON string to preserve array structure."""
        if not text_list:
            return "[]"
        
        if isinstance(text_list, list):
            return json.dumps(text_list)
        
        # If it's not a list but a single string, convert it to a list with one item
        return json.dumps([str(text_list)])
    
    def _process_education(self, education_list):
        """Process education data into a JSON string."""
        if not education_list:
            return "[]"
            
        if isinstance(education_list, list):
            return json.dumps(education_list)
            
        # If it's already a JSON string, return as is
        if isinstance(education_list, str):
            try:
                json.loads(education_list)
                return education_list
            except:
                pass
                
        # Last resort: convert to JSON array with single item
        return json.dumps([education_list])
    
    def find_candidates(self, filters=None, limit=20, offset=0):
        """Find candidates matching specified filters.
        
        Args:
            filters: Dictionary containing filter criteria
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            List of candidates matching the filters
        """
        # Prepare WHERE clauses based on filters
        where_clauses = []
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if filters:
            # Handle domain filter
            if 'domain' in filters and filters['domain']:
                where_clauses.append("c.domain = $domain")
                params['domain'] = filters['domain']
            
            # Handle location filter
            if 'location' in filters and filters['location']:
                where_clauses.append("c.location = $location")
                params['location'] = filters['location']
            
            # Handle title filter
            if 'title' in filters and filters['title']:
                where_clauses.append("c.title = $title")
                params['title'] = filters['title']
                
            # Handle skill filter
            if 'skill' in filters and filters['skill']:
                where_clauses.append("(c)-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(:Skill {name: $skill})")
                params['skill'] = filters['skill']
        
        # Build query
        query = """
            MATCH (c:Candidate)
        """
        
        # Add WHERE clause if there are filters
        if where_clauses:
            query += "WHERE " + " AND ".join(where_clauses)
        
        # Add return statement
        query += """
            RETURN c.resume_id as resume_id, 
                   c.name as name, 
                   c.title as title,
                   c.location as location, 
                   c.domain as domain,
                   c.email as email
            ORDER BY c.name
            SKIP $offset
            LIMIT $limit
        """
        
        print(f"Debug - Executing candidate search query with params: {params}")
        results = self.execute_read_query(query, params)
        print(f"Debug - Found {len(results)} candidates")
        return results
    
    def get_candidate_filter_options(self):
        """Get options for candidate filters.
        
        Returns:
            Dictionary with filter options
        """
        query = """
            MATCH (c:Candidate)
            WITH COLLECT(DISTINCT c.domain) AS domains,
                 COLLECT(DISTINCT c.location) AS locations,
                 COLLECT(DISTINCT c.title) AS titles
            RETURN domains, locations, titles
        """
        
        result = self.execute_read_query(query)
        if not result:
            return {"domains": [], "locations": [], "titles": []}
        
        return {
            "domains": result[0].get("domains", []),
            "locations": result[0].get("locations", []),
            "titles": result[0].get("titles", [])
        }
        
    def update_candidate(self, resume_id, candidate_data):
        """Update a candidate by ID.
        
        Args:
            resume_id: ID of the candidate to update
            candidate_data: Dictionary containing updated candidate data
            
        Returns:
            resume_id of the updated candidate
        """
        # Build SET clause dynamically based on provided fields
        set_clauses = []
        params = {"resume_id": resume_id}
        
        fields_to_update = [
            "name", "email", "title", "domain", "location", "summary", "education"
        ]
        
        for field in fields_to_update:
            if field in candidate_data:
                if field == "education" and isinstance(candidate_data[field], list):
                    set_clauses.append(f"c.{field} = ${field}")
                    params[field] = self._process_education(candidate_data[field])
                else:
                    set_clauses.append(f"c.{field} = ${field}")
                    params[field] = candidate_data[field]
        
        # Only proceed if there are fields to update
        if not set_clauses:
            return resume_id
        
        query = f"""
            MATCH (c:Candidate {{resume_id: $resume_id}})
            SET {", ".join(set_clauses)}
            RETURN c.resume_id as resume_id
        """
        
        self.execute_write_query(query, params)
        return resume_id
        
    def delete_candidate(self, resume_id):
        """Delete a candidate by ID.
        
        Args:
            resume_id: ID of the candidate to delete
            
        Returns:
            True if successful
        """
        # First remove relationships
        self.remove_candidate_skills(resume_id)
        self.remove_candidate_experiences(resume_id)
        self.remove_candidate_education(resume_id)
        
        # Then delete the candidate node
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})
            DETACH DELETE c
        """
        
        self.execute_write_query(query, {"resume_id": resume_id})
        return True
        
    def remove_candidate_skills(self, resume_id):
        """Remove all skills from a candidate.
        
        Args:
            resume_id: ID of the candidate
            
        Returns:
            True if successful
        """
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})-[r:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]->(s:Skill)
            DELETE r
        """
        
        self.execute_write_query(query, {"resume_id": resume_id})
        return True
        
    def remove_candidate_experiences(self, resume_id):
        """Remove all experiences from a candidate.
        
        Args:
            resume_id: ID of the candidate
            
        Returns:
            True if successful
        """
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})-[r:HAS_EXPERIENCE]->(e:Experience)
            DETACH DELETE e
        """
        
        self.execute_write_query(query, {"resume_id": resume_id})
        return True
        
    def remove_candidate_education(self, resume_id):
        """Remove all education entries from a candidate.
        
        Args:
            resume_id: ID of the candidate
            
        Returns:
            True if successful
        """
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})-[r:HAS_EDUCATION]->(e:Education)
            DETACH DELETE e
        """
        
        self.execute_write_query(query, {"resume_id": resume_id})
        return True 