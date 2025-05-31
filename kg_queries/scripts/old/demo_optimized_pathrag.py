#!/usr/bin/env python3
"""
Optimized PathRAG Demonstration Script

This script demonstrates the optimized PathRAG retriever with the tuned parameters.
It provides a clean interface to test the retriever's performance and view the results.
"""

import argparse
import json
import logging
import sys
import time
from typing import Dict, Any, List

from graphrag_retriever import GraphRAGRetriever

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def format_node(node: Dict[str, Any]) -> str:
    """Format a node for display."""
    node_name = node["properties"].get("name", node["id"])
    if isinstance(node_name, list):
        node_name = ', '.join(str(n) for n in node_name)
    
    labels = ', '.join(node['labels'])
    
    # Get key properties
    properties = []
    for prop, value in node["properties"].items():
        if prop != "name":  # Skip name as it's already included
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            properties.append(f"{prop}: {value}")
    
    properties_str = "; ".join(properties) if properties else "No additional properties"
    
    return f"{node_name} ({labels}): {properties_str}"

def format_path(path: Dict[str, Any]) -> str:
    """Format a path for display."""
    result = [f"Path (length {path['length']}):"]
    
    for i, node in enumerate(path["nodes"]):
        # Format node
        node_name = node["properties"].get("name", node["id"])
        if isinstance(node_name, list):
            node_name = ', '.join(str(n) for n in node_name)
        
        result.append(f"  Node {i+1}: {node_name} ({', '.join(node['labels'])})")
        
        # Format relationship to next node if not the last node
        if i < path["length"]:
            rel = path["relationships"][i]
            rel_type = rel["type"]
            result.append(f"  → {rel_type} →")
    
    return "\n".join(result)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Optimized PathRAG Demo")
    parser.add_argument("query", help="Question to answer")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching for retrieval")
    parser.add_argument("--output-file", help="File to write results to (JSON format)")
    parser.add_argument("--max-communities", type=int, default=5, 
                        help="Maximum number of communities to retrieve (default: 5)")
    parser.add_argument("--max-path-length", type=int, default=3, 
                        help="Maximum path length in hops (default: 3)")
    parser.add_argument("--max-paths-per-entity", type=int, default=5, 
                        help="Maximum paths per entity pair (default: 5)")
    args = parser.parse_args()
    
    try:
        # Initialize GraphRAG retriever with optimized PathRAG parameters
        logger.info(f"Initializing GraphRAG retriever with optimized PathRAG parameters")
        retriever = GraphRAGRetriever(
            use_cache=not args.no_cache,
            pathrag_max_communities=args.max_communities,
            pathrag_max_path_length=args.max_path_length,
            pathrag_max_paths_per_entity=args.max_paths_per_entity
        )
        
        # Execute retrieval
        logger.info(f"Executing PathRAG retrieval for query: {args.query}")
        start_time = time.time()
        result = retriever.retrieve(args.query, strategy="pathrag")
        retrieval_time = time.time() - start_time
        logger.info(f"Retrieval completed in {retrieval_time:.3f}s with {result.total_results} results")
        
        # Print results
        print("\n=== Optimized PathRAG Retrieval Results ===")
        print(f"Query: {args.query}")
        print(f"Execution Time: {retrieval_time:.3f}s")
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
            
            print(f"\n=== Relevant Communities ({len(communities)}) ===")
            for i, community in enumerate(communities):
                print(f"  Community {community}: {community_entities[i] if i < len(community_entities) else 'No entities'}")
            
            # Print extracted entities from communities
            if "extracted_entities" in result.metadata:
                extracted_entities = result.metadata["extracted_entities"]
                print(f"\n=== Key Community Entities ({len(extracted_entities)}) ===")
                print(f"  {', '.join(extracted_entities)}")
            elif community_entities and isinstance(community_entities, list):
                print(f"\n=== Community Entities ===")
                for i, entity_list in enumerate(community_entities):
                    if entity_list:
                        print(f"  Community {communities[i] if i < len(communities) else 'Unknown'}: {entity_list}")
            else:
                print("\n=== No community entities found ===")
        
        # Print paths
        if result.paths:
            print(f"\n=== Relevant Paths ({len(result.paths)}) ===")
            for i, path in enumerate(result.paths):
                print(f"\n{format_path(path)}")
        
        # Print nodes if verbose
        if args.verbose and result.nodes:
            print(f"\n=== Nodes ({len(result.nodes)}) ===")
            for i, node in enumerate(result.nodes):
                print(f"\nNode {i+1}: {format_node(node)}")
        
        # Write results to file if specified
        if args.output_file:
            output = {
                "query": args.query,
                "retrieval_time": retrieval_time,
                "total_results": result.total_results,
                "entities": result.metadata.get("entities", []),
                "communities": result.metadata.get("communities", []),
                "paths_count": len(result.paths),
                "nodes_count": len(result.nodes),
                "parameters": {
                    "max_communities": args.max_communities,
                    "max_path_length": args.max_path_length,
                    "max_paths_per_entity": args.max_paths_per_entity,
                    "use_cache": not args.no_cache
                }
            }
            
            with open(args.output_file, "w") as f:
                json.dump(output, f, indent=2)
            logger.info(f"Results written to {args.output_file}")
        
        # Print summary
        print("\n=== Performance Summary ===")
        print(f"Retrieval Time: {retrieval_time:.3f}s")
        print(f"Total Results: {result.total_results}")
        print(f"Entities: {len(result.metadata.get('entities', []))}")
        print(f"Communities: {len(result.metadata.get('communities', []))}")
        print(f"Paths: {len(result.paths)}")
        print(f"Nodes: {len(result.nodes)}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
