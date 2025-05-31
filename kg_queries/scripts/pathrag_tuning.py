#!/usr/bin/env python3
"""
PathRAG Parameter Tuning Script

This script allows tuning of the PathRAG retriever parameters to optimize
performance and relevance for different query types.
"""

import argparse
import json
import logging
import sys
import time
from typing import Dict, Any, List, Optional, Tuple

from graphrag_retriever import PathRAGRetriever, RetrievalResult, GraphRAGRetriever

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Test queries for parameter tuning
TEST_QUERIES = [
    "What is the relationship between Frodo and the Ring of Power?",
    "How is Bilbo related to Frodo?",
    "What is the connection between Gandalf and Saruman?",
    "How did the Ring get from Gollum to Frodo?",
    "What is the path of the Fellowship from Rivendell to Mordor?"
]

# Parameter configurations to test
PARAMETER_CONFIGS = [
    # Format: (max_communities, max_path_length, max_paths_per_entity, description)
    (3, 3, 5, "Default configuration"),
    (5, 3, 5, "More communities"),
    (3, 4, 5, "Longer paths"),
    (3, 3, 8, "More paths per entity"),
    (5, 4, 8, "Maximum coverage"),
    (2, 2, 3, "Minimal configuration")
]


def run_with_params(
    query: str, 
    max_communities: int, 
    max_path_length: int, 
    max_paths_per_entity: int
) -> Tuple[RetrievalResult, float]:
    """
    Run the PathRAG retriever with specific parameter values.
    
    Args:
        query: The query to test
        max_communities: Maximum number of communities to retrieve
        max_path_length: Maximum path length (hops)
        max_paths_per_entity: Maximum paths per entity
        
    Returns:
        Tuple of (retrieval result, execution time)
    """
    # Create a GraphRAG retriever with specified PathRAG parameters
    retriever = GraphRAGRetriever(
        use_cache=False,
        pathrag_max_communities=max_communities,
        pathrag_max_path_length=max_path_length,
        pathrag_max_paths_per_entity=max_paths_per_entity
    )
    
    # Execute retrieval
    start_time = time.time()
    result = retriever.retrieve(query, strategy="pathrag")
    execution_time = time.time() - start_time
    
    return result, execution_time


def evaluate_result(result: RetrievalResult, execution_time: float) -> Dict[str, Any]:
    """
    Evaluate a retrieval result based on multiple metrics.
    
    Args:
        result: The retrieval result
        execution_time: Execution time in seconds
        
    Returns:
        Dictionary with evaluation metrics
    """
    # Extract metrics
    metrics = {
        "execution_time": execution_time,
        "total_results": result.total_results,
        "node_count": len(result.nodes) if result.nodes else 0,
        "relationship_count": len(result.relationships) if result.relationships else 0,
        "path_count": len(result.paths) if result.paths else 0,
        "avg_path_length": 0,
        "unique_entity_count": 0,
        "community_count": len(result.metadata.get("communities", [])),
        "entity_count": len(result.metadata.get("entities", [])),
    }
    
    # Calculate average path length
    if result.paths:
        path_lengths = [path.get("length", 0) for path in result.paths]
        metrics["avg_path_length"] = sum(path_lengths) / len(path_lengths)
    
    # Count unique entities in nodes
    if result.nodes:
        unique_entities = set()
        for node in result.nodes:
            node_id = node.get("id")
            if node_id:
                unique_entities.add(node_id)
        metrics["unique_entity_count"] = len(unique_entities)
    
    return metrics


