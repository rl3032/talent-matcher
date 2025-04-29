"""
Job Repository for Knowledge Graph
This module provides job-related database operations.
"""

from src.backend.repositories.base.repository import BaseRepository
import json

class JobRepository(BaseRepository):
    """Repository for job-related operations in the knowledge graph."""
    
    def add_job(self, job_data):
        """Add a job node to the graph.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            job_id of the created job
        """
        query = """
            MERGE (j:Job {job_id: $job_id})
            SET j.title = $title,
                j.company = $company,
                j.domain = $domain,
                j.location = $location,
                j.description = $description,
                j.responsibilities = $responsibilities,
                j.qualifications = $qualifications,
                j.owner_email = $owner_email,
                j.created_at = $created_at,
                j.updated_at = $updated_at
            RETURN j.job_id as job_id
        """
        
        parameters = {
            "job_id": job_data["job_id"],
            "title": job_data["title"],
            "company": job_data["company"],
            "domain": job_data.get("domain", ""),
            "location": job_data.get("location", ""),
            "description": job_data.get("summary", ""),
            "responsibilities": self._process_text_list(job_data.get("responsibilities", [])),
            "qualifications": self._process_text_list(job_data.get("qualifications", [])),
            "owner_email": job_data.get("owner_email", ""),
            "created_at": job_data.get("created_at", ""),
            "updated_at": job_data.get("updated_at", "")
        }
        
        result = self.execute_write_query(query, parameters)
        return job_data["job_id"]
    
    def add_job_skill(self, job_id, skill_id, proficiency, importance, is_primary=True):
        """Add a skill requirement to a job.
        
        Args:
            job_id: ID of the job
            skill_id: ID of the skill
            proficiency: Required proficiency level
            importance: Importance of the skill (0-1)
            is_primary: Whether this is a primary (core) skill
            
        Returns:
            True if successful
        """
        rel_type = "REQUIRES_PRIMARY" if is_primary else "REQUIRES_SECONDARY"
        
        query = f"""
            MATCH (j:Job {{job_id: $job_id}})
            MATCH (s:Skill {{skill_id: $skill_id}})
            MERGE (j)-[r:`{rel_type}`]->(s)
            SET r.proficiency = $proficiency,
                r.importance = $importance
        """
        
        parameters = {
            "job_id": job_id,
            "skill_id": skill_id,
            "proficiency": proficiency,
            "importance": importance
        }
        
        self.execute_write_query(query, parameters)
        return True
    
    def find_matching_candidates(self, job_id, limit=10):
        """Find candidates matching a job based on skill graph analysis.
        
        Args:
            job_id: ID of the job
            limit: Maximum number of results to return
            
        Returns:
            List of candidate matches with scores
        """
        query = """
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
        """
        
        return self.execute_read_query(query, {"job_id": job_id, "limit": limit})
    
    def find_matching_candidates_enhanced(self, job_id, limit=10, weights=None):
        """Find candidates matching a job with enhanced algorithm including
        skill matching, location matching, and semantic text matching.
        
        Args:
            job_id: ID of the job
            limit: Maximum number of results to return
            weights: Dictionary of weights for different matching aspects
            
        Returns:
            List of candidate matches with detailed scores
        """
        # Default weights if not provided
        if weights is None:
            weights = {
                "skills": 0.75,
                "location": 0.15,
                "semantic": 0.1
            }
        
        # First check if job exists
        job_check_query = """
            MATCH (j:Job {job_id: $job_id})
            RETURN COUNT(j) > 0 as exists
        """
        
        job_exists = self.execute_read_query(job_check_query, {"job_id": job_id})
        
        if not job_exists or not job_exists[0]["exists"]:
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
        
        return self.execute_read_query(query, {
            "job_id": job_id, 
            "limit": limit,
            "weights": weights
        })
    
    def get_job(self, job_id):
        """Get a job by ID.
        
        Args:
            job_id: ID of the job
            
        Returns:
            Job data as dictionary or None if not found
        """
        query = """
            MATCH (j:Job {job_id: $job_id})
            RETURN j.job_id as job_id, 
                   j.title as title, 
                   j.company as company,
                   j.location as location, 
                   j.domain as domain,
                   j.description as description,
                   j.responsibilities as responsibilities,
                   j.qualifications as qualifications,
                   j.owner_email as owner_email
        """
        
        results = self.execute_read_query(query, {"job_id": job_id})
        if not results:
            return None
        
        # Process the job data before returning
        job_data = results[0]
        
        # Handle JSON strings for responsibilities and qualifications without logging errors
        for field in ['responsibilities', 'qualifications']:
            try:
                if field in job_data and job_data[field] and isinstance(job_data[field], str):
                    # Try to parse as JSON if it's a string that looks like JSON
                    if job_data[field].strip().startswith('['):
                        import json
                        job_data[field] = json.loads(job_data[field])
            except:
                # On any error, fall back to a list with the original value
                if field in job_data and job_data[field]:
                    job_data[field] = [job_data[field]]
            
            # Ensure fields are always lists
            if field in job_data and not isinstance(job_data[field], list):
                job_data[field] = [job_data[field]] if job_data[field] else []
            elif field in job_data and job_data[field] is None:
                job_data[field] = []
            
        return job_data
    
    def get_job_skills(self, job_id):
        """Get skills required for a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            List of skills with relationship properties
        """
        query = """
            MATCH (j:Job {job_id: $job_id})-[r]->(s:Skill)
            RETURN s.skill_id as skill_id, s.name as name, 
                   s.category as category, r.level as level,
                   r.proficiency as proficiency,
                   type(r) as relationship_type,
                   r.importance as importance
            ORDER BY r.importance DESC, s.name
        """
        
        return self.execute_read_query(query, {"job_id": job_id})
    
    def _process_text_list(self, text_list):
        """Process a list of text items into a JSON string to preserve array structure.
        
        Args:
            text_list: A list of text items or a single text item
            
        Returns:
            JSON string representation of the list
        """
        # If the input is None or empty, return an empty array
        if not text_list:
            return "[]"
            
        # If it's a list, encode it as JSON
        if isinstance(text_list, list):
            # Ensure all items are strings
            text_list = [str(item) for item in text_list]
            return json.dumps(text_list)
        
        # If it's a single string (not a JSON array), convert to a list with one item
        return json.dumps([str(text_list)])
    
    def find_jobs(self, filters=None, limit=20, offset=0):
        """Find jobs matching specified filters.
        
        Args:
            filters: Dictionary containing filter criteria
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            List of jobs matching the filters
        """
        # Prepare WHERE clauses based on filters
        where_clauses = []
        params = {
            "limit": limit,
            "offset": offset
        }
        
        # Base query
        query = "MATCH (j:Job)"
        
        # If owner_email filter is present, use the relationship
        if filters and 'owner_email' in filters and filters['owner_email']:
            query = "MATCH (u:User {email: $owner_email})-[:CREATED]->(j:Job)"
            params['owner_email'] = filters['owner_email']
        
        if filters:
            # Handle company filter
            if 'company' in filters and filters['company']:
                where_clauses.append("j.company = $company")
                params['company'] = filters['company']
            
            # Handle location filter
            if 'location' in filters and filters['location']:
                where_clauses.append("j.location = $location")
                params['location'] = filters['location']
            
            # Handle domain filter
            if 'domain' in filters and filters['domain']:
                where_clauses.append("j.domain = $domain")
                params['domain'] = filters['domain']
        
        # Add WHERE clause if there are filters
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        # Add return statement
        query += """
            RETURN j.job_id as job_id, 
                   j.title as title, 
                   j.company as company,
                   j.location as location, 
                   j.domain as domain,
                   j.owner_email as owner_email,
                   j.created_at as created_at,
                   j.updated_at as updated_at
            ORDER BY j.created_at DESC
            SKIP $offset
            LIMIT $limit
        """
        
        return self.execute_read_query(query, params)
    
    def get_job_filter_options(self):
        """Get options for job filters.
        
        Returns:
            Dictionary with filter options
        """
        query = """
            MATCH (j:Job)
            WITH COLLECT(DISTINCT j.company) AS companies,
                 COLLECT(DISTINCT j.location) AS locations,
                 COLLECT(DISTINCT j.domain) AS domains
            RETURN companies, locations, domains
        """
        
        result = self.execute_read_query(query)
        if not result:
            return {"companies": [], "locations": [], "domains": []}
        
        return {
            "companies": result[0].get("companies", []),
            "locations": result[0].get("locations", []),
            "domains": result[0].get("domains", [])
        }
    
    def update_job(self, job_id, job_data):
        """Update a job by ID.
        
        Args:
            job_id: ID of the job to update
            job_data: Dictionary containing updated job data
            
        Returns:
            job_id of the updated job
        """
        # Build SET clause dynamically based on provided fields
        set_clauses = []
        params = {"job_id": job_id}
        
        fields_to_update = [
            "title", "company", "domain", "location", "description",
            "responsibilities", "qualifications", "updated_at", "owner_email"
        ]
        
        for field in fields_to_update:
            if field in job_data:
                set_clauses.append(f"j.{field} = ${field}")
                params[field] = job_data[field]
        
        # Only proceed if there are fields to update
        if not set_clauses:
            return job_id
        
        query = f"""
            MATCH (j:Job {{job_id: $job_id}})
            SET {", ".join(set_clauses)}
            RETURN j.job_id as job_id
        """
        
        self.execute_write_query(query, params)
        return job_id
    
    def delete_job(self, job_id):
        """Delete a job by ID.
        
        Args:
            job_id: ID of the job to delete
            
        Returns:
            True if successful
        """
        # First delete all relationships
        self.remove_job_skills(job_id)
        
        # Then delete the job node
        query = """
            MATCH (j:Job {job_id: $job_id})
            DETACH DELETE j
        """
        
        self.execute_write_query(query, {"job_id": job_id})
        return True
    
    def remove_job_skills(self, job_id):
        """Remove all skills from a job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            True if successful
        """
        query = """
            MATCH (j:Job {job_id: $job_id})-[r:REQUIRES_PRIMARY|REQUIRES_SECONDARY]->(s:Skill)
            DELETE r
        """
        
        self.execute_write_query(query, {"job_id": job_id})
        return True
    
    def create_job_owner_relationship(self, job_id, owner_email):
        """Create a relationship between a job and its owner.
        
        Args:
            job_id: ID of the job
            owner_email: Email of the job owner
            
        Returns:
            True if successful
        """
        query = """
            MATCH (j:Job {job_id: $job_id})
            MATCH (u:User {email: $owner_email})
            MERGE (u)-[:CREATED]->(j)
        """
        
        self.execute_write_query(query, {
            "job_id": job_id,
            "owner_email": owner_email
        })
        return True
        
    def check_job_owner_relationship(self, job_id, owner_email):
        """Check if a user has the CREATED relationship with a job.
        
        Args:
            job_id: ID of the job
            owner_email: Email of the user
            
        Returns:
            True if the relationship exists, False otherwise
        """
        query = """
            MATCH (u:User {email: $owner_email})-[:CREATED]->(j:Job {job_id: $job_id})
            RETURN COUNT(j) > 0 as has_relationship
        """
        
        result = self.execute_read_query(query, {
            "job_id": job_id,
            "owner_email": owner_email
        })
        
        if result and len(result) > 0:
            return result[0]["has_relationship"]
        return False 