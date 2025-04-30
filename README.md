# Talent Matcher

Talent Matcher is a comprehensive skill-based job matching platform that uses graph database technology to connect candidates with the most suitable job opportunities based on their skills, experience, and career goals.

## Features

- **Skill-Based Matching**: Advanced algorithm for matching candidates to jobs based on skills, location, and semantic analysis of experience
- **Knowledge Graph**: Uses Neo4j graph database to model relationships between skills, jobs, and candidates
- **Interactive Skill Visualization**:
  - Explore skill relationships and discover related skills
  - View the entire skill network with interactive filtering and search
  - Visualize connections between skills including related and complementary relationships
- **Skill Gap Analysis**: Identify missing skills and leverage existing related skills for job opportunities
- **Comprehensive API**: Full-featured REST API for all platform functionality
- **Role-Based Access Control**: Secure endpoints and user interfaces based on user roles (admin, hiring manager, job seeker)
- **Complete CRUD Operations**: Create, read, update, and delete functionality for resumes and job postings
- **User Authentication**: JWT-based authentication system with secure password handling

## Backend Architecture

The backend has been refactored to follow a layered architecture for better maintainability, testability, and scalability:

- **Controller Layer**: Handles HTTP requests and responses
- **Service Layer**: Contains business logic and orchestrates operations
- **Repository Layer**: Manages data access and persistence
- **Model Layer**: Defines data structures and domain objects

This architecture provides:

- Clear separation of concerns
- Improved testability through dependency injection
- Better maintainability with modular components
- Enhanced error handling across layers

## Tech Stack

### Backend

- Python
- Flask
- Neo4j Graph Database
- JWT Authentication

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Context API for auth state management

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- Neo4j Database

### Installation

1. Clone the repository

   ```bash
   git clone https://github.com/yourusername/talent-matcher.git
   cd talent-matcher
   ```

2. Install Python dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Install frontend dependencies

   ```bash
   cd src/frontend
   npm install
   ```

4. Configure environment variables in a `.env` file

   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   JWT_SECRET_KEY=your_jwt_secret
   ```

### Running the Application

The project provides a unified CLI through the `run.py` script:

```bash
# Start the backend server
python run.py backend

# Start the frontend development server
python run.py frontend

# Load test data into the database
python run.py load-data

# Generate synthetic test data
python run.py generate-data

# Run tests
python run.py test

# Run tests with coverage
python run.py test --coverage
```

You can also get help for each command:

```bash
python run.py --help
python run.py <command> --help
```

For example, to run the backend on a specific port:

```bash
python run.py backend --port 5000 --host localhost
```

After starting both servers, open your browser and navigate to `http://localhost:3000`

## Testing

The project includes comprehensive unit and integration tests for the backend.

To run tests using pytest directly:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html:coverage_html
```

### Test Structure

- `/tests`: All test files
  - `/unit`: Unit tests for individual components
    - `/backend`: Backend unit tests
      - `/models`: Tests for data models
      - `/repositories`: Tests for database repositories
      - `/routes`: Tests for API routes
      - `/services`: Tests for service layer
      - `/utils`: Tests for utility functions
  - `/integration`: Integration tests
    - Tests for service interactions and API workflows

### Coverage Reports

After running tests, a coverage report will be displayed in the console and an HTML coverage report will be generated in the `coverage_html` directory.

## User Roles

Talent Matcher supports three user roles, each with specific permissions:

- **Job Seekers**: Can upload and edit resumes, view matching jobs, analyze skill gaps, and access their own profile data
- **Hiring Managers**: Can post, edit, and delete job listings, view and filter candidates matching their job posts
- **Administrators**: Have full access to all features and user management

## Project Structure

- `/src`: All source code
  - `/backend`: Flask API and backend services with layered architecture
    - `/models`: Data models
    - `/repositories`: Data access layer
    - `/routes`: API endpoints
    - `/services`: Business logic
    - `/utils`: Utility functions
  - `/frontend`: Next.js/React frontend application
    - `/app`: Next.js application routes
    - `/components`: Reusable React components
    - `/lib`: Utility functions and API client
- `/tests`: Test files
- `/data`: Sample data and schemas

## License

This project is licensed under the MIT License - see the LICENSE file for details.
