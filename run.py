#!/usr/bin/env python
"""
Central Run Script for Talent Matcher application
This script provides a single entry point to run the application in API mode or run tests.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

def main():
    """Main entry point for the Talent Matcher application."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run Talent Matcher in different modes')
    parser.add_argument('mode', choices=['api', 'test'], default='api', nargs='?',
                        help='Run mode: api or test')
    parser.add_argument('--port', type=int, help='Port to run on (overrides config)')
    parser.add_argument('--host', type=str, help='Host to bind to (overrides config)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Run in the selected mode
    if args.mode == 'api':
        # API only
        print("Starting Talent Matcher API...")
        from src.config import API_PORT, API_HOST
        from src.api.app import app
        
        port = args.port or API_PORT
        host = args.host or API_HOST
        debug = args.debug or True
        
        print(f"- API: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
        app.run(host=host, port=port, debug=debug)
        
    elif args.mode == 'test':
        # Run tests
        print("Running Talent Matcher tests...")
        import pytest
        sys.exit(pytest.main(['tests', '-v']))

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
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
    
    # Run the application
    main() 