"""
Neo4j client for GraphRAG.

This module provides a client for interacting with the Neo4j database.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Set
from neo4j import GraphDatabase, Driver

from .models import Node, Relationship, Path
from .config import get_config

# Set up logging
logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Client for interacting with the Neo4j database.
    """
    
    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize the Neo4j client.
        
        Args:
            uri: Neo4j URI
            username: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.username = username
        self.password = password
        self._driver = None
    
    @property
    def driver(self) -> Driver:
        """
        Get the Neo4j driver.
        
        Returns:
            Neo4j driver
        """
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.username, self.password)
            )
        return self._driver
    
    def close(self):
        """Close the Neo4j driver."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query.
        
        Args:
            query: Cypher query
            params: Query parameters
            
        Returns:
            List of records as dictionaries
        """
        if params is None:
            params = {}
        
        try:
            with self.driver.session() as session:
                result = session.run(query, params)
                records = [dict(record) for record in result]
                return records
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            return []
    
    def search_nodes(
        self, 
        search_text: str, 
        labels: Optional[List[str]] = None,
        properties: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Node]:
        """
        Search for nodes matching the given text.
        
        Args:
            search_text: Text to search for
            labels: Optional list of labels to filter by
            properties: Optional list of properties to search in
            limit: Maximum number of nodes to return
            
        Returns:
            List of matching nodes
        """
        # Build the Cypher query
        query_parts = ["MATCH (n)"]
        where_clauses = []
        
        # Add label filter if specified
        if labels and len(labels) > 0:
            label_filter = " OR ".join([f"n:{label}" for label in labels])
            where_clauses.append(f"({label_filter})")
        
        # Add property search
        if properties and len(properties) > 0:
            property_clauses = []
            
            for prop in properties:
                # Handle string properties
                property_clauses.append(
                    f"n.{prop} IS NOT NULL AND toLower(toString(n.{prop})) CONTAINS toLower($search_text)"
                )
                
                # Handle array properties
                property_clauses.append(
                    f"n.{prop} IS NOT NULL AND any(x IN n.{prop} WHERE toLower(toString(x)) CONTAINS toLower($search_text))"
                )
            
            where_clauses.append(f"({' OR '.join(property_clauses)})")
        else:
            # Default search across all properties
            where_clauses.append(
                f"any(prop IN keys(n) WHERE n[prop] IS NOT NULL AND " +
                f"(toLower(toString(n[prop])) CONTAINS toLower($search_text) OR " +
                f"(n[prop] IS NOT NULL AND n[prop] IS LIST AND " +
                f"any(x IN n[prop] WHERE toLower(toString(x)) CONTAINS toLower($search_text)))))"
            )
        
        # Add WHERE clause if we have conditions
        if where_clauses:
            query_parts.append(f"WHERE {' AND '.join(where_clauses)}")
        
        # Complete the query
        query_parts.append(f"RETURN n LIMIT {limit}")
        query = "\n".join(query_parts)
        
        # Execute the query
        records = self.execute_query(query, {"search_text": search_text})
        
        # Convert records to Node objects
        nodes = []
        for record in records:
            if "n" in record:
                neo4j_node = record["n"]
                node = self._neo4j_node_to_node(neo4j_node)
                nodes.append(node)
        
        return nodes
    
    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """
        Get a node by ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            Node or None if not found
        """
        query = "MATCH (n) WHERE id(n) = $node_id OR elementId(n) = $node_id RETURN n"
        records = self.execute_query(query, {"node_id": node_id})
        
        if records and "n" in records[0]:
            neo4j_node = records[0]["n"]
            return self._neo4j_node_to_node(neo4j_node)
        
        return None
    
    def find_paths(
        self, 
        start_node_id: str, 
        end_node_id: str,
        max_depth: int = 3,
        rel_types: Optional[List[str]] = None
    ) -> List[Path]:
        """
        Find paths between two nodes.
        
        Args:
            start_node_id: Starting node ID
            end_node_id: Ending node ID
            max_depth: Maximum path depth
            rel_types: Optional list of relationship types to consider
            
        Returns:
            List of paths
        """
        # Build the Cypher query
        rel_filter = ""
        if rel_types and len(rel_types) > 0:
            rel_type_list = "|".join(rel_types)
            rel_filter = f":{rel_type_list}"
        
        query = f"""
        MATCH (start) WHERE id(start) = $start_id OR elementId(start) = $start_id
        MATCH (end) WHERE id(end) = $end_id OR elementId(end) = $end_id
        MATCH path = shortestPath((start)-[r{rel_filter}*1..{max_depth}]-(end))
        RETURN path
        """
        
        # Execute the query
        records = self.execute_query(
            query, {"start_id": start_node_id, "end_id": end_node_id}
        )
        
        # Convert records to Path objects
        paths = []
        for record in records:
            if "path" in record:
                neo4j_path = record["path"]
                path = self._neo4j_path_to_path(neo4j_path)
                paths.append(path)
        
        return paths
    
    def find_related_nodes(
        self, 
        node_id: str,
        max_depth: int = 1,
        rel_types: Optional[List[str]] = None
    ) -> List[Tuple[Relationship, Node]]:
        """
        Find nodes related to the given node.
        
        Args:
            node_id: Node ID
            max_depth: Maximum relationship depth
            rel_types: Optional list of relationship types to consider
            
        Returns:
            List of (relationship, node) tuples
        """
        # Build the Cypher query
        rel_filter = ""
        if rel_types and len(rel_types) > 0:
            rel_type_list = "|".join(rel_types)
            rel_filter = f":{rel_type_list}"
        
        query = f"""
        MATCH (n) WHERE id(n) = $node_id OR elementId(n) = $node_id
        MATCH (n)-[r{rel_filter}]-(related)
        RETURN r, related
        """
        
        # Execute the query
        records = self.execute_query(query, {"node_id": node_id})
        
        # Convert records to (Relationship, Node) tuples
        related = []
        for record in records:
            if "r" in record and "related" in record:
                neo4j_rel = record["r"]
                neo4j_node = record["related"]
                
                rel = self._neo4j_relationship_to_relationship(neo4j_rel)
                node = self._neo4j_node_to_node(neo4j_node)
                
                related.append((rel, node))
        
        return related
    
    def extract_subgraph(
        self, 
        node_id: str,
        max_depth: int = 2,
        max_nodes: int = 50
    ) -> Tuple[List[Node], List[Relationship]]:
        """
        Extract a subgraph around a node.
        
        Args:
            node_id: Node ID
            max_depth: Maximum depth
            max_nodes: Maximum number of nodes
            
        Returns:
            Tuple of (nodes, relationships)
        """
        # Try to use APOC if available
        try:
            query = f"""
            MATCH (n) WHERE id(n) = $node_id OR elementId(n) = $node_id
            CALL apoc.path.subgraphAll(n, {{maxLevel: {max_depth}, limit: {max_nodes}}})
            YIELD nodes, relationships
            RETURN nodes, relationships
            """
            
            records = self.execute_query(query, {"node_id": node_id})
            
            if records and "nodes" in records[0] and "relationships" in records[0]:
                neo4j_nodes = records[0]["nodes"]
                neo4j_rels = records[0]["relationships"]
                
                nodes = [self._neo4j_node_to_node(n) for n in neo4j_nodes]
                relationships = [self._neo4j_relationship_to_relationship(r) for r in neo4j_rels]
                
                return nodes, relationships
        except Exception:
            # APOC not available or error occurred, use fallback
            pass
        
        # Fallback to standard Cypher
        query = f"""
        MATCH (n) WHERE id(n) = $node_id OR elementId(n) = $node_id
        MATCH path = (n)-[*1..{max_depth}]-(related)
        RETURN n, related, [r IN relationships(path) | r] as rels
        LIMIT {max_nodes}
        """
        
        records = self.execute_query(query, {"node_id": node_id})
        
        # Process results
        nodes_dict = {}
        rels_dict = {}
        
        for record in records:
            if "n" in record and "related" in record and "rels" in record:
                # Add start node
                neo4j_start = record["n"]
                start_node = self._neo4j_node_to_node(neo4j_start)
                nodes_dict[start_node.id] = start_node
                
                # Add related node
                neo4j_related = record["related"]
                related_node = self._neo4j_node_to_node(neo4j_related)
                nodes_dict[related_node.id] = related_node
                
                # Add relationships
                neo4j_rels = record["rels"]
                for neo4j_rel in neo4j_rels:
                    rel = self._neo4j_relationship_to_relationship(neo4j_rel)
                    rels_dict[rel.id] = rel
        
        return list(nodes_dict.values()), list(rels_dict.values())
    
    def _neo4j_node_to_node(self, neo4j_node) -> Node:
        """
        Convert a Neo4j node to a Node object.
        
        Args:
            neo4j_node: Neo4j node
            
        Returns:
            Node object
        """
        # Get node ID
        try:
            node_id = neo4j_node.element_id
        except AttributeError:
            node_id = str(neo4j_node.id)
        
        # Get node labels
        labels = list(neo4j_node.labels)
        
        # Get node properties
        properties = dict(neo4j_node)
        
        return Node(
            id=node_id,
            labels=labels,
            properties=properties
        )
    
    def _neo4j_relationship_to_relationship(self, neo4j_rel) -> Relationship:
        """
        Convert a Neo4j relationship to a Relationship object.
        
        Args:
            neo4j_rel: Neo4j relationship
            
        Returns:
            Relationship object
        """
        # Get relationship ID
        try:
            rel_id = neo4j_rel.element_id
        except AttributeError:
            rel_id = str(neo4j_rel.id)
        
        # Get relationship type
        rel_type = neo4j_rel.type
        
        # Get source and target node IDs
        try:
            source_id = neo4j_rel.start_node.element_id
            target_id = neo4j_rel.end_node.element_id
        except AttributeError:
            source_id = str(neo4j_rel.start_node.id)
            target_id = str(neo4j_rel.end_node.id)
        
        # Get relationship properties
        properties = dict(neo4j_rel)
        
        return Relationship(
            id=rel_id,
            type=rel_type,
            source_id=source_id,
            target_id=target_id,
            properties=properties
        )
    
    def _neo4j_path_to_path(self, neo4j_path) -> Path:
        """
        Convert a Neo4j path to a Path object.
        
        Args:
            neo4j_path: Neo4j path
            
        Returns:
            Path object
        """
        # Get nodes
        neo4j_nodes = list(neo4j_path.nodes)
        nodes = [self._neo4j_node_to_node(n) for n in neo4j_nodes]
        
        # Get relationships
        neo4j_rels = list(neo4j_path.relationships)
        relationships = [self._neo4j_relationship_to_relationship(r) for r in neo4j_rels]
        
        return Path(
            nodes=nodes,
            relationships=relationships
        )


# Global client instance
_client = None


def get_client() -> Neo4jClient:
    """
    Get the global Neo4j client instance.
    
    Returns:
        Neo4jClient instance
    """
    global _client
    
    if _client is None:
        config = get_config().neo4j
        _client = Neo4jClient(
            uri=config.uri,
            username=config.username,
            password=config.password
        )
    
    return _client


def set_client(client: Neo4jClient) -> None:
    """
    Set the global Neo4j client instance.
    
    Args:
        client: Neo4jClient instance
    """
    global _client
    _client = client
