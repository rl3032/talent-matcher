#!/usr/bin/env python
"""
Test script for the Talent Matcher Backend API
This test ensures the backend API continues to function correctly after frontend removal.
"""

import pytest
import json
from src.knowledge_graph.model import KnowledgeGraph
from src.knowledge_graph.matcher import KnowledgeGraphMatcher

def test_api_endpoints(api_client):
    """Test that all API endpoints are working correctly."""
    
    # Test 1: Get all jobs
    response = api_client.get('/api/jobs')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'jobs' in data
    assert isinstance(data['jobs'], list)
    if len(data['jobs']) > 0:
        assert 'title' in data['jobs'][0]
        assert 'company' in data['jobs'][0]
        assert 'job_id' in data['jobs'][0]
        # Store a job_id for later tests
        job_id = data['jobs'][0]['job_id']
    
    # Test 2: Get all candidates
    response = api_client.get('/api/candidates')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'candidates' in data
    assert isinstance(data['candidates'], list)
    if len(data['candidates']) > 0:
        assert 'name' in data['candidates'][0]
        assert 'resume_id' in data['candidates'][0]
        # Store a resume_id for later tests
        resume_id = data['candidates'][0]['resume_id']
    
    # Test 3: Get all skills
    response = api_client.get('/api/skills')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'skills' in data
    assert isinstance(data['skills'], list)
    
    # Skip the remaining tests if we don't have both a job and candidate
    if 'job_id' not in locals() or 'resume_id' not in locals():
        return
    
    # Test 4: Get job details by ID
    response = api_client.get(f'/api/jobs/{job_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'job' in data
    assert data['job']['job_id'] == job_id
    
    # Test 5: Get candidate details by ID
    response = api_client.get(f'/api/candidates/{resume_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'candidate' in data
    assert data['candidate']['resume_id'] == resume_id
    
    # Test 6: Get job matches for a candidate
    response = api_client.get(f'/api/candidates/{resume_id}/jobs')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'matches' in data
    assert isinstance(data['matches'], list)
    
    # Test 7: Get candidate matches for a job
    response = api_client.get(f'/api/jobs/{job_id}/candidates')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'matches' in data
    assert isinstance(data['matches'], list)
    
    # Test 8: Get skill gap analysis
    response = api_client.get(f'/api/candidates/{resume_id}/jobs/{job_id}/skill-gap')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'matching_skills' in data
    assert 'missing_skills' in data
    assert 'exceeding_skills' in data
    
def test_knowledge_graph_matcher(kg_connection):
    """Test that the knowledge graph matcher works correctly."""
    # Create a matcher
    matcher = KnowledgeGraphMatcher(kg_connection)
    
    # Get a job ID from the knowledge graph
    with kg_connection.driver.session() as session:
        result = session.run("MATCH (j:Job) RETURN j.job_id as job_id LIMIT 1")
        records = list(result)
        if len(records) > 0:
            job_id = records[0]['job_id']
            
            # Test matching job to candidates
            matches = matcher.match_job_to_candidates(job_id, limit=5)
            assert isinstance(matches, list)
            if len(matches) > 0:
                assert 'resume_id' in matches[0]
                assert 'match_percentage' in matches[0]
    
    # Get a candidate ID from the knowledge graph
    with kg_connection.driver.session() as session:
        result = session.run("MATCH (c:Candidate) RETURN c.resume_id as resume_id LIMIT 1")
        records = list(result)
        if len(records) > 0:
            resume_id = records[0]['resume_id']
            
            # Test matching candidate to jobs
            matches = matcher.match_candidate_to_jobs(resume_id, limit=5)
            assert isinstance(matches, list)
            if len(matches) > 0:
                assert 'job_id' in matches[0]
                assert 'match_percentage' in matches[0] 