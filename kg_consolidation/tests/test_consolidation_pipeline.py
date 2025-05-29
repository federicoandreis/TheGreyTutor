"""
Minimal test script for Knowledge Graph Consolidation routines (runs on the current database).
WARNING: This will operate on your actual database. Use with care!
"""
import os
from neo4j import GraphDatabase
from kg_consolidation.core.duplicate_detector import DuplicateDetector
from kg_consolidation.core.node_merger import NodeMerger
from kg_consolidation.core.relationship_discoverer import RelationshipDiscoverer
from kg_consolidation.core.conflict_resolver import ConflictResolver
from kg_consolidation.core.summary_consolidator import SummaryConsolidator
from kg_consolidation.core.community_analyzer import CommunityAnalyzer

def get_driver():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(user, password))

def main():
    driver = get_driver()
    print("--- Duplicate Detection ---")
    duplicate_detector = DuplicateDetector(driver)
    duplicates = duplicate_detector.find_duplicates()
    print(f"Found {len(duplicates)} duplicate groups.")
    for group in duplicates:
        print(group)

    print("\n--- Node Merging (DRY RUN) ---")
    node_merger = NodeMerger(driver)
    # Only print what would be merged (do not actually merge)
    for group in duplicates:
        print(f"Would merge nodes: {group.node_ids}")
        # Uncomment the next line to actually merge!
        # result = node_merger.merge_nodes(group.node_ids)
        # print(result)

    print("\n--- Relationship Discovery ---")
    rel_discoverer = RelationshipDiscoverer(driver)
    rels = rel_discoverer.find_relationships()
    print(f"Found {len(rels)} relationship candidates.")
    for rel in rels[:5]:
        print(rel)

    print("\n--- Conflict Detection ---")
    conflict_resolver = ConflictResolver(driver)
    conflicts = conflict_resolver.detect_conflicts()
    print(f"Found {len(conflicts)} conflict groups.")
    for conflict in conflicts[:5]:
        print(conflict)

    print("\n--- Summary Consolidation ---")
    summary_consolidator = SummaryConsolidator(driver)
    summary_conflicts = summary_consolidator.detect_summary_conflicts()
    print(f"Found {len(summary_conflicts)} summary conflicts.")
    for sc in summary_conflicts[:5]:
        print(sc)

    print("\n--- Community Analysis ---")
    community_analyzer = CommunityAnalyzer(driver)
    links = community_analyzer.find_inter_community_relationships()
    print(f"Found {len(links)} inter-community links.")
    for link in links[:5]:
        print(link)

    driver.close()

if __name__ == "__main__":
    main()
