"""
Candidate Routes

This module defines API routes for candidate-related operations.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from src.backend.services.candidate_service import CandidateService

# Create blueprint
candidate_bp = Blueprint('candidates', __name__, url_prefix='/api/candidates')

# Service instances
candidate_service = None


def init_routes(app, candidate_svc):
    """Initialize routes with required services.
    
    Args:
        app: Flask application
        candidate_svc: CandidateService instance
    """
    global candidate_service
    candidate_service = candidate_svc
    
    # Register blueprint
    app.register_blueprint(candidate_bp)


@candidate_bp.route('', methods=['GET'])
@jwt_required()
def get_all_candidates():
    """Get all available candidates with filtering."""
    # Add detailed logging
    print(f"User accessing candidates API: {current_user.email} with role {current_user.role}")
    
    # Check permissions - Admin or any user with hiring_manager role
    if not current_user.is_admin and current_user.role != 'hiring_manager':
        print(f"Access denied: User {current_user.email} has insufficient permissions with role {current_user.role}")
        return jsonify({"error": "You don't have permission to view all candidates"}), 403
    
    # Get query parameters
    domain = request.args.get('domain')
    location = request.args.get('location')
    skill = request.args.get('skill')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Build filters
    filters = {}
    if domain:
        filters['domain'] = domain
    if location:
        filters['location'] = location
    if skill:
        filters['skill'] = skill
    
    print(f"Fetching candidates with filters: {filters}")
    
    # Get candidates
    result = candidate_service.find_candidates(filters, limit, offset)
    
    if not result['success']:
        print(f"Error finding candidates: {result['error']}")
        return jsonify({"error": result['error']}), 400
    
    print(f"Found {len(result.get('candidates', []))} candidates")
    return jsonify(result), 200


@candidate_bp.route('/<resume_id>', methods=['GET'])
@jwt_required()
def get_candidate(resume_id):
    """Get a specific candidate by ID."""
    result = candidate_service.get_candidate(resume_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 404
    
    # Return the full result with success flag
    return jsonify(result), 200


@candidate_bp.route('/create', methods=['POST'])
@jwt_required()
def create_candidate():
    """Create a new candidate profile."""
    # Get request data
    candidate_data = request.json
    
    # Create candidate
    result = candidate_service.create_candidate(candidate_data)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({
        "resume_id": result['resume_id'],
        "message": "Candidate created successfully"
    }), 201


@candidate_bp.route('/<resume_id>', methods=['PUT'])
@jwt_required()
def update_candidate(resume_id):
    """Update an existing candidate."""
    # Get request data
    candidate_data = request.json
    
    # Update candidate
    result = candidate_service.update_candidate(resume_id, candidate_data)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({
        "resume_id": result['resume_id'],
        "message": "Candidate updated successfully"
    }), 200


@candidate_bp.route('/<resume_id>/jobs', methods=['GET'])
@jwt_required()
def get_candidate_matches(resume_id):
    """Get jobs matching a candidate."""
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
    
    # Get matching jobs
    result = candidate_service.get_matching_jobs(resume_id, limit, weights)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify(result['jobs']), 200


@candidate_bp.route('/<resume_id>/jobs/enhanced', methods=['GET'])
@jwt_required()
def get_candidate_matches_enhanced(resume_id):
    """Get enhanced job matches for a candidate."""
    print(f"Enhanced job matching requested for candidate {resume_id} by user {current_user.email}")
    
    # Get parameters
    limit = request.args.get('limit', 10, type=int)
    
    # Get weights
    weights = {
        "skills": request.args.get('skills_weight', 0.75, type=float),
        "location": request.args.get('location_weight', 0.15, type=float),
        "semantic": request.args.get('semantic_weight', 0.1, type=float)
    }
    
    print(f"Using weights: {weights}")
    
    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight > 0:
        for key in weights:
            weights[key] = weights[key] / total_weight
    
    # Get matching jobs
    result = candidate_service.get_matching_jobs(resume_id, limit, weights)
    
    if not result['success']:
        print(f"Error finding jobs for candidate {resume_id}: {result.get('error')}")
        return jsonify({"error": result['error']}), 400
    
    print(f"Found {len(result.get('jobs', []))} matching jobs for candidate {resume_id}")
    return jsonify(result['jobs']), 200


@candidate_bp.route('/<resume_id>', methods=['DELETE'])
@jwt_required()
def delete_candidate(resume_id):
    """Delete a candidate profile."""
    # Only admins should be able to delete candidates
    if not current_user.is_admin:
        return jsonify({"error": "Only administrators can delete candidate profiles"}), 403
        
    # Delete candidate
    result = candidate_service.delete_candidate(resume_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({"message": result['message']}), 200


@candidate_bp.route('/resume/upload', methods=['POST'])
@jwt_required()
def upload_resume():
    """Upload and process a candidate resume."""
    # This endpoint would handle file upload and processing
    # For now we'll just create a candidate from JSON data
    
    # Get request data
    resume_data = request.json
    
    # Create candidate
    result = candidate_service.create_candidate(resume_data)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({
        "resume_id": result['resume_id'],
        "message": "Resume uploaded and processed successfully"
    }), 201 