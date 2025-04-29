"""
Configuration Module for Talent Matcher

This module contains configuration settings for the application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Neo4j database connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# API settings
API_PORT = int(os.getenv("API_PORT", 8000))
API_HOST = os.getenv("API_HOST", "0.0.0.0")

# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-dev-key")
JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", 24))

# Data settings
DATA_DIR = os.getenv("DATA_DIR", "data") 