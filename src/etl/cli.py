#!/usr/bin/env python
"""
Data Loading CLI for Talent Matcher

This module provides CLI functionality to run the ETL pipeline and load test data 
into the Neo4j database. Must be run from the project root directory.
"""

import os
import sys
from dotenv import load_dotenv

# Import the data loader
from src.etl.data_loader import initialize_knowledge_graph, ETLPipeline

def main():
    """Run the ETL pipeline to load data into the database."""
    # Load environment variables
    load_dotenv()
    
    # Make sure we're running from the project root
    if not os.path.exists(os.path.join(os.getcwd(), 'src')):
        print("Error: This script must be run from the project root directory")
        sys.exit(1)
        
    print("Initializing Knowledge Graph...")
    
    # Initialize the knowledge graph
    kg = initialize_knowledge_graph()
    
    # Create ETL pipeline
    etl = ETLPipeline(kg)
    
    # Run the pipeline with all data
    print("Loading data into Knowledge Graph...")
    success = etl.run_pipeline(
        clear_db=True,  # Clear existing data
        force=True,     # Skip confirmation prompts
        generate_embeddings=True  # Generate embeddings for enhanced matching
    )
    
    # Create test accounts
    if success:
        try:
            print("Creating test accounts...")
            kg.create_test_accounts()
            print("Test accounts created successfully")
        except Exception as e:
            print(f"Warning: Failed to create test accounts: {str(e)}")
    
    print(f"Data loading {'completed successfully' if success else 'failed'}")
    kg.close()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 