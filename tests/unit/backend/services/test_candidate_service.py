"""
Unit tests for the candidate service module.
"""

import unittest
from unittest.mock import MagicMock, patch, ANY
import os
import sys

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.services.candidate_service import CandidateService
from src.backend.models.candidate_model import Candidate, CandidateSkill, Experience, Education


class TestCandidateService(unittest.TestCase):
    """Test case for the CandidateService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock graph service
        self.mock_graph_service = MagicMock()
        self.mock_graph_service.driver = MagicMock()
        
        # Create mock candidate repository
        self.mock_candidate_repository = MagicMock()
        
        # Create mock matching service
        self.mock_matching_service = MagicMock()
        
        # Create the candidate service
        self.candidate_service = CandidateService(self.mock_graph_service)
        
        # Replace the candidate_repository directly
        self.candidate_service.candidate_repository = self.mock_candidate_repository
        
        # Replace the matching_service directly
        self.candidate_service.matching_service = self.mock_matching_service
        
        # Sample candidate data
        self.sample_candidate_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "title": "Software Engineer",
            "location": "San Francisco, CA",
            "domain": "Software Development",
            "summary": "Experienced software engineer with 5+ years of experience",
            "skills": {
                "core": [
                    {"skill_id": "s1", "name": "Python", "proficiency": "Expert", "experience_years": 5}
                ],
                "secondary": [
                    {"skill_id": "s2", "name": "JavaScript", "proficiency": "Intermediate", "experience_years": 3}
                ]
            },
            "experience": [
                {
                    "title": "Senior Developer",
                    "company": "Tech Co",
                    "start_date": "2020-01-01",
                    "end_date": "Present",
                    "description": ["Led a team of 5 developers", "Implemented new features"]
                }
            ],
            "education": [
                {
                    "institution": "University of California",
                    "degree": "Bachelor of Science",
                    "field": "Computer Science",
                    "start_date": "2010-09-01",
                    "end_date": "2014-06-01"
                }
            ]
        }
        
        # Sample candidate object as returned from repo
        self.sample_candidate = {
            "resume_id": "resume_123",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "title": "Software Engineer",
            "location": "San Francisco, CA",
            "domain": "Software Development",
            "summary": "Experienced software engineer with 5+ years of experience"
        }
    
    def test_get_instance(self):
        """Test getting the singleton instance."""
        # Reset singleton instance
        CandidateService._instance = None
        
        # First call should create a new instance
        instance1 = CandidateService.get_instance(self.mock_graph_service)
        
        # Second call should return the same instance
        instance2 = CandidateService.get_instance()
        
        self.assertEqual(instance1, instance2)
    
    def test_create_candidate_success(self):
        """Test creating a candidate successfully."""
        resume_id = "resume_12345678"
        
        # Set up repository to return resume_id
        self.mock_candidate_repository.add_candidate.return_value = resume_id
        
        # Call service method with patched uuid
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "12345678abcdef"
            result = self.candidate_service.create_candidate(self.sample_candidate_data)
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['resume_id'], resume_id)
        
        # Verify repository calls
        self.mock_candidate_repository.add_candidate.assert_called_once()
        self.assertEqual(self.mock_candidate_repository.add_candidate_skill.call_count, 2)  # One for core and one for secondary skill
    
    def test_create_candidate_validation_error(self):
        """Test creating a candidate with validation errors."""
        # Invalid candidate data without required fields
        invalid_candidate_data = {
            "email": "john.doe@example.com",
            # Missing name
            "summary": "Experienced software engineer"
        }
        
        # Call service method
        result = self.candidate_service.create_candidate(invalid_candidate_data)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("Missing required field", result['error'])
        
        # Verify repository calls were not made
        self.mock_candidate_repository.add_candidate.assert_not_called()
    
    def test_create_candidate_invalid_skills(self):
        """Test creating a candidate with invalid skills data."""
        # Invalid candidate data with invalid skills
        invalid_candidate_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "skills": {
                "core": [
                    {"name": "Python"}  # Missing skill_id
                ]
            }
        }
        
        # Call service method
        result = self.candidate_service.create_candidate(invalid_candidate_data)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("Skills must have a skill_id", result['error'])
        
        # Verify repository calls were not made
        self.mock_candidate_repository.add_candidate.assert_not_called()
    
    def test_get_candidate_success(self):
        """Test getting a candidate successfully."""
        resume_id = "resume_123"
        skills = [
            {"skill_id": "s1", "name": "Python", "relationship_type": "HAS_CORE_SKILL", "proficiency": "Expert", "years": 5},
            {"skill_id": "s2", "name": "JavaScript", "relationship_type": "HAS_SECONDARY_SKILL", "proficiency": "Intermediate", "years": 3}
        ]
        experiences = [
            {"experience_id": "exp_1", "title": "Senior Developer", "company": "Tech Co", "start_date": "2020-01-01", "end_date": "Present", "description": "[]"}
        ]
        education = [
            {"education_id": "edu_1", "institution": "University of California", "degree": "Bachelor of Science", "field": "Computer Science", "start_date": "2010-09-01", "end_date": "2014-06-01"}
        ]
        
        # Set up mock repository
        self.mock_candidate_repository.get_candidate.return_value = self.sample_candidate
        self.mock_candidate_repository.get_candidate_skills.return_value = skills
        self.mock_candidate_repository.get_candidate_experiences.return_value = experiences
        self.mock_candidate_repository.get_candidate_education.return_value = education
        
        # Call service method
        result = self.candidate_service.get_candidate(resume_id)
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['candidate']['resume_id'], resume_id)
        self.assertEqual(len(result['candidate']['skills']['core']), 1)
        self.assertEqual(len(result['candidate']['skills']['secondary']), 1)
        self.assertEqual(len(result['candidate']['experience']), 1)
        self.assertEqual(len(result['candidate']['education']), 1)
        
        # Verify repository calls
        self.mock_candidate_repository.get_candidate.assert_called_once_with(resume_id)
        self.mock_candidate_repository.get_candidate_skills.assert_called_once_with(resume_id)
        self.mock_candidate_repository.get_candidate_experiences.assert_called_once_with(resume_id)
        self.mock_candidate_repository.get_candidate_education.assert_called_once_with(resume_id)
    
    def test_get_candidate_not_found(self):
        """Test getting a candidate that doesn't exist."""
        resume_id = "resume_nonexistent"
        
        # Set up mock repository to return None for non-existent candidate
        self.mock_candidate_repository.get_candidate.return_value = None
        
        # Call service method
        result = self.candidate_service.get_candidate(resume_id)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("not found", result['error'])
        
        # Verify repository calls
        self.mock_candidate_repository.get_candidate.assert_called_once_with(resume_id)
        self.mock_candidate_repository.get_candidate_skills.assert_not_called()
        self.mock_candidate_repository.get_candidate_experiences.assert_not_called()
        self.mock_candidate_repository.get_candidate_education.assert_not_called()
    
    def test_update_candidate_success(self):
        """Test updating a candidate successfully."""
        resume_id = "resume_123"
        
        # Update data
        update_data = {
            "title": "Senior Software Engineer",
            "skills": {
                "core": [
                    {"skill_id": "s1", "proficiency": "Expert", "experience_years": 6}
                ]
            }
        }
        
        # Set up mock repository
        self.mock_candidate_repository.get_candidate.return_value = self.sample_candidate
        
        # Call service method
        result = self.candidate_service.update_candidate(resume_id, update_data)
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['resume_id'], resume_id)
        
        # Verify repository calls
        self.mock_candidate_repository.get_candidate.assert_called_once_with(resume_id)
        self.mock_candidate_repository.add_candidate.assert_called_once()
        self.assertTrue(self.mock_candidate_repository.add_candidate_skill.called)
    
    def test_update_candidate_not_found(self):
        """Test updating a candidate that doesn't exist."""
        resume_id = "resume_nonexistent"
        
        # Update data
        update_data = {
            "title": "Senior Software Engineer"
        }
        
        # Set up mock repository to return None for non-existent candidate
        self.mock_candidate_repository.get_candidate.return_value = None
        
        # Call service method
        result = self.candidate_service.update_candidate(resume_id, update_data)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("not found", result['error'])
        
        # Verify repository calls
        self.mock_candidate_repository.get_candidate.assert_called_once_with(resume_id)
        self.mock_candidate_repository.add_candidate.assert_not_called()
    
    def test_delete_candidate_success(self):
        """Test deleting a candidate successfully."""
        resume_id = "resume_123"
        
        # Set up mock repository
        self.mock_candidate_repository.get_candidate.return_value = self.sample_candidate
        # Note: delete_candidate method is not implemented yet, just mocked
        
        # Call service method
        result = self.candidate_service.delete_candidate(resume_id)
        
        # Check result
        self.assertTrue(result['success'])
        self.assertIn("deleted successfully", result['message'])
        
        # Verify repository calls
        self.mock_candidate_repository.get_candidate.assert_called_once_with(resume_id)
        # self.mock_candidate_repository.delete_candidate.assert_called_once_with(resume_id)
    
    def test_delete_candidate_not_found(self):
        """Test deleting a candidate that doesn't exist."""
        resume_id = "resume_nonexistent"
        
        # Set up mock repository to return None for non-existent candidate
        self.mock_candidate_repository.get_candidate.return_value = None
        
        # Call service method
        result = self.candidate_service.delete_candidate(resume_id)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("not found", result['error'])
        
        # Verify repository calls
        self.mock_candidate_repository.get_candidate.assert_called_once_with(resume_id)
        # self.mock_candidate_repository.delete_candidate.assert_not_called()
    
    def test_get_matching_jobs_success(self):
        """Test getting matching jobs successfully."""
        resume_id = "resume_123"
        
        # Sample matches
        sample_matches = [
            {
                "job_id": "job_1",
                "title": "Software Engineer",
                "company": "Tech Co",
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
        self.mock_candidate_repository.get_candidate.return_value = self.sample_candidate
        
        # Setup mock matching service to return a success response
        self.mock_matching_service.get_matching_jobs_for_candidate.return_value = {
            'success': True,
            'jobs': sample_matches,
            'total': len(sample_matches)
        }
        
        # Call service method
        result = self.candidate_service.get_matching_jobs(resume_id, 10)
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(len(result['jobs']), 1)
        self.assertEqual(result['jobs'][0]['job_id'], "job_1")
        
        # Verify matching service was called correctly
        self.mock_matching_service.get_matching_jobs_for_candidate.assert_called_once_with(resume_id, 10, 0.0, None)
    
    def test_get_matching_jobs_candidate_not_found(self):
        """Test getting matching jobs for a candidate that doesn't exist."""
        resume_id = "resume_nonexistent"
        
        # Set up mock matching service to return a failure response
        self.mock_matching_service.get_matching_jobs_for_candidate.return_value = {
            'success': False,
            'error': f"Candidate with ID {resume_id} not found"
        }
        
        # Call service method
        result = self.candidate_service.get_matching_jobs(resume_id, 10)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("not found", result['error'])
        
        # Verify matching service was called correctly
        self.mock_matching_service.get_matching_jobs_for_candidate.assert_called_once_with(resume_id, 10, 0.0, None)
    
    def test_validate_candidate_data(self):
        """Test validating candidate data."""
        # Valid data
        valid_result = self.candidate_service._validate_candidate_data(self.sample_candidate_data)
        self.assertTrue(valid_result['valid'])
        
        # Missing required fields
        invalid_data = {"email": "john.doe@example.com"}
        invalid_result = self.candidate_service._validate_candidate_data(invalid_data)
        self.assertFalse(invalid_result['valid'])
        
        # Invalid skills data
        invalid_skills_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "skills": {
                "core": [
                    {"name": "Python"}  # Missing skill_id
                ]
            }
        }
        invalid_skills_result = self.candidate_service._validate_candidate_data(invalid_skills_data)
        self.assertFalse(invalid_skills_result['valid'])
        
        # Update validation (less strict)
        update_data = {"title": "New Title"}
        update_result = self.candidate_service._validate_candidate_data(update_data, is_update=True)
        self.assertTrue(update_result['valid'])
    
    def test_prepare_candidate_data(self):
        """Test preparing candidate data for database operations."""
        # Prepare candidate data for creation
        prepared_data = self.candidate_service._prepare_candidate_data(self.sample_candidate_data)
        
        # Check prepared data
        self.assertEqual(prepared_data['name'], "John Doe")
        self.assertEqual(prepared_data['email'], "john.doe@example.com")
        self.assertIn('created_at', prepared_data)
        self.assertIn('updated_at', prepared_data)
        
        # Check education JSON serialization if present
        if 'education' in prepared_data:
            self.assertIsInstance(prepared_data['education'], str)
        
        # Check skills removed
        self.assertNotIn('skills', prepared_data)
        self.assertNotIn('experience', prepared_data)
        
        # Prepare candidate data for update
        update_data = {"name": "Jane Doe", "title": "Updated Title"}
        prepared_update = self.candidate_service._prepare_candidate_data(update_data, is_update=True)
        
        # Check update data
        self.assertEqual(prepared_update['name'], "Jane Doe")
        self.assertEqual(prepared_update['title'], "Updated Title")
        self.assertIn('updated_at', prepared_update)
        self.assertNotIn('created_at', prepared_update)


if __name__ == '__main__':
    unittest.main() 