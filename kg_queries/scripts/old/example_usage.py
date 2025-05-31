#!/usr/bin/env python3
"""
Example usage of the GraphRAG retriever.

This script demonstrates how to use the GraphRAG retriever in different ways,
showing practical examples of each retrieval strategy.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import kg_query_utils
sys.path.append(str(Path(__file__).parent.parent))

from graphrag_retriever import GraphRAGRetriever


def example_entity_search():
    """Example of entity-centric search."""
    print("=== Entity-Centric Search Example ===")
    print("This strategy focuses on finding specific entities mentioned in the query.\n")
    
    retriever = GraphRAGRetriever()
    
    # Example queries that work well with entity search
    queries = [
        "Who is Frodo?",
        "Tell me about Gandalf",
        "What is the One Ring?",
        "Information about Mordor"
    ]
    
    for query in queries:
        print(f"Query: '{query}'")
        print("-" * 40)
        
        result = retriever.retrieve(query, strategy="entity", max_results=3)
        
        if result.nodes:
            print(f"Found {len(result.nodes)} entities:")
            for i, node in enumerate(result.nodes[:2]):  # Show first 2
                name = node["properties"].get("name", "Unknown")
                labels = ", ".join(node["labels"])
                print(f"  {i+1}. {name} ({labels})")
        else:
            print("No entities found.")
        
        print(f"Execution time: {result.execution_time:.3f}s\n")


def example_relationship_search():
    """Example of relationship-aware search."""
    print("=== Relationship-Aware Search Example ===")
    print("This strategy focuses on finding connections between entities.\n")
    
    retriever = GraphRAGRetriever()
    
    # Example queries that work well with relationship search
    queries = [
        "How is Frodo related to Bilbo?",
        "What is the connection between Gandalf and Saruman?",
        "How are the hobbits connected?",
        "What relationships does Aragorn have?"
    ]
    
    for query in queries:
        print(f"Query: '{query}'")
        print("-" * 40)
        
        result = retriever.retrieve(query, strategy="relationship", max_results=5)
        
        if result.paths:
            print(f"Found {len(result.paths)} paths:")
            for i, path in enumerate(result.paths[:2]):  # Show first 2
                print(f"  Path {i+1}: {path['length']} steps")
                for j, node in enumerate(path["nodes"]):
                    name = node["properties"].get("name", "Unknown")
                    print(f"    {j+1}. {name}")
                    if j < path["length"]:
                        rel = path["relationships"][j]
                        print(f"       ↓ {rel['type']} ↓")
        
        if result.relationships:
            print(f"Found {len(result.relationships)} direct relationships:")
            for i, rel in enumerate(result.relationships[:3]):  # Show first 3
                print(f"  {i+1}. {rel['type']}")
        
        if not result.paths and not result.relationships:
            print("No relationships found.")
        
        print(f"Execution time: {result.execution_time:.3f}s\n")


def example_hybrid_search():
    """Example of hybrid search."""
    print("=== Hybrid Search Example ===")
    print("This strategy combines entity and relationship search for comprehensive results.\n")
    
    retriever = GraphRAGRetriever()
    
    # Example queries that benefit from hybrid approach
    queries = [
        "Tell me about the Fellowship of the Ring",
        "What happened to the One Ring?",
        "Describe the relationship between hobbits and the Shire",
        "How did Frodo destroy the Ring?"
    ]
    
    for query in queries:
        print(f"Query: '{query}'")
        print("-" * 40)
        
        result = retriever.retrieve(query, strategy="hybrid", max_results=8)
        
        print(f"Comprehensive results:")
        print(f"  - Entities found: {len(result.nodes)}")
        print(f"  - Relationships found: {len(result.relationships)}")
        print(f"  - Paths found: {len(result.paths)}")
        
        if result.metadata:
            print(f"  - Strategy breakdown: {result.metadata}")
        
        # Show some key results
        if result.nodes:
            print(f"\nKey entities:")
            for i, node in enumerate(result.nodes[:3]):  # Show first 3
                name = node["properties"].get("name", "Unknown")
                labels = ", ".join(node["labels"])
                print(f"  {i+1}. {name} ({labels})")
        
        print(f"Execution time: {result.execution_time:.3f}s\n")


def example_programmatic_usage():
    """Example of using the retriever programmatically."""
    print("=== Programmatic Usage Example ===")
    print("This shows how to use the retriever in your own code.\n")
    
    # Initialize retriever
    retriever = GraphRAGRetriever(use_cache=True)
    
    # Example: Building a simple Q&A system
    questions = [
        "Who is the main character?",
        "What is the quest about?",
        "Who are the villains?"
    ]
    
    print("Simple Q&A System:")
    print("-" * 20)
    
    for question in questions:
        print(f"Q: {question}")
        
        # Get results
        result = retriever.retrieve(question, strategy="hybrid", max_results=5)
        
        # Process results to create a simple answer
        if result.nodes:
            # Find the most relevant node
            best_node = result.nodes[0]
            name = best_node["properties"].get("name", "Unknown")
            description = best_node["properties"].get("description", "No description available")
            
            # Truncate description if too long
            if len(description) > 150:
                description = description[:147] + "..."
            
            print(f"A: {name} - {description}")
        else:
            print("A: I couldn't find information about that.")
        
        print()


def example_json_output():
    """Example of getting JSON output for API usage."""
    print("=== JSON Output Example ===")
    print("This shows how to get structured JSON output for API integration.\n")
    
    retriever = GraphRAGRetriever()
    
    query = "Tell me about Frodo"
    result = retriever.retrieve(query, strategy="entity", max_results=3)
    
    # Convert to JSON
    import json
    from dataclasses import asdict
    
    json_result = asdict(result)
    
    print("JSON structure:")
    print(f"- strategy: {json_result['strategy']}")
    print(f"- query: {json_result['query']}")
    print(f"- execution_time: {json_result['execution_time']}")
    print(f"- total_results: {json_result['total_results']}")
    print(f"- nodes: {len(json_result['nodes'])} items")
    print(f"- relationships: {len(json_result['relationships'])} items")
    print(f"- paths: {len(json_result['paths'])} items")
    print(f"- metadata: {json_result['metadata']}")
    
    print(f"\nFirst node structure:")
    if json_result['nodes']:
        first_node = json_result['nodes'][0]
        print(f"- id: {first_node['id']}")
        print(f"- labels: {first_node['labels']}")
        print(f"- properties: {list(first_node['properties'].keys())}")
    
    print(f"\nFull JSON (first 300 chars):")
    json_str = json.dumps(json_result, indent=2)
    print(json_str[:300] + "..." if len(json_str) > 300 else json_str)


def main():
    """Run all examples."""
    print("GraphRAG Retriever Usage Examples")
    print("=" * 50)
    print("This script demonstrates different ways to use the GraphRAG retriever.\n")
    
    try:
        # Run examples
        example_entity_search()
        print("\n" + "="*60 + "\n")
        
        example_relationship_search()
        print("\n" + "="*60 + "\n")
        
        example_hybrid_search()
        print("\n" + "="*60 + "\n")
        
        example_programmatic_usage()
        print("\n" + "="*60 + "\n")
        
        example_json_output()
        
        print("\n" + "="*60)
        print("Examples complete! Try running the retriever with your own queries:")
        print("python graphrag_retriever.py \"Your question here\" --strategy hybrid")
        
    except Exception as e:
        print(f"Example failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
