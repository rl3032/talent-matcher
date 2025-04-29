"""
Unit tests for the User model.
"""

import unittest
from unittest import mock
import os
import sys
from datetime import datetime

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.models.user_model import User

class TestUserModel(unittest.TestCase):
    """Test case for the User model."""
    
    def test_user_init(self):
        """Test User initialization."""
        # Create a user
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            role="candidate",
            profile_id="resume_123",
            created_at=datetime(2023, 1, 1)
        )
        
        # Check attributes
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.password_hash, "hashed_password")
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.role, "candidate")
        self.assertEqual(user.profile_id, "resume_123")
        self.assertEqual(user.created_at, datetime(2023, 1, 1))

    def test_user_to_dict(self):
        """Test converting User to dictionary."""
        # Create a user with a fixed datetime for testing
        test_date = datetime(2023, 1, 1)
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            role="candidate",
            profile_id="resume_123",
            created_at=test_date
        )
        
        # Convert to dictionary
        user_dict = user.to_dict()
        
        # Check dictionary contents
        self.assertEqual(user_dict["email"], "test@example.com")
        self.assertEqual(user_dict["name"], "Test User")
        self.assertEqual(user_dict["role"], "candidate")
        self.assertEqual(user_dict["profile_id"], "resume_123")
        self.assertEqual(user_dict["created_at"], test_date.isoformat())
        # Password hash should not be included
        self.assertNotIn("password_hash", user_dict)

    def test_user_role_properties(self):
        """Test User role properties."""
        # Admin user
        admin = User("admin@example.com", "hash", "Admin", "admin")
        self.assertTrue(admin.is_admin)
        self.assertFalse(admin.is_hiring_manager)
        self.assertFalse(admin.is_candidate)
        
        # Hiring manager
        manager = User("manager@example.com", "hash", "Manager", "hiring_manager")
        self.assertFalse(manager.is_admin)
        self.assertTrue(manager.is_hiring_manager)
        self.assertFalse(manager.is_candidate)
        
        # Candidate
        candidate = User("candidate@example.com", "hash", "Candidate", "candidate")
        self.assertFalse(candidate.is_admin)
        self.assertFalse(candidate.is_hiring_manager)
        self.assertTrue(candidate.is_candidate)

    def test_validate_email(self):
        """Test email validation."""
        # Valid emails
        self.assertTrue(User.validate_email("user@example.com"))
        self.assertTrue(User.validate_email("user.name@example.co.uk"))
        self.assertTrue(User.validate_email("user+tag@example.com"))
        
        # Invalid emails
        self.assertFalse(User.validate_email("invalid"))
        self.assertFalse(User.validate_email("invalid@"))
        self.assertFalse(User.validate_email("@example.com"))
        self.assertFalse(User.validate_email("user@example"))

    def test_validate_password(self):
        """Test password validation."""
        # Valid passwords (meets minimum length)
        self.assertTrue(User.validate_password("password123"))
        self.assertTrue(User.validate_password("12345678"))
        
        # Invalid passwords (too short)
        self.assertFalse(User.validate_password("pass"))
        self.assertFalse(User.validate_password("1234567"))

    def test_user_create(self):
        """Test User.create factory method."""
        # Valid user creation
        user = User.create(
            email="test@example.com",
            password="password123",
            name="Test User",
            role="candidate"
        )
        
        # Check attributes
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.role, "candidate")
        # Password should be hashed
        self.assertNotEqual(user.password_hash, "password123")
        
        # Invalid email
        with self.assertRaises(ValueError):
            User.create(
                email="invalid",
                password="password123",
                name="Test User",
                role="candidate"
            )
        
        # Invalid password
        with self.assertRaises(ValueError):
            User.create(
                email="test@example.com",
                password="short",
                name="Test User",
                role="candidate"
            )
        
        # Invalid role
        with self.assertRaises(ValueError):
            User.create(
                email="test@example.com",
                password="password123",
                name="Test User",
                role="invalid_role"
            )

    def test_verify_password(self):
        """Test password verification."""
        # Create a user with a known password
        user = User.create(
            email="test@example.com",
            password="password123",
            name="Test User",
            role="candidate"
        )
        
        # Correct password
        self.assertTrue(user.verify_password("password123"))
        
        # Incorrect password
        self.assertFalse(user.verify_password("wrong_password"))

if __name__ == '__main__':
    unittest.main() 