"""
Integration tests for the Talent Matcher application

This module tests the integration of the Flask application with its routes and services.
"""

import unittest
from src.backend.app import create_app
from src.backend.services.graph_service import GraphService


class TestAppIntegration(unittest.TestCase):
    """Test the integration of the Flask application"""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment once before all tests"""
        # Create a test app
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        
        # Create a test client
        cls.client = cls.app.test_client()
        
        # Get the graph service instance
        cls.graph_service = GraphService.get_instance()

    def test_app_health_check(self):
        """Test the API health check endpoint"""
        with self.app.app_context():
            response = self.client.get('/')
            self.assertEqual(200, response.status_code)
            
            data = response.get_json()
            self.assertEqual("Talent Matcher API", data["name"])
            self.assertEqual("running", data["status"])
            self.assertIn("version", data)
    
    def test_app_route_initialization(self):
        """Test that all routes are correctly initialized"""
        # Get all the routes registered in the app
        rules = [rule.rule for rule in self.app.url_map.iter_rules()]
        
        # Check that essential routes exist
        essential_routes = [
            '/',  # Health check
            '/api/auth/login',
            '/api/auth/register',
            '/api/jobs',
            '/api/candidates',
            '/api/skills'
        ]
        
        for route in essential_routes:
            self.assertIn(route, rules, f"Essential route {route} is missing")
        
        # Count routes by type
        auth_routes = [r for r in rules if r.startswith('/api/auth')]
        job_routes = [r for r in rules if r.startswith('/api/jobs')]
        candidate_routes = [r for r in rules if r.startswith('/api/candidates')]
        skill_routes = [r for r in rules if r.startswith('/api/skills')]
        
        # Ensure we have multiple routes for each major feature
        self.assertGreater(len(auth_routes), 1, "Insufficient auth routes")
        self.assertGreater(len(job_routes), 1, "Insufficient job routes")
        self.assertGreater(len(candidate_routes), 1, "Insufficient candidate routes")
        self.assertGreater(len(skill_routes), 1, "Insufficient skill routes")
    
    def test_invalid_routes(self):
        """Test that invalid routes return 404"""
        with self.app.app_context():
            response = self.client.get('/nonexistent-route')
            self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main() 