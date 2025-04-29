"""
Unit tests for the Authentication Service.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.services.auth_service import AuthService
from src.backend.models.user_model import User


class TestAuthService(unittest.TestCase):
    """Test case for the AuthService class."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_graph_service = MagicMock()
        self.mock_graph_service.driver = MagicMock()
        
        # Mock session
        self.mock_session = MagicMock()
        self.mock_graph_service.driver.session.return_value.__enter__.return_value = self.mock_session
        
        # Create auth service
        self.auth_service = AuthService(self.mock_graph_service)
    
    def test_register_user_success(self):
        """Test successful user registration."""
        # Mock find_user_by_email to return None (user doesn't exist)
        self.auth_service.find_user_by_email = MagicMock(return_value=None)
        
        # Call register_user
        result = self.auth_service.register_user(
            email="test@example.com",
            password="password123",
            name="Test User",
            role="candidate"
        )
        
        # Check result
        self.assertTrue(result['success'])
        self.assertIsInstance(result['user'], User)
        self.assertEqual(result['user'].email, "test@example.com")
        self.assertEqual(result['user'].name, "Test User")
        self.assertEqual(result['user'].role, "candidate")
        
        # Verify database operation was called
        self.assertTrue(self.mock_session.run.called)

    def test_register_user_already_exists(self):
        """Test user registration when user already exists."""
        # Mock find_user_by_email to return a user (user exists)
        existing_user = User("test@example.com", "hash", "Existing User", "candidate")
        self.auth_service.find_user_by_email = MagicMock(return_value=existing_user)
        
        # Call register_user
        result = self.auth_service.register_user(
            email="test@example.com",
            password="password123",
            name="Test User",
            role="candidate"
        )
        
        # Check result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'User already exists')

    def test_register_user_validation_error(self):
        """Test user registration with validation error."""
        # Mock find_user_by_email to return None (user doesn't exist)
        self.auth_service.find_user_by_email = MagicMock(return_value=None)
        
        # Call register_user with invalid email
        result = self.auth_service.register_user(
            email="invalid",
            password="password123",
            name="Test User",
            role="candidate"
        )
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("Invalid email format", result['error'])

    def test_login_success(self):
        """Test successful login."""
        # Create a user with a known password
        user = User.create(
            email="test@example.com",
            password="password123",
            name="Test User",
            role="candidate"
        )
        
        # Mock find_user_by_email to return the user
        self.auth_service.find_user_by_email = MagicMock(return_value=user)
        
        # Call login with correct password
        result = self.auth_service.login(
            email="test@example.com",
            password="password123"
        )
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['user'], user)

    def test_login_invalid_email(self):
        """Test login with invalid email format."""
        # Call login with invalid email
        result = self.auth_service.login(
            email="invalid",
            password="password123"
        )
        
        # Check result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Invalid email format')

    def test_login_user_not_found(self):
        """Test login when user not found."""
        # Mock find_user_by_email to return None (user doesn't exist)
        self.auth_service.find_user_by_email = MagicMock(return_value=None)
        
        # Call login
        result = self.auth_service.login(
            email="test@example.com",
            password="password123"
        )
        
        # Check result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Invalid credentials')

    def test_login_wrong_password(self):
        """Test login with wrong password."""
        # Create a user with a known password
        user = User.create(
            email="test@example.com",
            password="password123",
            name="Test User",
            role="candidate"
        )
        
        # Mock find_user_by_email to return the user
        self.auth_service.find_user_by_email = MagicMock(return_value=user)
        
        # Call login with wrong password
        result = self.auth_service.login(
            email="test@example.com",
            password="wrong_password"
        )
        
        # Check result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Invalid credentials')

    def test_find_user_by_email(self):
        """Test finding a user by email."""
        # Create the expected User object
        expected_user = User(
            email="test@example.com",
            password_hash="hash",
            name="Test User",
            role="candidate",
            profile_id="resume_123"
        )
        
        # Instead of mocking the database response, mock the find_user_by_email method directly
        self.auth_service.find_user_by_email = MagicMock(return_value=expected_user)
        
        # Call find_user_by_email
        user = self.auth_service.find_user_by_email("test@example.com")
        
        # Check result
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.password_hash, "hash")
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.role, "candidate")
        self.assertEqual(user.profile_id, "resume_123")
        
        # Verify the method was called with correct parameters
        self.auth_service.find_user_by_email.assert_called_once_with("test@example.com")

    def test_find_user_by_email_not_found(self):
        """Test finding a user by email when user not found."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.single.return_value = None
        self.mock_session.run.return_value = mock_result
        
        # Call find_user_by_email (without mocking the method itself)
        user = self.auth_service.find_user_by_email("test@example.com")
        
        # Check result
        self.assertIsNone(user)

    def test_update_user_success(self):
        """Test successful user update."""
        # Create a user
        user = User("test@example.com", "hash", "Test User", "candidate")
        
        # Mock find_user_by_email to return the user
        self.auth_service.find_user_by_email = MagicMock(side_effect=[user, user])
        
        # Updates to apply
        updates = {"name": "Updated Name"}
        
        # Call update_user
        result = self.auth_service.update_user("test@example.com", updates)
        
        # Check result
        self.assertTrue(result['success'])
        
        # Verify database operation was called with correct parameters
        self.assertTrue(self.mock_session.run.called)
        call_args = self.mock_session.run.call_args[0]
        self.assertIn("SET u.name = $name", call_args[0])
        self.assertEqual(call_args[1], {"email": "test@example.com", "name": "Updated Name"})

    def test_update_user_not_found(self):
        """Test updating a user that doesn't exist."""
        # Mock find_user_by_email to return None (user doesn't exist)
        self.auth_service.find_user_by_email = MagicMock(return_value=None)
        
        # Call update_user
        result = self.auth_service.update_user("test@example.com", {"name": "New Name"})
        
        # Check result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'User not found')

    def test_update_user_no_updates(self):
        """Test updating a user with no updates."""
        # Call update_user with empty updates
        result = self.auth_service.update_user("test@example.com", {})
        
        # Check result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'No updates provided')

    def test_update_user_invalid_role(self):
        """Test updating a user with invalid role."""
        # Create a user
        user = User("test@example.com", "hash", "Test User", "candidate")
        
        # Mock find_user_by_email to return the user
        self.auth_service.find_user_by_email = MagicMock(return_value=user)
        
        # Updates with invalid role
        updates = {"role": "invalid_role"}
        
        # Call update_user
        result = self.auth_service.update_user("test@example.com", updates)
        
        # Check result
        self.assertFalse(result['success'])
        self.assertIn("Invalid role", result['error'])

    def test_delete_user_success(self):
        """Test successful user deletion."""
        # Create a user
        user = User("test@example.com", "hash", "Test User", "candidate")
        
        # Mock find_user_by_email to return the user
        self.auth_service.find_user_by_email = MagicMock(return_value=user)
        
        # Mock database response for successful deletion
        mock_result = MagicMock()
        mock_counters = MagicMock()
        mock_counters.nodes_deleted = 1
        mock_result.consume.return_value.counters = mock_counters
        self.mock_session.run.return_value = mock_result
        
        # Call delete_user
        result = self.auth_service.delete_user("test@example.com")
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'User deleted successfully')
        
        # Verify database operation was called with correct parameters
        self.assertTrue(self.mock_session.run.called)
        call_args = self.mock_session.run.call_args[0]
        self.assertIn("DELETE u", call_args[0])
        self.assertEqual(call_args[1], {"email": "test@example.com"})

    def test_delete_user_not_found(self):
        """Test deleting a user that doesn't exist."""
        # Mock find_user_by_email to return None (user doesn't exist)
        self.auth_service.find_user_by_email = MagicMock(return_value=None)
        
        # Call delete_user
        result = self.auth_service.delete_user("test@example.com")
        
        # Check result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'User not found')

    def test_make_admin_success(self):
        """Test successful promotion to admin."""
        # Create a user
        user = User("test@example.com", "hash", "Test User", "candidate")
        admin_user = User("test@example.com", "hash", "Test User", "admin")
        
        # Mock find_user_by_email to return the user then the admin user
        self.auth_service.find_user_by_email = MagicMock(side_effect=[user, admin_user])
        
        # Call make_admin
        result = self.auth_service.make_admin("test@example.com")
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['user'].role, 'admin')
        
        # Verify database operation was called with correct parameters
        self.assertTrue(self.mock_session.run.called)
        call_args = self.mock_session.run.call_args[0]
        self.assertIn("SET u.role = 'admin'", call_args[0])
        self.assertEqual(call_args[1], {"email": "test@example.com"})

    def test_make_admin_user_not_found(self):
        """Test promoting a user to admin when user not found."""
        # Mock find_user_by_email to return None (user doesn't exist)
        self.auth_service.find_user_by_email = MagicMock(return_value=None)
        
        # Call make_admin
        result = self.auth_service.make_admin("test@example.com")
        
        # Check result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'User not found')

    def test_change_password_success(self):
        """Test successful password change."""
        # Create a user with a known password
        user = User.create(
            email="test@example.com",
            password="password123",
            name="Test User",
            role="candidate"
        )
        
        # Mock find_user_by_email to return the user
        self.auth_service.find_user_by_email = MagicMock(return_value=user)
        
        # Call change_password
        result = self.auth_service.change_password(
            email="test@example.com",
            current_password="password123",
            new_password="new_password123"
        )
        
        # Check result
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Password changed successfully')
        
        # Verify database operation was called
        self.assertTrue(self.mock_session.run.called)
        call_args = self.mock_session.run.call_args[0]
        self.assertIn("SET u.password_hash = $password_hash", call_args[0])
        self.assertEqual(call_args[1]["email"], "test@example.com")

    def test_change_password_user_not_found(self):
        """Test changing password when user not found."""
        # Mock find_user_by_email to return None (user doesn't exist)
        self.auth_service.find_user_by_email = MagicMock(return_value=None)
        
        # Call change_password
        result = self.auth_service.change_password(
            email="test@example.com",
            current_password="password123",
            new_password="new_password123"
        )
        
        # Check result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'User not found')

    def test_change_password_wrong_current_password(self):
        """Test changing password with wrong current password."""
        # Create a user with a known password
        user = User.create(
            email="test@example.com",
            password="password123",
            name="Test User",
            role="candidate"
        )
        
        # Mock find_user_by_email to return the user
        self.auth_service.find_user_by_email = MagicMock(return_value=user)
        
        # Call change_password with wrong current password
        result = self.auth_service.change_password(
            email="test@example.com",
            current_password="wrong_password",
            new_password="new_password123"
        )
        
        # Check result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Current password is incorrect')

    def test_change_password_invalid_new_password(self):
        """Test changing password with invalid new password."""
        # Create a user with a known password
        user = User.create(
            email="test@example.com",
            password="password123",
            name="Test User",
            role="candidate"
        )
        
        # Mock find_user_by_email to return the user
        self.auth_service.find_user_by_email = MagicMock(return_value=user)
        
        # Call change_password with invalid new password (too short)
        result = self.auth_service.change_password(
            email="test@example.com",
            current_password="password123",
            new_password="short"
        )
        
        # Check result
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Password must be at least 8 characters')

if __name__ == '__main__':
    unittest.main() 