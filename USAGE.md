# Talent Matcher Usage Guide

This guide provides instructions on how to use the Talent Matcher application, a knowledge graph-based hiring recommendation system.

## Overview

Talent Matcher uses Neo4j knowledge graph technology to create meaningful connections between skills, candidates, and job postings. This approach provides several advantages over traditional keyword matching:

1. **Contextual Skill Matching** - Understanding relationships between skills (e.g., React requires JavaScript)
2. **Skill Gap Analysis** - Identifying what skills a candidate needs to learn for a specific job
3. **Career Path Recommendations** - Suggesting optimal learning paths for career advancement

## Getting Started

### Prerequisites

- Python 3.8+
- Neo4j database (already set up)
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure your Neo4j database credentials in `.env`:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

## Using the Application

### Starting the API Server

Run the API server:

```
python run.py api
```

This will start the API on port 8000 (by default):

- API: http://localhost:8000/api

You can also use the start script:

```
./start.sh
```

### API Endpoints

The Talent Matcher system provides a comprehensive REST API for programmatic access:

#### Job Matching

- `GET /api/jobs/<job_id>/candidates` - Find candidates matching a job
- `GET /api/candidates/<resume_id>/jobs` - Find jobs matching a candidate
- `GET /api/candidates/<resume_id>/jobs/<job_id>/skill-gap` - Get skill gap analysis
- `GET /api/candidates/<resume_id>/jobs/<job_id>/recommendations` - Get skill recommendations

#### Skill Navigation

- `GET /api/skills/<skill_id>/related` - Get skills related to a specific skill
- `GET /api/skills/path?start=<skill_id>&end=<skill_id>` - Find a path between skills
- `GET /api/careers/path?current=<title>&target=<title>` - Get career path between titles

#### Browsing

- `GET /api/jobs` - List all jobs
- `GET /api/candidates` - List all candidates
- `GET /api/skills` - List all skills

#### Details

- `GET /api/jobs/<job_id>` - Get details for a specific job
- `GET /api/candidates/<resume_id>` - Get details for a specific candidate
- `GET /api/skills/<skill_id>` - Get details for a specific skill

## API Response Examples

### Job Listing

```json
GET /api/jobs

{
  "jobs": [
    {
      "job_id": "job_001",
      "title": "Senior Software Engineer",
      "company": "Tech Solutions Inc",
      "location": "San Francisco, CA",
      "domain": "Software Development"
    },
    ...
  ]
}
```

### Candidate Matching

```json
GET /api/jobs/job_001/candidates

{
  "matches": [
    {
      "resume_id": "resume_042",
      "name": "Sarah Johnson",
      "title": "Full Stack Developer",
      "match_percentage": 87.5,
      "matching_skills": ["JavaScript", "React", "Node.js"],
      "missing_skills": ["Kubernetes"]
    },
    ...
  ]
}
```

### Skill Gap Analysis

```json
GET /api/candidates/resume_042/jobs/job_001/skill-gap

{
  "matching_skills": [
    {
      "skill_id": "skill_007",
      "name": "JavaScript",
      "proficiency": 4,
      "required_proficiency": 3
    },
    ...
  ],
  "missing_skills": [
    {
      "skill_id": "skill_023",
      "name": "Kubernetes",
      "required_proficiency": 2
    },
    ...
  ],
  "exceeding_skills": [
    {
      "skill_id": "skill_015",
      "name": "GraphQL",
      "proficiency": 3
    },
    ...
  ]
}
```

## Example Use Cases

### Scenario 1: Recruiter Looking for Candidates

A recruiting application can:

1. Get a job's details using `GET /api/jobs/<job_id>`
2. Find matching candidates with `GET /api/jobs/<job_id>/candidates`
3. Examine detailed skill matches for each candidate

### Scenario 2: Job Seeker Finding Opportunities

A job search application can:

1. Get a candidate's profile using `GET /api/candidates/<resume_id>`
2. Find matching job opportunities with `GET /api/candidates/<resume_id>/jobs`
3. Analyze skill gaps for specific jobs with `GET /api/candidates/<resume_id>/jobs/<job_id>/skill-gap`

### Scenario 3: Career Development Planning

A career planning tool can:

1. Get skill recommendations with `GET /api/candidates/<resume_id>/jobs/<job_id>/recommendations`
2. Find career paths between roles with `GET /api/careers/path?current=<title>&target=<title>`
3. Create personalized learning paths based on skill gaps

## Data Management with ETL

Talent Matcher includes a robust ETL (Extract, Transform, Load) module to manage the Neo4j knowledge graph data. This module handles:

1. Extracting data from JSON files in the data directory
2. Transforming the data for optimal storage in the graph database
3. Loading the data into Neo4j with proper relationships

### Using the ETL Module

The ETL module can be used from the command line to perform various data operations:

```bash
# Basic usage - clears database and loads all data (with confirmation prompt)
python -m src.etl.data_loader

# Non-interactive mode (skips confirmation prompts)
python -m src.etl.data_loader --force

# Clear the database without loading data
python -m src.etl.data_loader --clear-only

# Load data without clearing the database first
python -m src.etl.data_loader --no-clear

# Use a custom data directory
python -m src.etl.data_loader --data-dir custom/path/to/data
```

### ETL Process Details

The ETL pipeline performs the following steps:

1. **Extract** - Reads data from:

   - Skill taxonomy in `src/data_generation/skill_taxonomy.py`
   - Job postings in `data/job_dataset.json`
   - Candidate resumes in `data/resume_dataset.json`

2. **Transform** - Processes the data:

   - Creates nodes for skills, jobs, and candidates
   - Establishes relationships between entities
   - Calculates proficiency levels and importance scores

3. **Load** - Populates the Neo4j database:
   - Creates constraints for faster queries
   - Creates nodes with properties
   - Creates relationships with properties

### Using ETL in Your Code

You can also programmatically use the ETL functionality in your Python code:

```python
from src.etl.data_loader import reload_database, clear_database

# Clear database only
clear_database(force=True)  # force=True skips confirmation

# Reload entire database
reload_database(clear=True, force=True, data_dir="custom/data/path")
```

## Troubleshooting

Common issues and their solutions:

1. **Connection Errors**

   - Ensure Neo4j is running
   - Verify credentials in .env file
   - Check network connectivity

2. **No Matches Found**
   - Verify the data is loaded properly
   - Check skill spellings and formatting
   - Consider broadening search criteria
