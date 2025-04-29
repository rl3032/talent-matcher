"""
Unit tests for the Job model.
"""

import unittest
from unittest import mock
import os
import sys
import json
from datetime import datetime

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.models.job_model import Job, JobSkill

class TestJobModel(unittest.TestCase):
    """Test case for the Job model."""
    
    def test_job_init(self):
        """Test Job initialization."""
        # Create a job
        job = Job(
            title="Software Engineer",
            company="Tech Company",
            location="San Francisco, CA",
            job_id="job_123",
            owner_email="employer@example.com",
            domain="Software Development",
            summary="Looking for a skilled Software Engineer",
            description="We are looking for a skilled Software Engineer to join our team.",
            job_type="Full-time",
            employment_type="Permanent",
            salary_range="$100,000 - $150,000",
            industry="Technology",
            responsibilities=["Write code", "Review code", "Debug issues"],
            qualifications=["Bachelor's degree", "5+ years experience", "Python skills"],
            created_at=datetime(2023, 1, 1)
        )
        
        # Check attributes
        self.assertEqual(job.title, "Software Engineer")
        self.assertEqual(job.company, "Tech Company")
        self.assertEqual(job.location, "San Francisco, CA")
        self.assertEqual(job.job_id, "job_123")
        self.assertEqual(job.owner_email, "employer@example.com")
        self.assertEqual(job.domain, "Software Development")
        self.assertEqual(job.summary, "Looking for a skilled Software Engineer")
        self.assertEqual(job.description, "We are looking for a skilled Software Engineer to join our team.")
        self.assertEqual(job.job_type, "Full-time")
        self.assertEqual(job.employment_type, "Permanent")
        self.assertEqual(job.salary_range, "$100,000 - $150,000")
        self.assertEqual(job.industry, "Technology")
        self.assertEqual(job.responsibilities, ["Write code", "Review code", "Debug issues"])
        self.assertEqual(job.qualifications, ["Bachelor's degree", "5+ years experience", "Python skills"])
        self.assertEqual(job.created_at, datetime(2023, 1, 1))
        self.assertIsNotNone(job.updated_at)  # Should be auto-created
        
    def test_job_post_init(self):
        """Test Job __post_init__ method."""
        # Test that created_at and updated_at are set if not provided
        job = Job(
            title="Software Engineer",
            company="Tech Company",
            location="San Francisco, CA"
        )
        self.assertIsNotNone(job.created_at)
        self.assertIsNotNone(job.updated_at)
        
        # Test that description is set from summary if empty
        job = Job(
            title="Software Engineer",
            company="Tech Company",
            location="San Francisco, CA",
            summary="Job summary"
        )
        self.assertEqual(job.description, "Job summary")
    
    def test_job_to_dict(self):
        """Test converting Job to dictionary."""
        # Create a job with a fixed datetime for testing
        test_date = datetime(2023, 1, 1)
        job = Job(
            title="Software Engineer",
            company="Tech Company",
            location="San Francisco, CA",
            job_id="job_123",
            owner_email="employer@example.com",
            domain="Software Development",
            responsibilities=["Write code", "Review code"],
            qualifications=["Bachelor's degree", "5+ years experience"],
            created_at=test_date,
            updated_at=test_date
        )
        
        # Convert to dictionary
        job_dict = job.to_dict()
        
        # Check dictionary contents
        self.assertEqual(job_dict["title"], "Software Engineer")
        self.assertEqual(job_dict["company"], "Tech Company")
        self.assertEqual(job_dict["location"], "San Francisco, CA")
        self.assertEqual(job_dict["job_id"], "job_123")
        self.assertEqual(job_dict["owner_email"], "employer@example.com")
        self.assertEqual(job_dict["domain"], "Software Development")
        self.assertEqual(job_dict["created_at"], test_date.isoformat())
        self.assertEqual(job_dict["updated_at"], test_date.isoformat())
        self.assertEqual(job_dict["responsibilities"], json.dumps(["Write code", "Review code"]))
        self.assertEqual(job_dict["qualifications"], json.dumps(["Bachelor's degree", "5+ years experience"]))
    
    def test_job_to_api_dict(self):
        """Test converting Job to API dictionary."""
        # Create a job with a fixed datetime for testing
        test_date = datetime(2023, 1, 1)
        
        # Create a job with primary and secondary skills
        job = Job(
            title="Software Engineer",
            company="Tech Company",
            location="San Francisco, CA",
            created_at=test_date,
            updated_at=test_date
        )
        
        # Add skills
        job.primary_skills = [
            JobSkill(skill_id="skill1", name="Python", proficiency="Expert", importance=0.8)
        ]
        job.secondary_skills = [
            JobSkill(skill_id="skill2", name="JavaScript", proficiency="Intermediate", importance=0.5)
        ]
        
        # Convert to API dictionary
        api_dict = job.to_api_dict()
        
        # Check dictionary contents
        self.assertEqual(api_dict["title"], "Software Engineer")
        self.assertEqual(api_dict["company"], "Tech Company")
        self.assertEqual(api_dict["location"], "San Francisco, CA")
        self.assertEqual(api_dict["created_at"], test_date.isoformat())
        self.assertEqual(api_dict["updated_at"], test_date.isoformat())
        
        # Check skills
        self.assertEqual(len(api_dict["skills"]["primary"]), 1)
        self.assertEqual(len(api_dict["skills"]["secondary"]), 1)
        self.assertEqual(api_dict["skills"]["primary"][0]["skill_id"], "skill1")
        self.assertEqual(api_dict["skills"]["primary"][0]["name"], "Python")
        self.assertEqual(api_dict["skills"]["secondary"][0]["skill_id"], "skill2")
        self.assertEqual(api_dict["skills"]["secondary"][0]["name"], "JavaScript")
    
    def test_job_from_dict(self):
        """Test creating Job from dictionary."""
        # Test job with minimal required fields
        job_dict = {
            "title": "Software Engineer",
            "company": "Tech Company",
            "location": "San Francisco, CA"
        }
        
        job = Job.from_dict(job_dict)
        self.assertEqual(job.title, "Software Engineer")
        self.assertEqual(job.company, "Tech Company")
        self.assertEqual(job.location, "San Francisco, CA")
        
        # Test job with all fields
        test_date_str = "2023-01-01T00:00:00"
        job_dict = {
            "job_id": "job_123",
            "title": "Senior Developer",
            "company": "Big Tech",
            "location": "Remote",
            "owner_email": "employer@example.com",
            "domain": "Web Development",
            "summary": "Senior role",
            "description": "Senior developer role",
            "job_type": "Contract",
            "employment_type": "Part-time",
            "salary_range": "$50/hr",
            "industry": "E-commerce",
            "responsibilities": json.dumps(["Lead team", "Architect solutions"]),
            "qualifications": json.dumps(["10+ years experience", "Leadership skills"]),
            "created_at": test_date_str,
            "updated_at": test_date_str,
            "skills": {
                "primary": [
                    {"skill_id": "skill1", "name": "Python", "proficiency": "Expert", "importance": 0.9}
                ],
                "secondary": [
                    {"skill_id": "skill2", "name": "JavaScript", "proficiency": "Intermediate", "importance": 0.6}
                ]
            }
        }
        
        job = Job.from_dict(job_dict)
        self.assertEqual(job.job_id, "job_123")
        self.assertEqual(job.title, "Senior Developer")
        self.assertEqual(job.responsibilities, ["Lead team", "Architect solutions"])
        self.assertEqual(job.qualifications, ["10+ years experience", "Leadership skills"])
        self.assertEqual(job.created_at.isoformat(), test_date_str)
        self.assertEqual(job.updated_at.isoformat(), test_date_str)
        self.assertEqual(len(job.primary_skills), 1)
        self.assertEqual(len(job.secondary_skills), 1)
        self.assertEqual(job.primary_skills[0].skill_id, "skill1")
        self.assertEqual(job.secondary_skills[0].skill_id, "skill2")
    
    def test_job_validate(self):
        """Test job validation."""
        # Valid job
        valid_job = Job(
            title="Software Engineer",
            company="Tech Company",
            location="San Francisco, CA"
        )
        validation_result = valid_job.validate()
        self.assertTrue(validation_result["valid"])
        self.assertEqual(len(validation_result["errors"]), 0)
        
        # Invalid job - missing title
        invalid_job = Job(
            title="",
            company="Tech Company",
            location="San Francisco, CA"
        )
        validation_result = invalid_job.validate()
        self.assertFalse(validation_result["valid"])
        self.assertTrue(any("title" in error.lower() for error in validation_result["errors"]))
        
        # Invalid job - missing company
        invalid_job = Job(
            title="Software Engineer",
            company="",
            location="San Francisco, CA"
        )
        validation_result = invalid_job.validate()
        self.assertFalse(validation_result["valid"])
        self.assertTrue(any("company" in error.lower() for error in validation_result["errors"]))
        
        # Invalid job - missing location
        invalid_job = Job(
            title="Software Engineer",
            company="Tech Company",
            location=""
        )
        validation_result = invalid_job.validate()
        self.assertFalse(validation_result["valid"])
        self.assertTrue(any("location" in error.lower() for error in validation_result["errors"]))
        
        # Invalid job - skill without skill_id
        invalid_job = Job(
            title="Software Engineer",
            company="Tech Company",
            location="San Francisco, CA"
        )
        invalid_job.primary_skills = [JobSkill(skill_id="", name="Python")]
        validation_result = invalid_job.validate()
        self.assertFalse(validation_result["valid"])
        self.assertTrue(any("skill" in error.lower() for error in validation_result["errors"]))

