"""
Routes Package

This package contains all the API route definitions.
"""

from flask import Flask
from src.backend.services.auth_service import AuthService
from src.backend.services.graph_service import GraphService
from src.backend.services.matching_service import MatchingService
from src.backend.services.job_service import JobService
from src.backend.services.candidate_service import CandidateService
from src.backend.services.skill_service import SkillService
from src.backend.services.analytics_service import AnalyticsService


def init_all_routes(app: Flask, auth_service: AuthService, graph_service: GraphService, matching_service: MatchingService):
    """Initialize all API routes.
    
    Args:
        app: Flask application
        auth_service: AuthService instance
        graph_service: GraphService instance
        matching_service: MatchingService instance
    """
    # Import route modules
    from src.backend.routes.auth_routes import init_routes as init_auth_routes
    from src.backend.routes.job_routes import init_routes as init_job_routes
    from src.backend.routes.candidate_routes import init_routes as init_candidate_routes
    from src.backend.routes.skill_routes import init_routes as init_skill_routes
    from src.backend.routes.analytics_routes import init_routes as init_analytics_routes
    
    # Initialize services
    job_service = JobService.get_instance(graph_service)
    candidate_service = CandidateService.get_instance(graph_service)
    skill_service = SkillService.get_instance(graph_service)
    analytics_service = AnalyticsService.get_instance(graph_service)
    
    # Pass matching_service to job_service and candidate_service
    job_service.matching_service = matching_service
    candidate_service.matching_service = matching_service
    
    # Initialize routes
    init_auth_routes(app, auth_service)
    init_job_routes(app, job_service)
    init_candidate_routes(app, candidate_service)
    init_skill_routes(app, skill_service)
    init_analytics_routes(app, analytics_service)
    
    