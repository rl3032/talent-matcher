#!/usr/bin/env python
"""Unit tests for data_loader.py."""

import unittest
import json
from unittest.mock import patch, MagicMock, mock_open, ANY

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Fix the Python path to find 'src' module
import sys
# Get the absolute path of the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.etl.data_loader import (
    load_skills,
    load_jobs,
    load_resumes,
    load_single_resume,
    load_directory,
    initialize_knowledge_graph,
    ETLPipeline
)
from src.backend.services.graph_service import GraphService
from src.backend.services.skill_service import SkillService

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
    @patch('src.backend.services.skill_service.SkillService.get_instance')
    def test_load_skills(self, mock_skill_service_get_instance):
        """Test loading skills taxonomy."""
        # Setup mock data
        mock_kg = MagicMock()
        mock_skill_service = MagicMock()
        mock_skill_service_get_instance.return_value = mock_skill_service
        
        # Call the function
        load_skills(mock_kg)
        
        # Verify skill_service.create_skill was called for each skill
        assert mock_skill_service.create_skill.call_count == 2
        mock_skill_service.create_skill.assert_any_call({
            "skill_id": "python",
            "name": "Python",
            "category": "languages",
            "domain": "software_development"
        })
        
        # Verify skill_repository.add_skill_relationship was called for the relationship
        mock_kg.skill_repository.add_skill_relationship.assert_called_once_with(
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
        
        # Create mock for kg and its repositories
        mock_kg = MagicMock()
        mock_job_repo = MagicMock()
        mock_skill_repo = MagicMock()
        mock_kg.job_repository = mock_job_repo
        mock_kg.skill_repository = mock_skill_repo
        
        # Call the function
        load_jobs(mock_kg, "data/job_dataset.json")
        
        # Verify
        mock_file_open.assert_called_once_with("data/job_dataset.json", 'r')
        assert mock_job_repo.add_job.call_count == 2
        
        # Verify add_job_skill was called for primary and secondary skills
        assert mock_job_repo.add_job_skill.call_count == 3
        
        # Updated assertions to match the actual method signature
        mock_job_repo.add_job_skill.assert_any_call("job_1", "python", "advanced", 0.9, True)
        mock_job_repo.add_job_skill.assert_any_call("job_1", "javascript", "intermediate", 0.7, False)
        mock_job_repo.add_job_skill.assert_any_call("job_2", "python", "expert", 0.95, True)
        
        # Verify skill_repository.add_skill_relationship was called for the relationship
        mock_skill_repo.add_skill_relationship.assert_called_once_with(
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
        
        # Create mock for kg and its repositories
        mock_kg = MagicMock()
        mock_candidate_repo = MagicMock()
        mock_kg.candidate_repository = mock_candidate_repo
        
        # Call the function
        load_resumes(mock_kg, "data/resume_dataset.json")
        
        # Verify
        mock_file_open.assert_called_once_with("data/resume_dataset.json", 'r')
        # Each resume should be passed to add_candidate
        assert mock_candidate_repo.add_candidate.call_count == 2
        
        # Verify add_candidate_skill was called for core and secondary skills
        assert mock_candidate_repo.add_candidate_skill.call_count == 3
    
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
        
        # Create mock for kg and its repositories
        mock_kg = MagicMock()
        mock_candidate_repo = MagicMock()
        mock_skill_repo = MagicMock()
        mock_session = MagicMock()
        
        # Set up mock session for the experience data
        mock_kg.driver.session.return_value.__enter__.return_value = mock_session
        mock_kg.candidate_repository = mock_candidate_repo
        mock_kg.skill_repository = mock_skill_repo
        mock_kg._process_text_list = lambda x: x if isinstance(x, list) else [x]
        
        # Call the function
        load_single_resume(mock_kg, resume_data)
        
        # Verify candidate repository methods called
        mock_candidate_repo.add_candidate.assert_called_once_with(resume_data)
        
        # Verify add_candidate_skill was called for core and secondary skills
        assert mock_candidate_repo.add_candidate_skill.call_count == 2
        
        # According to the logic in load_single_resume, proficiency is mapped as:
        # >=8: "advanced", >=5: "intermediate", else: "beginner"
        # So proficiency=4 should map to "beginner" for the primary skill
        mock_candidate_repo.add_candidate_skill.assert_any_call(
            "resume_1", "python", "beginner", 3, True
        )
        
        # Similarly, proficiency=3 should map to "beginner" for the secondary skill
        mock_candidate_repo.add_candidate_skill.assert_any_call(
            "resume_1", "javascript", "beginner", 2, False
        )
        
        # Verify skill_repository.add_skill_relationship was called for the relationship
        mock_skill_repo.add_skill_relationship.assert_called_once_with(
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
        assert mock_basename.call_count == 2
        assert mock_json_load.call_count == 2
        assert mock_file_open.call_count == 2
        
        # Verify job and resume load functions called
        mock_kg.add_job.assert_called_once_with(job_data)
        mock_load_resume.assert_called_once_with(mock_kg, resume_data)
    
    @patch('src.etl.data_loader.os.path.exists', return_value=True)
    @patch('src.etl.data_loader.ETLPipeline')
    @patch('src.backend.services.graph_service.GraphService')
    def test_initialize_knowledge_graph(self, mock_graph_class, mock_etl_pipeline_class, mock_exists):
        """Test knowledge graph initialization with both empty and non-empty database scenarios."""
        # Setup
        mock_kg = MagicMock()
        mock_graph_class.return_value = mock_kg
        
        # Mock create_test_accounts on mock_kg
        mock_kg.create_test_accounts = MagicMock()
        
        # Mock session for database check
        mock_session = MagicMock()
        mock_kg.driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock ETL Pipeline instance
        mock_pipeline = MagicMock()
        mock_etl_pipeline_class.return_value = mock_pipeline
        
        # Test 1: Non-empty database case
        mock_result_non_empty = MagicMock()
        mock_result_non_empty.single.return_value = {"node_count": 10}  # Non-zero count to skip data loading
        mock_session.run.return_value = mock_result_non_empty
        
        # Call the function
        result = initialize_knowledge_graph("/path/to/data")
        
        # Verify
        assert result == mock_kg
        mock_graph_class.assert_called_once_with(
            uri=ANY, user=ANY, password=ANY
        )
        mock_kg.create_constraints.assert_called_once()
        mock_kg.ensure_user_schema.assert_called_once()
        
        # Verify session query
        mock_session.run.assert_called_with("MATCH (n) RETURN count(n) as node_count")
        
        # Verify ETL not run since database not empty
        mock_etl_pipeline_class.assert_not_called()
        mock_kg.create_test_accounts.assert_not_called()
        
        # Reset mocks for empty database scenario
        mock_kg.reset_mock()
        mock_session.reset_mock()
        mock_etl_pipeline_class.reset_mock()
        
        # Test 2: Empty database scenario
        mock_result_empty = MagicMock()
        mock_result_empty.single.return_value = {"node_count": 0}  # Empty database
        mock_session.run.return_value = mock_result_empty
        
        # Configure pipeline to successfully complete
        mock_pipeline.run_pipeline.return_value = True
        
        # Call the function again
        result = initialize_knowledge_graph("/path/to/data")
        
        # Verify
        assert result == mock_kg
        mock_kg.create_constraints.assert_called_once()
        mock_kg.ensure_user_schema.assert_called_once()
        
        # Verify session query
        mock_session.run.assert_called_with("MATCH (n) RETURN count(n) as node_count")
        
        # Verify ETL pipeline is instantiated and run
        mock_etl_pipeline_class.assert_called_once_with(mock_kg, data_dir="/path/to/data")
        mock_pipeline.run_pipeline.assert_called_once_with(clear_db=False, generate_embeddings=True)
        mock_kg.create_test_accounts.assert_called_once()

    @patch('src.etl.data_loader.os.path.exists', return_value=True)
    @patch('src.etl.data_loader.ETLPipeline')
    @patch('src.backend.services.graph_service.GraphService')
    def test_initialize_knowledge_graph_with_create_accounts_error(self, mock_graph_class, mock_etl_pipeline_class, mock_exists):
        """Test knowledge graph initialization when creating test accounts raises an error."""
        # Setup
        mock_kg = MagicMock()
        mock_graph_class.return_value = mock_kg
        
        # Mock create_test_accounts on mock_kg to raise an exception
        mock_kg.create_test_accounts = MagicMock(side_effect=Exception("Failed to create test accounts"))
        
        # Mock session for database check
        mock_session = MagicMock()
        mock_kg.driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock ETL Pipeline instance
        mock_pipeline = MagicMock()
        mock_pipeline.run_pipeline.return_value = True  # Pipeline completes successfully
        mock_etl_pipeline_class.return_value = mock_pipeline
        
        # Set up the database to be empty
        mock_result_empty = MagicMock()
        mock_result_empty.single.return_value = {"node_count": 0}  # Empty database
        mock_session.run.return_value = mock_result_empty
        
        # Call the function - should handle error in creating accounts
        result = initialize_knowledge_graph("/path/to/data")
        
        # Verify
        assert result == mock_kg  # Should still return the KG instance
        mock_graph_class.assert_called_once()
        mock_kg.create_constraints.assert_called_once()
        mock_kg.ensure_user_schema.assert_called_once()
        
        # Verify ETL pipeline was instantiated and run successfully
        mock_etl_pipeline_class.assert_called_once_with(mock_kg, data_dir="/path/to/data")
        mock_pipeline.run_pipeline.assert_called_once_with(clear_db=False, generate_embeddings=True)
        
        # Verify create_test_accounts was called but error was caught
        mock_kg.create_test_accounts.assert_called_once()

    @patch('src.etl.data_loader.os.path.exists', return_value=True)
    @patch('src.etl.data_loader.ETLPipeline')
    @patch('src.backend.services.graph_service.GraphService')
    def test_initialize_knowledge_graph_with_etl_error(self, mock_graph_class, mock_etl_pipeline_class, mock_exists):
        """Test knowledge graph initialization when ETL pipeline raises an error."""
        # Setup
        mock_kg = MagicMock()
        mock_graph_class.return_value = mock_kg
        
        # Mock create_test_accounts on mock_kg
        mock_kg.create_test_accounts = MagicMock()
        
        # Mock session for database check
        mock_session = MagicMock()
        mock_kg.driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock ETL Pipeline instance
        mock_pipeline = MagicMock()
        mock_pipeline.run_pipeline.side_effect = Exception("ETL pipeline error")
        mock_etl_pipeline_class.return_value = mock_pipeline
        
        # Set up the database to be empty
        mock_result_empty = MagicMock()
        mock_result_empty.single.return_value = {"node_count": 0}  # Empty database
        mock_session.run.return_value = mock_result_empty
        
        # Call the function - should handle the error
        result = initialize_knowledge_graph("/path/to/data")
        
        # Verify
        assert result == mock_kg  # Should still return the KG instance
        mock_graph_class.assert_called_once_with(
            uri=ANY, user=ANY, password=ANY
        )
        mock_kg.create_constraints.assert_called_once()
        mock_kg.ensure_user_schema.assert_called_once()
        
        # Verify ETL pipeline was instantiated but the error was caught
        mock_etl_pipeline_class.assert_called_once_with(mock_kg, data_dir="/path/to/data")
        mock_pipeline.run_pipeline.assert_called_once_with(clear_db=False, generate_embeddings=True)
        
        # Verify create_test_accounts was not called after error
        mock_kg.create_test_accounts.assert_not_called()


class TestETLPipeline(unittest.TestCase):
    """Test case for the ETLPipeline class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock GraphService
        self.mock_kg = MagicMock(spec=GraphService)
        
        # Set up mock skill service
        self.mock_skill_service = MagicMock(spec=SkillService)
        with patch('src.backend.services.skill_service.SkillService.get_instance', return_value=self.mock_skill_service):
            # Create ETLPipeline instance
            self.etl = ETLPipeline(self.mock_kg)
        
        # Sample test data
        self.sample_skills = {
            "python": {
                "name": "Python",
                "category": "Programming",
                "domain": "Software Development",
                "relationships": {
                    "REQUIRES": ["javascript"]
                }
            },
            "javascript": {
                "name": "JavaScript",
                "category": "Programming",
                "domain": "Web Development"
            }
        }
        
        self.sample_jobs = [
            {
                "job_id": "job_123",
                "title": "Python Developer",
                "company": "Tech Co",
                "location": "Remote",
                "domain": "Software",
                "skills": {
                    "primary": [
                        {"skill_id": "python", "name": "Python", "proficiency": "advanced", "importance": 0.9}
                    ],
                    "secondary": [
                        {"skill_id": "javascript", "name": "JavaScript", "proficiency": "intermediate", "importance": 0.5}
                    ]
                },
                "skill_relationships": [
                    {"source": "python", "target": "javascript", "type": "USES", "weight": 0.8}
                ]
            }
        ]
        
        self.sample_resumes = [
            {
                "resume_id": "resume_123",
                "name": "Jane Developer",
                "title": "Senior Developer",
                "location": "San Francisco",
                "domain": "Software Engineering",
                "skills": {
                    "core": [
                        {"skill_id": "python", "name": "Python", "proficiency": "advanced", "experience_years": 5}
                    ],
                    "secondary": [
                        {"skill_id": "javascript", "name": "JavaScript", "proficiency": "intermediate", "experience_years": 3}
                    ]
                },
                "experience": [
                    {
                        "job_title": "Senior Developer",
                        "company": "Tech Inc",
                        "start_date": "2020-01",
                        "end_date": "Present",
                        "description": ["Developed Python applications"]
                    }
                ],
                "skill_relationships": [
                    {"source": "python", "target": "javascript", "type": "USES", "weight": 0.7}
                ]
            }
        ]
    
    def tearDown(self):
        """Clean up after tests."""
        # Reset mock objects if needed
        self.mock_kg.reset_mock()
        self.mock_skill_service.reset_mock()
    
    def test_extract_skills(self):
        """Test extracting skills from taxonomy."""
        with patch('src.etl.data_loader.SKILLS', self.sample_skills):
            skills = self.etl.extract_skills()
            self.assertEqual(skills, self.sample_skills)
    
    def test_extract_jobs(self):
        """Test extracting jobs from JSON file."""
        with patch('src.etl.data_loader.os.path.exists', return_value=True):
            with patch('src.etl.data_loader.open', mock_open()):
                with patch('src.etl.data_loader.json.load', return_value={"jobs": self.sample_jobs}):
                    jobs = self.etl.extract_jobs()
                    self.assertEqual(jobs, self.sample_jobs)
    
    def test_extract_resumes(self):
        """Test extracting resumes from JSON file."""
        with patch('src.etl.data_loader.os.path.exists', return_value=True):
            with patch('src.etl.data_loader.open', mock_open()):
                with patch('src.etl.data_loader.json.load', return_value={"resumes": self.sample_resumes}):
                    resumes = self.etl.extract_resumes()
                    self.assertEqual(resumes, self.sample_resumes)
    
    def test_transform_skills(self):
        """Test transforming skills data."""
        skill_nodes, skill_relationships = self.etl.transform_skills(self.sample_skills)
        
        # Verify correct number of nodes and relationships
        self.assertEqual(len(skill_nodes), 2)
        self.assertEqual(len(skill_relationships), 1)
        
        # Verify node structure
        self.assertIn({"skill_id": "python", "name": "Python", "category": "Programming", "domain": "Software Development"}, skill_nodes)
        self.assertIn({"skill_id": "javascript", "name": "JavaScript", "category": "Programming", "domain": "Web Development"}, skill_nodes)
        
        # Verify relationship structure
        self.assertIn({"source": "python", "target": "javascript", "type": "REQUIRES"}, skill_relationships)
    
    def test_transform_jobs(self):
        """Test transforming jobs data."""
        job_nodes, job_skill_relationships, skill_relationships = self.etl.transform_jobs(self.sample_jobs)
        
        # Verify job nodes
        self.assertEqual(len(job_nodes), 1)
        job = job_nodes[0]
        self.assertEqual(job["job_id"], "job_123")
        self.assertEqual(job["title"], "Python Developer")
        
        # Verify job-skill relationships
        self.assertEqual(len(job_skill_relationships), 2)
        
        # Verify skill-skill relationships inferred from job
        self.assertEqual(len(skill_relationships), 1)
        rel = skill_relationships[0]
        self.assertEqual(rel["source"], "python")
        self.assertEqual(rel["target"], "javascript")
        self.assertEqual(rel["type"], "USES")
        self.assertEqual(rel["weight"], 0.8)
    
    def test_transform_resumes(self):
        """Test transforming resume data."""
        candidate_nodes, candidate_skill_rels, skill_rels, experience_data = self.etl.transform_resumes(self.sample_resumes)
        
        # Verify candidate nodes
        self.assertEqual(len(candidate_nodes), 1)
        candidate = candidate_nodes[0]
        self.assertEqual(candidate["resume_id"], "resume_123")
        self.assertEqual(candidate["name"], "Jane Developer")
        
        # Verify candidate-skill relationships
        self.assertEqual(len(candidate_skill_rels), 2)
        
        # Verify skill-skill relationships inferred from resume
        self.assertEqual(len(skill_rels), 1)
        
        # Verify experience data
        self.assertEqual(len(experience_data), 1)
        exp = experience_data[0]
        self.assertEqual(exp["resume_id"], "resume_123")
        self.assertEqual(exp["job_title"], "Senior Developer")
        self.assertEqual(exp["company"], "Tech Inc")
    
    def test_proficiency_string_to_level(self):
        """Test proficiency string conversion."""
        # Test valid values
        self.assertEqual(self.etl._get_proficiency_value("beginner"), "beginner")
        self.assertEqual(self.etl._get_proficiency_value("intermediate"), "intermediate")
        self.assertEqual(self.etl._get_proficiency_value("advanced"), "advanced")
        self.assertEqual(self.etl._get_proficiency_value("expert"), "expert")
        
        # Test case insensitivity
        self.assertEqual(self.etl._get_proficiency_value("BEGINNER"), "beginner")
        self.assertEqual(self.etl._get_proficiency_value("Advanced"), "advanced")
        
        # Test invalid values default to beginner
        self.assertEqual(self.etl._get_proficiency_value("unknown"), "beginner")
        self.assertEqual(self.etl._get_proficiency_value(""), "beginner")

    def test_run_pipeline_with_clear_database(self):
        """Test run_pipeline when clear_db is True."""
        # Setup - patch the clear_database method on the mock_kg object
        self.mock_kg.clear_database = MagicMock(return_value=True)
        
        # Mock extract methods
        with patch.object(self.etl, 'extract_skills', return_value={}):
            with patch.object(self.etl, 'extract_jobs', return_value=[]):
                with patch.object(self.etl, 'extract_resumes', return_value=[]):
                    with patch.object(self.etl, 'transform_skills', return_value=([], [])):
                        with patch.object(self.etl, 'transform_jobs', return_value=([], [], [])):
                            with patch.object(self.etl, 'transform_resumes', return_value=([], [], [], [])):
                                with patch.object(self.etl, 'load_skills'):
                                    with patch.object(self.etl, 'load_jobs'):
                                        with patch.object(self.etl, 'load_candidates'):
                                            with patch.object(self.etl, 'load_experiences'):
                                                # Call run_pipeline with clear_db=True
                                                result = self.etl.run_pipeline(clear_db=True, force=True)
                                                
                                                # Verify
                                                self.assertTrue(result)
                                                self.mock_kg.clear_database.assert_called_once_with(True)
                                                self.mock_kg.create_constraints.assert_called_once()

    @patch.object(ETLPipeline, 'load_experiences')
    @patch.object(ETLPipeline, 'load_candidates')
    @patch.object(ETLPipeline, 'load_jobs')
    @patch.object(ETLPipeline, 'load_skills')
    @patch.object(ETLPipeline, 'transform_resumes')
    @patch.object(ETLPipeline, 'transform_jobs')
    @patch.object(ETLPipeline, 'transform_skills')
    @patch.object(ETLPipeline, 'extract_resumes')
    @patch.object(ETLPipeline, 'extract_jobs')
    @patch.object(ETLPipeline, 'extract_skills')
    def test_run_pipeline(self, mock_extract_skills, mock_extract_jobs, 
                         mock_extract_resumes, mock_transform_skills, mock_transform_jobs, 
                         mock_transform_resumes, mock_load_skills, mock_load_jobs, 
                         mock_load_candidates, mock_load_experiences):
        """Test running the full ETL pipeline."""
        # Setup mocks
        mock_extract_skills.return_value = self.sample_skills
        mock_extract_jobs.return_value = self.sample_jobs
        mock_extract_resumes.return_value = self.sample_resumes
        
        # Setup transform mock return values
        mock_transform_skills.return_value = (["skill1"], ["rel1"])
        mock_transform_jobs.return_value = (["job1"], ["job_skill1"], ["rel2"])
        mock_transform_resumes.return_value = (["candidate1"], ["candidate_skill1"], ["rel3"], ["exp1"])
        
        # Mock GraphService.clear_database
        with patch.object(self.mock_kg, 'clear_database', return_value=True) as mock_clear_database:
            # Add generation embeddings mock
            with patch.object(self.mock_kg, 'generate_embeddings', return_value=True) as mock_generate_embeddings:
                # Run the pipeline with embeddings
                result = self.etl.run_pipeline(clear_db=True, force=True, generate_embeddings=True)
                
                # Verify all methods were called in order
                mock_clear_database.assert_called_once_with(True)
                self.mock_kg.create_constraints.assert_called_once()
                mock_extract_skills.assert_called_once()
                mock_extract_jobs.assert_called_once()
                mock_extract_resumes.assert_called_once()
                mock_transform_skills.assert_called_once_with(self.sample_skills)
                mock_transform_jobs.assert_called_once_with(self.sample_jobs)
                mock_transform_resumes.assert_called_once_with(self.sample_resumes)
                
                # Verify combined skill relationships are passed to load_skills
                mock_load_skills.assert_called_once_with(["skill1"], ["rel1", "rel2", "rel3"])
                mock_load_jobs.assert_called_once_with(["job1"], ["job_skill1"])
                mock_load_candidates.assert_called_once_with(["candidate1"], ["candidate_skill1"])
                mock_load_experiences.assert_called_once_with(["exp1"])
                
                # Verify embeddings were generated
                mock_generate_embeddings.assert_called_once()
                
                # Verify result
                self.assertTrue(result)
            
    @patch.object(ETLPipeline, 'extract_skills')
    def test_run_pipeline_with_exception(self, mock_extract_skills):
        """Test handling exceptions in the pipeline."""
        # Setup exception in extract_skills
        mock_extract_skills.side_effect = Exception("Test exception")
        
        # Run the pipeline and verify it handles the exception
        result = self.etl.run_pipeline(clear_db=False)
        
        # Verify result is False on exception
        self.assertFalse(result)

    def test_transform_experiences(self):
        """Test transforming experience data."""
        # This is tested as part of transform_resumes
        pass


class TestClearDatabase(unittest.TestCase):
    """Test case for the clear_database function."""
    
    @patch('src.backend.services.graph_service.GraphService')
    def test_clear_database(self, mock_graph_service_class):
        """Test clearing the database."""
        # Setup mocks
        mock_kg = MagicMock()
        mock_graph_service_class.return_value = mock_kg
        
        # Mock clear_database method
        mock_kg.clear_database.return_value = True
        
        # Test with force=True to skip confirmation
        from src.etl.data_loader import clear_database
        result = clear_database(force=True)
        
        # Verify
        self.assertTrue(result)
        mock_kg.clear_database.assert_called_once_with(True)
        mock_kg.close.assert_called_once()


if __name__ == '__main__':
    unittest.main() 