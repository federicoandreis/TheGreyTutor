#!/usr/bin/env python3
"""
GraphRAG Retriever - A simple, working retrieval system for Neo4j knowledge graphs.

This script provides multiple retrieval strategies for answering questions using a Neo4j knowledge graph.
It builds on the existing kg_query_utils.py infrastructure and provides a clean, testable interface.

Usage:
    python graphrag_retriever.py "Who is Frodo?" --strategy entity
    python graphrag_retriever.py "How is Frodo related to Bilbo?" --strategy relationship
    python graphrag_retriever.py "Tell me about the One Ring" --strategy hybrid
"""

import sys
import os
import argparse
import json
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from kg_query_utils import execute_query, format_node_for_display

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result of a retrieval operation."""
    strategy: str
    query: str
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    paths: List[Dict[str, Any]]
    execution_time: float
    total_results: int
    metadata: Dict[str, Any]


class SimpleCache:
    """Simple file-based cache for query results."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, query: str, strategy: str, params: Dict[str, Any]) -> str:
        """Generate a cache key for the query."""
        import hashlib
        content = f"{query}:{strategy}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, query: str, strategy: str, params: Dict[str, Any]) -> Optional[RetrievalResult]:
        """Get cached result."""
        cache_key = self._get_cache_key(query, strategy, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return RetrievalResult(**data)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        return None
    
    def set(self, query: str, strategy: str, params: Dict[str, Any], result: RetrievalResult):
        """Cache result."""
        cache_key = self._get_cache_key(query, strategy, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(asdict(result), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")


class EntityCentricRetriever:
    """Entity-centric retrieval strategy."""
    
    def retrieve(self, query: str, max_results: int = 10) -> RetrievalResult:
        """Retrieve information about entities mentioned in the query."""
        start_time = time.time()
        
        # Extract potential entities (simple approach: capitalized words)
        entities = self._extract_entities(query)
        
        nodes = []
        relationships = []
        paths = []
        
        # Search for each entity
        for entity in entities:
            # Search for nodes matching the entity - using a safer approach
            cypher = """
            MATCH (n)
            WHERE n.name CONTAINS $entity 
               OR (n.title IS NOT NULL AND n.title CONTAINS $entity)
               OR (n.description IS NOT NULL AND n.description CONTAINS $entity)
            RETURN n
            LIMIT $limit
            """
            
            records = execute_query(cypher, {"entity": entity, "limit": max_results})
            
            for record in records:
                node = record["n"]
                formatted_node = format_node_for_display(node, entity)
                nodes.append(formatted_node)
        
        # Remove duplicates
        unique_nodes = {}
        for node in nodes:
            if node["id"] not in unique_nodes:
                unique_nodes[node["id"]] = node
        
        nodes = list(unique_nodes.values())
        
        execution_time = time.time() - start_time
        
        return RetrievalResult(
            strategy="entity_centric",
            query=query,
            nodes=nodes,
            relationships=relationships,
            paths=paths,
            execution_time=execution_time,
            total_results=len(nodes),
            metadata={"entities_found": entities}
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract potential entities from the query."""
        words = query.split()
        entities = []
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,?!;:"\'()')
            
            # Check if it's capitalized but not at the start of the sentence
            if clean_word and clean_word[0].isupper() and word != words[0]:
                entities.append(clean_word)
        
        return entities


class RelationshipAwareRetriever:
    """Relationship-aware retrieval strategy."""
    
    def retrieve(self, query: str, max_results: int = 10, max_depth: int = 3) -> RetrievalResult:
        """Retrieve relationships between entities mentioned in the query."""
        start_time = time.time()
        
        # Extract potential entities
        entities = self._extract_entities(query)
        
        nodes = []
        relationships = []
        paths = []
        
        if len(entities) >= 2:
            # Find relationships between entity pairs
            for i in range(len(entities) - 1):
                for j in range(i + 1, len(entities)):
                    entity1, entity2 = entities[i], entities[j]
                    
                    # Find paths between entities - using safer property matching
                    cypher = """
                    MATCH (n1), (n2)
                    WHERE (n1.name CONTAINS $entity1 OR 
                           (n1.title IS NOT NULL AND n1.title CONTAINS $entity1))
                    AND (n2.name CONTAINS $entity2 OR 
                         (n2.title IS NOT NULL AND n2.title CONTAINS $entity2))
                    AND n1 <> n2
                    MATCH path = shortestPath((n1)-[*1..3]-(n2))
                    RETURN path
                    LIMIT $limit
                    """
                    
                    records = execute_query(cypher, {
                        "entity1": entity1, 
                        "entity2": entity2, 
                        "limit": max_results
                    })
                    
                    for record in records:
                        path = record["path"]
                        path_info = self._format_path(path)
                        paths.append(path_info)
                        
                        # Extract nodes and relationships from path
                        for node in path.nodes:
                            formatted_node = format_node_for_display(node, query)
                            nodes.append(formatted_node)
                        
                        for rel in path.relationships:
                            rel_info = {
                                "id": rel.element_id if hasattr(rel, 'element_id') else str(rel.id),
                                "type": rel.type,
                                "properties": dict(rel)
                            }
                            relationships.append(rel_info)
        
        elif len(entities) == 1:
            # Find related nodes for single entity
            entity = entities[0]
            
            cypher = """
            MATCH (n)-[r]-(related)
            WHERE n.name CONTAINS $entity 
               OR (n.title IS NOT NULL AND n.title CONTAINS $entity)
            RETURN n, r, related
            LIMIT $limit
            """
            
            records = execute_query(cypher, {"entity": entity, "limit": max_results})
            
            for record in records:
                # Add source node
                node = record["n"]
                formatted_node = format_node_for_display(node, entity)
                nodes.append(formatted_node)
                
                # Add related node
                related = record["related"]
                formatted_related = format_node_for_display(related, query)
                nodes.append(formatted_related)
                
                # Add relationship
                rel = record["r"]
                rel_info = {
                    "id": rel.element_id if hasattr(rel, 'element_id') else str(rel.id),
                    "type": rel.type,
                    "properties": dict(rel)
                }
                relationships.append(rel_info)
        
        # Remove duplicates
        unique_nodes = {}
        unique_rels = {}
        
        for node in nodes:
            if node["id"] not in unique_nodes:
                unique_nodes[node["id"]] = node
        
        for rel in relationships:
            if rel["id"] not in unique_rels:
                unique_rels[rel["id"]] = rel
        
        nodes = list(unique_nodes.values())
        relationships = list(unique_rels.values())
        
        execution_time = time.time() - start_time
        
        return RetrievalResult(
            strategy="relationship_aware",
            query=query,
            nodes=nodes,
            relationships=relationships,
            paths=paths,
            execution_time=execution_time,
            total_results=len(nodes) + len(relationships) + len(paths),
            metadata={"entities_found": entities}
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract potential entities from the query."""
        words = query.split()
        entities = []
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,?!;:"\'()')
            
            # Check if it's capitalized but not at the start of the sentence
            if clean_word and clean_word[0].isupper() and word != words[0]:
                entities.append(clean_word)
        
        return entities
    
    def _format_path(self, path) -> Dict[str, Any]:
        """Format a Neo4j path for display."""
        nodes = []
        relationships = []
        
        for node in path.nodes:
            formatted_node = format_node_for_display(node)
            nodes.append(formatted_node)
        
        for rel in path.relationships:
            # Get the start and end node IDs to determine direction
            start_id = rel.start_node.element_id if hasattr(rel.start_node, 'element_id') else str(rel.start_node.id)
            end_id = rel.end_node.element_id if hasattr(rel.end_node, 'element_id') else str(rel.end_node.id)
            
            rel_info = {
                "id": rel.element_id if hasattr(rel, 'element_id') else str(rel.id),
                "type": rel.type,
                "start_node": start_id,
                "end_node": end_id,
                "properties": dict(rel)
            }
            relationships.append(rel_info)
        
        return {
            "length": len(path.relationships),
            "nodes": nodes,
            "relationships": relationships
        }


class HybridRetriever:
    """Hybrid retrieval strategy combining entity-centric and relationship-aware approaches."""
    
    def __init__(self):
        self.entity_retriever = EntityCentricRetriever()
        self.relationship_retriever = RelationshipAwareRetriever()
    
    def retrieve(self, query: str, max_results: int = 10) -> RetrievalResult:
        """Retrieve using both entity-centric and relationship-aware strategies."""
        start_time = time.time()
        
        # Get results from both strategies
        entity_result = self.entity_retriever.retrieve(query, max_results // 2)
        relationship_result = self.relationship_retriever.retrieve(query, max_results // 2)
        
        # Combine results
        all_nodes = entity_result.nodes + relationship_result.nodes
        all_relationships = relationship_result.relationships
        all_paths = relationship_result.paths
        
        # Remove duplicates
        unique_nodes = {}
        unique_rels = {}
        
        for node in all_nodes:
            if node["id"] not in unique_nodes:
                unique_nodes[node["id"]] = node
        
        for rel in all_relationships:
            if rel["id"] not in unique_rels:
                unique_rels[rel["id"]] = rel
        
        nodes = list(unique_nodes.values())
        relationships = list(unique_rels.values())
        
        execution_time = time.time() - start_time
        
        return RetrievalResult(
            strategy="hybrid",
            query=query,
            nodes=nodes,
            relationships=relationships,
            paths=all_paths,
            execution_time=execution_time,
            total_results=len(nodes) + len(relationships) + len(all_paths),
            metadata={
                "entity_results": len(entity_result.nodes),
                "relationship_results": len(relationship_result.nodes) + len(relationship_result.relationships)
            }
        )


class PathRAGRetriever:
    """PathRAG-inspired retriever that uses community detection and path-based retrieval.
    
    This retriever implements the PathRAG approach by:
    1. Using community detection to find relevant entity clusters
    2. Identifying paths between entities through the knowledge graph
    3. Pruning paths to reduce redundancy and improve relevance
    4. Formatting paths in a way that preserves context and relationships
    
    Args:
        max_communities: Maximum number of communities to retrieve (default: 5)
        max_path_length: Maximum path length in hops (default: 3)
        max_paths_per_entity: Maximum paths to retrieve per entity pair (default: 5)
        use_community_detection: Whether to use community detection (default: True)
        
    Note:
        These default parameters were determined through parameter tuning to optimize
        for both coverage and relevance while maintaining good performance.
    """
    
    def __init__(self, max_communities: int = 5, max_path_length: int = 3, 
                 max_paths_per_entity: int = 5, use_community_detection: bool = True):
        self.entity_labels = ["Character", "Location", "Artifact", "Organization", "Event"]
        self.relationship_types = [
            "PARENT_OF", "CHILD_OF", "MARRIED_TO", "RULES", "SERVES", 
            "ALLIES_WITH", "OPPOSES", "MEMBER_OF", "LEADS", "LOCATED_IN", 
            "DWELLS_IN", "TRAVELS_TO", "OWNS", "WIELDS", "CREATES", 
            "PARTICIPATES_IN", "TAKES_PLACE_IN", "MENTORS", "KNOWS_ABOUT", "CREATED_BY"
        ]
        # Tunable parameters
        self.max_communities = max_communities
        self.max_path_length = max_path_length
        self.max_paths_per_entity = max_paths_per_entity
        self.use_community_detection = use_community_detection
    
    def retrieve(self, query: str, max_results: int = 10) -> RetrievalResult:
        """Retrieve information using the PathRAG approach."""
        start_time = time.time()
        
        # 1. Extract entities from the query
        entities = self._extract_entities(query)
        logger.info(f"Extracted entities: {entities}")
        
        # 2. Find communities containing these entities
        communities = self._find_relevant_communities(entities)
        logger.info(f"Found {len(communities)} relevant communities")
        
        # 3. Extract key entities from these communities
        community_entities = self._extract_community_entities(communities)
        logger.info(f"Extracted {len(community_entities)} key entities from communities")
        
        # 4. Find paths between query entities and community entities
        paths = self._find_paths(entities, community_entities)
        logger.info(f"Found {len(paths)} paths")
        
        # 5. Prune paths to reduce redundancy
        pruned_paths = self._prune_paths(paths)
        logger.info(f"Pruned to {len(pruned_paths)} paths")
        
        # 6. Extract nodes and relationships from paths
        nodes, relationships = self._extract_nodes_and_relationships(pruned_paths)
        
        execution_time = time.time() - start_time
        
        return RetrievalResult(
            strategy="pathrag",
            query=query,
            nodes=nodes,
            relationships=relationships,
            paths=pruned_paths,
            execution_time=execution_time,
            total_results=len(nodes) + len(relationships) + len(pruned_paths),
            metadata={
                "entities": entities,
                "communities": [c["id"] for c in communities],
                "community_entities": community_entities
            }
        )
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract potential entities from the query with multi-word support."""
        words = query.split()
        entities = []
        
        # Extract single capitalized words
        for i, word in enumerate(words):
            # Remove punctuation
            clean_word = word.strip('.,?!;:"\'\'()')
            
            # Check if it's capitalized (but not at the start of the sentence unless it's a proper noun)
            if clean_word and clean_word[0].isupper() and (i > 0 or len(clean_word) > 3):
                entities.append(clean_word)
        
        # Extract multi-word entities (e.g., "Bilbo Baggins", "War of the Ring")
        i = 0
        while i < len(words) - 1:
            # If current word is capitalized, check if it's part of a multi-word entity
            current_word = words[i].strip('.,?!;:"\'\'()')
            if current_word and current_word[0].isupper():
                # Try to find the longest multi-word entity
                found_multi_word = False
                for j in range(min(4, len(words) - i), 1, -1):  # Try up to 4-word entities
                    potential_entity = ' '.join(word.strip('.,?!;:"\'\'()') for word in words[i:i+j])
                    # Add if all words are capitalized or common connectors
                    if all(w[0].isupper() or w.lower() in ['of', 'the', 'and', 'in', 'to', 'son', 'daughter'] 
                           for w in potential_entity.split() if w):
                        entities.append(potential_entity)
                        i += j - 1  # Skip the words we just added
                        found_multi_word = True
                        break
                if not found_multi_word:
                    i += 1
            else:
                i += 1
        
        # Remove duplicates while preserving order
        unique_entities = []
        for entity in entities:
            if entity not in unique_entities:
                unique_entities.append(entity)
        
        return unique_entities
    
    def _find_relevant_communities(self, entities: List[str]) -> List[Dict[str, Any]]:
        """Find communities that contain the extracted entities."""
        if not entities or not self.use_community_detection:
            return []
        
        communities = []
        
        # Build a query to find communities containing any of the entities
        query = """
        MATCH (n)
        WHERE (n.name IN $entities OR 
              ANY(alias IN n.aliases WHERE alias IN $entities))
        MATCH (n)-[:BELONGS_TO_COMMUNITY]->(c:Community)
        RETURN DISTINCT c.id AS id, c.name AS name, c.summary AS summary, 
               c.node_count AS node_count, c.node_types AS node_types
        ORDER BY c.node_count DESC
        LIMIT $max_communities
        """
        
        result = execute_query(query, {
            "entities": entities,
            "max_communities": self.max_communities
        })
        
        for record in result:
            communities.append({
                "id": record.get("id"),
                "name": record.get("name"),
                "summary": record.get("summary"),
                "node_count": record.get("node_count"),
                "node_types": record.get("node_types")
            })
        
        return communities
    
    def _extract_community_entities(self, communities: List[Dict[str, Any]]) -> List[str]:
        """Extract key entities from the identified communities."""
        if not communities:
            return []
        
        community_ids = [c["id"] for c in communities]
        entities = []
        
        # Find the most central entities in each community
        query = """
        MATCH (n)-[:BELONGS_TO_COMMUNITY]->(c:Community)
        WHERE c.id IN $community_ids
        WITH n, c
        MATCH (n)-[r]-()
        WITH n, count(r) AS rel_count, c
        ORDER BY rel_count DESC
        RETURN n.name AS name, labels(n) AS labels, rel_count, c.id AS community_id
        LIMIT 15
        """
        
        result = execute_query(query, {"community_ids": community_ids})
        
        for record in result:
            name = record.get("name")
            if name and name not in entities:
                entities.append(name)
        
        return entities
    
    def _find_paths(self, query_entities: List[str], community_entities: List[str]) -> List[Dict[str, Any]]:
        """Find paths between query entities and community entities."""
        if not query_entities or not community_entities:
            return []
        
        paths = []
        
        # For each query entity, find paths to community entities
        for query_entity in query_entities:
            # Build a query to find paths
            query = """
            MATCH (source)
            WHERE (source.name = $source_entity OR $source_entity IN source.aliases)
            MATCH (target) 
            WHERE (target.name IN $target_entities OR 
                  ANY(alias IN target.aliases WHERE alias IN $target_entities))
            AND source <> target
            MATCH path = shortestPath((source)-[*..{max_path_length}]-(target))
            RETURN path
            LIMIT $max_paths_per_entity
            """.format(max_path_length=self.max_path_length)
            
            result = execute_query(query, {
                "source_entity": query_entity,
                "target_entities": community_entities,
                "max_paths_per_entity": self.max_paths_per_entity
            })
            
            for record in result:
                path = record.get("path")
                if path:
                    formatted_path = self._format_path(path)
                    paths.append(formatted_path)
        
        return paths
    
    def _format_path(self, path) -> Dict[str, Any]:
        """Format a path for display, preserving node and relationship information."""
        nodes = []
        relationships = []
        
        for node in path.nodes:
            formatted_node = format_node_for_display(node)
            nodes.append(formatted_node)
        
        for rel in path.relationships:
            start_id = rel.start_node.element_id if hasattr(rel.start_node, 'element_id') else str(rel.start_node.id)
            end_id = rel.end_node.element_id if hasattr(rel.end_node, 'element_id') else str(rel.end_node.id)
            rel_info = {
                "id": rel.element_id if hasattr(rel, 'element_id') else str(rel.id),
                "type": rel.type,
                "start_node": start_id,
                "end_node": end_id,
                "properties": dict(rel)
            }
            relationships.append(rel_info)
        
        return {
            "length": len(path.relationships),
            "nodes": nodes,
            "relationships": relationships
        }
    
    def _prune_paths(self, paths: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prune paths to reduce redundancy and improve relevance."""
        if not paths:
            return []
        
        # Sort paths by length (shorter paths first)
        sorted_paths = sorted(paths, key=lambda p: p["length"])
        
        # Keep track of nodes we've already covered
        covered_nodes = set()
        pruned_paths = []
        
        for path in sorted_paths:
            # Check if this path adds new information
            path_nodes = set(node["id"] for node in path["nodes"])
            new_nodes = path_nodes - covered_nodes
            
            # If the path adds at least one new node, keep it
            if new_nodes:
                pruned_paths.append(path)
                covered_nodes.update(path_nodes)
            
            # Limit to a reasonable number of paths
            if len(pruned_paths) >= 5:
                break
        
        return pruned_paths
    
    def _extract_nodes_and_relationships(self, paths: List[Dict[str, Any]]) -> tuple:
        """Extract unique nodes and relationships from paths."""
        unique_nodes = {}
        unique_rels = {}
        
        for path in paths:
            for node in path["nodes"]:
                unique_nodes[node["id"]] = node
            
            for rel in path["relationships"]:
                unique_rels[rel["id"]] = rel
        
        return list(unique_nodes.values()), list(unique_rels.values())


class GraphRAGRetriever:
    """Main GraphRAG retriever class.
    
    Args:
        use_cache: Whether to use caching for query results (default: True)
        pathrag_max_communities: Maximum number of communities for PathRAG (default: 5)
        pathrag_max_path_length: Maximum path length for PathRAG (default: 3)
        pathrag_max_paths_per_entity: Maximum paths per entity for PathRAG (default: 5)
        pathrag_use_community_detection: Whether to use community detection in PathRAG (default: True)
        
    Note:
        The default PathRAG parameters were determined through parameter tuning to optimize
        for both coverage and relevance while maintaining good performance.
    """
    
    def __init__(self, use_cache: bool = True, 
                 pathrag_max_communities: int = 5,
                 pathrag_max_path_length: int = 3,
                 pathrag_max_paths_per_entity: int = 5,
                 pathrag_use_community_detection: bool = True):
        self.cache = SimpleCache() if use_cache else None
        self.strategies = {
            "entity": EntityCentricRetriever(),
            "relationship": RelationshipAwareRetriever(),
            "hybrid": HybridRetriever(),
            "pathrag": PathRAGRetriever(
                max_communities=pathrag_max_communities,
                max_path_length=pathrag_max_path_length,
                max_paths_per_entity=pathrag_max_paths_per_entity,
                use_community_detection=pathrag_use_community_detection
            )
        }
    
    def retrieve(self, query: str, strategy: str = "hybrid", max_results: int = 10) -> RetrievalResult:
        """Retrieve information from the knowledge graph."""
        if strategy not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy}. Available: {list(self.strategies.keys())}")
        
        # Check cache
        cache_params = {"max_results": max_results}
        if self.cache:
            cached_result = self.cache.get(query, strategy, cache_params)
            if cached_result:
                logger.info(f"Cache hit for query: {query}")
                return cached_result
        
        # Execute retrieval
        logger.info(f"Executing {strategy} strategy for query: {query}")
        result = self.strategies[strategy].retrieve(query, max_results)
        
        # Cache result
        if self.cache:
            self.cache.set(query, strategy, cache_params, result)
        
        return result
    
    def print_result(self, result: RetrievalResult, verbose: bool = False):
        """Print retrieval result in a readable format."""
        print("\n=== GraphRAG Retrieval Result ===")
        print(f"Query: {result.query}")
        print(f"Strategy: {result.strategy}")
        print(f"Execution Time: {result.execution_time:.3f}s")
        print(f"Total Results: {result.total_results}")
        
        # Print metadata with improved formatting
        if result.metadata:
            print("\n--- Metadata ---")
            for key, value in result.metadata.items():
                if isinstance(value, list):
                    if len(value) > 10:  # Truncate long lists
                        formatted_value = ', '.join(str(v) for v in value[:10]) + f"... ({len(value)} total)"
                    else:
                        formatted_value = ', '.join(str(v) for v in value)
                    print(f"  {key}: {formatted_value}")
                else:
                    print(f"  {key}: {value}")
        
        # Print nodes with improved formatting
        if result.nodes:
            print(f"\n--- Nodes ({len(result.nodes)}) ---")
            for i, node in enumerate(result.nodes):
                # Get node name or ID
                node_name = node["properties"].get("name", node["id"])
                if isinstance(node_name, list):
                    node_name = ', '.join(str(n) for n in node_name)
                
                # Format labels
                labels = ', '.join(node['labels'])
                
                print(f"\nNode {i+1}: {node_name} ({labels})")
                
                # Print properties if verbose
                if node["properties"] and verbose:
                    for prop, value in node["properties"].items():
                        if prop != "name":  # Skip name as it's already displayed
                            if isinstance(value, list):
                                value = ', '.join(str(v) for v in value)
                            print(f"  {prop}: {value}")
                    
                    if "matched_in" in node:
                        print(f"  [Matched in: {', '.join(node['matched_in'])}]")
        # Print relationships
        if result.relationships:
            print(f"\n--- Relationships ({len(result.relationships)}) ---")
            for i, rel in enumerate(result.relationships):
                print(f"\nRelationship {i+1}: {rel['type']} (ID: {rel['id']})")
                
                if rel["properties"] and verbose:
                    for prop, value in rel["properties"].items():
                        print(f"  {prop}: {value}")
        
        # Print paths with improved formatting
        if result.paths:
            print(f"\n--- Paths ({len(result.paths)}) ---")
            for i, path in enumerate(result.paths):
                print(f"\nPath {i+1}: Length {path['length']}")
                
                for j, node in enumerate(path["nodes"]):
                    node_name = node["properties"].get("name", node["id"])
                    if isinstance(node_name, list):
                        node_name = ', '.join(str(n) for n in node_name)
                    print(f"  Node {j+1}: {node_name} ({', '.join(node['labels'])})")
                    
                    if j < path["length"]:
                        rel = path["relationships"][j]
                        # Get the start and end node IDs to determine direction
                        start_id = rel.get('start_node')
                        end_id = rel.get('end_node')
                        
                        # Determine if this relationship points to the next node or from it
                        next_node_id = path["nodes"][j+1]["id"] if j+1 < len(path["nodes"]) else None
                        
                        if start_id == node["id"] and end_id == next_node_id:
                            # Current node is start, next node is end
                            print(f"  → {rel['type']} →")
                        elif end_id == node["id"] and start_id == next_node_id:
                            # Current node is end, next node is start
                            print(f"  ← {rel['type']} ←")
                        elif start_id == node["id"]:
                            # Current node is start but end is not the next node
                            print(f"  → {rel['type']} →")
                        elif end_id == node["id"]:
                            # Current node is end but start is not the next node
                            print(f"  ← {rel['type']} ←")
                        else:
                            # Direction can't be determined clearly
                            print(f"  ↔ {rel['type']} ↔")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="GraphRAG Retriever for Neo4j Knowledge Graphs")
    parser.add_argument("query", help="Question to answer")
    parser.add_argument("--strategy", choices=["entity", "relationship", "hybrid", "pathrag"], 
                       default="hybrid", help="Retrieval strategy to use")
    parser.add_argument("--max-results", type=int, default=10, 
                       help="Maximum number of results to return")
    parser.add_argument("--no-cache", action="store_true", 
                       help="Disable caching")
    parser.add_argument("--verbose", action="store_true", 
                       help="Show detailed output")
    parser.add_argument("--output", choices=["text", "json"], default="text",
                       help="Output format")
    
    args = parser.parse_args()
    
    try:
        # Initialize retriever
        retriever = GraphRAGRetriever(use_cache=not args.no_cache)
        
        # Execute retrieval
        result = retriever.retrieve(
            query=args.query,
            strategy=args.strategy,
            max_results=args.max_results
        )
        
        # Output result
        if args.output == "json":
            print(json.dumps(asdict(result), indent=2))
        else:
            retriever.print_result(result, verbose=args.verbose)
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
