#!/usr/bin/env python3
"""
Comprehensive Test Suite for PathRAG Retriever

This script provides a structured test suite to evaluate the PathRAG retriever's
performance across different query types and compare it with other retrieval strategies.
"""

import argparse
import json
import logging
import sys
import time
from typing import Dict, Any, List, Optional, Tuple

from graphrag_retriever import (
    GraphRAGRetriever,
    PathRAGRetriever,
    EntityCentricRetriever,
    RelationshipAwareRetriever,
    HybridRetriever,
    RetrievalResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Test query categories and examples
TEST_QUERIES = {
    "entity_centric": [
        "Who is Frodo Baggins?",
        "What is the Shire?",
        "Tell me about Gandalf the Grey.",
        "What is the One Ring?",
        "Who is Aragorn son of Arathorn?"
    ],
    "relationship_focused": [
        "What is the relationship between Frodo and the Ring of Power?",
        "How is Bilbo related to Frodo?",
        "What is the connection between Gandalf and Saruman?",
        "How did Gollum obtain the Ring?",
        "What is the relationship between Aragorn and Arwen?"
    ],
    "multi_entity": [
        "Compare Frodo, Sam, and Gollum.",
        "What happened between Gandalf, Saruman, and the White Council?",
        "Describe the journey of Frodo, Sam, and the Ring to Mount Doom.",
        "How did Aragorn, Legolas, and Gimli help in the War of the Ring?",
        "What is the significance of Rivendell, Lothlorien, and Minas Tirith?"
    ],
    "complex_paths": [
        "How did the Ring get from Gollum to Frodo?",
        "Trace the lineage of the kings of Gondor.",
        "What is the path of the Fellowship from Rivendell to Mordor?",
        "How did the Rings of Power influence the different races of Middle-earth?",
        "What is the history of the sword Narsil/Andúril?"
    ],
    "community_based": [
        "Tell me about the Hobbits of the Shire.",
        "What are the key events of the War of the Ring?",
        "Describe the Elven realms in Middle-earth.",
        "What are the different races that inhabit Middle-earth?",
        "Explain the Council of Elrond and its participants."
    ]
}

# Strategies to test
STRATEGIES = ["entity", "relationship", "hybrid", "pathrag"]


def run_test_query(query: str, strategies: List[str] = None) -> Dict[str, Any]:
    """
    Run a test query using multiple retrieval strategies and collect results.
    
    Args:
        query: The query to test
        strategies: List of strategies to test (defaults to all strategies)
        
    Returns:
        Dictionary with test results
    """
    if strategies is None:
        strategies = STRATEGIES
    
    retriever = GraphRAGRetriever(use_cache=False)  # Disable cache for fair comparison
    
    results = {
        "query": query,
        "timestamp": time.time(),
        "strategies": {}
    }
    
    for strategy in strategies:
        logger.info(f"Testing query with {strategy} strategy: {query}")
        
        try:
            start_time = time.time()
            result = retriever.retrieve(query, strategy=strategy)
            execution_time = time.time() - start_time
            
            # Collect metrics
            metrics = {
                "execution_time": execution_time,
                "total_results": result.total_results,
                "node_count": len(result.nodes) if result.nodes else 0,
                "relationship_count": len(result.relationships) if result.relationships else 0,
                "path_count": len(result.paths) if result.paths else 0,
                "metadata": result.metadata
            }
            
            results["strategies"][strategy] = metrics
            logger.info(f"Strategy {strategy} completed in {execution_time:.3f}s with {result.total_results} results")
            
        except Exception as e:
            logger.error(f"Error testing {strategy} strategy: {str(e)}")
            results["strategies"][strategy] = {
                "error": str(e)
            }
    
    return results


def analyze_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze test results and generate summary statistics.
    
    Args:
        results: List of test results
        
    Returns:
        Dictionary with analysis results
    """
    analysis = {
        "total_queries": len(results),
        "successful_queries": 0,
        "failed_queries": 0,
        "strategies": {},
        "query_categories": {},
        "comparative_analysis": {}
    }
    
    # Initialize strategy metrics
    for strategy in STRATEGIES:
        analysis["strategies"][strategy] = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_execution_time": 0,
            "avg_total_results": 0,
            "avg_node_count": 0,
            "avg_relationship_count": 0,
            "avg_path_count": 0
        }
    
    # Process results
    for result in results:
        query = result["query"]
        category = None
        
        # Determine query category
        for cat, queries in TEST_QUERIES.items():
            if query in queries:
                category = cat
                break
        
        if category not in analysis["query_categories"]:
            analysis["query_categories"][category] = {
                "total_queries": 0,
                "strategies": {}
            }
            for strategy in STRATEGIES:
                analysis["query_categories"][category]["strategies"][strategy] = {
                    "successful_queries": 0,
                    "avg_execution_time": 0,
                    "avg_total_results": 0
                }
        
        analysis["query_categories"][category]["total_queries"] += 1
        
        # Process strategy results
        for strategy, metrics in result["strategies"].items():
            if "error" in metrics:
                analysis["strategies"][strategy]["failed_queries"] += 1
                analysis["failed_queries"] += 1
                continue
            
            # Update strategy metrics
            analysis["strategies"][strategy]["total_queries"] += 1
            analysis["strategies"][strategy]["successful_queries"] += 1
            analysis["successful_queries"] += 1
            
            # Update averages (running sum, will divide later)
            analysis["strategies"][strategy]["avg_execution_time"] += metrics["execution_time"]
            analysis["strategies"][strategy]["avg_total_results"] += metrics["total_results"]
            analysis["strategies"][strategy]["avg_node_count"] += metrics["node_count"]
            analysis["strategies"][strategy]["avg_relationship_count"] += metrics["relationship_count"]
            analysis["strategies"][strategy]["avg_path_count"] += metrics["path_count"]
            
            # Update category metrics
            analysis["query_categories"][category]["strategies"][strategy]["successful_queries"] += 1
            analysis["query_categories"][category]["strategies"][strategy]["avg_execution_time"] += metrics["execution_time"]
            analysis["query_categories"][category]["strategies"][strategy]["avg_total_results"] += metrics["total_results"]
    
    # Calculate averages
    for strategy, metrics in analysis["strategies"].items():
        if metrics["successful_queries"] > 0:
            metrics["avg_execution_time"] /= metrics["successful_queries"]
            metrics["avg_total_results"] /= metrics["successful_queries"]
            metrics["avg_node_count"] /= metrics["successful_queries"]
            metrics["avg_relationship_count"] /= metrics["successful_queries"]
            metrics["avg_path_count"] /= metrics["successful_queries"]
    
    # Calculate category averages
    for category, cat_metrics in analysis["query_categories"].items():
        for strategy, metrics in cat_metrics["strategies"].items():
            if metrics["successful_queries"] > 0:
                metrics["avg_execution_time"] /= metrics["successful_queries"]
                metrics["avg_total_results"] /= metrics["successful_queries"]
    
    # Comparative analysis
    if "pathrag" in analysis["strategies"] and analysis["strategies"]["pathrag"]["successful_queries"] > 0:
        pathrag_metrics = analysis["strategies"]["pathrag"]
        
        for strategy in ["entity", "relationship", "hybrid"]:
            if strategy in analysis["strategies"] and analysis["strategies"][strategy]["successful_queries"] > 0:
                strategy_metrics = analysis["strategies"][strategy]
                
                # Safely calculate ratios by avoiding division by zero
                def safe_ratio(a, b, default=1.0):
                    return a / b if b > 0 else default
                
                analysis["comparative_analysis"][f"pathrag_vs_{strategy}"] = {
                    "execution_time_ratio": safe_ratio(pathrag_metrics["avg_execution_time"], strategy_metrics["avg_execution_time"]),
                    "total_results_ratio": safe_ratio(pathrag_metrics["avg_total_results"], strategy_metrics["avg_total_results"]),
                    "node_count_ratio": safe_ratio(pathrag_metrics["avg_node_count"], strategy_metrics["avg_node_count"]),
                    "relationship_count_ratio": safe_ratio(pathrag_metrics["avg_relationship_count"], strategy_metrics["avg_relationship_count"]),
                    "path_count_ratio": safe_ratio(pathrag_metrics["avg_path_count"], strategy_metrics["avg_path_count"])
                }
    
    return analysis


def print_results_summary(analysis: Dict[str, Any]) -> None:
    """Print a summary of test results."""
    print("\n=== PathRAG Test Suite Results ===")
    print(f"Total Queries: {analysis['total_queries']}")
    print(f"Successful Queries: {analysis['successful_queries']}")
    print(f"Failed Queries: {analysis['failed_queries']}")
    
    print("\n--- Strategy Performance ---")
    for strategy, metrics in analysis["strategies"].items():
        if metrics["successful_queries"] > 0:
            print(f"\n{strategy.upper()} Strategy:")
            print(f"  Successful Queries: {metrics['successful_queries']}/{metrics['total_queries']}")
            print(f"  Avg Execution Time: {metrics['avg_execution_time']:.3f}s")
            print(f"  Avg Total Results: {metrics['avg_total_results']:.1f}")
            print(f"  Avg Node Count: {metrics['avg_node_count']:.1f}")
            print(f"  Avg Relationship Count: {metrics['avg_relationship_count']:.1f}")
            print(f"  Avg Path Count: {metrics['avg_path_count']:.1f}")
    
    print("\n--- Query Category Performance ---")
    for category, cat_metrics in analysis["query_categories"].items():
        print(f"\n{category.upper()} Queries:")
        for strategy, metrics in cat_metrics["strategies"].items():
            if metrics["successful_queries"] > 0:
                print(f"  {strategy.upper()}: {metrics['avg_execution_time']:.3f}s, {metrics['avg_total_results']:.1f} results")
    
    print("\n--- Comparative Analysis ---")
    for comparison, metrics in analysis.get("comparative_analysis", {}).items():
        print(f"\n{comparison.upper()}:")
        print(f"  Execution Time Ratio: {metrics['execution_time_ratio']:.2f}x")
        print(f"  Total Results Ratio: {metrics['total_results_ratio']:.2f}x")
        print(f"  Node Count Ratio: {metrics['node_count_ratio']:.2f}x")
        print(f"  Relationship Count Ratio: {metrics['relationship_count_ratio']:.2f}x")
        print(f"  Path Count Ratio: {metrics['path_count_ratio']:.2f}x")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PathRAG Retriever Test Suite")
    parser.add_argument("--categories", nargs="+", choices=list(TEST_QUERIES.keys()),
                       help="Query categories to test (default: all)")
    parser.add_argument("--strategies", nargs="+", choices=STRATEGIES,
                       help="Retrieval strategies to test (default: all)")
    parser.add_argument("--output", choices=["text", "json"], default="text",
                       help="Output format (text or JSON)")
    parser.add_argument("--output-file", help="File to write results to")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    args = parser.parse_args()
    
    try:
        # Determine which categories to test
        categories = args.categories if args.categories else list(TEST_QUERIES.keys())
        strategies = args.strategies if args.strategies else STRATEGIES
        
        # Collect test queries
        test_queries = []
        for category in categories:
            test_queries.extend(TEST_QUERIES[category])
        
        logger.info(f"Running test suite with {len(test_queries)} queries across {len(categories)} categories")
        logger.info(f"Testing strategies: {', '.join(strategies)}")
        
        # Run tests
        results = []
        for query in test_queries:
            result = run_test_query(query, strategies)
            results.append(result)
        
        # Analyze results
        analysis = analyze_results(results)
        
        # Output results
        if args.output == "json":
            output = {
                "results": results,
                "analysis": analysis
            }
            
            if args.output_file:
                with open(args.output_file, "w") as f:
                    json.dump(output, f, indent=2)
            else:
                print(json.dumps(output, indent=2))
        else:
            print_results_summary(analysis)
            
            if args.output_file:
                with open(args.output_file, "w") as f:
                    f.write("=== PathRAG Test Suite Results ===\n")
                    f.write(f"Total Queries: {analysis['total_queries']}\n")
                    f.write(f"Successful Queries: {analysis['successful_queries']}\n")
                    f.write(f"Failed Queries: {analysis['failed_queries']}\n")
                    # Add more detailed results as needed
        
        logger.info("Test suite completed successfully")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
