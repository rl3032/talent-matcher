"""
Unit tests for the KnowledgeGraph model
"""
import pytest
from unittest.mock import patch, MagicMock
from src.knowledge_graph.model import KnowledgeGraph

class TestKnowledgeGraph:
    
    def test_init(self):
        """Test KnowledgeGraph initialization."""
        kg = KnowledgeGraph("uri", "user", "pass")
        assert kg.uri == "uri"
        assert kg.user == "user"
        assert kg.password == "pass"
        assert kg.driver is None
    
    @patch('src.knowledge_graph.model.GraphDatabase')
    def test_connect(self, mock_graph_db):
        """Test connecting to Neo4j."""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        kg = KnowledgeGraph("uri", "user", "pass")
        kg.connect()
        
        mock_graph_db.driver.assert_called_once_with("uri", auth=("user", "pass"))
        assert kg.driver == mock_driver
    
    @patch('src.knowledge_graph.model.GraphDatabase')
    def test_close(self, mock_graph_db):
        """Test closing the Neo4j connection."""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        
        kg = KnowledgeGraph("uri", "user", "pass")
        kg.connect()
        kg.close()
        
        mock_driver.close.assert_called_once()
    
    @patch('src.knowledge_graph.model.GraphDatabase')
    def test_create_constraints(self, mock_graph_db):
        """Test creating database constraints."""
        # Setup mock session
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_graph_db.driver.return_value = mock_driver
        
        # Execute test
        kg = KnowledgeGraph("uri", "user", "pass")
        kg.connect()
        kg.create_constraints()
        
        # Verify constrains were created
        assert mock_session.run.call_count == 3
        
    @patch('src.knowledge_graph.model.GraphDatabase')
    def test_add_skill(self, mock_graph_db):
        """Test adding a skill to the graph."""
        # Setup mock session
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_graph_db.driver.return_value = mock_driver
        
        # Execute test
        kg = KnowledgeGraph("uri", "user", "pass")
        kg.connect()
        
        skill_data = {
            "skill_id": "python",
            "name": "Python",
            "category": "languages", 
            "domain": "programming"
        }
        kg.add_skill(skill_data)
        
        # Verify query was executed with correct parameters
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args[0]
        assert "MERGE (s:Skill {skill_id: $skill_id})" in call_args[0]
        assert call_args[1] == skill_data
    
    @patch('src.knowledge_graph.model.GraphDatabase')
    def test_add_job(self, mock_graph_db):
        """Test adding a job to the graph."""
        # Setup mock session
        mock_session = MagicMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_graph_db.driver.return_value = mock_driver
        
        # Execute test
        kg = KnowledgeGraph("uri", "user", "pass")
        kg.connect()
        
        job_data = {
            "job_id": "job1",
            "title": "Software Engineer",
            "company": "Tech Inc",
            "responsibilities": ["Write code", "Debug issues"]
        }
        kg.add_job(job_data)
        
        # Verify query was executed
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args[0]
        assert "MERGE (j:Job {job_id: $job_id})" in call_args[0]
        
    @patch('src.knowledge_graph.model.GraphDatabase')
    def test_find_matching_candidates(self, mock_graph_db):
        """Test finding matching candidates for a job."""
        # Setup mock session and result
        mock_result = [
            {"resume_id": "r1", "name": "Candidate 1", "matchScore": 0.85},
            {"resume_id": "r2", "name": "Candidate 2", "matchScore": 0.75}
        ]
        
        mock_session = MagicMock()
        mock_session.run.return_value = mock_result
        
        mock_driver = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_graph_db.driver.return_value = mock_driver
        
        # Execute test
        kg = KnowledgeGraph("uri", "user", "pass")
        kg.connect()
        result = kg.find_matching_candidates("job1", limit=10)
        
        # Verify query was executed with correct parameters
        mock_session.run.assert_called_once()
        call_args = mock_session.run.call_args[0][1]  # Get the second positional argument (the parameter dict)
        assert call_args["job_id"] == "job1"
        assert call_args["limit"] == 10
        
        # Verify result is correct
        assert result == mock_result 