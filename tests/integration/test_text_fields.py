#!/usr/bin/env python
"""
Test Text Fields Script for Talent Matcher
This script verifies that text fields have been properly loaded into the Neo4j database.
"""

import os
from dotenv import load_dotenv
from src.knowledge_graph.model import KnowledgeGraph
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

def test_text_fields():
    """Test if text fields were properly loaded into the database."""
    print(f"Connecting to Neo4j at {NEO4J_URI}...")
    kg = KnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    kg.connect()
    
    print("\nVerifying text fields were loaded correctly...")
    
    with kg.driver.session() as session:
        # Check job text fields
        job_result = session.run("""
            MATCH (j:Job) 
            WHERE j.description IS NOT NULL OR j.responsibilities IS NOT NULL OR j.qualifications IS NOT NULL
            RETURN count(j) as count
        """).single()
        
        job_text_count = job_result["count"] if job_result else 0
        print(f"Jobs with text fields: {job_text_count}")
        
        # Check candidate text fields
        candidate_result = session.run("""
            MATCH (c:Candidate) 
            WHERE c.summary IS NOT NULL OR c.experience IS NOT NULL OR c.education IS NOT NULL
            RETURN count(c) as count
        """).single()
        
        candidate_text_count = candidate_result["count"] if candidate_result else 0
        print(f"Candidates with text fields: {candidate_text_count}")
        
        # Sample a job to verify text content
        job_sample = session.run("""
            MATCH (j:Job) 
            WHERE j.description IS NOT NULL
            RETURN j.job_id, j.description, j.responsibilities, j.qualifications
            LIMIT 1
        """).single()
        
        if job_sample:
            print(f"\nSample job ({job_sample['j.job_id']}) text fields:")
            print(f"Description: {job_sample['j.description'][:100]}...")
            print(f"Responsibilities: {job_sample['j.responsibilities'][:100]}...")
            print(f"Qualifications: {job_sample['j.qualifications'][:100]}...")
        
        # Sample a candidate to verify text content
        candidate_sample = session.run("""
            MATCH (c:Candidate) 
            WHERE c.summary IS NOT NULL
            RETURN c.resume_id, c.summary, c.experience, c.education
            LIMIT 1
        """).single()
        
        if candidate_sample:
            print(f"\nSample candidate ({candidate_sample['c.resume_id']}) text fields:")
            print(f"Summary: {candidate_sample['c.summary'][:100]}...")
            print(f"Experience: {candidate_sample['c.experience'][:100]}...")
            print(f"Education: {candidate_sample['c.education'][:100]}...")
    
    print("\nTest complete!")
    kg.close()

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    test_text_fields() 