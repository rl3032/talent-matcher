"""
Unit tests for the candidate routes.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import json
from flask import Flask
from dataclasses import dataclass
from flask_jwt_extended import JWTManager

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.routes.candidate_routes import init_routes, candidate_bp
from src.backend.models.candidate_model import Candidate, CandidateSkill, Experience, Education
from src.backend.services.candidate_service import CandidateService

# Create a mock user class for testing
@dataclass
class MockUser:
    email: str = "recruiter@example.com"
    is_admin: bool = True
    role: str = "admin"

class TestCandidateRoutes(unittest.TestCase):
    """Test case for the candidate routes."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a Flask app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        
        # Configure JWT settings
        self.app.config['JWT_SECRET_KEY'] = 'test_secret_key'
        self.app.config['JWT_TOKEN_LOCATION'] = ['headers']
        self.app.config['JWT_HEADER_NAME'] = 'Authorization'
        self.app.config['JWT_HEADER_TYPE'] = 'Bearer'
        
        # Initialize JWT extension
        self.jwt = JWTManager(self.app)
        
        # Create a test client
        self.client = self.app.test_client()
        
        # Create a sample candidate
        self.sample_candidate = {
            "resume_id": "resume_123",
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
                    "experience_id": "exp_1",
                    "title": "Senior Developer",
                    "company": "Tech Co",
                    "start_date": "2020-01-01",
                    "end_date": "Present",
                    "description": ["Led a team of 5 developers", "Implemented new features"]
                }
            ],
            "education": [
                {
                    "education_id": "edu_1",
                    "institution": "University of California",
                    "degree": "Bachelor of Science",
                    "field": "Computer Science",
                    "start_date": "2010-09-01",
                    "end_date": "2014-06-01"
                }
            ]
        }
        
        # Create an app context for the tests
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create mock services
        self.mock_candidate_service = MagicMock(spec=CandidateService)
        
        # Set up the routes
        init_routes(self.app, self.mock_candidate_service)
        
        # Start patching
        # Override the jwt_required decorator to be a no-op
        self.jwt_patcher = patch('flask_jwt_extended.view_decorators.verify_jwt_in_request')
        self.mock_verify_jwt = self.jwt_patcher.start()
        
        # Mock get_current_user function to return our test user
        self.get_user_patcher = patch('flask_jwt_extended.utils.get_current_user')
        self.mock_get_current_user = self.get_user_patcher.start()
        self.mock_get_current_user.return_value = MockUser()
    
    def tearDown(self):
        """Clean up after tests."""
        self.jwt_patcher.stop()
        self.get_user_patcher.stop()
        self.app_context.pop()
    
    def test_get_all_candidates(self):
        """Test getting all candidates."""
        # Mock the service response
        result = {
            'success': True,
            'candidates': [self.sample_candidate],
            'total': 1,
            'limit': 20,
            'offset': 0
        }
        self.mock_candidate_service.find_candidates.return_value = result
        
        # Make the request
        response = self.client.get('/api/candidates')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['candidates']), 1)
        self.assertEqual(data['candidates'][0]['resume_id'], "resume_123")
        self.mock_candidate_service.find_candidates.assert_called_once()

    def test_get_all_candidates_not_admin(self):
        """Test getting all candidates when user is not admin or hiring manager."""
        # Create a user with non-admin, non-hiring manager role
        non_admin_user = MockUser(is_admin=False, role='user')
        
        # Create a local patch to return non-admin user
        with patch('flask_jwt_extended.utils.get_current_user', return_value=non_admin_user):
            # Make the request
            response = self.client.get('/api/candidates')
            data = json.loads(response.data)
            
            # Assertions - expect forbidden
            self.assertEqual(response.status_code, 403)
            self.assertEqual(data['error'], "You don't have permission to view all candidates")
            self.mock_candidate_service.find_candidates.assert_not_called()

    def test_get_all_candidates_hiring_manager(self):
        """Test getting all candidates as a hiring manager."""
        # Create a hiring manager user
        hiring_manager = MockUser(is_admin=False, role='hiring_manager')
        
        # Create a local patch to return hiring manager user
        with patch('flask_jwt_extended.utils.get_current_user', return_value=hiring_manager):
            # Mock the service response
            result = {
                'success': True,
                'candidates': [self.sample_candidate],
                'total': 1,
                'limit': 20,
                'offset': 0
            }
            self.mock_candidate_service.find_candidates.return_value = result
            
            # Make the request
            response = self.client.get('/api/candidates')
            data = json.loads(response.data)
            
            # Assertions - hiring managers should have access
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data['success'])
            self.assertEqual(len(data['candidates']), 1)
            self.mock_candidate_service.find_candidates.assert_called_once()

    def test_get_all_candidates_with_filters(self):
        """Test getting candidates with filters."""
        # Mock the service response
        result = {
            'success': True,
            'candidates': [self.sample_candidate],
            'total': 1,
            'limit': 10,
            'offset': 0
        }
        self.mock_candidate_service.find_candidates.return_value = result
        
        # Make the request with query parameters
        response = self.client.get(
            '/api/candidates?domain=Software%20Development&location=San%20Francisco&skill=Python&limit=10&offset=0'
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        
        # Check that filters were properly constructed
        expected_filters = {
            'domain': 'Software Development',
            'location': 'San Francisco',
            'skill': 'Python'
        }
        self.mock_candidate_service.find_candidates.assert_called_once_with(expected_filters, 10, 0)

    def test_get_all_candidates_error(self):
        """Test getting all candidates when service returns an error."""
        # Mock the service response with an error
        result = {
            'success': False,
            'error': 'Database error'
        }
        self.mock_candidate_service.find_candidates.return_value = result
        
        # Make the request
        response = self.client.get('/api/candidates')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Database error')
    
    def test_get_candidate_by_id_success(self):
        """Test getting a candidate by ID successfully."""
        # Mock the service response
        result = {
            'success': True,
            'candidate': self.sample_candidate
        }
        self.mock_candidate_service.get_candidate.return_value = result
        
        # Make the request
        response = self.client.get('/api/candidates/resume_123')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['candidate']['resume_id'], "resume_123")
        self.mock_candidate_service.get_candidate.assert_called_once_with("resume_123")
    
    def test_get_candidate_by_id_not_found(self):
        """Test getting a candidate by ID when not found."""
        # Mock the service response
        result = {
            'success': False,
            'error': 'Candidate not found'
        }
        self.mock_candidate_service.get_candidate.return_value = result
        
        # Make the request
        response = self.client.get('/api/candidates/resume_999')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'Candidate not found')
        self.mock_candidate_service.get_candidate.assert_called_once_with("resume_999")
    
    def test_create_candidate_success(self):
        """Test creating a candidate successfully."""
        # Mock the service response
        result = {
            'success': True,
            'resume_id': 'resume_123'
        }
        self.mock_candidate_service.create_candidate.return_value = result
        
        # Candidate data to send
        candidate_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "title": "Software Engineer",
            "location": "San Francisco, CA",
            "domain": "Software Development",
            "summary": "Experienced software engineer with 5+ years of experience"
        }
        
        # Make the request
        response = self.client.post(
            '/api/candidates/create',
            data=json.dumps(candidate_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['resume_id'], 'resume_123')
        self.mock_candidate_service.create_candidate.assert_called_once()

    def test_create_candidate_error(self):
        """Test creating a candidate with validation error."""
        # Mock the service response
        result = {
            'success': False,
            'error': 'Missing required fields'
        }
        self.mock_candidate_service.create_candidate.return_value = result
        
        # Candidate data to send (incomplete)
        candidate_data = {
            "name": "John Doe"
        }
        
        # Make the request
        response = self.client.post(
            '/api/candidates/create',
            data=json.dumps(candidate_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Missing required fields')
        self.mock_candidate_service.create_candidate.assert_called_once()
    
    def test_update_candidate_success(self):
        """Test updating a candidate successfully."""
        # Mock the service response
        result = {
            'success': True,
            'resume_id': 'resume_123'
        }
        self.mock_candidate_service.update_candidate.return_value = result
        
        # Update data
        update_data = {
            "title": "Senior Software Engineer"
        }
        
        # Make the request
        response = self.client.put(
            '/api/candidates/resume_123',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['resume_id'], 'resume_123')
        self.mock_candidate_service.update_candidate.assert_called_once_with("resume_123", update_data)

    def test_update_candidate_not_found(self):
        """Test updating a candidate that doesn't exist."""
        # Mock the service response
        result = {
            'success': False,
            'error': 'Candidate not found'
        }
        self.mock_candidate_service.update_candidate.return_value = result
        
        # Update data
        update_data = {
            "title": "Senior Software Engineer"
        }
        
        # Make the request
        response = self.client.put(
            '/api/candidates/nonexistent',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Candidate not found')
        self.mock_candidate_service.update_candidate.assert_called_once_with("nonexistent", update_data)
    
    def test_delete_candidate_success(self):
        """Test deleting a candidate successfully."""
        # Mock the service response
        result = {
            'success': True,
            'message': 'Candidate deleted successfully'
        }
        self.mock_candidate_service.delete_candidate.return_value = result
        
        # Make the request
        response = self.client.delete(
            '/api/candidates/resume_123',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Candidate deleted successfully')
        self.mock_candidate_service.delete_candidate.assert_called_once_with("resume_123")

    def test_delete_candidate_not_admin(self):
        """Test deleting a candidate without admin privileges."""
        # Create a non-admin user
        non_admin_user = MockUser(is_admin=False, role='user')
        
        # Create a local patch
        with patch('flask_jwt_extended.utils.get_current_user', return_value=non_admin_user):
            # Make the request
            response = self.client.delete(
                '/api/candidates/resume_123',
                headers={'Authorization': 'Bearer test_token'}
            )
            data = json.loads(response.data)
            
            # Assertions
            self.assertEqual(response.status_code, 403)
            self.assertEqual(data['error'], 'Only administrators can delete candidate profiles')
            self.mock_candidate_service.delete_candidate.assert_not_called()

    def test_delete_candidate_not_found(self):
        """Test deleting a candidate that doesn't exist."""
        # Mock the service response
        result = {
            'success': False,
            'error': 'Candidate not found'
        }
        self.mock_candidate_service.delete_candidate.return_value = result
        
        # Make the request
        response = self.client.delete(
            '/api/candidates/nonexistent',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Candidate not found')
        self.mock_candidate_service.delete_candidate.assert_called_once_with("nonexistent")
    
    def test_get_matching_jobs_success(self):
        """Test getting matching jobs for a candidate successfully."""
        # Sample job data
        jobs_data = [
            {
                "job_id": "job_1",
                "title": "Software Engineer",
                "company": "Tech Co",
                "match_percentage": 85
            },
            {
                "job_id": "job_2",
                "title": "Web Developer",
                "company": "Web Co",
                "match_percentage": 75
            }
        ]
        
        # Mock the service response
        result = {
            'success': True,
            'jobs': jobs_data,
            'total': 2
        }
        self.mock_candidate_service.get_matching_jobs.return_value = result
        
        # Make the request
        response = self.client.get(
            '/api/candidates/resume_123/jobs?limit=10',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['job_id'], 'job_1')
        self.mock_candidate_service.get_matching_jobs.assert_called_once()

    def test_get_matching_jobs_with_custom_weights(self):
        """Test getting matching jobs with custom weights."""
        # Sample job data
        jobs_data = [
            {
                "job_id": "job_1",
                "title": "Software Engineer",
                "company": "Tech Co",
                "match_percentage": 85
            }
        ]
        
        # Mock the service response
        result = {
            'success': True,
            'jobs': jobs_data,
            'total': 1
        }
        self.mock_candidate_service.get_matching_jobs.return_value = result
        
        # Make the request with custom weights
        response = self.client.get(
            '/api/candidates/resume_123/jobs?skills_weight=0.8&location_weight=0.1&semantic_weight=0.1',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Check that weights were correctly passed
        call_args = self.mock_candidate_service.get_matching_jobs.call_args
        weights = call_args[0][2]
        self.assertAlmostEqual(weights['skills'], 0.8)
        self.assertAlmostEqual(weights['location'], 0.1)
        self.assertAlmostEqual(weights['semantic'], 0.1)

    def test_get_matching_jobs_error(self):
        """Test getting matching jobs with service error."""
        # Mock the service response
        result = {
            'success': False,
            'error': 'Candidate not found'
        }
        self.mock_candidate_service.get_matching_jobs.return_value = result
        
        # Make the request
        response = self.client.get(
            '/api/candidates/nonexistent/jobs',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Candidate not found')
    
    def test_get_candidate_matches_enhanced(self):
        """Test getting enhanced job matches for a candidate."""
        # Sample job data
        jobs_data = [
            {
                "job_id": "job_1",
                "title": "Software Engineer",
                "company": "Tech Co",
                "match_percentage": 85
            }
        ]
        
        # Mock the service response
        result = {
            'success': True,
            'jobs': jobs_data,
            'total': 1
        }
        self.mock_candidate_service.get_matching_jobs.return_value = result
        
        # Make the request
        response = self.client.get(
            '/api/candidates/resume_123/jobs/enhanced',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['job_id'], 'job_1')
        
        # The enhanced endpoint directly calls get_candidate_matches,
        # which calls the service method, so we only expect one call
        self.assertEqual(self.mock_candidate_service.get_matching_jobs.call_count, 1)

    def test_get_matches_enhanced_error(self):
        """Test getting enhanced matches with service error."""
        # Mock the service response
        result = {
            'success': False,
            'error': 'Candidate not found'
        }
        self.mock_candidate_service.get_matching_jobs.return_value = result
        
        # Make the request
        response = self.client.get(
            '/api/candidates/nonexistent/jobs/enhanced',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Candidate not found')
    
    def test_upload_resume(self):
        """Test uploading a resume."""
        # Mock the service response
        result = {
            'success': True,
            'resume_id': 'resume_123'
        }
        self.mock_candidate_service.create_candidate.return_value = result
        
        # Resume data to send
        resume_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "summary": "Experienced software engineer"
        }
        
        # Make the request
        response = self.client.post(
            '/api/candidates/resume/upload',
            data=json.dumps(resume_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['resume_id'], 'resume_123')
        self.mock_candidate_service.create_candidate.assert_called_once()

    def test_upload_resume_error(self):
        """Test uploading a resume with validation error."""
        # Mock the service response
        result = {
            'success': False,
            'error': 'Missing required fields'
        }
        self.mock_candidate_service.create_candidate.return_value = result
        
        # Resume data to send (incomplete)
        resume_data = {
            "name": "John Doe"
        }
        
        # Make the request
        response = self.client.post(
            '/api/candidates/resume/upload',
            data=json.dumps(resume_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Missing required fields')
        self.mock_candidate_service.create_candidate.assert_called_once()

if __name__ == '__main__':
    unittest.main() 