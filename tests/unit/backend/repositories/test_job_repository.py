"""
Unit tests for the JobRepository class.
"""

import unittest
from unittest import mock
import os
import sys
import json

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.repositories.job_repository import JobRepository
from neo4j import GraphDatabase, Result, ResultSummary, Record

class TestJobRepository(unittest.TestCase):
    """Test case for the JobRepository class."""
    
    def setUp(self):
        """Set up test environment by mocking Neo4j driver."""
        # Create mock for Neo4j driver
        self.mock_driver = mock.MagicMock()
        self.mock_session = mock.MagicMock()
        
        # Configure driver to return mock_session
        self.mock_driver.session.return_value = self.mock_session
        
        # Create mock for Neo4j Result and Record
        self.mock_result = mock.MagicMock(spec=Result)
        self.mock_record = mock.MagicMock(spec=Record)
        
        # Configure mock_record to return test values
        self.test_job_id = "test_job_123"
        self.test_data = {
            "job_id": self.test_job_id,
            "title": "Test Engineer",
            "company": "Test Company",
            "location": "Test Location",
            "domain": "Test Domain"
        }
        self.mock_record.__getitem__.side_effect = lambda key: self.test_data.get(key)
        self.mock_record.items.return_value = list(self.test_data.items())
        self.mock_record.keys.return_value = list(self.test_data.keys())
        
        # Make the record properly convert to a dict when dict(record) is called
        self.mock_record.__iter__.return_value = iter(self.test_data.items())
        
        # Configure mock_result to return records
        self.mock_result.__iter__.return_value = [self.mock_record]
        self.mock_result.single.return_value = self.mock_record
        
        # Configure session to return mock_result
        self.mock_session.run.return_value = self.mock_result
        self.mock_session.__enter__.return_value = self.mock_session
        self.mock_session.__exit__.return_value = None
        
        # For transaction methods
        self.mock_session.execute_read.side_effect = lambda func, *args, **kwargs: [self.test_data]
        self.mock_session.execute_write.side_effect = lambda func, *args, **kwargs: func(self.mock_session, *args, **kwargs)
        
        # Configure result summary
        self.mock_summary = mock.MagicMock(spec=ResultSummary)
        self.mock_result.consume.return_value = self.mock_summary
        
        # Create repository
        self.repo = JobRepository(driver=self.mock_driver)
        
        # Patch execute_write_query to return the mock summary but still track calls
        self.original_execute_write_query = self.repo.execute_write_query
        self.repo.execute_write_query = mock.MagicMock(return_value=self.mock_summary)
        
    def tearDown(self):
        """Clean up test environment."""
        self.repo.close()
        
    def test_add_job(self):
        """Test add_job method."""
        # Arrange
        job_data = {
            "job_id": self.test_job_id,
            "title": "Test Engineer",
            "company": "Test Company",
            "location": "Test Location",
            "domain": "Test Domain",
            "summary": "Test job description",
            "responsibilities": ["Responsibility 1", "Responsibility 2"],
            "qualifications": ["Qualification 1", "Qualification 2"]
        }
        
        # Mock _process_text_list to return test values
        with mock.patch.object(self.repo, '_process_text_list', side_effect=lambda x: json.dumps(x)):
            # Act
            result = self.repo.add_job(job_data)
            
            # Assert
            self.assertEqual(result, self.test_job_id)
            self.repo.execute_write_query.assert_called_once()
            
    def test_add_job_skill(self):
        """Test add_job_skill method."""
        # Arrange
        job_id = self.test_job_id
        skill_id = "test_skill_123"
        proficiency = "advanced"
        importance = 0.8
        is_primary = True
        
        # Act
        result = self.repo.add_job_skill(job_id, skill_id, proficiency, importance, is_primary)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_add_job_skill_secondary(self):
        """Test add_job_skill method with secondary skill."""
        # Arrange
        job_id = self.test_job_id
        skill_id = "test_skill_123"
        proficiency = "intermediate"
        importance = 0.5
        is_primary = False
        
        # Act
        result = self.repo.add_job_skill(job_id, skill_id, proficiency, importance, is_primary)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_find_matching_candidates(self):
        """Test find_matching_candidates method."""
        # Arrange
        job_id = self.test_job_id
        limit = 5
        
        # Configure mock to return test candidate matches
        candidate_matches = [
            {"resume_id": "test_resume_1", "name": "Test Candidate 1", "matchScore": 0.85},
            {"resume_id": "test_resume_2", "name": "Test Candidate 2", "matchScore": 0.75}
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=candidate_matches):
            # Act
            result = self.repo.find_matching_candidates(job_id, limit)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["resume_id"], "test_resume_1")
            self.assertEqual(result[1]["resume_id"], "test_resume_2")
            
    def test_find_matching_candidates_enhanced(self):
        """Test find_matching_candidates_enhanced method."""
        # Arrange
        job_id = self.test_job_id
        limit = 5
        weights = {"skills": 0.8, "location": 0.1, "semantic": 0.1}
        
        # Mock job exists check
        job_exists_result = [{"exists": True}]
        
        # Configure mock to return test candidate matches with enhanced scores
        candidate_matches = [
            {
                "resume_id": "test_resume_1", 
                "name": "Test Candidate 1", 
                "skillScore": 85.0,
                "locationScore": 100.0,
                "semanticScore": 75.0,
                "totalScore": 86.0,
                "match_percentage": 86
            },
            {
                "resume_id": "test_resume_2", 
                "name": "Test Candidate 2", 
                "skillScore": 75.0,
                "locationScore": 80.0,
                "semanticScore": 65.0,
                "totalScore": 75.0,
                "match_percentage": 75
            }
        ]
        
        # Configure mock to return different results based on query
        def mock_execute_read(query, params):
            if "COUNT(j) > 0 as exists" in query:
                return job_exists_result
            return candidate_matches
            
        with mock.patch.object(self.repo, 'execute_read_query', side_effect=mock_execute_read):
            # Act
            result = self.repo.find_matching_candidates_enhanced(job_id, limit, weights)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["resume_id"], "test_resume_1")
            self.assertEqual(result[1]["resume_id"], "test_resume_2")
            
    def test_find_matching_candidates_enhanced_job_not_exists(self):
        """Test find_matching_candidates_enhanced when job doesn't exist."""
        # Arrange
        job_id = "nonexistent_job"
        limit = 5
        
        # Mock job exists check to return False
        job_exists_result = [{"exists": False}]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=job_exists_result):
            # Act
            result = self.repo.find_matching_candidates_enhanced(job_id, limit)
            
            # Assert
            self.assertEqual(len(result), 0)
            
    def test_get_job(self):
        """Test get_job method."""
        # Arrange
        job_id = self.test_job_id
        
        # Configure mock to return test job data
        job_data = [{
            "job_id": job_id,
            "title": "Test Engineer",
            "company": "Test Company",
            "location": "Test Location",
            "domain": "Test Domain",
            "description": "Test Description",
            "responsibilities": json.dumps(["Responsibility 1", "Responsibility 2"]),
            "qualifications": json.dumps(["Qualification 1", "Qualification 2"])
        }]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=job_data):
            # Act
            result = self.repo.get_job(job_id)
            
            # Assert
            self.assertEqual(result["job_id"], job_id)
            self.assertEqual(result["title"], "Test Engineer")
            
    def test_get_job_not_found(self):
        """Test get_job method when job doesn't exist."""
        # Arrange
        job_id = "nonexistent_job"
        
        # Configure mock to return empty result
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[]):
            # Act
            result = self.repo.get_job(job_id)
            
            # Assert
            self.assertIsNone(result)
            
    def test_get_job_skills(self):
        """Test get_job_skills method."""
        # Arrange
        job_id = self.test_job_id
        
        # Configure mock to return test job skills
        job_skills = [
            {
                "skill_id": "skill_1",
                "name": "Python",
                "category": "Programming",
                "level": 8,
                "proficiency": "advanced",
                "relationship_type": "REQUIRES_PRIMARY",
                "importance": 0.8
            },
            {
                "skill_id": "skill_2",
                "name": "Testing",
                "category": "QA",
                "level": 7,
                "proficiency": "intermediate",
                "relationship_type": "REQUIRES_SECONDARY",
                "importance": 0.6
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=job_skills):
            # Act
            result = self.repo.get_job_skills(job_id)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "Python")
            self.assertEqual(result[1]["name"], "Testing")
            
    def test_process_text_list_with_list(self):
        """Test _process_text_list method with a list."""
        # Arrange
        text_list = ["Item 1", "Item 2", "Item 3"]
        
        # Act
        result = self.repo._process_text_list(text_list)
        
        # Assert
        self.assertEqual(result, json.dumps(text_list))
        
    def test_process_text_list_with_string(self):
        """Test _process_text_list method with a string."""
        # Arrange
        text_string = "Single text item"
        
        # Act
        result = self.repo._process_text_list(text_string)
        
        # Assert
        self.assertEqual(result, json.dumps([text_string]))
        
    def test_process_text_list_with_empty(self):
        """Test _process_text_list method with empty input."""
        # Arrange
        text_list = []
        
        # Act
        result = self.repo._process_text_list(text_list)
        
        # Assert
        self.assertEqual(result, "[]")
        
    def test_find_jobs_with_no_filters(self):
        """Test find_jobs method with no filters."""
        # Arrange
        limit = 20
        offset = 0
        
        # Configure mock to return test jobs
        test_jobs = [
            {
                "job_id": "job_1",
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco",
                "domain": "Software",
                "owner_email": "test@example.com",
                "created_at": "2023-01-01",
                "updated_at": "2023-01-02"
            },
            {
                "job_id": "job_2",
                "title": "Data Scientist",
                "company": "Data Co",
                "location": "New York",
                "domain": "Data Science",
                "owner_email": "test@example.com",
                "created_at": "2023-01-03",
                "updated_at": "2023-01-04"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=test_jobs):
            # Act
            result = self.repo.find_jobs(limit=limit, offset=offset)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["job_id"], "job_1")
            self.assertEqual(result[1]["job_id"], "job_2")
            
    def test_find_jobs_with_filters(self):
        """Test find_jobs method with filters."""
        # Arrange
        filters = {
            "company": "Tech Corp",
            "location": "San Francisco",
            "domain": "Software",
            "owner_email": "test@example.com"
        }
        limit = 10
        offset = 0
        
        # Configure mock to return filtered jobs
        filtered_jobs = [
            {
                "job_id": "job_1",
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco",
                "domain": "Software",
                "owner_email": "test@example.com",
                "created_at": "2023-01-01",
                "updated_at": "2023-01-02"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=filtered_jobs):
            # Act
            result = self.repo.find_jobs(filters=filters, limit=limit, offset=offset)
            
            # Assert
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["company"], "Tech Corp")
            self.assertEqual(result[0]["location"], "San Francisco")
            
    def test_get_job_filter_options(self):
        """Test get_job_filter_options method."""
        # Arrange
        filter_options = [{
            "companies": ["Tech Corp", "Data Co", "AI Inc"],
            "locations": ["San Francisco", "New York", "Remote"],
            "domains": ["Software", "Data Science", "AI"]
        }]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=filter_options):
            # Act
            result = self.repo.get_job_filter_options()
            
            # Assert
            self.assertEqual(len(result["companies"]), 3)
            self.assertEqual(len(result["locations"]), 3)
            self.assertEqual(len(result["domains"]), 3)
            self.assertIn("Tech Corp", result["companies"])
            self.assertIn("San Francisco", result["locations"])
            self.assertIn("Software", result["domains"])
            
    def test_get_job_filter_options_empty(self):
        """Test get_job_filter_options method with empty results."""
        # Arrange
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[]):
            # Act
            result = self.repo.get_job_filter_options()
            
            # Assert
            self.assertEqual(result, {"companies": [], "locations": [], "domains": []})
            
    def test_update_job(self):
        """Test update_job method."""
        # Arrange
        job_id = self.test_job_id
        job_data = {
            "title": "Updated Test Engineer",
            "company": "Updated Test Company",
            "location": "Updated Test Location",
            "domain": "Updated Test Domain",
            "description": "Updated Test Description",
            "updated_at": "2023-01-10"
        }
        
        # Act
        result = self.repo.update_job(job_id, job_data)
        
        # Assert
        self.assertEqual(result, job_id)
        self.repo.execute_write_query.assert_called_once()
        
    def test_update_job_no_fields(self):
        """Test update_job method with no fields to update."""
        # Arrange
        job_id = self.test_job_id
        job_data = {}
        
        # Act
        result = self.repo.update_job(job_id, job_data)
        
        # Assert
        self.assertEqual(result, job_id)
        self.repo.execute_write_query.assert_not_called()
        
    def test_delete_job(self):
        """Test delete_job method."""
        # Arrange
        job_id = self.test_job_id
        
        # Mock remove_job_skills method
        with mock.patch.object(self.repo, 'remove_job_skills', return_value=True):
            # Act
            result = self.repo.delete_job(job_id)
            
            # Assert
            self.assertTrue(result)
            self.repo.remove_job_skills.assert_called_once_with(job_id)
            self.repo.execute_write_query.assert_called_once()
            
    def test_remove_job_skills(self):
        """Test remove_job_skills method."""
        # Arrange
        job_id = self.test_job_id
        
        # Act
        result = self.repo.remove_job_skills(job_id)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_create_job_owner_relationship(self):
        """Test create_job_owner_relationship method."""
        # Arrange
        job_id = self.test_job_id
        owner_email = "test@example.com"
        
        # Act
        result = self.repo.create_job_owner_relationship(job_id, owner_email)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_check_job_owner_relationship_exists(self):
        """Test check_job_owner_relationship method with existing relationship."""
        # Arrange
        job_id = self.test_job_id
        owner_email = "test@example.com"
        
        # Configure mock to return that relationship exists
        relationship_exists = [{"has_relationship": True}]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=relationship_exists):
            # Act
            result = self.repo.check_job_owner_relationship(job_id, owner_email)
            
            # Assert
            self.assertTrue(result)
            
    def test_check_job_owner_relationship_not_exists(self):
        """Test check_job_owner_relationship method with non-existing relationship."""
        # Arrange
        job_id = self.test_job_id
        owner_email = "wrong@example.com"
        
        # Configure mock to return that relationship doesn't exist
        relationship_not_exists = [{"has_relationship": False}]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=relationship_not_exists):
            # Act
            result = self.repo.check_job_owner_relationship(job_id, owner_email)
            
            # Assert
            self.assertFalse(result)
            
    def test_check_job_owner_relationship_empty_result(self):
        """Test check_job_owner_relationship method with empty result."""
        # Arrange
        job_id = self.test_job_id
        owner_email = "test@example.com"
        
        # Configure mock to return empty result
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[]):
            # Act
            result = self.repo.check_job_owner_relationship(job_id, owner_email)
            
            # Assert
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main() 