"""
Backend package for Talent Matcher

This package contains the API and database access layers for the talent matching system.
"""

# Import core services and models for convenient access
from src.backend.services.graph_service import GraphService
from src.backend.services.matching_service import MatchingService
from src.backend.services.auth_service import AuthService
from src.backend.services.job_service import JobService
from src.backend.services.candidate_service import CandidateService
from src.backend.services.skill_service import SkillService
from src.backend.services.analytics_service import AnalyticsService

from src.backend.models.user_model import User
from src.backend.models.job_model import Job, JobPost
from src.backend.models.candidate_model import Candidate, Resume
from src.backend.models.skill_model import Skill, SkillCategory
from src.backend.models.analytics_model import SkillGraph, JobMarketInsight, CareerPathInsight

__version__ = '0.1.0'

__all__ = [
    # Services
    'GraphService',
    'MatchingService',
    'AuthService',
    'JobService',
    'CandidateService',
    'SkillService',
    'AnalyticsService',
    
    # Models
    'User',
    'Job', 'JobPost',
    'Candidate', 'Resume',
    'Skill', 'SkillCategory',
    'SkillGraph', 'JobMarketInsight', 'CareerPathInsight'
] 