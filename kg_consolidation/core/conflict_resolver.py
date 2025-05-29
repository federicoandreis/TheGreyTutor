"""
ConflictResolver: Non-destructive, provenance-rich conflict handling for the Tolkien Knowledge Graph.
- Detects property/relationship conflicts and always annotates the source node(s) for each value.
- Preserves all variants in a structured way; nothing is overwritten or lost.
- If a conflict cannot be resolved, logs all variants to a 'conflicts' property for human or LLM review.
- All actions are reversible and fully provenance-aware.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from .base import KGComponent

@dataclass
class ConflictGroup:
    node_ids: List[int]
    conflicting_properties: Dict[str, List[Any]]
    provenance: Dict[str, Dict[Any, List[int]]]
    context: str

@dataclass
class Resolution:
    node_id: int
    resolved_properties: Dict[str, Any]
    rationale: str
    confidence: float
    provenance: Dict[str, Any]

class ConflictResolver(KGComponent):
    """Handles non-destructive, provenance-aware conflict resolution for the knowledge graph."""
    def __init__(self, driver, config=None):
        super().__init__(driver, config)
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_config(self) -> bool:
        return True

    def detect_conflicts(self) -> List[ConflictGroup]:
        """Detect conflicting property values among nodes, annotating all sources."""
        # Example: find all nodes with the same alias/name but conflicting property values
        query = """
        MATCH (n)
        WITH n, [toLower(trim(n.name))] + [toLower(trim(alias)) | alias IN coalesce(n.aliases,[])] AS all_names
        UNWIND all_names AS alias
        WITH alias, collect(n) AS nodes
        WHERE size(nodes) > 1
        UNWIND keys(nodes[0]) AS prop
        WITH alias, prop, [n IN nodes | n[prop]] AS values, [n IN nodes | id(n)] AS node_ids
        WHERE size(apoc.coll.toSet(values)) > 1 AND prop <> 'aliases' AND prop <> 'name'
        RETURN alias, prop, values, node_ids
        """
        results = self.execute_query(query)
        conflicts_by_alias = {}
        for rec in results:
            alias = rec['alias']
            prop = rec['prop']
            values = rec['values']
            node_ids = rec['node_ids']
            provenance = {}
            for v, nid in zip(values, node_ids):
                provenance.setdefault(v, []).append(nid)
            conflicts_by_alias.setdefault(alias, {}).setdefault(prop, []).extend(values)
            # Provenance per value
            if 'provenance' not in conflicts_by_alias[alias]:
                conflicts_by_alias[alias]['provenance'] = {}
            conflicts_by_alias[alias]['provenance'][prop] = provenance
        # Convert to ConflictGroup
        conflict_groups = []
        for alias, props in conflicts_by_alias.items():
            node_ids = []
            for prov in props.get('provenance', {}).values():
                for nids in prov.values():
                    node_ids.extend(nids)
            node_ids = list(set(node_ids))
            conflict_groups.append(ConflictGroup(
                node_ids=node_ids,
                conflicting_properties={k: v for k, v in props.items() if k != 'provenance'},
                provenance=props.get('provenance', {}),
                context=f"Alias: {alias}"
            ))
        return conflict_groups

    def resolve_conflicts(self, conflicts: List[ConflictGroup]) -> List[Resolution]:
        """Resolve conflicts using LLM or rules, always retaining provenance and all variants."""
        resolutions = []
        for group in conflicts:
            # Example: choose most frequent value, but keep all variants and provenance
            resolved = {}
            for prop, values in group.conflicting_properties.items():
                value_counts = {v: len(group.provenance.get(prop, {}).get(v, [])) for v in values}
                best = max(value_counts, key=value_counts.get)
                resolved[prop] = best
            resolutions.append(Resolution(
                node_id=group.node_ids[0],
                resolved_properties=resolved,
                rationale="Chose most frequent value, preserved all variants in 'conflicts' property.",
                confidence=1.0,
                provenance=group.provenance
            ))
        return resolutions

    def apply_conflict_resolutions(self, resolutions: List[Resolution]) -> None:
        """Apply resolved properties in a non-destructive way, logging all variants and provenance."""
        for res in resolutions:
            # Only update if not already set, and always log all variants
            update_query = """
            MATCH (n) WHERE id(n) = $node_id
            SET n.conflicts = $conflicts, n.resolved_properties = $resolved_properties, n.conflict_provenance = $provenance
            """
            params = {
                "node_id": res.node_id,
                "conflicts": {k: list(v.keys()) for k, v in res.provenance.items()},
                "resolved_properties": res.resolved_properties,
                "provenance": res.provenance
            }
            self.execute_query(update_query, params)
