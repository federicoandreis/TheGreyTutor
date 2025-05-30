import os
from neo4j import GraphDatabase
from typing import List, Dict, Any, Tuple, Set
import difflib

# Load Neo4j credentials from environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Minimum similarity ratio for fuzzy matching
FUZZY_THRESHOLD = 0.99

class Neo4jDuplicateFinder:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    TARGET_LABELS = {"Artifact", "Character", "Community", "Event", "Location", "Organization"}
    def fetch_nodes_by_label(self, label: str) -> List[Dict[str, Any]]:
        query = f'''
        MATCH (n:`{label}`)
        RETURN elementId(n) as id, labels(n) as labels, n.name as name, coalesce(n.aliases, []) as aliases
        '''
        with self.driver.session() as session:
            nodes = list(session.run(query))
        return nodes


    def fetch_node_relationships(self, node_id: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        # Outgoing and incoming relationships
        query_out = """
        MATCH (n)-[r]->(m)
        WHERE elementId(n) = $node_id
        RETURN type(r) as type, elementId(m) as target_id, properties(r) as properties
        """
        query_in = """
        MATCH (n)<-[r]-(m)
        WHERE elementId(n) = $node_id
        RETURN type(r) as type, elementId(m) as source_id, properties(r) as properties
        """
        with self.driver.session() as session:
            outgoing = list(session.run(query_out, node_id=node_id))
            incoming = list(session.run(query_in, node_id=node_id))
        return outgoing, incoming

    def _extract_names_and_aliases(self, node: Dict[str, Any]) -> List[str]:
        # Helper: flatten and clean all name/alias strings from node
        names = []
        name_val = node.get('name')
        if isinstance(name_val, str):
            names.append(name_val.strip().lower())
        elif isinstance(name_val, list):
            names.extend([n.strip().lower() for n in name_val if isinstance(n, str)])
        aliases_val = node.get('aliases', [])
        if isinstance(aliases_val, str):
            names.append(aliases_val.strip().lower())
        elif isinstance(aliases_val, list):
            for a in aliases_val:
                if isinstance(a, str):
                    names.append(a.strip().lower())
                elif isinstance(a, list):
                    names.extend([x.strip().lower() for x in a if isinstance(x, str)])
        return [n for n in names if n]

    def fuzzy_group_nodes(self, nodes: List[Dict[str, Any]]) -> List[Set[str]]:
        # Group nodes by fuzzy match over any name or alias
        groups = []
        seen = set()
        for i, node in enumerate(nodes):
            if node['id'] in seen:
                continue
            group = set([node['id']])
            names_i = self._extract_names_and_aliases(node)
            for j, other in enumerate(nodes):
                if i == j or other['id'] in seen:
                    continue
                names_j = self._extract_names_and_aliases(other)
                # Fuzzy match any name/alias between nodes
                match_found = False
                for ni in names_i:
                    for nj in names_j:
                        if self.is_fuzzy_match(ni, nj):
                            group.add(other['id'])
                            match_found = True
                            break
                    if match_found:
                        break
            if len(group) > 1:
                groups.append(group)
                seen.update(group)
        return groups

    def is_fuzzy_match(self, a: str, b: str) -> bool:
        if not a or not b:
            return False
        return difflib.SequenceMatcher(None, a, b).ratio() >= FUZZY_THRESHOLD

    def collect_duplicates_with_relationships_for_label(self, label: str) -> List[Dict[str, Any]]:
        nodes = self.fetch_nodes_by_label(label)
        node_map = {n['id']: n for n in nodes}
        groups = self.fuzzy_group_nodes(nodes)
        results = []
        for group in groups:
            group_nodes = [node_map[nid] for nid in group]
            rels = {}
            for node in group_nodes:
                out, inc = self.fetch_node_relationships(node['id'])
                rels[node['id']] = {
                    'outgoing': [dict(r) for r in out],
                    'incoming': [dict(r) for r in inc]
                }
            results.append({'node_ids': list(group), 'nodes': group_nodes, 'relationships': rels})
        return results

import json

def main():
    finder = Neo4jDuplicateFinder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        all_results = {}
        log_summary = []
        for label in finder.TARGET_LABELS:
            duplicates = finder.collect_duplicates_with_relationships_for_label(label)
            all_results[label] = duplicates
            # Logging: summary for this label
            total_nodes = len(finder.fetch_nodes_by_label(label))
            total_groups = len(duplicates)
            total_grouped_nodes = sum(len(g['nodes']) for g in duplicates)
            log_entry = {
                'node_type': label,
                'total_nodes': total_nodes,
                'duplicate_groups': total_groups,
                'total_nodes_in_groups': total_grouped_nodes,
                'groups': []
            }
            for idx, group in enumerate(duplicates, 1):
                names = [str(n.get('name')) for n in group['nodes']]
                log_entry['groups'].append({
                    'group_number': idx,
                    'names': names,
                    'node_ids': group['node_ids']
                })
            log_summary.append(log_entry)
            # Print concise summary for this label
            print(f"[{label}] Total nodes: {total_nodes}")
            print(f"[{label}] Found {total_groups} duplicate groups.")
            print(f"[{label}] Total nodes in groups: {total_grouped_nodes}")
            for g in log_entry['groups']:
                print(f"[{label}] Group {g['group_number']}: {g['names']}")
        # Write all duplicate groups and their relationships to a JSON file (by type)
        with open("duplicate_groups_by_type.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        # Write the structured log
        with open("deduplication_log.json", "w", encoding="utf-8") as f:
            json.dump(log_summary, f, indent=2, ensure_ascii=False)
    finally:
        finder.close()

if __name__ == "__main__":
    main()
