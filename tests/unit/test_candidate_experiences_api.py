import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.api.app import app, get_candidate

class TestCandidateExperiencesAPI(unittest.TestCase):
    """Test cases for candidate experiences API endpoints."""
    
    def setUp(self):
        """Set up test client and mocks."""
        self.app = app.test_client()
        self.app.testing = True
        
    @patch('src.api.app.kg')
    def test_get_candidate_experiences(self, mock_kg):
        """Test retrieving candidate experiences via the API."""
        # Mock knowledge graph response for candidate data
        mock_candidate_data = {
            "resume_id": "resume_123",
            "name": "John Doe",
            "title": "Software Engineer",
            "location": "New York",
            "domain": "software",
            "email": "john@example.com",
            "summary": "Experienced developer",
            "education": json.dumps([
                {"institution": "MIT", "degree": "BS", "field": "Computer Science", "year": "2018"}
            ])
        }
        
        # Create mock session result for candidate query
        mock_session = MagicMock()
        mock_record = MagicMock()
        mock_record.items.return_value = [(k, v) for k, v in mock_candidate_data.items()]
        # Ensure the method returns a single record
        mock_session.run.return_value.single.return_value = mock_record
        
        # Mock the driver session context manager
        mock_kg.driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock the get_candidate_experiences method
        mock_kg.get_candidate_experiences.return_value = [
            {
                "exp_id": "resume_123_exp_1",
                "job_title": "Senior Developer",
                "company": "Tech Co",
                "start_date": "2020-01",
                "end_date": "Present",
                "description": ["Led development team", "Implemented CI/CD pipeline"],
                "skills": [
                    {"skill_id": "python", "name": "Python", "category": "Programming"},
                    {"skill_id": "docker", "name": "Docker", "category": "DevOps"}
                ]
            },
            {
                "exp_id": "resume_123_exp_0",
                "job_title": "Junior Developer",
                "company": "StartupX",
                "start_date": "2018-06",
                "end_date": "2019-12",
                "description": ["Built frontend features", "Fixed critical bugs"],
                "skills": [
                    {"skill_id": "javascript", "name": "JavaScript", "category": "Programming"}
                ]
            }
        ]
        
        # Make the API request
        response = self.app.get('/api/candidates/resume_123')
        self.assertEqual(response.status_code, 200)
        
        # Parse response data
        data = json.loads(response.data)
        self.assertIn('candidate', data)
        
        # Check experience data formatting
        experiences = data['candidate']['experience']
        self.assertEqual(len(experiences), 2)
        
        # Verify first experience (should be most recent)
        self.assertEqual(experiences[0]['title'], 'Senior Developer')
        self.assertEqual(experiences[0]['company'], 'Tech Co')
        self.assertEqual(experiences[0]['period'], '2020-01 - Present')
        self.assertEqual(len(experiences[0]['description']), 2)
        self.assertEqual(experiences[0]['description'][0], 'Led development team')
        self.assertEqual(len(experiences[0]['skills']), 2)
        self.assertEqual(experiences[0]['skills'][0]['name'], 'Python')
        
        # Verify second experience
        self.assertEqual(experiences[1]['title'], 'Junior Developer')
        self.assertEqual(experiences[1]['company'], 'StartupX')
        self.assertEqual(experiences[1]['period'], '2018-06 - 2019-12')
        
        # Verify that get_candidate_experiences was called with correct resume_id
        mock_kg.get_candidate_experiences.assert_called_once_with('resume_123')
        
    @patch('src.api.app.kg')
    def test_get_candidate_empty_experiences(self, mock_kg):
        """Test retrieving candidate with no experiences."""
        # Mock knowledge graph response for candidate data
        mock_candidate_data = {
            "resume_id": "resume_123",
            "name": "John Doe",
            "title": "Software Engineer"
        }
        
        # Create mock session result
        mock_session = MagicMock()
        mock_record = MagicMock()
        mock_record.items.return_value = [(k, v) for k, v in mock_candidate_data.items()]
        mock_session.run.return_value.single.return_value = mock_record
        
        # Mock the driver session context manager
        mock_kg.driver.session.return_value.__enter__.return_value = mock_session
        
        # Return empty experiences list
        mock_kg.get_candidate_experiences.return_value = []
        
        # Make the API request
        response = self.app.get('/api/candidates/resume_123')
        self.assertEqual(response.status_code, 200)
        
        # Parse response data
        data = json.loads(response.data)
        
        # Check experience data is empty array
        experiences = data['candidate']['experience']
        self.assertEqual(len(experiences), 0)
        
    @patch('src.api.app.kg')
    def test_get_candidate_with_invalid_experience_format(self, mock_kg):
        """Test retrieving candidate with improperly formatted experience data."""
        # Mock knowledge graph response for candidate data
        mock_candidate_data = {
            "resume_id": "resume_123",
            "name": "John Doe",
            "title": "Software Engineer"
        }
        
        # Create mock session result
        mock_session = MagicMock()
        mock_record = MagicMock()
        mock_record.items.return_value = [(k, v) for k, v in mock_candidate_data.items()]
        mock_session.run.return_value.single.return_value = mock_record
        
        # Mock the driver session context manager
        mock_kg.driver.session.return_value.__enter__.return_value = mock_session
        
        # Return experience with missing/invalid fields
        mock_kg.get_candidate_experiences.return_value = [
            {
                "exp_id": "resume_123_exp_1",
                "job_title": "Senior Developer",
                "company": "Tech Co",
                "start_date": "2020-01",
                # Missing end_date
                "description": None,  # Null description
                "skills": []  # Empty skills
            }
        ]
        
        # Make the API request
        response = self.app.get('/api/candidates/resume_123')
        self.assertEqual(response.status_code, 200)
        
        # Parse response data
        data = json.loads(response.data)
        
        # Check that experience was still processed properly
        experiences = data['candidate']['experience']
        self.assertEqual(len(experiences), 1)
        self.assertEqual(experiences[0]['title'], 'Senior Developer')
        self.assertEqual(experiences[0]['period'], '2020-01 - None')  # Should handle missing end_date
        self.assertEqual(experiences[0]['description'], [])  # Should convert null to empty array

if __name__ == '__main__':
    unittest.main() 