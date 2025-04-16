#!/usr/bin/env python
"""
Data Loader for Knowledge Graph
This module handles extracting, transforming, and loading data into the Neo4j knowledge graph.
"""

import json
import os
import glob
from typing import Dict, List, Optional, Any, Tuple
from src.knowledge_graph.model import KnowledgeGraph
from src.data_generation.skill_taxonomy import SKILLS
from src.config import DATA_DIR


class ETLPipeline:
    """ETL Pipeline for Knowledge Graph data."""
    
    def __init__(self, kg: KnowledgeGraph, data_dir: str = DATA_DIR):
        """Initialize ETL Pipeline with knowledge graph and data directory."""
        self.kg = kg
        self.data_dir = data_dir
        
    def extract_skills(self) -> Dict[str, Dict]:
        """Extract skills data from taxonomy."""
        print("Extracting skills taxonomy...")
        return SKILLS
    
    def extract_jobs(self) -> List[Dict]:
        """Extract job data from JSON files."""
        job_file = os.path.join(self.data_dir, "job_dataset.json")
        if not os.path.exists(job_file):
            print(f"Warning: Job file not found at {job_file}")
            return []
            
        print(f"Extracting jobs from {job_file}")
        with open(job_file, 'r') as f:
            try:
                return json.load(f).get("jobs", [])
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in {job_file}")
                return []
    
    def extract_resumes(self) -> List[Dict]:
        """Extract resume data from JSON files."""
        resume_file = os.path.join(self.data_dir, "resume_dataset.json")
        if not os.path.exists(resume_file):
            print(f"Warning: Resume file not found at {resume_file}")
            return []
            
        print(f"Extracting resumes from {resume_file}")
        with open(resume_file, 'r') as f:
            try:
                data = json.load(f)
                if isinstance(data, dict) and "resumes" in data:
                    return data["resumes"]
                elif isinstance(data, list):
                    return data
                else:
                    return [data] if isinstance(data, dict) else []
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in {resume_file}")
                return []
    
    def transform_skills(self, skills_data: Dict[str, Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Transform skills data for loading."""
        print("Transforming skills data...")
        skill_nodes = []
        skill_relationships = []
        
        for skill_id, skill_data in skills_data.items():
            # Create skill node
            skill_nodes.append({
                "skill_id": skill_id,
                "name": skill_data["name"],
                "category": skill_data["category"],
                "domain": skill_data["domain"]
            })
            
            # Extract relationships
            for rel_type, related_skills in skill_data.get("relationships", {}).items():
                for target_skill_id in related_skills:
                    skill_relationships.append({
                        "source": skill_id,
                        "target": target_skill_id,
                        "type": rel_type
                    })
        
        return skill_nodes, skill_relationships
    
    def transform_jobs(self, jobs_data: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Transform jobs data for loading."""
        print("Transforming jobs data...")
        job_nodes = []
        job_skill_relationships = []
        skill_relationships = []
        
        for job in jobs_data:
            # Create job node
            job_nodes.append({
                "job_id": job["job_id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "domain": job.get("domain", ""),
                "summary": job.get("summary", ""),
                "responsibilities": job.get("responsibilities", []),
                "qualifications": job.get("qualifications", [])
            })
            
            # Extract primary skills
            for skill in job.get("skills", {}).get("primary", []):
                job_skill_relationships.append({
                    "job_id": job["job_id"],
                    "skill_id": skill["skill_id"],
                    "level": skill.get("importance", 8) * 10,  # Convert to 0-10 scale
                    "is_primary": True,
                    "proficiency": skill.get("proficiency", "advanced")
                })
                
            # Extract secondary skills
            for skill in job.get("skills", {}).get("secondary", []):
                job_skill_relationships.append({
                    "job_id": job["job_id"],
                    "skill_id": skill["skill_id"],
                    "level": skill.get("importance", 5) * 10,  # Convert to 0-10 scale
                    "is_primary": False,
                    "proficiency": skill.get("proficiency", "intermediate")
                })
                
            # Extract skill relationships
            for rel in job.get("skill_relationships", []):
                skill_relationships.append({
                    "source": rel["source"],
                    "target": rel["target"],
                    "type": rel["type"],
                    "weight": rel.get("weight", 1.0)
                })
        
        return job_nodes, job_skill_relationships, skill_relationships
    
    def transform_resumes(self, resumes_data: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
        """Transform resumes data for loading."""
        print("Transforming resumes data...")
        candidate_nodes = []
        candidate_skill_relationships = []
        skill_relationships = []
        experience_data = []  # New list to store experience data
        
        for resume in resumes_data:
            # Create candidate node
            candidate_nodes.append({
                "resume_id": resume["resume_id"],
                "name": resume["name"],
                "email": resume.get("email", ""),
                "title": resume.get("title", ""),
                "location": resume.get("location", ""),
                "domain": resume.get("domain", ""),
                "summary": resume.get("summary", ""),
                "education": resume.get("education", [])
            })
            
            # Process experience data
            if "experience" in resume and resume["experience"]:
                for i, exp in enumerate(resume["experience"]):
                    # Create a unique ID for the experience
                    exp_id = f"{resume['resume_id']}_exp_{i}"
                    
                    # Create experience node data
                    exp_data = {
                        "exp_id": exp_id,
                        "resume_id": resume["resume_id"],
                        "job_title": exp.get("job_title", ""),
                        "company": exp.get("company", ""),
                        "start_date": exp.get("start_date", ""),
                        "end_date": exp.get("end_date", "Present"),
                        "description": exp.get("description", [])
                    }
                    
                    # Process skills used in this experience
                    if "skills_used" in exp and exp["skills_used"]:
                        exp_data["skills_used"] = exp["skills_used"]
                    
                    experience_data.append(exp_data)
            
            # Handle case where skills might be missing or have unexpected structure
            skills_data = resume.get("skills", {})
            if not isinstance(skills_data, dict):
                skills_data = {}
            
            # Extract core skills
            for skill in skills_data.get("core", []):
                if not isinstance(skill, dict) or "skill_id" not in skill:
                    continue  # Skip invalid skill entries
                
                # Use proficiency field instead of proficiency_level
                # Map string proficiency to numeric value if needed
                proficiency_value = self._get_proficiency_value(skill.get("proficiency", ""))
                
                candidate_skill_relationships.append({
                    "resume_id": resume["resume_id"],
                    "skill_id": skill["skill_id"],
                    "level": proficiency_value,
                    "years": skill.get("experience_years", 0),
                    "is_core": True
                })
                
            # Extract secondary skills
            for skill in skills_data.get("secondary", []):
                if not isinstance(skill, dict) or "skill_id" not in skill:
                    continue  # Skip invalid skill entries
                    
                # Use proficiency field instead of proficiency_level
                proficiency_value = self._get_proficiency_value(skill.get("proficiency", ""))
                
                candidate_skill_relationships.append({
                    "resume_id": resume["resume_id"],
                    "skill_id": skill["skill_id"],
                    "level": proficiency_value,
                    "years": skill.get("experience_years", 0),
                    "is_core": False
                })
                
            # Extract skill relationships
            for rel in resume.get("skill_relationships", []):
                if not isinstance(rel, dict) or "source" not in rel or "target" not in rel or "type" not in rel:
                    continue  # Skip invalid relationship entries
                    
                skill_relationships.append({
                    "source": rel["source"],
                    "target": rel["target"],
                    "type": rel["type"],
                    "weight": rel.get("weight", 1.0)
                })
        
        return candidate_nodes, candidate_skill_relationships, skill_relationships, experience_data
    
    def _get_proficiency_value(self, proficiency: str) -> float:
        """Convert string proficiency to numeric value."""
        proficiency_map = {
            "beginner": 5.0,
            "intermediate": 7.0,
            "advanced": 8.5,
            "expert": 10.0
        }
        # Default to a middle value if proficiency not recognized
        return proficiency_map.get(proficiency.lower(), 5.0)
    
    def load_skills(self, skill_nodes: List[Dict], skill_relationships: List[Dict]) -> None:
        """Load skills into knowledge graph."""
        print(f"Loading {len(skill_nodes)} skills...")
        for skill in skill_nodes:
            self.kg.add_skill(skill)
            
        print(f"Loading {len(skill_relationships)} skill relationships...")
        for rel in skill_relationships:
            self.kg.add_skill_relationship(
                rel["source"],
                rel["target"],
                rel["type"],
                rel.get("weight", 1.0)
            )
    
    def load_jobs(self, job_nodes: List[Dict], job_skill_relationships: List[Dict]) -> None:
        """Load jobs into knowledge graph."""
        print(f"Loading {len(job_nodes)} jobs...")
        for job in job_nodes:
            self.kg.add_job(job)
            
        print(f"Loading {len(job_skill_relationships)} job skill relationships...")
        for rel in job_skill_relationships:
            self.kg.add_job_skill(
                rel["job_id"],
                rel["skill_id"],
                proficiency=rel.get("proficiency", "intermediate"),
                importance=rel["level"],
                is_primary=rel["is_primary"]
            )
    
    def load_candidates(self, candidate_nodes: List[Dict], candidate_skill_rels: List[Dict]):
        """Load candidate data into the knowledge graph."""
        print(f"Loading {len(candidate_nodes)} candidates into knowledge graph...")
        for node in candidate_nodes:
            self.kg.add_candidate(node)
            
        print(f"Loading {len(candidate_skill_rels)} candidate-skill relationships...")
        for rel in candidate_skill_rels:
            self.kg.add_candidate_skill(
                rel["resume_id"],
                rel["skill_id"],
                proficiency=rel["level"],
                experience_years=rel.get("years", 0),
                is_core=rel["is_core"]
            )
    
    def load_experiences(self, experience_data: List[Dict]):
        """Load experience data into the knowledge graph."""
        print(f"Loading {len(experience_data)} experiences into knowledge graph...")
        for exp in experience_data:
            # Create the experience node
            with self.kg.driver.session() as session:
                # Create the experience node
                session.run("""
                    MERGE (e:Experience {exp_id: $exp_id})
                    SET e.job_title = $job_title,
                        e.company = $company,
                        e.start_date = $start_date,
                        e.end_date = $end_date,
                        e.description = $description
                """, {
                    "exp_id": exp["exp_id"],
                    "job_title": exp["job_title"],
                    "company": exp["company"],
                    "start_date": exp["start_date"],
                    "end_date": exp["end_date"],
                    "description": self.kg._process_text_list(exp["description"])
                })
                
                # Link the experience to the candidate
                session.run("""
                    MATCH (c:Candidate {resume_id: $resume_id})
                    MATCH (e:Experience {exp_id: $exp_id})
                    MERGE (c)-[r:HAS_EXPERIENCE]->(e)
                """, {
                    "resume_id": exp["resume_id"],
                    "exp_id": exp["exp_id"]
                })
                
                # If there are skills used in this experience, link them
                if "skills_used" in exp and exp["skills_used"]:
                    for skill_name in exp["skills_used"]:
                        # Try to find the skill by name (case insensitive)
                        skill_result = session.run("""
                            MATCH (s:Skill)
                            WHERE toLower(s.name) = toLower($skill_name)
                            RETURN s.skill_id as skill_id
                        """, {"skill_name": skill_name})
                        
                        # If skill found, create the relationship
                        skill_record = skill_result.single()
                        if skill_record:
                            session.run("""
                                MATCH (e:Experience {exp_id: $exp_id})
                                MATCH (s:Skill {skill_id: $skill_id})
                                MERGE (e)-[r:USED_SKILL]->(s)
                            """, {
                                "exp_id": exp["exp_id"],
                                "skill_id": skill_record["skill_id"]
                            })
        print("Experience data loading completed.")
    
    def clear_database(self, force: bool = False) -> bool:
        """Clear all data from the Neo4j database."""
        if not force:
            # Ask for confirmation before clearing
            confirm = input("This will delete ALL data from the Neo4j database. Are you sure? (y/n): ")
            if confirm.lower() != 'y':
                print("Operation cancelled.")
                return False
        
        print("Clearing database (this might take a while)...")
        with self.kg.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        print("Database cleared successfully!")
        return True
    
    def run_pipeline(self, clear_db: bool = True, force: bool = False, generate_embeddings: bool = False) -> bool:
        """Run the complete ETL pipeline.
        
        Args:
            clear_db: Whether to clear the database before loading
            force: Whether to bypass confirmation for clearing the database
            generate_embeddings: Whether to generate text embeddings for experiences and jobs
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Step 1: Clear database if requested
            if clear_db and not self.clear_database(force):
                return False
                
            # Step 2: Create constraints
            self.kg.create_constraints()
            
            # Step 3: Extract data
            skills_data = self.extract_skills()
            jobs_data = self.extract_jobs()
            resumes_data = self.extract_resumes()
            
            # Step 4: Transform data
            skill_nodes, skill_relationships = self.transform_skills(skills_data)
            job_nodes, job_skill_relationships, job_skill_rels = self.transform_jobs(jobs_data)
            candidate_nodes, candidate_skill_relationships, candidate_skill_rels, experience_data = self.transform_resumes(resumes_data)
            
            # Combine all skill relationships
            all_skill_relationships = skill_relationships + job_skill_rels + candidate_skill_rels
            
            # Step 5: Load data
            self.load_skills(skill_nodes, all_skill_relationships)
            self.load_jobs(job_nodes, job_skill_relationships)
            self.load_candidates(candidate_nodes, candidate_skill_relationships)
            self.load_experiences(experience_data)
            
            # Step 6: Generate embeddings if requested
            if generate_embeddings:
                print("Generating text embeddings for enhanced matching...")
                try:
                    success = self.kg.generate_embeddings()
                    if not success:
                        print("Warning: Failed to generate embeddings. Enhanced matching may not work properly.")
                except Exception as e:
                    print(f"Error generating embeddings: {str(e)}")
                    print("Enhanced matching may not work properly.")
            
            print("ETL pipeline completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error in ETL pipeline: {str(e)}")
            return False

# Legacy functions for backward compatibility
def load_skills(kg):
    """Load skills taxonomy into the knowledge graph."""
    print("Loading skills taxonomy...")
    for skill_id, skill_data in SKILLS.items():
        kg.add_skill({
            "skill_id": skill_id,
            "name": skill_data["name"],
            "category": skill_data["category"],
            "domain": skill_data["domain"]
        })
        
    # Add skill relationships
    for skill_id, skill_data in SKILLS.items():
        for rel_type, related_skills in skill_data.get("relationships", {}).items():
            for target_skill_id in related_skills:
                kg.add_skill_relationship(skill_id, target_skill_id, rel_type)
                
    print(f"Loaded {len(SKILLS)} skills with relationships")

def load_jobs(kg, job_file_path):
    """Load job data into the knowledge graph."""
    print(f"Loading jobs from {job_file_path}")
    with open(job_file_path, 'r') as f:
        job_data = json.load(f)
        
    job_count = 0
    for job in job_data.get("jobs", []):
        kg.add_job(job)
        
        # Add primary skills
        for skill in job.get("skills", {}).get("primary", []):
            importance_value = skill.get("importance", 0.8) * 10  # Scale to 0-10
            kg.add_job_skill(
                job["job_id"],
                skill["skill_id"],
                proficiency=skill.get("proficiency", "advanced"),
                importance=importance_value,
                is_primary=True
            )
            
        # Add secondary skills
        for skill in job.get("skills", {}).get("secondary", []):
            importance_value = skill.get("importance", 0.5) * 10  # Scale to 0-10
            kg.add_job_skill(
                job["job_id"],
                skill["skill_id"],
                proficiency=skill.get("proficiency", "intermediate"),
                importance=importance_value,
                is_primary=False
            )
            
        # Add job-specific skill relationships
        for rel in job.get("skill_relationships", []):
            kg.add_skill_relationship(
                rel["source"],
                rel["target"],
                rel["type"],
                rel.get("weight", 1.0)
            )
            
        job_count += 1
        
    print(f"Loaded {job_count} jobs")
    
def load_resumes(kg, resume_file_path):
    """Load resume data into the knowledge graph."""
    print(f"Loading resumes from {resume_file_path}")
    with open(resume_file_path, 'r') as f:
        resume_data = json.load(f)
        
    if isinstance(resume_data, dict):
        # Check if it's a dictionary with a 'resumes' key
        if "resumes" in resume_data:
            resume_count = 0
            for resume in resume_data["resumes"]:
                load_single_resume(kg, resume)
                resume_count += 1
            print(f"Loaded {resume_count} resumes")
        else:
            # Single resume
            load_single_resume(kg, resume_data)
            print("Loaded 1 resume")
    else:
        # List of resumes
        resume_count = 0
        for resume in resume_data:
            load_single_resume(kg, resume)
            resume_count += 1
        print(f"Loaded {resume_count} resumes")
        
def load_single_resume(kg, resume_data):
    """Load a single resume into the knowledge graph."""
    kg.add_candidate(resume_data)
    
    # Add core skills
    for skill in resume_data.get("skills", {}).get("core", []):
        # Handle numeric proficiency directly or convert string proficiency
        proficiency_value = skill.get("proficiency", 0)
        if isinstance(proficiency_value, (int, float)):
            proficiency_level = proficiency_value * 10  # Scale 0-10 to 0-100
        else:
            proficiency_level = skill.get("proficiency_level", 0.8) * 10
            
        kg.add_candidate_skill(
            resume_data["resume_id"],
            skill["skill_id"],
            proficiency=proficiency_level,
            experience_years=skill.get("experience_years", 0),
            is_core=True
        )
        
    # Add secondary skills
    for skill in resume_data.get("skills", {}).get("secondary", []):
        # Handle numeric proficiency directly or convert string proficiency
        proficiency_value = skill.get("proficiency", 0)
        if isinstance(proficiency_value, (int, float)):
            proficiency_level = proficiency_value * 10  # Scale 0-10 to 0-100
        else:
            proficiency_level = skill.get("proficiency_level", 0.5) * 10
            
        kg.add_candidate_skill(
            resume_data["resume_id"],
            skill["skill_id"],
            proficiency=proficiency_level,
            experience_years=skill.get("experience_years", 0),
            is_core=False
        )
        
    # Add candidate-specific skill relationships
    for rel in resume_data.get("skill_relationships", []):
        kg.add_skill_relationship(
            rel["source"],
            rel["target"],
            rel["type"],
            rel.get("weight", 1.0)
        )
        
    # Add experience data if present
    # The KnowledgeGraph class now handles this directly
    # This will be used by the legacy functions

def load_directory(kg, directory_path):
    """Load all JSON files from a directory."""
    json_files = glob.glob(os.path.join(directory_path, "*.json"))
    
    for file_path in json_files:
        filename = os.path.basename(file_path)
        if filename.startswith("job_"):
            kg.add_job(json.load(open(file_path)))
        elif filename.startswith("resume_"):
            load_single_resume(kg, json.load(open(file_path)))
            
def initialize_knowledge_graph(data_dir=None):
    """Initialize the knowledge graph and load all data."""
    from src.knowledge_graph.model import KnowledgeGraph
    kg = KnowledgeGraph()
    kg.connect()
    kg.create_constraints()
    
    # Use the configured data directory if none provided
    data_dir = data_dir or DATA_DIR
    
    # Load skills taxonomy
    load_skills(kg)
    
    # Load main job dataset
    job_file = os.path.join(data_dir, "job_dataset.json")
    if os.path.exists(job_file):
        load_jobs(kg, job_file)
        
    # Load main resume dataset
    resume_file = os.path.join(data_dir, "resume_dataset.json")
    if os.path.exists(resume_file):
        load_resumes(kg, resume_file)
        
    # Load individual files from generated directory
    generated_dir = os.path.join(data_dir, "generated")
    if os.path.exists(generated_dir):
        load_directory(kg, generated_dir)
        
    return kg 

def clear_database(force=False):
    """Clear all data from the Neo4j database."""
    # Load environment variables if needed
    if os.path.exists('.env'):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass  # dotenv is optional
    
    from src.knowledge_graph.model import KnowledgeGraph
    
    if not force:
        # Ask for confirmation before clearing
        confirm = input("This will delete ALL data from the Neo4j database. Are you sure? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return False
    
    print("Connecting to Neo4j database...")
    kg = KnowledgeGraph()
    kg.connect()
    
    try:
        print("Clearing database (this might take a while)...")
        with kg.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        print("Database cleared successfully!")
        return True
    finally:
        kg.close()

def reload_database(clear=True, force=False, data_dir=None):
    """Reload all data into the Neo4j database."""
    # Clear the database if requested
    if clear and not clear_database(force):
        return False
    
    # Initialize knowledge graph and load data
    kg = initialize_knowledge_graph(data_dir)
    kg.close()
    
    print("Database successfully reloaded!")
    return True

def main():
    """Command line interface for ETL pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ETL pipeline for Neo4j knowledge graph')
    parser.add_argument('--no-clear', action='store_true', help='Skip clearing the database before loading')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    parser.add_argument('--data-dir', type=str, help='Custom data directory path')
    parser.add_argument('--clear-only', action='store_true', help='Only clear the database without loading data')
    parser.add_argument('--generate-embeddings', action='store_true', help='Generate text embeddings for enhanced matching')
    args = parser.parse_args()
    
    if args.clear_only:
        clear_database(args.force)
    else:
        # Use the ETLPipeline instead of the legacy functions
        from src.knowledge_graph.model import KnowledgeGraph
        from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
        
        # Initialize knowledge graph
        kg = KnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        kg.connect()  # Explicitly connect to the database
        
        # Create ETL pipeline
        data_dir = args.data_dir or DATA_DIR
        etl = ETLPipeline(kg, data_dir)
        
        # Run the pipeline
        success = etl.run_pipeline(
            clear_db=not args.no_clear,
            force=args.force,
            generate_embeddings=args.generate_embeddings
        )
        
        print("Database reload " + ("successful" if success else "failed"))
        kg.close()

if __name__ == "__main__":
    main() 