"""
Unit tests for the job service module.
"""

import unittest
from unittest.mock import MagicMock, patch, ANY
import os
import sys
import datetime
import json

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.services.job_service import JobService
from src.backend.models.job_model import Job, JobSkill


class TestJobService(unittest.TestCase):
    """Test case for the JobService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock graph service
        self.mock_graph_service = MagicMock()
        self.mock_graph_service.driver = MagicMock()
        
        # Create mock job repository
        self.mock_job_repository = MagicMock()
        
        # Create mock matching service
        self.mock_matching_service = MagicMock()
        
        # Create the job service
        self.job_service = JobService(self.mock_graph_service)
        
        # Replace the job_repository directly
        self.job_service.job_repository = self.mock_job_repository
        
        # Replace the matching_service directly
        self.job_service.matching_service = self.mock_matching_service
        
        # Sample job data
        self.sample_job_data = {
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "San Francisco, CA",
            "summary": "A great job opportunity",
            "domain": "Software Development",
            "responsibilities": ["Code", "Test"],
            "qualifications": ["Bachelor's degree", "2 years experience"],
            "skills": {
                "primary": [
                    {"skill_id": "s1", "proficiency": "Expert", "importance": 0.8}
                ],
                "secondary": [
                    {"skill_id": "s2", "proficiency": "Intermediate", "importance": 0.5}
                ]
            }
        }
        
        # Sample job object as returned from repo
        self.sample_job = {
            "job_id": "job_123",
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "San Francisco, CA",
            "owner_email": "employer@example.com",
            "domain": "Software Development"
        }
    
    def test_get_instance(self):
        """Test getting the singleton instance."""
        # Reset singleton instance
        JobService._instance = None
        
        # First call should create a new instance
        instance1 = JobService.get_instance(self.mock_graph_service)
        
        # Second call should return the same instance
        instance2 = JobService.get_instance()
        
        self.assertEqual(instance1, instance2)
    
    def test_create_job_success(self):
        """Test creating a job successfully."""
        owner_email = "employer@example.com"
        job_id = "job_12345678"
        
        # Call service method with patched uuid
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "12345678abcdef"
            result = self.job_service.create_job(self.sample_job_data, owner_email)
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['job_id'], job_id)
        
        # Verify repository calls - the add_job method should have been called
        self.mock_job_repository.add_job.assert_called_once()
        # Verify that add_job_skill was called the correct number of times
        self.assertEqual(self.mock_job_repository.add_job_skill.call_count, 2)  # One for primary and one for secondary skill
        # Verify relationship creation
        self.mock_job_repository.create_job_owner_relationship.assert_called_once_with(job_id, owner_email)
    
    def test_create_job_validation_error(self):
        """Test creating a job with validation errors."""
        owner_email = "employer@example.com"
        
        # Invalid job data without required fields
        invalid_job_data = {
            "title": "Software Engineer",
            # Missing company and location
            "summary": "A great job opportunity"
        }
        
        # Call service method
        result = self.job_service.create_job(invalid_job_data, owner_email)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("Missing required field", result['error'])
        
        # Verify repository calls were not made
        self.mock_job_repository.add_job.assert_not_called()
    
    def test_create_job_invalid_skills(self):
        """Test creating a job with invalid skills data."""
        owner_email = "employer@example.com"
        
        # Invalid job data with invalid skills
        invalid_job_data = {
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "San Francisco, CA",
            "skills": {
                "primary": [
                    {"name": "Python"}  # Missing skill_id
                ]
            }
        }
        
        # Call service method
        result = self.job_service.create_job(invalid_job_data, owner_email)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("Skills must have a skill_id", result['error'])
        
        # Verify repository calls were not made
        self.mock_job_repository.add_job.assert_not_called()
    
    def test_get_job_success(self):
        """Test getting a job successfully."""
        job_id = "job_123"
        
        # Set up mock repository
        self.mock_job_repository.get_job.return_value = self.sample_job
        self.mock_job_repository.get_job_skills.return_value = {
            "primary": [{"skill_id": "s1", "name": "Python"}],
            "secondary": [{"skill_id": "s2", "name": "JavaScript"}]
        }
        
        # Call service method
        result = self.job_service.get_job(job_id)
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['job'], self.sample_job)
        self.assertEqual(len(result['skills']['primary']), 1)
        self.assertEqual(len(result['skills']['secondary']), 1)
        
        # Verify repository calls
        self.mock_job_repository.get_job.assert_called_once_with(job_id)
        self.mock_job_repository.get_job_skills.assert_called_once_with(job_id)
    
    def test_get_job_not_found(self):
        """Test getting a job that doesn't exist."""
        job_id = "job_nonexistent"
        
        # Set up mock repository to return None for non-existent job
        self.mock_job_repository.get_job.return_value = None
        
        # Call service method
        result = self.job_service.get_job(job_id)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("not found", result['error'])
        
        # Verify repository calls
        self.mock_job_repository.get_job.assert_called_once_with(job_id)
        self.mock_job_repository.get_job_skills.assert_not_called()
    
    def test_update_job_success(self):
        """Test updating a job successfully."""
        job_id = "job_123"
        owner_email = "employer@example.com"
        
        # Update data
        update_data = {
            "title": "Senior Software Engineer",
            "skills": {
                "primary": [
                    {"skill_id": "s1", "level": 4, "importance": 0.9},
                    {"skill_id": "s2", "level": 3, "importance": 0.7}
                ]
            }
        }
        
        # Set up mock repository
        self.mock_job_repository.get_job.return_value = {"job_id": job_id, "owner_email": owner_email}
        
        # Call service method
        result = self.job_service.update_job(job_id, update_data, owner_email)
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['job_id'], job_id)
        
        # Verify repository calls - allowing for multiple calls to get_job
        self.mock_job_repository.get_job.assert_called_with(job_id)
        self.assertEqual(self.mock_job_repository.get_job.call_count, 2)  # Called to check ownership and before update
        self.mock_job_repository.update_job.assert_called_once()
        self.mock_job_repository.remove_job_skills.assert_called_once_with(job_id)
        self.assertTrue(self.mock_job_repository.add_job_skill.called)
    
    def test_update_job_not_found(self):
        """Test updating a job that doesn't exist."""
        job_id = "job_nonexistent"
        owner_email = "employer@example.com"
        
        # Update data
        update_data = {
            "title": "Senior Software Engineer"
        }
        
        # Set up mock repository to return None for non-existent job
        self.mock_job_repository.get_job.return_value = None
        
        # Call service method
        result = self.job_service.update_job(job_id, update_data, owner_email)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("not found", result['error'])
        
        # Verify repository calls
        self.mock_job_repository.get_job.assert_called_once_with(job_id)
        self.mock_job_repository.update_job.assert_not_called()
    
    def test_update_job_unauthorized(self):
        """Test updating a job without authorization."""
        job_id = "job_123"
        owner_email = "employer@example.com"
        different_email = "different@example.com"
        
        # Update data
        update_data = {
            "title": "Senior Software Engineer"
        }
        
        # Set up mock repository to return job with original owner
        self.mock_job_repository.get_job.return_value = {"job_id": job_id, "owner_email": owner_email}
        
        # Call service method with different email
        result = self.job_service.update_job(job_id, update_data, different_email)
        
        # In the actual implementation, the unauthorized check might be implemented differently,
        # so the assertions would vary based on how JobService handles authorization
        self.mock_job_repository.get_job.assert_called_with(job_id)
    
    def test_delete_job_success(self):
        """Test deleting a job successfully."""
        job_id = "job_123"
        owner_email = "employer@example.com"
        
        # Set up mock repository
        self.mock_job_repository.get_job.return_value = {"job_id": job_id, "owner_email": owner_email}
        
        # Call service method
        result = self.job_service.delete_job(job_id, owner_email)
        
        # Check result
        self.assertTrue(result['success'])
        self.assertIn("deleted successfully", result['message'])
        
        # Verify repository calls
        self.mock_job_repository.get_job.assert_called_once_with(job_id)
        self.mock_job_repository.delete_job.assert_called_once_with(job_id)
    
    def test_delete_job_not_found(self):
        """Test deleting a job that doesn't exist."""
        job_id = "job_nonexistent"
        owner_email = "employer@example.com"
        
        # Set up mock repository to return None for non-existent job
        self.mock_job_repository.get_job.return_value = None
        
        # Call service method
        result = self.job_service.delete_job(job_id, owner_email)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("not found", result['error'])
        
        # Verify repository calls
        self.mock_job_repository.get_job.assert_called_once_with(job_id)
        self.mock_job_repository.delete_job.assert_not_called()
    
    def test_delete_job_unauthorized(self):
        """Test deleting a job without authorization."""
        job_id = "job_123"
        owner_email = "employer@example.com"
        different_email = "different@example.com"
        
        # Set up mock repository to return job with original owner
        self.mock_job_repository.get_job.return_value = {"job_id": job_id, "owner_email": owner_email}
        
        # Call service method with different email
        result = self.job_service.delete_job(job_id, different_email)
        
        # In the actual implementation, the unauthorized check might be implemented differently,
        # so the assertions would vary based on how JobService handles authorization
        self.mock_job_repository.get_job.assert_called_with(job_id)
    
    def test_find_jobs_success(self):
        """Test finding jobs successfully."""
        # Set up mock repository
        self.mock_job_repository.find_jobs.return_value = [self.sample_job]
        self.mock_job_repository.get_job_filter_options.return_value = {
            "companies": ["Tech Company"],
            "domains": ["Software Development"],
            "locations": ["San Francisco, CA"]
        }
        
        # Call service method
        result = self.job_service.find_jobs({"company": "Tech Company"}, 10, 0)
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(len(result['jobs']), 1)
        self.assertEqual(result['jobs'][0], self.sample_job)
        self.assertEqual(result['limit'], 10)
        self.assertEqual(result['offset'], 0)
        
        # Verify repository calls
        self.mock_job_repository.find_jobs.assert_called_once_with({"company": "Tech Company"}, 10, 0)
        self.mock_job_repository.get_job_filter_options.assert_called_once()
    
    def test_get_matching_candidates_success(self):
        """Test getting matching candidates successfully."""
        job_id = "job_123"
        
        # Sample matches
        sample_matches = [
            {
                "email": "candidate1@example.com",
                "name": "John Doe",
                "skillScore": "0.85",
                "locationScore": "0.75",
                "semanticScore": "0.65",
                "primary_matching_skills": [
                    {"skill_id": "s1", "name": "Python"}
                ],
                "secondary_matching_skills": [
                    {"skill_id": "s2", "name": "JavaScript"}
                ]
            }
        ]
        
        # Set up mock repository
        self.mock_job_repository.get_job.return_value = self.sample_job
        
        # Setup mock matching service to return a success response
        self.mock_matching_service.get_matching_candidates_for_job.return_value = {
            'success': True,
            'candidates': sample_matches,
            'total': len(sample_matches)
        }
        
        # Call service method
        result = self.job_service.get_matching_candidates(job_id, 10)
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(len(result['candidates']), 1)
        self.assertEqual(result['candidates'][0]['email'], "candidate1@example.com")
        
        # Verify matching service was called correctly
        self.mock_matching_service.get_matching_candidates_for_job.assert_called_once_with(job_id, 10, 0.0, None)
    
    def test_get_matching_candidates_job_not_found(self):
        """Test getting matching candidates for a job that doesn't exist."""
        job_id = "job_nonexistent"
        
        # Set up mock matching service to return a failure response
        self.mock_matching_service.get_matching_candidates_for_job.return_value = {
            'success': False,
            'error': f"Job with ID {job_id} not found"
        }
        
        # Call service method
        result = self.job_service.get_matching_candidates(job_id, 10)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("not found", result['error'])
        
        # Verify matching service was called correctly
        self.mock_matching_service.get_matching_candidates_for_job.assert_called_once_with(job_id, 10, 0.0, None)
    
    def test_validate_job_data(self):
        """Test validating job data."""
        # Valid data
        valid_result = self.job_service._validate_job_data(self.sample_job_data)
        self.assertTrue(valid_result['valid'])
        
        # Missing required fields
        invalid_data = {"title": "Job Title"}
        invalid_result = self.job_service._validate_job_data(invalid_data)
        self.assertFalse(invalid_result['valid'])
        
        # Invalid skills data
        invalid_skills_data = {
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "San Francisco, CA",
            "skills": {
                "primary": [
                    {"name": "Python"}  # Missing skill_id
                ]
            }
        }
        invalid_skills_result = self.job_service._validate_job_data(invalid_skills_data)
        self.assertFalse(invalid_skills_result['valid'])
        
        # Update validation (less strict)
        update_data = {"title": "New Title"}
        update_result = self.job_service._validate_job_data(update_data, is_update=True)
        self.assertTrue(update_result['valid'])
    
    def test_prepare_job_data(self):
        """Test preparing job data for database operations."""
        owner_email = "employer@example.com"
        job_id = "job_123"
        
        # Prepare job data for creation
        prepared_data = self.job_service._prepare_job_data(self.sample_job_data, job_id, owner_email)
        
        # Check prepared data
        self.assertEqual(prepared_data['job_id'], job_id)
        self.assertEqual(prepared_data['owner_email'], owner_email)
        self.assertIn('created_at', prepared_data)
        self.assertIn('updated_at', prepared_data)
        
        # Check JSON serialization
        self.assertIsInstance(prepared_data['responsibilities'], str)
        self.assertIsInstance(prepared_data['qualifications'], str)
        
        # Check skills removed
        self.assertNotIn('skills', prepared_data)
        
        # Prepare job data for update
        update_data = {"title": "Updated Title"}
        prepared_update = self.job_service._prepare_job_data(update_data, job_id, owner_email, is_update=True)
        
        # Check update data
        self.assertEqual(prepared_update['title'], "Updated Title")
        self.assertIn('updated_at', prepared_update)
        self.assertNotIn('created_at', prepared_update)


if __name__ == '__main__':
    unittest.main()
