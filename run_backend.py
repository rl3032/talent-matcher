#!/usr/bin/env python
"""
Run Script for the new Backend with layered architecture
"""

import os
import argparse
from dotenv import load_dotenv

def main():
    """Main entry point for the Talent Matcher backend."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run Talent Matcher Backend')
    parser.add_argument('--port', type=int, help='Port to run on (overrides config)')
    parser.add_argument('--host', type=str, help='Host to bind to (overrides config)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Import the app from the new backend
    from src.backend.app import create_app
    from src.backend.config import API_PORT, API_HOST
    
    app = create_app()
    
    port = args.port or API_PORT
    host = args.host or API_HOST
    debug = args.debug or True
    
    print(f"Starting Talent Matcher Backend...")
    print(f"- API: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    app.run(host=host, port=port, debug=debug)

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