"""Module for detecting duplicate nodes in the knowledge graph."""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from enum import Enum
from ..utils.similarity import calculate_similarity
from .base import KGComponent

class MatchStrategy(Enum):
    """Strategies for matching duplicate nodes."""
    EXACT = "exact"
    FUZZY = "fuzzy"
    EMBEDDING = "embedding"
    CONTEXTUAL = "contextual"

@dataclass
class DuplicateGroup:
    """Represents a group of nodes that are potential duplicates."""
    node_ids: List[int]
    confidence: float
    match_strategy: MatchStrategy
    matching_properties: Dict[str, Any]

class DuplicateDetector(KGComponent):
    """Detects duplicate nodes in the knowledge graph using various strategies."""
    
    def __init__(self, driver, config=None):
        """Initialize the duplicate detector.
        
        Args:
            driver: Neo4j driver instance
            config: Configuration dictionary with the following optional keys:
                - similarity_threshold: Minimum similarity score (0-1) to consider nodes as duplicates
                - batch_size: Number of nodes to process in each batch
                - strategies: List of strategies to use for duplicate detection
                - property_weights: Dictionary of property weights for similarity calculation
        """
        super().__init__(driver, config)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.9)
        self.batch_size = self.config.get('batch_size', 1000)
        self.strategies = self.config.get('strategies', ['exact', 'fuzzy'])
        self.property_weights = self.config.get('property_weights', {'name': 1.0})
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_config(self) -> bool:
        """Validate the configuration."""
        if not 0 <= self.similarity_threshold <= 1:
            self.logger.error("similarity_threshold must be between 0 and 1")
            return False
        if self.batch_size <= 0:
            self.logger.error("batch_size must be positive")
            return False
        return True
    
    def find_duplicates(self, node_ids: Optional[List[int]] = None, batch_size: Optional[int] = None) -> List[DuplicateGroup]:
        """Find potential duplicate nodes in the graph.
        
        Args:
            node_ids: Optional list of node IDs to check for duplicates.
                     If None, checks all nodes in the graph.
            batch_size: Number of nodes to process in each batch.
                      If None, uses the instance's batch_size.
        
        Returns:
            List of DuplicateGroup objects representing groups of potential duplicates.
        """
        batch_size = batch_size or self.batch_size
        duplicates = []
        
        # Process each strategy in order of precision
        if 'exact' in self.strategies:
            self.logger.info("Finding exact duplicates...")
            exact_dupes = self._find_exact_duplicates(node_ids, batch_size)
            duplicates.extend(exact_dupes)
            self.logger.info(f"Found {len(exact_dupes)} groups of exact duplicates")
        
        if 'fuzzy' in self.strategies:
            self.logger.info("Finding fuzzy duplicates...")
            # Exclude nodes already matched in exact duplicates
            fuzzy_dupes = self._find_fuzzy_duplicates(node_ids, batch_size, self._get_matched_node_ids(duplicates))
            duplicates.extend(fuzzy_dupes)
            self.logger.info(f"Found {len(fuzzy_dupes)} groups of fuzzy duplicates")
        
        if 'embedding' in self.strategies:
            self.logger.info("Finding duplicates using embeddings...")
            # Exclude nodes already matched in previous steps
            embedding_dupes = self._find_embedding_duplicates(
                node_ids, 
                batch_size, 
                self._get_matched_node_ids(duplicates)
            )
            duplicates.extend(embedding_dupes)
            self.logger.info(f"Found {len(embedding_dupes)} groups of duplicates via embeddings")
        
        if 'contextual' in self.strategies:
            self.logger.info("Finding contextual duplicates...")
            # Exclude nodes already matched in previous steps
            contextual_dupes = self._find_contextual_duplicates(
                node_ids,
                batch_size,
                self._get_matched_node_ids(duplicates)
            )
            duplicates.extend(contextual_dupes)
            self.logger.info(f"Found {len(contextual_dupes)} groups of contextual duplicates")
        
        return duplicates
    
    def _find_exact_duplicates(self, node_ids: Optional[List[int]] = None, batch_size: int = 1000) -> List[DuplicateGroup]:
        """Find nodes with exact matching names or aliases (case-insensitive, normalized)."""
        query = (
            "MATCH (n)\n"
            "WHERE size(labels(n)) > 0 AND (n.name IS NOT NULL OR n.aliases IS NOT NULL) "
            + ("AND id(n) IN $node_ids " if node_ids else "") +
            "WITH n, [toLower(trim(n.name))] + [toLower(trim(alias)) | alias IN coalesce(n.aliases,[])] AS all_names, labels(n) AS nodeLabels\n"
            "UNWIND all_names AS name\n"
            "WITH name, collect({id: id(n), name: n.name, aliases: n.aliases, props: properties(n), labels: nodeLabels}) AS nodes\n"
            "WHERE size(nodes) > 1\n"
            "RETURN name, nodes"
        )
        params = {"node_ids": node_ids} if node_ids else {}
        results = self.execute_query(query, params)
        duplicate_groups = []
        for record in results:
            node_ids = [n['id'] for n in record['nodes']]
            node_labels = record['nodes'][0]['labels'] if record['nodes'] else []
            # Collect all names and aliases for provenance
            all_names = set()
            for n in record['nodes']:
                all_names.add(n['name'].lower().strip() if n['name'] else "")
                for alias in n.get('aliases') or []:
                    all_names.add(alias.lower().strip())
            duplicate_groups.append(DuplicateGroup(
                node_ids=node_ids,
                node_labels=node_labels,
                confidence=1.0,
                reason="exact_match_via_name_or_alias",
                properties={"matched_names": list(all_names)}
            ))
        return duplicate_groups
    
    def _find_fuzzy_duplicates(self, node_ids: Optional[List[int]] = None, batch_size: int = 1000) -> List[DuplicateGroup]:
        """Find nodes with similar names or aliases using fuzzy matching."""
        # Get all candidate nodes with their names and aliases
        query = """
        MATCH (n)
        WHERE size(labels(n)) > 0 AND (n.name IS NOT NULL OR n.aliases IS NOT NULL)
        RETURN id(n) as id, labels(n) as labels, n.name as name, coalesce(n.aliases, []) as aliases, properties(n) as props
        """
        params = {"node_ids": node_ids} if node_ids else {}
        results = self.execute_query(query, params)
        # Prepare for fuzzy matching using all names and aliases
        candidates = []
        for rec in results:
            all_names = [rec['name'].lower().strip()] if rec['name'] else []
            all_names += [alias.lower().strip() for alias in rec['aliases']]
            candidates.append({
                "id": rec['id'],
                "labels": rec['labels'],
                "all_names": all_names,
                "props": rec['props']
            })
        duplicate_groups = []
        visited = set()
        for i, node1 in enumerate(candidates):
            if node1['id'] in visited:
                continue
            group = [node1['id']]
            for j, node2 in enumerate(candidates):
                if i == j or node2['id'] in visited:
                    continue
                if set(node1['labels']) != set(node2['labels']):
                    continue
                # Fuzzy match any name/alias pair
                match_found = False
                for name1 in node1['all_names']:
                    for name2 in node2['all_names']:
                        similarity = calculate_similarity(name1, name2, method='ratio')
                        if similarity >= self.similarity_threshold:
                            match_found = True
                            break
                    if match_found:
                        break
                if match_found:
                    group.append(node2['id'])
                    visited.add(node2['id'])
            if len(group) > 1:
                duplicate_groups.append(DuplicateGroup(
                    node_ids=group,
                    node_labels=node1['labels'],
                    confidence=0.8,
                    reason="fuzzy_match_via_name_or_alias",
                    properties={"matched_names": node1['all_names']}
                ))
            visited.add(node1['id'])
        return duplicate_groups
    
    def _find_embedding_duplicates(self, node_ids: Optional[List[int]], batch_size: int, 
                                  exclude_node_ids: List[int] = None) -> List[DuplicateGroup]:
        """Find duplicate nodes using vector embeddings."""
        # This is a placeholder - in a real implementation, you would:
        # 1. Generate or retrieve embeddings for nodes
        # 2. Use vector similarity search to find similar nodes
        # 3. Group nodes that are similar above the threshold
        return []
    
    def _find_contextual_duplicates(self, node_ids: Optional[List[int]], batch_size: int, 
                                   exclude_node_ids: List[int] = None) -> List[DuplicateGroup]:
        """Find duplicate nodes based on graph context and relationships."""
        # This is a placeholder - in a real implementation, you would:
        # 1. Analyze the graph neighborhood of each node
        # 2. Compare neighborhood structures and relationships
        # 3. Use graph algorithms to find structurally similar nodes
        return []
    
    def _calculate_node_similarity(self, node1: Dict, node2: Dict) -> float:
        """Calculate similarity between two nodes based on their properties."""
        # Simple implementation that just compares names
        name1 = node1["props"].get("name", "")
        name2 = node2["props"].get("name", "")
        
        if not name1 or not name2:
            return 0.0
            
        return calculate_similarity(name1, name2)
    
    @staticmethod
    def _get_matched_node_ids(duplicate_groups: List[DuplicateGroup]) -> List[int]:
        """Get a flat list of all node IDs that have been matched in duplicate groups."""
        matched_ids = []
        for group in duplicate_groups:
            matched_ids.extend(group.node_ids)
        return matched_ids
