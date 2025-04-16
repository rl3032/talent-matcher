#!/usr/bin/env python
"""
Database Connection Test for Talent Matcher
This script tests the connection to the Neo4j database.
"""

import os
import argparse
from dotenv import load_dotenv
from neo4j import GraphDatabase

def test_connection(uri=None, user=None, password=None, verbose=True):
    """Test the connection to the Neo4j database."""
    # Load environment variables if not provided
    if not all([uri, user, password]):
        load_dotenv()
        uri = uri or os.getenv("NEO4J_URI")
        user = user or os.getenv("NEO4J_USER")
        password = password or os.getenv("NEO4J_PASSWORD")
    
    if verbose:
        print(f"Testing connection to Neo4j at {uri}...")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run("RETURN 1")
            result.single()  # Validate that we got a result
            if verbose:
                print("Successfully connected to Neo4j!")
            return True
    except Exception as e:
        if verbose:
            print(f"Failed to connect to Neo4j: {str(e)}")
        return False
    finally:
        driver.close()

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Test Neo4j database connection')
    parser.add_argument('--uri', help='Neo4j URI (default: from .env)')
    parser.add_argument('--user', help='Neo4j username (default: from .env)')
    parser.add_argument('--password', help='Neo4j password (default: from .env)')
    args = parser.parse_args()
    
    success = test_connection(args.uri, args.user, args.password)
    return 0 if success else 1

if __name__ == "__main__":
    exit(main()) 