"""
Analytics Models

This module defines the data models for analytics in the talent matcher system.
"""

import datetime


class SkillGapAnalysis:
    """Model representing a skill gap analysis between a candidate and a job."""
    
    def __init__(self, job_id, resume_id):
        """Initialize a new SkillGapAnalysis instance.
        
        Args:
            job_id: ID of the job
            resume_id: ID of the candidate
        """
        self.job_id = job_id
        self.resume_id = resume_id
        self.job_title = ""
        self.candidate_name = ""
        self.gap_score = 0
        self.missing_skills = []
        self.proficiency_gaps = []
        self.total_required_skills = 0
        self.missing_skill_count = 0
        self.created_at = datetime.datetime.now().isoformat()
    
    @classmethod
    def from_dict(cls, data):
        """Create a SkillGapAnalysis from a dictionary.
        
        Args:
            data: Dictionary containing analysis data
            
        Returns:
            SkillGapAnalysis: New analysis instance
        """
        analysis = cls(data.get("job_id", ""), data.get("resume_id", ""))
        analysis.job_title = data.get("job_title", "")
        analysis.candidate_name = data.get("candidate_name", "")
        analysis.gap_score = data.get("gap_score", 0)
        analysis.missing_skills = data.get("missing_skills", [])
        analysis.proficiency_gaps = data.get("proficiency_gaps", [])
        analysis.total_required_skills = data.get("total_required_skills", 0)
        analysis.missing_skill_count = data.get("missing_skill_count", 0)
        
        if "created_at" in data:
            analysis.created_at = data["created_at"]
            
        return analysis
    
    def to_dict(self):
        """Convert to dictionary.
        
        Returns:
            dict: Dictionary representation of the analysis
        """
        return {
            "job_id": self.job_id,
            "resume_id": self.resume_id,
            "job_title": self.job_title,
            "candidate_name": self.candidate_name,
            "gap_score": self.gap_score,
            "missing_skills": self.missing_skills,
            "proficiency_gaps": self.proficiency_gaps,
            "total_required_skills": self.total_required_skills,
            "missing_skill_count": self.missing_skill_count,
            "created_at": self.created_at
        }
    
    def validate(self):
        """Validate the analysis data.
        
        Returns:
            dict: Dictionary with 'valid' (bool) and 'errors' (list) keys
        """
        errors = []
        
        # Validate required fields
        if not self.job_id:
            errors.append("Job ID is required")
        if not self.resume_id:
            errors.append("Resume ID is required")
        
        # Validate score range
        if not isinstance(self.gap_score, (int, float)) or self.gap_score < 0 or self.gap_score > 100:
            errors.append("Gap score must be a number between 0 and 100")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


class SkillRecommendation:
    """Model representing skill recommendations for a candidate targeting a job."""
    
    def __init__(self, job_id, resume_id):
        """Initialize a new SkillRecommendation instance.
        
        Args:
            job_id: ID of the job
            resume_id: ID of the candidate
        """
        self.job_id = job_id
        self.resume_id = resume_id
        self.skills = []
        self.gap_score = 0
        self.created_at = datetime.datetime.now().isoformat()
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary.
        
        Args:
            data: Dictionary containing recommendation data
            
        Returns:
            SkillRecommendation: New recommendation instance
        """
        recommendation = cls(data.get("job_id", ""), data.get("resume_id", ""))
        recommendation.skills = data.get("skills", [])
        recommendation.gap_score = data.get("gap_score", 0)
        
        if "created_at" in data:
            recommendation.created_at = data["created_at"]
            
        return recommendation
    
    def to_dict(self):
        """Convert to dictionary.
        
        Returns:
            dict: Dictionary representation of the recommendation
        """
        return {
            "job_id": self.job_id,
            "resume_id": self.resume_id,
            "skills": self.skills,
            "gap_score": self.gap_score,
            "created_at": self.created_at
        }
    
    def validate(self):
        """Validate the recommendation data.
        
        Returns:
            dict: Dictionary with 'valid' (bool) and 'errors' (list) keys
        """
        errors = []
        
        # Validate required fields
        if not self.job_id:
            errors.append("Job ID is required")
        if not self.resume_id:
            errors.append("Resume ID is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


class CareerPath:
    """Model representing a career path from one job title to another."""
    
    def __init__(self, source_title, target_title=None):
        """Initialize a new CareerPath instance.
        
        Args:
            source_title: Starting job title
            target_title: Target job title (optional)
        """
        self.source_title = source_title
        self.target_title = target_title
        self.titles = [source_title]
        self.salaries = []
        self.transitions = []
        self.path_length = 0
        self.created_at = datetime.datetime.now().isoformat()
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary.
        
        Args:
            data: Dictionary containing path data
            
        Returns:
            CareerPath: New path instance
        """
        path = cls(data.get("source_title", ""), data.get("target_title"))
        path.titles = data.get("titles", [path.source_title])
        path.salaries = data.get("salaries", [])
        path.transitions = data.get("transitions", [])
        path.path_length = data.get("length", 0)
        
        if "created_at" in data:
            path.created_at = data["created_at"]
            
        return path
    
    def to_dict(self):
        """Convert to dictionary.
        
        Returns:
            dict: Dictionary representation of the path
        """
        return {
            "source_title": self.source_title,
            "target_title": self.target_title,
            "titles": self.titles,
            "salaries": self.salaries,
            "transitions": self.transitions,
            "length": self.path_length,
            "created_at": self.created_at
        }
    
    def validate(self):
        """Validate the path data.
        
        Returns:
            dict: Dictionary with 'valid' (bool) and 'errors' (list) keys
        """
        errors = []
        
        # Validate required fields
        if not self.source_title:
            errors.append("Source title is required")
        
        # Validate consistency of arrays
        if len(self.titles) < 1:
            errors.append("Path must contain at least one title")
        
        if self.path_length > 0 and len(self.transitions) != self.path_length:
            errors.append("Number of transitions must match path length")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


class DashboardStats:
    """Model representing dashboard statistics."""
    
    def __init__(self, start_date=None, end_date=None):
        """Initialize a new DashboardStats instance.
        
        Args:
            start_date: Start date for statistics period
            end_date: End date for statistics period
        """
        self.start_date = start_date or (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
        self.end_date = end_date or datetime.datetime.now().isoformat()
        self.job_count = 0
        self.candidate_count = 0
        self.company_count = 0
        self.top_skills = []
        self.recent_matches = []
        self.created_at = datetime.datetime.now().isoformat()
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary.
        
        Args:
            data: Dictionary containing stats data
            
        Returns:
            DashboardStats: New stats instance
        """
        date_range = data.get("date_range", {})
        stats = cls(date_range.get("start"), date_range.get("end"))
        
        stats.job_count = data.get("job_count", 0)
        stats.candidate_count = data.get("candidate_count", 0)
        stats.company_count = data.get("company_count", 0)
        stats.top_skills = data.get("top_skills", [])
        stats.recent_matches = data.get("recent_matches", [])
        
        if "created_at" in data:
            stats.created_at = data["created_at"]
            
        return stats
    
    def to_dict(self):
        """Convert to dictionary.
        
        Returns:
            dict: Dictionary representation of the stats
        """
        return {
            "job_count": self.job_count,
            "candidate_count": self.candidate_count,
            "company_count": self.company_count,
            "top_skills": self.top_skills,
            "recent_matches": self.recent_matches,
            "date_range": {
                "start": self.start_date,
                "end": self.end_date
            },
            "created_at": self.created_at
        } 