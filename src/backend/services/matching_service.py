"""
Matching Service

This module implements algorithms for matching candidates to jobs using graph traversal.
"""

from src.backend.repositories.job_repository import JobRepository
from src.backend.repositories.candidate_repository import CandidateRepository
from src.backend.repositories.skill_repository import SkillRepository
from src.backend.services.graph_service import GraphService
from src.backend.utils.formatters import format_match_results, _score_to_percentage

class MatchingService:
    """Matching algorithms using the knowledge graph."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls, graph_service=None):
        """Get singleton instance of MatchingService."""
        if cls._instance is None:
            if graph_service is None:
                graph_service = GraphService.get_instance()
            cls._instance = cls(graph_service)
        return cls._instance
    
    def __init__(self, graph_service):
        """Initialize the matcher with a graph service.
        
        Args:
            graph_service: GraphService instance
        """
        self.graph_service = graph_service
        self.driver = graph_service.driver
        
        # Initialize repositories
        self.job_repository = JobRepository(self.driver)
        self.candidate_repository = CandidateRepository(self.driver)
        self.skill_repository = SkillRepository(self.driver)
        
        # Initialize text processing tools
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            import nltk
            from nltk.corpus import stopwords
            
            # Download required NLTK data if not already downloaded
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('stopwords')
                
            self.tfidf_vectorizer = TfidfVectorizer(stop_words='english')
            self.text_matching_available = True
        except ImportError:
            # Fall back to simple word overlap if scikit-learn is not available
            self.text_matching_available = False
            print("Warning: scikit-learn or nltk not available. Using simplified text matching.")

    # MAIN PUBLIC INTERFACE METHODS
        
    def match_candidate_to_jobs(self, resume_id, limit=10, min_score=0.0):
        """Find the best matching jobs for a candidate.
        
        Args:
            resume_id: ID of the candidate to match against
            limit: Maximum number of results to return
            min_score: Minimum match score to include in results
            
        Returns:
            list: List of job matches with scores and details
        """
        # Get basic matches from knowledge graph
        basic_matches = self.graph_service.candidate_repository.find_matching_jobs(resume_id, limit=limit*3)
        
        # Return empty list if no matches found
        if not basic_matches:
            return []
        
        # Collect detailed data for hybrid scoring
        matches = []
        for match in basic_matches:
            # Add the resume_id to each job match record (it's not included by default)
            match["resume_id"] = resume_id
            
            # Get skill details
            matching_skills = self._get_matching_skills(resume_id, match["job_id"])
            missing_skills = self._get_missing_skills(resume_id, match["job_id"])
            exceeding_skills = self._get_exceeding_skills(resume_id, match["job_id"])
            
            # Calculate graph-based score (normalized to 0-1 range)
            total_required_skills = matching_skills + missing_skills
            skill_match_score = self._calculate_skill_match_score(matching_skills, total_required_skills)
            graph_score = skill_match_score / 100  # Normalize to 0-1 range
            
            # Calculate text similarity score (already normalized in the method)
            raw_text_score, normalized_text_score = self._calculate_text_similarity(resume_id, match["job_id"])
            
            # Calculate hybrid score using all components
            hybrid_score = self._calculate_hybrid_score(
                match["matchScore"],
                matching_skills,
                missing_skills,
                exceeding_skills,
                resume_id,
                match["job_id"],
                raw_text_score,
                graph_score
            )
            
            # Get the skill coverage ratio for additional context
            skill_coverage_ratio = len(matching_skills) / max(len(total_required_skills), 1)
            
            # Enrich match data
            match["hybrid_score"] = hybrid_score
            match["match_percentage"] = _score_to_percentage(hybrid_score)
            match["graph_score"] = graph_score
            # Apply our percentage mapping to graph score for consistency
            match["graph_percentage"] = _score_to_percentage(graph_score)
            match["text_score"] = raw_text_score
            # Use normalized text score for display
            match["text_percentage"] = round(normalized_text_score * 100, 1)
            match["matching_skills"] = matching_skills
            match["missing_skills"] = missing_skills
            match["exceeding_skills"] = exceeding_skills
            matches.append(match)
        
        # Filter and sort by hybrid score
        matches = [m for m in matches if m["match_percentage"] >= min_score]
        matches = sorted(matches, key=lambda x: x["hybrid_score"], reverse=True)[:limit]
        
        return matches
    
    def match_job_to_candidates(self, job_id, limit=10, min_score=0.0):
        """Find the best matching candidates for a job.
        
        Args:
            job_id: ID of the job to match against
            limit: Maximum number of results to return
            min_score: Minimum match score to include in results
            
        Returns:
            list: List of candidate matches with scores and details
        """
        # Get basic matches from knowledge graph
        basic_matches = self.graph_service.job_repository.find_matching_candidates(job_id, limit=limit*3)
        
        # Return empty list if no matches found
        if not basic_matches:
            return []
        
        # Collect detailed data for hybrid scoring
        matches = []
        for match in basic_matches:
            # Get skill details
            matching_skills = self._get_matching_skills(match["resume_id"], job_id)
            missing_skills = self._get_missing_skills(match["resume_id"], job_id)
            exceeding_skills = self._get_exceeding_skills(match["resume_id"], job_id)
            
            # Calculate graph-based score (normalized to 0-1 range)
            total_required_skills = matching_skills + missing_skills
            skill_match_score = self._calculate_skill_match_score(matching_skills, total_required_skills)
            graph_score = skill_match_score / 100  # Normalize to 0-1 range
            
            # Calculate text similarity score (already normalized in the method)
            raw_text_score, normalized_text_score = self._calculate_text_similarity(match["resume_id"], job_id)
            
            # Calculate hybrid score using all components
            hybrid_score = self._calculate_hybrid_score(
                match["matchScore"],
                matching_skills,
                missing_skills,
                exceeding_skills,
                match["resume_id"],
                job_id,
                raw_text_score,
                graph_score
            )
            
            # Get the skill coverage ratio for additional context
            skill_coverage_ratio = len(matching_skills) / max(len(total_required_skills), 1)
            
            # Enrich match data
            match["hybrid_score"] = hybrid_score
            match["match_percentage"] = _score_to_percentage(hybrid_score)
            match["graph_score"] = graph_score
            # Apply our percentage mapping to graph score for consistency
            match["graph_percentage"] = _score_to_percentage(graph_score)
            match["text_score"] = raw_text_score
            # Use normalized text score for display
            match["text_percentage"] = round(normalized_text_score * 100, 1)
            match["matching_skills"] = matching_skills
            match["missing_skills"] = missing_skills
            match["exceeding_skills"] = exceeding_skills
            matches.append(match)
        
        # Filter and sort by hybrid score
        matches = [m for m in matches if m["match_percentage"] >= min_score]
        matches = sorted(matches, key=lambda x: x["hybrid_score"], reverse=True)[:limit]
        
        return matches
        
    def get_matching_jobs_for_candidate(self, resume_id, limit=10, min_score=0.0, weights=None):
        """Service-level method to find jobs matching a candidate.
        
        This is the method that JobService and CandidateService should call.
        
        Args:
            resume_id: ID of the candidate to match against
            limit: Maximum number of results to return
            min_score: Minimum match score to include in results
            weights: Optional dictionary of weights for different aspects of matching
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'jobs'/'error' keys
        """
        try:
            # Verify candidate exists by attempting to get data
            candidate_data = self.candidate_repository.get_candidate(resume_id)
            if not candidate_data:
                return {'success': False, 'error': f"Candidate with ID {resume_id} not found"}
            
            # Get matching jobs using the core matching algorithm
            matches = self.match_candidate_to_jobs(resume_id, limit, min_score)
            
            # Format the results for consistent API using the utility function
            formatted_matches = format_match_results(matches)
            
            return {
                'success': True,
                'jobs': formatted_matches,
                'total': len(formatted_matches)
            }
        except Exception as e:
            return {'success': False, 'error': f"Error finding matching jobs: {str(e)}"}
            
    def get_matching_candidates_for_job(self, job_id, limit=10, min_score=0.0, weights=None):
        """Service-level method to find candidates matching a job.
        
        This is the method that JobService and CandidateService should call.
        
        Args:
            job_id: ID of the job to match against
            limit: Maximum number of results to return
            min_score: Minimum match score to include in results
            weights: Optional dictionary of weights for different aspects of matching
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'candidates'/'error' keys
        """
        try:
            # Verify job exists by attempting to get data
            job_data = self.job_repository.get_job(job_id)
            if not job_data:
                return {'success': False, 'error': f"Job with ID {job_id} not found"}
            
            # Get matching candidates using the core matching algorithm
            matches = self.match_job_to_candidates(job_id, limit, min_score)
            
            # Format the results for consistent API using the utility function
            formatted_matches = format_match_results(matches)
            
            return {
                'success': True,
                'candidates': formatted_matches,
                'total': len(formatted_matches)
            }
        except Exception as e:
            return {'success': False, 'error': f"Error finding matching candidates: {str(e)}"}
    
    def recommend_skills_for_job(self, resume_id, job_id, limit=5):
        """Recommend skills for a candidate to learn for a specific job."""
        return self.skill_repository.recommend_skills_for_job(resume_id, job_id, limit)
    
    def get_skill_path(self, start_skill_id, end_skill_id, max_depth=3):
        """Find a learning path between two skills."""
        return self.skill_repository.get_skill_path(start_skill_id, end_skill_id, max_depth)
    
    def get_career_path(self, current_title, target_title, limit=5):
        """Suggest career path from current job title to target job title."""
        # This is a simplified version that would need to be enhanced
        # with actual job title nodes and career progression relationships
        query = """
            MATCH (c1:Candidate)-[:HAS_CORE_SKILL]->(s:Skill)<-[:HAS_CORE_SKILL]-(c2:Candidate)
            WHERE c1.title = $current_title AND c2.title = $target_title
            AND c1 <> c2
            WITH s, count(*) as common_count
            ORDER BY common_count DESC
            LIMIT $limit
            RETURN s.skill_id as skill_id, s.name as name, common_count
        """
        
        return self.candidate_repository.execute_read_query(query, {
            "current_title": current_title, 
            "target_title": target_title, 
            "limit": limit
        })
    
    # PRIVATE HELPER METHODS
    
    def _format_match_skills(self, match):
        """Format skills in match results.
        
        Args:
            match: Match result to format
        """
        # Format matching skills
        if 'primary_matching_skills' in match:
            match['matching_skills'] = [s for s in match['primary_matching_skills'] if s and s.get('skill_id') is not None]
            
        # Format secondary matching skills
        if 'secondary_matching_skills' in match:
            # Filter out null skills
            secondary_skills = [s for s in match['secondary_matching_skills'] if s and s.get('skill_id') is not None]
            
            # Remove duplicate skills
            if 'matching_skills' in match:
                primary_skill_ids = {s.get('skill_id') for s in match.get('matching_skills', [])}
                secondary_skills = [s for s in secondary_skills if s.get('skill_id') not in primary_skill_ids]
                
            match['secondary_matching_skills'] = secondary_skills
        
        # Add placeholder values if needed
        if 'matching_skills' not in match:
            match['matching_skills'] = []
        if 'secondary_matching_skills' not in match:
            match['secondary_matching_skills'] = []
        if 'missing_skills' not in match:
            match['missing_skills'] = []
        
        # Remove raw skills arrays to clean up response
        if 'primary_matching_skills' in match:
            del match['primary_matching_skills']
        
    def _calculate_hybrid_score(self, base_score, matching_skills, missing_skills, exceeding_skills, 
                               resume_id, job_id, text_similarity_score=None, graph_score=None):
        """Calculate a hybrid score using graph-based and vector-based approaches."""
        # Calculate graph score if not provided
        if graph_score is None:
            # Use the new skill match calculation for graph score
            total_required_skills = matching_skills + missing_skills
            skill_match_score = self._calculate_skill_match_score(matching_skills, total_required_skills)
            graph_score = skill_match_score / 100  # Normalize to 0-1 range
            
        # Calculate text similarity score if not provided
        if text_similarity_score is None:
            raw_text_score, _ = self._calculate_text_similarity(resume_id, job_id)
        else:
            # If text_similarity_score is provided, it's already the raw score
            raw_text_score = text_similarity_score
            
        # Calculate normalized proficiency score
        proficiency_match_score = 0
        total_importance = 0
        for skill in matching_skills:
            job_proficiency = self._proficiency_to_numeric(skill.get("job_proficiency", "intermediate"))
            candidate_proficiency = self._proficiency_to_numeric(skill.get("candidate_proficiency", "intermediate"))
            importance = float(skill.get("importance", 1.0))
            total_importance += importance
            
            if candidate_proficiency >= job_proficiency:
                proficiency_match_score += importance
            else:
                gap = job_proficiency - candidate_proficiency
                proficiency_match_score += importance * (1 - gap * 0.25)
        
        normalized_proficiency = proficiency_match_score / max(total_importance, 1.0)
        
        # Calculate skill balance factor
        primary_skill_count = sum(1 for skill in matching_skills if skill.get("is_core", True))
        secondary_skill_count = len(matching_skills) - primary_skill_count
        total_skills = primary_skill_count + secondary_skill_count
        skill_balance_factor = 0.2 * (primary_skill_count / total_skills) if total_skills > 0 else 0
        
        # Calculate exceeding bonus
        exceeding_bonus = min(len(exceeding_skills) * 0.1, 0.5)  # Cap at 0.5
        
        # Calculate coverage boost
        total_required_skills = len(matching_skills) + len(missing_skills)
        coverage_boost = len(matching_skills) / max(total_required_skills, 1)
        
        # Combine all components with their weights
        hybrid_score = (graph_score * 0.20) + (raw_text_score * 0.20) + \
                      (normalized_proficiency * 0.20) + (skill_balance_factor * 0.10) + \
                      (exceeding_bonus * 0.05) + (coverage_boost * 0.25)
        
        return hybrid_score
    
    def _calculate_text_similarity(self, resume_id, job_id):
        """Calculate text similarity between job descriptions and candidate experience."""
        # Retrieve job and candidate text data
        job_text, candidate_text = self._get_text_data(resume_id, job_id)
        
        if not job_text or not candidate_text:
            return 0.0, 0.0  # No text data available
            
        if self.text_matching_available:
            try:
                # Use TF-IDF and cosine similarity for more sophisticated matching
                from sklearn.metrics.pairwise import cosine_similarity
                
                # Join multiple text fields
                job_description = ' '.join(job_text)
                candidate_experience = ' '.join(candidate_text)
                
                # Create TF-IDF vectors
                tfidf_matrix = self.tfidf_vectorizer.fit_transform([job_description, candidate_experience])
                
                # Calculate cosine similarity
                raw_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                
                # Return both raw score and normalized score
                return raw_score, self._normalize_text_similarity_score(raw_score)
            except Exception as e:
                print(f"Error in text similarity calculation: {e}")
                # Fall back to simple matching
                raw_score = self._simple_text_similarity(job_text, candidate_text)
                return raw_score, self._normalize_text_similarity_score(raw_score)
        else:
            # Use simple word overlap for basic matching
            raw_score = self._simple_text_similarity(job_text, candidate_text)
            return raw_score, self._normalize_text_similarity_score(raw_score)
    
    def _normalize_text_similarity_score(self, raw_score):
        """Normalize text similarity scores to ensure they fit within 0-1 range."""
        # Ensure score is in 0-1 range
        raw_score = max(0, min(1.0, raw_score))
        
        # Define thresholds for typical cosine similarity scores
        if raw_score > 0.4:  # High similarity
            normalized = 0.85 + (raw_score - 0.4) * 1.5  # Map 0.4-0.5 to 0.85-1.0
        elif raw_score > 0.2:  # Medium similarity
            normalized = 0.6 + (raw_score - 0.2) * 1.25  # Map 0.2-0.4 to 0.6-0.85
        else:  # Low similarity
            normalized = raw_score * 3.0  # Map 0-0.2 to 0-0.6
        
        return normalized
    
    def _simple_text_similarity(self, job_text_list, candidate_text_list):
        """Calculate a simple text similarity score based on word overlap."""
        # Join all texts
        job_text = ' '.join(job_text_list).lower()
        candidate_text = ' '.join(candidate_text_list).lower()
        
        # Remove common punctuation
        import re
        for text in [job_text, candidate_text]:
            text = re.sub(r'[,.;:!?()"\'-]', ' ', text)
        
        # Create word sets
        job_words = set(job_text.split())
        candidate_words = set(candidate_text.split())
        
        # Remove very common words (simplified stopwords)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                        'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 
                        'about', 'of', 'as', 'from'}
        job_words = job_words - common_words
        candidate_words = candidate_words - common_words
        
        # Calculate Jaccard similarity
        if not job_words or not candidate_words:
            return 0.0
            
        overlap = len(job_words.intersection(candidate_words))
        union = len(job_words.union(candidate_words))
        
        return overlap / union if union > 0 else 0.0
    
    def _get_text_data(self, resume_id, job_id):
        """Retrieve text data for job and candidate for comparison."""
        job_text = []
        candidate_text = []
        
        # Get job description and responsibilities
        job_query = """
            MATCH (j:Job {job_id: $job_id})
            RETURN j.description as description, 
                   j.responsibilities as responsibilities,
                   j.qualifications as qualifications
        """
        
        job_records = self.job_repository.execute_read_query(job_query, {"job_id": job_id})
        
        if job_records and job_records[0]:
            for field in ['description', 'responsibilities', 'qualifications']:
                if job_records[0].get(field):
                    job_text.append(job_records[0][field])
                    
        # Get candidate experience and qualifications
        candidate_query = """
            MATCH (c:Candidate {resume_id: $resume_id})
            RETURN c.experience as experience,
                   c.education as education,
                   c.summary as summary
        """
        
        candidate_records = self.candidate_repository.execute_read_query(candidate_query, {"resume_id": resume_id})
        
        if candidate_records and candidate_records[0]:
            for field in ['experience', 'education', 'summary']:
                if candidate_records[0].get(field):
                    candidate_text.append(candidate_records[0][field])
        
        return job_text, candidate_text
    
    def _proficiency_to_numeric(self, proficiency):
        """Convert proficiency level to numeric value."""
        # If proficiency is already a number, scale it to 0-1 range
        if isinstance(proficiency, (int, float)):
            # Assume scale of 0-10, normalize to 0-1
            return min(1.0, max(0.0, proficiency / 10.0))
            
        # Otherwise handle string proficiency
        proficiency_map = {
            "beginner": 0.25,
            "intermediate": 0.5,
            "advanced": 0.75,
            "expert": 1.0
        }
        return proficiency_map.get(proficiency.lower(), 0.5)
    
    def _get_matching_skills(self, resume_id, job_id):
        """Get skills that match between a candidate and job."""
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})-[r1:HAS_CORE_SKILL]->(s:Skill)<-[r2:REQUIRES_PRIMARY]-(j:Job {job_id: $job_id})
            RETURN s.skill_id as skill_id, s.name as name, r1.proficiency as candidate_proficiency, 
                   r2.proficiency as job_proficiency, r2.importance as importance
            ORDER BY importance DESC
        """
        
        return self.job_repository.execute_read_query(query, {"resume_id": resume_id, "job_id": job_id})
    
    def _get_missing_skills(self, resume_id, job_id):
        """Get skills required by the job but missing from the candidate."""
        query = """
            MATCH (j:Job {job_id: $job_id})-[r:REQUIRES_PRIMARY]->(s:Skill)
            WHERE NOT (s)<-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(:Candidate {resume_id: $resume_id})
            RETURN s.skill_id as skill_id, s.name as name, r.proficiency as job_proficiency, 
                   r.importance as importance
            ORDER BY importance DESC
        """
        
        return self.job_repository.execute_read_query(query, {"resume_id": resume_id, "job_id": job_id})
    
    def _get_exceeding_skills(self, resume_id, job_id):
        """Get skills the candidate has that exceed job requirements."""
        query = """
            MATCH (c:Candidate {resume_id: $resume_id})-[r1:HAS_CORE_SKILL]->(s:Skill)
            WHERE NOT (s)<-[:REQUIRES_PRIMARY|REQUIRES_SECONDARY]-(:Job {job_id: $job_id})
            RETURN s.skill_id as skill_id, s.name as name, r1.proficiency as candidate_proficiency, 
                   r1.experience_years as experience_years
            ORDER BY experience_years DESC
        """
        
        return self.candidate_repository.execute_read_query(query, {"resume_id": resume_id, "job_id": job_id})
    
    def _get_total_job_importance(self, job_id):
        """Calculate the total possible score for a job (sum of all skill importances with appropriate weights)."""
        # Just get the primary importance - since this is the baseline we measure against
        query = """
            MATCH (j:Job {job_id: $job_id})-[r:REQUIRES_PRIMARY]->(s:Skill)
            RETURN sum(r.importance) as total_importance
        """
        
        results = self.job_repository.execute_read_query(query, {"job_id": job_id})
        
        if not results or not results[0]:
            return 10
            
        primary = results[0].get("total_importance", 0) or 0
        
        # We don't need secondary and related scores in the denominator because 
        # we're comparing against the primary skills for percentage calculation
        return primary if primary > 0 else 10
    
    def _calculate_skill_match_score(self, matching_skills, total_required_skills):
        """Calculate a comprehensive skill match score considering importance, proficiency, and core vs. secondary skills."""
        total_importance = sum(skill.get("importance", 1.0) for skill in total_required_skills)
        if total_importance == 0:
            return 0  # Avoid division by zero
            
        matched_importance = 0
        
        for skill in matching_skills:
            job_proficiency = self._proficiency_to_numeric(skill.get("job_proficiency", "intermediate"))
            candidate_proficiency = self._proficiency_to_numeric(skill.get("candidate_proficiency", "intermediate"))
            importance = float(skill.get("importance", 1.0))
            is_core = skill.get("is_core", True)
            
            # Apply proficiency adjustment
            proficiency_adjustment = min(candidate_proficiency / max(job_proficiency, 0.1), 1.0)
            
            # Apply core vs. secondary weighting
            core_weight = 1.0 if is_core else 0.5
            
            # Calculate adjusted importance
            adjusted_importance = importance * proficiency_adjustment * core_weight
            matched_importance += adjusted_importance
        
        # Calculate skill count factor
        skill_count_factor = len(matching_skills) / max(len(total_required_skills), 1)
        
        # Calculate final skill match score
        skill_match_score = (matched_importance / total_importance) * skill_count_factor * 100
        return skill_match_score 