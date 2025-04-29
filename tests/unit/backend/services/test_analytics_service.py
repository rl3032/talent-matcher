"""
Unit tests for the analytics service.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import datetime

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.services.analytics_service import AnalyticsService
from src.backend.repositories.job_repository import JobRepository
from src.backend.repositories.candidate_repository import CandidateRepository
from src.backend.repositories.skill_repository import SkillRepository


class TestAnalyticsService(unittest.TestCase):
    """Test case for AnalyticsService."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock graph service with a mock driver
        self.mock_driver = MagicMock()
        self.mock_graph_service = MagicMock()
        self.mock_graph_service.driver = self.mock_driver
        
        # Create the service with the mock graph service
        self.analytics_service = AnalyticsService(graph_service=self.mock_graph_service)
        
        # Replace the repositories with mocks
        self.mock_job_repo = MagicMock(spec=JobRepository)
        self.mock_candidate_repo = MagicMock(spec=CandidateRepository)
        self.mock_skill_repo = MagicMock(spec=SkillRepository)
        
        self.analytics_service.job_repository = self.mock_job_repo
        self.analytics_service.candidate_repository = self.mock_candidate_repo
        self.analytics_service.skill_repository = self.mock_skill_repo
        
        # Sample data for tests
        self.sample_jobs = [
            {
                'job_id': 'job_1',
                'title': 'Software Engineer',
                'company': 'Tech Corp',
                'location': 'San Francisco',
                'salary_min': 80000,
                'salary_max': 120000,
                'active': True,
                'required_skills': [
                    {'skill_id': 'skill_1', 'name': 'Python', 'proficiency': 'Advanced', 'importance': 0.8},
                    {'skill_id': 'skill_2', 'name': 'JavaScript', 'proficiency': 'Intermediate', 'importance': 0.6}
                ],
                'category': 'Software Development',
                'created_at': datetime.datetime(2023, 1, 15).isoformat()
            },
            {
                'job_id': 'job_2',
                'title': 'Data Scientist',
                'company': 'Data Insights',
                'location': 'New York',
                'salary_min': 90000,
                'salary_max': 130000,
                'active': True,
                'required_skills': [
                    {'skill_id': 'skill_1', 'name': 'Python', 'proficiency': 'Advanced', 'importance': 0.9},
                    {'skill_id': 'skill_3', 'name': 'Machine Learning', 'proficiency': 'Advanced', 'importance': 0.8}
                ],
                'category': 'Data Science',
                'created_at': datetime.datetime(2023, 2, 10).isoformat()
            }
        ]
        
        self.sample_candidates = [
            {
                'resume_id': 'resume_1',
                'name': 'John Doe',
                'location': 'San Francisco',
                'skills': [
                    {'skill_id': 'skill_1', 'name': 'Python', 'proficiency': 'Intermediate', 'years': 2},
                    {'skill_id': 'skill_2', 'name': 'JavaScript', 'proficiency': 'Intermediate', 'years': 3}
                ],
                'active': True,
                'created_at': datetime.datetime(2023, 1, 20).isoformat()
            },
            {
                'resume_id': 'resume_2',
                'name': 'Jane Smith',
                'location': 'New York',
                'skills': [
                    {'skill_id': 'skill_1', 'name': 'Python', 'proficiency': 'Advanced', 'years': 4},
                    {'skill_id': 'skill_3', 'name': 'Machine Learning', 'proficiency': 'Beginner', 'years': 1}
                ],
                'active': True,
                'created_at': datetime.datetime(2023, 2, 15).isoformat()
            }
        ]
        
        self.sample_skills = [
            {
                'skill_id': 'skill_1',
                'name': 'Python',
                'category': 'Programming',
                'description': 'Python programming language'
            },
            {
                'skill_id': 'skill_2',
                'name': 'JavaScript',
                'category': 'Programming',
                'description': 'JavaScript programming language'
            },
            {
                'skill_id': 'skill_3',
                'name': 'Machine Learning',
                'category': 'Data Science',
                'description': 'Machine learning algorithms and techniques'
            }
        ]
        
        # Sample related skills
        self.sample_related_skills = [
            {
                'skill_id': 'skill_4',
                'name': 'Data Analysis',
                'relationship_type': 'RELATED_TO',
                'weight': 0.8
            },
            {
                'skill_id': 'skill_5',
                'name': 'Statistics',
                'relationship_type': 'REQUIRED_FOR',
                'weight': 0.7
            }
        ]
        
        # Sample session for Neo4j driver
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__.return_value = self.mock_session

    def test_get_skill_gap_analysis(self):
        """Test getting skill gap analysis."""
        # Set up repository mocks
        job_id = 'job_1'
        resume_id = 'resume_1'
        
        self.mock_candidate_repo.get_candidate.return_value = self.sample_candidates[0]
        self.mock_job_repo.get_job.return_value = self.sample_jobs[0]
        
        # For this test, we'll add one missing skill for the candidate
        job_skills = [
            {'skill_id': 'skill_1', 'name': 'Python', 'proficiency': 'Advanced', 'importance': 0.8},
            {'skill_id': 'skill_2', 'name': 'JavaScript', 'proficiency': 'Intermediate', 'importance': 0.6},
            {'skill_id': 'skill_6', 'name': 'React', 'proficiency': 'Intermediate', 'importance': 0.5}
        ]
        self.mock_job_repo.get_job_skills.return_value = job_skills
        
        candidate_skills = [
            {'skill_id': 'skill_1', 'name': 'Python', 'proficiency': 'Intermediate', 'years': 2},
            {'skill_id': 'skill_2', 'name': 'JavaScript', 'proficiency': 'Intermediate', 'years': 3}
        ]
        self.mock_candidate_repo.get_candidate_skills.return_value = candidate_skills
        
        # Call the service method
        result = self.analytics_service.get_skill_gap_analysis(resume_id, job_id)
        
        # Verify the result
        self.assertTrue(result['success'])
        self.assertIn('analysis', result)
        
        analysis = result['analysis']
        self.assertEqual(analysis['job_id'], job_id)
        self.assertEqual(analysis['resume_id'], resume_id)
        self.assertTrue(0 <= analysis['gap_score'] <= 100)
        
        # Check for missing skills
        self.assertIn('missing_skills', analysis)
        self.assertEqual(len(analysis['missing_skills']), 1)  # React should be missing
        self.assertEqual(analysis['missing_skills'][0]['name'], 'React')
        
        # Check for proficiency gaps
        self.assertIn('proficiency_gaps', analysis)
        self.assertEqual(len(analysis['proficiency_gaps']), 1)  # Python: Advanced vs Intermediate
        self.assertEqual(analysis['proficiency_gaps'][0]['name'], 'Python')
        
        # Verify repository methods were called
        self.mock_candidate_repo.get_candidate.assert_called_once_with(resume_id)
        self.mock_job_repo.get_job.assert_called_once_with(job_id)
        self.mock_candidate_repo.get_candidate_skills.assert_called_once_with(resume_id)
        self.mock_job_repo.get_job_skills.assert_called_once_with(job_id)

    def test_get_skill_recommendations(self):
        """Test getting skill recommendations."""
        # Set up mocks - we'll reuse the gap analysis setup
        job_id = 'job_1'
        resume_id = 'resume_1'
        
        # Mock the get_skill_gap_analysis to return a fixed result
        gap_analysis = {
            'success': True,
            'analysis': {
                'job_id': job_id,
                'job_title': 'Software Engineer',
                'resume_id': resume_id,
                'candidate_name': 'John Doe',
                'gap_score': 70.0,
                'missing_skills': [
                    {
                        'skill_id': 'skill_6',
                        'name': 'React',
                        'category': 'Frontend',
                        'importance': 0.5,
                        'proficiency': 'Intermediate'
                    }
                ],
                'proficiency_gaps': [
                    {
                        'skill_id': 'skill_1',
                        'name': 'Python',
                        'candidate_proficiency': 'Intermediate',
                        'job_proficiency': 'Advanced',
                        'importance': 0.8
                    }
                ],
                'total_required_skills': 3,
                'missing_skill_count': 1
            }
        }
        
        # Patch the method to return our fixed result
        with patch.object(self.analytics_service, 'get_skill_gap_analysis', return_value=gap_analysis):
            # Set up related skills
            self.mock_skill_repo.get_related_skills.return_value = self.sample_related_skills
            
            # Call the service method
            result = self.analytics_service.get_skill_recommendations(resume_id, job_id)
            
            # Verify the result
            self.assertTrue(result['success'])
            self.assertIn('recommendations', result)
            
            recommendations = result['recommendations']
            self.assertEqual(recommendations['job_id'], job_id)
            self.assertEqual(recommendations['resume_id'], resume_id)
            self.assertEqual(recommendations['gap_score'], 70.0)
            
            # Check for recommended skills
            self.assertIn('skills', recommendations)
            self.assertEqual(len(recommendations['skills']), 1)  # Should recommend React
            self.assertEqual(recommendations['skills'][0]['name'], 'React')
            
            # Each recommendation should have related skills and learning resources
            for skill in recommendations['skills']:
                self.assertIn('related_skills', skill)
                self.assertIn('learning_resources', skill)
            
            # Verify repository methods were called
            self.mock_skill_repo.get_related_skills.assert_called_once_with('skill_6')

    def test_get_career_path(self):
        """Test getting career path."""
        # Set up mock for Neo4j session
        current_title = "Software Engineer"
        target_title = "Engineering Manager"
        
        # Create a mock result for the Neo4j query
        mock_record = MagicMock()
        mock_record.get.side_effect = lambda key: {
            "titles": ["Software Engineer", "Senior Software Engineer", "Engineering Manager"],
            "salaries": [100000, 130000, 160000],
            "transitions": [50, 30],
            "path_length": 2
        }[key]
        
        # Set up the mock session to return our mock record
        self.mock_session.run.return_value = [mock_record]
        
        # Call the service method
        result = self.analytics_service.get_career_path(current_title, target_title)
        
        # Verify the result
        self.assertTrue(result['success'])
        self.assertIn('paths', result)
        self.assertEqual(len(result['paths']), 1)
        
        path = result['paths'][0]
        self.assertEqual(path['titles'], ["Software Engineer", "Senior Software Engineer", "Engineering Manager"])
        self.assertEqual(path['salaries'], [100000, 130000, 160000])
        self.assertEqual(path['transitions'], [50, 30])
        self.assertEqual(path['length'], 2)
        
        # Verify the session was used correctly
        self.mock_driver.session.assert_called_once()
        self.mock_session.run.assert_called_once()

    def test_get_dashboard_stats(self):
        """Test getting dashboard statistics."""
        # Set up mock for Neo4j session
        # We need multiple query results
        
        # Job count query
        mock_job_record = MagicMock()
        mock_job_record.__getitem__.side_effect = lambda key: {
            "job_count": 100,
            "company_count": 30
        }[key]
        mock_job_result = MagicMock()
        mock_job_result.single.return_value = mock_job_record
        
        # Candidate count query
        mock_candidate_record = MagicMock()
        mock_candidate_record.__getitem__.side_effect = lambda key: {
            "candidate_count": 200
        }[key]
        mock_candidate_result = MagicMock()
        mock_candidate_result.single.return_value = mock_candidate_record
        
        # Skills query
        mock_skill_records = [
            {"skill_name": "Python", "usage_count": 50},
            {"skill_name": "JavaScript", "usage_count": 40}
        ]
        mock_skill_result = [MagicMock(**record) for record in mock_skill_records]
        
        # Recent matches query
        mock_match_records = [
            {
                "job_id": "job_1",
                "job_title": "Software Engineer",
                "resume_id": "resume_1",
                "candidate_name": "John Doe",
                "match_score": 0.85
            },
            {
                "job_id": "job_2",
                "job_title": "Data Scientist",
                "resume_id": "resume_2",
                "candidate_name": "Jane Smith",
                "match_score": 0.78
            }
        ]
        mock_match_result = [MagicMock(**record) for record in mock_match_records]
        
        # Set up the mock session to return our mock results
        self.mock_session.run.side_effect = [
            mock_job_result,
            mock_candidate_result,
            mock_skill_result,
            mock_match_result
        ]
        
        # Call the service method
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        result = self.analytics_service.get_dashboard_stats(start_date, end_date)
        
        # Verify the result
        self.assertTrue(result['success'])
        self.assertIn('stats', result)
        
        stats = result['stats']
        self.assertEqual(stats['job_count'], 100)
        self.assertEqual(stats['candidate_count'], 200)
        self.assertEqual(stats['company_count'], 30)
        self.assertIn('top_skills', stats)
        self.assertIn('recent_matches', stats)
        self.assertIn('date_range', stats)
        
        # Verify the session was used correctly
        self.assertEqual(self.mock_driver.session.call_count, 1)
        self.assertEqual(self.mock_session.run.call_count, 4)

    def test_get_learning_resources(self):
        """Test getting learning resources (private method)."""
        skill_id = 'skill_1'
        
        # Call the private method directly
        resources = self.analytics_service._get_learning_resources(skill_id)
        
        # Verify the result
        self.assertEqual(len(resources), 2)
        self.assertIn("url", resources[0])
        self.assertIn("title", resources[0])
        self.assertIn("provider", resources[0])
        self.assertIn("type", resources[0])

    def test_get_instance(self):
        """Test getting singleton instance."""
        # Create a mock graph service
        mock_graph_svc = MagicMock()
        
        # Get service instance
        service1 = AnalyticsService.get_instance(mock_graph_svc)
        service2 = AnalyticsService.get_instance()
        
        # Verify both are the same instance
        self.assertIs(service1, service2)


if __name__ == '__main__':
    unittest.main() 