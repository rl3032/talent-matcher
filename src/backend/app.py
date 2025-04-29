"""
Talent Matcher API

This module provides the main Flask application for the talent matching system.
"""

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import datetime

from src.backend.services.graph_service import GraphService
from src.backend.services.matching_service import MatchingService
from src.backend.services.auth_service import AuthService
from src.backend.routes import init_all_routes
from src.backend.config import JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES_HOURS, API_PORT, API_HOST


def create_app():
    """Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    
    # Configure JWT
    app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours=JWT_ACCESS_TOKEN_EXPIRES_HOURS)
    jwt = JWTManager(app)
    
    # Initialize services
    graph_service = GraphService.get_instance()
    matching_service = MatchingService.get_instance(graph_service)
    auth_service = AuthService.get_instance(graph_service)
    
    # Create database constraints and schema
    graph_service.create_constraints()
    graph_service.ensure_user_schema()
    
    # User loader callback for Flask-JWT-Extended
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return auth_service.find_user_by_email(identity)
    
    # Initialize all routes
    init_all_routes(app, auth_service, graph_service, matching_service)
    
    # Define a simple index route
    @app.route('/')
    def index():
        return {
            "name": "Talent Matcher API",
            "version": "0.1.0",
            "status": "running"
        }
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', API_PORT))
    app.run(host=API_HOST, port=port, debug=True) 