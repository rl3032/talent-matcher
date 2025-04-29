"""
Unit tests for the candidate model.
"""

import unittest
import datetime
import json
import os
import sys

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.models.candidate_model import Candidate, CandidateSkill, Experience, Education


class TestCandidateModel(unittest.TestCase):
    """Test case for the Candidate model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data for testing
        self.candidate_data = {
            "resume_id": "resume_123",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "title": "Software Engineer",
            "location": "San Francisco, CA",
            "domain": "Software Development",
            "summary": "Experienced software engineer with 5+ years of experience",
            "skills": {
                "core": [
                    {"skill_id": "s1", "name": "Python", "proficiency": "Expert", "experience_years": 5}
                ],
                "secondary": [
                    {"skill_id": "s2", "name": "JavaScript", "proficiency": "Intermediate", "experience_years": 3}
                ]
            },
            "experience": [
                {
                    "experience_id": "exp_1",
                    "title": "Senior Developer",
                    "company": "Tech Co",
                    "start_date": "2020-01-01",
                    "end_date": "Present",
                    "description": ["Led a team of 5 developers", "Implemented new features"]
                }
            ],
            "education": [
                {
                    "education_id": "edu_1",
                    "institution": "University of California",
                    "degree": "Bachelor of Science",
                    "field": "Computer Science",
                    "start_date": "2010-09-01",
                    "end_date": "2014-06-01"
                }
            ]
        }
        
        # Sample skill data
        self.skill_data = {
            "skill_id": "s1",
            "name": "Python",
            "proficiency": "Expert",
            "experience_years": 5,
            "category": "Programming",
            "level": 9,
            "is_core": True
        }
        
        # Sample experience data
        self.experience_data = {
            "experience_id": "exp_1",
            "title": "Senior Developer",
            "company": "Tech Co",
            "start_date": "2020-01-01",
            "end_date": "Present",
            "description": ["Led a team of 5 developers", "Implemented new features"],
            "location": "San Francisco, CA",
            "skills": [{"skill_id": "s1", "name": "Python"}]
        }
        
        # Sample education data
        self.education_data = {
            "education_id": "edu_1",
            "institution": "University of California",
            "degree": "Bachelor of Science",
            "field": "Computer Science",
            "start_date": "2010-09-01",
            "end_date": "2014-06-01",
            "gpa": 3.8
        }
    
    def test_candidate_initialization(self):
        """Test candidate model initialization."""
        # Test with minimum required fields
        candidate = Candidate(name="John Doe")
        self.assertEqual(candidate.name, "John Doe")
        self.assertEqual(candidate.resume_id, "")
        self.assertEqual(candidate.email, "")
        self.assertEqual(len(candidate.core_skills), 0)
        self.assertEqual(len(candidate.secondary_skills), 0)
        self.assertEqual(len(candidate.experiences), 0)
        self.assertEqual(len(candidate.education), 0)
        self.assertIsNotNone(candidate.created_at)
        self.assertIsNotNone(candidate.updated_at)
        
        # Test with all fields
        candidate = Candidate(
            resume_id="resume_123",
            name="John Doe",
            email="john.doe@example.com",
            title="Software Engineer",
            location="San Francisco, CA",
            domain="Software Development",
            summary="Experienced software engineer"
        )
        self.assertEqual(candidate.resume_id, "resume_123")
        self.assertEqual(candidate.name, "John Doe")
        self.assertEqual(candidate.email, "john.doe@example.com")
        self.assertEqual(candidate.title, "Software Engineer")
        self.assertEqual(candidate.location, "San Francisco, CA")
        self.assertEqual(candidate.domain, "Software Development")
        self.assertEqual(candidate.summary, "Experienced software engineer")
    
    def test_candidate_skill_initialization(self):
        """Test candidate skill model initialization."""
        # Test with minimum required fields
        skill = CandidateSkill(skill_id="s1", name="Python")
        self.assertEqual(skill.skill_id, "s1")
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.proficiency, "Intermediate")  # Default value
        self.assertEqual(skill.experience_years, 0.0)  # Default value
        
        # Test with all fields
        skill = CandidateSkill(
            skill_id="s1",
            name="Python",
            proficiency="Expert",
            experience_years=5.0,
            category="Programming",
            level=9,
            is_core=True
        )
        self.assertEqual(skill.skill_id, "s1")
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.proficiency, "Expert")
        self.assertEqual(skill.experience_years, 5.0)
        self.assertEqual(skill.category, "Programming")
        self.assertEqual(skill.level, 9)
        self.assertTrue(skill.is_core)
    
    def test_experience_initialization(self):
        """Test experience model initialization."""
        # Test with minimum required fields
        experience = Experience(title="Developer", company="Tech Co", start_date="2020-01-01")
        self.assertEqual(experience.title, "Developer")
        self.assertEqual(experience.company, "Tech Co")
        self.assertEqual(experience.start_date, "2020-01-01")
        self.assertEqual(experience.end_date, "Present")  # Default value
        self.assertEqual(len(experience.description), 0)  # Default value
        
        # Test with all fields
        experience = Experience(
            experience_id="exp_1",
            title="Senior Developer",
            company="Tech Co",
            start_date="2020-01-01",
            end_date="2022-12-31",
            description=["Led a team", "Implemented features"],
            location="San Francisco, CA",
            skills_used=[{"skill_id": "s1", "name": "Python"}]
        )
        self.assertEqual(experience.experience_id, "exp_1")
        self.assertEqual(experience.title, "Senior Developer")
        self.assertEqual(experience.company, "Tech Co")
        self.assertEqual(experience.start_date, "2020-01-01")
        self.assertEqual(experience.end_date, "2022-12-31")
        self.assertEqual(len(experience.description), 2)
        self.assertEqual(experience.location, "San Francisco, CA")
        self.assertEqual(len(experience.skills_used), 1)
    
    def test_education_initialization(self):
        """Test education model initialization."""
        # Test with required fields
        education = Education(
            institution="University",
            degree="BS",
            field="Computer Science",
            start_date="2010-09-01",
            end_date="2014-06-01"
        )
        self.assertEqual(education.institution, "University")
        self.assertEqual(education.degree, "BS")
        self.assertEqual(education.field, "Computer Science")
        self.assertEqual(education.start_date, "2010-09-01")
        self.assertEqual(education.end_date, "2014-06-01")
        
        # Test with all fields
        education = Education(
            education_id="edu_1",
            institution="University of California",
            degree="Bachelor of Science",
            field="Computer Science",
            start_date="2010-09-01",
            end_date="2014-06-01",
            gpa=3.8
        )
        self.assertEqual(education.education_id, "edu_1")
        self.assertEqual(education.institution, "University of California")
        self.assertEqual(education.degree, "Bachelor of Science")
        self.assertEqual(education.field, "Computer Science")
        self.assertEqual(education.start_date, "2010-09-01")
        self.assertEqual(education.end_date, "2014-06-01")
        self.assertEqual(education.gpa, 3.8)
    
    def test_candidate_from_dict(self):
        """Test creating a candidate from a dictionary."""
        candidate = Candidate.from_dict(self.candidate_data)
        
        # Check main fields
        self.assertEqual(candidate.resume_id, "resume_123")
        self.assertEqual(candidate.name, "John Doe")
        self.assertEqual(candidate.email, "john.doe@example.com")
        
        # Check nested objects
        self.assertEqual(len(candidate.core_skills), 1)
        self.assertEqual(candidate.core_skills[0].skill_id, "s1")
        self.assertEqual(candidate.core_skills[0].name, "Python")
        
        self.assertEqual(len(candidate.secondary_skills), 1)
        self.assertEqual(candidate.secondary_skills[0].skill_id, "s2")
        self.assertEqual(candidate.secondary_skills[0].name, "JavaScript")
        
        self.assertEqual(len(candidate.experiences), 1)
        self.assertEqual(candidate.experiences[0].title, "Senior Developer")
        self.assertEqual(candidate.experiences[0].company, "Tech Co")
        
        self.assertEqual(len(candidate.education), 1)
        self.assertEqual(candidate.education[0].institution, "University of California")
        self.assertEqual(candidate.education[0].degree, "Bachelor of Science")
    
    def test_candidate_to_dict(self):
        """Test converting a candidate to a dictionary."""
        # Create a candidate from dict
        candidate = Candidate.from_dict(self.candidate_data)
        
        # Convert back to dict
        result = candidate.to_dict()
        
        # Check main fields
        self.assertEqual(result["resume_id"], "resume_123")
        self.assertEqual(result["name"], "John Doe")
        self.assertEqual(result["email"], "john.doe@example.com")
        
        # Check that timestamps are included
        self.assertIn("created_at", result)
        self.assertIn("updated_at", result)
    
    def test_candidate_to_api_dict(self):
        """Test converting a candidate to an API dictionary."""
        # Create a candidate from dict
        candidate = Candidate.from_dict(self.candidate_data)
        
        # Convert to API dict
        result = candidate.to_api_dict()
        
        # Check that skills were included
        self.assertIn("skills", result)
        self.assertEqual(len(result["skills"]["core"]), 1)
        self.assertEqual(len(result["skills"]["secondary"]), 1)
        
        # Check that experiences were included
        self.assertIn("experience", result)
        self.assertEqual(len(result["experience"]), 1)
        
        # Check that education was included
        self.assertIn("education", result)
        self.assertEqual(len(result["education"]), 1)
    
    def test_candidate_skill_serialization(self):
        """Test skill serialization to and from dict."""
        # Create from dict
        skill = CandidateSkill.from_dict(self.skill_data)
        
        # Convert back to dict
        result = skill.to_dict()
        
        # Check fields
        self.assertEqual(result["skill_id"], "s1")
        self.assertEqual(result["name"], "Python")
        self.assertEqual(result["proficiency"], "Expert")
        self.assertEqual(result["experience_years"], 5.0)
        self.assertEqual(result["category"], "Programming")
        self.assertEqual(result["level"], 9)
        self.assertTrue(result["is_core"])
    
    def test_experience_serialization(self):
        """Test experience serialization to and from dict."""
        # Create from dict
        experience = Experience.from_dict(self.experience_data)
        
        # Convert back to dict
        result = experience.to_dict()
        
        # Check fields
        self.assertEqual(result["experience_id"], "exp_1")
        self.assertEqual(result["title"], "Senior Developer")
        self.assertEqual(result["company"], "Tech Co")
        self.assertEqual(result["start_date"], "2020-01-01")
        self.assertEqual(result["end_date"], "Present")
        self.assertIsInstance(result["description"], list)
        self.assertEqual(len(result["description"]), 2)
    
    def test_education_serialization(self):
        """Test education serialization to and from dict."""
        # Create from dict
        education = Education.from_dict(self.education_data)
        
        # Convert back to dict
        result = education.to_dict()
        
        # Check fields
        self.assertEqual(result["education_id"], "edu_1")
        self.assertEqual(result["institution"], "University of California")
        self.assertEqual(result["degree"], "Bachelor of Science")
        self.assertEqual(result["field"], "Computer Science")
        self.assertEqual(result["start_date"], "2010-09-01")
        self.assertEqual(result["end_date"], "2014-06-01")
        self.assertEqual(result["gpa"], 3.8)
    
    def test_candidate_validation(self):
        """Test candidate validation."""
        # Valid candidate
        candidate = Candidate(name="John Doe")
        result = candidate.validate()
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Invalid candidate - missing name
        candidate = Candidate(name="")
        result = candidate.validate()
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("name is required", result["errors"][0])
        
        # Invalid candidate - invalid skills
        candidate = Candidate(name="John Doe")
        # Add a skill without skill_id
        candidate.core_skills.append(CandidateSkill(skill_id="", name="Python"))
        result = candidate.validate()
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("must have a skill_id", result["errors"][0])


if __name__ == '__main__':
    unittest.main() 