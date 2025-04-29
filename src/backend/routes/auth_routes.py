"""
Authentication Routes

This module defines API routes for authentication and user management.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, create_access_token, current_user, get_jwt_identity

from src.backend.services.auth_service import AuthService

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Get service instances
auth_service = None


def init_routes(app, auth_svc):
    """Initialize routes with required services.
    
    Args:
        app: Flask application
        auth_svc: AuthService instance
    """
    global auth_service
    auth_service = auth_svc
    
    # Register blueprint
    app.register_blueprint(auth_bp)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.json
    
    # Validate required fields
    required_fields = ['email', 'password', 'name', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    email = data['email']
    password = data['password']
    name = data['name']
    role = data['role']
    
    # Register user
    result = auth_service.register_user(email, password, name, role)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 409
    
    # Create access token
    access_token = create_access_token(identity=email)
    
    return jsonify({
        "access_token": access_token,
        "user": result['user'].to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Log in an existing user."""
    data = request.json
    
    # Validate required fields
    required_fields = ['email', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    email = data['email']
    password = data['password']
    
    # Login user
    result = auth_service.login(email, password)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 401
    
    # Create access token
    access_token = create_access_token(identity=email)
    
    return jsonify({
        "access_token": access_token,
        "user": result['user'].to_dict()
    })


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get current user profile."""
    return jsonify({"user": current_user.to_dict()})


@auth_bp.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile."""
    data = request.json
    updates = {}
    
    # Collect valid fields to update
    if 'name' in data:
        updates['name'] = data['name']
    
    if 'profile_id' in data:
        updates['profile_id'] = data['profile_id']
    
    # Update user
    result = auth_service.update_user(current_user.email, updates)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({"user": result['user'].to_dict()})


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password."""
    data = request.json
    
    # Validate required fields
    required_fields = ['current_password', 'new_password']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    current_password = data['current_password']
    new_password = data['new_password']
    
    # Change password
    result = auth_service.change_password(current_user.email, current_password, new_password)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({"message": result['message']})


@auth_bp.route('/admin/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Get all users (admin only)."""
    # Check if user is admin
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized access"}), 403
    
    # This would need to be implemented in auth_service
    # For now, return placeholder
    return jsonify({"message": "Admin user list endpoint"})


@auth_bp.route('/admin/make-admin', methods=['POST'])
@jwt_required()
def promote_to_admin():
    """Promote a user to admin (admin only)."""
    # Check if user is admin
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized access"}), 403
    
    data = request.json
    
    # Validate required fields
    if 'email' not in data:
        return jsonify({"error": "Missing email field"}), 400
    
    email = data['email']
    
    # Promote user
    result = auth_service.make_admin(email)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({
        "message": f"User {email} promoted to admin",
        "user": result['user'].to_dict()
    })


@auth_bp.route('/admin/delete-user/<email>', methods=['DELETE'])
@jwt_required()
def delete_user(email):
    """Delete a user (admin only)."""
    # Check if user is admin
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized access"}), 403
    
    # Delete user
    result = auth_service.delete_user(email)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({"message": result['message']}) 