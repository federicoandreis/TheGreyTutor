"""
Data models for GraphRAG retrieval.

This module defines the data models used throughout the GraphRAG system.
"""

from typing import Dict, List, Any, Optional, Union, Set
from enum import Enum
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Types of nodes in the knowledge graph."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DOCUMENT = "document"
    EVENT = "event"
    PRODUCT = "product"
    CONCEPT = "concept"
    UNKNOWN = "unknown"


class RelationshipType(str, Enum):
    """Types of relationships in the knowledge graph."""
    BELONGS_TO = "belongs_to"
    PART_OF = "part_of"
    CREATED_BY = "created_by"
    LOCATED_IN = "located_in"
    RELATED_TO = "related_to"
    DEPENDS_ON = "depends_on"
    CAUSES = "causes"
    INSTANCE_OF = "instance_of"
    UNKNOWN = "unknown"


class RetrievalStrategy(str, Enum):
    """Types of retrieval strategies."""
    ENTITY_CENTRIC = "entity_centric"
    RELATIONSHIP_AWARE = "relationship_aware"
    SUBGRAPH_EXTRACTION = "subgraph_extraction"
    HYBRID_SEARCH = "hybrid_search"
    MULTI_HOP = "multi_hop"
    PATH_BASED = "path_based"


class Node(BaseModel):
    """
    A node in the knowledge graph.
    
    Attributes:
        id: Node ID
        labels: Node labels
        properties: Node properties
        node_type: Type of node
    """
    id: str
    labels: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)
    node_type: str = NodeType.UNKNOWN
    
    def get_name(self) -> str:
        """
        Get the name of the node.
        
        Returns:
            Node name or ID if not available
        """
        # Try common name properties
        for prop in ["name", "title", "label"]:
            if prop in self.properties:
                value = self.properties[prop]
                if isinstance(value, str):
                    return value
                elif isinstance(value, list) and len(value) > 0:
                    return str(value[0])
        
        # Fall back to ID
        return self.id
    
    def get_description(self) -> str:
        """
        Get the description of the node.
        
        Returns:
            Node description or empty string if not available
        """
        # Try common description properties
        for prop in ["description", "content", "text", "summary"]:
            if prop in self.properties:
                value = self.properties[prop]
                if isinstance(value, str):
                    return value
                elif isinstance(value, list) and len(value) > 0:
                    return str(value[0])
        
        # Fall back to empty string
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the node to a dictionary.
        
        Returns:
            Dictionary representation of the node
        """
        return {
            "id": self.id,
            "labels": self.labels,
            "properties": self.properties,
            "node_type": self.node_type
        }


class Relationship(BaseModel):
    """
    A relationship in the knowledge graph.
    
    Attributes:
        id: Relationship ID
        type: Relationship type
        source_id: Source node ID
        target_id: Target node ID
        properties: Relationship properties
    """
    id: str
    type: str
    source_id: str
    target_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the relationship to a dictionary.
        
        Returns:
            Dictionary representation of the relationship
        """
        return {
            "id": self.id,
            "type": self.type,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "properties": self.properties
        }


class Path(BaseModel):
    """
    A path in the knowledge graph.
    
    Attributes:
        nodes: List of nodes in the path
        relationships: List of relationships in the path
        relevance_score: Relevance score of the path
    """
    nodes: List[Node] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    relevance_score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the path to a dictionary.
        
        Returns:
            Dictionary representation of the path
        """
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "relationships": [rel.to_dict() for rel in self.relationships],
            "relevance_score": self.relevance_score
        }


class QueryParameters(BaseModel):
    """
    Parameters for a query.
    
    Attributes:
        search_text: Text to search for
        node_ids: List of node IDs to include
        labels: List of labels to filter by
        properties: List of properties to search in
        rel_types: List of relationship types to consider
        max_depth: Maximum path depth
        max_results: Maximum number of results to return
        similarity_threshold: Minimum similarity threshold
    """
    search_text: Optional[str] = None
    node_ids: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    properties: List[str] = Field(default_factory=list)
    rel_types: List[str] = Field(default_factory=list)
    max_depth: int = 2
    max_results: int = 10
    similarity_threshold: float = 0.7


class QueryResult(BaseModel):
    """
    Result of a query.
    
    Attributes:
        nodes: List of nodes in the result
        relationships: List of relationships in the result
        paths: List of paths in the result
        query_time: Time taken to execute the query in seconds
        total_results: Total number of results
        strategy: Retrieval strategy used
    """
    nodes: List[Node] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    paths: List[Path] = Field(default_factory=list)
    query_time: float = 0.0
    total_results: int = 0
    strategy: str = RetrievalStrategy.ENTITY_CENTRIC
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the query result to a dictionary.
        
        Returns:
            Dictionary representation of the query result
        """
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "relationships": [rel.to_dict() for rel in self.relationships],
            "paths": [path.to_dict() for path in self.paths],
            "query_time": self.query_time,
            "total_results": self.total_results,
            "strategy": self.strategy
        }


class EntityInfo(BaseModel):
    """
    Information about an entity.
    
    Attributes:
        name: Entity name
        entity_type: Entity type
        properties: Entity properties
        confidence: Confidence score
    """
    name: str
    entity_type: str = NodeType.UNKNOWN
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0


class RelationshipInfo(BaseModel):
    """
    Information about a relationship.
    
    Attributes:
        source: Source entity name
        target: Target entity name
        relationship_type: Relationship type
        properties: Relationship properties
        confidence: Confidence score
    """
    source: str
    target: str
    relationship_type: str = RelationshipType.RELATED_TO
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0


class QuestionAnalysis(BaseModel):
    """
    Analysis of a question.
    
    Attributes:
        entities: List of entities in the question
        relationships: List of relationships in the question
        keywords: List of keywords in the question
        complexity: Complexity of the question (1-5)
    """
    entities: List[EntityInfo] = Field(default_factory=list)
    relationships: List[RelationshipInfo] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    complexity: int = 1


class RetrievalRequest(BaseModel):
    """
    Request for retrieving information from the knowledge graph.
    
    Attributes:
        query: Query text
        strategy: Retrieval strategy to use
        parameters: Query parameters
    """
    query: str
    strategy: str = RetrievalStrategy.ENTITY_CENTRIC
    parameters: QueryParameters = Field(default_factory=QueryParameters)


class RetrievalResponse(BaseModel):
    """
    Response from retrieving information from the knowledge graph.
    
    Attributes:
        query: Original query text
        strategy: Retrieval strategy used
        results: Query results
        analysis: Question analysis
    """
    query: str
    strategy: str
    results: QueryResult
    analysis: Optional[QuestionAnalysis] = None
