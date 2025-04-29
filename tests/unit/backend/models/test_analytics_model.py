"""
Unit tests for the analytics models.
"""

import unittest
import datetime
import json
import os
import sys

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.models.analytics_model import (
    SkillGapAnalysis,
    SkillRecommendation,
    CareerPath,
    DashboardStats
)


class TestSkillGapAnalysisModel(unittest.TestCase):
    """Test case for the SkillGapAnalysis model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data for testing
        self.analysis_data = {
            "job_id": "job123",
            "resume_id": "resume456",
            "job_title": "Software Engineer",
            "candidate_name": "John Doe",
            "gap_score": 75.5,
            "missing_skills": [
                {"skill_id": "s1", "name": "Python", "importance": 0.8}
            ],
            "proficiency_gaps": [
                {
                    "skill_id": "s2", 
                    "name": "JavaScript",
                    "candidate_proficiency": "Intermediate",
                    "job_proficiency": "Expert"
                }
            ],
            "total_required_skills": 10,
            "missing_skill_count": 2,
            "created_at": "2023-01-01T12:00:00"
        }
    
    def test_skill_gap_analysis_initialization(self):
        """Test skill gap analysis model initialization."""
        # Test basic initialization
        analysis = SkillGapAnalysis("job123", "resume456")
        self.assertEqual(analysis.job_id, "job123")
        self.assertEqual(analysis.resume_id, "resume456")
        self.assertEqual(analysis.job_title, "")
        self.assertEqual(analysis.gap_score, 0)
        self.assertEqual(len(analysis.missing_skills), 0)
        self.assertEqual(len(analysis.proficiency_gaps), 0)
        self.assertIsNotNone(analysis.created_at)
    
    def test_skill_gap_analysis_from_dict(self):
        """Test creating a skill gap analysis from a dictionary."""
        analysis = SkillGapAnalysis.from_dict(self.analysis_data)
        
        # Check main fields
        self.assertEqual(analysis.job_id, "job123")
        self.assertEqual(analysis.resume_id, "resume456")
        self.assertEqual(analysis.job_title, "Software Engineer")
        self.assertEqual(analysis.candidate_name, "John Doe")
        self.assertEqual(analysis.gap_score, 75.5)
        
        # Check nested structures
        self.assertEqual(len(analysis.missing_skills), 1)
        self.assertEqual(analysis.missing_skills[0]["skill_id"], "s1")
        
        self.assertEqual(len(analysis.proficiency_gaps), 1)
        self.assertEqual(analysis.proficiency_gaps[0]["skill_id"], "s2")
        
        # Check other fields
        self.assertEqual(analysis.total_required_skills, 10)
        self.assertEqual(analysis.missing_skill_count, 2)
        
        # Check timestamp
        self.assertEqual(analysis.created_at, "2023-01-01T12:00:00")
    
    def test_skill_gap_analysis_to_dict(self):
        """Test converting a skill gap analysis to a dictionary."""
        # Create an analysis from dict
        analysis = SkillGapAnalysis.from_dict(self.analysis_data)
        
        # Convert back to dict
        result = analysis.to_dict()
        
        # Check main fields
        self.assertEqual(result["job_id"], "job123")
        self.assertEqual(result["resume_id"], "resume456")
        self.assertEqual(result["job_title"], "Software Engineer")
        self.assertEqual(result["candidate_name"], "John Doe")
        self.assertEqual(result["gap_score"], 75.5)
        
        # Check nested structures
        self.assertEqual(len(result["missing_skills"]), 1)
        self.assertEqual(result["missing_skills"][0]["skill_id"], "s1")
        
        self.assertEqual(len(result["proficiency_gaps"]), 1)
        self.assertEqual(result["proficiency_gaps"][0]["skill_id"], "s2")
        
        # Check timestamp is included
        self.assertIn("created_at", result)
    
    def test_skill_gap_analysis_validation_valid(self):
        """Test validation with valid data."""
        analysis = SkillGapAnalysis("job123", "resume456")
        analysis.gap_score = 75.5
        
        result = analysis.validate()
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
    
    def test_skill_gap_analysis_validation_invalid(self):
        """Test validation with invalid data."""
        # Test with missing job_id
        analysis = SkillGapAnalysis("", "resume456")
        result = analysis.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Job ID is required", result["errors"][0])
        
        # Test with missing resume_id
        analysis = SkillGapAnalysis("job123", "")
        result = analysis.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Resume ID is required", result["errors"][0])
        
        # Test with invalid gap_score
        analysis = SkillGapAnalysis("job123", "resume456")
        analysis.gap_score = 101  # Above range
        result = analysis.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Gap score must be", result["errors"][0])
        
        analysis.gap_score = -1  # Below range
        result = analysis.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Gap score must be", result["errors"][0])


class TestSkillRecommendationModel(unittest.TestCase):
    """Test case for the SkillRecommendation model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data for testing
        self.recommendation_data = {
            "job_id": "job123",
            "resume_id": "resume456",
            "skills": [
                {
                    "skill_id": "s1",
                    "name": "Python",
                    "importance": 0.8,
                    "related_skills": [
                        {"skill_id": "s3", "name": "Django"}
                    ],
                    "learning_resources": [
                        {"title": "Python Course", "provider": "Coursera"}
                    ]
                }
            ],
            "gap_score": 75.5,
            "created_at": "2023-01-01T12:00:00"
        }
    
    def test_skill_recommendation_initialization(self):
        """Test skill recommendation model initialization."""
        # Test basic initialization
        recommendation = SkillRecommendation("job123", "resume456")
        self.assertEqual(recommendation.job_id, "job123")
        self.assertEqual(recommendation.resume_id, "resume456")
        self.assertEqual(len(recommendation.skills), 0)
        self.assertEqual(recommendation.gap_score, 0)
        self.assertIsNotNone(recommendation.created_at)
    
    def test_skill_recommendation_from_dict(self):
        """Test creating a skill recommendation from a dictionary."""
        recommendation = SkillRecommendation.from_dict(self.recommendation_data)
        
        # Check main fields
        self.assertEqual(recommendation.job_id, "job123")
        self.assertEqual(recommendation.resume_id, "resume456")
        self.assertEqual(recommendation.gap_score, 75.5)
        
        # Check skills array
        self.assertEqual(len(recommendation.skills), 1)
        self.assertEqual(recommendation.skills[0]["skill_id"], "s1")
        self.assertEqual(len(recommendation.skills[0]["related_skills"]), 1)
        self.assertEqual(len(recommendation.skills[0]["learning_resources"]), 1)
        
        # Check timestamp
        self.assertEqual(recommendation.created_at, "2023-01-01T12:00:00")
    
    def test_skill_recommendation_to_dict(self):
        """Test converting a skill recommendation to a dictionary."""
        # Create recommendation from dict
        recommendation = SkillRecommendation.from_dict(self.recommendation_data)
        
        # Convert back to dict
        result = recommendation.to_dict()
        
        # Check main fields
        self.assertEqual(result["job_id"], "job123")
        self.assertEqual(result["resume_id"], "resume456")
        self.assertEqual(result["gap_score"], 75.5)
        
        # Check skills array
        self.assertEqual(len(result["skills"]), 1)
        self.assertEqual(result["skills"][0]["skill_id"], "s1")
        
        # Check timestamp is included
        self.assertIn("created_at", result)
    
    def test_skill_recommendation_validation(self):
        """Test validation."""
        # Test with valid data
        recommendation = SkillRecommendation("job123", "resume456")
        result = recommendation.validate()
        
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Test with missing job_id
        recommendation = SkillRecommendation("", "resume456")
        result = recommendation.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Job ID is required", result["errors"][0])
        
        # Test with missing resume_id
        recommendation = SkillRecommendation("job123", "")
        result = recommendation.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Resume ID is required", result["errors"][0])