def run_parameter_tuning() -> Dict[str, Any]:
    """
    Run parameter tuning across all configurations and queries.
    
    Returns:
        Dictionary with tuning results
    """
    results = {
        "queries": {},
        "configs": {},
        "summary": {}
    }
    
    # Test each query with each parameter configuration
    for query in TEST_QUERIES:
        query_results = []
        
        for config in PARAMETER_CONFIGS:
            max_communities, max_path_length, max_paths_per_entity, description = config
            
            logger.info(f"Testing query with {description} configuration: {query}")
            logger.info(f"Parameters: communities={max_communities}, path_length={max_path_length}, paths_per_entity={max_paths_per_entity}")
            
            try:
                # Run retrieval with parameters
                result, execution_time = run_with_params(
                    query, max_communities, max_path_length, max_paths_per_entity
                )
                
                # Evaluate result
                metrics = evaluate_result(result, execution_time)
                
                # Store results
                config_key = f"c{max_communities}_p{max_path_length}_e{max_paths_per_entity}"
                query_results.append({
                    "config": config_key,
                    "description": description,
                    "metrics": metrics
                })
                
                logger.info(f"Configuration {description} completed in {execution_time:.3f}s with {metrics['total_results']} results")
                
                # Update config summary if not already present
                if config_key not in results["configs"]:
                    results["configs"][config_key] = {
                        "description": description,
                        "parameters": {
                            "max_communities": max_communities,
                            "max_path_length": max_path_length,
                            "max_paths_per_entity": max_paths_per_entity
                        },
                        "avg_metrics": {
                            "execution_time": 0,
                            "total_results": 0,
                            "node_count": 0,
                            "relationship_count": 0,
                            "path_count": 0,
                            "avg_path_length": 0,
                            "unique_entity_count": 0,
                            "community_count": 0,
                            "entity_count": 0
                        },
                        "query_count": 0
                    }
                
                # Update running totals for config
                config_summary = results["configs"][config_key]
                config_summary["query_count"] += 1
                for metric, value in metrics.items():
                    config_summary["avg_metrics"][metric] += value
                
            except Exception as e:
                logger.error(f"Error testing configuration {description}: {str(e)}")
                query_results.append({
                    "config": f"c{max_communities}_p{max_path_length}_e{max_paths_per_entity}",
                    "description": description,
                    "error": str(e)
                })
        
        # Store query results
        results["queries"][query] = query_results
    
    # Calculate averages for each configuration
    for config_key, config_data in results["configs"].items():
        query_count = config_data["query_count"]
        if query_count > 0:
            for metric in config_data["avg_metrics"]:
                config_data["avg_metrics"][metric] /= query_count
    
    # Calculate overall best configuration based on different priorities
    best_configs = {
        "balanced": None,
        "speed": None,
        "coverage": None,
        "relevance": None
    }
    
    # Find best configurations
    if results["configs"]:
        # Best for speed (lowest execution time)
        best_configs["speed"] = min(
            results["configs"].items(),
            key=lambda x: x[1]["avg_metrics"]["execution_time"]
        )[0]
        
        # Best for coverage (highest total results)
        best_configs["coverage"] = max(
            results["configs"].items(),
            key=lambda x: x[1]["avg_metrics"]["total_results"]
        )[0]
        
        # Best for relevance (highest unique entity count)
        best_configs["relevance"] = max(
            results["configs"].items(),
            key=lambda x: x[1]["avg_metrics"]["unique_entity_count"]
        )[0]
        
        # Best balanced (score based on multiple factors)
        def balanced_score(config_data):
            metrics = config_data["avg_metrics"]
            # Normalize execution time (lower is better)
            time_factor = 1.0 / (1.0 + metrics["execution_time"])
            # Coverage and relevance factors (higher is better)
            coverage_factor = metrics["total_results"] / 20.0  # Normalize to ~1.0
            relevance_factor = metrics["unique_entity_count"] / 10.0  # Normalize to ~1.0
            # Combined score with weights
            return (0.3 * time_factor) + (0.4 * coverage_factor) + (0.3 * relevance_factor)
        
        best_configs["balanced"] = max(
            results["configs"].items(),
            key=lambda x: balanced_score(x[1])
        )[0]
    
    # Add best configs to summary
    results["summary"]["best_configs"] = best_configs
    
    return results


def print_tuning_summary(results: Dict[str, Any]) -> None:
    """Print a summary of parameter tuning results."""
    print("\n=== PathRAG Parameter Tuning Results ===")
    
    # Print configuration summaries
    print("\n--- Configuration Performance ---")
    for config_key, config_data in results["configs"].items():
        metrics = config_data["avg_metrics"]
        params = config_data["parameters"]
        
        print(f"\n{config_data['description']} ({config_key}):")
        print(f"  Parameters: communities={params['max_communities']}, path_length={params['max_path_length']}, paths_per_entity={params['max_paths_per_entity']}")
        print(f"  Avg Execution Time: {metrics['execution_time']:.3f}s")
        print(f"  Avg Total Results: {metrics['total_results']:.1f}")
        print(f"  Avg Path Count: {metrics['path_count']:.1f}")
        print(f"  Avg Path Length: {metrics['avg_path_length']:.1f}")
        print(f"  Avg Unique Entities: {metrics['unique_entity_count']:.1f}")
    
    # Print best configurations
    if "best_configs" in results.get("summary", {}):
        best_configs = results["summary"]["best_configs"]
        
        print("\n--- Best Configurations ---")
        for priority, config_key in best_configs.items():
            if config_key:
                config_data = results["configs"][config_key]
                params = config_data["parameters"]
                print(f"\nBest for {priority.upper()}: {config_data['description']} ({config_key})")
                print(f"  Parameters: communities={params['max_communities']}, path_length={params['max_path_length']}, paths_per_entity={params['max_paths_per_entity']}")
    
    # Print recommendations
    print("\n--- Recommendations ---")
    if "balanced" in results.get("summary", {}).get("best_configs", {}):
        balanced_key = results["summary"]["best_configs"]["balanced"]
        if balanced_key:
            balanced_config = results["configs"][balanced_key]
            params = balanced_config["parameters"]
            
            print(f"\nRecommended configuration: {balanced_config['description']}")
            print(f"  max_communities = {params['max_communities']}")
            print(f"  max_path_length = {params['max_path_length']}")
            print(f"  max_paths_per_entity = {params['max_paths_per_entity']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PathRAG Parameter Tuning")
    parser.add_argument("--output", choices=["text", "json"], default="text",
                       help="Output format (text or JSON)")
    parser.add_argument("--output-file", help="File to write results to")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()
    
    try:
        logger.info("Starting PathRAG parameter tuning")
        
        # Run parameter tuning
        results = run_parameter_tuning()
        
        # Output results
        if args.output == "json":
            output = results
            
            if args.output_file:
                with open(args.output_file, "w") as f:
                    json.dump(output, f, indent=2)
            else:
                print(json.dumps(output, indent=2))
        else:
            print_tuning_summary(results)
            
            if args.output_file:
                with open(args.output_file, "w") as f:
                    f.write("=== PathRAG Parameter Tuning Results ===\n")
                    # Add more detailed results as needed
        
        logger.info("Parameter tuning completed successfully")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
