"""
Unit tests for the skill model.
"""

import unittest
import datetime
import json
import os
import sys

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.models.skill_model import Skill


class TestSkillModel(unittest.TestCase):
    """Test case for the Skill model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data for testing
        self.skill_data = {
            "skill_id": "s1",
            "name": "Python",
            "category": "Programming",
            "description": "Python programming language",
            "level": 8,
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:00:00"
        }
    
    def test_skill_initialization(self):
        """Test skill model initialization."""
        # Test with minimum required fields
        skill = Skill(name="Python")
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.skill_id, "")
        self.assertEqual(skill.category, "")
        self.assertEqual(skill.description, "")
        self.assertEqual(skill.level, 0)
        self.assertIsNotNone(skill.created_at)
        self.assertIsNotNone(skill.updated_at)
        
        # Test with all fields
        skill = Skill(
            skill_id="s1",
            name="Python",
            category="Programming",
            description="Python programming language",
            level=8
        )
        self.assertEqual(skill.skill_id, "s1")
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.category, "Programming")
        self.assertEqual(skill.description, "Python programming language")
        self.assertEqual(skill.level, 8)
        self.assertIsNotNone(skill.created_at)
        self.assertIsNotNone(skill.updated_at)
    
    def test_skill_from_dict(self):
        """Test creating a skill from a dictionary."""
        skill = Skill.from_dict(self.skill_data)
        
        # Check main fields
        self.assertEqual(skill.skill_id, "s1")
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.category, "Programming")
        self.assertEqual(skill.description, "Python programming language")
        self.assertEqual(skill.level, 8)
        
        # Check timestamps
        self.assertEqual(skill.created_at, "2023-01-01T12:00:00")
        self.assertEqual(skill.updated_at, "2023-01-01T12:00:00")
        
        # Test with partial data
        partial_data = {"name": "JavaScript"}
        skill = Skill.from_dict(partial_data)
        self.assertEqual(skill.name, "JavaScript")
        self.assertEqual(skill.skill_id, "")
        self.assertEqual(skill.category, "")
        self.assertEqual(skill.level, 0)
    
    def test_skill_to_dict(self):
        """Test converting a skill to a dictionary."""
        # Create a skill from dict
        skill = Skill.from_dict(self.skill_data)
        
        # Convert back to dict
        result = skill.to_dict()
        
        # Check main fields
        self.assertEqual(result["skill_id"], "s1")
        self.assertEqual(result["name"], "Python")
        self.assertEqual(result["category"], "Programming")
        self.assertEqual(result["description"], "Python programming language")
        self.assertEqual(result["level"], 8)
        
        # Check that timestamps are included
        self.assertIn("created_at", result)
        self.assertIn("updated_at", result)
    
    def test_skill_validation_valid(self):
        """Test validation with valid data."""
        skill = Skill(name="Python", level=5)
        result = skill.validate()
        
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
    
    def test_skill_validation_invalid_name(self):
        """Test validation with missing name."""
        skill = Skill(name="", level=5)
        result = skill.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("name is required", result["errors"][0])
    
    def test_skill_validation_invalid_level(self):
        """Test validation with invalid level."""
        # Test with level below range
        skill = Skill(name="Python", level=-1)
        result = skill.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("level must be", result["errors"][0])
        
        # Test with level above range
        skill = Skill(name="Python", level=11)
        result = skill.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("level must be", result["errors"][0])
        
        # Test with non-numeric level
        skill = Skill(name="Python")
        skill.level = "high"
        result = skill.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("level must be", result["errors"][0])
    
    def test_skill_string_representation(self):
        """Test string representation of skill."""
        skill = Skill(name="Python", category="Programming")
        self.assertEqual(str(skill), "Python (Programming)")
        
        # Test with missing category
        skill = Skill(name="Python")
        self.assertEqual(str(skill), "Python ()")


if __name__ == '__main__':
    unittest.main() 