class TestJobSkill(unittest.TestCase):
    """Test case for the JobSkill model."""
    
    def test_job_skill_init(self):
        """Test JobSkill initialization."""
        # Create a job skill with default values
        skill = JobSkill(
            skill_id="skill_123",
            name="Python"
        )
        
        # Check attributes
        self.assertEqual(skill.skill_id, "skill_123")
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.proficiency, "Intermediate")  # Default value
        self.assertEqual(skill.importance, 0.5)  # Default value
        self.assertEqual(skill.category, "")  # Default value
        self.assertEqual(skill.level, 5)  # Default value
        self.assertTrue(skill.is_primary)  # Default value
        
        # Create a job skill with all attributes
        skill = JobSkill(
            skill_id="skill_456",
            name="JavaScript",
            proficiency="Expert",
            importance=0.9,
            category="Frontend",
            level=8,
            is_primary=False
        )
        
        # Check attributes
        self.assertEqual(skill.skill_id, "skill_456")
        self.assertEqual(skill.name, "JavaScript")
        self.assertEqual(skill.proficiency, "Expert")
        self.assertEqual(skill.importance, 0.9)
        self.assertEqual(skill.category, "Frontend")
        self.assertEqual(skill.level, 8)
        self.assertFalse(skill.is_primary)
    
    def test_job_skill_to_dict(self):
        """Test converting JobSkill to dictionary."""
        # Create a job skill
        skill = JobSkill(
            skill_id="skill_123",
            name="Python",
            proficiency="Expert",
            importance=0.8,
            category="Backend",
            level=7,
            is_primary=True
        )
        
        # Convert to dictionary
        skill_dict = skill.to_dict()
        
        # Check dictionary contents
        self.assertEqual(skill_dict["skill_id"], "skill_123")
        self.assertEqual(skill_dict["name"], "Python")
        self.assertEqual(skill_dict["proficiency"], "Expert")
        self.assertEqual(skill_dict["importance"], 0.8)
        self.assertEqual(skill_dict["category"], "Backend")
        self.assertEqual(skill_dict["level"], 7)
        self.assertTrue(skill_dict["is_primary"])
    
    def test_job_skill_from_dict(self):
        """Test creating JobSkill from dictionary."""
        # Minimal dictionary
        skill_dict = {
            "skill_id": "skill_123",
            "name": "Python"
        }
        
        skill = JobSkill.from_dict(skill_dict)
        self.assertEqual(skill.skill_id, "skill_123")
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.proficiency, "Intermediate")  # Default value
        
        # Complete dictionary
        skill_dict = {
            "skill_id": "skill_456",
            "name": "JavaScript",
            "proficiency": "Expert",
            "importance": 0.9,
            "category": "Frontend",
            "level": 8,
            "is_primary": False
        }
        
        skill = JobSkill.from_dict(skill_dict)
        self.assertEqual(skill.skill_id, "skill_456")
        self.assertEqual(skill.name, "JavaScript")
        self.assertEqual(skill.proficiency, "Expert")
        self.assertEqual(skill.importance, 0.9)
        self.assertEqual(skill.category, "Frontend")
        self.assertEqual(skill.level, 8)
        self.assertFalse(skill.is_primary)

if __name__ == '__main__':
    unittest.main() 