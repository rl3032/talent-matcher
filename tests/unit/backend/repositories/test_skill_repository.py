"""
Unit tests for the SkillRepository class.
"""

import unittest
from unittest import mock
import os
import sys
import json
import uuid

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.repositories.skill_repository import SkillRepository
from neo4j import GraphDatabase, Result, ResultSummary, Record

class TestSkillRepository(unittest.TestCase):
    """Test case for the SkillRepository class."""
    
    def setUp(self):
        """Set up test environment by mocking Neo4j driver."""
        # Create mock for Neo4j driver
        self.mock_driver = mock.MagicMock()
        self.mock_session = mock.MagicMock()
        
        # Configure driver to return mock_session
        self.mock_driver.session.return_value = self.mock_session
        
        # Create mock for Neo4j Result and Record
        self.mock_result = mock.MagicMock(spec=Result)
        self.mock_record = mock.MagicMock(spec=Record)
        
        # Configure mock_record to return test values
        self.test_skill_id = "test_skill_123"
        self.test_data = {
            "skill_id": self.test_skill_id,
            "name": "Python",
            "category": "Programming",
            "description": "Python programming language"
        }
        self.mock_record.__getitem__.side_effect = lambda key: self.test_data.get(key)
        self.mock_record.items.return_value = list(self.test_data.items())
        self.mock_record.keys.return_value = list(self.test_data.keys())
        
        # Make the record properly convert to a dict when dict(record) is called
        self.mock_record.__iter__.return_value = iter(self.test_data.items())
        
        # Configure mock_result to return records
        self.mock_result.__iter__.return_value = [self.mock_record]
        self.mock_result.single.return_value = self.mock_record
        
        # Configure session to return mock_result
        self.mock_session.run.return_value = self.mock_result
        self.mock_session.__enter__.return_value = self.mock_session
        self.mock_session.__exit__.return_value = None
        
        # For transaction methods
        self.mock_session.execute_read.side_effect = lambda func, *args, **kwargs: [self.test_data]
        self.mock_session.execute_write.side_effect = lambda func, *args, **kwargs: func(self.mock_session, *args, **kwargs)
        
        # Configure result summary
        self.mock_summary = mock.MagicMock(spec=ResultSummary)
        self.mock_result.consume.return_value = self.mock_summary
        
        # Create repository
        self.repo = SkillRepository(driver=self.mock_driver)
        
        # Patch execute_write_query to return the mock summary but still track calls
        self.original_execute_write_query = self.repo.execute_write_query
        self.repo.execute_write_query = mock.MagicMock(return_value=self.mock_summary)
        
    def tearDown(self):
        """Clean up test environment."""
        self.repo.close()
        
    def test_add_skill(self):
        """Test add_skill method."""
        # Arrange
        skill_data = {
            "skill_id": self.test_skill_id,
            "name": "Python",
            "category": "Programming",
            "description": "Python programming language"
        }
        
        # Act
        result = self.repo.add_skill(skill_data)
        
        # Assert
        self.assertEqual(result, self.test_skill_id)
        self.repo.execute_write_query.assert_called_once()
        
    def test_add_skill_without_id(self):
        """Test add_skill method when skill_id is not provided."""
        # Arrange
        skill_data = {
            "name": "JavaScript",
            "category": "Programming",
            "description": "JavaScript programming language"
        }
        
        # Mock uuid to return a predictable value
        with mock.patch('uuid.uuid4', return_value=mock.MagicMock(hex='abcdef1234567890')):
            # Act
            result = self.repo.add_skill(skill_data)
            
            # Assert
            self.assertTrue(result.startswith('skill_'))
            self.repo.execute_write_query.assert_called_once()
        
    def test_add_skill_relationship(self):
        """Test add_skill_relationship method."""
        # Arrange
        source_id = self.test_skill_id
        target_id = "test_skill_456"
        rel_type = "RELATED_TO"
        weight = 0.8
        
        # Act
        result = self.repo.add_skill_relationship(source_id, target_id, rel_type, weight)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_add_skill_relationship_with_properties(self):
        """Test add_skill_relationship method with property dictionary."""
        # Arrange
        source_id = self.test_skill_id
        target_id = "test_skill_456"
        rel_type = "RELATED_TO"
        properties = {"weight": 0.8, "strength": "high", "verified": True}
        
        # Act
        result = self.repo.add_skill_relationship(source_id, target_id, rel_type, properties)
        
        # Assert
        self.assertTrue(result)
        self.repo.execute_write_query.assert_called_once()
        
    def test_get_skill(self):
        """Test get_skill method."""
        # Arrange
        skill_id = self.test_skill_id
        
        # Configure mock to return test skill data
        skill_data = [{
            "skill_id": skill_id,
            "name": "Python",
            "category": "Programming",
            "description": "Python programming language"
        }]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=skill_data):
            # Act
            result = self.repo.get_skill(skill_id)
            
            # Assert
            self.assertEqual(result["skill_id"], skill_id)
            self.assertEqual(result["name"], "Python")
            
    def test_get_skill_not_found(self):
        """Test get_skill method when skill doesn't exist."""
        # Arrange
        skill_id = "nonexistent_skill"
        
        # Configure mock to return empty result
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[]):
            # Act
            result = self.repo.get_skill(skill_id)
            
            # Assert
            self.assertIsNone(result)
            
    def test_get_skills_by_category(self):
        """Test get_skills_by_category method."""
        # Arrange
        category = "Programming"
        
        # Configure mock to return test skills
        skills = [
            {
                "skill_id": self.test_skill_id,
                "name": "Python",
                "category": "Programming",
                "description": "Python programming language"
            },
            {
                "skill_id": "test_skill_456",
                "name": "JavaScript",
                "category": "Programming",
                "description": "JavaScript programming language"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=skills):
            # Act
            result = self.repo.get_skills_by_category(category)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "Python")
            self.assertEqual(result[1]["name"], "JavaScript")
            
    def test_get_related_skills(self):
        """Test get_related_skills method."""
        # Arrange
        skill_id = self.test_skill_id
        
        # Configure mock to return test related skills
        related_skills = [
            {
                "skill_id": "test_skill_456",
                "name": "Django",
                "category": "Framework",
                "description": "Python web framework",
                "relationship_type": "REQUIRES"
            },
            {
                "skill_id": "test_skill_789",
                "name": "Flask",
                "category": "Framework",
                "description": "Python micro framework",
                "relationship_type": "RELATED_TO"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=related_skills):
            # Act
            result = self.repo.get_related_skills(skill_id)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "Django")
            self.assertEqual(result[1]["name"], "Flask")
            
    def test_get_related_skills_with_rel_type(self):
        """Test get_related_skills method with specified relationship type."""
        # Arrange
        skill_id = self.test_skill_id
        relationship_type = "RELATED_TO"
        
        # Configure mock to return test related skills
        related_skills = [
            {
                "skill_id": "test_skill_789",
                "name": "Flask",
                "category": "Framework",
                "description": "Python micro framework",
                "relationship_type": "RELATED_TO"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=related_skills):
            # Act
            result = self.repo.get_related_skills(skill_id, relationship_type)
            
            # Assert
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["name"], "Flask")
            self.assertEqual(result[0]["relationship_type"], "RELATED_TO")
            
    def test_recommend_skills_for_job(self):
        """Test recommend_skills_for_job method."""
        # Arrange
        resume_id = "test_resume_123"
        job_id = "test_job_123"
        limit = 5
        
        # Configure mock to return test recommended skills
        recommended_skills = [
            {
                "skill_id": "test_skill_456",
                "name": "Django",
                "category": "Framework",
                "description": "Python web framework",
                "job_importance": 0.9,
                "relevance_to_existing_skills": 2,
                "learning_value": 2.7
            },
            {
                "skill_id": "test_skill_789",
                "name": "Flask",
                "category": "Framework",
                "description": "Python micro framework",
                "job_importance": 0.7,
                "relevance_to_existing_skills": 1,
                "learning_value": 1.4
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=recommended_skills):
            # Act
            result = self.repo.recommend_skills_for_job(resume_id, job_id, limit)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "Django")
            self.assertEqual(result[1]["name"], "Flask")
            
    def test_get_skill_path(self):
        """Test get_skill_path method."""
        # Arrange
        start_skill_id = self.test_skill_id
        end_skill_id = "test_skill_456"
        max_depth = 3
        
        # Configure mock to return test skill path
        skill_path = [{
            "skill_ids": [start_skill_id, "test_skill_789", end_skill_id],
            "skill_names": ["Python", "Django", "Web Development"],
            "relationship_types": ["REQUIRES", "RELATED_TO"]
        }]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=skill_path):
            # Act
            result = self.repo.get_skill_path(start_skill_id, end_skill_id, max_depth)
            
            # Assert
            self.assertIsNotNone(result)
            self.assertEqual(result["skill_ids"][0], start_skill_id)
            self.assertEqual(result["skill_ids"][2], end_skill_id)
            self.assertEqual(result["skill_names"][1], "Django")
            self.assertEqual(len(result["relationship_types"]), 2)
            
    def test_get_skill_path_not_found(self):
        """Test get_skill_path method when no path exists."""
        # Arrange
        start_skill_id = self.test_skill_id
        end_skill_id = "test_skill_999"
        max_depth = 3
        
        # Configure mock to return empty result
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[]):
            # Act
            result = self.repo.get_skill_path(start_skill_id, end_skill_id, max_depth)
            
            # Assert
            self.assertIsNone(result)
            
    def test_extract_skill_details(self):
        """Test _extract_skill_details method."""
        # Arrange
        cypher_response = [
            {
                "skill_id": self.test_skill_id,
                "name": "Python",
                "category": "Programming",
                "description": "Python programming language",
                "additional_field": "value"
            }
        ]
        required_fields = ["skill_id", "name", "category"]
        optional_fields = ["description"]
        
        # Act
        result = self.repo._extract_skill_details(cypher_response, required_fields, optional_fields)
        
        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["skill_id"], self.test_skill_id)
        self.assertEqual(result[0]["name"], "Python")
        self.assertEqual(result[0]["category"], "Programming")
        self.assertEqual(result[0]["description"], "Python programming language")
        # Additional field should not be present
        self.assertNotIn("additional_field", result[0])
        
    def test_extract_skill_details_missing_required_field(self):
        """Test _extract_skill_details method with missing required field."""
        # Arrange
        cypher_response = [
            {
                "skill_id": self.test_skill_id,
                "name": "Python",
                # Missing category field
                "description": "Python programming language"
            }
        ]
        required_fields = ["skill_id", "name", "category"]
        optional_fields = ["description"]
        
        # Act
        result = self.repo._extract_skill_details(cypher_response, required_fields, optional_fields)
        
        # Assert
        self.assertEqual(len(result), 0)
        
    def test_find_skill_by_name(self):
        """Test find_skill_by_name method."""
        # Arrange
        skill_name = "Python"
        
        # Configure mock to return test skill data
        skill_data = [{
            "skill_id": self.test_skill_id,
            "name": "Python",
            "category": "Programming",
            "description": "Python programming language"
        }]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=skill_data):
            # Act
            result = self.repo.find_skill_by_name(skill_name)
            
            # Assert
            self.assertEqual(result["skill_id"], self.test_skill_id)
            self.assertEqual(result["name"], "Python")
            
    def test_find_skill_by_name_not_found(self):
        """Test find_skill_by_name method when skill doesn't exist."""
        # Arrange
        skill_name = "NonexistentSkill"
        
        # Configure mock to return empty result
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[]):
            # Act
            result = self.repo.find_skill_by_name(skill_name)
            
            # Assert
            self.assertIsNone(result)
            
    def test_recommend_skills(self):
        """Test recommend_skills method."""
        # Arrange
        resume_id = "test_resume_123"
        limit = 5
        
        # Configure mock to return test recommended skills
        recommended_skills = [
            {
                "skill_id": "test_skill_456",
                "name": "Django",
                "job_demand": 15,
                "relevance": 3,
                "score": 45
            },
            {
                "skill_id": "test_skill_789",
                "name": "Flask",
                "job_demand": 10,
                "relevance": 2,
                "score": 20
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=recommended_skills):
            # Act
            result = self.repo.recommend_skills(resume_id, limit)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "Django")
            self.assertEqual(result[1]["name"], "Flask")
            
    def test_get_all_skills(self):
        """Test get_all_skills method."""
        # Arrange
        skills = [
            {
                "skill_id": self.test_skill_id,
                "name": "Python",
                "category": "Programming",
                "description": "Python programming language"
            },
            {
                "skill_id": "test_skill_456",
                "name": "JavaScript",
                "category": "Programming",
                "description": "JavaScript programming language"
            },
            {
                "skill_id": "test_skill_789",
                "name": "Project Management",
                "category": "Business",
                "description": "Project management skills"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=skills):
            # Act
            result = self.repo.get_all_skills()
            
            # Assert
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]["name"], "Python")
            self.assertEqual(result[2]["category"], "Business")

    def test_find_skills_without_filters(self):
        """Test find_skills method with no filters."""
        # Arrange
        limit = 10
        offset = 0
        
        skills = [
            {
                "skill_id": self.test_skill_id,
                "name": "Python",
                "category": "Programming",
                "description": "Python programming language"
            },
            {
                "skill_id": "test_skill_456",
                "name": "JavaScript",
                "category": "Programming",
                "description": "JavaScript programming language"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=skills):
            # Act
            result = self.repo.find_skills(None, limit, offset)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "Python")
            self.assertEqual(result[1]["name"], "JavaScript")
    
    def test_find_skills_with_name_filter(self):
        """Test find_skills method with name filter."""
        # Arrange
        filters = {"name": "Py"}
        limit = 10
        offset = 0
        
        skills = [
            {
                "skill_id": self.test_skill_id,
                "name": "Python",
                "category": "Programming",
                "description": "Python programming language"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=skills):
            # Act
            result = self.repo.find_skills(filters, limit, offset)
            
            # Assert
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["name"], "Python")
    
    def test_find_skills_with_category_filter(self):
        """Test find_skills method with category filter."""
        # Arrange
        filters = {"category": "Programming"}
        limit = 10
        offset = 0
        
        skills = [
            {
                "skill_id": self.test_skill_id,
                "name": "Python",
                "category": "Programming",
                "description": "Python programming language"
            },
            {
                "skill_id": "test_skill_456",
                "name": "JavaScript",
                "category": "Programming",
                "description": "JavaScript programming language"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=skills):
            # Act
            result = self.repo.find_skills(filters, limit, offset)
            
            # Assert
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["category"], "Programming")
            self.assertEqual(result[1]["category"], "Programming")
    
    def test_find_skills_with_domain_filter(self):
        """Test find_skills method with domain filter."""
        # Arrange
        filters = {"domain": "Web Development"}
        limit = 10
        offset = 0
        
        skills = [
            {
                "skill_id": "test_skill_456",
                "name": "JavaScript",
                "category": "Programming",
                "domain": "Web Development",
                "description": "JavaScript programming language"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=skills):
            # Act
            result = self.repo.find_skills(filters, limit, offset)
            
            # Assert
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["name"], "JavaScript")
    
    def test_find_skills_with_multiple_filters(self):
        """Test find_skills method with multiple filters."""
        # Arrange
        filters = {
            "name": "Java",
            "category": "Programming",
            "domain": "Web Development"
        }
        limit = 10
        offset = 0
        
        skills = [
            {
                "skill_id": "test_skill_456",
                "name": "JavaScript",
                "category": "Programming",
                "domain": "Web Development",
                "description": "JavaScript programming language"
            }
        ]
        
        with mock.patch.object(self.repo, 'execute_read_query', return_value=skills):
            # Act
            result = self.repo.find_skills(filters, limit, offset)
            
            # Assert
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["name"], "JavaScript")
    
    def test_get_skill_graph(self):
        """Test get_skill_graph method."""
        # Arrange
        skill_id = self.test_skill_id
        
        # Mock the central skill query result
        central_node = [{
            "id": skill_id,
            "name": "Python",
            "category": "Programming",
            "type": "skill"
        }]
        
        # Mock the related skills query result
        related_nodes = [
            {
                "id": "test_skill_456",
                "name": "Django",
                "category": "Framework",
                "type": "skill",
                "source": skill_id,
                "target": "test_skill_456",
                "relationship": "REQUIRES"
            },
            {
                "id": "test_skill_789",
                "name": "Flask",
                "category": "Framework",
                "type": "skill",
                "source": skill_id,
                "target": "test_skill_789",
                "relationship": "RELATED_TO"
            }
        ]
        
        # Configure mock to return different results based on query
        def mock_execute_read(query, params):
            if "related:Skill" in query:
                return related_nodes
            return central_node
            
        with mock.patch.object(self.repo, 'execute_read_query', side_effect=mock_execute_read):
            # Act
            result = self.repo.get_skill_graph(skill_id)
            
            # Assert
            self.assertEqual(len(result["nodes"]), 3)  # Central node + 2 related nodes
            self.assertEqual(len(result["edges"]), 2)  # 2 relationships
            
            # Check if central node is included
            node_ids = [node["id"] for node in result["nodes"]]
            self.assertIn(skill_id, node_ids)
            
            # Check if relationships are properly formed
            edge_rels = [edge["relationship"] for edge in result["edges"]]
            self.assertIn("REQUIRES", edge_rels)
            self.assertIn("RELATED_TO", edge_rels)
    
    def test_get_skill_graph_not_found(self):
        """Test get_skill_graph method when skill doesn't exist."""
        # Arrange
        skill_id = "nonexistent_skill"
        
        # Configure mock to return empty result
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[]):
            # Act
            result = self.repo.get_skill_graph(skill_id)
            
            # Assert
            self.assertEqual(len(result["nodes"]), 0)
            self.assertEqual(len(result["edges"]), 0)
    
    def test_get_skills_network(self):
        """Test get_skills_network method."""
        # Arrange
        limit = 10
        
        # Mock the skills query result
        nodes = [
            {
                "id": self.test_skill_id,
                "name": "Python",
                "category": "Programming",
                "type": "skill"
            },
            {
                "id": "test_skill_456",
                "name": "Django",
                "category": "Framework",
                "type": "skill"
            }
        ]
        
        # Mock the relationships query result
        edges = [
            {
                "source": self.test_skill_id,
                "target": "test_skill_456",
                "relationship": "REQUIRES"
            }
        ]
        
        # Configure mock to return different results based on query
        def mock_execute_read(query, params):
            if "s1:Skill)-[r]-(s2:Skill" in query:
                return edges
            return nodes
            
        with mock.patch.object(self.repo, 'execute_read_query', side_effect=mock_execute_read):
            # Act
            result = self.repo.get_skills_network(limit)
            
            # Assert
            self.assertEqual(len(result["nodes"]), 2)
            self.assertEqual(len(result["edges"]), 1)
            
            # Check if nodes are properly included
            node_ids = [node["id"] for node in result["nodes"]]
            self.assertIn(self.test_skill_id, node_ids)
            self.assertIn("test_skill_456", node_ids)
            
            # Check if relationship is properly formed
            self.assertEqual(result["edges"][0]["source"], self.test_skill_id)
            self.assertEqual(result["edges"][0]["target"], "test_skill_456")
            self.assertEqual(result["edges"][0]["relationship"], "REQUIRES")
    
    def test_get_skills_network_empty(self):
        """Test get_skills_network method when no skills exist."""
        # Arrange
        limit = 10
        
        # Configure mock to return empty result
        with mock.patch.object(self.repo, 'execute_read_query', return_value=[]):
            # Act
            result = self.repo.get_skills_network(limit)
            
            # Assert
            self.assertEqual(len(result["nodes"]), 0)
            self.assertEqual(len(result["edges"]), 0)

if __name__ == '__main__':
    unittest.main() 