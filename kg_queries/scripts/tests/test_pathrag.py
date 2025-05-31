#!/usr/bin/env python3
"""
Test script for the PathRAG retriever in GraphRAG.
This script demonstrates the PathRAG retriever's capabilities for community-aware path-based retrieval.
"""

import argparse
import logging
import sys
import time
from typing import List, Dict, Any

from graphrag_retriever import PathRAGRetriever, RetrievalResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def format_paths(paths: List[Dict[str, Any]], verbose: bool = False) -> None:
    """Format paths for display with improved readability."""
    print(f"\n=== Paths ({len(paths)}) ===")
    for i, path in enumerate(paths):
        print(f"\nPath {i+1}: Length {path['length']}")
        
        for j, node in enumerate(path["nodes"]):
            # Format node name
            node_name = node["properties"].get("name", node["id"])
            if isinstance(node_name, list):
                node_name = ', '.join(str(n) for n in node_name)
            
            # Format labels
            labels = ', '.join(node['labels'])
            
            print(f"  Node {j+1}: {node_name} ({labels})")
            
            # Print relationship to next node if not the last node
            if j < path["length"]:
                rel = path["relationships"][j]
                rel_type = rel["type"]
                
                # Get the start and end node IDs to determine direction
                start_id = rel.get('start_node')
                end_id = rel.get('end_node')
                
                # Determine if this relationship points to the next node or from it
                next_node_id = path["nodes"][j+1]["id"] if j+1 < len(path["nodes"]) else None
                
                if start_id == node["id"] and end_id == next_node_id:
                    # Current node is start, next node is end
                    print(f"  → {rel_type} →")
                elif end_id == node["id"] and start_id == next_node_id:
                    # Current node is end, next node is start
                    print(f"  ← {rel_type} ←")
                else:
                    # Direction can't be determined clearly
                    print(f"  ↔ {rel_type} ↔")


def format_communities(communities: List[int], community_entities) -> None:
    """Format community information for display."""
    print("\n=== Communities ===")
    for community_id in communities:
        if isinstance(community_entities, dict):
            entities = community_entities.get(str(community_id), [])
        else:
            # Handle the case where community_entities is a list
            entities = []
            for item in community_entities:
                if isinstance(item, list) and len(item) > 0:
                    entities.extend(item)
        
        print(f"\nCommunity {community_id}: {len(entities) if entities else 0} entities")
        if entities:
            # Format entities in columns
            max_entities_per_line = 4
            for i in range(0, len(entities), max_entities_per_line):
                chunk = entities[i:i+max_entities_per_line]
                print(f"  {', '.join(str(e) for e in chunk)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test PathRAG Retriever")
    parser.add_argument("query", help="Question to answer")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()
    
    try:
        # Initialize PathRAG retriever
        retriever = PathRAGRetriever()
        
        # Execute retrieval
        logger.info(f"Executing PathRAG retrieval for query: {args.query}")
        result = retriever.retrieve(args.query)
        
        # Print results
        print("\n=== PathRAG Retrieval Result ===")
        print(f"Query: {args.query}")
        print(f"Execution Time: {result.execution_time:.3f}s")
        print(f"Total Results: {result.total_results}")
        
        # Print extracted entities
        if "entities" in result.metadata:
            entities = result.metadata["entities"]
            print(f"\n=== Extracted Entities ({len(entities)}) ===")
            print(f"  {', '.join(entities)}")
        
        # Print community information
        if "communities" in result.metadata:
            communities = result.metadata["communities"]
            community_entities = result.metadata.get("community_entities", [])
            format_communities(communities, community_entities)
        
        # Print paths
        if result.paths:
            format_paths(result.paths, args.verbose)
        
        # Print nodes if verbose
        if args.verbose and result.nodes:
            print(f"\n=== Nodes ({len(result.nodes)}) ===")
            for i, node in enumerate(result.nodes):
                node_name = node["properties"].get("name", node["id"])
                if isinstance(node_name, list):
                    node_name = ', '.join(str(n) for n in node_name)
                print(f"\nNode {i+1}: {node_name} ({', '.join(node['labels'])})")
                
                for prop, value in node["properties"].items():
                    if prop != "name":  # Skip name as it's already displayed
                        if isinstance(value, list):
                            value = ', '.join(str(v) for v in value)
                        print(f"  {prop}: {value}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
