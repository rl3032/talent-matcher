"""
Unit tests for skill routes.
"""
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys
from flask import Flask
from dataclasses import dataclass
from flask_jwt_extended import JWTManager

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.routes.skill_routes import init_routes, skill_bp
from src.backend.services.skill_service import SkillService
from src.backend.models.skill_model import Skill

# Create a mock user class for testing
@dataclass
class MockUser:
    email: str = "admin@example.com"
    is_hiring_manager: bool = False
    is_admin: bool = True
    role: str = "admin"


class TestSkillRoutes(unittest.TestCase):
    """Test case for the skill routes."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test Flask app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        
        # Configure JWT settings
        self.app.config['JWT_SECRET_KEY'] = 'test_secret_key'
        self.app.config['JWT_TOKEN_LOCATION'] = ['headers']
        self.app.config['JWT_HEADER_NAME'] = 'Authorization'
        self.app.config['JWT_HEADER_TYPE'] = 'Bearer'
        
        # Initialize JWT extension
        self.jwt = JWTManager(self.app)
        
        # Create a test client
        self.client = self.app.test_client()
        
        # Create an app context for the tests
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create mock services
        self.mock_skill_service = MagicMock(spec=SkillService)
        
        # Now that we have an app context, set up the routes
        init_routes(self.app, self.mock_skill_service)
        
        # Start patching
        # Override the jwt_required decorator to be a no-op
        self.jwt_patcher = patch('flask_jwt_extended.view_decorators.verify_jwt_in_request')
        self.mock_verify_jwt = self.jwt_patcher.start()
        
        # Mock get_current_user function to return our test user
        self.get_user_patcher = patch('flask_jwt_extended.utils.get_current_user')
        self.mock_get_current_user = self.get_user_patcher.start()
        self.mock_get_current_user.return_value = MockUser()
        
        # Create sample data
        self.sample_skill = Skill(
            skill_id='skill_1',
            name="Python",
            category="Programming",
            description="Python programming language"
        )
        
        self.sample_skills = [
            self.sample_skill.to_dict(),
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
            }
        ]
        
        # New skill data for creation tests
        self.new_skill_data = {
            'name': 'React',
            'category': 'Frontend',
            'description': 'React JavaScript library'
        }
        
        # Updated skill data for update tests
        self.updated_skill_data = {
            'name': 'Python 3',
            'category': 'Programming',
            'description': 'Updated Python programming language'
        }

    def tearDown(self):
        """Clean up test fixtures."""
        # Stop all patches
        self.jwt_patcher.stop()
        self.get_user_patcher.stop()
        self.app_context.pop()

    def test_get_all_skills(self):
        """Test getting all skills."""
        # Set up mock service response
        result = {
            'success': True,
            'skills': self.sample_skills
        }
        self.mock_skill_service.find_skills.return_value = result
        
        # Make request to the endpoint
        response = self.client.get('/api/skills')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['skills']), 3)
        
        # Verify service was called
        self.mock_skill_service.find_skills.assert_called_once()

    def test_get_all_skills_with_filters(self):
        """Test getting skills with filters."""
        # Set up mock service response
        result = {
            'success': True,
            'skills': [self.sample_skill.to_dict()]
        }
        self.mock_skill_service.find_skills.return_value = result
        
        # Make request with query parameters
        response = self.client.get('/api/skills?name=Python&category=Programming&limit=10&offset=0')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        
        # Verify service was called with correct filters
        expected_filters = {'name': 'Python', 'category': 'Programming'}
        self.mock_skill_service.find_skills.assert_called_once_with(expected_filters, 10, 0)

    def test_get_all_skills_failure(self):
        """Test getting all skills with service error."""
        # Set up mock service response
        result = {
            'success': False,
            'error': 'Database error'
        }
        self.mock_skill_service.find_skills.return_value = result
        
        # Make request
        response = self.client.get('/api/skills')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Database error')

    def test_get_skill_by_id_success(self):
        """Test getting a skill by ID successfully."""
        skill_id = 'skill_1'
        
        # Set up mock service response
        result = {
            'success': True,
            'skill': self.sample_skill.to_dict()
        }
        self.mock_skill_service.get_skill.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/skills/{skill_id}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['skill']['skill_id'], skill_id)
        self.assertEqual(data['skill']['name'], 'Python')
        
        # Verify service was called with correct ID
        self.mock_skill_service.get_skill.assert_called_once_with(skill_id)

    def test_get_skill_by_id_not_found(self):
        """Test getting a skill by ID when it doesn't exist."""
        skill_id = 'nonexistent'
        
        # Set up mock service response for not found
        result = {
            'success': False,
            'error': 'Skill not found'
        }
        self.mock_skill_service.get_skill.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/skills/{skill_id}')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Skill not found')
        
        # Verify service was called with correct ID
        self.mock_skill_service.get_skill.assert_called_once_with(skill_id)

    def test_create_skill_success(self):
        """Test creating a new skill successfully."""
        # Set up mock service response
        created_skill = {**self.new_skill_data, 'skill_id': 'skill_4'}
        result = {
            'success': True,
            'skill_id': 'skill_4'
        }
        self.mock_skill_service.create_skill.return_value = result
        
        # Make request to the endpoint
        response = self.client.post(
            '/api/skills/create',
            data=json.dumps(self.new_skill_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['skill_id'], 'skill_4')
        self.assertEqual(data['message'], 'Skill created successfully')
        
        # Verify service was called with correct data
        self.mock_skill_service.create_skill.assert_called_once_with(self.new_skill_data)

    def test_create_skill_not_admin(self):
        """Test creating a skill without admin privileges."""
        # Set the user as non-admin
        self.mock_get_current_user.return_value = MockUser(is_admin=False, role='user')
        
        # Make request to the endpoint
        response = self.client.post(
            '/api/skills/create',
            data=json.dumps(self.new_skill_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Only administrators can create skills')
        
        # Verify service was not called
        self.mock_skill_service.create_skill.assert_not_called()

    def test_create_skill_validation_error(self):
        """Test creating a skill with validation errors."""
        # Invalid skill data
        invalid_skill = {'name': ''}  # Empty name
        
        # Set up mock service response
        result = {
            'success': False,
            'error': 'Missing required field: name'
        }
        self.mock_skill_service.create_skill.return_value = result
        
        # Make request to the endpoint
        response = self.client.post(
            '/api/skills/create',
            data=json.dumps(invalid_skill),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Missing required field: name')
        
        # Verify service was called with the invalid data
        self.mock_skill_service.create_skill.assert_called_once_with(invalid_skill)

    def test_update_skill_success(self):
        """Test updating an existing skill successfully."""
        skill_id = 'skill_1'
        
        # Set up mock service response
        updated_skill = {**self.updated_skill_data, 'skill_id': skill_id}
        result = {
            'success': True,
            'skill_id': skill_id
        }
        self.mock_skill_service.update_skill.return_value = result
        
        # Make request to the endpoint
        response = self.client.put(
            f'/api/skills/{skill_id}',
            data=json.dumps(self.updated_skill_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['skill_id'], skill_id)
        self.assertEqual(data['message'], 'Skill updated successfully')
        
        # Verify service was called with correct data
        self.mock_skill_service.update_skill.assert_called_once_with(skill_id, self.updated_skill_data)

    def test_update_skill_not_admin(self):
        """Test updating a skill without admin privileges."""
        # Set the user as non-admin
        self.mock_get_current_user.return_value = MockUser(is_admin=False, role='user')
        
        # Make request to the endpoint
        response = self.client.put(
            '/api/skills/skill_1',
            data=json.dumps(self.updated_skill_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Only administrators can update skills')
        
        # Verify service was not called
        self.mock_skill_service.update_skill.assert_not_called()

    def test_update_skill_not_found(self):
        """Test updating a skill that doesn't exist."""
        skill_id = 'nonexistent'
        
        # Set up mock service response for not found
        result = {
            'success': False,
            'error': 'Skill not found'
        }
        self.mock_skill_service.update_skill.return_value = result
        
        # Make request to the endpoint
        response = self.client.put(
            f'/api/skills/{skill_id}',
            data=json.dumps(self.updated_skill_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)  # Note: Routes return 400, not 404 for this
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Skill not found')
        
        # Verify service was called with correct data
        self.mock_skill_service.update_skill.assert_called_once_with(skill_id, self.updated_skill_data)

    def test_delete_skill_success(self):
        """Test deleting a skill successfully."""
        skill_id = 'skill_1'
        
        # Set up mock service response
        result = {
            'success': True,
            'message': 'Skill deleted successfully'
        }
        self.mock_skill_service.delete_skill.return_value = result
        
        # Make request to the endpoint
        response = self.client.delete(
            f'/api/skills/{skill_id}',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Skill deleted successfully')
        
        # Verify service was called with correct ID
        self.mock_skill_service.delete_skill.assert_called_once_with(skill_id)

    def test_delete_skill_not_admin(self):
        """Test deleting a skill without admin privileges."""
        # Set the user as non-admin
        self.mock_get_current_user.return_value = MockUser(is_admin=False, role='user')
        
        # Make request to the endpoint
        response = self.client.delete(
            '/api/skills/skill_1',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Only administrators can delete skills')
        
        # Verify service was not called
        self.mock_skill_service.delete_skill.assert_not_called()

    def test_delete_skill_not_found(self):
        """Test deleting a skill that doesn't exist."""
        skill_id = 'nonexistent'
        
        # Set up mock service response for not found
        result = {
            'success': False,
            'error': 'Skill not found'
        }
        self.mock_skill_service.delete_skill.return_value = result
        
        # Make request to the endpoint
        response = self.client.delete(
            f'/api/skills/{skill_id}',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)  # Routes return 400, not 404 for this
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Skill not found')
        
        # Verify service was called with correct ID
        self.mock_skill_service.delete_skill.assert_called_once_with(skill_id)

    def test_get_related_skills(self):
        """Test getting related skills."""
        skill_id = 'skill_1'
        
        # Set up mock service response
        related_skills = [
            {
                'skill_id': 'skill_2',
                'name': 'JavaScript',
                'relationship_type': 'RELATED_TO',
                'weight': 0.8
            },
            {
                'skill_id': 'skill_3',
                'name': 'Django',
                'relationship_type': 'USED_WITH',
                'weight': 0.9
            }
        ]
        
        result = {
            'success': True,
            'related_skills': related_skills
        }
        self.mock_skill_service.get_related_skills.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/skills/{skill_id}/related')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['related_skills']), 2)
        
        # Verify service was called with correct skill ID
        self.mock_skill_service.get_related_skills.assert_called_once_with(skill_id)

    def test_get_related_skills_not_found(self):
        """Test getting related skills for a skill that doesn't exist."""
        skill_id = 'nonexistent'
        
        # Set up mock service response
        result = {
            'success': False,
            'error': 'Skill not found'
        }
        self.mock_skill_service.get_related_skills.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/skills/{skill_id}/related')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Skill not found')
        
        # Verify service was called with correct skill ID
        self.mock_skill_service.get_related_skills.assert_called_once_with(skill_id)

    def test_get_skill_path(self):
        """Test getting the path between two skills."""
        source_id = 'skill_1'
        target_id = 'skill_3'
        
        # Set up mock service response
        path_data = [
            {'skill_id': 'skill_1', 'name': 'Python'},
            {'skill_id': 'skill_2', 'name': 'JavaScript'},
            {'skill_id': 'skill_3', 'name': 'SQL'}
        ]
        
        result = {
            'success': True,
            'path': path_data
        }
        self.mock_skill_service.get_skill_path.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/skills/path?source={source_id}&target={target_id}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['path']), 3)
        
        # Verify service was called with correct IDs
        self.mock_skill_service.get_skill_path.assert_called_once_with(source_id, target_id)

    def test_get_skill_path_missing_params(self):
        """Test getting the path with missing parameters."""
        # Make request to the endpoint without source
        response = self.client.get('/api/skills/path?target=skill_3')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Both source and target skill IDs are required')
        
        # Service should not be called
        self.mock_skill_service.get_skill_path.assert_not_called()

    def test_get_skill_path_not_found(self):
        """Test getting the path when service returns an error."""
        # Set up mock service response
        result = {
            'success': False,
            'error': 'No path found between skills'
        }
        self.mock_skill_service.get_skill_path.return_value = result
        
        # Make request to the endpoint
        response = self.client.get('/api/skills/path?source=skill_1&target=nonexistent')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'No path found between skills')

    def test_get_skill_graph(self):
        """Test getting a skill graph for visualization."""
        skill_id = 'skill_1'
        
        # Set up mock service response
        graph_data = {
            'nodes': [
                {'id': 'skill_1', 'label': 'Python', 'category': 'Programming'},
                {'id': 'skill_2', 'label': 'Django', 'category': 'Framework'}
            ],
            'edges': [
                {'source': 'skill_1', 'target': 'skill_2', 'type': 'USED_WITH'}
            ]
        }
        
        result = {
            'success': True,
            'graph': graph_data
        }
        self.mock_skill_service.get_skill_graph.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/skills/{skill_id}/graph')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('graph', data)
        self.assertEqual(len(data['graph']['nodes']), 2)
        self.assertEqual(len(data['graph']['edges']), 1)
        
        # Verify service was called with correct ID
        self.mock_skill_service.get_skill_graph.assert_called_once_with(skill_id)

    def test_get_skill_graph_not_found(self):
        """Test getting a graph for a skill that doesn't exist."""
        skill_id = 'nonexistent'
        
        # Set up mock service response
        result = {
            'success': False,
            'error': 'Skill not found'
        }
        self.mock_skill_service.get_skill_graph.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/skills/{skill_id}/graph')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Skill not found')
        
        # Verify service was called with correct ID
        self.mock_skill_service.get_skill_graph.assert_called_once_with(skill_id)

    def test_get_skills_network(self):
        """Test getting a network of skills for visualization."""
        # Set up mock service response
        network_data = {
            'nodes': [
                {'id': 'skill_1', 'label': 'Python', 'category': 'Programming'},
                {'id': 'skill_2', 'label': 'JavaScript', 'category': 'Programming'},
                {'id': 'skill_3', 'label': 'SQL', 'category': 'Database'}
            ],
            'edges': [
                {'source': 'skill_1', 'target': 'skill_2', 'type': 'RELATED_TO'},
                {'source': 'skill_2', 'target': 'skill_3', 'type': 'USED_WITH'}
            ]
        }
        
        result = {
            'success': True,
            'network': network_data
        }
        self.mock_skill_service.get_skills_network.return_value = result
        
        # Make request to the endpoint
        response = self.client.get('/api/skills/network?limit=50')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('network', data)
        self.assertEqual(len(data['network']['nodes']), 3)
        self.assertEqual(len(data['network']['edges']), 2)
        
        # Verify service was called with correct limit
        self.mock_skill_service.get_skills_network.assert_called_once_with(50)

    def test_get_skills_network_error(self):
        """Test getting a network of skills with an error."""
        # Set up mock service response
        result = {
            'success': False,
            'error': 'Error retrieving network data'
        }
        self.mock_skill_service.get_skills_network.return_value = result
        
        # Make request to the endpoint
        response = self.client.get('/api/skills/network')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Error retrieving network data')

    def test_get_skill_recommendations(self):
        """Test getting skill recommendations for a candidate targeting a job."""
        resume_id = 'resume_123'
        job_id = 'job_456'
        
        # Set up mock service response
        recommendations = [
            {'skill_id': 'skill_1', 'name': 'Python', 'score': 0.9},
            {'skill_id': 'skill_2', 'name': 'JavaScript', 'score': 0.8}
        ]
        
        result = {
            'success': True,
            'recommendations': recommendations
        }
        self.mock_skill_service.recommend_skills_for_job.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/skills/recommendations/{resume_id}/{job_id}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['recommendations']), 2)
        
        # Verify service was called with correct parameters
        self.mock_skill_service.recommend_skills_for_job.assert_called_once_with(resume_id, job_id)

    def test_get_skill_recommendations_error(self):
        """Test getting skill recommendations when there's an error."""
        resume_id = 'resume_123'
        job_id = 'nonexistent'
        
        # Set up mock service response
        result = {
            'success': False,
            'error': 'Job not found'
        }
        self.mock_skill_service.recommend_skills_for_job.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/skills/recommendations/{resume_id}/{job_id}')
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Job not found')

    def test_get_skill_graph_data(self):
        """Test getting graph data for a skill in the graph API."""
        skill_id = 'skill_1'
        
        # Set up mock service response
        graph_data = {
            'nodes': [
                {'id': 'skill_1', 'label': 'Python', 'category': 'Programming'},
                {'id': 'skill_2', 'label': 'Django', 'category': 'Framework'}
            ],
            'edges': [
                {'source': 'skill_1', 'target': 'skill_2', 'type': 'USED_WITH'}
            ]
        }
        
        result = {
            'success': True,
            'graph': graph_data
        }
        self.mock_skill_service.get_skill_graph.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/graph/skill/{skill_id}')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['nodes']), 2)
        self.assertEqual(len(data['edges']), 1)
        
        # Verify service was called with correct ID
        self.mock_skill_service.get_skill_graph.assert_called_once_with(skill_id)

    def test_get_skill_graph_data_not_found(self):
        """Test getting graph data for a non-existent skill."""
        skill_id = 'nonexistent'
        
        # Set up mock service response
        result = {
            'success': False,
            'error': 'Skill not found'
        }
        self.mock_skill_service.get_skill_graph.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/graph/skill/{skill_id}')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Skill not found')

    def test_get_skill_graph_data_empty(self):
        """Test getting graph data with empty results."""
        skill_id = 'skill_1'
        
        # Set up mock service response with empty data
        result = {
            'success': True,
            'graph': {}  # Empty graph
        }
        self.mock_skill_service.get_skill_graph.return_value = result
        
        # Make request to the endpoint
        response = self.client.get(f'/api/graph/skill/{skill_id}')
        
        # Check response - should still return valid format
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('nodes', data)
        self.assertIn('edges', data)
        self.assertEqual(len(data['nodes']), 0)
        self.assertEqual(len(data['edges']), 0)

    def test_get_skill_graph_data_exception(self):
        """Test getting graph data when service throws an exception."""
        skill_id = 'skill_1'
        
        # Set up mock service to raise an exception
        self.mock_skill_service.get_skill_graph.side_effect = Exception("Unexpected error")
        
        # Make request to the endpoint
        response = self.client.get(f'/api/graph/skill/{skill_id}')
        
        # Check response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Failed to retrieve skill graph data')
        self.assertIn('details', data)

    def test_get_skills_network_data(self):
        """Test getting network data for the graph API."""
        # Set up mock service response
        network_data = {
            'nodes': [
                {'id': 'skill_1', 'label': 'Python', 'category': 'Programming'},
                {'id': 'skill_2', 'label': 'JavaScript', 'category': 'Programming'}
            ],
            'edges': [
                {'source': 'skill_1', 'target': 'skill_2', 'type': 'RELATED_TO'}
            ]
        }
        
        result = {
            'success': True,
            'network': network_data
        }
        self.mock_skill_service.get_skills_network.return_value = result
        
        # Make request to the endpoint
        response = self.client.get('/api/graph/skills-network?limit=50')
        
        # Check response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['nodes']), 2)
        self.assertEqual(len(data['edges']), 1)
        
        # Verify service was called with correct limit
        self.mock_skill_service.get_skills_network.assert_called_once_with(50)

    def test_get_skills_network_data_not_found(self):
        """Test getting network data with an error."""
        # Set up mock service response
        result = {
            'success': False,
            'error': 'Error building network'
        }
        self.mock_skill_service.get_skills_network.return_value = result
        
        # Make request to the endpoint
        response = self.client.get('/api/graph/skills-network')
        
        # Check response
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Error building network')

    def test_get_skills_network_data_empty(self):
        """Test getting network data with empty results."""
        # Set up mock service response with empty data
        result = {
            'success': True,
            'network': {}  # Empty network
        }
        self.mock_skill_service.get_skills_network.return_value = result
        
        # Make request to the endpoint
        response = self.client.get('/api/graph/skills-network')
        
        # Check response - should still return valid format
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('nodes', data)
        self.assertIn('edges', data)
        self.assertEqual(len(data['nodes']), 0)
        self.assertEqual(len(data['edges']), 0)

    def test_get_skills_network_data_exception(self):
        """Test getting network data when service throws an exception."""
        # Set up mock service to raise an exception
        self.mock_skill_service.get_skills_network.side_effect = Exception("Unexpected error")
        
        # Make request to the endpoint
        response = self.client.get('/api/graph/skills-network')
        
        # Check response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Failed to retrieve skills network data')
        self.assertIn('details', data)


if __name__ == '__main__':
    unittest.main() 