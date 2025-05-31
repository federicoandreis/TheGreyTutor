"""
GraphRAG retrieval package.

This package provides functionality for retrieving information from a Neo4j
knowledge graph using various strategies, including entity-centric and
path-based approaches.
"""

from .config import get_config, set_config, GraphRAGConfig
from .models import (
    Node, Relationship, Path, QueryRequest, QueryResult,
    EntityMatch, PathMatch, RetrievalStrategy
)
from .neo4j_client import get_client, set_client, Neo4jClient

__all__ = [
    'get_config', 'set_config', 'GraphRAGConfig',
    'Node', 'Relationship', 'Path', 'QueryRequest', 'QueryResult',
    'EntityMatch', 'PathMatch', 'RetrievalStrategy',
    'get_client', 'set_client', 'Neo4jClient',
]

# Import cache_manager if it exists
try:
    from .cache_manager import get_cache_manager, set_cache_manager, cached
    __all__.extend(['get_cache_manager', 'set_cache_manager', 'cached'])
except ImportError:
    pass
