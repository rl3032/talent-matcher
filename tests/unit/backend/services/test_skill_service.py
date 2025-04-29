"""
Unit tests for the skill service.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import datetime
import json

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.services.skill_service import SkillService
from src.backend.repositories.skill_repository import SkillRepository


class TestSkillService(unittest.TestCase):
    """Test case for the skill service."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock graph service
        self.mock_graph_service = MagicMock()
        self.mock_graph_service.driver = MagicMock()
        
        # Create a mock repository
        self.mock_repo = MagicMock()
        
        # Create the service with mock graph service
        self.skill_service = SkillService(graph_service=self.mock_graph_service)
        
        # Replace the skill_repository with our mock
        self.skill_service.skill_repository = self.mock_repo
        
        # Sample skill data for testing
        self.sample_skills = [
            {
                'skill_id': 'skill_1',
                'name': 'Python',
                'category': 'Programming',
                'description': 'Python programming language'
            },
            {
                'skill_id': 'skill_2',
                'name': 'JavaScript',
                'category': 'Programming',
                'description': 'JavaScript programming language'
            },
            {
                'skill_id': 'skill_3',
                'name': 'SQL',
                'category': 'Database',
                'description': 'SQL database query language'
            },
            {
                'skill_id': 'skill_4',
                'name': 'AWS',
                'category': 'Cloud',
                'description': 'Amazon Web Services'
            },
            {
                'skill_id': 'skill_5',
                'name': 'Project Management',
                'category': 'Soft Skills',
                'description': 'Managing projects and teams'
            }
        ]
        
        # Sample skill for create/update testing
        self.new_skill_data = {
            'name': 'React',
            'category': 'Frontend',
            'description': 'React JavaScript library'
        }
        
        self.updated_skill_data = {
            'skill_id': 'skill_1',
            'name': 'Python 3',
            'category': 'Programming',
            'description': 'Updated Python programming language'
        }
    
    def test_find_skills(self):
        """Test finding skills with filters."""
        # Set up mock repository
        self.mock_repo.find_skills.return_value = self.sample_skills
        
        # Call the service method
        result = self.skill_service.find_skills()
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(len(result['skills']), 5)
        
        # Verify repo was called
        self.mock_repo.find_skills.assert_called_once()
    
    def test_find_skills_with_filters(self):
        """Test finding skills with specific filters."""
        # Set up filters
        filters = {'category': 'Programming'}
        
        # Filter to only programming skills
        filtered_skills = [skill for skill in self.sample_skills if skill['category'] == 'Programming']
        
        # Set up mock repository to return filtered results
        self.mock_repo.find_skills.return_value = filtered_skills
        
        # Call the service method with filters
        result = self.skill_service.find_skills(filters=filters, limit=10, offset=0)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(len(result['skills']), 2)  # Should have 2 programming skills
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['limit'], 10)
        self.assertEqual(result['offset'], 0)
        
        # Verify repo was called with correct parameters
        self.mock_repo.find_skills.assert_called_once_with(filters, 10, 0)
    
    def test_get_skill_success(self):
        """Test getting a skill by ID successfully."""
        # Sample skill data to return
        skill_id = 'skill_1'
        sample_skill = self.sample_skills[0]
        
        # Set up mock repository
        self.mock_repo.get_skill.return_value = sample_skill
        
        # Call the service method
        result = self.skill_service.get_skill(skill_id)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['skill'], sample_skill)
        self.assertEqual(result['skill']['name'], 'Python')
        
        # Verify repo was called with correct ID
        self.mock_repo.get_skill.assert_called_once_with(skill_id)
    
    def test_get_skill_not_found(self):
        """Test getting a skill by ID when it doesn't exist."""
        # Set up mock repository to return None (not found)
        self.mock_repo.get_skill.return_value = None
        
        # Call the service method
        result = self.skill_service.get_skill('nonexistent_skill')
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('not found', result['error'].lower())
        
        # Verify repo was called
        self.mock_repo.get_skill.assert_called_once()
    
    def test_create_skill_success(self):
        """Test creating a new skill successfully."""
        # Set up mock repository
        skill_id = 'skill_642a9d9a'  # Use the actual format generated by the service
        self.mock_repo.add_skill.return_value = skill_id
        
        # Call the service method
        result = self.skill_service.create_skill(self.new_skill_data)
        
        # Assertions
        self.assertTrue(result['success'])
        # Don't check the exact ID since it's generated dynamically
        self.assertTrue('skill_id' in result)
        self.assertTrue(result['skill_id'].startswith('skill_'))
        
        # Verify repo was called
        self.mock_repo.add_skill.assert_called_once()
    
    def test_create_skill_with_provided_id(self):
        """Test creating a skill with a provided ID."""
        # Create skill data with an ID already specified
        skill_data_with_id = self.new_skill_data.copy()
        skill_data_with_id['skill_id'] = 'skill_custom_id'
        
        # Set up mock repository
        self.mock_repo.add_skill.return_value = 'skill_custom_id'
        
        # Call the service method
        result = self.skill_service.create_skill(skill_data_with_id)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['skill_id'], 'skill_custom_id')
        
        # Verify repo was called with the prepared skill that includes the provided ID
        called_args = self.mock_repo.add_skill.call_args[0][0]
        self.assertEqual(called_args['skill_id'], 'skill_custom_id')
    
    def test_create_skill_validation_error(self):
        """Test creating a skill with missing required fields."""
        # Create an invalid skill missing required fields
        invalid_skill = {'description': 'Invalid skill'}  # Missing name field
        
        # Call the service method
        result = self.skill_service.create_skill(invalid_skill)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('name', result['error'].lower())
        
        # Verify repo was NOT called
        self.mock_repo.add_skill.assert_not_called()
    
    def test_update_skill_success(self):
        """Test updating an existing skill successfully."""
        # Set up mock repository
        skill_id = 'skill_1'
        existing_skill = self.sample_skills[0]
        
        # Set up the mock returns
        self.mock_repo.get_skill.return_value = existing_skill
        self.mock_repo.add_skill.return_value = skill_id
        
        # Call the service method
        result = self.skill_service.update_skill(skill_id, self.updated_skill_data)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['skill_id'], skill_id)
        
        # Verify repo methods were called correctly
        self.mock_repo.get_skill.assert_called_once_with(skill_id)
        # add_skill should be called once for updating
        self.mock_repo.add_skill.assert_called_once()
    
    def test_update_skill_not_found(self):
        """Test updating a skill that doesn't exist."""
        # Set up mock repository to return None (not found)
        self.mock_repo.get_skill.return_value = None
        
        # Call the service method
        skill_id = 'nonexistent_skill'
        result = self.skill_service.update_skill(skill_id, self.updated_skill_data)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('not found', result['error'].lower())
        
        # Verify get_skill was called but add_skill was not
        self.mock_repo.get_skill.assert_called_once_with(skill_id)
        self.mock_repo.add_skill.assert_not_called()
    
    def test_update_skill_error(self):
        """Test handling of exceptions in update_skill."""
        skill_id = 'skill_1'
        
        # Set up mocks
        self.mock_repo.get_skill.return_value = self.sample_skills[0]
        self.mock_repo.add_skill.side_effect = Exception("Test error")
        
        # Call service method
        result = self.skill_service.update_skill(skill_id, self.updated_skill_data)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('error updating skill', result['error'].lower())
    
    def test_delete_skill_success(self):
        """Test deleting a skill successfully."""
        # Set up mock repository
        skill_id = 'skill_1'
        existing_skill = self.sample_skills[0]
        
        # Set up mock returns
        self.mock_repo.get_skill.return_value = existing_skill
        self.mock_repo.delete_skill.return_value = True
        
        # Call the service method
        result = self.skill_service.delete_skill(skill_id)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertIn('message', result)
        self.assertIn('deleted', result['message'].lower())
        
        # Verify repo methods were called correctly
        self.mock_repo.get_skill.assert_called_once_with(skill_id)
        self.mock_repo.delete_skill.assert_called_once_with(skill_id)
    
    def test_delete_skill_not_found(self):
        """Test deleting a skill that doesn't exist."""
        # Set up mock repository to return None (not found)
        self.mock_repo.get_skill.return_value = None
        
        # Call the service method
        skill_id = 'nonexistent_skill'
        result = self.skill_service.delete_skill(skill_id)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('not found', result['error'].lower())
        
        # Verify get_skill was called but delete_skill was not
        self.mock_repo.get_skill.assert_called_once_with(skill_id)
        self.mock_repo.delete_skill.assert_not_called()
    
    def test_delete_skill_error(self):
        """Test handling of exceptions in delete_skill."""
        skill_id = 'skill_1'
        
        # Set up mocks
        self.mock_repo.get_skill.return_value = self.sample_skills[0]
        self.mock_repo.delete_skill.side_effect = Exception("Test error")
        
        # Call service method
        result = self.skill_service.delete_skill(skill_id)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('error deleting skill', result['error'].lower())
    
    def test_get_related_skills(self):
        """Test getting related skills."""
        skill_id = 'skill_1'
        related_skills = [
            {
                'skill_id': 'skill_2',
                'name': 'JavaScript',
                'relationship_type': 'RELATED_TO'
            }
        ]
        
        # Set up mock repository
        self.mock_repo.get_skill.return_value = self.sample_skills[0]
        self.mock_repo.get_related_skills.return_value = related_skills
        
        # Call the service method
        result = self.skill_service.get_related_skills(skill_id)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['related_skills'], related_skills)
        
        # Verify repo was called with correct parameters
        self.mock_repo.get_skill.assert_called_once_with(skill_id)
        self.mock_repo.get_related_skills.assert_called_once_with(skill_id)
    
    def test_get_related_skills_not_found(self):
        """Test getting related skills for a non-existent skill."""
        skill_id = 'nonexistent_skill'
        
        # Set up mock returns
        self.mock_repo.get_skill.return_value = None
        
        # Call service method
        result = self.skill_service.get_related_skills(skill_id)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('not found', result['error'].lower())
        
        # Verify repo method was called correctly
        self.mock_repo.get_skill.assert_called_once_with(skill_id)
        self.mock_repo.get_related_skills.assert_not_called()
    
    def test_get_related_skills_error(self):
        """Test handling of exceptions in get_related_skills."""
        skill_id = 'skill_1'
        
        # Set up mock to raise exception
        self.mock_repo.get_skill.return_value = self.sample_skills[0]
        self.mock_repo.get_related_skills.side_effect = Exception("Test error")
        
        # Call service method
        result = self.skill_service.get_related_skills(skill_id)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('error finding related skills', result['error'].lower())
    
    def test_get_instance(self):
        """Test getting singleton instance."""
        # Create a mock graph service
        mock_graph_svc = MagicMock()
        
        # Get service instance
        service1 = SkillService.get_instance(mock_graph_svc)
        service2 = SkillService.get_instance()
        
        # Verify both are the same instance
        self.assertIs(service1, service2)
    
    def test_get_skill_path_success(self):
        """Test getting a path between two skills successfully."""
        source_id = 'skill_1'
        target_id = 'skill_3'
        
        # Sample path data
        path_data = {
            'skill_ids': [source_id, 'skill_2', target_id],
            'skill_names': ['Python', 'JavaScript', 'SQL'],
            'relationship_types': ['RELATED_TO', 'RELATED_TO']
        }
        
        # Set up mocks
        self.mock_repo.get_skill.side_effect = [self.sample_skills[0], self.sample_skills[2]]  # Source and target skills
        self.mock_repo.get_skill_path.return_value = path_data
        
        # Call service method
        result = self.skill_service.get_skill_path(source_id, target_id)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['path'], path_data)
        
        # Verify repo methods were called
        self.mock_repo.get_skill.assert_any_call(source_id)
        self.mock_repo.get_skill.assert_any_call(target_id)
        self.mock_repo.get_skill_path.assert_called_once_with(source_id, target_id)
    
    def test_get_skill_path_source_not_found(self):
        """Test getting a path when source skill doesn't exist."""
        source_id = 'nonexistent_skill'
        target_id = 'skill_3'
        
        # Set up mocks
        self.mock_repo.get_skill.side_effect = [None, self.sample_skills[2]]  # Source not found, target found
        
        # Call service method
        result = self.skill_service.get_skill_path(source_id, target_id)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('source skill', result['error'].lower())
        
        # Verify repo methods were called
        self.mock_repo.get_skill.assert_called_with(source_id)
        self.mock_repo.get_skill_path.assert_not_called()
    
    def test_get_skill_path_target_not_found(self):
        """Test getting a path when target skill doesn't exist."""
        source_id = 'skill_1'
        target_id = 'nonexistent_skill'
        
        # Set up mocks
        self.mock_repo.get_skill.side_effect = [self.sample_skills[0], None]  # Source found, target not found
        
        # Call service method
        result = self.skill_service.get_skill_path(source_id, target_id)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('target skill', result['error'].lower())
        
        # Verify repo methods were called
        self.mock_repo.get_skill.assert_any_call(source_id)
        self.mock_repo.get_skill.assert_any_call(target_id)
        self.mock_repo.get_skill_path.assert_not_called()
    
    def test_get_skill_path_no_path_found(self):
        """Test getting a path when no path exists between skills."""
        source_id = 'skill_1'
        target_id = 'skill_3'
        
        # Set up mocks
        self.mock_repo.get_skill.side_effect = [self.sample_skills[0], self.sample_skills[2]]  # Both skills exist
        self.mock_repo.get_skill_path.return_value = None  # No path found
        
        # Call service method
        result = self.skill_service.get_skill_path(source_id, target_id)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('no path', result['error'].lower())
        
        # Verify repo methods were called
        self.mock_repo.get_skill.assert_any_call(source_id)
        self.mock_repo.get_skill.assert_any_call(target_id)
        self.mock_repo.get_skill_path.assert_called_once_with(source_id, target_id)
    
    def test_get_skill_path_error(self):
        """Test handling of exceptions in get_skill_path."""
        # Set up mock to raise exception
        self.mock_repo.get_skill.side_effect = Exception("Test error")
        
        # Call service method
        result = self.skill_service.get_skill_path('skill_1', 'skill_3')
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('error finding skill path', result['error'].lower())
    
    def test_get_skill_graph_success(self):
        """Test getting a skill graph successfully."""
        skill_id = 'skill_1'
        
        # Sample graph data
        graph_data = {
            'nodes': [{'id': 'skill_1', 'name': 'Python'}, {'id': 'skill_2', 'name': 'JavaScript'}],
            'edges': [{'source': 'skill_1', 'target': 'skill_2', 'type': 'RELATED_TO'}]
        }
        
        # Set up mocks
        self.mock_repo.get_skill.return_value = self.sample_skills[0]
        self.mock_repo.get_skill_graph.return_value = graph_data
        
        # Call service method
        result = self.skill_service.get_skill_graph(skill_id)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['graph'], graph_data)
        
        # Verify repo methods were called
        self.mock_repo.get_skill.assert_called_once_with(skill_id)
        self.mock_repo.get_skill_graph.assert_called_once_with(skill_id)
    
    def test_get_skill_graph_not_found(self):
        """Test getting a skill graph for a non-existent skill."""
        skill_id = 'nonexistent_skill'
        
        # Set up mocks
        self.mock_repo.get_skill.return_value = None
        
        # Call service method
        result = self.skill_service.get_skill_graph(skill_id)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('not found', result['error'].lower())
        
        # Verify repo methods were called
        self.mock_repo.get_skill.assert_called_once_with(skill_id)
        self.mock_repo.get_skill_graph.assert_not_called()
    
    def test_get_skill_graph_error(self):
        """Test handling of exceptions in get_skill_graph."""
        skill_id = 'skill_1'
        
        # Set up mock to raise exception
        self.mock_repo.get_skill.return_value = self.sample_skills[0]
        self.mock_repo.get_skill_graph.side_effect = Exception("Test error")
        
        # Call service method
        result = self.skill_service.get_skill_graph(skill_id)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('error generating skill graph', result['error'].lower())
    
    def test_get_skills_network_success(self):
        """Test getting a skills network successfully."""
        # Sample network data
        network_data = {
            'nodes': [
                {'id': 'skill_1', 'name': 'Python'}, 
                {'id': 'skill_2', 'name': 'JavaScript'}
            ],
            'edges': [
                {'source': 'skill_1', 'target': 'skill_2', 'type': 'RELATED_TO'}
            ]
        }
        
        # Set up mock
        self.mock_repo.get_skills_network.return_value = network_data
        
        # Call service method
        result = self.skill_service.get_skills_network(limit=50)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['network'], network_data)
        
        # Verify repo method was called
        self.mock_repo.get_skills_network.assert_called_once_with(50)
    
    def test_get_skills_network_error(self):
        """Test handling of exceptions in get_skills_network."""
        # Set up mock to raise exception
        self.mock_repo.get_skills_network.side_effect = Exception("Test error")
        
        # Call service method
        result = self.skill_service.get_skills_network()
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('error generating skills network', result['error'].lower())
    
    def test_recommend_skills_for_job_success(self):
        """Test recommending skills for a job successfully."""
        resume_id = 'resume_123'
        job_id = 'job_456'
        
        # Sample recommendations
        recommendations = [
            {'skill_id': 'skill_3', 'name': 'SQL', 'relevance': 0.9},
            {'skill_id': 'skill_4', 'name': 'AWS', 'relevance': 0.8}
        ]
        
        # Set up mock
        self.mock_repo.recommend_skills_for_job.return_value = recommendations
        
        # Call service method
        result = self.skill_service.recommend_skills_for_job(resume_id, job_id)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['recommendations'], recommendations)
        
        # Verify repo method was called
        self.mock_repo.recommend_skills_for_job.assert_called_once_with(resume_id, job_id)
    
    def test_recommend_skills_for_job_error(self):
        """Test handling of exceptions in recommend_skills_for_job."""
        resume_id = 'resume_123'
        job_id = 'job_456'
        
        # Set up mock to raise exception
        self.mock_repo.recommend_skills_for_job.side_effect = Exception("Test error")
        
        # Call service method
        result = self.skill_service.recommend_skills_for_job(resume_id, job_id)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('error generating skill recommendations', result['error'].lower())
    
    def test_find_skills_error(self):
        """Test handling of exceptions in find_skills."""
        # Set up mock to raise exception
        self.mock_repo.find_skills.side_effect = Exception("Test error")
        
        # Call service method
        result = self.skill_service.find_skills()
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('error finding skills', result['error'].lower())
    
    def test_create_skill_error(self):
        """Test handling of exceptions in create_skill."""
        # Set up mock to raise exception
        self.mock_repo.add_skill.side_effect = Exception("Test error")
        
        # Call service method
        result = self.skill_service.create_skill(self.new_skill_data)
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('error creating skill', result['error'].lower())
    
    def test_validate_skill_data_update(self):
        """Test validation of skill data for updates."""
        # For updates, no fields are required
        update_data = {}
        
        # Call internal validation method directly
        result = self.skill_service._validate_skill_data(update_data, is_update=True)
        
        # Assertions
        self.assertTrue(result['valid'])
    
    def test_prepare_skill_data_with_update(self):
        """Test preparation of skill data for updates."""
        skill_id = 'skill_1'
        update_data = {'name': 'Updated Skill'}
        
        # Get the current time before calling the method
        now = datetime.datetime.now()
        
        # Call internal prepare method directly
        result = self.skill_service._prepare_skill_data(update_data, skill_id, is_update=True)
        
        # Assertions
        self.assertEqual(result['skill_id'], skill_id)
        self.assertEqual(result['name'], 'Updated Skill')
        self.assertNotIn('created_at', result)  # Should not add created_at for updates
        self.assertIn('updated_at', result)  # Should add updated_at
        
        # Convert the updated_at to datetime for comparison
        updated_at = datetime.datetime.fromisoformat(result['updated_at'])
        
        # Verify the timestamp is recent (within 2 seconds)
        self.assertLess((datetime.datetime.now() - updated_at).total_seconds(), 2)
    
    def test_prepare_skill_data_new_skill(self):
        """Test preparation of skill data for new skills."""
        skill_id = 'skill_new'
        new_data = {'name': 'New Skill'}
        
        # Get the current time before calling the method
        now = datetime.datetime.now()
        
        # Call internal prepare method directly
        result = self.skill_service._prepare_skill_data(new_data, skill_id, is_update=False)
        
        # Assertions
        self.assertEqual(result['skill_id'], skill_id)
        self.assertEqual(result['name'], 'New Skill')
        self.assertIn('created_at', result)  # Should add created_at for new skills
        self.assertIn('updated_at', result)  # Should add updated_at
        
        # Convert the timestamps to datetime for comparison
        created_at = datetime.datetime.fromisoformat(result['created_at'])
        updated_at = datetime.datetime.fromisoformat(result['updated_at'])
        
        # Verify the timestamps are recent (within 2 seconds)
        self.assertLess((datetime.datetime.now() - created_at).total_seconds(), 2)
        self.assertLess((datetime.datetime.now() - updated_at).total_seconds(), 2)
    
    def test_get_skill_error(self):
        """Test handling of exceptions in get_skill."""
        # Set up mock to raise exception
        self.mock_repo.get_skill.side_effect = Exception("Test error")
        
        # Call service method
        result = self.skill_service.get_skill('skill_1')
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('error retrieving skill', result['error'].lower())
    
    def test_validate_skill_data_missing_field(self):
        """Test validation with specific missing field."""
        # Test with each required field missing
        invalid_skill = {'category': 'Test', 'description': 'Test desc'}  # Missing name
        
        # Call validation method
        result = self.skill_service._validate_skill_data(invalid_skill)
        
        # Assertions
        self.assertFalse(result['valid'])
        self.assertEqual(result['error'], "Missing required field: name")


if __name__ == '__main__':
    unittest.main() 