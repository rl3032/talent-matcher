"""
Skill Routes

This module defines API routes for skill-related operations.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from src.backend.services.skill_service import SkillService

# Create blueprints
skill_bp = Blueprint('skills', __name__, url_prefix='/api/skills')
graph_bp = Blueprint('graph', __name__, url_prefix='/api/graph')

# Service instances
skill_service = None


def init_routes(app, skill_svc):
    """Initialize routes with required services.
    
    Args:
        app: Flask application
        skill_svc: SkillService instance
    """
    global skill_service
    skill_service = skill_svc
    
    # Register blueprints
    app.register_blueprint(skill_bp)
    app.register_blueprint(graph_bp)


@skill_bp.route('', methods=['GET'])
def get_all_skills():
    """Get all skills with filtering."""
    # Get query parameters
    name = request.args.get('name')
    category = request.args.get('category')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Build filters
    filters = {}
    if name:
        filters['name'] = name
    if category:
        filters['category'] = category
    
    # Get skills
    result = skill_service.find_skills(filters, limit, offset)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify(result), 200


@skill_bp.route('/<skill_id>', methods=['GET'])
def get_skill(skill_id):
    """Get a specific skill by ID."""
    result = skill_service.get_skill(skill_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 404
    
    return jsonify(result), 200


@skill_bp.route('/<skill_id>/related', methods=['GET'])
def get_related_skills(skill_id):
    """Get skills related to a specific skill."""
    result = skill_service.get_related_skills(skill_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 404
    
    return jsonify(result), 200


@skill_bp.route('/path', methods=['GET'])
def get_skill_path():
    """Get the path between two skills."""
    # Get query parameters
    source_id = request.args.get('source')
    target_id = request.args.get('target')
    
    if not source_id or not target_id:
        return jsonify({"error": "Both source and target skill IDs are required"}), 400
    
    result = skill_service.get_skill_path(source_id, target_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 404
    
    return jsonify(result), 200


@skill_bp.route('/create', methods=['POST'])
@jwt_required()
def create_skill():
    """Create a new skill."""
    # Only admins can create skills
    if not current_user.is_admin:
        return jsonify({"error": "Only administrators can create skills"}), 403
    
    # Get request data
    skill_data = request.json
    
    # Create skill
    result = skill_service.create_skill(skill_data)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({
        "skill_id": result['skill_id'],
        "message": "Skill created successfully"
    }), 201


@skill_bp.route('/<skill_id>', methods=['PUT'])
@jwt_required()
def update_skill(skill_id):
    """Update an existing skill."""
    # Only admins can update skills
    if not current_user.is_admin:
        return jsonify({"error": "Only administrators can update skills"}), 403
    
    # Get request data
    skill_data = request.json
    
    # Update skill
    result = skill_service.update_skill(skill_id, skill_data)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({
        "skill_id": result['skill_id'],
        "message": "Skill updated successfully"
    }), 200


@skill_bp.route('/<skill_id>', methods=['DELETE'])
@jwt_required()
def delete_skill(skill_id):
    """Delete a skill."""
    # Only admins can delete skills
    if not current_user.is_admin:
        return jsonify({"error": "Only administrators can delete skills"}), 403
    
    # Delete skill
    result = skill_service.delete_skill(skill_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify({"message": result['message']}), 200


# Additional routes for graph visualizations
@skill_bp.route('/<skill_id>/graph', methods=['GET'])
def get_skill_graph(skill_id):
    """Get a graph visualization of a skill and its connections."""
    result = skill_service.get_skill_graph(skill_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 404
    
    return jsonify(result), 200


@skill_bp.route('/network', methods=['GET'])
def get_skills_network():
    """Get a network of skills for visualization."""
    limit = request.args.get('limit', 100, type=int)
    
    result = skill_service.get_skills_network(limit)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify(result), 200


@skill_bp.route('/recommendations/<resume_id>/<job_id>', methods=['GET'])
def get_skill_recommendations(resume_id, job_id):
    """Get skill recommendations for a candidate targeting a specific job."""
    result = skill_service.recommend_skills_for_job(resume_id, job_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
    
    return jsonify(result), 200


# Graph routes
@graph_bp.route('/skill/<skill_id>', methods=['GET'])
def get_skill_graph_data(skill_id):
    """Get graph data for a skill."""
    try:
        result = skill_service.get_skill_graph(skill_id)
        
        if not result['success']:
            print(f"Error getting skill graph: {result['error']}")
            return jsonify({"error": result['error']}), 404
        
        graph_data = result['graph']
        node_count = len(graph_data.get('nodes', []))
        edge_count = len(graph_data.get('edges', []))
        print(f"Skill graph data for {skill_id}: {node_count} nodes, {edge_count} edges")
        
        # Make sure we always return valid format even if empty
        if 'nodes' not in graph_data:
            graph_data['nodes'] = []
        if 'edges' not in graph_data:
            graph_data['edges'] = []
            
        return jsonify(graph_data), 200
    except Exception as e:
        print(f"Unexpected error in get_skill_graph_data: {str(e)}")
        return jsonify({"error": "Failed to retrieve skill graph data", "details": str(e)}), 500


@graph_bp.route('/skills-network', methods=['GET'])
def get_skills_network_data():
    """Get network of skills for visualization."""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        result = skill_service.get_skills_network(limit)
        
        if not result['success']:
            print(f"Error getting skills network: {result['error']}")
            return jsonify({"error": result['error']}), 404
        
        network_data = result['network']
        node_count = len(network_data.get('nodes', []))
        edge_count = len(network_data.get('edges', []))
        print(f"Skills network data: {node_count} nodes, {edge_count} edges")
        
        # Make sure we always return valid format even if empty
        if 'nodes' not in network_data:
            network_data['nodes'] = []
        if 'edges' not in network_data:
            network_data['edges'] = []
            
        return jsonify(network_data), 200
    except Exception as e:
        print(f"Unexpected error in get_skills_network_data: {str(e)}")
        return jsonify({"error": "Failed to retrieve skills network data", "details": str(e)}), 500 