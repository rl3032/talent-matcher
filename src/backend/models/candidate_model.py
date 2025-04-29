"""
Candidate Model

This module defines the Candidate model for the talent matcher system.
"""

import json
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class CandidateSkill:
    """Represents a skill possessed by a candidate."""
    skill_id: str
    name: str
    proficiency: str = "Intermediate"
    experience_years: float = 0.0
    category: str = ""
    level: int = 5
    is_core: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'skill_id': self.skill_id,
            'name': self.name,
            'proficiency': self.proficiency,
            'experience_years': self.experience_years,
            'category': self.category,
            'level': self.level,
            'is_core': self.is_core
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CandidateSkill':
        """Create CandidateSkill from dictionary."""
        return cls(
            skill_id=data['skill_id'],
            name=data.get('name', ''),
            proficiency=data.get('proficiency', 'Intermediate'),
            experience_years=data.get('experience_years', 0.0),
            category=data.get('category', ''),
            level=data.get('level', 5),
            is_core=data.get('is_core', True)
        )


@dataclass
class Experience:
    """Represents a work experience."""
    title: str
    company: str
    start_date: str
    end_date: str = "Present"
    description: List[str] = field(default_factory=list)
    location: str = ""
    experience_id: str = ""
    skills_used: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'experience_id': self.experience_id,
            'title': self.title,
            'company': self.company,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'description': self.description,
            'location': self.location,
            'skills_used': self.skills_used
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Experience':
        """Create Experience from dictionary."""
        # Extract and process description
        description = data.get('description', [])
        if isinstance(description, str):
            try:
                description = json.loads(description)
            except json.JSONDecodeError:
                description = [description]
        
        # Extract skills
        skills_used = data.get('skills', [])
        
        return cls(
            experience_id=data.get('experience_id', ''),
            title=data['title'],
            company=data['company'],
            start_date=data.get('start_date', ''),
            end_date=data.get('end_date', 'Present'),
            description=description,
            location=data.get('location', ''),
            skills_used=skills_used
        )


@dataclass
class Education:
    """Represents an education entry."""
    institution: str
    degree: str
    field: str
    start_date: str
    end_date: str
    education_id: str = ""
    gpa: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'education_id': self.education_id,
            'institution': self.institution,
            'degree': self.degree,
            'field': self.field,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'gpa': self.gpa
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Education':
        """Create Education from dictionary."""
        return cls(
            education_id=data.get('education_id', ''),
            institution=data['institution'],
            degree=data['degree'],
            field=data['field'],
            start_date=data.get('start_date', ''),
            end_date=data.get('end_date', ''),
            gpa=data.get('gpa')
        )


@dataclass
class Candidate:
    """Represents a candidate profile."""
    name: str
    resume_id: str = ""
    email: str = ""
    title: str = ""
    location: str = ""
    domain: str = ""
    summary: str = ""
    core_skills: List[CandidateSkill] = field(default_factory=list)
    secondary_skills: List[CandidateSkill] = field(default_factory=list)
    experiences: List[Experience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None
    
    def __post_init__(self):
        """Initialize after creation."""
        # Initialize timestamps if not provided
        if self.created_at is None:
            self.created_at = datetime.datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        candidate_dict = {
            'resume_id': self.resume_id,
            'name': self.name,
            'email': self.email,
            'title': self.title,
            'location': self.location,
            'domain': self.domain,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime.datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime.datetime) else self.updated_at
        }
        
        return candidate_dict
    
    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        candidate_dict = self.to_dict()
        
        # Add skills, experiences, and education
        candidate_dict['skills'] = {
            'core': [skill.to_dict() for skill in self.core_skills],
            'secondary': [skill.to_dict() for skill in self.secondary_skills]
        }
        
        candidate_dict['experience'] = [exp.to_dict() for exp in self.experiences]
        candidate_dict['education'] = [edu.to_dict() for edu in self.education]
        
        return candidate_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Candidate':
        """Create Candidate from dictionary."""
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
        
        # Create candidate
        candidate = cls(
            resume_id=data.get('resume_id', ''),
            name=data['name'],
            email=data.get('email', ''),
            title=data.get('title', ''),
            location=data.get('location', ''),
            domain=data.get('domain', ''),
            summary=data.get('summary', ''),
            created_at=created_at,
            updated_at=updated_at
        )
        
        # Add skills if present
        if 'skills' in data:
            skills = data['skills']
            if 'core' in skills:
                candidate.core_skills = [CandidateSkill.from_dict(skill) for skill in skills['core']]
            if 'secondary' in skills:
                candidate.secondary_skills = [CandidateSkill.from_dict(skill) for skill in skills['secondary']]
        
        # Add experiences if present
        if 'experience' in data and isinstance(data['experience'], list):
            candidate.experiences = [Experience.from_dict(exp) for exp in data['experience']]
            
        # Add education if present
        if 'education' in data and isinstance(data['education'], list):
            candidate.education = [Education.from_dict(edu) for edu in data['education']]
        
        return candidate
    
    def validate(self) -> Dict[str, Any]:
        """Validate candidate data.
        
        Returns:
            Dictionary with 'valid' (bool) and 'errors' (list) keys
        """
        errors = []
        
        # Check required fields
        if not self.name:
            errors.append("Candidate name is required")
        
        # Validate skills
        for skill in self.core_skills + self.secondary_skills:
            if not skill.skill_id:
                errors.append("All skills must have a skill_id")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        } 