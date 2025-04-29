"""
Skill Model

This module defines the data models for skills in the talent matcher system.
"""

import datetime


class Skill:
    """Model representing a skill in the system."""
    
    def __init__(self, skill_id="", name="", category="", description="", level=0):
        """Initialize a new Skill instance.
        
        Args:
            skill_id: Unique identifier for the skill
            name: Name of the skill
            category: Category of the skill (e.g., Programming, Design)
            description: Description of the skill
            level: Numeric level of the skill (0-10)
        """
        self.skill_id = skill_id
        self.name = name
        self.category = category
        self.description = description
        self.level = level
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = self.created_at
    
    @classmethod
    def from_dict(cls, data):
        """Create a Skill instance from a dictionary.
        
        Args:
            data: Dictionary containing skill data
            
        Returns:
            Skill: New Skill instance
        """
        skill = cls(
            skill_id=data.get("skill_id", ""),
            name=data.get("name", ""),
            category=data.get("category", ""),
            description=data.get("description", ""),
            level=data.get("level", 0)
        )
        
        # Add timestamps if present
        if "created_at" in data:
            skill.created_at = data["created_at"]
        if "updated_at" in data:
            skill.updated_at = data["updated_at"]
        
        return skill
    
    def to_dict(self):
        """Convert Skill instance to a dictionary.
        
        Returns:
            dict: Dictionary representation of the skill
        """
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "level": self.level,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def validate(self):
        """Validate the skill data.
        
        Returns:
            dict: Dictionary with 'valid' (bool) and 'errors' (list) keys
        """
        errors = []
        
        # Validate required fields
        if not self.name:
            errors.append("Skill name is required")
        
        # Validate level range
        if not isinstance(self.level, (int, float)) or self.level < 0 or self.level > 10:
            errors.append("Skill level must be a number between 0 and 10")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def __str__(self):
        """String representation of the skill.
        
        Returns:
            str: String representation
        """
        return f"{self.name} ({self.category})" 