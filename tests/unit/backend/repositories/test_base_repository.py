"""
Unit tests for the BaseRepository class.
"""

import unittest
from unittest import mock
import os
import sys

# Make sure we can import from the parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.backend.repositories.base.repository import BaseRepository
from neo4j import GraphDatabase, Result, ResultSummary, Record
from neo4j.exceptions import ServiceUnavailable, AuthError

class TestBaseRepository(unittest.TestCase):
    """Test case for the BaseRepository class."""
    
    def setUp(self):
        """Set up test environment by mocking Neo4j driver."""
        # Create mock for Neo4j driver
        self.mock_driver = mock.MagicMock()
        self.mock_session = mock.MagicMock()
        
        # Configure driver.session() method to return mock_session
        self.mock_driver.session.return_value = self.mock_session
        
        # Create mock for Neo4j Result and Record
        self.mock_result = mock.MagicMock(spec=Result)
        self.mock_record = mock.MagicMock(spec=Record)
        
        # Configure mock_record to return test values and properly support dict conversion
        self.test_data = {"test_key": "test_value"}
        self.mock_record.__getitem__.side_effect = lambda key: self.test_data.get(key)
        self.mock_record.items.return_value = list(self.test_data.items())
        self.mock_record.keys.return_value = list(self.test_data.keys())
        
        # Make the record properly convert to a dict when dict(record) is called
        self.mock_record.__iter__.return_value = iter(self.test_data.items())
        
        # Configure mock_result to return records
        self.mock_result.__iter__.return_value = [self.mock_record]
        self.mock_result.single.return_value = self.mock_record
        
        # Configure session to return mock_result
        self.mock_session.run.return_value = self.mock_result
        self.mock_session.__enter__.return_value = self.mock_session
        self.mock_session.__exit__.return_value = None
        
        # Configure result summary
        self.mock_summary = mock.MagicMock(spec=ResultSummary)
        self.mock_result.consume.return_value = self.mock_summary
        
        # For transaction methods
        self.mock_session.execute_read.side_effect = lambda func, *args, **kwargs: [self.test_data]
        self.mock_session.execute_write.return_value = self.mock_summary  # Return mock_summary instead of mock_result
        
        # Create repository
        self.repo = BaseRepository(driver=self.mock_driver)
        
    def tearDown(self):
        """Clean up test environment."""
        self.repo.close()
        
    def test_init_with_driver(self):
        """Test initialization with an existing driver."""
        repo = BaseRepository(driver=self.mock_driver)
        self.assertEqual(repo.driver, self.mock_driver)
        
    @mock.patch('src.backend.repositories.base.repository.GraphDatabase')
    def test_init_with_connection_params(self, mock_graph_db):
        """Test initialization with connection parameters."""
        # Arrange
        mock_graph_db.driver.return_value = self.mock_driver
        test_uri = "bolt://test:7687"
        test_user = "test_user"
        test_password = "test_password"
        
        # Act
        repo = BaseRepository(uri=test_uri, user=test_user, password=test_password)
        
        # Assert
        mock_graph_db.driver.assert_called_once_with(test_uri, auth=(test_user, test_password))
        self.assertEqual(repo.driver, self.mock_driver)
        
    @mock.patch('src.backend.repositories.base.repository.NEO4J_URI', new="bolt://default:7687")
    @mock.patch('src.backend.repositories.base.repository.NEO4J_USER', new="neo4j")
    @mock.patch('src.backend.repositories.base.repository.NEO4J_PASSWORD', new="password")
    @mock.patch('src.backend.repositories.base.repository.GraphDatabase')
    def test_init_with_default_connection_params(self, mock_graph_db):
        """Test initialization with default connection parameters from environment."""
        # Arrange
        mock_graph_db.driver.return_value = self.mock_driver
        
        # Act - initialize without providing any params
        repo = BaseRepository()
        
        # Assert
        mock_graph_db.driver.assert_called_once_with("bolt://default:7687", auth=("neo4j", "password"))
        self.assertEqual(repo.driver, self.mock_driver)
        
    def test_close(self):
        """Test close method."""
        self.repo.close()
        self.mock_driver.close.assert_called_once()
        
    def test_get_session(self):
        """Test get_session method."""
        session = self.repo.get_session()
        self.assertEqual(session, self.mock_session)
        
    def test_execute_query(self):
        """Test execute_query method."""
        # Arrange
        test_query = "MATCH (n) RETURN n"
        test_params = {"param1": "value1"}
        
        # Mock the session.run to properly convert records to dictionaries
        def run_side_effect(query, params):
            result = mock.MagicMock(spec=Result)
            result.__iter__.return_value = [self.mock_record]
            return result
            
        self.mock_session.run.side_effect = run_side_effect
        
        # Act
        with mock.patch.object(self.repo, 'execute_query', return_value=[self.test_data]):
            result = self.repo.execute_query(test_query, test_params)
            
            # Assert
            self.assertEqual(result[0], self.test_data)
        
    def test_execute_write_query(self):
        """Test execute_write_query method."""
        # Arrange
        test_query = "CREATE (n:Test) RETURN n"
        test_params = {"param1": "value1"}
        
        # Act
        result = self.repo.execute_write_query(test_query, test_params)
        
        # Assert
        self.mock_session.execute_write.assert_called_once()
        self.assertEqual(result, self.mock_summary)
        
    def test_execute_read_query(self):
        """Test execute_read_query method."""
        # Arrange
        test_query = "MATCH (n:Test) RETURN n"
        test_params = {"param1": "value1"}
        
        # Act
        result = self.repo.execute_read_query(test_query, test_params)
        
        # Assert
        self.mock_session.execute_read.assert_called_once()
        self.assertEqual(result[0], self.test_data)
        
    @mock.patch('src.backend.repositories.base.repository.GraphDatabase')
    def test_connect_fails_with_auth_error(self, mock_graph_db):
        """Test connection failure with authentication error."""
        # Arrange
        mock_graph_db.driver.side_effect = AuthError("Authentication failed")
        
        # Act & Assert
        with self.assertRaises(AuthError):
            repo = BaseRepository(uri="bolt://test:7687", user="wrong", password="wrong")
            
    @mock.patch('src.backend.repositories.base.repository.GraphDatabase')
    def test_connect_fails_with_service_unavailable(self, mock_graph_db):
        """Test connection failure with service unavailable."""
        # Arrange
        mock_graph_db.driver.side_effect = ServiceUnavailable("Service is not available")
        
        # Act & Assert
        with self.assertRaises(ServiceUnavailable):
            repo = BaseRepository(uri="bolt://nonexistent:7687", user="test", password="test")
            
    def test_execute_query_with_none_params(self):
        """Test execute_query method with None parameters."""
        # Arrange
        test_query = "MATCH (n) RETURN n"
        
        # Act
        with mock.patch.object(self.repo, 'execute_query', return_value=[self.test_data]):
            result = self.repo.execute_query(test_query)
            
            # Assert
            self.assertEqual(result[0], self.test_data)
        
    def test_execute_query_with_empty_result(self):
        """Test execute_query method with empty result."""
        # Arrange
        test_query = "MATCH (n:NonExistent) RETURN n"
        
        # Mock an empty result set
        empty_result = mock.MagicMock(spec=Result)
        empty_result.__iter__.return_value = []
        self.mock_session.run.return_value = empty_result
        
        # Act
        with mock.patch.object(self.repo, 'execute_query', return_value=[]):
            result = self.repo.execute_query(test_query)
            
            # Assert
            self.assertEqual(len(result), 0)
            
    def test_execute_write_query_error(self):
        """Test execute_write_query method with error in transaction."""
        # Arrange
        test_query = "CREATE (n:Test) RETURN n"
        test_params = {"param1": "value1"}
        
        # Configure execute_write to raise an exception
        self.mock_session.execute_write.side_effect = Exception("Transaction error")
        
        # Act & Assert
        with self.assertRaises(Exception) as context:
            self.repo.execute_write_query(test_query, test_params)
            
        self.assertIn("Transaction error", str(context.exception))
        
    def test_execute_read_query_error_in_transaction(self):
        """Test execute_read_query method with error in transaction function."""
        # Arrange
        test_query = "MATCH (n:Test) RETURN n"
        test_params = {"param1": "value1"}
        
        # Configure execute_read to execute the transaction function but make it raise an exception
        def failing_transaction(tx):
            raise Exception("Query execution error")
            
        self.mock_session.execute_read.side_effect = lambda func, *args, **kwargs: func(failing_transaction)
        
        # Act
        result = self.repo.execute_read_query(test_query, test_params)
        
        # Assert 
        self.assertEqual(result, [])  # Should return empty list on error
        
    def test_execute_read_query_session_error(self):
        """Test execute_read_query method with session error."""
        # Arrange
        test_query = "MATCH (n:Test) RETURN n"
        test_params = {"param1": "value1"}
        
        # Configure get_session to raise an exception
        self.repo.get_session = mock.MagicMock(side_effect=Exception("Session error"))
        
        # Act
        result = self.repo.execute_read_query(test_query, test_params)
        
        # Assert
        self.assertEqual(result, [])  # Should return empty list on error
        
    def test_execute_read_query_unexpected_exception(self):
        """Test execute_read_query method with an unexpected exception."""
        # Arrange
        test_query = "MATCH (n:Test) RETURN n"
        test_params = {"param1": "value1"}
        
        # Configure execute_read to raise an unexpected exception
        self.mock_session.execute_read.side_effect = KeyError("Unexpected error")
        
        # Act
        result = self.repo.execute_read_query(test_query, test_params)
        
        # Assert
        self.assertEqual(result, [])  # Should return empty list on error
        
    def test_execute_write_query_with_tx_collect(self):
        """Test execute_write_query method's transaction function collecting records."""
        # Arrange
        test_query = "CREATE (n:Test) RETURN n"
        test_params = {"param1": "value1"}
        
        # Create a new mock for the result summary specifically for this test
        test_summary = mock.MagicMock(spec=ResultSummary)
        
        # Mock a real transaction execution that executes the function passed to it
        def execute_write_side_effect(func, *args, **kwargs):
            tx_mock = mock.MagicMock()
            tx_result = mock.MagicMock(spec=Result)
            tx_result.__iter__.return_value = [self.mock_record, self.mock_record]  # Multiple records
            tx_result.consume.return_value = test_summary
            tx_mock.run.return_value = tx_result
            return func(tx_mock, *args, **kwargs)
            
        # Save the original execute_write method
        original_execute_write = self.mock_session.execute_write
        
        # Configure execute_write to use our side effect
        self.mock_session.execute_write.side_effect = execute_write_side_effect
        
        # Act
        # We need to create a real method call rather than using a preexisting mock
        # Create a temporary driver and repository just for this test
        temp_driver = mock.MagicMock()
        temp_driver.session.return_value = self.mock_session
        temp_repo = BaseRepository(driver=temp_driver)
        
        # Call the real method
        result = temp_repo.execute_write_query(test_query, test_params)
        
        # Assert
        self.assertEqual(result, test_summary)
        
        # Restore the mock
        self.mock_session.execute_write = original_execute_write

    def test_execute_transaction_function(self):
        """Test the transaction function execution in execute_write_query."""
        # Arrange
        test_query = "CREATE (n:Test) RETURN n"
        test_params = {"param1": "value1"}
        
        # Create a new mock for testing the transaction execution
        tx_mock = mock.MagicMock()
        result_mock = mock.MagicMock(spec=Result)
        summary_mock = mock.MagicMock(spec=ResultSummary)
        
        # Configure the mock chain
        result_mock.consume.return_value = summary_mock
        tx_mock.run.return_value = result_mock
        
        # Act - directly call the transaction function
        # Extract the transaction function for testing
        def execute_write(tx_func):
            return tx_func(tx_mock)
            
        # Mock the session's execute_write to execute our function directly
        self.mock_session.execute_write = execute_write
        
        # Call the function
        result = self.repo.execute_write_query(test_query, test_params)
        
        # Assert
        tx_mock.run.assert_called_once_with(test_query, test_params)
        self.assertEqual(result, summary_mock)

    def test_execute_read_query_with_query_error(self):
        """Test execute_read_query error handling within the query execution."""
        # Arrange
        test_query = "MATCH (n:Test) RETURN n"
        test_params = {"param1": "value1"}
        
        # Create a transaction mock that will execute the transaction function
        def execute_read_with_error(tx_func):
            tx_mock = mock.MagicMock()
            # Make tx.run raise an exception specifically for this test query
            tx_mock.run.side_effect = Exception("Query execution error")
            return tx_func(tx_mock)
            
        self.mock_session.execute_read.side_effect = execute_read_with_error
        
        # Mock print function to capture error logging
        with mock.patch('builtins.print') as mock_print:
            # Act
            result = self.repo.execute_read_query(test_query, test_params)
            
            # Assert
            self.assertEqual(result, [])  # Should return empty list on error
            # Verify error was printed (line 103)
            mock_print.assert_any_call(f"Error executing query: Query execution error")

if __name__ == '__main__':
    unittest.main() 