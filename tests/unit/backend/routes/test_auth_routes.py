"""
Unit tests for the Authentication Routes.
"""

import unittest
import json
from unittest.mock import MagicMock, patch
import os
import sys
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.models.user_model import User
from src.backend.routes.auth_routes import init_routes


class TestAuthRoutes(unittest.TestCase):
    """Test case for the Authentication Routes."""
    
    def setUp(self):
        """Set up test environment."""
        # Create mock auth service
        self.mock_auth_service = MagicMock()
        
        # Create Flask app
        self.app = Flask(__name__)
        self.app.config["JWT_SECRET_KEY"] = "test-secret-key"
        self.app.config["TESTING"] = True
        
        # Initialize JWT
        self.jwt = JWTManager(self.app)
        
        # Initialize routes with mock service
        init_routes(self.app, self.mock_auth_service)
        
        # Configure user loader for JWT
        @self.jwt.user_lookup_loader
        def user_lookup_callback(_jwt_header, jwt_data):
            identity = jwt_data["sub"]
            # Return a dummy user for testing
            if identity == "admin@example.com":
                return User("admin@example.com", "hash", "Admin", "admin")
            elif identity == "candidate@example.com":
                return User("candidate@example.com", "hash", "Candidate", "candidate", "resume_123")
            elif identity == "manager@example.com":
                return User("manager@example.com", "hash", "Manager", "hiring_manager", "job_123")
            return None
        
        # Create test client
        self.client = self.app.test_client()
    
    def create_test_token(self, email):
        """Create a JWT token for testing."""
        with self.app.test_request_context():
            return create_access_token(identity=email)
    
    def test_register_success(self):
        """Test successful user registration."""
        # Mock auth service response
        test_user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            role="candidate"
        )
        self.mock_auth_service.register_user.return_value = {
            'success': True,
            'user': test_user
        }
        
        # Send request
        response = self.client.post(
            '/api/auth/register',
            json={
                'email': 'test@example.com',
                'password': 'password123',
                'name': 'Test User',
                'role': 'candidate'
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertEqual(data['user']['email'], 'test@example.com')
        self.assertEqual(data['user']['name'], 'Test User')
        self.assertEqual(data['user']['role'], 'candidate')
        
        # Verify service was called with correct parameters - using positional arguments to match actual call
        self.mock_auth_service.register_user.assert_called_with(
            'test@example.com',
            'password123',
            'Test User',
            'candidate'
        )
    
    def test_register_missing_fields(self):
        """Test registration with missing fields."""
        # Send request with missing fields
        response = self.client.post(
            '/api/auth/register',
            json={
                'email': 'test@example.com',
                'name': 'Test User'
                # Missing password and role
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Missing required fields', data['error'])
    
    def test_register_user_exists(self):
        """Test registration when user already exists."""
        # Mock auth service response for user already exists
        self.mock_auth_service.register_user.return_value = {
            'success': False,
            'error': 'User already exists'
        }
        
        # Send request
        response = self.client.post(
            '/api/auth/register',
            json={
                'email': 'existing@example.com',
                'password': 'password123',
                'name': 'Existing User',
                'role': 'candidate'
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 409)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'User already exists')
    
    def test_login_success(self):
        """Test successful login."""
        # Mock auth service response
        test_user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            role="candidate"
        )
        self.mock_auth_service.login.return_value = {
            'success': True,
            'user': test_user
        }
        
        # Send request
        response = self.client.post(
            '/api/auth/login',
            json={
                'email': 'test@example.com',
                'password': 'password123'
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertEqual(data['user']['email'], 'test@example.com')
        self.assertEqual(data['user']['name'], 'Test User')
        self.assertEqual(data['user']['role'], 'candidate')
        
        # Verify service was called with correct parameters - using positional arguments to match actual call
        self.mock_auth_service.login.assert_called_with(
            'test@example.com',
            'password123'
        )
    
    def test_login_missing_fields(self):
        """Test login with missing fields."""
        # Send request with missing fields
        response = self.client.post(
            '/api/auth/login',
            json={
                'email': 'test@example.com'
                # Missing password
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Missing required fields', data['error'])
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        # Mock auth service response for invalid credentials
        self.mock_auth_service.login.return_value = {
            'success': False,
            'error': 'Invalid credentials'
        }
        
        # Send request
        response = self.client.post(
            '/api/auth/login',
            json={
                'email': 'test@example.com',
                'password': 'wrong_password'
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Invalid credentials')
    
    def test_get_user_profile(self):
        """Test getting user profile."""
        # Create authorization header with JWT for admin
        admin_token = self.create_test_token("admin@example.com")
        
        # Send request with authorization
        response = self.client.get(
            '/api/auth/me',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'admin@example.com')
        self.assertEqual(data['user']['role'], 'admin')
    
    def test_get_user_profile_unauthorized(self):
        """Test getting user profile without authentication."""
        # Send request without authorization
        response = self.client.get('/api/auth/me')
        
        # Check response
        self.assertEqual(response.status_code, 401)
    
    def test_update_profile_success(self):
        """Test successful profile update."""
        # Mock auth service response
        updated_user = User(
            email="admin@example.com",
            password_hash="hashed_password",
            name="Updated Admin",
            role="admin"
        )
        self.mock_auth_service.update_user.return_value = {
            'success': True,
            'user': updated_user
        }
        
        # Create authorization header with JWT for admin
        admin_token = self.create_test_token("admin@example.com")
        
        # Send request with authorization
        response = self.client.put(
            '/api/auth/update-profile',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'name': 'Updated Admin'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['name'], 'Updated Admin')
        
        # Verify service was called with correct parameters
        self.mock_auth_service.update_user.assert_called_with(
            'admin@example.com',
            {'name': 'Updated Admin'}
        )
    
    def test_update_profile_error(self):
        """Test profile update with error."""
        # Mock auth service response for error
        self.mock_auth_service.update_user.return_value = {
            'success': False,
            'error': 'Update failed'
        }
        
        # Create authorization header with JWT for admin
        admin_token = self.create_test_token("admin@example.com")
        
        # Send request with authorization
        response = self.client.put(
            '/api/auth/update-profile',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'role': 'invalid_role'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Update failed')
    
    def test_change_password_success(self):
        """Test successful password change."""
        # Mock auth service response
        self.mock_auth_service.change_password.return_value = {
            'success': True,
            'message': 'Password changed successfully'
        }
        
        # Create authorization header with JWT for admin
        admin_token = self.create_test_token("admin@example.com")
        
        # Send request with authorization
        response = self.client.post(
            '/api/auth/change-password',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'current_password': 'old_password',
                'new_password': 'new_password123'
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'Password changed successfully')
        
        # Verify service was called with correct parameters
        self.mock_auth_service.change_password.assert_called_with(
            'admin@example.com',
            'old_password',
            'new_password123'
        )
    
    def test_change_password_missing_fields(self):
        """Test password change with missing fields."""
        # Create authorization header with JWT for admin
        admin_token = self.create_test_token("admin@example.com")
        
        # Send request with missing fields
        response = self.client.post(
            '/api/auth/change-password',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'current_password': 'old_password'
                # Missing new_password
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Missing required fields', data['error'])
    
    def test_change_password_error(self):
        """Test password change with error."""
        # Mock auth service response for error
        self.mock_auth_service.change_password.return_value = {
            'success': False,
            'error': 'Current password is incorrect'
        }
        
        # Create authorization header with JWT for admin
        admin_token = self.create_test_token("admin@example.com")
        
        # Send request with authorization
        response = self.client.post(
            '/api/auth/change-password',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'current_password': 'wrong_password',
                'new_password': 'new_password123'
            }
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Current password is incorrect')
    
    def test_admin_access(self):
        """Test admin only endpoint access."""
        # Create tokens for different user types
        admin_token = self.create_test_token("admin@example.com")
        candidate_token = self.create_test_token("candidate@example.com")
        
        # Test admin access - should succeed
        response = self.client.get(
            '/api/auth/admin/users',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        self.assertEqual(response.status_code, 200)
        
        # Test non-admin access - should fail
        response = self.client.get(
            '/api/auth/admin/users',
            headers={'Authorization': f'Bearer {candidate_token}'}
        )
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Unauthorized access', data['error'])
    
    def test_make_admin_success(self):
        """Test successful promote to admin."""
        # Mock auth service response
        promoted_user = User(
            email="user@example.com",
            password_hash="hashed_password",
            name="Test User",
            role="admin"
        )
        self.mock_auth_service.make_admin.return_value = {
            'success': True,
            'user': promoted_user
        }
        
        # Create authorization header with JWT for admin
        admin_token = self.create_test_token("admin@example.com")
        
        # Send request with authorization
        response = self.client.post(
            '/api/auth/admin/make-admin',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'email': 'user@example.com'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('user@example.com promoted to admin', data['message'])
        self.assertIn('user', data)
        self.assertEqual(data['user']['role'], 'admin')
        
        # Verify service was called with correct parameters
        self.mock_auth_service.make_admin.assert_called_with('user@example.com')
    
    def test_make_admin_missing_email(self):
        """Test promote to admin with missing email."""
        # Create authorization header with JWT for admin
        admin_token = self.create_test_token("admin@example.com")
        
        # Send request with missing email
        response = self.client.post(
            '/api/auth/admin/make-admin',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={}
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Missing email field', data['error'])
    
    def test_make_admin_error(self):
        """Test promote to admin with error."""
        # Mock auth service response for error
        self.mock_auth_service.make_admin.return_value = {
            'success': False,
            'error': 'User not found'
        }
        
        # Create authorization header with JWT for admin
        admin_token = self.create_test_token("admin@example.com")
        
        # Send request with authorization
        response = self.client.post(
            '/api/auth/admin/make-admin',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'email': 'nonexistent@example.com'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'User not found')
    
    def test_delete_user_success(self):
        """Test successful user deletion."""
        # Mock auth service response
        self.mock_auth_service.delete_user.return_value = {
            'success': True,
            'message': 'User deleted successfully'
        }
        
        # Create authorization header with JWT for admin
        admin_token = self.create_test_token("admin@example.com")
        
        # Send request with authorization
        response = self.client.delete(
            '/api/auth/admin/delete-user/user@example.com',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertEqual(data['message'], 'User deleted successfully')
        
        # Verify service was called with correct parameters
        self.mock_auth_service.delete_user.assert_called_with('user@example.com')
    
    def test_delete_user_error(self):
        """Test user deletion with error."""
        # Mock auth service response for error
        self.mock_auth_service.delete_user.return_value = {
            'success': False,
            'error': 'User not found'
        }
        
        # Create authorization header with JWT for admin
        admin_token = self.create_test_token("admin@example.com")
        
        # Send request with authorization
        response = self.client.delete(
            '/api/auth/admin/delete-user/nonexistent@example.com',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'User not found')
    
    def test_delete_user_unauthorized(self):
        """Test user deletion without admin privileges."""
        # Create authorization header with JWT for non-admin
        candidate_token = self.create_test_token("candidate@example.com")
        
        # Send request with non-admin authorization
        response = self.client.delete(
            '/api/auth/admin/delete-user/user@example.com',
            headers={'Authorization': f'Bearer {candidate_token}'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Unauthorized access', data['error'])


if __name__ == '__main__':
    unittest.main() 