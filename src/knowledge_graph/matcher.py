"""
Knowledge Graph-based Matching Algorithm
This module implements algorithms for matching candidates to jobs using graph traversal.
"""

class KnowledgeGraphMatcher:
    """Matching algorithms using the knowledge graph."""
    
    def __init__(self, knowledge_graph):
        """Initialize the matcher with a knowledge graph."""
        self.kg = knowledge_graph
        
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
        
    def match_candidate_to_jobs(self, resume_id, limit=10, min_score=0.0):
        """Find the best matching jobs for a candidate."""
        # Get basic matches from knowledge graph
        basic_matches = self.kg.find_matching_jobs(resume_id, limit=limit*3)
        
        # Collect detailed data for hybrid scoring
        matches = []
        for match in basic_matches:
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
            match["match_percentage"] = self._score_to_percentage(hybrid_score)
            match["graph_score"] = graph_score
            # Apply our percentage mapping to graph score for consistency
            match["graph_percentage"] = self._score_to_percentage(graph_score)
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
        """Find the best matching candidates for a job."""
        # Get basic matches from knowledge graph
        basic_matches = self.kg.find_matching_candidates(job_id, limit=limit*3)
        
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
            match["match_percentage"] = self._score_to_percentage(hybrid_score)
            match["graph_score"] = graph_score
            # Apply our percentage mapping to graph score for consistency
            match["graph_percentage"] = self._score_to_percentage(graph_score)
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
        
        with self.kg.driver.session() as session:
            # Get job description and responsibilities
            job_result = session.run("""
                MATCH (j:Job {job_id: $job_id})
                RETURN j.description as description, 
                       j.responsibilities as responsibilities,
                       j.qualifications as qualifications
            """, {"job_id": job_id})
            
            job_records = [dict(record) for record in job_result]
            if job_records and job_records[0]:
                for field in ['description', 'responsibilities', 'qualifications']:
                    if job_records[0].get(field):
                        job_text.append(job_records[0][field])
                        
            # Get candidate experience and qualifications
            candidate_result = session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})
                RETURN c.experience as experience,
                       c.education as education,
                       c.summary as summary
            """, {"resume_id": resume_id})
            
            candidate_records = [dict(record) for record in candidate_result]
            if candidate_records and candidate_records[0]:
                for field in ['experience', 'education', 'summary']:
                    if candidate_records[0].get(field):
                        candidate_text.append(candidate_records[0][field])
        
        return job_text, candidate_text
    
    def _score_to_percentage(self, score):
        """Convert normalized score to percentage with distribution adjustment.
        
        This applies a modified curve to spread scores appropriately across ranges:
        - Excellent matches (85-100% range) - only for candidates with almost all primary skills
        - High matches (70-85% range)
        - Medium matches (60-70% range)
        - Low matches (<60% range)
        """
        # Ensure score is in 0-1 range
        score = max(0, min(1.0, score))
        
        # First apply a pre-conditioning transformation to spread out the raw scores
        # This helps ensure we're using the full scoring range
        if score > 0.5:
            # Boost higher scores even more before mapping
            transformed_score = 0.5 + (score - 0.5) ** 0.7
        else:
            # Compress lower scores
            transformed_score = score * 0.5 / 0.5
            
        # Now apply our tier-based mapping with the transformed score
        if transformed_score > 0.8:  # Top tier
            percentage = 85 + (transformed_score - 0.8) * 150  # Map 0.8-1.0 to 85-100%
        elif transformed_score > 0.6:  # High tier
            percentage = 70 + (transformed_score - 0.6) * 75  # Map 0.6-0.8 to 70-85%
        elif transformed_score > 0.4:  # Medium tier
            percentage = 60 + (transformed_score - 0.4) * 50  # Map 0.4-0.6 to 60-70%
        else:  # Low tier
            percentage = transformed_score * 150  # Map 0-0.4 to 0-60%
        
        # Ensure we never exceed 100%
        return round(min(100.0, percentage), 1)
    
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
        with self.kg.driver.session() as session:
            result = session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})-[r1:HAS_CORE_SKILL]->(s:Skill)<-[r2:REQUIRES_PRIMARY]-(j:Job {job_id: $job_id})
                RETURN s.skill_id as skill_id, s.name as name, r1.proficiency as candidate_proficiency, 
                       r2.proficiency as job_proficiency, r2.importance as importance
                ORDER BY importance DESC
            """, {"resume_id": resume_id, "job_id": job_id})
            
            return [dict(record) for record in result]
    
    def _get_missing_skills(self, resume_id, job_id):
        """Get skills required by the job but missing from the candidate."""
        with self.kg.driver.session() as session:
            result = session.run("""
                MATCH (j:Job {job_id: $job_id})-[r:REQUIRES_PRIMARY]->(s:Skill)
                WHERE NOT (s)<-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(:Candidate {resume_id: $resume_id})
                RETURN s.skill_id as skill_id, s.name as name, r.proficiency as job_proficiency, 
                       r.importance as importance
                ORDER BY importance DESC
            """, {"resume_id": resume_id, "job_id": job_id})
            
            return [dict(record) for record in result]
    
    def _get_exceeding_skills(self, resume_id, job_id):
        """Get skills the candidate has that exceed job requirements."""
        with self.kg.driver.session() as session:
            result = session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})-[r1:HAS_CORE_SKILL]->(s:Skill)
                WHERE NOT (s)<-[:REQUIRES_PRIMARY|REQUIRES_SECONDARY]-(:Job {job_id: $job_id})
                RETURN s.skill_id as skill_id, s.name as name, r1.proficiency as candidate_proficiency, 
                       r1.experience_years as experience_years
                ORDER BY experience_years DESC
            """, {"resume_id": resume_id, "job_id": job_id})
            
            return [dict(record) for record in result]
    
    def _get_total_job_importance(self, job_id):
        """Calculate the total possible score for a job (sum of all skill importances with appropriate weights)."""
        with self.kg.driver.session() as session:
            # Just get the primary importance - since this is the baseline we measure against
            result = session.run("""
                MATCH (j:Job {job_id: $job_id})-[r:REQUIRES_PRIMARY]->(s:Skill)
                RETURN sum(r.importance) as total_importance
            """, {"job_id": job_id})
            
            records = [dict(record) for record in result]
            
            if not records or not records[0]:
                return 10
                
            primary = records[0].get("total_importance", 0) or 0
            
            # We don't need secondary and related scores in the denominator because 
            # we're comparing against the primary skills for percentage calculation
            return primary if primary > 0 else 10
    
    def recommend_skills_for_job(self, resume_id, job_id, limit=5):
        """Recommend skills for a candidate to learn for a specific job."""
        with self.kg.driver.session() as session:
            result = session.run("""
                MATCH (j:Job {job_id: $job_id})-[r:REQUIRES_PRIMARY]->(s:Skill)
                WHERE NOT (s)<-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(:Candidate {resume_id: $resume_id})
                
                // Find candidate's existing skills that are related to the missing skills
                OPTIONAL MATCH (c:Candidate {resume_id: $resume_id})-[:HAS_CORE_SKILL]->(cs:Skill)
                                 -[:RELATED_TO|REQUIRES|COMPLEMENTARY_TO]->(s)
                
                RETURN s.skill_id as skill_id, s.name as name, 
                       r.importance as job_importance,
                       count(cs) as relevance_to_existing_skills,
                       r.importance * (1 + count(cs)/3) as learning_value
                ORDER BY learning_value DESC
                LIMIT $limit
            """, {"resume_id": resume_id, "job_id": job_id, "limit": limit})
            
            return [dict(record) for record in result]
    
    def get_skill_path(self, start_skill_id, end_skill_id, max_depth=3):
        """Find a learning path between two skills."""
        with self.kg.driver.session() as session:
            result = session.run("""
                MATCH path = shortestPath((s1:Skill {skill_id: $start_skill_id})-[:RELATED_TO|REQUIRES|COMPLEMENTARY_TO*1..{max_depth}]->(s2:Skill {skill_id: $end_skill_id}))
                WITH [node in nodes(path) | node.skill_id] AS skill_ids,
                     [node in nodes(path) | node.name] AS skill_names,
                     [rel in relationships(path) | type(rel)] AS relationship_types
                RETURN skill_ids, skill_names, relationship_types
            """, {"start_skill_id": start_skill_id, "end_skill_id": end_skill_id, "max_depth": max_depth})
            
            paths = [dict(record) for record in result]
            if not paths:
                return None
                
            return {
                "skill_ids": paths[0]["skill_ids"],
                "skill_names": paths[0]["skill_names"],
                "relationship_types": paths[0]["relationship_types"]
            }
    
    def get_career_path(self, current_title, target_title, limit=5):
        """Suggest career path from current job title to target job title."""
        # This is a simplified version that would need to be enhanced
        # with actual job title nodes and career progression relationships
        with self.kg.driver.session() as session:
            result = session.run("""
                MATCH (c1:Candidate)-[:HAS_CORE_SKILL]->(s:Skill)<-[:HAS_CORE_SKILL]-(c2:Candidate)
                WHERE c1.title = $current_title AND c2.title = $target_title
                AND c1 <> c2
                WITH s, count(*) as common_count
                ORDER BY common_count DESC
                LIMIT $limit
                RETURN s.skill_id as skill_id, s.name as name, common_count
            """, {"current_title": current_title, "target_title": target_title, "limit": limit})
            
            return [dict(record) for record in result]
    
    def _calculate_skill_match_score(self, matching_skills, total_required_skills):
        """Calculate a comprehensive skill match score considering importance, proficiency, and core vs. secondary skills."""
        total_importance = sum(skill.get("importance", 1.0) for skill in total_required_skills)
        matched_importance = 0
        
        for skill in matching_skills:
            job_proficiency = self._proficiency_to_numeric(skill.get("job_proficiency", "intermediate"))
            candidate_proficiency = self._proficiency_to_numeric(skill.get("candidate_proficiency", "intermediate"))
            importance = float(skill.get("importance", 1.0))
            is_core = skill.get("is_core", True)
            
            # Apply proficiency adjustment
            proficiency_adjustment = min(candidate_proficiency / job_proficiency, 1.0)
            
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