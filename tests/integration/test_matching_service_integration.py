"""
Integration tests for the MatchingService.

These tests verify that the matcher service interacts correctly with other components
and properly integrates with the Knowledge Graph database.
"""

import unittest
import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src import config
from src.backend.services.graph_service import GraphService
from src.backend.services.matching_service import MatchingService


class TestMatcherIntegration(unittest.TestCase):
    """Integration tests for the MatchingService class."""

    @classmethod
    def setUpClass(cls):
        """Set up test database and initialize components once before all tests."""
        # Load test configuration with test database credentials
        test_config_path = os.path.join(os.path.dirname(__file__), '../test_config.json')
        
        # Default connection parameters
        neo4j_uri = config.NEO4J_URI
        neo4j_user = config.NEO4J_USER
        neo4j_password = config.NEO4J_PASSWORD
        
        if os.path.exists(test_config_path):
            try:
                with open(test_config_path, 'r') as f:
                    test_config = json.load(f)
                    neo4j_uri = test_config.get('neo4j_uri', neo4j_uri)
                    neo4j_user = test_config.get('neo4j_user', neo4j_user)
                    neo4j_password = test_config.get('neo4j_password', neo4j_password)
            except Exception as e:
                print(f"Failed to load test configuration: {e}")
        
        # Initialize graph service with test database connection
        cls.graph_service = GraphService(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password
        )
        
        # Initialize matcher service with graph service
        cls.matcher = MatchingService(cls.graph_service)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests have completed."""
        # Close the database connection
        if hasattr(cls, 'graph_service') and cls.graph_service is not None:
            cls.graph_service.close()
    
    def setUp(self):
        """Set up before each test - clear test database and add test data."""
        # Skip tests if integration tests are not enabled
        if not self._is_integration_test_enabled():
            self.skipTest("Integration tests not enabled or test database not available")
        
        # Clear the test database
        self._clear_test_database()
        
        # Add test data (will be implemented in each test)
    
    def tearDown(self):
        """Clean up after each test."""
        # Clear test data if needed
        if self._is_integration_test_enabled():
            self._clear_test_database()
    
    def _is_integration_test_enabled(self):
        """Check if integration tests are enabled."""
        # Always return True for now to allow tests to run without environment variable
        # In production, you might want to check for a specific environment variable
        # return os.environ.get('RUN_INTEGRATION_TESTS', '').lower() == 'true'
        return True
    
    def _clear_test_database(self):
        """Clear all test data from the database."""
        if hasattr(self, 'graph_service') and self.graph_service is not None:
            try:
                with self.graph_service.driver.session() as session:
                    session.run("MATCH (n) DETACH DELETE n")
            except Exception as e:
                print(f"Failed to clear test database: {e}")
    
    def _add_test_job(self, job_id="test_job_1", title="Software Engineer", 
                     description="Software engineering position requiring Python and JavaScript"):
        """Add a test job to the database."""
        job_data = {
            "job_id": job_id,
            "title": title,
            "summary": description,
            "company": "Test Company"
        }
        self.graph_service.job_repository.add_job(job_data)
        
        # First ensure these skills exist
        self.graph_service.skill_repository.add_skill({"skill_id": "Python", "name": "Python", "category": "Programming Language"})
        self.graph_service.skill_repository.add_skill({"skill_id": "JavaScript", "name": "JavaScript", "category": "Programming Language"})
        self.graph_service.skill_repository.add_skill({"skill_id": "Docker", "name": "Docker", "category": "DevOps Tool"})
        
        # Add job skills
        self.graph_service.job_repository.add_job_skill(job_id, "Python", "advanced", 0.9)
        self.graph_service.job_repository.add_job_skill(job_id, "JavaScript", "intermediate", 0.8)
        self.graph_service.job_repository.add_job_skill(job_id, "Docker", "beginner", 0.6)
        
        return job_id
    
    def _add_test_candidate(self, resume_id="test_resume_1", name="Test Candidate", 
                           summary="Experienced software engineer with Python skills"):
        """Add a test candidate to the database."""
        candidate_data = {
            "resume_id": resume_id,
            "name": name,
            "summary": summary
        }
        self.graph_service.candidate_repository.add_candidate(candidate_data)
        
        # First ensure these skills exist
        self.graph_service.skill_repository.add_skill({"skill_id": "Python", "name": "Python", "category": "Programming Language"})
        self.graph_service.skill_repository.add_skill({"skill_id": "JavaScript", "name": "JavaScript", "category": "Programming Language"})
        
        # Add candidate skills using direct Cypher query to set correct property names
        with self.graph_service.driver.session() as session:
            session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})
                MATCH (s:Skill {skill_id: $skill_id})
                MERGE (c)-[r:HAS_CORE_SKILL]->(s)
                SET r.proficiency = $proficiency,
                    r.experience_years = $years
            """, {
                "resume_id": resume_id,
                "skill_id": "Python",
                "proficiency": "advanced",
                "years": 3
            })
            
            session.run("""
                MATCH (c:Candidate {resume_id: $resume_id})
                MATCH (s:Skill {skill_id: $skill_id})
                MERGE (c)-[r:HAS_CORE_SKILL]->(s)
                SET r.proficiency = $proficiency,
                    r.experience_years = $years
            """, {
                "resume_id": resume_id,
                "skill_id": "JavaScript",
                "proficiency": "intermediate",
                "years": 2
            })
        
        # Add candidate experience
        exp_id = f"exp_{resume_id}_1"
        self.graph_service.candidate_repository.add_candidate_experience(
            resume_id, exp_id, "Software Developer", "ABC Company",
            start_date=datetime(2018, 1, 1), end_date=datetime(2021, 1, 1),
            description="Developed web applications using Python and JavaScript"
        )
        
        return resume_id
    
    def _add_test_skills(self):
        """Add test skills to the database with relationships."""
        # Add skills with relationships
        self.graph_service.skill_repository.add_skill({"skill_id": "Python", "name": "Python", "category": "Programming Language"})
        self.graph_service.skill_repository.add_skill({"skill_id": "JavaScript", "name": "JavaScript", "category": "Programming Language"})
        self.graph_service.skill_repository.add_skill({"skill_id": "Docker", "name": "Docker", "category": "DevOps Tool"})
        self.graph_service.skill_repository.add_skill({"skill_id": "Kubernetes", "name": "Kubernetes", "category": "DevOps Tool"})
        self.graph_service.skill_repository.add_skill({"skill_id": "Django", "name": "Django", "category": "Python Framework"})
        self.graph_service.skill_repository.add_skill({"skill_id": "Flask", "name": "Flask", "category": "Python Framework"})
        self.graph_service.skill_repository.add_skill({"skill_id": "React", "name": "React", "category": "JavaScript Framework"})
        
        # Add relationships with the correct direction (framework -> language)
        # Django requires Python
        with self.graph_service.driver.session() as session:
            # Django REQUIRES Python
            session.run("""
                MATCH (source:Skill {skill_id: 'Django'})
                MATCH (target:Skill {skill_id: 'Python'})
                MERGE (source)-[r:REQUIRES]->(target)
            """)
            
            # Flask REQUIRES Python
            session.run("""
                MATCH (source:Skill {skill_id: 'Flask'})
                MATCH (target:Skill {skill_id: 'Python'})
                MERGE (source)-[r:REQUIRES]->(target)
            """)
            
            # React REQUIRES JavaScript
            session.run("""
                MATCH (source:Skill {skill_id: 'React'})
                MATCH (target:Skill {skill_id: 'JavaScript'})
                MERGE (source)-[r:REQUIRES]->(target)
            """)
            
            # Kubernetes RELATED_TO Docker
            session.run("""
                MATCH (source:Skill {skill_id: 'Kubernetes'})
                MATCH (target:Skill {skill_id: 'Docker'})
                MERGE (source)-[r:RELATED_TO]->(target)
            """)
    
    def test_match_job_to_candidates_integration(self):
        """Integration test for finding candidates for a job."""
        # Set up test data
        self._add_test_skills()
        job_id = self._add_test_job()
        candidate_id = self._add_test_candidate()
        
        # Add another candidate with fewer matching skills
        candidate_data = {
            "resume_id": "test_resume_2",
            "name": "Another Candidate",
            "summary": "Developer with some JavaScript experience"
        }
        self.graph_service.candidate_repository.add_candidate(candidate_data)
        self.graph_service.candidate_repository.add_candidate_skill("test_resume_2", "JavaScript", "intermediate", 1)
        
        # Execute the matcher method
        candidates = self.matcher.match_job_to_candidates(job_id)
        
        # Verify results
        self.assertIsNotNone(candidates)
        self.assertGreaterEqual(len(candidates), 1)
        
        # Check that our main test candidate is in the results
        found_candidate = next((c for c in candidates if c.get("resume_id") == candidate_id), None)
        self.assertIsNotNone(found_candidate)
        
        # Check that match percentage is calculated
        self.assertIn("match_percentage", found_candidate)
        self.assertGreater(found_candidate["match_percentage"], 0)
    
    def test_match_candidate_to_jobs_integration(self):
        """Integration test for finding jobs for a candidate."""
        # Set up test data
        self._add_test_skills()
        job_id = self._add_test_job()
        candidate_id = self._add_test_candidate()
        
        # Add another job with fewer matching skills
        job_data = {
            "job_id": "test_job_2",
            "title": "Frontend Developer",
            "summary": "Frontend development position requiring JavaScript",
            "company": "Test Company"
        }
        self.graph_service.job_repository.add_job(job_data)
        self.graph_service.job_repository.add_job_skill("test_job_2", "JavaScript", "advanced", 0.9)
        self.graph_service.job_repository.add_job_skill("test_job_2", "React", "intermediate", 0.8)
        
        # Execute the matcher method
        jobs = self.matcher.match_candidate_to_jobs(candidate_id)
        
        # Verify results
        self.assertIsNotNone(jobs)
        self.assertGreaterEqual(len(jobs), 1)
        
        # Check that our main test job is in the results
        found_job = next((j for j in jobs if j.get("job_id") == job_id), None)
        self.assertIsNotNone(found_job)
        
        # Check that match percentage is calculated
        self.assertIn("match_percentage", found_job)
        self.assertGreater(found_job["match_percentage"], 0)
    
    def test_recommend_skills_for_job_integration(self):
        """Integration test for skill recommendation."""
        # Set up test data
        self._add_test_skills()
        job_id = self._add_test_job()
        candidate_id = self._add_test_candidate()
        
        # Execute the matcher method to get recommended skills
        recommended_skills = self.matcher.recommend_skills_for_job(candidate_id, job_id)
        
        # Verify results
        self.assertIsNotNone(recommended_skills)
        
        # We should get Docker as a recommendation since it's required by the job but not in candidate skills
        docker_recommendation = next((s for s in recommended_skills if s.get("name") == "Docker"), None)
        self.assertIsNotNone(docker_recommendation)
        
        # Check the structure of the recommendation
        self.assertIn("skill_id", docker_recommendation)
        self.assertIn("name", docker_recommendation)
    
    def test_get_skill_path_integration(self):
        """Integration test for finding skill paths."""
        # Set up test data
        self._add_test_skills()
        
        # Make sure we're getting skill paths in the correct direction (React -> JavaScript)
        # since that's how the relationship is defined
        path = self.matcher.get_skill_path("React", "JavaScript")
        
        print("Actual path:", path)
        
        # Verify results
        self.assertIsNotNone(path)
        self.assertIn("skill_names", path)
        self.assertGreaterEqual(len(path.get("skill_names", [])), 2)  # At least React and JavaScript
        self.assertIn("relationship_types", path)
        self.assertIn("REQUIRES", path.get("relationship_types", []))
    
    def test_graph_and_matching_service_integration(self):
        """Integration test to verify the interaction between GraphService and MatchingService."""
        # Set up test data
        self._add_test_skills()
        
        # Add skills explicitly including Machine Learning
        self.graph_service.skill_repository.add_skill({"skill_id": "Statistics", "name": "Statistics", "category": "Data Science Skill"})
        self.graph_service.skill_repository.add_skill({"skill_id": "Machine Learning", "name": "Machine Learning", "category": "Data Science Skill"})
        self.graph_service.skill_repository.add_skill({"skill_id": "HTML", "name": "HTML", "category": "Web Development Skill"})
        self.graph_service.skill_repository.add_skill({"skill_id": "CSS", "name": "CSS", "category": "Web Development Skill"})
        
        # Add different jobs with varying skill requirements
        job_ids = []
        job_ids.append(self._add_test_job("data_job", "Data Scientist", 
                     "Data science position requiring Python and statistics skills"))
        
        print("Adding specific job skills for data scientist...")
        # Add these directly to ensure REQUIRES_PRIMARY relationship is used
        with self.graph_service.driver.session() as session:
            # First ensure all skills exist
            session.run("""
                MATCH (s:Skill {skill_id: 'Machine Learning'})
                RETURN count(s) as count
            """)
            
            # Clear existing job skills to avoid duplicates
            session.run("""
                MATCH (j:Job {job_id: 'data_job'})-[r]->(s:Skill)
                DELETE r
            """)
            
            session.run("""
                MATCH (j:Job {job_id: 'data_job'})
                MATCH (s:Skill {skill_id: 'Python'})
                MERGE (j)-[r:REQUIRES_PRIMARY]->(s)
                SET r.proficiency = 'advanced',
                    r.importance = 0.9
            """)
            
            session.run("""
                MATCH (j:Job {job_id: 'data_job'})
                MATCH (s:Skill {skill_id: 'Statistics'})
                MERGE (j)-[r:REQUIRES_PRIMARY]->(s)
                SET r.proficiency = 'advanced',
                    r.importance = 0.9
            """)
            
            # Make sure this relationship is created
            session.run("""
                MATCH (j:Job {job_id: 'data_job'})
                MATCH (s:Skill {skill_id: 'Machine Learning'})
                MERGE (j)-[r:REQUIRES_PRIMARY]->(s)
                SET r.proficiency = 'intermediate',
                    r.importance = 0.8
            """)
            
            # Verify Machine Learning was added
            result = session.run("""
                MATCH (j:Job {job_id: 'data_job'})-[r:REQUIRES_PRIMARY]->(s:Skill {skill_id: 'Machine Learning'})
                RETURN count(r) as count
            """).single()
            
            print(f"Machine Learning skill requirement count: {result['count']}")
        
        job_ids.append(self._add_test_job("web_job", "Web Developer", 
                     "Web development position requiring JavaScript and React"))
        self.graph_service.job_repository.add_job_skill("web_job", "JavaScript", "advanced", 0.9)
        self.graph_service.job_repository.add_job_skill("web_job", "React", "intermediate", 0.8)
        self.graph_service.job_repository.add_job_skill("web_job", "HTML", "advanced", 0.7)
        self.graph_service.job_repository.add_job_skill("web_job", "CSS", "advanced", 0.7)
        
        # Add relationships
        print("Adding skill relationships...")
        with self.graph_service.driver.session() as session:
            # Machine Learning REQUIRES Statistics
            session.run("""
                MATCH (source:Skill {skill_id: 'Machine Learning'})
                MATCH (target:Skill {skill_id: 'Statistics'})
                MERGE (source)-[r:REQUIRES]->(target)
            """)
            
            # Machine Learning RELATED_TO Python (not COMMONLY_USED_WITH)
            session.run("""
                MATCH (source:Skill {skill_id: 'Machine Learning'})
                MATCH (target:Skill {skill_id: 'Python'})
                MERGE (source)-[r:RELATED_TO]->(target)
            """)
        
        # Add different candidates with varying skill sets
        candidate_ids = []
        # Data science candidate
        candidate_ids.append(self._add_test_candidate("data_candidate", "Data Analyst", 
                           "Experienced data analyst with statistics background"))
        self.graph_service.candidate_repository.add_candidate_skill("data_candidate", "Python", "intermediate", 2)
        self.graph_service.candidate_repository.add_candidate_skill("data_candidate", "Statistics", "advanced", 4)
        
        # Web development candidate
        candidate_ids.append(self._add_test_candidate("web_candidate", "Frontend Developer", 
                           "Frontend developer with React experience"))
        self.graph_service.candidate_repository.add_candidate_skill("web_candidate", "JavaScript", "advanced", 3)
        self.graph_service.candidate_repository.add_candidate_skill("web_candidate", "React", "intermediate", 2)
        self.graph_service.candidate_repository.add_candidate_skill("web_candidate", "HTML", "advanced", 5)
        self.graph_service.candidate_repository.add_candidate_skill("web_candidate", "CSS", "advanced", 5)
        
        # Test 1: Verify GraphService directly returns jobs from database
        graph_jobs = []
        for job_id in job_ids:
            job = self.graph_service.job_repository.get_job(job_id)
            self.assertIsNotNone(job)
            graph_jobs.append(job)
            
        # Test 2: Verify GraphService directly returns candidates from database
        graph_candidates = []
        for candidate_id in candidate_ids:
            candidate = self.graph_service.candidate_repository.get_candidate(candidate_id)
            self.assertIsNotNone(candidate)
            graph_candidates.append(candidate)
            
        # Test 3: Verify direct graph relationships via GraphService
        # Get skills for a job
        job_skills = self.graph_service.job_repository.get_job_skills("data_job")
        self.assertIsNotNone(job_skills)
        self.assertGreaterEqual(len(job_skills), 3)  # At least 3 skills for data job
        
        # Verify Machine Learning is among the job skills
        ml_job_skill = next((s for s in job_skills if s.get("name") == "Machine Learning"), None)
        self.assertIsNotNone(ml_job_skill, "Machine Learning skill was not found in the job skills")
        
        # Get skills for a candidate
        candidate_skills = self.graph_service.candidate_repository.get_candidate_skills("web_candidate")
        self.assertIsNotNone(candidate_skills)
        self.assertGreaterEqual(len(candidate_skills), 4)  # At least 4 skills for web candidate
        
        # Test 4: Verify MatchingService correctly uses GraphService for job matching
        matching_jobs = self.matcher.match_candidate_to_jobs("data_candidate")
        
        # Verify results
        self.assertIsNotNone(matching_jobs)
        self.assertGreaterEqual(len(matching_jobs), 1)
        
        # Data candidate should match data job better than web job
        data_job_match = next((j for j in matching_jobs if j.get("job_id") == "data_job"), None)
        web_job_match = next((j for j in matching_jobs if j.get("job_id") == "web_job"), None)
        
        self.assertIsNotNone(data_job_match)
        if web_job_match:  # If web job match exists, it should have lower score
            self.assertGreater(data_job_match["match_percentage"], web_job_match["match_percentage"])
        
        # Verify match contains both graph-based and text-based scores from hybrid matching
        self.assertIn("graph_percentage", data_job_match)
        self.assertIn("text_percentage", data_job_match)
        
        # Test 5: Verify MatchingService correctly uses GraphService for candidate matching
        matching_candidates = self.matcher.match_job_to_candidates("web_job")
        
        # Verify results
        self.assertIsNotNone(matching_candidates)
        self.assertGreaterEqual(len(matching_candidates), 1)
        
        # Web job should match web candidate better than data candidate
        web_candidate_match = next((c for c in matching_candidates if c.get("resume_id") == "web_candidate"), None)
        data_candidate_match = next((c for c in matching_candidates if c.get("resume_id") == "data_candidate"), None)
        
        self.assertIsNotNone(web_candidate_match)
        if data_candidate_match:  # If data candidate match exists, it should have lower score
            self.assertGreater(web_candidate_match["match_percentage"], data_candidate_match["match_percentage"])
        
        # Test 6: Verify skill recommendations use both services correctly
        print("\nFetching skill recommendations...")
        recommended_skills = self.matcher.recommend_skills_for_job("data_candidate", "data_job")
        
        # Verify results
        self.assertIsNotNone(recommended_skills)
        print(f"Recommended skills: {recommended_skills}")
        
        # Print job requirements for debugging
        with self.graph_service.driver.session() as session:
            # Query to debug the recommendation system
            debug_query = """
                MATCH (j:Job {job_id: 'data_job'})-[r:REQUIRES_PRIMARY]->(s:Skill)
                WHERE NOT (s)<-[:HAS_CORE_SKILL|HAS_SECONDARY_SKILL]-(:Candidate {resume_id: 'data_candidate'})
                RETURN s.name as skill_name, r.importance as importance
            """
            missing_skills = session.run(debug_query).data()
            print(f"Missing skills that should be recommended: {missing_skills}")
            
            query = """
                MATCH (j:Job {job_id: 'data_job'})-[r]->(s:Skill)
                RETURN j.job_id, s.name, type(r) as relationship, r.proficiency, r.importance
            """
            job_skills = session.run(query).data()
            print(f"Job skills: {job_skills}")
            
            query = """
                MATCH (c:Candidate {resume_id: 'data_candidate'})-[r]->(s:Skill)
                RETURN c.resume_id, s.name, type(r) as relationship, r.proficiency, r.experience_years
            """
            candidate_skills = session.run(query).data()
            print(f"Candidate skills: {candidate_skills}")
            
            query = """
                MATCH (s1:Skill)-[r]->(s2:Skill)
                RETURN s1.name, type(r) as relationship, s2.name
            """
            skill_relationships = session.run(query).data()
            print(f"Skill relationships: {skill_relationships}")
        
        # Machine Learning should be recommended since it's required by data_job but not in data_candidate skills
        ml_recommendation = next((s for s in recommended_skills if s.get("name") == "Machine Learning"), None)
        if ml_recommendation is None:
            print("ERROR: Machine Learning not found in recommendations!")
            print("All recommended skills:", [s.get("name") for s in recommended_skills])
        self.assertIsNotNone(ml_recommendation, "Machine Learning skill was not recommended")
        
        # Test 7: Verify skill path traversal uses both services correctly
        # There should be a path from Statistics to Machine Learning based on our relationships
        path = self.matcher.get_skill_path("Machine Learning", "Statistics")
        print(f"\nSkill path: {path}")
        
        # Verify results
        self.assertIsNotNone(path)
        self.assertGreaterEqual(len(path.get("skill_names", [])), 2)  # Should include at least Machine Learning and Statistics


if __name__ == '__main__':
    # Use TextTestRunner with verbose output for better debugging
    import unittest
    # Configure the test runner
    runner = unittest.TextTestRunner(verbosity=2)
    # Create a test suite with just our problematic tests
    suite = unittest.TestSuite()
    
    # Add the failing tests
    suite.addTest(TestMatcherIntegration('test_match_candidate_to_jobs_integration'))
    suite.addTest(TestMatcherIntegration('test_graph_and_matching_service_integration'))
    
    # Run the suite
    runner.run(suite)
    
    # Or run all tests
    # unittest.main() 