"""
Unit tests for the job routes.
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

from src.backend.routes.job_routes import init_routes, job_bp
from src.backend.models.job_model import Job, JobSkill
from src.backend.services.job_service import JobService

# Create a mock user class for testing
@dataclass
class MockUser:
    email: str = "employer@example.com"
    is_hiring_manager: bool = True
    is_admin: bool = True  
    role: str = "admin"    

class TestJobRoutes(unittest.TestCase):
    """Test case for the job routes."""
    
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
        
        # Create a sample job
        self.sample_job = Job(
            job_id="job_123",
            title="Software Engineer",
            company="Tech Company",
            location="San Francisco, CA",
            owner_email="employer@example.com",
            domain="Software Development"
        )
        
        # Create an app context for the tests
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create mock services
        self.mock_job_service = MagicMock(spec=JobService)
        
        # Now that we have an app context, set up the routes
        init_routes(self.app, self.mock_job_service)
        
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
    
    def test_get_all_jobs(self):
        """Test getting all jobs."""
        # Mock the service response
        result = {
            'success': True,
            'jobs': [self.sample_job.to_api_dict()]
        }
        self.mock_job_service.find_jobs.return_value = result
        
        # Make the request
        response = self.client.get('/api/jobs')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['jobs']), 1)
        self.assertEqual(data['jobs'][0]['job_id'], "job_123")
        self.mock_job_service.find_jobs.assert_called_once()
    
    def test_get_all_jobs_with_filters(self):
        """Test getting jobs with query parameters."""
        # Mock the service response
        result = {
            'success': True,
            'jobs': [self.sample_job.to_api_dict()]
        }
        self.mock_job_service.find_jobs.return_value = result
        
        # Make the request with query parameters
        response = self.client.get('/api/jobs?company=Tech&domain=Software&location=San Francisco&owner_email=employer@example.com&limit=5&offset=10')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        
        # Verify filters were passed correctly
        expected_filters = {
            'company': 'Tech',
            'domain': 'Software',
            'location': 'San Francisco',
            'owner_email': 'employer@example.com'
        }
        self.mock_job_service.find_jobs.assert_called_once_with(expected_filters, 5, 10)
    
    def test_get_all_jobs_failure(self):
        """Test getting all jobs when service returns an error."""
        # Mock the service response for failure
        result = {
            'success': False,
            'error': 'Database error'
        }
        self.mock_job_service.find_jobs.return_value = result
        
        # Make the request
        response = self.client.get('/api/jobs')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Database error')
    
    def test_get_job_by_id_success(self):
        """Test getting a job by ID successfully."""
        # Mock the service response
        result = {
            'success': True,
            'job': self.sample_job.to_api_dict(),
            'skills': {'primary': [], 'secondary': []}
        }
        self.mock_job_service.get_job.return_value = result
        
        # Make the request
        response = self.client.get('/api/jobs/job_123')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['job']['job_id'], "job_123")
        self.mock_job_service.get_job.assert_called_once_with("job_123")
    
    def test_get_job_by_id_not_found(self):
        """Test getting a job by ID when not found."""
        # Mock the service response
        result = {
            'success': False,
            'error': 'Job not found'
        }
        self.mock_job_service.get_job.return_value = result
        
        # Make the request
        response = self.client.get('/api/jobs/job_999')
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'Job not found')
        self.mock_job_service.get_job.assert_called_once_with("job_999")
    
    def test_create_job_success(self):
        """Test creating a job successfully."""
        # Mock the service response
        result = {
            'success': True,
            'job_id': 'job_123'
        }
        self.mock_job_service.create_job.return_value = result
        
        # Job data to send
        job_data = {
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "San Francisco, CA",
            "summary": "A great job opportunity",
            "domain": "Software Development",
            "responsibilities": ["Code", "Test"],
            "qualifications": ["Bachelor's degree", "2 years experience"]
        }
        
        # Make the request
        response = self.client.post(
            '/api/jobs/create',
            data=json.dumps(job_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['job_id'], 'job_123')
        self.mock_job_service.create_job.assert_called_once()
    
    def test_create_job_with_primary_secondary_skills(self):
        """Test creating a job with primary and secondary skills."""
        # Mock the service response
        result = {
            'success': True,
            'job_id': 'job_123'
        }
        self.mock_job_service.create_job.return_value = result
        
        # Job data with primary_skills and secondary_skills
        job_data = {
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "San Francisco, CA",
            "domain": "Software Development",
            "primary_skills": [
                {"skill_id": "python_123", "name": "Python", "importance": 0.9, "proficiency": "advanced"}
            ],
            "secondary_skills": [
                {"skill_id": "javascript_123", "name": "JavaScript", "importance": 0.7, "proficiency": "intermediate"}
            ]
        }
        
        # Make the request
        response = self.client.post(
            '/api/jobs/create',
            data=json.dumps(job_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['job_id'], 'job_123')
        
        # Check that skills were formatted correctly in the call to the service
        job_data_expected = self.mock_job_service.create_job.call_args[0][0]
        self.assertIn('skills', job_data_expected)
        self.assertEqual(job_data_expected['skills']['primary'], job_data['primary_skills'])
        self.assertEqual(job_data_expected['skills']['secondary'], job_data['secondary_skills'])
        self.assertNotIn('primary_skills', job_data_expected)
        self.assertNotIn('secondary_skills', job_data_expected)
    
    def test_create_job_not_hiring_manager(self):
        """Test creating a job when user is not a hiring manager."""
        # Set the user as a non-hiring manager
        self.mock_get_current_user.return_value = MockUser(is_hiring_manager=False, is_admin=False)
        
        # Job data to send
        job_data = {
            "title": "Software Engineer",
            "company": "Tech Company"
        }
        
        # Make the request
        response = self.client.post(
            '/api/jobs/create',
            data=json.dumps(job_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['error'], 'Only hiring managers can post jobs')
        self.mock_job_service.create_job.assert_not_called()
    
    def test_create_job_failure(self):
        """Test creating a job that fails at the service level."""
        # Mock the service response for failure
        result = {
            'success': False,
            'error': 'Missing required fields'
        }
        self.mock_job_service.create_job.return_value = result
        
        # Job data to send (incomplete)
        job_data = {
            "title": "Software Engineer"
        }
        
        # Make the request
        response = self.client.post(
            '/api/jobs/create',
            data=json.dumps(job_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Missing required fields')
    
    def test_update_job_success(self):
        """Test updating a job successfully."""
        # Mock the service response
        result = {
            'success': True,
            'job_id': 'job_123'
        }
        self.mock_job_service.update_job.return_value = result
        
        # Update data
        update_data = {
            "title": "Senior Software Engineer"
        }
        
        # Make the request
        response = self.client.put(
            '/api/jobs/job_123',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['job_id'], 'job_123')
        self.mock_job_service.update_job.assert_called_once()
    
    def test_update_job_failure(self):
        """Test updating a job that fails at the service level."""
        # Mock the service response for failure
        result = {
            'success': False,
            'error': 'Job not found or unauthorized'
        }
        self.mock_job_service.update_job.return_value = result
        
        # Update data
        update_data = {
            "title": "Senior Software Engineer"
        }
        
        # Make the request
        response = self.client.put(
            '/api/jobs/job_999',
            data=json.dumps(update_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Job not found or unauthorized')
    
    def test_delete_job_success(self):
        """Test deleting a job successfully."""
        # Mock the service response
        result = {
            'success': True,
            'message': 'Job deleted successfully'
        }
        self.mock_job_service.delete_job.return_value = result
        
        # Make the request
        response = self.client.delete(
            '/api/jobs/job_123',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], 'Job deleted successfully')
        self.mock_job_service.delete_job.assert_called_once()
    
    def test_delete_job_failure(self):
        """Test deleting a job that fails at the service level."""
        # Mock the service response for failure
        result = {
            'success': False,
            'error': 'Job not found or unauthorized'
        }
        self.mock_job_service.delete_job.return_value = result
        
        # Make the request
        response = self.client.delete(
            '/api/jobs/job_999',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Job not found or unauthorized')
    
    def test_get_matching_candidates_success(self):
        """Test getting matching candidates for a job successfully."""
        # Sample candidate data
        candidates_data = [
            {
                "email": "candidate1@example.com",
                "name": "Candidate One",
                "matching_score": 0.85
            },
            {
                "email": "candidate2@example.com",
                "name": "Candidate Two",
                "matching_score": 0.75
            }
        ]
        
        # Mock the service response
        result = {
            'success': True,
            'candidates': candidates_data
        }
        self.mock_job_service.get_matching_candidates.return_value = result
        
        # Make the request
        response = self.client.get(
            '/api/jobs/job_123/candidates?limit=10',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['email'], 'candidate1@example.com')
        self.mock_job_service.get_matching_candidates.assert_called_once()
    
    def test_get_matching_candidates_no_permission(self):
        """Test getting candidates when user has no permission."""
        # Set user as non-admin hiring manager
        self.mock_get_current_user.return_value = MockUser(is_admin=False, role='hiring_manager')
        
        # Mock the job service to show that the user is not the owner
        job_info = {
            'success': True,
            'job': {'owner_email': 'different_user@example.com'}
        }
        self.mock_job_service.get_job.return_value = job_info
        
        # Mock the permission check
        self.mock_job_service.job_repository = MagicMock()
        self.mock_job_service.job_repository.check_job_owner_relationship.return_value = False
        
        # Make the request
        response = self.client.get(
            '/api/jobs/job_123/candidates',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['error'], "You don't have permission to view candidates for this job")
        self.mock_job_service.get_matching_candidates.assert_not_called()
    
    def test_get_matching_candidates_with_custom_weights(self):
        """Test getting candidates with custom matching weights."""
        # Sample candidate data
        candidates_data = [{"name": "Candidate One", "matching_score": 0.9}]
        
        # Mock the service response
        result = {
            'success': True,
            'candidates': candidates_data
        }
        self.mock_job_service.get_matching_candidates.return_value = result
        
        # Make the request with custom weights
        response = self.client.get(
            '/api/jobs/job_123/candidates?skills_weight=0.8&location_weight=0.1&semantic_weight=0.1',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Verify weights were normalized correctly
        call_args = self.mock_job_service.get_matching_candidates.call_args
        weights = call_args[0][2]
        self.assertAlmostEqual(weights['skills'], 0.8)
        self.assertAlmostEqual(weights['location'], 0.1)
        self.assertAlmostEqual(weights['semantic'], 0.1)
    
    def test_get_matching_candidates_failure(self):
        """Test getting candidates with service error."""
        # Mock the service response
        result = {
            'success': False,
            'error': 'Job not found'
        }
        self.mock_job_service.get_matching_candidates.return_value = result
        
        # Make the request
        response = self.client.get(
            '/api/jobs/job_999/candidates',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Job not found')
    
    def test_get_user_jobs(self):
        """Test getting jobs by current user."""
        # Mock the service response
        result = {
            'success': True,
            'jobs': [self.sample_job.to_api_dict()]
        }
        self.mock_job_service.find_jobs.return_value = result
        
        # Make the request
        response = self.client.get(
            '/api/jobs/user',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['jobs']), 1)
        self.assertEqual(data['jobs'][0]['job_id'], 'job_123')
        
        # Verify correct filters were passed to service
        call_args = self.mock_job_service.find_jobs.call_args
        self.assertEqual(call_args[0][0], {'owner_email': 'employer@example.com'})
    
    def test_get_job_candidates_enhanced(self):
        """Test getting enhanced matching candidates."""
        # Sample candidate data
        candidates_data = [
            {"name": "Candidate One", "matching_score": 0.9, "skillScore": 90, "locationScore": 100}
        ]
        
        # Mock the service response
        result = {
            'success': True,
            'candidates': candidates_data
        }
        self.mock_job_service.get_matching_candidates.return_value = result
        
        # Make the request
        response = self.client.get(
            '/api/jobs/job_123/candidates/enhanced',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Candidate One')
        
        # Make sure weights are passed along
        call_args = self.mock_job_service.get_matching_candidates.call_args
        self.assertIsNotNone(call_args[0][2])  # weights parameter
    
    def test_get_job_candidates_enhanced_no_permission(self):
        """Test getting enhanced candidates without permission."""
        # Set user as non-admin hiring manager
        self.mock_get_current_user.return_value = MockUser(is_admin=False, role='hiring_manager')
        
        # Mock the job service to show that the user is not the owner
        job_info = {
            'success': True,
            'job': {'owner_email': 'different_user@example.com'}
        }
        self.mock_job_service.get_job.return_value = job_info
        
        # Mock the permission check
        self.mock_job_service.job_repository = MagicMock()
        self.mock_job_service.job_repository.check_job_owner_relationship.return_value = False
        
        # Make the request
        response = self.client.get(
            '/api/jobs/job_123/candidates/enhanced',
            headers={'Authorization': 'Bearer test_token'}
        )
        data = json.loads(response.data)
        
        # Assertions
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['error'], "You don't have permission to view candidates for this job")

if __name__ == '__main__':
    unittest.main() 