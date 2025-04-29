"""
Graph Service

This module provides access to the Neo4j knowledge graph database and repositories.
It acts as a central service for database operations.
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from src.backend.repositories.job_repository import JobRepository
from src.backend.repositories.candidate_repository import CandidateRepository
from src.backend.repositories.skill_repository import SkillRepository
from src.backend.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from datetime import datetime
import json

# Load environment variables
load_dotenv()

class GraphService:
    """Main graph service class that coordinates all graph operations."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls, uri=None, user=None, password=None):
        """Get singleton instance of GraphService."""
        if cls._instance is None:
            cls._instance = cls(uri, user, password)
        return cls._instance
    
    def __init__(self, uri=None, user=None, password=None):
        """Initialize the graph service with Neo4j connection.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self.driver = None
        self.connect()
        
        # Initialize repositories
        self.job_repository = JobRepository(self.driver)
        self.candidate_repository = CandidateRepository(self.driver)
        self.skill_repository = SkillRepository(self.driver)
        
    def connect(self):
        """Connect to the Neo4j database."""
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        print("Connected to Neo4j knowledge graph database")
        
    def close(self):
        """Close the connection to Neo4j."""
        if self.driver:
            self.driver.close()
            
    def create_constraints(self):
        """Create constraints for the graph database."""
        with self.driver.session() as session:
            # Create constraints for unique IDs
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.skill_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (j:Job) REQUIRE j.job_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Candidate) REQUIRE c.resume_id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE")
            
    def ensure_user_schema(self):
        """Make sure the User schema exists in the database."""
        with self.driver.session() as session:
            # Check if User label already exists by looking for any User nodes
            result = session.run("MATCH (u:User) RETURN COUNT(u) AS count")
            record = result.single()
            
            # If no User nodes exist, it's likely the schema has not been created
            if record["count"] == 0:
                print("Initializing User schema in the database")
                # Create an index on email for faster lookups
                session.run("CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.email)")
                # Add timestamps index
                session.run("CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.created_at)")
                print("User schema initialized successfully")
            else:
                print(f"User schema already present with {record['count']} users")
    
    def _process_text_list(self, text_list):
        """Helper method to process text lists for storage."""
        if isinstance(text_list, list):
            return text_list
        elif isinstance(text_list, str):
            # Try to parse as JSON
            try:
                parsed = json.loads(text_list)
                if isinstance(parsed, list):
                    return parsed
                else:
                    return [text_list]  # Single item list
            except json.JSONDecodeError:
                return [text_list]  # Single item list
        else:
            return []  # Empty list as fallback
    
    def generate_embeddings(self):
        """Generate text embeddings for enhanced semantic search.
        
        This method creates embeddings for job descriptions, candidate experiences,
        and skills to enable semantic matching between jobs and candidates.
        
        Returns:
            bool: True if embedding generation was successful, False otherwise
        """
        try:
            # Import the required libraries
            from sentence_transformers import SentenceTransformer
            import numpy as np
            
            print("Starting embedding generation process...")
            
            # Load pre-trained model
            model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Loaded embedding model: all-MiniLM-L6-v2")
            
            # Get all jobs
            with self.driver.session() as session:
                # Get jobs needing embeddings
                job_results = session.run("""
                    MATCH (j:Job)
                    WHERE NOT EXISTS(j.embedding)
                    RETURN j.job_id AS job_id, j.title AS title, 
                           j.description AS description, j.responsibilities AS responsibilities,
                           j.qualifications AS qualifications
                """)
                
                job_count = 0
                for job in job_results:
                    # Combine job text for embedding
                    job_text = f"{job['title'] or ''} {job['description'] or ''}"
                    
                    # Process responsibilities and qualifications
                    responsibilities = self._process_text_list(job['responsibilities'])
                    qualifications = self._process_text_list(job['qualifications'])
                    
                    # Join lists if they exist
                    if responsibilities:
                        job_text += " " + " ".join(responsibilities)
                    if qualifications:
                        job_text += " " + " ".join(qualifications)
                    
                    # Generate embedding
                    embedding = model.encode(job_text)
                    
                    # Store embedding in Neo4j
                    session.run("""
                        MATCH (j:Job {job_id: $job_id})
                        SET j.embedding = $embedding
                    """, {
                        "job_id": job['job_id'],
                        "embedding": embedding.tolist()  # Convert to list for storage
                    })
                    
                    job_count += 1
                    if job_count % 10 == 0:
                        print(f"Processed {job_count} job embeddings")
                
                print(f"Completed job embeddings: {job_count} total")
                
                # Get candidates needing embeddings
                candidate_results = session.run("""
                    MATCH (c:Candidate)
                    WHERE NOT EXISTS(c.embedding)
                    RETURN c.resume_id AS resume_id, c.name AS name, 
                           c.title AS title, c.summary AS summary
                """)
                
                candidate_count = 0
                for candidate in candidate_results:
                    # Combine candidate text for embedding
                    candidate_text = f"{candidate['name'] or ''} {candidate['title'] or ''} {candidate['summary'] or ''}"
                    
                    # Get candidate experiences
                    experiences = self.candidate_repository.get_candidate_experiences(candidate['resume_id'])
                    for exp in experiences:
                        exp_text = f"{exp.get('job_title', '')} {exp.get('company', '')}"
                        if exp.get('description'):
                            if isinstance(exp['description'], list):
                                exp_text += " " + " ".join(exp['description'])
                            else:
                                exp_text += " " + exp['description']
                        candidate_text += " " + exp_text
                    
                    # Generate embedding
                    embedding = model.encode(candidate_text)
                    
                    # Store embedding in Neo4j
                    session.run("""
                        MATCH (c:Candidate {resume_id: $resume_id})
                        SET c.embedding = $embedding
                    """, {
                        "resume_id": candidate['resume_id'],
                        "embedding": embedding.tolist()  # Convert to list for storage
                    })
                    
                    candidate_count += 1
                    if candidate_count % 10 == 0:
                        print(f"Processed {candidate_count} candidate embeddings")
                
                print(f"Completed candidate embeddings: {candidate_count} total")
                
                # Get skills needing embeddings
                skill_results = session.run("""
                    MATCH (s:Skill)
                    WHERE NOT EXISTS(s.embedding)
                    RETURN s.skill_id AS skill_id, s.name AS name, 
                           s.category AS category
                """)
                
                skill_count = 0
                for skill in skill_results:
                    # Combine skill text for embedding
                    skill_text = f"{skill['name'] or ''} {skill['category'] or ''}"
                    
                    # Generate embedding
                    embedding = model.encode(skill_text)
                    
                    # Store embedding in Neo4j
                    session.run("""
                        MATCH (s:Skill {skill_id: $skill_id})
                        SET s.embedding = $embedding
                    """, {
                        "skill_id": skill['skill_id'],
                        "embedding": embedding.tolist()  # Convert to list for storage
                    })
                    
                    skill_count += 1
                    if skill_count % 100 == 0:
                        print(f"Processed {skill_count} skill embeddings")
                
                print(f"Completed skill embeddings: {skill_count} total")
                
                # Create index for vector search if not exists (Neo4j 4.4+)
                try:
                    session.run("""
                        CREATE VECTOR INDEX job_embedding IF NOT EXISTS
                        FOR (j:Job) ON j.embedding
                    """)
                    session.run("""
                        CREATE VECTOR INDEX candidate_embedding IF NOT EXISTS
                        FOR (c:Candidate) ON c.embedding
                    """)
                    session.run("""
                        CREATE VECTOR INDEX skill_embedding IF NOT EXISTS
                        FOR (s:Skill) ON s.embedding
                    """)
                    print("Created vector indexes for embeddings")
                except Exception as e:
                    print(f"Note: Vector indexes not created - may require Neo4j 4.4+ or Enterprise Edition: {e}")
                
            print("Embedding generation completed successfully")
            return True
            
        except ImportError:
            print("Error: sentence-transformers library not installed. Please install with: pip install sentence-transformers")
            return False
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            return False
            
    def clear_database(self, force: bool = False) -> bool:
        """Clear all data from the Neo4j database.
        
        Args:
            force: Whether to bypass confirmation for clearing the database
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not force:
            # Ask for confirmation before clearing
            confirm = input("This will delete ALL data from the Neo4j database. Are you sure? (y/n): ")
            if confirm.lower() != 'y':
                print("Operation cancelled.")
                return False
        
        print("Clearing database (this might take a while)...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        print("Database cleared successfully!")
        return True
        
    def create_test_accounts(self):
        """Create test admin, HR, and candidate accounts and link them to test data."""
        from werkzeug.security import generate_password_hash
        
        # Create User schema directly with Cypher instead of relying on the User class
        with self.driver.session() as session:
            # Create unique constraint for User.email
            try:
                session.run("CREATE CONSTRAINT unique_user_email IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE")
            except Exception as e:
                print(f"Warning: Could not create constraint: {str(e)}")
        
        # Now import the User class
        try:
            from src.api.app import User
        except ImportError:
            try:
                from api.app import User
            except ImportError:
                print("Warning: Could not import User class, creating users directly with Cypher")
                User = None
        
        print("Creating test accounts...")
        
        # Create admin HR account
        hr_email = "hr@example.com"
        hr_password = generate_password_hash("password123")
        hr_name = "Test HR Manager"
        
        # Create HR user directly with Cypher if User class is not available
        if User is None:
            with self.driver.session() as session:
                session.run("""
                    MERGE (u:User {email: $email})
                    SET u.password_hash = $password_hash,
                        u.name = $name,
                        u.role = 'hiring_manager',
                        u.created_at = datetime()
                """, {"email": hr_email, "password_hash": hr_password, "name": hr_name})
                print(f"Created HR account directly: {hr_email}")
        else:
            # Check if user already exists
            hr_user = User.find_by_email(hr_email)
            if not hr_user:
                hr_user = User.create(hr_email, hr_password, hr_name, "hiring_manager")
                print(f"Created HR account: {hr_email}")
        
        # Make the HR account an admin
        with self.driver.session() as session:
            session.run("""
                MATCH (u:User {email: $email})
                SET u.role = 'admin'
            """, {"email": hr_email})
            print(f"Promoted {hr_email} to admin")
            
            # Link all existing jobs to the HR account
            job_count = session.run("""
                MATCH (j:Job)
                SET j.owner_email = $email
                WITH j
                MATCH (u:User {email: $email})
                MERGE (u)-[:CREATED]->(j)
                RETURN count(j) as count
            """, {"email": hr_email}).single()["count"]
            
            print(f"Assigned {job_count} jobs to {hr_email}")
        
        # Create test candidate accounts (up to 30)
        with self.driver.session() as session:
            # Get all candidate profiles
            candidates = session.run("""
                MATCH (c:Candidate)
                RETURN c.resume_id as resume_id, c.name as name, c.email as email
                LIMIT 30
            """).values()
            
            # Create candidate accounts and link them to profiles
            for resume_id, name, candidate_email in candidates:
                # Generate an email if not present
                email = candidate_email or f"candidate_{resume_id}@example.com"
                password = generate_password_hash("password123")
                
                if User is None:
                    # Create directly with Cypher
                    session.run("""
                        MERGE (u:User {email: $email})
                        SET u.password_hash = $password_hash,
                            u.name = $name,
                            u.role = 'candidate',
                            u.profile_id = $profile_id,
                            u.created_at = datetime()
                    """, {
                        "email": email, 
                        "password_hash": password, 
                        "name": name,
                        "profile_id": resume_id
                    })
                    print(f"Created candidate account directly: {email} linked to {resume_id}")
                else:
                    # Use the User class
                    candidate_user = User.find_by_email(email)
                    if not candidate_user:
                        candidate_user = User.create(email, password, name, "candidate", resume_id)
                        print(f"Created candidate account: {email} linked to {resume_id}")
                    else:
                        # Make sure profile_id is set
                        candidate_user.update_profile_id(resume_id)
                        print(f"Updated candidate account: {email} linked to {resume_id}")
        
        print("Test accounts created successfully") 

    def process_neo4j_datetime(self, value):
        """Convert Neo4j DateTime objects to ISO format strings.
        
        Args:
            value: Value that might be a Neo4j DateTime object
            
        Returns:
            str or original value: ISO formatted string if DateTime, otherwise original value
        """
        # Check if it's a Neo4j DateTime object by looking for expected attributes
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day') and \
           hasattr(value, 'hour') and hasattr(value, 'minute') and hasattr(value, 'second'):
            try:
                # Convert to Python datetime then to ISO format string
                dt = datetime(
                    year=value.year, 
                    month=value.month, 
                    day=value.day,
                    hour=value.hour, 
                    minute=value.minute, 
                    second=value.second
                )
                return dt.isoformat()
            except:
                # If conversion fails, return as string
                return str(value)
        return value 