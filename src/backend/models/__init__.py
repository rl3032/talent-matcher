"""
Models Package

This package contains data models for the application.
"""

# Define exported names without importing directly
__all__ = [
    'User',
    'Job', 'JobSkill',
    'Candidate', 'CandidateSkill', 'Experience', 'Education',
    'Skill',
    'SkillGapAnalysis', 'SkillRecommendation', 'CareerPath', 'DashboardStats'
]

# Import models here to make them available when importing from the package,
# but after __all__ is defined to avoid circular dependencies issues
from src.backend.models.user_model import User
from src.backend.models.job_model import Job, JobSkill
from src.backend.models.candidate_model import Candidate, CandidateSkill, Experience, Education
from src.backend.models.skill_model import Skill
from src.backend.models.analytics_model import SkillGapAnalysis, SkillRecommendation, CareerPath, DashboardStats 