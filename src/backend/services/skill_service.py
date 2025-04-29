"""
Skill Service

This module provides business logic for skill-related operations in the talent matcher system.
"""

import uuid
import datetime
from src.backend.repositories.skill_repository import SkillRepository


class SkillService:
    """Service for skill-related operations."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls, graph_service=None):
        """Get singleton instance of SkillService."""
        if cls._instance is None:
            cls._instance = cls(graph_service)
        return cls._instance
    
    def __init__(self, graph_service):
        """Initialize the skill service with required dependencies.
        
        Args:
            graph_service: GraphService instance for database operations
        """
        self.graph_service = graph_service
        self.skill_repository = SkillRepository(graph_service.driver)
    
    def get_skill(self, skill_id):
        """Get a skill by ID.
        
        Args:
            skill_id: ID of the skill to retrieve
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'skill' or 'error' keys
        """
        try:
            # Get skill from repository
            skill = self.skill_repository.get_skill(skill_id)
            
            if not skill:
                return {'success': False, 'error': f"Skill with ID {skill_id} not found"}
            
            return {
                'success': True,
                'skill': skill
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error retrieving skill: {str(e)}"}
    
    def create_skill(self, skill_data):
        """Create a new skill.
        
        Args:
            skill_data: Dictionary containing skill details
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'skill_id' or 'error' keys
        """
        try:
            # Validate skill data
            validation_result = self._validate_skill_data(skill_data)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # Generate a unique skill_id if not provided
            skill_id = skill_data.get('skill_id', f"skill_{uuid.uuid4().hex[:8]}")
            
            # Prepare skill data
            prepared_skill = self._prepare_skill_data(skill_data, skill_id)
            
            # Add skill to database
            self.skill_repository.add_skill(prepared_skill)
            
            return {'success': True, 'skill_id': skill_id}
        
        except Exception as e:
            return {'success': False, 'error': f"Error creating skill: {str(e)}"}
    
    def update_skill(self, skill_id, skill_data):
        """Update an existing skill.
        
        Args:
            skill_id: ID of the skill to update
            skill_data: Dictionary containing updated skill details
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'skill_id' or 'error' keys
        """
        try:
            # Verify skill exists
            existing_skill = self.skill_repository.get_skill(skill_id)
            if not existing_skill:
                return {'success': False, 'error': f"Skill with ID {skill_id} not found"}
            
            # Validate skill data
            validation_result = self._validate_skill_data(skill_data, is_update=True)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['error']}
            
            # Ensure skill_id is preserved
            skill_data['skill_id'] = skill_id
            
            # Prepare skill data for update
            prepared_skill = self._prepare_skill_data(skill_data, skill_id, is_update=True)
            
            # Update skill in database
            self.skill_repository.add_skill(prepared_skill)  # Reuse add method for update
            
            return {'success': True, 'skill_id': skill_id}
        
        except Exception as e:
            return {'success': False, 'error': f"Error updating skill: {str(e)}"}
    
    def delete_skill(self, skill_id):
        """Delete a skill.
        
        Args:
            skill_id: ID of the skill to delete
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'message' or 'error' keys
        """
        try:
            # Verify skill exists
            existing_skill = self.skill_repository.get_skill(skill_id)
            if not existing_skill:
                return {'success': False, 'error': f"Skill with ID {skill_id} not found"}
            
            # Delete skill from database
            self.skill_repository.delete_skill(skill_id)
            
            return {'success': True, 'message': "Skill deleted successfully"}
        
        except Exception as e:
            return {'success': False, 'error': f"Error deleting skill: {str(e)}"}
    
    def find_skills(self, filters=None, limit=50, offset=0):
        """Find skills matching specified filters.
        
        Args:
            filters: Dictionary containing filter criteria
            limit: Maximum number of results to return
            offset: Offset for pagination
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'skills' or 'error' keys
        """
        try:
            # Get skills from repository
            skills = self.skill_repository.find_skills(filters, limit, offset)
            
            # Get total count
            total = len(skills)
            
            return {
                'success': True,
                'skills': skills,
                'total': total,
                'limit': limit,
                'offset': offset
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error finding skills: {str(e)}"}
    
    def get_related_skills(self, skill_id):
        """Get skills related to a specific skill.
        
        Args:
            skill_id: ID of the skill to find related skills for
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'related_skills' or 'error' keys
        """
        try:
            # Verify skill exists
            existing_skill = self.skill_repository.get_skill(skill_id)
            if not existing_skill:
                return {'success': False, 'error': f"Skill with ID {skill_id} not found"}
            
            # Get related skills from repository
            related_skills = self.skill_repository.get_related_skills(skill_id)
            
            return {
                'success': True,
                'related_skills': related_skills
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error finding related skills: {str(e)}"}
    
    def get_skill_path(self, source_id, target_id):
        """Get the path between two skills.
        
        Args:
            source_id: ID of the source skill
            target_id: ID of the target skill
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'path' or 'error' keys
        """
        try:
            # Verify skills exist
            source_skill = self.skill_repository.get_skill(source_id)
            if not source_skill:
                return {'success': False, 'error': f"Source skill with ID {source_id} not found"}
            
            target_skill = self.skill_repository.get_skill(target_id)
            if not target_skill:
                return {'success': False, 'error': f"Target skill with ID {target_id} not found"}
            
            # Get path from repository
            path = self.skill_repository.get_skill_path(source_id, target_id)
            
            if not path:
                return {'success': False, 'error': f"No path found between skills {source_id} and {target_id}"}
            
            return {
                'success': True,
                'path': path
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error finding skill path: {str(e)}"}
    
    def get_skill_graph(self, skill_id):
        """Get a graph visualization of a skill and its connections.
        
        Args:
            skill_id: ID of the skill to visualize
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'graph' or 'error' keys
        """
        try:
            # Verify skill exists
            existing_skill = self.skill_repository.get_skill(skill_id)
            if not existing_skill:
                return {'success': False, 'error': f"Skill with ID {skill_id} not found"}
            
            # Get graph data from repository
            graph_data = self.skill_repository.get_skill_graph(skill_id)
            
            return {
                'success': True,
                'graph': graph_data
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error generating skill graph: {str(e)}"}
    
    def get_skills_network(self, limit=100):
        """Get a network of skills for visualization.
        
        Args:
            limit: Maximum number of skills to include
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'network' or 'error' keys
        """
        try:
            # Get skills network from repository
            network = self.skill_repository.get_skills_network(limit)
            
            return {
                'success': True,
                'network': network
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error generating skills network: {str(e)}"}
    
    def recommend_skills_for_job(self, resume_id, job_id):
        """Recommend skills a candidate should learn for a specific job.
        
        Args:
            resume_id: ID of the candidate
            job_id: ID of the target job
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'recommendations' or 'error' keys
        """
        try:
            # Get skill recommendations from repository
            recommendations = self.skill_repository.recommend_skills_for_job(resume_id, job_id)
            
            return {
                'success': True,
                'recommendations': recommendations
            }
        
        except Exception as e:
            return {'success': False, 'error': f"Error generating skill recommendations: {str(e)}"}
    
    def _validate_skill_data(self, skill_data, is_update=False):
        """Validate skill data.
        
        Args:
            skill_data: Dictionary containing skill details
            is_update: Whether this is an update operation
            
        Returns:
            dict: Dictionary with 'valid' (bool) and 'error' (str) keys
        """
        # Required fields for new skill creation
        if not is_update:
            required_fields = ['name']
            for field in required_fields:
                if field not in skill_data or not skill_data[field]:
                    return {'valid': False, 'error': f"Missing required field: {field}"}
        
        return {'valid': True}
    
    def _prepare_skill_data(self, skill_data, skill_id, is_update=False):
        """Prepare skill data for database operations.
        
        Args:
            skill_data: Dictionary containing skill details
            skill_id: ID of the skill
            is_update: Whether this is an update operation
            
        Returns:
            dict: Prepared skill data
        """
        # Copy skill data to avoid modifying the original
        prepared_skill = skill_data.copy()
        
        # Add skill_id
        prepared_skill['skill_id'] = skill_id
        
        # Add created_at timestamp for new skills
        if not is_update:
            prepared_skill['created_at'] = datetime.datetime.now().isoformat()
        
        # Add updated_at timestamp
        prepared_skill['updated_at'] = datetime.datetime.now().isoformat()
        
        return prepared_skill 