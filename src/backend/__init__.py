"""
Backend package for Talent Matcher

This package contains the API and database access layers for the talent matching system.
"""

# Do not directly import services or models here to avoid circular imports
# Instead, declare what should be exposed without importing

__version__ = '0.1.0'

# Define what symbols should be exported
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
    'Job', 'JobSkill',
    'Candidate', 'CandidateSkill', 'Experience', 'Education',
    'Skill',
    'SkillGapAnalysis', 'SkillRecommendation', 'CareerPath', 'DashboardStats'
] 