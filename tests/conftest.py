"""
Pytest configuration file for Talent Matcher tests
This file contains fixtures and configuration for the pytest test suite.
"""

import os
import sys
import pytest
from dotenv import load_dotenv
from src.backend.services.graph_service import GraphService

# Load environment variables for testing
load_dotenv()

# Fixtures for testing with Neo4j
@pytest.fixture(scope="session")
def kg_connection():
    """Create a reusable knowledge graph connection for tests."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    # Create connection
    kg = GraphService(uri, user, password)
    kg.connect()
    
    # Return the connection for test use
    yield kg
    
    # Close the connection after tests complete
    kg.close()

# Fixtures for API testing
@pytest.fixture(scope="session")
def api_client():
    """Create a test client for the API."""
    from src.api.app import app
    with app.test_client() as client:
        yield client 