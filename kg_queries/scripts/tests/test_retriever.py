#!/usr/bin/env python3
"""
Test script for the GraphRAG retriever.

This script tests the basic functionality of the GraphRAG retriever
with simple queries to ensure everything is working correctly.
"""

import sys
import os
from pathlib import Path

# Update import to use parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from graphrag_retriever import GraphRAGRetriever


def test_basic_functionality():
    """Test basic functionality of the retriever."""
    print("=== Testing GraphRAG Retriever ===\n")
    
    # Initialize retriever
    retriever = GraphRAGRetriever(use_cache=False)  # Disable cache for testing
    
    # Test queries
    test_queries = [
        ("Who is Frodo?", "entity"),
        ("Tell me about the Ring", "entity"),
        ("How is Frodo related to Bilbo?", "relationship"),
        ("What is the One Ring?", "hybrid")
    ]
    
    for query, strategy in test_queries:
        print(f"Testing query: '{query}' with strategy: {strategy}")
        print("-" * 50)
        
        try:
            result = retriever.retrieve(query, strategy=strategy, max_results=5)
            
            print(f"✓ Query executed successfully")
            print(f"  - Strategy: {result.strategy}")
            print(f"  - Execution time: {result.execution_time:.3f}s")
            print(f"  - Total results: {result.total_results}")
            print(f"  - Nodes found: {len(result.nodes)}")
            print(f"  - Relationships found: {len(result.relationships)}")
            print(f"  - Paths found: {len(result.paths)}")
            
            if result.metadata:
                print(f"  - Metadata: {result.metadata}")
            
            # Show first result if available
            if result.nodes:
                first_node = result.nodes[0]
                node_name = first_node["properties"].get("name", "Unknown")
                print(f"  - First node: {node_name} ({', '.join(first_node['labels'])})")
            
        except Exception as e:
            print(f"✗ Query failed: {str(e)}")
        
        print("\n")


def test_caching():
    """Test caching functionality."""
    print("=== Testing Caching ===\n")
    
    # Initialize retriever with caching
    retriever = GraphRAGRetriever(use_cache=True)
    
    query = "Who is Frodo?"
    strategy = "entity"
    
    print(f"Testing caching with query: '{query}'")
    print("-" * 40)
    
    # First execution (should cache)
    print("First execution (should cache):")
    result1 = retriever.retrieve(query, strategy=strategy, max_results=5)
    print(f"  - Execution time: {result1.execution_time:.3f}s")
    
    # Second execution (should use cache)
    print("Second execution (should use cache):")
    result2 = retriever.retrieve(query, strategy=strategy, max_results=5)
    print(f"  - Execution time: {result2.execution_time:.3f}s")
    
    # Compare results
    if result1.total_results == result2.total_results:
        print("✓ Cache working correctly - same results returned")
    else:
        print("✗ Cache issue - different results returned")
    
    if result2.execution_time < result1.execution_time:
        print("✓ Cache performance benefit observed")
    else:
        print("? Cache performance benefit not clear")
    
    print("\n")


def test_output_formats():
    """Test different output formats."""
    print("=== Testing Output Formats ===\n")
    
    retriever = GraphRAGRetriever(use_cache=False)
    query = "Tell me about Frodo"
    
    print(f"Testing output formats with query: '{query}'")
    print("-" * 40)
    
    try:
        result = retriever.retrieve(query, strategy="entity", max_results=3)
        
        print("Text format:")
        retriever.print_result(result, verbose=False)
        
        print("\n" + "="*50 + "\n")
        
        print("JSON format (first 500 chars):")
        import json
        from dataclasses import asdict
        json_output = json.dumps(asdict(result), indent=2)
        print(json_output[:500] + "..." if len(json_output) > 500 else json_output)
        
    except Exception as e:
        print(f"✗ Output format test failed: {str(e)}")
    
    print("\n")


def main():
    """Run all tests."""
    print("GraphRAG Retriever Test Suite")
    print("=" * 50)
    
    try:
        # Test basic functionality
        test_basic_functionality()
        
        # Test caching
        test_caching()
        
        # Test output formats
        test_output_formats()
        
        print("=== Test Suite Complete ===")
        print("If you see ✓ marks above, the retriever is working correctly!")
        
    except Exception as e:
        print(f"Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
