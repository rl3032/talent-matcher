"""
User Model

This module defines the User model for authentication.
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re

class User:
    """User model for authentication."""
    
    VALID_ROLES = ['hiring_manager', 'candidate', 'admin']
    
    def __init__(self, email, password_hash, name, role, profile_id=None, created_at=None):
        """Initialize a user.
        
        Args:
            email: User's email
            password_hash: Hashed password
            name: User's name
            role: User's role ('hiring_manager', 'candidate', or 'admin')
            profile_id: ID of associated profile (job_id or resume_id)
            created_at: Timestamp when user was created
        """
        self.email = email
        self.password_hash = password_hash
        self.name = name
        self.role = role
        self.profile_id = profile_id
        self.created_at = created_at or datetime.now()
        
    def to_dict(self):
        """Convert user to dictionary.
        
        Returns:
            dict: Dictionary representation of user
        """
        return {
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'profile_id': self.profile_id,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
        
    @property
    def is_admin(self):
        """Check if user is an admin.
        
        Returns:
            bool: True if user is an admin, False otherwise
        """
        return self.role == 'admin'
        
    @property
    def is_hiring_manager(self):
        """Check if user is a hiring manager.
        
        Returns:
            bool: True if user is a hiring manager, False otherwise
        """
        return self.role == 'hiring_manager'
        
    @property
    def is_candidate(self):
        """Check if user is a candidate.
        
        Returns:
            bool: True if user is a candidate, False otherwise
        """
        return self.role == 'candidate'
        
    @staticmethod
    def validate_email(email):
        """Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            bool: True if email is valid, False otherwise
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_regex, email))
        
    @staticmethod
    def validate_password(password):
        """Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            bool: True if password is valid, False otherwise
        """
        # Minimum 8 characters
        if len(password) < 8:
            return False
            
        return True
        
    @classmethod
    def create(cls, email, password, name, role, profile_id=None):
        """Create a new user with password hashing.
        
        Args:
            email: User's email
            password: Plain text password
            name: User's name
            role: User's role
            profile_id: ID of associated profile
            
        Returns:
            User: New user instance
        """
        # Validate inputs
        if not cls.validate_email(email):
            raise ValueError("Invalid email format")
            
        if not cls.validate_password(password):
            raise ValueError("Password must be at least 8 characters")
            
        if role not in cls.VALID_ROLES:
            raise ValueError(f"Role must be one of {cls.VALID_ROLES}")
            
        # Hash password
        password_hash = generate_password_hash(password)
        
        return cls(email, password_hash, name, role, profile_id)
        
    def verify_password(self, password):
        """Verify password against stored hash.
        
        Args:
            password: Plain text password
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password) 