class TestCareerPathModel(unittest.TestCase):
    """Test case for the CareerPath model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data for testing
        self.path_data = {
            "source_title": "Junior Developer",
            "target_title": "Senior Developer",
            "titles": ["Junior Developer", "Developer", "Senior Developer"],
            "salaries": [60000, 80000, 120000],
            "transitions": [0.8, 0.6],
            "length": 2,
            "created_at": "2023-01-01T12:00:00"
        }
    
    def test_career_path_initialization(self):
        """Test career path model initialization."""
        # Test basic initialization
        path = CareerPath("Junior Developer", "Senior Developer")
        self.assertEqual(path.source_title, "Junior Developer")
        self.assertEqual(path.target_title, "Senior Developer")
        self.assertEqual(path.titles, ["Junior Developer"])
        self.assertEqual(len(path.salaries), 0)
        self.assertEqual(len(path.transitions), 0)
        self.assertEqual(path.path_length, 0)
        self.assertIsNotNone(path.created_at)
        
        # Test without target
        path = CareerPath("Junior Developer")
        self.assertEqual(path.source_title, "Junior Developer")
        self.assertIsNone(path.target_title)
    
    def test_career_path_from_dict(self):
        """Test creating a career path from a dictionary."""
        path = CareerPath.from_dict(self.path_data)
        
        # Check main fields
        self.assertEqual(path.source_title, "Junior Developer")
        self.assertEqual(path.target_title, "Senior Developer")
        
        # Check arrays
        self.assertEqual(len(path.titles), 3)
        self.assertEqual(path.titles[0], "Junior Developer")
        self.assertEqual(path.titles[2], "Senior Developer")
        
        self.assertEqual(len(path.salaries), 3)
        self.assertEqual(path.salaries[0], 60000)
        
        self.assertEqual(len(path.transitions), 2)
        self.assertEqual(path.transitions[0], 0.8)
        
        # Check other fields
        self.assertEqual(path.path_length, 2)
        
        # Check timestamp
        self.assertEqual(path.created_at, "2023-01-01T12:00:00")
    
    def test_career_path_to_dict(self):
        """Test converting a career path to a dictionary."""
        # Create path from dict
        path = CareerPath.from_dict(self.path_data)
        
        # Convert back to dict
        result = path.to_dict()
        
        # Check main fields
        self.assertEqual(result["source_title"], "Junior Developer")
        self.assertEqual(result["target_title"], "Senior Developer")
        
        # Check arrays
        self.assertEqual(len(result["titles"]), 3)
        self.assertEqual(result["titles"][0], "Junior Developer")
        
        self.assertEqual(len(result["salaries"]), 3)
        self.assertEqual(result["salaries"][2], 120000)
        
        self.assertEqual(len(result["transitions"]), 2)
        
        # Check other fields
        self.assertEqual(result["length"], 2)
        
        # Check timestamp is included
        self.assertIn("created_at", result)
    
    def test_career_path_validation(self):
        """Test validation."""
        # Test with valid data
        path = CareerPath.from_dict(self.path_data)
        result = path.validate()
        
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Test with missing source_title
        path = CareerPath("")
        result = path.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("Source title is required", result["errors"][0])
        
        # Test with inconsistent arrays
        path = CareerPath("Junior Developer")
        path.titles = []
        result = path.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("at least one title", result["errors"][0])
        
        # Test with inconsistent path length and transitions
        path = CareerPath("Junior Developer")
        path.path_length = 2
        path.transitions = [0.5]  # Only one transition for path length 2
        result = path.validate()
        
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("must match path length", result["errors"][0])


class TestDashboardStatsModel(unittest.TestCase):
    """Test case for the DashboardStats model."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample data for testing
        self.stats_data = {
            "job_count": 100,
            "candidate_count": 500,
            "company_count": 50,
            "top_skills": [
                {"name": "Python", "count": 200},
                {"name": "JavaScript", "count": 180}
            ],
            "recent_matches": [
                {
                    "job_id": "job123",
                    "job_title": "Software Engineer",
                    "resume_id": "resume456",
                    "candidate_name": "John Doe",
                    "match_score": 85.5
                }
            ],
            "date_range": {
                "start": "2023-01-01T00:00:00",
                "end": "2023-02-01T00:00:00"
            },
            "created_at": "2023-02-02T12:00:00"
        }
    
    def test_dashboard_stats_initialization(self):
        """Test dashboard stats model initialization."""
        # Test without dates
        stats = DashboardStats()
        self.assertIsNotNone(stats.start_date)
        self.assertIsNotNone(stats.end_date)
        self.assertEqual(stats.job_count, 0)
        self.assertEqual(stats.candidate_count, 0)
        self.assertEqual(stats.company_count, 0)
        self.assertEqual(len(stats.top_skills), 0)
        self.assertEqual(len(stats.recent_matches), 0)
        self.assertIsNotNone(stats.created_at)
        
        # Test with specific dates
        start_date = "2023-01-01T00:00:00"
        end_date = "2023-02-01T00:00:00"
        stats = DashboardStats(start_date, end_date)
        self.assertEqual(stats.start_date, start_date)
        self.assertEqual(stats.end_date, end_date)
    
    def test_dashboard_stats_from_dict(self):
        """Test creating dashboard stats from a dictionary."""
        stats = DashboardStats.from_dict(self.stats_data)
        
        # Check main fields
        self.assertEqual(stats.job_count, 100)
        self.assertEqual(stats.candidate_count, 500)
        self.assertEqual(stats.company_count, 50)
        
        # Check arrays
        self.assertEqual(len(stats.top_skills), 2)
        self.assertEqual(stats.top_skills[0]["name"], "Python")
        self.assertEqual(stats.top_skills[0]["count"], 200)
        
        self.assertEqual(len(stats.recent_matches), 1)
        self.assertEqual(stats.recent_matches[0]["job_id"], "job123")
        self.assertEqual(stats.recent_matches[0]["match_score"], 85.5)
        
        # Check date range
        self.assertEqual(stats.start_date, "2023-01-01T00:00:00")
        self.assertEqual(stats.end_date, "2023-02-01T00:00:00")
        
        # Check timestamp
        self.assertEqual(stats.created_at, "2023-02-02T12:00:00")
    
    def test_dashboard_stats_to_dict(self):
        """Test converting dashboard stats to a dictionary."""
        # Create stats from dict
        stats = DashboardStats.from_dict(self.stats_data)
        
        # Convert back to dict
        result = stats.to_dict()
        
        # Check main fields
        self.assertEqual(result["job_count"], 100)
        self.assertEqual(result["candidate_count"], 500)
        self.assertEqual(result["company_count"], 50)
        
        # Check arrays
        self.assertEqual(len(result["top_skills"]), 2)
        self.assertEqual(result["top_skills"][1]["name"], "JavaScript")
        
        self.assertEqual(len(result["recent_matches"]), 1)
        self.assertEqual(result["recent_matches"][0]["candidate_name"], "John Doe")
        
        # Check date range
        self.assertEqual(result["date_range"]["start"], "2023-01-01T00:00:00")
        self.assertEqual(result["date_range"]["end"], "2023-02-01T00:00:00")
        
        # Check timestamp is included
        self.assertIn("created_at", result)


if __name__ == '__main__':
    unittest.main() 