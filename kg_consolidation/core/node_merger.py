"""Module for merging duplicate nodes in the knowledge graph."""
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
import logging
from enum import Enum
from ..utils.similarity import calculate_node_similarity
from .base import KGComponent

class MergeStrategy(Enum):
    """Strategies for merging node properties."""
    KEEP_FIRST = "keep_first"  # Keep the first occurrence's value
    KEEP_LAST = "keep_last"    # Keep the last occurrence's value
    MERGE = "merge"           # Merge values (for lists, sets, etc.)
    CONCAT = "concat"         # Concatenate string values
    MAX = "max"               # Keep the maximum value
    MIN = "min"               # Keep the minimum value
    ASK_USER = "ask_user"     # Ask the user to resolve conflicts

@dataclass
class MergeResult:
    """Result of a node merge operation."""
    kept_node_id: int           # ID of the node that was kept
    merged_node_ids: List[int]  # IDs of nodes that were merged into kept_node
    properties_merged: Dict[str, Any]  # Properties that were merged
    relationships_updated: int  # Number of relationships updated

class NodeMerger(KGComponent):
    """Handles merging of duplicate nodes in the knowledge graph."""
    
    def __init__(self, driver, config=None):
        """Initialize the node merger.
        
        Args:
            driver: Neo4j driver instance
            config: Configuration dictionary with the following optional keys:
                - default_strategy: Default merge strategy to use
                - property_strategies: Dictionary mapping property names to merge strategies
                - preserve_history: Whether to preserve history of merged nodes
                - batch_size: Number of nodes to process in each batch
        """
        super().__init__(driver, config)
        self.default_strategy = self.config.get('default_strategy', MergeStrategy.KEEP_FIRST)
        self.property_strategies = self.config.get('property_strategies', {})
        self.preserve_history = self.config.get('preserve_history', True)
        self.batch_size = self.config.get('batch_size', 1000)
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_config(self) -> bool:
        """Validate the configuration."""
        if not isinstance(self.default_strategy, MergeStrategy):
            try:
                self.default_strategy = MergeStrategy(self.default_strategy)
            except ValueError:
                self.logger.error(f"Invalid default_strategy: {self.default_strategy}")
                return False
                
        for prop, strategy in self.property_strategies.items():
            if not isinstance(strategy, MergeStrategy):
                try:
                    self.property_strategies[prop] = MergeStrategy(strategy)
                except ValueError:
                    self.logger.error(f"Invalid strategy for property {prop}: {strategy}")
                    return False
        
        return True

    def merge_nodes(self, node_ids: List[int], main_node_id: Optional[int] = None) -> MergeResult:
        """Merge the given nodes into a single node, preserving all properties, aliases, relationships, and provenance.
        
        This method performs a non-destructive merge, updating the main node with merged properties and relationships.
        It also tracks provenance for all properties and returns a MergeResult object.
        
        Args:
            node_ids: List of node IDs to merge
            main_node_id: ID of the main node to keep (optional, defaults to the first node ID)
        
        Returns:
            MergeResult object containing the ID of the kept node, merged node IDs, merged properties, and relationships updated
        """
        if not node_ids or len(node_ids) < 2:
            raise ValueError("Need at least two nodes to merge.")

        main_id = main_node_id if main_node_id is not None else node_ids[0]
        other_ids = [nid for nid in node_ids if nid != main_id]

        # Gather all properties and relationships
        query = """
        MATCH (main) WHERE id(main) = $main_id
        WITH main
        MATCH (n) WHERE id(n) IN $other_ids
        RETURN properties(main) AS main_props, collect(properties(n)) AS others_props
        """
        result = self.execute_query(query, {"main_id": main_id, "other_ids": other_ids})
        if not result:
            raise ValueError("Main or other nodes not found.")
        main_props = result[0]["main_props"]
        others_props = result[0]["others_props"]
        all_props = [main_props] + others_props

        # Merge aliases and names
        all_aliases = set()
        alias_provenance = {}
        for idx, props in enumerate(all_props):
            node_id = node_ids[idx] if idx < len(node_ids) else None
            if props.get("name"):
                name = props["name"].strip()
                all_aliases.add(name)
                alias_provenance[name] = alias_provenance.get(name, []) + [node_id]
            for alias in props.get("aliases", []):
                alias = alias.strip()
                all_aliases.add(alias)
                alias_provenance[alias] = alias_provenance.get(alias, []) + [node_id]
        merged_aliases = sorted(all_aliases)

        # Merge properties (track all variants and provenance)
        merged_properties = {}
        property_provenance = {}
        conflicts = {}
        for key in set(k for props in all_props for k in props.keys() if k not in ["aliases", "name"]):
            values = []
            value_sources = {}
            for idx, props in enumerate(all_props):
                node_id = node_ids[idx] if idx < len(node_ids) else None
                val = props.get(key)
                if val is not None and val != "":
                    values.append(val)
                    value_sources.setdefault(val, []).append(node_id)
            unique_values = list({v for v in values})
            merged_properties[key] = unique_values[0] if len(unique_values) == 1 else unique_values
            property_provenance[key] = value_sources
            if len(unique_values) > 1:
                conflicts[key] = unique_values

        # Build merge history
        merge_history = {
            "merged_node_ids": node_ids,
            "alias_provenance": alias_provenance,
            "property_provenance": property_provenance
        }

        # Update main node (non-destructively)
        update_query = """
        MATCH (n) WHERE id(n) = $main_id
        SET n.aliases = $merged_aliases,
            n.merge_history = $merge_history,
            n.conflicts = $conflicts
        """
        # Set all merged properties except aliases (already handled)
        set_props = {k: v for k, v in merged_properties.items() if k not in ["aliases", "name"]}
        for k, v in set_props.items():
            update_query += f"\nSET n.{k} = ${k}"
        params = {"main_id": main_id, "merged_aliases": merged_aliases, "merge_history": merge_history, "conflicts": conflicts, **set_props}
        self.execute_query(update_query, params)

        # Transfer all relationships from others to main (non-destructive)
        rel_query = """
        UNWIND $other_ids AS oid
        MATCH (o) WHERE id(o) = oid
        MATCH (main) WHERE id(main) = $main_id
        CALL apoc.refactor.mergeNodes([main, o], {properties:'discard', mergeRels:true}) YIELD node
        RETURN count(*)
        """
        relationships_updated = self.execute_query(rel_query, {"main_id": main_id, "other_ids": other_ids})[0][0]

        return MergeResult(
            kept_node_id=main_id,
            merged_node_ids=other_ids,
            properties_merged=merged_properties,
            relationships_updated=relationships_updated
        )
        nodes = self._get_nodes_by_ids(node_ids)
        if not nodes:
            self.logger.warning(f"No nodes found with IDs: {node_ids}")
            return
            
        # Determine which node to keep (the one with the most complete data)
        node_to_keep = self._select_node_to_keep(nodes)
        nodes_to_merge = [n for n in nodes if n['id'] != node_to_keep['id']]
            
        # Merge properties
        merged_properties = self._merge_node_properties(node_to_keep, nodes_to_merge)
            
        # Update relationships
        relationships_updated = self._update_relationships(node_to_keep['id'], nodes_to_merge)
            
        # Update the kept node with merged properties
        self._update_node(node_to_keep['id'], merged_properties)
            
        # Create merge history if enabled
        if self.preserve_history:
            self._create_merge_history(node_to_keep['id'], nodes_to_merge, group)
            
        # Delete the merged nodes (if not preserving history)
        if not self.preserve_history:
            self._delete_nodes([n['id'] for n in nodes_to_merge])
            
        # Record the result
        result = MergeResult(
            kept_node_id=node_to_keep['id'],
            merged_node_ids=[n['id'] for n in nodes_to_merge],
            properties_merged=merged_properties,
            relationships_updated=relationships_updated
        )
        results.append(result)
            
        self.logger.info(
            f"Merged {len(nodes_to_merge)} nodes into {node_to_keep['id']}. "
            f"Updated {relationships_updated} relationships."
        )
        
        return results
    
    def _get_nodes_by_ids(self, node_ids: List[int]) -> List[Dict]:
        """Retrieve nodes by their Neo4j IDs."""
        if not node_ids:
            return []
            
        query = """
        UNWIND $node_ids AS node_id
        MATCH (n)
        WHERE id(n) = node_id
        RETURN id(n) as id, properties(n) as props, labels(n) as labels
        """
        
        results = self.execute_query(query, {'node_ids': node_ids})
        return [
            {
                'id': record['id'],
                'props': record['props'],
                'labels': record['labels']
            }
            for record in results
        ]
    
    def _select_node_to_keep(self, nodes: List[Dict]) -> Dict:
        """Select the best node to keep from a group of duplicates."""
        # Simple implementation: keep the node with the most non-null properties
        # In a real implementation, you might consider other factors like:
        # - Node labels
        # - Relationship counts
        # - Timestamps or version numbers
        # - Source reliability
        
        def score_node(node):
            # Count non-null, non-empty properties
            return sum(
                1 for v in node['props'].values() 
                if v is not None and v != ''
            )
        
        return max(nodes, key=score_node)
    
    def _merge_node_properties(self, node_to_keep: Dict, nodes_to_merge: List[Dict]) -> Dict:
        """Merge properties from multiple nodes into a single property set."""
        merged_props = node_to_keep['props'].copy()
        
        for node in nodes_to_merge:
            for prop, value in node['props'].items():
                if prop not in merged_props or merged_props[prop] is None:
                    # If the property doesn't exist in the kept node, add it
                    merged_props[prop] = value
                else:
                    # Otherwise, apply the appropriate merge strategy
                    strategy = self.property_strategies.get(prop, self.default_strategy)
                    merged_props[prop] = self._merge_values(
                        prop, 
                        merged_props[prop], 
                        value, 
                        strategy
                    )
        
        return merged_props
    
    def _merge_values(self, prop: str, value1: Any, value2: Any, strategy: MergeStrategy) -> Any:
        """Merge two property values according to the specified strategy."""
        if value1 is None:
            return value2
        if value2 is None:
            return value1
        if value1 == value2:
            return value1
            
        if strategy == MergeStrategy.KEEP_FIRST:
            return value1
        elif strategy == MergeStrategy.KEEP_LAST:
            return value2
        elif strategy == MergeStrategy.MERGE:
            if isinstance(value1, list) and isinstance(value2, list):
                # Merge lists, preserving order and removing duplicates
                return list(dict.fromkeys(value1 + value2))
            elif isinstance(value1, set) and isinstance(value2, set):
                return value1.union(value2)
            elif isinstance(value1, dict) and isinstance(value2, dict):
                # Merge dictionaries, with value2 taking precedence for overlapping keys
                return {**value1, **value2}
            else:
                # Fall back to keeping the first value for incompatible types
                return value1
        elif strategy == MergeStrategy.CONCAT:
            if isinstance(value1, str) and isinstance(value2, str):
                return f"{value1}, {value2}"
            else:
                return value1
        elif strategy == MergeStrategy.MAX:
            try:
                return max(value1, value2)
            except (TypeError, ValueError):
                return value1
        elif strategy == MergeStrategy.MIN:
            try:
                return min(value1, value2)
            except (TypeError, ValueError):
                return value1
        else:
            # Default to keeping the first value
            return value1
    
    def _update_relationships(self, kept_node_id: int, nodes_to_merge: List[Dict]) -> int:
        """Update relationships to point to the kept node."""
        if not nodes_to_merge:
            return 0
            
        # Get all relationship types in the graph
        rel_types_query = """
        CALL db.relationshipTypes() YIELD relationshipType
        RETURN relationshipType
        """
        rel_types = [r['relationshipType'] for r in self.execute_query(rel_types_query)]
        
        total_updated = 0
        
        # For each relationship type, update relationships
        for rel_type in rel_types:
            # Update incoming relationships
            incoming_query = f"""
            UNWIND $node_ids AS node_id
            MATCH (a)-[r:{rel_type}]->(b)
            WHERE id(b) = node_id AND id(a) <> $kept_node_id
            WITH a, collect(DISTINCT r) as rels, b
            CALL apoc.refactor.mergeNodes([a, $kept_node_id], {{
                properties: 'combine',
                mergeRels: true
            }}) YIELD node
            RETURN count(*) as updated
            """
            
            # Update outgoing relationships
            outgoing_query = f"""
            UNWIND $node_ids AS node_id
            MATCH (a)-[r:{rel_type}]->(b)
            WHERE id(a) = node_id AND id(b) <> $kept_node_id
            WITH collect(DISTINCT r) as rels, b
            CALL apoc.refactor.mergeNodes([b, $kept_node_id], {{
                properties: 'combine',
                mergeRels: true
            }}) YIELD node
            RETURN count(*) as updated
            """
            
            try:
                # Execute both queries and sum the results
                incoming_updated = self.execute_query(
                    incoming_query,
                    {'node_ids': [n['id'] for n in nodes_to_merge], 'kept_node_id': kept_node_id}
                )
                outgoing_updated = self.execute_query(
                    outgoing_query,
                    {'node_ids': [n['id'] for n in nodes_to_merge], 'kept_node_id': kept_node_id}
                )
                
                total_updated += (incoming_updated[0].get('updated', 0) if incoming_updated else 0)
                total_updated += (outgoing_updated[0].get('updated', 0) if outgoing_updated else 0)
                
            except Exception as e:
                self.logger.warning(f"Error updating {rel_type} relationships: {e}")
        
        return total_updated
    
    def _update_node(self, node_id: int, properties: Dict) -> None:
        """Update a node with new properties."""
        query = """
        MATCH (n)
        WHERE id(n) = $node_id
        SET n += $properties
        """
        self.execute_write_query(query, {'node_id': node_id, 'properties': properties})
    
    def _create_merge_history(self, kept_node_id: int, merged_nodes: List[Dict], duplicate_group: Dict) -> None:
        """Create a record of the merge operation."""
        query = """
        MATCH (n)
        WHERE id(n) = $kept_node_id
        SET n.merged_from = coalesce(n.merged_from, []) + $merged_node_ids,
            n.merge_history = coalesce(n.merge_history, []) + [$merge_record]
        """
        
        merge_record = {
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'kept_node_id': kept_node_id,
            'merged_node_ids': [n['id'] for n in merged_nodes],
            'match_type': duplicate_group.get('match_type'),
            'confidence': duplicate_group.get('confidence'),
            'matching_properties': duplicate_group.get('matching_properties', {})
        }
        
        self.execute_write_query(query, {
            'kept_node_id': kept_node_id,
            'merged_node_ids': [n['id'] for n in merged_nodes],
            'merge_record': merge_record
        })
    
    def _delete_nodes(self, node_ids: List[int]) -> None:
        """Delete nodes by their IDs."""
        if not node_ids:
            return
            
        query = """
        UNWIND $node_ids AS node_id
        MATCH (n)
        WHERE id(n) = node_id
        DETACH DELETE n
        """
        self.execute_write_query(query, {'node_ids': node_ids})
