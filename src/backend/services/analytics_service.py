"""
Analytics Service

This module provides business logic for analytics and reporting functionality in the talent matcher system.
"""

import datetime
from src.backend.repositories.job_repository import JobRepository
from src.backend.repositories.candidate_repository import CandidateRepository
from src.backend.repositories.skill_repository import SkillRepository


class AnalyticsService:
    """Service for analytics and reporting operations."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls, graph_service=None):
        """Get singleton instance of AnalyticsService."""
        if cls._instance is None:
            cls._instance = cls(graph_service)
        return cls._instance
    
    def __init__(self, graph_service):
        """Initialize the analytics service with required dependencies.
        
        Args:
            graph_service: GraphService instance for database operations
        """
        self.graph_service = graph_service
        self.job_repository = JobRepository(graph_service.driver)
        self.candidate_repository = CandidateRepository(graph_service.driver)
        self.skill_repository = SkillRepository(graph_service.driver)
        self.driver = graph_service.driver
    
    def get_skill_gap_analysis(self, resume_id, job_id):
        """Get skill gap analysis for a candidate and job.
        
        Args:
            resume_id: ID of the candidate
            job_id: ID of the job
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'analysis' or 'error' keys
        """
        try:
            # Verify that both candidate and job exist
            candidate = self.candidate_repository.get_candidate(resume_id)
            if not candidate:
                return {'success': False, 'error': f"Candidate with ID {resume_id} not found"}
            
            job = self.job_repository.get_job(job_id)
            if not job:
                return {'success': False, 'error': f"Job with ID {job_id} not found"}
            
            # Get candidate skills
            candidate_skills = self.candidate_repository.get_candidate_skills(resume_id)
            
            # Get job skills
            job_skills = self.job_repository.get_job_skills(job_id)
            
            # Analyze skill gap
            candidate_skill_ids = {s.get('skill_id') for s in candidate_skills}
            missing_skills = []
            for skill in job_skills:
                if skill.get('skill_id') not in candidate_skill_ids:
                    missing_skills.append({
                        'skill_id': skill.get('skill_id'),
                        'name': skill.get('name'),
                        'category': skill.get('category', ''),
                        'proficiency': skill.get('proficiency', 'Intermediate'),
                        'importance': skill.get('importance', 0.5)
                    })
            
            # Get matching skills with proficiency gap
            matching_skills = []
            proficiency_map = {'Beginner': 1, 'Intermediate': 2, 'Advanced': 3, 'Expert': 4}
            
            for job_skill in job_skills:
                for candidate_skill in candidate_skills:
                    if job_skill.get('skill_id') == candidate_skill.get('skill_id'):
                        job_proficiency = proficiency_map.get(job_skill.get('proficiency', 'Intermediate'), 2)
                        candidate_proficiency = proficiency_map.get(candidate_skill.get('proficiency', 'Intermediate'), 2)
                        
                        if job_proficiency > candidate_proficiency:
                            matching_skills.append({
                                'skill_id': job_skill.get('skill_id'),
                                'name': job_skill.get('name'),
                                'category': job_skill.get('category', ''),
                                'candidate_proficiency': candidate_skill.get('proficiency', 'Intermediate'),
                                'job_proficiency': job_skill.get('proficiency', 'Intermediate'),
                                'experience_years': candidate_skill.get('years', 0),
                                'importance': job_skill.get('importance', 0.5)
                            })
            
            # Calculate gap score (0-100 scale)
            total_skills = len(job_skills)
            missing_count = len(missing_skills)
            proficiency_gap_count = len(matching_skills)
            
            if total_skills > 0:
                gap_score = 100 - ((missing_count * 0.7 + proficiency_gap_count * 0.3) / total_skills * 100)
                gap_score = max(0, min(100, gap_score))  # Clamp to 0-100 range
            else:
                gap_score = 100  # No gap if no skills required
            
            return {
                'success': True,
                'analysis': {
                    'job_id': job_id,
                    'job_title': job.get('title', ''),
                    'resume_id': resume_id,
                    'candidate_name': candidate.get('name', ''),
                    'gap_score': round(gap_score, 1),
                    'missing_skills': missing_skills,
                    'proficiency_gaps': matching_skills,
                    'total_required_skills': total_skills,
                    'missing_skill_count': missing_count
                }
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error analyzing skill gap: {str(e)}"}
    
    def get_skill_recommendations(self, resume_id, job_id):
        """Get skill recommendations for a candidate targeting a specific job.
        
        Args:
            resume_id: ID of the candidate
            job_id: ID of the job
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'recommendations' or 'error' keys
        """
        try:
            # Get skill gap analysis
            gap_result = self.get_skill_gap_analysis(resume_id, job_id)
            if not gap_result['success']:
                return gap_result
            
            analysis = gap_result['analysis']
            
            # Get recommendations for missing skills
            recommendations = []
            
            # Sort missing skills by importance
            missing_skills = sorted(
                analysis.get('missing_skills', []),
                key=lambda x: x.get('importance', 0),
                reverse=True
            )
            
            for skill in missing_skills[:5]:  # Recommend top 5 skills
                skill_id = skill.get('skill_id')
                
                # Get related skills or prerequisites
                related_skills = self.skill_repository.get_related_skills(skill_id)
                
                # Get learning resources (placeholder)
                learning_resources = self._get_learning_resources(skill_id)
                
                recommendations.append({
                    'skill_id': skill_id,
                    'name': skill.get('name'),
                    'category': skill.get('category', ''),
                    'importance': skill.get('importance', 0.5),
                    'related_skills': related_skills[:3],  # Top 3 related skills
                    'learning_resources': learning_resources
                })
            
            return {
                'success': True,
                'recommendations': {
                    'job_id': job_id,
                    'resume_id': resume_id,
                    'skills': recommendations,
                    'gap_score': analysis.get('gap_score', 0)
                }
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error generating recommendations: {str(e)}"}
    
    def get_career_path(self, current_title, target_title=None):
        """Get career path from current to target job title.
        
        Args:
            current_title: Current job title
            target_title: Target job title
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'path' or 'error' keys
        """
        try:
            # Query career path from database
            with self.driver.session() as session:
                if target_title:
                    # Path between two specific titles
                    result = session.run("""
                        MATCH path = (start:JobTitle {title: $current_title})-[:LEADS_TO*1..5]->(end:JobTitle {title: $target_title})
                        RETURN path, 
                               [node in nodes(path) | node.title] as titles,
                               [node in nodes(path) | node.avg_salary] as salaries,
                               [rel in relationships(path) | rel.transition_count] as transitions,
                               length(path) as path_length
                        ORDER BY path_length ASC
                        LIMIT 1
                    """, {
                        "current_title": current_title,
                        "target_title": target_title
                    })
                else:
                    # All possible paths from current title
                    result = session.run("""
                        MATCH path = (start:JobTitle {title: $current_title})-[:LEADS_TO*1..3]->(end:JobTitle)
                        WHERE start <> end
                        RETURN path, 
                               [node in nodes(path) | node.title] as titles,
                               [node in nodes(path) | node.avg_salary] as salaries,
                               [rel in relationships(path) | rel.transition_count] as transitions,
                               length(path) as path_length
                        ORDER BY path_length ASC
                        LIMIT 5
                    """, {
                        "current_title": current_title
                    })
                
                # Process results
                paths = []
                for record in result:
                    titles = record.get("titles")
                    salaries = record.get("salaries")
                    transitions = record.get("transitions")
                    
                    # Create path data
                    path_data = {
                        "titles": titles,
                        "salaries": salaries,
                        "transitions": transitions,
                        "length": record.get("path_length")
                    }
                    
                    paths.append(path_data)
            
            if not paths:
                return {'success': False, 'error': f"No career path found from {current_title} to {target_title or 'any position'}"}
            
            return {
                'success': True,
                'paths': paths
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error finding career path: {str(e)}"}
    
    def get_dashboard_stats(self, start_date=None, end_date=None):
        """Get statistics for dashboard.
        
        Args:
            start_date: Start date for data range
            end_date: End date for data range
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'stats' or 'error' keys
        """
        try:
            # Convert date strings to datetime if provided
            if isinstance(start_date, str):
                start_date = datetime.datetime.fromisoformat(start_date)
            
            if isinstance(end_date, str):
                end_date = datetime.datetime.fromisoformat(end_date)
            
            if not start_date:
                # Default to last 30 days
                start_date = datetime.datetime.now() - datetime.timedelta(days=30)
            
            if not end_date:
                end_date = datetime.datetime.now()
            
            # Format dates for Neo4j
            start_date_str = start_date.isoformat()
            end_date_str = end_date.isoformat()
            
            # Query database for statistics
            with self.driver.session() as session:
                # Job statistics
                job_result = session.run("""
                    MATCH (j:Job)
                    WHERE j.created_at >= $start_date AND j.created_at <= $end_date
                    RETURN count(j) as job_count,
                           count(DISTINCT j.company) as company_count
                """, {
                    "start_date": start_date_str,
                    "end_date": end_date_str
                })
                
                job_record = job_result.single()
                job_count = job_record["job_count"] if job_record else 0
                company_count = job_record["company_count"] if job_record else 0
                
                # Candidate statistics
                candidate_result = session.run("""
                    MATCH (c:Candidate)
                    WHERE c.created_at >= $start_date AND c.created_at <= $end_date
                    RETURN count(c) as candidate_count
                """, {
                    "start_date": start_date_str,
                    "end_date": end_date_str
                })
                
                candidate_record = candidate_result.single()
                candidate_count = candidate_record["candidate_count"] if candidate_record else 0
                
                # Skill distribution
                skill_result = session.run("""
                    MATCH (s:Skill)<-[r]-(n)
                    WHERE n:Job OR n:Candidate
                    RETURN s.name as skill_name, count(r) as usage_count
                    ORDER BY usage_count DESC
                    LIMIT 10
                """)
                
                top_skills = [
                    {"name": record["skill_name"], "count": record["usage_count"]}
                    for record in skill_result
                ]
                
                # Recent matches
                match_result = session.run("""
                    MATCH (j:Job)-[m:MATCHES]-(c:Candidate)
                    RETURN j.job_id as job_id, j.title as job_title,
                           c.resume_id as resume_id, c.name as candidate_name,
                           m.score as match_score
                    ORDER BY m.created_at DESC
                    LIMIT 5
                """)
                
                recent_matches = [
                    {
                        "job_id": record["job_id"],
                        "job_title": record["job_title"],
                        "resume_id": record["resume_id"],
                        "candidate_name": record["candidate_name"],
                        "match_score": record["match_score"]
                    }
                    for record in match_result
                ]
            
            # Compile stats
            stats = {
                "job_count": job_count,
                "candidate_count": candidate_count,
                "company_count": company_count,
                "top_skills": top_skills,
                "recent_matches": recent_matches,
                "date_range": {
                    "start": start_date_str,
                    "end": end_date_str
                }
            }
            
            return {
                'success': True,
                'stats': stats
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error generating dashboard stats: {str(e)}"}
    
    def _get_learning_resources(self, skill_id):
        """Get learning resources for a skill (placeholder).
        
        Args:
            skill_id: ID of the skill
            
        Returns:
            list: List of learning resources
        """
        # This is a placeholder implementation
        # In a real system, this would query a database of learning resources
        return [
            {
                "title": "Online Course",
                "provider": "Coursera",
                "url": f"https://coursera.org/search?query={skill_id}",
                "type": "course"
            },
            {
                "title": "Documentation",
                "provider": "Official Documentation",
                "url": f"https://example.com/docs/{skill_id}",
                "type": "documentation"
            }
        ] 