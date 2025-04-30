"""
Models Package

This package contains data models for the application.
"""

from src.backend.models.user_model import User
from src.backend.models.job_model import Job, JobPost
from src.backend.models.candidate_model import Candidate, Resume
from src.backend.models.skill_model import Skill, SkillCategory
from src.backend.models.analytics_model import SkillGraph, JobMarketInsight, CareerPathInsight

__all__ = [
    'User',
    'Job', 'JobPost',
    'Candidate', 'Resume',
    'Skill', 'SkillCategory',
    'SkillGraph', 'JobMarketInsight', 'CareerPathInsight'
] 