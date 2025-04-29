"""
Base Repository for Knowledge Graph
This module provides the base repository class for database operations.
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Load environment variables
load_dotenv()

class BaseRepository:
    """Base repository class for Neo4j database operations."""
    
    def __init__(self, driver=None, uri=None, user=None, password=None):
        """Initialize the repository with Neo4j connection.
        
        Args:
            driver: An existing Neo4j driver instance
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        if driver:
            self.driver = driver
        else:
            self.uri = uri or NEO4J_URI
            self.user = user or NEO4J_USER
            self.password = password or NEO4J_PASSWORD
            self.connect()
    
    def connect(self):
        """Connect to the Neo4j database."""
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
    def close(self):
        """Close the connection to Neo4j."""
        if self.driver:
            self.driver.close()
            
    def get_session(self):
        """Get a new session from the driver.
        
        Returns:
            Neo4j session object
        """
        return self.driver.session()
    
    def execute_query(self, query, parameters=None):
        """Execute a Cypher query and return the results.
        
        Args:
            query: Cypher query string
            parameters: Dictionary of query parameters
            
        Returns:
            List of records as dictionaries
        """
        with self.get_session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def execute_write_query(self, query, parameters=None):
        """Execute a write query with transaction handling.
        
        Args:
            query: Cypher query string
            parameters: Dictionary of query parameters
            
        Returns:
            Result summary
        """
        with self.get_session() as session:
            # Use a transaction function that collects records before consuming the result
            def run_query(tx):
                result = tx.run(query, parameters or {})
                # Collect any results before the transaction closes
                records = list(result)
                summary = result.consume()
                return summary
                
            return session.execute_write(run_query)
    
    def execute_read_query(self, query, parameters=None):
        """Execute a read query with transaction handling.
        
        Args:
            query: Cypher query string
            parameters: Dictionary of query parameters
            
        Returns:
            List of records as dictionaries
        """
        try:
            with self.get_session() as session:
                # Use a transaction function that properly collects all records
                def run_query(tx):
                    try:
                        result = tx.run(query, parameters or {})
                        # Collect all records before the transaction closes
                        return [dict(record) for record in result]
                    except Exception as e:
                        print(f"Error executing query: {str(e)}")
                        print(f"Query: {query}")
                        print(f"Parameters: {parameters}")
                        return []
                        
                return session.execute_read(run_query)
        except Exception as e:
            print(f"Database error in execute_read_query: {str(e)}")
            print(f"Query: {query}")
            print(f"Parameters: {parameters}")
            return [] 