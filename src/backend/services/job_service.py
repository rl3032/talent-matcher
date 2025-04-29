"""
Job Service

This module provides business logic for job-related operations in the talent matcher system.
"""

import uuid
import datetime
import json
from src.backend.repositories.job_repository import JobRepository
from src.backend.services.matching_service import MatchingService


class JobService:
    """Service for job-related operations."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls, graph_service=None):
        """Get singleton instance of JobService."""
        if cls._instance is None:
            cls._instance = cls(graph_service)
        return cls._instance
    
    def __init__(self, graph_service):
        """Initialize the job service with required dependencies.
        
        Args:
            graph_service: GraphService instance for database operations
        """
        self.graph_service = graph_service
        self.job_repository = JobRepository(graph_service.driver)
        self.matching_service = MatchingService.get_instance(graph_service)
    
    def create_job(self, job_data, owner_email):
        """Create a new job posting.
        
        Args:
            job_data: Dictionary containing job details
            owner_email: Email of the user creating the job
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'job_id' or 'error' keys
        """
        try:
            # Validate job data
            validation_result = self._validate_job_data(job_data)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # Generate a unique job_id
            job_id = job_data.get('job_id', f"job_{uuid.uuid4().hex[:8]}")
            
            # Prepare job data
            prepared_job = self._prepare_job_data(job_data, job_id, owner_email)
            
            # Add job to database
            self.job_repository.add_job(prepared_job)
            
            # Add job skills if present
            if 'skills' in job_data:
                self._add_job_skills(job_id, job_data['skills'])
            
            # Create relationship between user and job
            self._link_job_to_owner(job_id, owner_email)
            
            return {'success': True, 'job_id': job_id}
        
        except Exception as e:
            return {'success': False, 'error': f"Error creating job: {str(e)}"}
    
    def get_job(self, job_id):
        """Get a job by ID.
        
        Args:
            job_id: ID of the job to retrieve
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'job' or 'error' keys
        """
        try:
            # Get job from repository
            job = self.job_repository.get_job(job_id)
            
            if not job:
                return {'success': False, 'error': f"Job with ID {job_id} not found"}
            
            # Get job skills
            skills = self.job_repository.get_job_skills(job_id)
            
            # Format response
            return {
                'success': True,
                'job': job,
                'skills': skills
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error retrieving job: {str(e)}"}
    
    def update_job(self, job_id, job_data, owner_email):
        """Update an existing job.
        
        Args:
            job_id: ID of the job to update
            job_data: Dictionary containing updated job details
            owner_email: Email of the user updating the job
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'job_id' or 'error' keys
        """
        try:
            # Verify job exists 
            existing_job = self.job_repository.get_job(job_id)
            if not existing_job:
                return {'success': False, 'error': f"Job with ID {job_id} not found"}
            
            # Check if user has permission to update the job
            # First check the owner_email property
            has_permission = existing_job.get('owner_email') == owner_email
            
            # If owner_email check fails, check for CREATED relationship
            if not has_permission:
                has_relationship = self.job_repository.check_job_owner_relationship(job_id, owner_email)
                has_permission = has_relationship
            
            if not has_permission:
                return {'success': False, 'error': "You don't have permission to update this job"}
            
            # Validate job data
            validation_result = self._validate_job_data(job_data, is_update=True)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # Prepare job data for update
            prepared_job = self._prepare_job_data(job_data, job_id, owner_email, is_update=True)
            
            # Update job in database
            self.job_repository.update_job(job_id, prepared_job)
            
            # Update job skills if present
            if 'skills' in job_data:
                self._update_job_skills(job_id, job_data['skills'])
            
            return {'success': True, 'job_id': job_id}
        
        except Exception as e:
            return {'success': False, 'error': f"Error updating job: {str(e)}"}
    
    def delete_job(self, job_id, owner_email):
        """Delete a job.
        
        Args:
            job_id: ID of the job to delete
            owner_email: Email of the user deleting the job
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'message' or 'error' keys
        """
        try:
            # Verify job exists
            existing_job = self.job_repository.get_job(job_id)
            if not existing_job:
                return {'success': False, 'error': f"Job with ID {job_id} not found"}
            
            # Check if user has permission to delete the job
            # First check the owner_email property
            has_permission = existing_job.get('owner_email') == owner_email
            
            # If owner_email check fails, check for CREATED relationship
            if not has_permission:
                has_relationship = self.job_repository.check_job_owner_relationship(job_id, owner_email)
                has_permission = has_relationship
            
            if not has_permission:
                return {'success': False, 'error': "You don't have permission to delete this job"}
            
            # Delete job from database
            self.job_repository.delete_job(job_id)
            
            return {'success': True, 'message': "Job deleted successfully"}
        
        except Exception as e:
            return {'success': False, 'error': f"Error deleting job: {str(e)}"}
    
    def find_jobs(self, filters=None, limit=20, offset=0):
        """Find jobs matching specified filters.
        
        Args:
            filters: Dictionary containing filter criteria
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'jobs' or 'error' keys
        """
        try:
            # Get jobs from repository
            jobs = self.job_repository.find_jobs(filters, limit, offset)
            
            # Get filter values for UI
            filter_data = self.job_repository.get_job_filter_options()
            
            return {
                'success': True,
                'jobs': jobs,
                'filters': filter_data,
                'total': len(jobs),
                'limit': limit,
                'offset': offset
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error finding jobs: {str(e)}"}
    
    def get_matching_candidates(self, job_id, limit=10, weights=None):
        """Find candidates matching a job.
        
        Args:
            job_id: ID of the job to match against
            limit: Maximum number of results to return
            weights: Dictionary containing matching weights
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'candidates' or 'error' keys
        """
        # Delegate to the matching service
        return self.matching_service.get_matching_candidates_for_job(job_id, limit, 0.0, weights)
    
    def _validate_job_data(self, job_data, is_update=False):
        """Validate job data.
        
        Args:
            job_data: Dictionary containing job details
            is_update: Whether this is an update operation
            
        Returns:
            dict: Dictionary with 'valid' (bool) and 'error' (str) keys
        """
        # Required fields for new job creation
        if not is_update:
            required_fields = ['title', 'company', 'location']
            for field in required_fields:
                if field not in job_data or not job_data[field]:
                    return {'valid': False, 'error': f"Missing required field: {field}"}
        
        # Validate skills if present
        if 'skills' in job_data:
            skills = job_data['skills']
            # Check primary skills
            if 'primary' in skills:
                for skill in skills['primary']:
                    if 'skill_id' not in skill:
                        return {'valid': False, 'error': "Skills must have a skill_id"}
            
            # Check secondary skills
            if 'secondary' in skills:
                for skill in skills['secondary']:
                    if 'skill_id' not in skill:
                        return {'valid': False, 'error': "Skills must have a skill_id"}
        
        return {'valid': True}
    
    def _prepare_job_data(self, job_data, job_id, owner_email, is_update=False):
        """Prepare job data for database operations.
        
        Args:
            job_data: Dictionary containing job details
            job_id: ID of the job
            owner_email: Email of the job owner
            is_update: Whether this is an update operation
            
        Returns:
            dict: Prepared job data
        """
        # Copy job data to avoid modifying the original
        prepared_job = job_data.copy()
        
        # Add job_id
        prepared_job['job_id'] = job_id
        
        # Add owner_email
        prepared_job['owner_email'] = owner_email
        
        # Ensure domain is included
        if 'domain' not in prepared_job and is_update:
            # If updating but domain not provided, preserve existing
            existing_job = self.job_repository.get_job(job_id)
            if existing_job and 'domain' in existing_job:
                prepared_job['domain'] = existing_job['domain']
        
        # Add created_at timestamp for new jobs
        if not is_update:
            prepared_job['created_at'] = datetime.datetime.now().isoformat()
        
        # Add updated_at timestamp
        prepared_job['updated_at'] = datetime.datetime.now().isoformat()
        
        # Map summary to description if present (API compatibility)
        if 'summary' in prepared_job and 'description' not in prepared_job:
            prepared_job['description'] = prepared_job['summary']
            
        # Format complex fields as JSON strings - the repository expects this format
        for field in ['responsibilities', 'qualifications']:
            if field in prepared_job:
                # Make sure the field is always a list first
                if not isinstance(prepared_job[field], list):
                    # If it's a string with multiple lines, split it
                    if isinstance(prepared_job[field], str) and '\n' in prepared_job[field]:
                        prepared_job[field] = prepared_job[field].strip().split('\n')
                    else:
                        prepared_job[field] = [prepared_job[field]]
                
                # Convert the list to a JSON string - this is required by the repository
                prepared_job[field] = json.dumps(prepared_job[field])
        
        # Remove skills field (handled separately)
        if 'skills' in prepared_job:
            del prepared_job['skills']
        
        return prepared_job
    
    def _add_job_skills(self, job_id, skills_data):
        """Add skills to a job.
        
        Args:
            job_id: ID of the job
            skills_data: Dictionary containing primary and secondary skills
        """
        # Add primary skills
        if 'primary' in skills_data:
            for skill in skills_data['primary']:
                self.job_repository.add_job_skill(
                    job_id,
                    skill['skill_id'],
                    proficiency=skill.get('proficiency', 'Intermediate'),
                    importance=skill.get('importance', 0.7),
                    is_primary=True
                )
        
        # Add secondary skills
        if 'secondary' in skills_data:
            for skill in skills_data['secondary']:
                self.job_repository.add_job_skill(
                    job_id,
                    skill['skill_id'],
                    proficiency=skill.get('proficiency', 'Beginner'),
                    importance=skill.get('importance', 0.4),
                    is_primary=False
                )
    
    def _update_job_skills(self, job_id, skills_data):
        """Update skills for a job.
        
        Args:
            job_id: ID of the job
            skills_data: Dictionary containing primary and secondary skills
        """
        # Remove existing skills
        self.job_repository.remove_job_skills(job_id)
        
        # Add updated skills
        self._add_job_skills(job_id, skills_data)
    
    def _link_job_to_owner(self, job_id, owner_email):
        """Create a relationship between a job and its owner.
        
        Args:
            job_id: ID of the job
            owner_email: Email of the job owner
        """
        self.job_repository.create_job_owner_relationship(job_id, owner_email) 