# Talent Matcher

A knowledge graph-based talent matching system that uses Neo4j to create meaningful connections between skills, candidates, and job postings.

## Overview

Talent Matcher uses Neo4j's graph database capabilities to model complex relationships between skills, job postings, and candidate profiles. This approach provides several advantages over traditional keyword-based matching systems:

1. **Contextual Skill Matching** - Understanding relationships between skills (e.g., React is related to JavaScript)
2. **Skill Gap Analysis** - Identifying what skills a candidate needs to learn for a specific job
3. **Career Path Recommendations** - Suggesting optimal learning paths for career advancement

## Architecture

The system is structured as follows:

```
talent-matcher/
├── data/                  # Data files (jobs, resumes, skills)
├── src/                   # Source code for backend
│   ├── api/               # REST API endpoints
│   ├── knowledge_graph/   # Neo4j database interaction
│   ├── data_generation/   # Utilities for generating sample data
│   └── utils/             # Helper utilities
├── tests/                 # Test cases
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
└── notebooks/             # Jupyter notebooks for exploration
```

### Key Components

1. **Knowledge Graph Layer** (`src/knowledge_graph/`):

   - Model of entities and relationships
   - Data loading utilities
   - Graph querying capabilities

2. **Matching Engine** (`src/knowledge_graph/matcher.py`):

   - Algorithms for matching candidates to jobs
   - Skill gap analysis
   - Recommendation logic

3. **API Layer** (`src/api/`):
   - REST endpoints for programmatic access
   - JSON responses for integration

## Installation

### Prerequisites

- Python 3.8+
- Neo4j database (v4.4+)
- Neo4j desktop or accessible Neo4j instance

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/talent-matcher.git
   cd talent-matcher
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install backend dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure Neo4j connection:
   Create a `.env` file in the project root with:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

## Usage

### Running the Application

Run the backend API server:

```bash
# Run API server
python run.py api
```

The API will be available at:

- **API**: http://localhost:8000

You can also use the start script:

```bash
# Run with the start script
./start.sh
```

### Testing

Run the test suite with:

```bash
python run.py test
```

You can also run specific test categories:

```bash
# Run unit tests only
python -m pytest tests/unit

# Run integration tests only
python -m pytest tests/integration

# Run specific test file
python -m pytest tests/integration/test_backend_api.py
```

### Database Management

To load or reload data into your database:

```bash
# Clear the database and load all data (with confirmation prompt)
python -m src.etl.data_loader

# Skip confirmation prompt (non-interactive mode)
python -m src.etl.data_loader --force

# Only clear the database without loading data
python -m src.etl.data_loader --clear-only

# Skip clearing the database, just load data
python -m src.etl.data_loader --no-clear

# Use a custom data directory
python -m src.etl.data_loader --data-dir custom/path/to/data
```

To test your database connection:

```bash
python -m tests.utils.test_db_connection
```

### Database Query Tools

The repository includes useful query tools for exploring the database:

```bash
# Query job details
python -m src.tools.query_job job_1

# Query job matches
python -m src.tools.query_matches job_1
```

### API Endpoints

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

## Documentation

For more details about the API and data structures, see the [USAGE.md](USAGE.md) file.

## Frontend Design Reference

The original frontend design documentation has been preserved in [FRONTEND_DESIGN.md](FRONTEND_DESIGN.md) for reference.
