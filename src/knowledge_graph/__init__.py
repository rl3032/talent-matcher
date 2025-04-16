"""
Knowledge Graph package for Talent Matcher
This package provides functionality for building and querying a skill-based knowledge graph.
"""

from .model import KnowledgeGraph
from .matcher import KnowledgeGraphMatcher
from src.etl.data_loader import initialize_knowledge_graph 