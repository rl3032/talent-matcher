# Talent Matcher

Talent Matcher is a comprehensive skill-based job matching platform that uses graph database technology to connect candidates with the most suitable job opportunities based on their skills, experience, and career goals.

## Features

- **Skill-Based Matching**: Advanced algorithm for matching candidates to jobs based on skills, location, and semantic analysis of experience
- **Knowledge Graph**: Uses Neo4j graph database to model relationships between skills, jobs, and candidates
- **Interactive Skill Visualization**: Explore skill relationships and discover related skills
- **Skill Gap Analysis**: Identify missing skills and leverage existing related skills for job opportunities
- **Comprehensive API**: Full-featured REST API for all platform functionality
- **Role-Based Access Control**: Secure endpoints and user interfaces based on user roles (admin, hiring manager, job seeker)
- **Complete CRUD Operations**: Create, read, update, and delete functionality for resumes and job postings
- **User Authentication**: JWT-based authentication system with secure password handling

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
   cd frontend
   npm install
   ```

4. Configure environment variables in a `.env` file

   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   JWT_SECRET_KEY=your_jwt_secret
   ```

5. Start the backend server

   ```bash
   python src/api/app.py
   ```

6. Start the frontend development server

   ```bash
   cd frontend
   npm run dev
   ```

7. Open your browser and navigate to `http://localhost:3000`

## User Roles

Talent Matcher supports three user roles, each with specific permissions:

- **Job Seekers**: Can upload and edit resumes, view matching jobs, analyze skill gaps, and access their own profile data
- **Hiring Managers**: Can post, edit, and delete job listings, view and filter candidates matching their job posts
- **Administrators**: Have full access to all features and user management

## Project Structure

- `/src`: Backend Python code
  - `/api`: Flask API endpoints
  - `/knowledge_graph`: Neo4j graph database interaction
  - `/data_generation`: Data generators for sample data
  - `/etl`: Data loading utilities
- `/frontend`: Next.js/React frontend application
  - `/app`: Next.js application routes
  - `/components`: Reusable React components
  - `/lib`: Utility functions and API client
- `/data`: Sample data and schemas
- `/tests`: Backend tests

## License

This project is licensed under the MIT License - see the LICENSE file for details.
