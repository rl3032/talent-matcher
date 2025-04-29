"""
Analytics Routes

This module defines API routes for analytics and reporting operations.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from src.backend.services.analytics_service import AnalyticsService

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

# Service instances
analytics_service = None


def init_routes(app, analytics_svc):
    """Initialize routes with required services.
    
    Args:
        app: Flask application
        analytics_svc: AnalyticsService instance
    """
    global analytics_service
    analytics_service = analytics_svc
    
    # Register blueprint
    app.register_blueprint(analytics_bp)


@analytics_bp.route('/skill-gap/<resume_id>/<job_id>', methods=['GET'])
@jwt_required()
def get_skill_gap_analysis(resume_id, job_id):
    """Get skill gap analysis for a candidate and job."""
    # Get analysis
    result = analytics_service.get_skill_gap_analysis(resume_id, job_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 404
    
    return jsonify(result['analysis']), 200


@analytics_bp.route('/recommendations/<resume_id>/<job_id>', methods=['GET'])
@jwt_required()
def get_skill_recommendations(resume_id, job_id):
    """Get skill recommendations for a candidate targeting a specific job."""
    # Get recommendations
    result = analytics_service.get_skill_recommendations(resume_id, job_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 404
    
    return jsonify(result['recommendations']), 200


@analytics_bp.route('/career-path', methods=['GET'])
def get_career_path():
    """Get career path from current to target job title."""
    # Get query parameters
    current_title = request.args.get('current')
    target_title = request.args.get('target')
    
    if not current_title:
        return jsonify({"error": "Current job title is required"}), 400
    
    # Get career path
    result = analytics_service.get_career_path(current_title, target_title)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 404
    
    return jsonify(result['paths']), 200


@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get statistics for dashboard."""
    # Only admin users should access this
    if not current_user.is_admin and not hasattr(current_user, 'role') and current_user.role != 'hiring_manager':
        return jsonify({"error": "You don't have permission to access dashboard statistics"}), 403
    
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Get statistics
    result = analytics_service.get_dashboard_stats(start_date, end_date)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify(result['stats']), 200


@analytics_bp.route('/job-match-distribution', methods=['GET'])
@jwt_required()
def get_job_match_distribution():
    """Get distribution of match scores for a job."""
    # Only admins, talent managers, and job owners can access this
    if not current_user.is_admin and current_user.role != 'hiring_manager':
        return jsonify({"error": "You don't have permission to access this data"}), 403
    
    # Get query parameters
    job_id = request.args.get('job_id')
    
    if not job_id:
        return jsonify({"error": "Job ID is required"}), 400
    
    # This would need to be implemented in the analytics service
    # For now, return dummy data
    return jsonify({
        "job_id": job_id,
        "job_title": "Software Engineer",
        "match_distribution": [
            {"range": "90-100", "count": 5},
            {"range": "80-89", "count": 12},
            {"range": "70-79", "count": 18},
            {"range": "60-69", "count": 25},
            {"range": "50-59", "count": 30},
            {"range": "40-49", "count": 15},
            {"range": "30-39", "count": 8},
            {"range": "20-29", "count": 4},
            {"range": "10-19", "count": 2},
            {"range": "0-9", "count": 1}
        ]
    }), 200


@analytics_bp.route('/candidate-match-distribution', methods=['GET'])
@jwt_required()
def get_candidate_match_distribution():
    """Get distribution of match scores for a candidate."""
    # Get query parameters
    resume_id = request.args.get('resume_id')
    
    if not resume_id:
        return jsonify({"error": "Resume ID is required"}), 400
    
    # Check if user has permission to access this candidate
    # (Admin, talent manager, or candidate owner)
    if not current_user.is_admin and current_user.role != 'hiring_manager' and (not hasattr(current_user, 'profile_id') or current_user.profile_id != resume_id):
        return jsonify({"error": "You don't have permission to access this data"}), 403
    
    # This would need to be implemented in the analytics service
    # For now, return dummy data
    return jsonify({
        "resume_id": resume_id,
        "candidate_name": "John Doe",
        "match_distribution": [
            {"range": "90-100", "count": 3},
            {"range": "80-89", "count": 7},
            {"range": "70-79", "count": 15},
            {"range": "60-69", "count": 23},
            {"range": "50-59", "count": 28},
            {"range": "40-49", "count": 18},
            {"range": "30-39", "count": 12},
            {"range": "20-29", "count": 5},
            {"range": "10-19", "count": 2},
            {"range": "0-9", "count": 0}
        ]
    }), 200 