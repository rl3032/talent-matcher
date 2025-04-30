#!/usr/bin/env python
"""
Backend CLI for Talent Matcher

This module provides CLI functionality to launch the backend server.
Must be run from the project root directory.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

def run_backend(port=None, host=None, debug=None):
    """Run the backend server."""
    # Load environment variables
    load_dotenv()
    
    # Make sure we're running from the project root
    if not os.path.exists(os.path.join(os.getcwd(), 'src')):
        print("Error: This script must be run from the project root directory")
        sys.exit(1)
    
    # Import the app from the backend
    from src.backend.app import create_app
    from src.backend.config import API_PORT, API_HOST
    
    app = create_app()
    
    port = port or API_PORT
    host = host or API_HOST
    debug = debug if debug is not None else True
    
    # Check Neo4j environment variables
    if not os.getenv("NEO4J_URI"):
        print("Warning: NEO4J_URI environment variable not set.")
        print("Using default: bolt://localhost:7687")
    
    if not os.getenv("NEO4J_USER"):
        print("Warning: NEO4J_USER environment variable not set.")
        print("Using default: neo4j")
    
    if not os.getenv("NEO4J_PASSWORD"):
        print("Warning: NEO4J_PASSWORD environment variable not set.")
        print("Using default: password")
    
    print(f"Starting Talent Matcher Backend...")
    print(f"- API: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    app.run(host=host, port=port, debug=debug)

def main():
    """CLI entry point for running the backend server."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run Talent Matcher Backend')
    parser.add_argument('--port', type=int, help='Port to run the backend on (overrides config)')
    parser.add_argument('--host', type=str, help='Host to bind the backend to (overrides config)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Run the backend
    run_backend(args.port, args.host, args.debug)
    return 0

if __name__ == "__main__":
    sys.exit(main()) 