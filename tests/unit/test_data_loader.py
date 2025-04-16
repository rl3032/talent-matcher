"""
Unit tests for the data loading functionality
"""
import pytest
import json
import os
import glob
import tempfile
import sys
from unittest.mock import patch, MagicMock, mock_open, call, Mock
from src.etl.data_loader import (
    load_skills,
    load_jobs,
    load_resumes,
    load_single_resume,
    load_directory,
    initialize_knowledge_graph,
    ETLPipeline
)
from src.knowledge_graph.model import KnowledgeGraph
import unittest

class TestDataLoader(unittest.TestCase):
    
    @patch('src.etl.data_loader.SKILLS', {
        "python": {
            "name": "Python",
            "category": "languages",
            "domain": "software_development",
            "relationships": {
                "RELATED_TO": ["javascript"]
            }
        },
        "javascript": {
            "name": "JavaScript",
            "category": "languages",
            "domain": "web_development"
        }
    })
    def test_load_skills(self):
        """Test loading skills taxonomy."""
        # Setup mock data
        mock_kg = MagicMock()
        
        # Call the function
        load_skills(mock_kg)
        
        # Verify kg.add_skill was called for each skill
        assert mock_kg.add_skill.call_count == 2
        mock_kg.add_skill.assert_any_call({
            "skill_id": "python",
            "name": "Python",
            "category": "languages",
            "domain": "software_development"
        })
        
        # Verify kg.add_skill_relationship was called for the relationship
        mock_kg.add_skill_relationship.assert_called_once_with(
            "python", "javascript", "RELATED_TO"
        )
    
    @patch('src.etl.data_loader.open', new_callable=mock_open)
    @patch('src.etl.data_loader.json.load')
    def test_load_jobs(self, mock_json_load, mock_file_open):
        """Test loading jobs."""
        # Setup mock data
        mock_json_load.return_value = {
            "jobs": [
                {
                    "job_id": "job_1",
                    "title": "Software Engineer",
                    "company": "Tech Inc",
                    "skills": {
                        "primary": [
                            {"skill_id": "python", "name": "Python", "proficiency": "advanced", "importance": 0.9}
                        ],
                        "secondary": [
                            {"skill_id": "javascript", "name": "JavaScript", "proficiency": "intermediate", "importance": 0.7}
                        ]
                    },
                    "skill_relationships": [
                        {"source": "python", "target": "javascript", "type": "REQUIRES", "weight": 0.8}
                    ]
                },
                {
                    "job_id": "job_2",
                    "title": "Data Scientist",
                    "company": "Data Corp",
                    "skills": {
                        "primary": [
                            {"skill_id": "python", "name": "Python", "proficiency": "expert", "importance": 0.95}
                        ],
                        "secondary": []
                    },
                    "skill_relationships": []
                }
            ]
        }
        
        mock_kg = MagicMock()
        
        # Call the function
        load_jobs(mock_kg, "data/job_dataset.json")
        
        # Verify
        mock_file_open.assert_called_once_with("data/job_dataset.json", 'r')
        assert mock_kg.add_job.call_count == 2
        
        # Verify add_job_skill was called for primary and secondary skills
        assert mock_kg.add_job_skill.call_count == 3
        mock_kg.add_job_skill.assert_any_call("job_1", "python", proficiency="advanced", importance=9.0, is_primary=True)
        mock_kg.add_job_skill.assert_any_call("job_1", "javascript", proficiency="intermediate", importance=7.0, is_primary=False)
        
        # Verify add_skill_relationship was called for the relationship
        mock_kg.add_skill_relationship.assert_called_once_with(
            "python", "javascript", "REQUIRES", 0.8
        )
    
    @patch('src.etl.data_loader.open', new_callable=mock_open)
    @patch('src.etl.data_loader.json.load')
    def test_load_resumes(self, mock_json_load, mock_file_open):
        """Test loading resumes."""
        # Setup mock data for a list of resumes
        mock_json_load.return_value = [
            {
                "resume_id": "resume_1",
                "name": "John Doe",
                "title": "Software Engineer",
                "skills": {
                    "core": [
                        {"skill_id": "python", "name": "Python", "proficiency": 4, "experience_years": 3}
                    ],
                    "secondary": [
                        {"skill_id": "javascript", "name": "JavaScript", "proficiency": 3, "experience_years": 2}
                    ]
                },
                "skill_relationships": []
            },
            {
                "resume_id": "resume_2",
                "name": "Jane Smith",
                "title": "Data Scientist",
                "skills": {
                    "core": [
                        {"skill_id": "python", "name": "Python", "proficiency": 5, "experience_years": 5}
                    ],
                    "secondary": []
                },
                "skill_relationships": []
            }
        ]
        
        mock_kg = MagicMock()
        
        # Call the function
        load_resumes(mock_kg, "data/resume_dataset.json")
        
        # Verify
        mock_file_open.assert_called_once_with("data/resume_dataset.json", 'r')
        assert mock_kg.add_candidate.call_count == 2
        
        # Verify add_candidate_skill was called for core and secondary skills
        assert mock_kg.add_candidate_skill.call_count == 3
    
    def test_load_single_resume(self):
        """Test loading a single resume."""
        # Setup mock data
        resume_data = {
            "resume_id": "resume_1",
            "name": "John Doe",
            "title": "Software Engineer",
            "skills": {
                "core": [
                    {"skill_id": "python", "name": "Python", "proficiency": 4, "experience_years": 3}
                ],
                "secondary": [
                    {"skill_id": "javascript", "name": "JavaScript", "proficiency": 3, "experience_years": 2}
                ]
            },
            "skill_relationships": [
                {"source": "python", "target": "javascript", "type": "USES", "weight": 0.7}
            ]
        }
        
        mock_kg = MagicMock()
        
        # Call the function
        load_single_resume(mock_kg, resume_data)
        
        # Verify
        mock_kg.add_candidate.assert_called_once_with(resume_data)
        
        # Verify add_candidate_skill was called for core and secondary skills
        assert mock_kg.add_candidate_skill.call_count == 2
        mock_kg.add_candidate_skill.assert_any_call(
            "resume_1", "python", proficiency=40, experience_years=3, is_core=True
        )
        mock_kg.add_candidate_skill.assert_any_call(
            "resume_1", "javascript", proficiency=30, experience_years=2, is_core=False
        )
        
        # Verify add_skill_relationship was called for the relationship
        mock_kg.add_skill_relationship.assert_called_once_with(
            "python", "javascript", "USES", 0.7
        )
    
    @patch('src.etl.data_loader.glob.glob')
    @patch('src.etl.data_loader.os.path.basename')
    @patch('src.etl.data_loader.json.load')
    @patch('src.etl.data_loader.open', new_callable=mock_open)
    @patch('src.etl.data_loader.load_single_resume')
    def test_load_directory(self, mock_load_resume, mock_file_open, mock_json_load, 
                           mock_basename, mock_glob):
        """Test loading files from a directory."""
        # Setup mock data
        mock_glob.return_value = [
            "/path/to/data/job_1.json",
            "/path/to/data/resume_1.json"
        ]
        
        mock_basename.side_effect = ["job_1.json", "resume_1.json"]
        
        job_data = {"job_id": "job_1", "title": "Software Engineer"}
        resume_data = {"resume_id": "resume_1", "name": "John Doe"}
        
        mock_json_load.side_effect = [job_data, resume_data]
        
        mock_kg = MagicMock()
        
        # Call the function
        load_directory(mock_kg, "/path/to/data")
        
        # Verify
        mock_glob.assert_called_once_with(os.path.join("/path/to/data", "*.json"))
        assert mock_file_open.call_count == 2
        mock_kg.add_job.assert_called_once_with(job_data)
        mock_load_resume.assert_called_once_with(mock_kg, resume_data)
    
    @patch('src.etl.data_loader.KnowledgeGraph')
    @patch('src.etl.data_loader.load_skills')
    @patch('src.etl.data_loader.load_jobs')
    @patch('src.etl.data_loader.load_resumes')
    @patch('src.etl.data_loader.load_directory')
    @patch('src.etl.data_loader.os.path.exists', return_value=True)
    def test_initialize_knowledge_graph(self, mock_exists, mock_load_dir, mock_load_resumes, 
                                       mock_load_jobs, mock_load_skills, mock_kg_class):
        """Test initializing the knowledge graph."""
        # Setup mock data
        mock_kg = MagicMock()
        mock_kg_class.return_value = mock_kg
        
        # Call the function
        with patch('src.knowledge_graph.model.KnowledgeGraph', return_value=mock_kg):
            kg = initialize_knowledge_graph(data_dir="custom/data/dir")
        
        # Verify
        assert kg == mock_kg
        mock_kg.connect.assert_called_once()
        mock_kg.create_constraints.assert_called_once()
        
        # Verify data loading functions were called with correct arguments
        mock_load_skills.assert_called_once_with(mock_kg)
        mock_load_jobs.assert_called_once_with(mock_kg, "custom/data/dir/job_dataset.json")
        mock_load_resumes.assert_called_once_with(mock_kg, "custom/data/dir/resume_dataset.json")
        mock_load_dir.assert_called_once_with(mock_kg, "custom/data/dir/generated")


