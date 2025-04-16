"""
Unit tests for the API endpoints
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.api.app import app

class TestAPIEndpoints:
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        with app.test_client() as client:
            yield client
    
    @patch('src.api.app.kg.driver.session')
    def test_get_all_jobs(self, mock_session, client):
        """Test getting all jobs endpoint."""
        # Setup mock data
        mock_session_ctx = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_ctx
        
        mock_records = [
            {"job_id": "j1", "title": "Software Engineer", "company": "Tech Inc"},
            {"job_id": "j2", "title": "Data Scientist", "company": "Data Corp"}
        ]
        
        mock_session_ctx.run.return_value = mock_records
        
        # Call the endpoint
        response = client.get('/api/jobs')
        
        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'jobs' in data
        assert len(data['jobs']) == 2
        assert data['jobs'][0]['job_id'] == 'j1'
        assert data['jobs'][1]['title'] == 'Data Scientist'
    
    @patch('src.api.app.kg.driver.session')
    def test_get_all_candidates(self, mock_session, client):
        """Test getting all candidates endpoint."""
        # Setup mock data
        mock_session_ctx = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_ctx
        
        mock_records = [
            {"resume_id": "r1", "name": "John Doe", "title": "Software Engineer"},
            {"resume_id": "r2", "name": "Jane Smith", "title": "Data Scientist"}
        ]
        
        mock_session_ctx.run.return_value = mock_records
        
        # Call the endpoint
        response = client.get('/api/candidates')
        
        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'candidates' in data
        assert len(data['candidates']) == 2
        assert data['candidates'][0]['resume_id'] == 'r1'
        assert data['candidates'][1]['name'] == 'Jane Smith'
    
    @patch('src.api.app.kg.driver.session')
    def test_get_job_by_id(self, mock_session, client):
        """Test getting a job by ID endpoint."""
        # Setup mock data
        mock_session_ctx = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_ctx
        
        job_data = {
            "job_id": "j1", 
            "title": "Software Engineer", 
            "company": "Tech Inc"
        }
        
        skills_data = [
            {"skill_id": "s1", "name": "Python", "category": "languages", "level": 8},
            {"skill_id": "s2", "name": "JavaScript", "category": "languages", "level": 6}
        ]
        
        # Mock the job query result
        job_record = MagicMock()
        job_record.single.return_value = job_data
        
        # Setup the side effect to return different results on each call
        mock_session_ctx.run.side_effect = [job_record, skills_data]
        
        # Call the endpoint
        response = client.get('/api/jobs/j1')
        
        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'job' in data
        assert data['job']['job_id'] == 'j1'
        assert data['job']['title'] == 'Software Engineer'
        assert 'skills' in data
        assert len(data['skills']) == 2
    
    @patch('src.api.app.kg.driver.session')
    def test_get_candidate_by_id(self, mock_session, client):
        """Test getting a candidate by ID endpoint."""
        # Setup mock data
        mock_session_ctx = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_session_ctx
        
        candidate_data = {
            "resume_id": "r1", 
            "name": "John Doe", 
            "title": "Software Engineer"
        }
        
        skills_data = [
            {"skill_id": "s1", "name": "Python", "category": "languages", "level": 4, "years": 3},
            {"skill_id": "s2", "name": "JavaScript", "category": "languages", "level": 3, "years": 2}
        ]
        
        # Mock the candidate query result
        candidate_record = MagicMock()
        candidate_record.single.return_value = candidate_data
        
        # Setup the side effect to return different results on each call
        mock_session_ctx.run.side_effect = [candidate_record, skills_data]
        
        # Call the endpoint
        response = client.get('/api/candidates/r1')
        
        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'candidate' in data
        assert data['candidate']['resume_id'] == 'r1'
        assert data['candidate']['name'] == 'John Doe'
        assert 'skills' in data
        assert len(data['skills']) == 2
    
    @patch('src.api.app.matcher.match_job_to_candidates')
    def test_get_matching_candidates(self, mock_match, client):
        """Test getting matching candidates for a job endpoint."""
        # Setup mock data
        mock_match.return_value = [
            {"resume_id": "r1", "name": "John Doe", "match_percentage": 85.5},
            {"resume_id": "r2", "name": "Jane Smith", "match_percentage": 75.0}
        ]
        
        # Call the endpoint
        response = client.get('/api/jobs/j1/candidates')
        
        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'matches' in data
        assert len(data['matches']) == 2
        assert data['matches'][0]['resume_id'] == 'r1'
        assert data['matches'][0]['match_percentage'] == 85.5
        
        # Verify the matcher was called with correct arguments
        mock_match.assert_called_once_with('j1', limit=10, min_score=0.0)
    
    @patch('src.api.app.matcher.match_candidate_to_jobs')
    def test_get_matching_jobs(self, mock_match, client):
        """Test getting matching jobs for a candidate endpoint."""
        # Setup mock data
        mock_match.return_value = [
            {"job_id": "j1", "title": "Software Engineer", "match_percentage": 90.0},
            {"job_id": "j2", "title": "Data Scientist", "match_percentage": 80.0}
        ]
        
        # Call the endpoint
        response = client.get('/api/candidates/r1/jobs')
        
        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'matches' in data
        assert len(data['matches']) == 2
        assert data['matches'][0]['job_id'] == 'j1'
        assert data['matches'][0]['match_percentage'] == 90.0
        
        # Verify the matcher was called with correct arguments
        mock_match.assert_called_once_with('r1', limit=10, min_score=0.0)
    
    @patch('src.api.app.matcher._get_matching_skills')
    @patch('src.api.app.matcher._get_missing_skills')
    @patch('src.api.app.matcher._get_exceeding_skills')
    def test_get_skill_gap(self, mock_exceeding, mock_missing, mock_matching, client):
        """Test getting skill gap analysis endpoint."""
        # Setup mock data
        mock_matching.return_value = [
            {"skill_id": "s1", "name": "Python", "proficiency": 4, "required_proficiency": 3}
        ]
        mock_missing.return_value = [
            {"skill_id": "s2", "name": "JavaScript", "required_proficiency": 3}
        ]
        mock_exceeding.return_value = [
            {"skill_id": "s3", "name": "Docker", "proficiency": 3}
        ]
        
        # Call the endpoint
        response = client.get('/api/candidates/r1/jobs/j1/skill-gap')
        
        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'matching_skills' in data
        assert 'missing_skills' in data
        assert 'exceeding_skills' in data
        assert len(data['matching_skills']) == 1
        assert len(data['missing_skills']) == 1
        assert len(data['exceeding_skills']) == 1
        
        # Verify the methods were called with correct arguments
        mock_matching.assert_called_once_with('r1', 'j1')
        mock_missing.assert_called_once_with('r1', 'j1')
        mock_exceeding.assert_called_once_with('r1', 'j1')
    
    @patch('src.api.app.matcher.recommend_skills_for_job')
    def test_get_skill_recommendations(self, mock_recommend, client):
        """Test getting skill recommendations endpoint."""
        # Setup mock data
        mock_recommend.return_value = [
            {"skill_id": "s2", "name": "JavaScript", "recommendation_score": 0.85},
            {"skill_id": "s3", "name": "Docker", "recommendation_score": 0.75}
        ]
        
        # Call the endpoint
        response = client.get('/api/candidates/r1/jobs/j1/recommendations')
        
        # Verify
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendations' in data
        assert len(data['recommendations']) == 2
        assert data['recommendations'][0]['skill_id'] == 's2'
        assert data['recommendations'][0]['recommendation_score'] == 0.85
        
        # Verify the method was called with correct arguments
        mock_recommend.assert_called_once_with('r1', 'j1', limit=5) 