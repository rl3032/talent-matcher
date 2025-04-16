#!/usr/bin/env python
"""
Test script for the Talent Matcher API
"""

import requests
import json
import sys
from src.config import API_PORT, API_HOST

# Construct the base URL using the configuration
BASE_URL = f"http://{API_HOST if API_HOST != '0.0.0.0' else 'localhost'}:{API_PORT}/api"

def test_api():
    """Test various API endpoints and print the results."""
    
    print(f"Testing API at {BASE_URL}")
    
    # Test 1: Get all jobs
    print("\nTesting /api/jobs endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/jobs")
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Found {len(data['jobs'])} jobs")
            if len(data['jobs']) > 0:
                print(f"Example job: {data['jobs'][0]['title']} at {data['jobs'][0]['company']}")
        else:
            print(f"Error: Status code {response.status_code}")
    except Exception as e:
        print(f"Error connecting to API: {e}")
        sys.exit(1)
        
    # Test 2: Get all candidates
    print("\nTesting /api/candidates endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/candidates")
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Found {len(data['candidates'])} candidates")
            if len(data['candidates']) > 0:
                print(f"Example candidate: {data['candidates'][0]['name']} - {data['candidates'][0]['title']}")
                # Save a sample resume_id for further testing
                sample_resume_id = data['candidates'][0]['resume_id']
        else:
            print(f"Error: Status code {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Error connecting to API: {e}")
        sys.exit(1)
        
    # Test 3: Get matching jobs for a candidate
    if 'sample_resume_id' in locals():
        print(f"\nTesting /api/candidates/{sample_resume_id}/jobs endpoint...")
        try:
            response = requests.get(f"{BASE_URL}/candidates/{sample_resume_id}/jobs")
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Found {len(data['matches'])} matching jobs for candidate {sample_resume_id}")
                if len(data['matches']) > 0:
                    print(f"Top matching job: {data['matches'][0]['title']} with {data['matches'][0]['match_percentage']}% match")
                    # Save a sample job_id for further testing
                    sample_job_id = data['matches'][0]['job_id']
            else:
                print(f"Error: Status code {response.status_code}")
        except Exception as e:
            print(f"Error connecting to API: {e}")
    
    # Test 4: Get skill gap analysis if we have both candidate and job
    if 'sample_resume_id' in locals() and 'sample_job_id' in locals():
        print(f"\nTesting /api/candidates/{sample_resume_id}/jobs/{sample_job_id}/skill-gap endpoint...")
        try:
            response = requests.get(f"{BASE_URL}/candidates/{sample_resume_id}/jobs/{sample_job_id}/skill-gap")
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Found:")
                print(f"- {len(data['matching_skills'])} matching skills")
                print(f"- {len(data['missing_skills'])} missing skills")
                print(f"- {len(data['exceeding_skills'])} exceeding skills")
            else:
                print(f"Error: Status code {response.status_code}")
        except Exception as e:
            print(f"Error connecting to API: {e}")
    
    print("\nAPI testing completed!")

if __name__ == "__main__":
    test_api() 