class TestETLPipeline(unittest.TestCase):
    """Test cases for ETL Pipeline."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample data for testing
        self.sample_skills = {
            "python": {
                "name": "Python",
                "category": "programming_language",
                "domain": "software_development",
                "relationships": {
                    "RELATED_TO": ["data_science"],
                    "REQUIRES": ["sql", "numpy"],
                    "INCLUDES": ["django"]
                }
            },
            "data_science": {
                "name": "Data Science",
                "category": "field",
                "domain": "analytics",
                "relationships": {}
            }
        }
        
        self.sample_jobs = [
            {
                "job_id": "job123",
                "title": "Software Developer",
                "company": "Tech Corp",
                "location": "Remote",
                "domain": "software",
                "summary": "Develop software applications",
                "responsibilities": ["Code review", "Development"],
                "qualifications": ["Bachelor's degree", "3+ years experience"],
                "skills": {
                    "primary": [
                        {"skill_id": "python", "name": "Python", "importance": 0.8, "proficiency": "advanced"}
                    ],
                    "secondary": [
                        {"skill_id": "data_science", "name": "Data Science", "importance": 0.5, "proficiency": "intermediate"}
                    ]
                },
                "skill_relationships": [
                    {"source": "python", "target": "data_science", "type": "RELATED_TO", "weight": 0.7}
                ]
            }
        ]
        
        self.sample_resumes = [
            {
                "resume_id": "res456",
                "name": "Jane Developer",
                "email": "jane@example.com",
                "title": "Senior Developer",
                "location": "New York",
                "domain": "software",
                "summary": "Experienced developer with Python skills",
                "experience": [
                    {
                        "job_title": "Senior Developer",
                        "company": "Tech Solutions",
                        "start_date": "2020-01",
                        "end_date": "Present",
                        "description": ["Led development team", "Implemented Python applications"],
                        "skills_used": ["Python", "Data Science"]
                    },
                    {
                        "job_title": "Junior Developer",
                        "company": "StartupCo",
                        "start_date": "2018-05",
                        "end_date": "2019-12",
                        "description": ["Developed web applications", "Worked with databases"],
                        "skills_used": ["Python", "SQL"]
                    }
                ],
                "education": [
                    {
                        "degree": "BS in Computer Science",
                        "institution": "Tech University",
                        "graduation_year": 2018
                    }
                ],
                "skills": {
                    "core": [
                        {"skill_id": "python", "name": "Python", "proficiency": "advanced", "experience_years": 5}
                    ],
                    "secondary": [
                        {"skill_id": "data_science", "name": "Data Science", "proficiency": "intermediate", "experience_years": 2}
                    ]
                },
                "skill_relationships": [
                    {"source": "python", "target": "data_science", "type": "RELATED_TO", "weight": 0.6}
                ]
            }
        ]
        
        # Create a mock knowledge graph
        self.mock_kg = MagicMock()
        
        # Create an ETL pipeline with the temp directory and mock kg
        self.etl = ETLPipeline(kg=self.mock_kg, data_dir=self.temp_dir)
        
        # Create a mock session for database operations
        self.mock_session = MagicMock()
        self.etl.kg.driver.session.return_value.__enter__.return_value = self.mock_session
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary test directory
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.temp_dir)
    
    def test_extract_skills(self):
        """Test extracting skills data."""
        # Mock SKILLS import
        with patch('src.etl.data_loader.SKILLS', self.sample_skills):
            skills = self.etl.extract_skills()
            self.assertIsInstance(skills, dict)
            self.assertEqual(len(skills), len(self.sample_skills))
    
    def test_extract_jobs(self):
        """Test extracting jobs data."""
        # Create a mock jobs file
        job_file = os.path.join(self.temp_dir, "job_dataset.json")
        with open(job_file, 'w') as f:
            json.dump({"jobs": self.sample_jobs}, f)
        
        jobs = self.etl.extract_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["job_id"], "job123")
    
    def test_extract_resumes(self):
        """Test extracting resumes data."""
        # Create a mock resumes file
        resume_file = os.path.join(self.temp_dir, "resume_dataset.json")
        with open(resume_file, 'w') as f:
            json.dump({"resumes": self.sample_resumes}, f)
        
        resumes = self.etl.extract_resumes()
        self.assertEqual(len(resumes), 1)
        self.assertEqual(resumes[0]["resume_id"], "res456")
    
    def test_transform_skills(self):
        """Test transforming skills data."""
        skill_nodes, skill_relationships = self.etl.transform_skills(self.sample_skills)
        
        # Check skill nodes
        self.assertEqual(len(skill_nodes), 2)
        self.assertEqual(skill_nodes[0]["skill_id"], "python")
        self.assertEqual(skill_nodes[0]["name"], "Python")
        
        # Check skill relationships
        self.assertEqual(len(skill_relationships), 4)  # 2 requires + 1 related_to + 1 includes
    
    def test_transform_jobs(self):
        """Test transforming jobs data."""
        job_nodes, job_skill_rels, skill_rels = self.etl.transform_jobs(self.sample_jobs)
        
        # Check job nodes
        self.assertEqual(len(job_nodes), 1)
        self.assertEqual(job_nodes[0]["job_id"], "job123")
        
        # Check job-skill relationships
        self.assertEqual(len(job_skill_rels), 2)  # 1 primary + 1 secondary
        self.assertEqual(job_skill_rels[0]["job_id"], "job123")
        self.assertEqual(job_skill_rels[0]["skill_id"], "python")
        self.assertEqual(job_skill_rels[0]["is_primary"], True)
        
        # Check skill relationships
        self.assertEqual(len(skill_rels), 1)
        self.assertEqual(skill_rels[0]["source"], "python")
        self.assertEqual(skill_rels[0]["target"], "data_science")
    
    def test_transform_resumes(self):
        """Test transforming resumes data."""
        candidate_nodes, candidate_skill_rels, skill_rels, experience_data = self.etl.transform_resumes(self.sample_resumes)
        
        # Check candidate nodes
        self.assertEqual(len(candidate_nodes), 1)
        self.assertEqual(candidate_nodes[0]["resume_id"], "res456")
        
        # Check candidate-skill relationships
        self.assertEqual(len(candidate_skill_rels), 2)  # 1 core + 1 secondary
        self.assertEqual(candidate_skill_rels[0]["resume_id"], "res456")
        self.assertEqual(candidate_skill_rels[0]["skill_id"], "python")
        self.assertEqual(candidate_skill_rels[0]["is_core"], True)
        self.assertEqual(candidate_skill_rels[0]["level"], 8.5)  # advanced proficiency
        
        # Check skill relationships
        self.assertEqual(len(skill_rels), 1)
        self.assertEqual(skill_rels[0]["source"], "python")
        self.assertEqual(skill_rels[0]["target"], "data_science")
        
        # Check experience data if present in sample
        if "experience" in self.sample_resumes[0]:
            self.assertGreater(len(experience_data), 0)
            self.assertEqual(experience_data[0]["resume_id"], "res456")
    
    def test_proficiency_string_to_level(self):
        """Test conversion of proficiency strings to numeric levels."""
        # Test all proficiency levels
        self.assertEqual(self.etl._get_proficiency_value("beginner"), 5.0)
        self.assertEqual(self.etl._get_proficiency_value("intermediate"), 7.0)
        self.assertEqual(self.etl._get_proficiency_value("advanced"), 8.5)
        self.assertEqual(self.etl._get_proficiency_value("expert"), 10.0)
        
        # Test case insensitivity
        self.assertEqual(self.etl._get_proficiency_value("ADVANCED"), 8.5)
        
        # Test default value for unknown proficiency
        self.assertEqual(self.etl._get_proficiency_value("unknown"), 5.0)
    
    def test_clear_database(self):
        """Test clearing the database."""
        # Call the method with force=True to bypass confirmation
        result = self.etl.clear_database(force=True)
        
        # Verify the result and method calls
        self.assertTrue(result)
        self.mock_session.run.assert_called_once_with("MATCH (n) DETACH DELETE n")
    
    def test_run_pipeline(self):
        """Test running the complete ETL pipeline."""
        # Mock the extract and transform methods
        self.etl.extract_skills = MagicMock(return_value=self.sample_skills)
        self.etl.extract_jobs = MagicMock(return_value=self.sample_jobs)
        self.etl.extract_resumes = MagicMock(return_value=self.sample_resumes)
        
        self.etl.transform_skills = MagicMock(return_value=([], []))
        self.etl.transform_jobs = MagicMock(return_value=([], [], []))
        self.etl.transform_resumes = MagicMock(return_value=([], [], [], []))  # Updated to include experience data
        
        # Mock the load methods
        self.etl.load_skills = MagicMock()
        self.etl.load_jobs = MagicMock()
        self.etl.load_candidates = MagicMock()
        self.etl.load_experiences = MagicMock()  # Mock the new experiences loading method
        
        # Call the pipeline
        result = self.etl.run_pipeline(force=True)
        
        # Verify the pipeline ran successfully
        self.assertTrue(result)
        
        # Verify all expected methods were called
        self.etl.extract_skills.assert_called_once()
        self.etl.extract_jobs.assert_called_once()
        self.etl.extract_resumes.assert_called_once()
        
        self.etl.transform_skills.assert_called_once()
        self.etl.transform_jobs.assert_called_once()
        self.etl.transform_resumes.assert_called_once()
        
        self.etl.load_skills.assert_called_once()
        self.etl.load_jobs.assert_called_once()
        self.etl.load_candidates.assert_called_once()
        self.etl.load_experiences.assert_called_once()  # Verify the new method was called

    def test_transform_experiences(self):
        """Test that experience data is properly extracted from resume data."""
        # We already have experience data in our sample
        _, _, _, experience_data = self.etl.transform_resumes(self.sample_resumes)
        
        # Verify we have the expected experience data
        self.assertEqual(len(experience_data), 2)  # Two experiences in our sample
        
        # Check first experience details
        exp1 = experience_data[0]
        self.assertEqual(exp1["resume_id"], "res456")
        self.assertEqual(exp1["job_title"], "Senior Developer")
        self.assertEqual(exp1["company"], "Tech Solutions")
        self.assertEqual(exp1["start_date"], "2020-01")
        self.assertEqual(exp1["end_date"], "Present")
        self.assertIn("Led development team", exp1["description"])
        self.assertIn("Python", exp1["skills_used"])
        self.assertIn("Data Science", exp1["skills_used"])
        
        # Check second experience details
        exp2 = experience_data[1]
        self.assertEqual(exp2["resume_id"], "res456")
        self.assertEqual(exp2["job_title"], "Junior Developer")
        self.assertEqual(exp2["company"], "StartupCo")
        self.assertEqual(exp2["start_date"], "2018-05")
        self.assertEqual(exp2["end_date"], "2019-12")
        self.assertIn("Developed web applications", exp2["description"])
        self.assertIn("Python", exp2["skills_used"])


if __name__ == '__main__':
    unittest.main() 