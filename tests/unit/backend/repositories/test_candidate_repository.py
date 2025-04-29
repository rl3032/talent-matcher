"""
Unit tests for the CandidateRepository class.
"""

import unittest
from unittest import mock
import os
import sys
import json
from datetime import datetime

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.repositories.candidate_repository import CandidateRepository
from neo4j import GraphDatabase, Result, ResultSummary, Record

class TestCandidateRepository(unittest.TestCase):
    """Test case for the CandidateRepository class."""
    
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
        self.test_resume_id = "test_resume_123"
        self.test_data = {
            "resume_id": self.test_resume_id,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
            "summary": "Experienced developer"
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
        self.repo = CandidateRepository(driver=self.mock_driver)
        
        # Patch execute_write_query to return the mock summary but still track calls
        self.original_execute_write_query = self.repo.execute_write_query
        self.repo.execute_write_query = mock.MagicMock(return_value=self.mock_summary)
        
    def tearDown(self):
        """Clean up test environment."""
        self.repo.close()
        
    def test_add_candidate(self):
        """Test add_candidate method."""
        # Arrange
        candidate_data = {
            "resume_id": self.test_resume_id,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
            "summary": "Experienced developer"
        }
        
        # Act
        result = self.repo.add_candidate(candidate_data)
        
        # Assert
        self.assertEqual(result, self.test_resume_id)
        self.repo.execute_write_query.assert_called_once()
        
    def test_add_candidate_skill(self):
        """Test add_candidate_skill method."""
        # Arrange
        resume_id = self.test_resume_id
        skill_id = "test_skill_123"
        level = "advanced"
        years = 5
        is_core = True
        
        # Act
        result = self.repo.add_candidate_skill(resume_id, skill_id, level, years, is_core)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_add_candidate_skill_secondary(self):
        """Test add_candidate_skill method with secondary skill."""
        # Arrange
        resume_id = self.test_resume_id
        skill_id = "test_skill_123"
        level = "intermediate"
        years = 2
        is_core = False
        
        # Act
        result = self.repo.add_candidate_skill(resume_id, skill_id, level, years, is_core)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_add_candidate_experience(self):
        """Test add_candidate_experience method."""
        # Arrange
        resume_id = self.test_resume_id
        experience_id = "test_exp_123"
        title = "Software Developer"
        company = "Test Company"
        start_date = datetime(2018, 1, 1)
        end_date = datetime(2020, 12, 31)
        description = "Developed web applications"
        location = "New York, NY"
        
        # Act
        result = self.repo.add_candidate_experience(
            resume_id, experience_id, title, company, start_date, end_date, description, location
        )
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_add_candidate_education(self):
        """Test add_candidate_education method."""
        # Arrange
        resume_id = self.test_resume_id
        education_id = "test_edu_123"
        institution = "Test University"
        degree = "Bachelor's"
        field = "Computer Science"
        start_date = datetime(2014, 9, 1)
        end_date = datetime(2018, 6, 30)
        
        # Act
        result = self.repo.add_candidate_education(
            resume_id, education_id, institution, degree, field, start_date, end_date
        )
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_find_matching_jobs(self):
        """Test find_matching_jobs method."""
        # Arrange
        resume_id = self.test_resume_id
        limit = 5
        
        # Configure mock to return test job matches
        job_matches = [
            {"job_id": "test_job_1", "title": "Software Engineer", "matchScore": 0.85},
            {"job_id": "test_job_2", "title": "Web Developer", "matchScore": 0.75}
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=job_matches):
            # Act
            result = self.repo.find_matching_jobs(resume_id, limit)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["job_id"], "test_job_1")
            self.assertEqual(result[1]["job_id"], "test_job_2")
            
    def test_find_matching_jobs_enhanced(self):
        """Test find_matching_jobs_enhanced method."""
        # Arrange
        resume_id = self.test_resume_id
        limit = 5
        weights = {"skills": 0.8, "semantic": 0.2}
        
        # Mock candidate exists check
        candidate_exists_result = [{"exists": True}]
        
        # Configure mock to return test job matches with enhanced scores
        job_matches = [
            {
                "job_id": "test_job_1", 
                "title": "Software Engineer", 
                "skillScore": 85.0,
                "semanticScore": 75.0,
                "totalScore": 83.0,
                "match_percentage": 83
            },
            {
                "job_id": "test_job_2", 
                "title": "Web Developer", 
                "skillScore": 75.0,
                "semanticScore": 85.0,
                "totalScore": 77.0,
                "match_percentage": 77
            }
        ]
        
        # Configure mock to return different results based on query
        def mock_execute_read(query, params):
            if "COUNT(c) > 0 as exists" in query:
                return candidate_exists_result
            return job_matches
            
        with mock.patch.object(self.repo, 'execute_read_query', side_effect=mock_execute_read):
            # Act
            result = self.repo.find_matching_jobs_enhanced(resume_id, limit, weights)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["job_id"], "test_job_1")
            self.assertEqual(result[1]["job_id"], "test_job_2")
            
    def test_find_matching_jobs_enhanced_candidate_not_exists(self):
        """Test find_matching_jobs_enhanced when candidate doesn't exist."""
        # Arrange
        resume_id = "nonexistent_resume"
        limit = 5
        
        # Mock candidate exists check to return False
        candidate_exists_result = [{"exists": False}]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=candidate_exists_result):
            # Act
            result = self.repo.find_matching_jobs_enhanced(resume_id, limit)
            
            # Assert
            self.assertEqual(len(result), 0)
            
    def test_get_candidate(self):
        """Test get_candidate method."""
        # Arrange
        resume_id = self.test_resume_id
        
        # Configure mock to return test candidate data
        candidate_data = [{
            "resume_id": resume_id,
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
            "summary": "Experienced developer",
            "experience": json.dumps(["Experience 1", "Experience 2"]),
            "education": json.dumps(["Education 1", "Education 2"])
        }]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=candidate_data):
            # Act
            result = self.repo.get_candidate(resume_id)
            
            # Assert
            self.assertEqual(result["resume_id"], resume_id)
            self.assertEqual(result["name"], "John Doe")
            
    def test_get_candidate_not_found(self):
        """Test get_candidate method when candidate doesn't exist."""
        # Arrange
        resume_id = "nonexistent_resume"
        
        # Configure mock to return empty result
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[]):
            # Act
            result = self.repo.get_candidate(resume_id)
            
            # Assert
            self.assertIsNone(result)
            
    def test_get_candidate_skills(self):
        """Test get_candidate_skills method."""
        # Arrange
        resume_id = self.test_resume_id
        
        # Configure mock to return test candidate skills
        candidate_skills = [
            {
                "skill_id": "skill_1",
                "name": "Python",
                "category": "Programming",
                "level": 8,
                "proficiency": "advanced",
                "relationship_type": "HAS_CORE_SKILL",
                "experience_years": 5
            },
            {
                "skill_id": "skill_2",
                "name": "JavaScript",
                "category": "Programming",
                "level": 7,
                "proficiency": "intermediate",
                "relationship_type": "HAS_SECONDARY_SKILL",
                "experience_years": 3
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=candidate_skills):
            # Act
            result = self.repo.get_candidate_skills(resume_id)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "Python")
            self.assertEqual(result[1]["name"], "JavaScript")
            
    def test_get_candidate_experiences(self):
        """Test get_candidate_experiences method."""
        # Arrange
        resume_id = self.test_resume_id
        
        # Configure mock to return test candidate experience
        candidate_experience = [
            {
                "experience_id": "exp_1",
                "title": "Software Developer",
                "company": "Test Company",
                "start_date": "2018-01-01",
                "end_date": "2020-12-31",
                "description": "Developed web applications",
                "location": "New York, NY"
            },
            {
                "experience_id": "exp_2",
                "title": "Junior Developer",
                "company": "Another Company",
                "start_date": "2016-06-01",
                "end_date": "2017-12-31",
                "description": "Assisted in development",
                "location": "Boston, MA"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=candidate_experience):
            # Act
            result = self.repo.get_candidate_experiences(resume_id)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["title"], "Software Developer")
            self.assertEqual(result[1]["title"], "Junior Developer")
            
    def test_get_candidate_education(self):
        """Test get_candidate_education method."""
        # Arrange
        resume_id = self.test_resume_id
        
        # Configure mock to return test candidate education
        candidate_education = [
            {
                "education_id": "edu_1",
                "institution": "Test University",
                "degree": "Bachelor's",
                "field": "Computer Science",
                "start_date": "2014-09-01",
                "end_date": "2018-06-30",
                "gpa": 3.8
            },
            {
                "education_id": "edu_2",
                "institution": "Another University",
                "degree": "Master's",
                "field": "Software Engineering",
                "start_date": "2018-09-01",
                "end_date": "2020-06-30",
                "gpa": 3.9
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=candidate_education):
            # Act
            result = self.repo.get_candidate_education(resume_id)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["institution"], "Test University")
            self.assertEqual(result[1]["institution"], "Another University")

    def test_process_text_list_with_list(self):
        """Test _process_text_list method with a list input."""
        # Arrange
        text_list = ["Item 1", "Item 2", "Item 3"]
        
        # Act
        result = self.repo._process_text_list(text_list)
        
        # Assert
        self.assertIsInstance(result, str)
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, text_list)
        
    def test_process_text_list_with_string(self):
        """Test _process_text_list method with a string input."""
        # Arrange
        text = "Single text item"
        
        # Act
        result = self.repo._process_text_list(text)
        
        # Assert
        self.assertIsInstance(result, str)
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, [text])
        
    def test_process_text_list_with_none(self):
        """Test _process_text_list method with None input."""
        # Act
        result = self.repo._process_text_list(None)
        
        # Assert
        self.assertIsInstance(result, str)
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, [])
        
    def test_process_education_with_list(self):
        """Test _process_education method with a list input."""
        # Arrange
        education_list = [
            {
                "institution": "Test University",
                "degree": "Bachelor's",
                "field": "Computer Science"
            },
            {
                "institution": "Another University",
                "degree": "Master's",
                "field": "Data Science"
            }
        ]
        
        # Act
        result = self.repo._process_education(education_list)
        
        # Assert
        self.assertIsInstance(result, str)
        parsed_result = json.loads(result)
        self.assertEqual(len(parsed_result), 2)
        self.assertEqual(parsed_result[0]["institution"], "Test University")
        
    def test_process_education_with_none(self):
        """Test _process_education method with None input."""
        # Act
        result = self.repo._process_education(None)
        
        # Assert
        self.assertIsInstance(result, str)
        parsed_result = json.loads(result)
        self.assertEqual(parsed_result, [])
        
    def test_find_candidates(self):
        """Test find_candidates method with filters."""
        # Arrange
        filters = {
            "name": "John",
            "skills": ["Python", "JavaScript"]
        }
        limit = 5
        offset = 0
        
        # Configure mock to return test candidates
        candidates = [
            {
                "resume_id": "resume_1",
                "name": "John Doe",
                "email": "john@example.com",
                "skills": [{"name": "Python"}, {"name": "JavaScript"}]
            },
            {
                "resume_id": "resume_2",
                "name": "John Smith",
                "email": "smith@example.com",
                "skills": [{"name": "Python"}, {"name": "React"}]
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=candidates):
            # Act
            result = self.repo.find_candidates(filters, limit, offset)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "John Doe")
            self.assertEqual(result[1]["name"], "John Smith")
            
    def test_find_candidates_with_full_filters(self):
        """Test find_candidates method with all possible filters."""
        # Arrange
        filters = {
            "domain": "Technology",
            "location": "New York, NY",
            "title": "Software Engineer",
            "skill": "Python"
        }
        limit = 5
        offset = 0
        
        # Configure mock to return filtered candidates
        candidates = [
            {
                "resume_id": "resume_1",
                "name": "John Doe",
                "email": "john@example.com",
                "title": "Software Engineer",
                "location": "New York, NY",
                "domain": "Technology"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=candidates):
            # Act
            result = self.repo.find_candidates(filters, limit, offset)
            
            # Assert
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["name"], "John Doe")
            self.assertEqual(result[0]["title"], "Software Engineer")
            
    def test_get_candidate_filter_options(self):
        """Test get_candidate_filter_options method."""
        # Arrange
        filter_options = {
            "titles": ["Software Engineer", "Data Scientist"],
            "locations": ["New York, NY", "San Francisco, CA"],
            "domains": ["Technology", "Finance"]
        }
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[filter_options]):
            # Act
            result = self.repo.get_candidate_filter_options()
            
            # Assert
            self.assertEqual(result["titles"], filter_options["titles"])
            self.assertEqual(result["locations"], filter_options["locations"])
            self.assertEqual(result["domains"], filter_options["domains"])
            
    def test_get_candidate_filter_options_empty(self):
        """Test get_candidate_filter_options method with empty results."""
        # Arrange
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[]):
            # Act
            result = self.repo.get_candidate_filter_options()
            
            # Assert
            self.assertEqual(result, {"domains": [], "locations": [], "titles": []})
            
    def test_update_candidate(self):
        """Test update_candidate method."""
        # Arrange
        resume_id = self.test_resume_id
        update_data = {
            "name": "Updated Name",
            "title": "Senior Developer",
            "location": "San Francisco, CA"
        }
        
        # Act
        result = self.repo.update_candidate(resume_id, update_data)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_update_candidate_with_education(self):
        """Test update_candidate method with education data."""
        # Arrange
        resume_id = self.test_resume_id
        education_data = [
            {
                "institution": "Test University",
                "degree": "Bachelor's",
                "field": "Computer Science"
            }
        ]
        update_data = {
            "name": "Updated Name",
            "title": "Senior Developer",
            "education": education_data
        }
        
        # Patch _process_education
        with mock.patch.object(self.repo, '_process_education', return_value=json.dumps(education_data)):
            # Act
            result = self.repo.update_candidate(resume_id, update_data)
            
            # Assert
            self.assertTrue(result)
            self.repo.execute_write_query.assert_called_once()
            self.repo._process_education.assert_called_once_with(education_data)
            
    def test_update_candidate_empty_data(self):
        """Test update_candidate method with empty update data."""
        # Arrange
        resume_id = self.test_resume_id
        update_data = {}
        
        # Act
        result = self.repo.update_candidate(resume_id, update_data)
        
        # Assert
        self.assertEqual(result, resume_id)
        self.repo.execute_write_query.assert_not_called()
        
    def test_delete_candidate(self):
        """Test delete_candidate method."""
        # Arrange
        resume_id = self.test_resume_id
        
        # Configure mocks for the dependent methods
        self.repo.remove_candidate_skills = mock.MagicMock(return_value=True)
        self.repo.remove_candidate_experiences = mock.MagicMock(return_value=True)
        self.repo.remove_candidate_education = mock.MagicMock(return_value=True)
        
        # Act
        result = self.repo.delete_candidate(resume_id)
        
        # Assert
        self.assertTrue(result)
        self.repo.remove_candidate_skills.assert_called_once_with(resume_id)
        self.repo.remove_candidate_experiences.assert_called_once_with(resume_id)
        self.repo.remove_candidate_education.assert_called_once_with(resume_id)
        self.repo.execute_write_query.assert_called_once()
        
    def test_remove_candidate_skills(self):
        """Test remove_candidate_skills method."""
        # Arrange
        resume_id = self.test_resume_id
        
        # Act
        result = self.repo.remove_candidate_skills(resume_id)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_remove_candidate_experiences(self):
        """Test remove_candidate_experiences method."""
        # Arrange
        resume_id = self.test_resume_id
        
        # Act
        result = self.repo.remove_candidate_experiences(resume_id)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_remove_candidate_education(self):
        """Test remove_candidate_education method."""
        # Arrange
        resume_id = self.test_resume_id
        
        # Act
        result = self.repo.remove_candidate_education(resume_id)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_add_candidate_with_generated_id(self):
        """Test add_candidate method with ID generation."""
        # Arrange
        candidate_data = {
            "name": "Jane Smith",
            "email": "jane@example.com", 
            "summary": "Skilled data scientist"
        }
        
        # Configure mock for uuid generation
        with mock.patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = mock.MagicMock(hex='12345678abcdefgh')
            
            # Act
            result = self.repo.add_candidate(candidate_data)
            
            # Assert
            self.assertTrue(result.startswith("resume_"))
            self.repo.execute_write_query.assert_called_once()
            
    def test_add_candidate_with_experiences(self):
        """Test add_candidate method with experiences included."""
        # Arrange
        candidate_data = {
            "resume_id": self.test_resume_id,
            "name": "John Doe",
            "email": "john@example.com", 
            "experience": [
                {
                    "job_title": "Developer",
                    "company": "Tech Co",
                    "start_date": "2018-01-01",
                    "end_date": "2020-12-31",
                    "description": ["Developed applications", "Led team projects"]
                }
            ]
        }
        
        # Mock the _add_candidate_experiences method
        self.repo._add_candidate_experiences = mock.MagicMock(return_value=True)
        
        # Act
        result = self.repo.add_candidate(candidate_data)
        
        # Assert
        self.assertEqual(result, self.test_resume_id)
        self.repo.execute_write_query.assert_called_once()
        self.repo._add_candidate_experiences.assert_called_once_with(
            self.test_resume_id, candidate_data["experience"]
        )
        
    def test_link_experience_skills(self):
        """Test _link_experience_skills method."""
        # Arrange
        exp_id = "test_exp_123"
        skills_used = ["Python", "JavaScript"]
        
        # Mock skill query results
        skill_results = [{"skill_id": "skill_1"}]
        
        # Configure mock to return skill results for execute_read_query
        with mock.patch.object(self.repo, 'execute_read_query', return_value=skill_results):
            # Patch execute_write_query to track calls
            with mock.patch.object(self.repo, 'execute_write_query') as mock_write:
                # Act
                self.repo._link_experience_skills(exp_id, skills_used)
                
                # Assert
                self.assertEqual(mock_write.call_count, len(skills_used))
                
    def test_add_candidate_experiences_full(self):
        """Test _add_candidate_experiences method with full experience data."""
        # Arrange
        resume_id = self.test_resume_id
        experiences = [
            {
                "job_title": "Software Developer",
                "company": "Tech Co",
                "start_date": "2018-01-01",
                "end_date": "2020-12-31",
                "description": ["Developed applications", "Led team projects"],
                "location": "San Francisco, CA",
                "skills_used": ["Python", "JavaScript"]
            },
            {
                "job_title": "Junior Developer",
                "company": "Startup Inc",
                "start_date": "2016-06-01",
                "end_date": "2017-12-31",
                "description": "Assisted in development",
                "location": "Remote"
            }
        ]
        
        # Reset the mock counter before this test
        self.repo.execute_write_query.reset_mock()
        
        # Mock the necessary methods
        with mock.patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = mock.MagicMock(hex='12345678abcdefgh')
            
            # Mock the _link_experience_skills method
            self.repo._link_experience_skills = mock.MagicMock(return_value=True)
            
            # Mock the _process_text_list method
            self.repo._process_text_list = mock.MagicMock(return_value=json.dumps(["Developed applications", "Led team projects"]))
            
            # Act
            result = self.repo._add_candidate_experiences(resume_id, experiences)
            
            # Assert
            self.assertTrue(result)
            # For each experience, we have 2 write operations:
            # 1. Create the experience node
            # 2. Create relationship between candidate and experience
            # So for 2 experiences, expect 4 calls
            self.assertEqual(self.repo.execute_write_query.call_count, 4)
            # Should be called for the first experience which has skills_used
            self.repo._link_experience_skills.assert_called_once()
            
    def test_add_candidate_experiences_minimal(self):
        """Test _add_candidate_experiences method with minimal experience data."""
        # Arrange
        resume_id = self.test_resume_id
        experiences = [
            {
                "job_title": "Software Developer",
                "company": "Tech Co",
                "start_date": "2018-01-01",
                "end_date": "2020-12-31"
            }
        ]
        
        # Reset the mock counter before this test
        self.repo.execute_write_query.reset_mock()
        
        # Mock the necessary methods
        with mock.patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = mock.MagicMock(hex='12345678abcdefgh')
            
            # Act
            result = self.repo._add_candidate_experiences(resume_id, experiences)
            
            # Assert
            self.assertTrue(result)
            # For each experience, we have 2 write operations:
            # 1. Create the experience node
            # 2. Create relationship between candidate and experience
            # So for 1 experience, expect 2 calls
            self.assertEqual(self.repo.execute_write_query.call_count, 2)

    def test_find_candidates_with_empty_results(self):
        """Test find_candidates method that returns no candidates."""
        # Arrange
        filters = {
            "domain": "Nonexistent Domain",
            "location": "Nonexistent Location"
        }
        limit = 10
        offset = 0
        
        # Configure mock to return empty results
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[]):
            # Act
            result = self.repo.find_candidates(filters, limit, offset)
            
            # Assert
            self.assertEqual(len(result), 0)
            
    def test_find_candidates_debug_logging(self):
        """Test find_candidates method with debug logging."""
        # Arrange
        filters = {
            "domain": "Technology",
            "location": "San Francisco, CA",
            "title": "Software Engineer",
            "skill": "Python"
        }
        limit = 5
        offset = 0
        
        # Configure mock to return filtered candidates
        candidates = [
            {
                "resume_id": "resume_1",
                "name": "John Doe",
                "email": "john@example.com",
                "title": "Software Engineer",
                "location": "San Francisco, CA",
                "domain": "Technology"
            }
        ]
        
        # Mock print to capture debug messages
        with mock.patch('builtins.print') as mock_print:
            with mock.patch.object(self.repo, 'execute_read_query', return_value=candidates):
                # Act
                result = self.repo.find_candidates(filters, limit, offset)
                
                # Assert
                self.assertEqual(len(result), 1)
                # Verify debug logging was called
                mock_print.assert_any_call(mock.ANY)

    def test_find_candidates_with_multiple_filters(self):
        """Test find_candidates method with multiple filter combinations."""
        # Arrange
        # Test with various filter combinations to cover the where_clauses construction
        test_cases = [
            {"domain": "Technology"},
            {"location": "San Francisco"},
            {"title": "Engineer"},
            {"skill": "Python"},
            {"domain": "Technology", "location": "San Francisco"},
            {"domain": "Technology", "title": "Engineer"},
            {"location": "San Francisco", "skill": "Python"},
            {"title": "Engineer", "skill": "Python"}
        ]
        
        candidates = [{"resume_id": "test_resume", "name": "Test Candidate"}]
        
        # Mock the execute_read_query to return candidates
        with mock.patch.object(self.repo, 'execute_read_query', return_value=candidates):
            for filters in test_cases:
                # Mock print to capture debug messages
                with mock.patch('builtins.print') as mock_print:
                    # Act
                    result = self.repo.find_candidates(filters)
                    
                    # Assert
                    self.assertEqual(len(result), 1)
                    self.assertEqual(result[0]["resume_id"], "test_resume")
                    
                    # Verify debug print was called
                    mock_print.assert_any_call(mock.ANY)

if __name__ == '__main__':
    unittest.main() 