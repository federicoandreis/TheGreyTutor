"""
Retrieval strategies for GraphRAG.

This module provides different strategies for retrieving information from the knowledge graph.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from abc import ABC, abstractmethod

from .models import (
    Node, Relationship, Path, QueryParameters, QueryResult,
    RetrievalStrategy, EntityInfo, RelationshipInfo, QuestionAnalysis
)
from .neo4j_client import get_client
from .cache_manager import cached
from .config import get_config

# Set up logging
logger = logging.getLogger(__name__)


class BaseRetrievalStrategy(ABC):
    """
    Base class for retrieval strategies.
    """
    
    @abstractmethod
    def retrieve(self, query: str, parameters: QueryParameters) -> QueryResult:
        """
        Retrieve information from the knowledge graph.
        
        Args:
            query: Query text
            parameters: Query parameters
            
        Returns:
            Query result
        """
        pass
    
    @abstractmethod
    def analyze_question(self, query: str) -> QuestionAnalysis:
        """
        Analyze a question to extract entities, relationships, and keywords.
        
        Args:
            query: Query text
            
        Returns:
            Question analysis
        """
        pass


class EntityCentricStrategy(BaseRetrievalStrategy):
    """
    Entity-centric retrieval strategy.
    
    This strategy focuses on retrieving information about specific entities.
    """
    
    @cached()
    def retrieve(self, query: str, parameters: QueryParameters) -> QueryResult:
        """
        Retrieve information about entities.
        
        Args:
            query: Query text
            parameters: Query parameters
            
        Returns:
            Query result
        """
        start_time = time.time()
        
        # Get Neo4j client
        client = get_client()
        
        # Analyze the question to extract entities
        analysis = self.analyze_question(query)
        
        # Initialize result
        result = QueryResult(
            strategy=RetrievalStrategy.ENTITY_CENTRIC
        )
        
        # If we have entities in the analysis, use them
        if analysis.entities:
            for entity in analysis.entities:
                # Search for nodes matching the entity name
                search_text = entity.name
                labels = parameters.labels or []
                properties = parameters.properties or get_config().retrieval.default_properties
                
                nodes = client.search_nodes(
                    search_text=search_text,
                    labels=labels,
                    properties=properties,
                    limit=parameters.max_results
                )
                
                # Add nodes to result
                result.nodes.extend(nodes)
        else:
            # No entities found, use the query text directly
            search_text = parameters.search_text or query
            labels = parameters.labels or []
            properties = parameters.properties or get_config().retrieval.default_properties
            
            nodes = client.search_nodes(
                search_text=search_text,
                labels=labels,
                properties=properties,
                limit=parameters.max_results
            )
            
            # Add nodes to result
            result.nodes.extend(nodes)
        
        # Remove duplicate nodes
        unique_nodes = {}
        for node in result.nodes:
            if node.id not in unique_nodes:
                unique_nodes[node.id] = node
        
        result.nodes = list(unique_nodes.values())
        result.total_results = len(result.nodes)
        
        # Calculate query time
        result.query_time = time.time() - start_time
        
        return result
    
    def analyze_question(self, query: str) -> QuestionAnalysis:
        """
        Analyze a question to extract entities.
        
        Args:
            query: Query text
            
        Returns:
            Question analysis
        """
        # Simple entity extraction based on capitalized words
        entities = []
        words = query.split()
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,?!;:"\'()')
            
            # Check if it's capitalized but not at the start of the sentence
            if clean_word and clean_word[0].isupper() and word != words[0]:
                entity = EntityInfo(
                    name=clean_word,
                    confidence=0.8
                )
                entities.append(entity)
        
        # Extract keywords (simple approach: just use all words)
        keywords = [word.strip('.,?!;:"\'()').lower() for word in words 
                   if len(word.strip('.,?!;:"\'()')) > 3]
        
        # Estimate complexity based on query length and number of entities
        complexity = min(5, max(1, len(words) // 5 + len(entities)))
        
        return QuestionAnalysis(
            entities=entities,
            keywords=keywords,
            complexity=complexity
        )


class RelationshipAwareStrategy(BaseRetrievalStrategy):
    """
    Relationship-aware retrieval strategy.
    
    This strategy focuses on exploring connections between entities.
    """
    
    @cached()
    def retrieve(self, query: str, parameters: QueryParameters) -> QueryResult:
        """
        Retrieve relationships between entities.
        
        Args:
            query: Query text
            parameters: Query parameters
            
        Returns:
            Query result
        """
        start_time = time.time()
        
        # Get Neo4j client
        client = get_client()
        
        # Analyze the question to extract entities and relationships
        analysis = self.analyze_question(query)
        
        # Initialize result
        result = QueryResult(
            strategy=RetrievalStrategy.RELATIONSHIP_AWARE
        )
        
        # If we have relationships in the analysis, use them
        if analysis.relationships:
            for rel_info in analysis.relationships:
                # First, find nodes matching the source and target
                source_nodes = client.search_nodes(
                    search_text=rel_info.source,
                    limit=5
                )
                
                target_nodes = client.search_nodes(
                    search_text=rel_info.target,
                    limit=5
                )
                
                # If we found both source and target nodes, find paths between them
                if source_nodes and target_nodes:
                    for source_node in source_nodes[:1]:  # Limit to first source node
                        for target_node in target_nodes[:1]:  # Limit to first target node
                            paths = client.find_paths(
                                start_node_id=source_node.id,
                                end_node_id=target_node.id,
                                max_depth=parameters.max_depth,
                                rel_types=parameters.rel_types
                            )
                            
                            # Add paths to result
                            result.paths.extend(paths)
                            
                            # Extract nodes and relationships from paths
                            for path in paths:
                                result.nodes.extend(path.nodes)
                                result.relationships.extend(path.relationships)
        
        # If we have entities but no relationships, find related nodes for each entity
        elif analysis.entities:
            for entity in analysis.entities:
                # Search for nodes matching the entity name
                nodes = client.search_nodes(
                    search_text=entity.name,
                    limit=3
                )
                
                # For each node, find related nodes
                for node in nodes:
                    related = client.find_related_nodes(
                        node_id=node.id,
                        max_depth=parameters.max_depth,
                        rel_types=parameters.rel_types
                    )
                    
                    # Add node to result
                    result.nodes.append(node)
                    
                    # Add related nodes and relationships to result
                    for rel, related_node in related:
                        result.nodes.append(related_node)
                        result.relationships.append(rel)
        
        # Remove duplicate nodes and relationships
        unique_nodes = {}
        unique_relationships = {}
        
        for node in result.nodes:
            if node.id not in unique_nodes:
                unique_nodes[node.id] = node
        
        for rel in result.relationships:
            if rel.id not in unique_relationships:
                unique_relationships[rel.id] = rel
        
        result.nodes = list(unique_nodes.values())
        result.relationships = list(unique_relationships.values())
        result.total_results = len(result.nodes) + len(result.relationships)
        
        # Calculate query time
        result.query_time = time.time() - start_time
        
        return result
    
    def analyze_question(self, query: str) -> QuestionAnalysis:
        """
        Analyze a question to extract entities and relationships.
        
        Args:
            query: Query text
            
        Returns:
            Question analysis
        """
        # Simple entity extraction based on capitalized words
        entities = []
        words = query.split()
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,?!;:"\'()')
            
            # Check if it's capitalized but not at the start of the sentence
            if clean_word and clean_word[0].isupper() and word != words[0]:
                entity = EntityInfo(
                    name=clean_word,
                    confidence=0.8
                )
                entities.append(entity)
        
        # Simple relationship extraction based on pairs of entities
        relationships = []
        
        if len(entities) >= 2:
            for i in range(len(entities) - 1):
                for j in range(i + 1, len(entities)):
                    relationship = RelationshipInfo(
                        source=entities[i].name,
                        target=entities[j].name,
                        confidence=0.7
                    )
                    relationships.append(relationship)
        
        # Extract keywords
        keywords = [word.strip('.,?!;:"\'()').lower() for word in words 
                   if len(word.strip('.,?!;:"\'()')) > 3]
        
        # Estimate complexity based on query length and number of entities/relationships
        complexity = min(5, max(1, len(words) // 5 + len(entities) + len(relationships)))
        
        return QuestionAnalysis(
            entities=entities,
            relationships=relationships,
            keywords=keywords,
            complexity=complexity
        )


class SubgraphExtractionStrategy(BaseRetrievalStrategy):
    """
    Subgraph extraction strategy.
    
    This strategy extracts a relevant subgraph around key entities.
    """
    
    @cached()
    def retrieve(self, query: str, parameters: QueryParameters) -> QueryResult:
        """
        Extract a subgraph around key entities.
        
        Args:
            query: Query text
            parameters: Query parameters
            
        Returns:
            Query result
        """
        start_time = time.time()
        
        # Get Neo4j client
        client = get_client()
        
        # Analyze the question to extract entities
        analysis = self.analyze_question(query)
        
        # Initialize result
        result = QueryResult(
            strategy=RetrievalStrategy.SUBGRAPH_EXTRACTION
        )
        
        # If we have entities in the analysis, use them
        if analysis.entities:
            for entity in analysis.entities[:2]:  # Limit to first 2 entities
                # Search for nodes matching the entity name
                nodes = client.search_nodes(
                    search_text=entity.name,
                    limit=2
                )
                
                # For each node, extract a subgraph
                for node in nodes:
                    subgraph_nodes, subgraph_relationships = client.extract_subgraph(
                        node_id=node.id,
                        max_depth=parameters.max_depth,
                        max_nodes=parameters.max_results
                    )
                    
                    # Add subgraph to result
                    result.nodes.extend(subgraph_nodes)
                    result.relationships.extend(subgraph_relationships)
        else:
            # No entities found, use the query text directly
            search_text = parameters.search_text or query
            nodes = client.search_nodes(
                search_text=search_text,
                limit=2
            )
            
            # For each node, extract a subgraph
            for node in nodes:
                subgraph_nodes, subgraph_relationships = client.extract_subgraph(
                    node_id=node.id,
                    max_depth=parameters.max_depth,
                    max_nodes=parameters.max_results
                )
                
                # Add subgraph to result
                result.nodes.extend(subgraph_nodes)
                result.relationships.extend(subgraph_relationships)
        
        # Remove duplicate nodes and relationships
        unique_nodes = {}
        unique_relationships = {}
        
        for node in result.nodes:
            if node.id not in unique_nodes:
                unique_nodes[node.id] = node
        
        for rel in result.relationships:
            if rel.id not in unique_relationships:
                unique_relationships[rel.id] = rel
        
        result.nodes = list(unique_nodes.values())
        result.relationships = list(unique_relationships.values())
        result.total_results = len(result.nodes) + len(result.relationships)
        
        # Calculate query time
        result.query_time = time.time() - start_time
        
        return result
    
    def analyze_question(self, query: str) -> QuestionAnalysis:
        """
        Analyze a question to extract entities.
        
        Args:
            query: Query text
            
        Returns:
            Question analysis
        """
        # Simple entity extraction based on capitalized words
        entities = []
        words = query.split()
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,?!;:"\'()')
            
            # Check if it's capitalized but not at the start of the sentence
            if clean_word and clean_word[0].isupper() and word != words[0]:
                entity = EntityInfo(
                    name=clean_word,
                    confidence=0.8
                )
                entities.append(entity)
        
        # Extract keywords
        keywords = [word.strip('.,?!;:"\'()').lower() for word in words 
                   if len(word.strip('.,?!;:"\'()')) > 3]
        
        # Estimate complexity based on query length and number of entities
        complexity = min(5, max(1, len(words) // 5 + len(entities)))
        
        return QuestionAnalysis(
            entities=entities,
            keywords=keywords,
            complexity=complexity
        )


class HybridSearchStrategy(BaseRetrievalStrategy):
    """
    Hybrid search strategy.
    
    This strategy combines structural graph queries with semantic search.
    """
    
    @cached()
    def retrieve(self, query: str, parameters: QueryParameters) -> QueryResult:
        """
        Perform a hybrid search combining structural and semantic approaches.
        
        Args:
            query: Query text
            parameters: Query parameters
            
        Returns:
            Query result
        """
        start_time = time.time()
        
        # Get Neo4j client
        client = get_client()
        
        # Analyze the question
        analysis = self.analyze_question(query)
        
        # Initialize result
        result = QueryResult(
            strategy=RetrievalStrategy.HYBRID_SEARCH
        )
        
        # First, perform a structural search using entity-centric strategy
        entity_strategy = EntityCentricStrategy()
        entity_result = entity_strategy.retrieve(query, parameters)
        
        # Add entity-centric results
        result.nodes.extend(entity_result.nodes)
        
        # If we have entities, also try relationship-aware strategy
        if analysis.entities and len(analysis.entities) >= 2:
            relationship_strategy = RelationshipAwareStrategy()
            relationship_result = relationship_strategy.retrieve(query, parameters)
            
            # Add relationship-aware results
            result.nodes.extend(relationship_result.nodes)
            result.relationships.extend(relationship_result.relationships)
            result.paths.extend(relationship_result.paths)
        
        # Remove duplicate nodes and relationships
        unique_nodes = {}
        unique_relationships = {}
        
        for node in result.nodes:
            if node.id not in unique_nodes:
                unique_nodes[node.id] = node
        
        for rel in result.relationships:
            if rel.id not in unique_relationships:
                unique_relationships[rel.id] = rel
        
        result.nodes = list(unique_nodes.values())
        result.relationships = list(unique_relationships.values())
        result.total_results = len(result.nodes) + len(result.relationships)
        
        # Calculate query time
        result.query_time = time.time() - start_time
        
        return result
    
    def analyze_question(self, query: str) -> QuestionAnalysis:
        """
        Analyze a question to extract entities, relationships, and keywords.
        
        Args:
            query: Query text
            
        Returns:
            Question analysis
        """
        # Use the relationship-aware strategy for analysis
        # as it extracts both entities and relationships
        strategy = RelationshipAwareStrategy()
        return strategy.analyze_question(query)


class MultiHopReasoningStrategy(BaseRetrievalStrategy):
    """
    Multi-hop reasoning strategy.
    
    This strategy follows chains of relationships to answer complex questions.
    """
    
    @cached()
    def retrieve(self, query: str, parameters: QueryParameters) -> QueryResult:
        """
        Perform multi-hop reasoning across the knowledge graph.
        
        Args:
            query: Query text
            parameters: Query parameters
            
        Returns:
            Query result
        """
        start_time = time.time()
        
        # Get Neo4j client
        client = get_client()
        
        # Analyze the question
        analysis = self.analyze_question(query)
        
        # Initialize result
        result = QueryResult(
            strategy=RetrievalStrategy.MULTI_HOP
        )
        
        # If we have entities, use them as starting points
        if analysis.entities:
            # First, find nodes matching the entities
            start_nodes = []
            
            for entity in analysis.entities:
                nodes = client.search_nodes(
                    search_text=entity.name,
                    limit=2
                )
                start_nodes.extend(nodes)
            
            # Add start nodes to result
            result.nodes.extend(start_nodes)
            
            # For each pair of start nodes, find paths between them
            if len(start_nodes) >= 2:
                for i in range(len(start_nodes) - 1):
                    for j in range(i + 1, len(start_nodes)):
                        paths = client.find_paths(
                            start_node_id=start_nodes[i].id,
                            end_node_id=start_nodes[j].id,
                            max_depth=parameters.max_depth,
                            rel_types=parameters.rel_types
                        )
                        
                        # Add paths to result
                        result.paths.extend(paths)
                        
                        # Extract nodes and relationships from paths
                        for path in paths:
                            result.nodes.extend(path.nodes)
                            result.relationships.extend(path.relationships)
            
            # If we only have one start node, extract a subgraph around it
            elif len(start_nodes) == 1:
                subgraph_nodes, subgraph_relationships = client.extract_subgraph(
                    node_id=start_nodes[0].id,
                    max_depth=parameters.max_depth,
                    max_nodes=parameters.max_results
                )
                
                # Add subgraph to result
                result.nodes.extend(subgraph_nodes)
                result.relationships.extend(subgraph_relationships)
        else:
            # No entities found, use the query text directly
            search_text = parameters.search_text or query
            nodes = client.search_nodes(
                search_text=search_text,
                limit=3
            )
            
            # Add nodes to result
            result.nodes.extend(nodes)
            
            # For each node, find related nodes
            for node in nodes:
                related = client.find_related_nodes(
                    node_id=node.id,
                    max_depth=parameters.max_depth,
                    rel_types=parameters.rel_types
                )
                
                # Add related nodes and relationships to result
                for rel, related_node in related:
                    result.nodes.append(related_node)
                    result.relationships.append(rel)
        
        # Remove duplicate nodes and relationships
        unique_nodes = {}
        unique_relationships = {}
        
        for node in result.nodes:
            if node.id not in unique_nodes:
                unique_nodes[node.id] = node
        
        for rel in result.relationships:
            if rel.id not in unique_relationships:
                unique_relationships[rel.id] = rel
        
        result.nodes = list(unique_nodes.values())
        result.relationships = list(unique_relationships.values())
        result.total_results = len(result.nodes) + len(result.relationships)
        
        # Calculate query time
        result.query_time = time.time() - start_time
        
        return result
    
    def analyze_question(self, query: str) -> QuestionAnalysis:
        """
        Analyze a question to extract entities, relationships, and keywords.
        
        Args:
            query: Query text
            
        Returns:
            Question analysis
        """
        # Use the relationship-aware strategy for analysis
        # as it extracts both entities and relationships
        strategy = RelationshipAwareStrategy()
        analysis = strategy.analyze_question(query)
        
        # For multi-hop reasoning, we assume higher complexity
        analysis.complexity = min(5, analysis.complexity + 1)
        
        return analysis


class PathBasedStrategy(BaseRetrievalStrategy):
    """
    Path-based retrieval strategy.
    
    This strategy focuses on finding and analyzing paths between entities.
    """
    
    @cached()
    def retrieve(self, query: str, parameters: QueryParameters) -> QueryResult:
        """
        Retrieve paths between entities.
        
        Args:
            query: Query text
            parameters: Query parameters
            
        Returns:
            Query result
        """
        start_time = time.time()
        
        # Get Neo4j client
        client = get_client()
        
        # Analyze the question
        analysis = self.analyze_question(query)
        
        # Initialize result
        result = QueryResult(
            strategy=RetrievalStrategy.PATH_BASED
        )
        
        # If we have entities, use them as endpoints for paths
        if analysis.entities and len(analysis.entities) >= 2:
            # Find nodes matching the entities
            entity_nodes = {}
            
            for entity in analysis.entities:
                nodes = client.search_nodes(
                    search_text=entity.name,
                    limit=2
                )
                
                if nodes:
                    entity_nodes[entity.name] = nodes
            
            # Find paths between entity pairs
            if len(entity_nodes) >= 2:
                entity_pairs = []
                
                # Create pairs of entities
                entity_names = list(entity_nodes.keys())
                for i in range(len(entity_names) - 1):
                    for j in range(i + 1, len(entity_names)):
                        entity_pairs.append((entity_names[i], entity_names[j]))
                
                # Find paths for each pair
                for source_name, target_name in entity_pairs:
                    source_nodes = entity_nodes[source_name]
                    target_nodes = entity_nodes[target_name]
                    
                    for source_node in source_nodes[:1]:  # Limit to first source node
                        for target_node in target_nodes[:1]:  # Limit to first target node
                            paths = client.find_paths(
                                start_node_id=source_node.id,
                                end_node_id=target_node.id,
                                max_depth=parameters.max_depth,
                                rel_types=parameters.rel_types
                            )
                            
                            # Add paths to result
                            result.paths.extend(paths)
                            
                            # Extract nodes and relationships from paths
                            for path in paths:
                                result.nodes.extend(path.nodes)
                                result.relationships.extend(path.relationships)
        
        # If we don't have enough entities for paths, fall back to entity-centric strategy
        if not result.paths:
            entity_strategy = EntityCentricStrategy()
            entity_result = entity_strategy.retrieve(query, parameters)
            
            # Add entity-centric results
            result.nodes.extend(entity_result.nodes)
        
        # Remove duplicate nodes and relationships
        unique_nodes = {}
        unique_relationships = {}
        
        for node in result.nodes:
            if node.id not in unique_nodes:
                unique_nodes[node.id] = node
        
        for rel in result.relationships:
            if rel.id not in unique_relationships:
                unique_relationships[rel.id] = rel
        
        result.nodes = list(unique_nodes.values())
        result.relationships = list(unique_relationships.values())
        result.total_results = len(result.nodes) + len(result.relationships) + len(result.paths)
        
        # Calculate query time
        result.query_time = time.time() - start_time
        
        return result
    
    def analyze_question(self, query: str) -> QuestionAnalysis:
        """
        Analyze a question to extract entities, relationships, and keywords.
        
        Args:
            query: Query text
            
        Returns:
            Question analysis
        """
        # Use the relationship-aware strategy for analysis
        # as it extracts both entities and relationships
        strategy = RelationshipAwareStrategy()
        return strategy.analyze_question(query)


# Strategy factory
def get_strategy(strategy_name: str) -> BaseRetrievalStrategy:
    """
    Get a retrieval strategy by name.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        Retrieval strategy
    """
    strategies = {
        RetrievalStrategy.ENTITY_CENTRIC: EntityCentricStrategy(),
        RetrievalStrategy.RELATIONSHIP_AWARE: RelationshipAwareStrategy(),
        RetrievalStrategy.SUBGRAPH_EXTRACTION: SubgraphExtractionStrategy(),
        RetrievalStrategy.HYBRID_SEARCH: HybridSearchStrategy(),
        RetrievalStrategy.MULTI_HOP: MultiHopReasoningStrategy(),
        RetrievalStrategy.PATH_BASED: PathBasedStrategy()
    }
    
    return strategies.get(strategy_name, EntityCentricStrategy())
