"""
RelationshipDiscoverer: Proposes new relationships based on alias overlap and community summary content.
- SAME_AS and RELATED_TO relationships are suggested when nodes/communities share aliases or are referenced together in summaries.
- All proposals are non-destructive and provenance-aware (evidence includes which aliases or summary matches triggered the suggestion).
- Designed to work with the Tolkien Knowledge Graph schema and PRD.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from .base import KGComponent
from ..utils.similarity import calculate_similarity

class RelationshipType(Enum):
    SAME_AS = "SAME_AS"
    RELATED_TO = "RELATED_TO"
    PART_OF = "PART_OF"
    ASSOCIATED_WITH = "ASSOCIATED_WITH"
    DERIVED_FROM = "DERIVED_FROM"

@dataclass
class RelationshipCandidate:
    source_id: int
    target_id: int
    relationship_type: RelationshipType
    confidence: float
    evidence: Dict[str, Any]

class RelationshipDiscoverer(KGComponent):
    """Discovers potential relationships between nodes using aliases and community summaries."""
    def __init__(self, driver, config=None):
        super().__init__(driver, config)
        self.min_confidence = self.config.get('min_confidence', 0.7)
        self.max_relationships = self.config.get('max_relationships', 1000)
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_config(self) -> bool:
        return True

    def find_relationships(self, node_ids: Optional[List[int]] = None) -> List[RelationshipCandidate]:
        self.logger.info("Starting relationship discovery...")
        nodes = self._get_nodes(node_ids)
        candidates = []
        # Alias overlap: SAME_AS or RELATED_TO
        for i, node1 in enumerate(nodes):
            aliases1 = set([node1['props'].get('name', '').strip().lower()])
            aliases1 |= set([a.strip().lower() for a in node1['props'].get('aliases', [])])
            for j, node2 in enumerate(nodes):
                if i >= j:
                    continue
                if set(node1['labels']) != set(node2['labels']):
                    continue
                aliases2 = set([node2['props'].get('name', '').strip().lower()])
                aliases2 |= set([a.strip().lower() for a in node2['props'].get('aliases', [])])
                shared_aliases = aliases1 & aliases2
                if shared_aliases:
                    candidates.append(RelationshipCandidate(
                        source_id=node1['id'],
                        target_id=node2['id'],
                        relationship_type=RelationshipType.SAME_AS,
                        confidence=1.0,
                        evidence={"shared_aliases": list(shared_aliases)}
                    ))
                else:
                    # Fuzzy similarity on aliases
                    for a1 in aliases1:
                        for a2 in aliases2:
                            sim = calculate_similarity(a1, a2, method='ratio')
                            if sim >= self.min_confidence:
                                candidates.append(RelationshipCandidate(
                                    source_id=node1['id'],
                                    target_id=node2['id'],
                                    relationship_type=RelationshipType.RELATED_TO,
                                    confidence=sim,
                                    evidence={"fuzzy_alias_pair": (a1, a2), "similarity": sim}
                                ))
        # Community summary soft links
        summary_nodes = [n for n in nodes if n['props'].get('summary')]
        for i, node1 in enumerate(summary_nodes):
            summary1 = node1['props'].get('summary', '').lower()
            for j, node2 in enumerate(summary_nodes):
                if i >= j:
                    continue
                summary2 = node2['props'].get('summary', '').lower()
                # Simple shared mention: if node1's name/alias appears in node2's summary or vice versa
                names1 = set([node1['props'].get('name', '').lower()] + [a.lower() for a in node1['props'].get('aliases', [])])
                names2 = set([node2['props'].get('name', '').lower()] + [a.lower() for a in node2['props'].get('aliases', [])])
                mention = False
                for n in names1:
                    if n and n in summary2:
                        mention = True
                        break
                for n in names2:
                    if n and n in summary1:
                        mention = True
                        break
                if mention:
                    candidates.append(RelationshipCandidate(
                        source_id=node1['id'],
                        target_id=node2['id'],
                        relationship_type=RelationshipType.ASSOCIATED_WITH,
                        confidence=0.8,
                        evidence={"summary_mention": True}
                    ))
        # Sort and limit
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        return candidates[:self.max_relationships]

    def _get_nodes(self, node_ids: Optional[List[int]] = None) -> List[Dict]:
        query = """
        MATCH (n)
        WHERE $node_ids IS NULL OR id(n) IN $node_ids
        RETURN id(n) as id, properties(n) as props, labels(n) as labels
        """
        results = self.execute_query(query, {'node_ids': node_ids})
        return [
            {'id': record['id'], 'props': record['props'], 'labels': record['labels']}
            for record in results
        ]
    evidence: Dict[str, Any]

class RelationshipDiscoverer(KGComponent):
    """Discovers potential relationships between nodes in the knowledge graph."""
    def __init__(self, driver, config=None):
        super().__init__(driver, config)
        self.min_confidence = self.config.get('min_confidence', 0.7)
        self.max_relationships = self.config.get('max_relationships', 1000)
        self.batch_size = self.config.get('batch_size', 1000)
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_config(self) -> bool:
        if not 0 <= self.min_confidence <= 1:
            self.logger.error("min_confidence must be between 0 and 1")
            return False
        if self.max_relationships <= 0:
            self.logger.error("max_relationships must be positive")
            return False
        if self.batch_size <= 0:
            self.logger.error("batch_size must be positive")
            return False
        return True

    def find_relationships(self, node_ids: Optional[List[int]] = None) -> List[RelationshipCandidate]:
        self.logger.info("Starting relationship discovery...")
        nodes = self._get_nodes(node_ids)
        self.logger.info(f"Analyzing {len(nodes)} nodes for relationships")
        candidates = []
        # For demonstration, only do SAME_AS based on high property similarity
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                sim = calculate_node_similarity(nodes[i]['props'], nodes[j]['props'])
                if sim >= self.min_confidence:
                    candidates.append(RelationshipCandidate(
                        source_id=nodes[i]['id'],
                        target_id=nodes[j]['id'],
                        relationship_type=RelationshipType.SAME_AS,
                        confidence=sim,
                        evidence={'similarity': sim}
                    ))
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        return candidates[:self.max_relationships]

    def _get_nodes(self, node_ids: Optional[List[int]] = None) -> List[Dict]:
        query = """
        MATCH (n)
        WHERE $node_ids IS NULL OR id(n) IN $node_ids
        RETURN id(n) as id, properties(n) as props, labels(n) as labels
        """
        results = self.execute_query(query, {'node_ids': node_ids})
        return [
            {'id': record['id'], 'props': record['props'], 'labels': record['labels']}
            for record in results
        ]
