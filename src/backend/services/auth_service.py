"""
Authentication Service

This module provides authentication and user management functionality.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from src.backend.models.user_model import User
from src.backend.services.graph_service import GraphService

class AuthService:
    """Service for authentication and user management."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls, graph_service=None):
        """Get singleton instance of AuthService."""
        if cls._instance is None:
            if graph_service is None:
                graph_service = GraphService.get_instance()
            cls._instance = cls(graph_service)
        return cls._instance
    
    def __init__(self, graph_service):
        """Initialize the auth service with graph service."""
        self.graph_service = graph_service
        self.driver = graph_service.driver
    
    def register_user(self, email, password, name, role, profile_id=None):
        """Register a new user.
        
        Args:
            email: User's email
            password: User's password
            name: User's name
            role: User's role ('hiring_manager' or 'candidate')
            profile_id: ID of the user's profile (job_id or resume_id)
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'user' or 'error' keys
        """
        try:
            # Check if user already exists
            existing_user = self.find_user_by_email(email)
            if existing_user:
                return {'success': False, 'error': 'User already exists'}
            
            # Validate and create user
            user = User.create(email, password, name, role, profile_id)
            
            # Create user in database
            with self.driver.session() as session:
                session.run("""
                    CREATE (u:User {
                        email: $email,
                        password_hash: $password_hash,
                        name: $name,
                        role: $role,
                        profile_id: $profile_id,
                        created_at: datetime()
                    })
                """, {
                    "email": user.email,
                    "password_hash": user.password_hash,
                    "name": user.name,
                    "role": user.role,
                    "profile_id": user.profile_id
                })
                
            return {'success': True, 'user': user}
        except ValueError as e:
            # Validation errors
            return {'success': False, 'error': str(e)}
        except Exception as e:
            # Other errors (database, etc.)
            return {'success': False, 'error': f'Registration failed: {str(e)}'}
    
    def login(self, email, password):
        """Login a user.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'user' or 'error' keys
        """
        try:
            # Validate email format
            if not User.validate_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            
            # Find user
            user = self.find_user_by_email(email)
            if not user:
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Verify password
            if not user.verify_password(password):
                return {'success': False, 'error': 'Invalid credentials'}
                
            return {'success': True, 'user': user}
        except Exception as e:
            return {'success': False, 'error': f'Login failed: {str(e)}'}
    
    def find_user_by_email(self, email):
        """Find a user by email.
        
        Args:
            email: User's email
            
        Returns:
            User: User object if found, None otherwise
        """
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User {email: $email})
                    RETURN u.email as email, 
                           u.password_hash as password_hash, 
                           u.name as name, 
                           u.role as role, 
                           u.profile_id as profile_id,
                           u.created_at as created_at
                """, {"email": email})
                
                record = result.single()
                if record:
                    # Convert Neo4j DateTime to string if present
                    created_at = record.get("created_at")
                    if created_at:
                        created_at = self.graph_service.process_neo4j_datetime(created_at)
                        
                    return User(
                        email=record["email"],
                        password_hash=record["password_hash"],
                        name=record["name"],
                        role=record["role"],
                        profile_id=record["profile_id"],
                        created_at=created_at
                    )
                return None
        except Exception as e:
            print(f"Error finding user: {str(e)}")
            return None
    
    def update_user(self, email, updates):
        """Update user information.
        
        Args:
            email: User's email
            updates: Dictionary of fields to update
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'user' or 'error' keys
        """
        try:
            if not updates:
                return {'success': False, 'error': 'No updates provided'}
            
            # Find user
            user = self.find_user_by_email(email)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Build update query
            update_fields = []
            params = {"email": email}
            
            # Validate update fields
            for key, value in updates.items():
                if key in ['name', 'role', 'profile_id']:
                    # Validate role if updating
                    if key == 'role' and value not in User.VALID_ROLES:
                        return {'success': False, 'error': f'Invalid role. Must be one of {User.VALID_ROLES}'}
                    
                    update_fields.append(f"u.{key} = ${key}")
                    params[key] = value
            
            if not update_fields:
                return {'success': False, 'error': 'No valid fields to update'}
                
            with self.driver.session() as session:
                session.run(f"""
                    MATCH (u:User {{email: $email}})
                    SET {', '.join(update_fields)}
                """, params)
                
            # Get updated user
            updated_user = self.find_user_by_email(email)
            return {'success': True, 'user': updated_user}
        except Exception as e:
            return {'success': False, 'error': f'Update failed: {str(e)}'}
    
    def delete_user(self, email):
        """Delete a user.
        
        Args:
            email: User's email
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'message' or 'error' keys
        """
        try:
            # Check if user exists
            user = self.find_user_by_email(email)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User {email: $email})
                    DELETE u
                """, {"email": email})
                
                if result.consume().counters.nodes_deleted > 0:
                    return {'success': True, 'message': 'User deleted successfully'}
                else:
                    return {'success': False, 'error': 'Failed to delete user'}
        except Exception as e:
            return {'success': False, 'error': f'Deletion failed: {str(e)}'}
    
    def make_admin(self, email):
        """Promote a user to admin.
        
        Args:
            email: User's email
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'user' or 'error' keys
        """
        try:
            # Check if user exists
            user = self.find_user_by_email(email)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            with self.driver.session() as session:
                session.run("""
                    MATCH (u:User {email: $email})
                    SET u.role = 'admin'
                """, {"email": email})
            
            # Get updated user
            updated_user = self.find_user_by_email(email)
            return {'success': True, 'user': updated_user}
        except Exception as e:
            return {'success': False, 'error': f'Promotion failed: {str(e)}'}
            
    def change_password(self, email, current_password, new_password):
        """Change a user's password.
        
        Args:
            email: User's email
            current_password: Current password
            new_password: New password
            
        Returns:
            dict: Dictionary with 'success' (bool) and 'message' or 'error' keys
        """
        try:
            # Validate new password
            if not User.validate_password(new_password):
                return {'success': False, 'error': 'Password must be at least 8 characters'}
            
            # Find user and verify current password
            user = self.find_user_by_email(email)
            if not user:
                return {'success': False, 'error': 'User not found'}
                
            if not user.verify_password(current_password):
                return {'success': False, 'error': 'Current password is incorrect'}
            
            # Generate new password hash
            new_password_hash = generate_password_hash(new_password)
            
            # Update password in database
            with self.driver.session() as session:
                session.run("""
                    MATCH (u:User {email: $email})
                    SET u.password_hash = $password_hash
                """, {
                    "email": email,
                    "password_hash": new_password_hash
                })
                
            return {'success': True, 'message': 'Password changed successfully'}
        except Exception as e:
            return {'success': False, 'error': f'Password change failed: {str(e)}'} 