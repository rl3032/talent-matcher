"""
Job Routes

This module defines API routes for job-related operations.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from src.backend.services.job_service import JobService
from src.backend.models.job_model import Job

# Create blueprint
job_bp = Blueprint('jobs', __name__, url_prefix='/api/jobs')

# Service instances
job_service = None


def init_routes(app, job_svc):
    """Initialize routes with required services.
    
    Args:
        app: Flask application
        job_svc: JobService instance
    """
    global job_service
    job_service = job_svc
    
    # Register blueprint
    app.register_blueprint(job_bp)


@job_bp.route('', methods=['GET'])
def get_all_jobs():
    """Get all available jobs with filtering."""
    company = request.args.get('company')
    domain = request.args.get('domain')
    location = request.args.get('location')
    owner_email = request.args.get('owner_email')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Build filters
    filters = {}
    if company:
        filters['company'] = company
    if domain:
        filters['domain'] = domain
    if location:
        filters['location'] = location
    if owner_email:
        filters['owner_email'] = owner_email
    
    # Get jobs
    result = job_service.find_jobs(filters, limit, offset)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify(result), 200


@job_bp.route('/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get a specific job by ID."""
    result = job_service.get_job(job_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 404
    
    return jsonify(result), 200


@job_bp.route('/create', methods=['POST'])
@jwt_required()
def create_job():
    """Create a new job posting."""
    # Check if user is a hiring manager
    if not current_user.is_hiring_manager and not current_user.is_admin:
        return jsonify({"error": "Only hiring managers can post jobs"}), 403
    
    # Get request data
    job_data = request.json
    
    # Ensure skills are properly formatted for the backend
    if 'skills' not in job_data and ('primary_skills' in job_data or 'secondary_skills' in job_data):
        job_data['skills'] = {
            'primary': job_data.get('primary_skills', []),
            'secondary': job_data.get('secondary_skills', [])
        }
        # Remove old keys to avoid confusion
        if 'primary_skills' in job_data:
            del job_data['primary_skills']
        if 'secondary_skills' in job_data:
            del job_data['secondary_skills']
    
    # Create job
    result = job_service.create_job(job_data, current_user.email)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({
        "job_id": result['job_id'],
        "message": "Job created successfully"
    }), 201


@job_bp.route('/<job_id>', methods=['PUT'])
@jwt_required()
def update_job(job_id):
    """Update an existing job."""
    # Get request data
    job_data = request.json
    
    # Update job
    result = job_service.update_job(job_id, job_data, current_user.email)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({
        "job_id": result['job_id'],
        "message": "Job updated successfully"
    }), 200


@job_bp.route('/<job_id>', methods=['DELETE'])
@jwt_required()
def delete_job(job_id):
    """Delete a job posting."""
    # Only admins and the job owner can delete
    result = job_service.delete_job(job_id, current_user.email)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({"message": result['message']}), 200


@job_bp.route('/<job_id>/candidates', methods=['GET'])
@jwt_required()
def get_job_candidates(job_id):
    """Get candidates matching a job."""
    # Check if user has access to this job
    # Admin can access any job, hiring manager can only access their own jobs
    if not current_user.is_admin and current_user.role == 'hiring_manager':
        job_info = job_service.get_job(job_id)
        # Check ownership based on owner_email
        has_permission = job_info['success'] and job_info['job'].get('owner_email') == current_user.email
        
        # If email check fails, check for CREATED relationship
        if not has_permission:
            has_relationship = job_service.job_repository.check_job_owner_relationship(job_id, current_user.email)
            has_permission = has_relationship
            
        if not has_permission:
            return jsonify({"error": "You don't have permission to view candidates for this job"}), 403
    
    # Get parameters
    limit = request.args.get('limit', 10, type=int)
    
    # Get weights
    weights = {
        "skills": request.args.get('skills_weight', 0.75, type=float),
        "location": request.args.get('location_weight', 0.15, type=float),
        "semantic": request.args.get('semantic_weight', 0.1, type=float)
    }
    
    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight > 0:
        for key in weights:
            weights[key] = weights[key] / total_weight
    
    # Get matching candidates
    result = job_service.get_matching_candidates(job_id, limit, weights)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify(result['candidates']), 200


@job_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_jobs():
    """Get jobs created by the current user."""
    # Get jobs for the current user
    filters = {'owner_email': current_user.email}
    result = job_service.find_jobs(filters)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify(result), 200


@job_bp.route('/<job_id>/candidates/enhanced', methods=['GET'])
@jwt_required()
def get_job_candidates_enhanced(job_id):
    """Get candidates matching a job using enhanced algorithm."""
    # Check if user has access to this job
    # Admin can access any job, hiring manager can only access their own jobs
    if not current_user.is_admin and current_user.role == 'hiring_manager':
        job_info = job_service.get_job(job_id)
        # Check ownership based on owner_email
        has_permission = job_info['success'] and job_info['job'].get('owner_email') == current_user.email
        
        # If email check fails, check for CREATED relationship
        if not has_permission:
            has_relationship = job_service.job_repository.check_job_owner_relationship(job_id, current_user.email)
            has_permission = has_relationship
            
        if not has_permission:
            return jsonify({"error": "You don't have permission to view candidates for this job"}), 403
    
    # Get parameters
    limit = request.args.get('limit', 10, type=int)
    
    # Get weights
    weights = {
        "skills": request.args.get('skills_weight', 0.75, type=float),
        "location": request.args.get('location_weight', 0.15, type=float),
        "semantic": request.args.get('semantic_weight', 0.1, type=float)
    }
    
    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight > 0:
        for key in weights:
            weights[key] = weights[key] / total_weight
    
    # Get matching candidates with enhanced algorithm
    result = job_service.get_matching_candidates(job_id, limit, weights)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify(result['candidates']), 200 