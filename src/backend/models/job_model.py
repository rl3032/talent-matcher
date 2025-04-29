"""
Job Model

This module defines the Job model for the talent matcher system.
"""

import json
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class JobSkill:
    """Represents a skill required for a job."""
    skill_id: str
    name: str
    proficiency: str = "Intermediate"
    importance: float = 0.5
    category: str = ""
    level: int = 5
    is_primary: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'skill_id': self.skill_id,
            'name': self.name,
            'proficiency': self.proficiency,
            'importance': self.importance,
            'category': self.category,
            'level': self.level,
            'is_primary': self.is_primary
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobSkill':
        """Create JobSkill from dictionary."""
        return cls(
            skill_id=data['skill_id'],
            name=data.get('name', ''),
            proficiency=data.get('proficiency', 'Intermediate'),
            importance=data.get('importance', 0.5),
            category=data.get('category', ''),
            level=data.get('level', 5),
            is_primary=data.get('is_primary', True)
        )


@dataclass
class Job:
    """Represents a job posting."""
    title: str
    company: str
    location: str
    job_id: str = ""
    owner_email: str = ""
    domain: str = ""
    summary: str = ""
    description: str = ""
    job_type: str = "Full-time"
    employment_type: str = "Permanent"
    salary_range: str = "Competitive"
    industry: str = ""
    responsibilities: List[str] = field(default_factory=list)
    qualifications: List[str] = field(default_factory=list)
    primary_skills: List[JobSkill] = field(default_factory=list)
    secondary_skills: List[JobSkill] = field(default_factory=list)
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    
    def __post_init__(self):
        """Initialize after creation."""
        # Initialize timestamps if not provided
        if self.created_at is None:
            self.created_at = datetime.datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.datetime.now()
            
        # Set description from summary if empty
        if not self.description and self.summary:
            self.description = self.summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        job_dict = {
            'job_id': self.job_id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'owner_email': self.owner_email,
            'domain': self.domain,
            'summary': self.summary,
            'description': self.description,
            'job_type': self.job_type,
            'employment_type': self.employment_type,
            'salary_range': self.salary_range,
            'industry': self.industry,
            'responsibilities': json.dumps(self.responsibilities),
            'qualifications': json.dumps(self.qualifications),
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime.datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime.datetime) else self.updated_at
        }
        
        return job_dict
    
    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        job_dict = {
            'job_id': self.job_id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'owner_email': self.owner_email,
            'domain': self.domain,
            'summary': self.summary,
            'description': self.description,
            'job_type': self.job_type,
            'employment_type': self.employment_type,
            'salary_range': self.salary_range,
            'industry': self.industry,
            'responsibilities': self.responsibilities,
            'qualifications': self.qualifications,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime.datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime.datetime) else self.updated_at
        }
        
        # Add skills
        job_dict['skills'] = {
            'primary': [skill.to_dict() for skill in self.primary_skills],
            'secondary': [skill.to_dict() for skill in self.secondary_skills]
        }
        
        return job_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create Job from dictionary."""
        # Extract and process responsibilities
        responsibilities = data.get('responsibilities', [])
        if isinstance(responsibilities, str):
            try:
                responsibilities = json.loads(responsibilities)
            except json.JSONDecodeError:
                responsibilities = [responsibilities]
        
        # Extract and process qualifications
        qualifications = data.get('qualifications', [])
        if isinstance(qualifications, str):
            try:
                qualifications = json.loads(qualifications)
            except json.JSONDecodeError:
                qualifications = [qualifications]
        
        # Parse timestamps
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        
        if isinstance(created_at, str):
            try:
                created_at = datetime.datetime.fromisoformat(created_at)
            except (ValueError, TypeError):
                created_at = None
                
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.datetime.fromisoformat(updated_at)
            except (ValueError, TypeError):
                updated_at = None
        
        # Create job
        job = cls(
            job_id=data.get('job_id', ''),
            title=data['title'],
            company=data['company'],
            location=data['location'],
            owner_email=data.get('owner_email', ''),
            domain=data.get('domain', ''),
            summary=data.get('summary', ''),
            description=data.get('description', ''),
            job_type=data.get('job_type', 'Full-time'),
            employment_type=data.get('employment_type', 'Permanent'),
            salary_range=data.get('salary_range', 'Competitive'),
            industry=data.get('industry', ''),
            responsibilities=responsibilities,
            qualifications=qualifications,
            created_at=created_at,
            updated_at=updated_at
        )
        
        # Add skills if present
        if 'skills' in data:
            skills = data['skills']
            if 'primary' in skills:
                job.primary_skills = [JobSkill.from_dict(skill) for skill in skills['primary']]
            if 'secondary' in skills:
                job.secondary_skills = [JobSkill.from_dict(skill) for skill in skills['secondary']]
        
        return job
    
    def validate(self) -> Dict[str, Any]:
        """Validate job data.
        
        Returns:
            Dictionary with 'valid' (bool) and 'errors' (list) keys
        """
        errors = []
        
        # Check required fields
        if not self.title:
            errors.append("Job title is required")
        if not self.company:
            errors.append("Company name is required")
        if not self.location:
            errors.append("Location is required")
        
        # Validate skills
        for skill in self.primary_skills + self.secondary_skills:
            if not skill.skill_id:
                errors.append("All skills must have a skill_id")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        } 