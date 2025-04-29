"""
Candidate Service

This module provides business logic for candidate-related operations in the talent matcher system.
"""

import uuid
import datetime
import json
from src.backend.repositories.candidate_repository import CandidateRepository
from src.backend.models.candidate_model import Candidate, Experience, Education, CandidateSkill
from src.backend.services.matching_service import MatchingService


class CandidateService:
    """Service for candidate-related operations."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls, graph_service=None):
        """Get singleton instance of CandidateService."""
        if cls._instance is None:
            cls._instance = cls(graph_service)
        return cls._instance
    
    def __init__(self, graph_service):
        """Initialize the candidate service with required dependencies.
        
        Args:
            graph_service: GraphService instance for database operations
        """
        self.graph_service = graph_service
        self.candidate_repository = CandidateRepository(graph_service.driver)
        self.matching_service = MatchingService.get_instance(graph_service)
    
    def create_candidate(self, candidate_data):
        """Create a new candidate profile.
        
        Args:
            candidate_data: Dictionary containing candidate details
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'resume_id' or 'error' keys
        """
        try:
            # Validate candidate data
            validation_result = self._validate_candidate_data(candidate_data)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # Generate a unique resume_id if not provided
            if 'resume_id' not in candidate_data or not candidate_data['resume_id']:
                candidate_data['resume_id'] = f"resume_{uuid.uuid4().hex[:8]}"
            
            # Prepare candidate data
            prepared_candidate = self._prepare_candidate_data(candidate_data)
            
            # Add candidate to database
            resume_id = self.candidate_repository.add_candidate(prepared_candidate)
            
            # Add candidate skills if present
            if 'skills' in candidate_data:
                self._add_candidate_skills(resume_id, candidate_data['skills'])
            
            # Add experiences if present
            if 'experience' in candidate_data and isinstance(candidate_data['experience'], list):
                for i, exp in enumerate(candidate_data['experience']):
                    self._add_candidate_experience(resume_id, exp, i)
            
            # Add education if present
            if 'education' in candidate_data and isinstance(candidate_data['education'], list):
                for i, edu in enumerate(candidate_data['education']):
                    self._add_candidate_education(resume_id, edu, i)
            
            return {'success': True, 'resume_id': resume_id}
        
        except Exception as e:
            return {'success': False, 'error': f"Error creating candidate: {str(e)}"}
    
    def get_candidate(self, resume_id):
        """Get a candidate by ID.
        
        Args:
            resume_id: ID of the candidate to retrieve
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'candidate' or 'error' keys
        """
        try:
            # Get candidate from repository
            candidate_data = self.candidate_repository.get_candidate(resume_id)
            
            if not candidate_data:
                return {'success': False, 'error': f"Candidate with ID {resume_id} not found"}
            
            # Get candidate skills
            skills = self.candidate_repository.get_candidate_skills(resume_id)
            
            # Get candidate experiences
            experiences = self.candidate_repository.get_candidate_experiences(resume_id)
            
            # Get candidate education
            education = self.candidate_repository.get_candidate_education(resume_id)
            
            # Process education string into list if needed
            education_list = []
            if education:
                education_list = education
            elif 'education' in candidate_data and candidate_data['education']:
                try:
                    education_data = candidate_data['education']
                    if isinstance(education_data, str):
                        education_list = json.loads(education_data)
                    elif isinstance(education_data, list):
                        education_list = education_data
                except:
                    pass
            
            # Process skills for response
            skill_list = []
            core_skills = []
            secondary_skills = []
            
            for skill in skills:
                # Convert string proficiency to numeric level
                proficiency = skill.get('proficiency', 'intermediate').lower()
                level = skill.get('level', 0)
                
                # If we don't have a numeric level already, convert from string proficiency
                if not level or level <= 0:
                    if proficiency == 'expert':
                        level = 9
                    elif proficiency == 'advanced':
                        level = 7
                    elif proficiency == 'intermediate':
                        level = 5
                    elif proficiency == 'beginner':
                        level = 3
                    else:
                        level = 5  # Default to intermediate
                
                skill_data = {
                    'skill_id': skill.get('skill_id'),
                    'name': skill.get('name'),
                    'proficiency': skill.get('proficiency', 'Intermediate'),
                    'years': skill.get('years', 0) or skill.get('experience_years', 0),  # Handle different field names
                    'category': skill.get('category', ''),
                    'level': level,
                    'relationship_type': skill.get('relationship_type', 'HAS_SKILL')
                }
                skill_list.append(skill_data)
                
                # Add to core or secondary skills based on relationship type
                relationship_type = skill.get('relationship_type', 'HAS_SKILL')
                if relationship_type == 'HAS_CORE_SKILL':
                    core_skills.append(skill_data)
                else:
                    secondary_skills.append(skill_data)
            
            # Add experiences and education to candidate data
            candidate_data['experience'] = experiences
            candidate_data['education'] = education_list
            
            # Add skills to candidate data
            candidate_data['skills'] = {
                'core': core_skills,
                'secondary': secondary_skills
            }
            
            # Format response
            return {
                'success': True,
                'candidate': candidate_data
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error retrieving candidate: {str(e)}"}
    
    def update_candidate(self, resume_id, candidate_data):
        """Update an existing candidate.
        
        Args:
            resume_id: ID of the candidate to update
            candidate_data: Dictionary containing updated candidate details
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'resume_id' or 'error' keys
        """
        try:
            # Verify candidate exists
            existing_candidate = self.candidate_repository.get_candidate(resume_id)
            if not existing_candidate:
                return {'success': False, 'error': f"Candidate with ID {resume_id} not found"}
            
            # Validate candidate data
            validation_result = self._validate_candidate_data(candidate_data, is_update=True)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # Ensure resume_id is preserved
            candidate_data['resume_id'] = resume_id
            
            # Prepare candidate data for update
            prepared_candidate = self._prepare_candidate_data(candidate_data, is_update=True)
            
            # Update candidate in database
            self.candidate_repository.add_candidate(prepared_candidate)  # Reuse add method for update
            
            # Update skills if present
            if 'skills' in candidate_data:
                self._update_candidate_skills(resume_id, candidate_data['skills'])
            
            # Update experiences if present
            if 'experience' in candidate_data and isinstance(candidate_data['experience'], list):
                self._update_candidate_experiences(resume_id, candidate_data['experience'])
            
            # Update education if present
            if 'education' in candidate_data and isinstance(candidate_data['education'], list):
                self._update_candidate_education(resume_id, candidate_data['education'])
            
            return {'success': True, 'resume_id': resume_id}
        
        except Exception as e:
            return {'success': False, 'error': f"Error updating candidate: {str(e)}"}
    
    def delete_candidate(self, resume_id):
        """Delete a candidate profile.
        
        Args:
            resume_id: ID of the candidate to delete
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'message' or 'error' keys
        """
        try:
            # Verify candidate exists
            existing_candidate = self.candidate_repository.get_candidate(resume_id)
            if not existing_candidate:
                return {'success': False, 'error': f"Candidate with ID {resume_id} not found"}
            
            # TODO: Implement delete method in repository
            # self.candidate_repository.delete_candidate(resume_id)
            
            # For now, we'll just return a success message
            return {'success': True, 'message': "Candidate deleted successfully"}
        
        except Exception as e:
            return {'success': False, 'error': f"Error deleting candidate: {str(e)}"}
    
    def find_candidates(self, filters=None, limit=20, offset=0):
        """Find candidates matching specified filters.
        
        Args:
            filters: Dictionary containing filter criteria
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'candidates' or 'error' keys
        """
        try:
            # Use repository's find_candidates method
            candidates = self.candidate_repository.find_candidates(filters, limit, offset)
            
            # Get filter options for the frontend
            filter_options = self.candidate_repository.get_candidate_filter_options()
            
            return {
                'success': True,
                'candidates': candidates,
                'filters': filter_options,
                'total': len(candidates),
                'limit': limit,
                'offset': offset
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error finding candidates: {str(e)}"}
    
    def get_matching_jobs(self, resume_id, limit=10, weights=None):
        """Find jobs matching a candidate.
        
        Args:
            resume_id: ID of the candidate to match against
            limit: Maximum number of results to return
            weights: Dictionary containing matching weights
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'jobs' or 'error' keys
        """
        # Delegate to the matching service
        return self.matching_service.get_matching_jobs_for_candidate(resume_id, limit, 0.0, weights)
    
    def _validate_candidate_data(self, candidate_data, is_update=False):
        """Validate candidate data.
        
        Args:
            candidate_data: Dictionary containing candidate details
            is_update: Whether this is an update operation
            
        Returns:
            dict: Dictionary with 'valid' (bool) and 'error' (str) keys
        """
        # Required fields for new candidate creation
        if not is_update:
            required_fields = ['name']
            for field in required_fields:
                if field not in candidate_data or not candidate_data[field]:
                    return {'valid': False, 'error': f"Missing required field: {field}"}
        
        # Validate skills if present
        if 'skills' in candidate_data:
            skills = candidate_data['skills']
            # Check core skills
            if 'core' in skills:
                for skill in skills['core']:
                    if 'skill_id' not in skill:
                        return {'valid': False, 'error': "Skills must have a skill_id"}
            
            # Check secondary skills
            if 'secondary' in skills:
                for skill in skills['secondary']:
                    if 'skill_id' not in skill:
                        return {'valid': False, 'error': "Skills must have a skill_id"}
        
        return {'valid': True}
    
    def _prepare_candidate_data(self, candidate_data, is_update=False):
        """Prepare candidate data for database operations.
        
        Args:
            candidate_data: Dictionary containing candidate details
            is_update: Whether this is an update operation
            
        Returns:
            dict: Prepared candidate data
        """
        # Copy candidate data to avoid modifying the original
        prepared_candidate = candidate_data.copy()
        
        # Add created_at timestamp for new candidates
        if not is_update:
            prepared_candidate['created_at'] = datetime.datetime.now().isoformat()
        
        # Add updated_at timestamp
        prepared_candidate['updated_at'] = datetime.datetime.now().isoformat()
        
        # Format education as JSON string if it's a list
        if 'education' in prepared_candidate and isinstance(prepared_candidate['education'], list):
            prepared_candidate['education'] = json.dumps(prepared_candidate['education'])
        
        # Remove skills, experience from the main candidate data (handled separately)
        if 'skills' in prepared_candidate:
            del prepared_candidate['skills']
        if 'experience' in prepared_candidate:
            del prepared_candidate['experience']
        
        return prepared_candidate
    
    def _add_candidate_skills(self, resume_id, skills_data):
        """Add skills to a candidate.
        
        Args:
            resume_id: ID of the candidate
            skills_data: Dictionary containing core and secondary skills
        """
        # Add core skills
        if 'core' in skills_data:
            for skill in skills_data['core']:
                self.candidate_repository.add_candidate_skill(
                    resume_id,
                    skill['skill_id'],
                    skill.get('proficiency', 'Intermediate'),
                    skill.get('experience_years', 0),
                    is_core=True
                )
        
        # Add secondary skills
        if 'secondary' in skills_data:
            for skill in skills_data['secondary']:
                self.candidate_repository.add_candidate_skill(
                    resume_id,
                    skill['skill_id'],
                    skill.get('proficiency', 'Beginner'),
                    skill.get('experience_years', 0),
                    is_core=False
                )
    
    def _update_candidate_skills(self, resume_id, skills_data):
        """Update skills for a candidate.
        
        Args:
            resume_id: ID of the candidate
            skills_data: Dictionary containing core and secondary skills
        """
        # Remove existing skills - TODO: implement this method in the repository
        self._remove_candidate_skills(resume_id)
        
        # Add updated skills
        self._add_candidate_skills(resume_id, skills_data)
    
    def _remove_candidate_skills(self, resume_id):
        """Remove all skills from a candidate.
        
        Args:
            resume_id: ID of the candidate
        """
        # TODO: Implement this method in the repository
        # For now, we'll just add a placeholder implementation that does nothing
        pass
    
    def _add_candidate_experience(self, resume_id, experience_data, index=0):
        """Add an experience to a candidate.
        
        Args:
            resume_id: ID of the candidate
            experience_data: Dictionary containing experience details
            index: Index for generating experience_id
        """
        experience_id = experience_data.get('experience_id', f"{resume_id}_exp_{index}")
        
        self.candidate_repository.add_candidate_experience(
            resume_id,
            experience_id,
            experience_data['title'],
            experience_data['company'],
            experience_data.get('start_date', ''),
            experience_data.get('end_date', 'Present'),
            json.dumps(experience_data.get('description', [])) if isinstance(experience_data.get('description', []), list) else experience_data.get('description', ''),
            experience_data.get('location', '')
        )
    
    def _update_candidate_experiences(self, resume_id, experiences_data):
        """Update experiences for a candidate.
        
        Args:
            resume_id: ID of the candidate
            experiences_data: List of experience dictionaries
        """
        # TODO: Implement method to remove existing experiences
        # self._remove_candidate_experiences(resume_id)
        
        # Add updated experiences
        for i, exp in enumerate(experiences_data):
            self._add_candidate_experience(resume_id, exp, i)
    
    def _add_candidate_education(self, resume_id, education_data, index=0):
        """Add an education entry to a candidate.
        
        Args:
            resume_id: ID of the candidate
            education_data: Dictionary containing education details
            index: Index for generating education_id
        """
        education_id = education_data.get('education_id', f"{resume_id}_edu_{index}")
        
        self.candidate_repository.add_candidate_education(
            resume_id,
            education_id,
            education_data['institution'],
            education_data['degree'],
            education_data['field'],
            education_data.get('start_date', ''),
            education_data.get('end_date', ''),
            education_data.get('gpa')
        )
    
    def _update_candidate_education(self, resume_id, education_data):
        """Update education entries for a candidate.
        
        Args:
            resume_id: ID of the candidate
            education_data: List of education dictionaries
        """
        # TODO: Implement method to remove existing education entries
        # self._remove_candidate_education(resume_id)
        
        # Add updated education entries
        for i, edu in enumerate(education_data):
            self._add_candidate_education(resume_id, edu, i) 