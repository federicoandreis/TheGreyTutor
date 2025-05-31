#!/usr/bin/env python3
"""
PathRAG LLM Integration Module

This module demonstrates how to integrate the PathRAG retriever with an LLM
to generate comprehensive answers based on knowledge graph retrieval.
"""

import argparse
import json
import logging
import sys
import time
import os
from typing import Dict, Any, List, Optional

from graphrag_retriever import GraphRAGRetriever, RetrievalResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# LLM API integration
try:
    import openai
    from dotenv import load_dotenv
    load_dotenv()
    OPENAI_AVAILABLE = True
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("OpenAI client initialized successfully")
except ImportError as e:
    logger.warning(f"OpenAI package or dotenv not found: {e}. Using mock LLM implementation.")
    OPENAI_AVAILABLE = False
except Exception as e:
    logger.warning(f"Error initializing OpenAI client: {e}. Using mock LLM implementation.")
    OPENAI_AVAILABLE = False

# LLM response cache to avoid redundant API calls
LLM_CACHE = {}

def call_llm(prompt: str, use_cache: bool = True) -> str:
    """
    Call an LLM API to generate a response based on the provided prompt.
    
    Args:
        prompt: The prompt to send to the LLM
        use_cache: Whether to use cached responses (default: True)
        
    Returns:
        The LLM's response
    """
    # Check cache first if enabled
    if use_cache and prompt in LLM_CACHE:
        logger.info("Using cached LLM response")
        return LLM_CACHE[prompt]
    
    # Log prompt (truncated for readability)
    logger.info("Calling LLM with prompt (truncated):\n" + prompt[:500] + "...")
    
    # System prompt for the LLM
    system_prompt = (
        "You are a knowledgeable assistant with expertise in Tolkien's Middle-earth. "
        "Your task is to provide comprehensive, accurate answers about the Lord of the Rings universe "
        "based on the knowledge graph information provided. Focus on relationships between entities "
        "and use the path information to explain connections. Be detailed but concise."
    )
    
    # Use OpenAI if available, otherwise use mock implementation
    if OPENAI_AVAILABLE:
        try:
            # Call OpenAI API using the global client
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Using the same model as in other project files
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=1000
            )
            response = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            response = f"[API ERROR] Failed to get response from LLM API: {str(e)}"
    else:
        # Use mock implementation
        response = "[MOCK] This is a mock LLM response. Install the OpenAI package for real responses."
    
    # Cache response if caching is enabled
    if use_cache:
        LLM_CACHE[prompt] = response
    
    return response


def format_node_for_llm(node: Dict[str, Any]) -> str:
    """Format a node for inclusion in an LLM prompt."""
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


def format_path_for_llm(path: Dict[str, Any]) -> str:
    """Format a path for inclusion in an LLM prompt."""
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
            
            # Get the start and end node IDs to determine direction
            start_id = rel.get('start_node')
            end_id = rel.get('end_node')
            
            # Determine if this relationship points to the next node or from it
            next_node_id = path["nodes"][i+1]["id"] if i+1 < len(path["nodes"]) else None
            
            if start_id == node["id"] and end_id == next_node_id:
                # Current node is start, next node is end
                result.append(f"  → {rel_type} →")
            elif end_id == node["id"] and start_id == next_node_id:
                # Current node is end, next node is start
                result.append(f"  ← {rel_type} ←")
            else:
                # Direction can't be determined clearly
                result.append(f"  ↔ {rel_type} ↔")
    
    return "\n".join(result)


def create_llm_prompt(query: str, result: RetrievalResult) -> str:
    """
    Create a prompt for the LLM based on the retrieval result.
    
    This formats the knowledge graph information in a way that's easy for the LLM
    to understand and use in generating a comprehensive answer.
    """
    prompt_parts = [
        "You are an AI assistant with access to a knowledge graph about Tolkien's Middle-earth.",
        "Use the following information from the knowledge graph to answer the user's question.",
        f"\nUser Question: {query}\n",
        "\n=== Knowledge Graph Information ===\n"
    ]
    
    # Add extracted entities
    if "entities" in result.metadata:
        entities = result.metadata["entities"]
        prompt_parts.append(f"Extracted Entities: {', '.join(entities)}\n")
    
    # Add community information
    if "communities" in result.metadata:
        communities = result.metadata["communities"]
        community_entities = result.metadata.get("community_entities", {})
        
        prompt_parts.append(f"Relevant Communities: {', '.join(str(c) for c in communities)}")
        
        if isinstance(community_entities, dict):
            for community_id in communities:
                entities = community_entities.get(str(community_id), [])
                if entities:
                    prompt_parts.append(f"Community {community_id} entities: {', '.join(str(e) for e in entities[:10])}")
    
    # Add key nodes
    if result.nodes:
        prompt_parts.append("\nKey Entities:")
        for node in result.nodes[:10]:  # Limit to first 10 nodes to keep prompt size reasonable
            prompt_parts.append(format_node_for_llm(node))
    
    # Add paths
    if result.paths:
        prompt_parts.append("\nRelevant Paths:")
        for path in result.paths:
            prompt_parts.append(format_path_for_llm(path))
    
    # Add instructions for the LLM
    prompt_parts.append("\n=== Instructions ===")
    prompt_parts.append("Based on the knowledge graph information above, please answer the user's question.")
    prompt_parts.append("If the information is insufficient, say so and explain what's missing.")
    prompt_parts.append("Focus on the relationships and paths between entities to provide a comprehensive answer.")
    
    return "\n".join(prompt_parts)


def process_query(query: str, verbose: bool = False, use_cache: bool = True) -> str:
    """
    Process a user query using PathRAG retrieval and LLM integration.
    
    Args:
        query: The user's question
        verbose: Whether to print verbose output
        use_cache: Whether to use caching for both retrieval and LLM calls
        
    Returns:
        The LLM's answer to the question
    """
    # Initialize GraphRAG retriever with optimized PathRAG parameters
    retriever = GraphRAGRetriever(
        use_cache=use_cache,
        pathrag_max_communities=5,  # Optimized value from parameter tuning
        pathrag_max_path_length=3,
        pathrag_max_paths_per_entity=5
    )
    
    # Execute retrieval using the PathRAG strategy
    logger.info(f"Executing PathRAG retrieval for query: {query}")
    start_time = time.time()
    result = retriever.retrieve(query, strategy="pathrag")
    retrieval_time = time.time() - start_time
    logger.info(f"Retrieval completed in {retrieval_time:.3f}s with {result.total_results} results")
    
    # Create LLM prompt
    prompt = create_llm_prompt(query, result)
    
    # Call LLM
    logger.info("Calling LLM for answer synthesis")
    start_time = time.time()
    answer = call_llm(prompt, use_cache=use_cache)
    llm_time = time.time() - start_time
    logger.info(f"LLM processing completed in {llm_time:.3f}s")
    
    if verbose:
        print("\n=== Retrieval Result ===")
        print(f"Query: {query}")
        print(f"Retrieval Time: {retrieval_time:.3f}s")
        print(f"LLM Processing Time: {llm_time:.3f}s")
        print(f"Total Processing Time: {retrieval_time + llm_time:.3f}s")
        
        # Print extracted entities
        if "entities" in result.metadata:
            entities = result.metadata["entities"]
            print(f"\nExtracted Entities ({len(entities)}): {', '.join(entities)}")
        
        # Print paths summary
        if result.paths:
            print(f"\nRetrieved {len(result.paths)} paths")
            for i, path in enumerate(result.paths):
                print(f"  Path {i+1}: {len(path['nodes'])} nodes, {path['length']} relationships")
    
    return answer


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PathRAG LLM Integration Demo")
    parser.add_argument("query", help="Question to answer")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching for both retrieval and LLM calls")
    parser.add_argument("--output-file", help="File to write results to (JSON format)")
    parser.add_argument("--max-communities", type=int, default=5, help="Maximum number of communities to retrieve")
    parser.add_argument("--max-path-length", type=int, default=3, help="Maximum path length in hops")
    parser.add_argument("--max-paths-per-entity", type=int, default=5, help="Maximum paths per entity pair")
    args = parser.parse_args()

    try:
        # Process query
        start_time = time.time()
        answer = process_query(
            query=args.query, 
            verbose=args.verbose,
            use_cache=not args.no_cache
        )
        total_time = time.time() - start_time

        # Print answer
        print("\n=== LLM Answer ===\n")
        print(answer)
        print(f"\nTotal processing time: {total_time:.3f}s")

        # Write results to file if specified
        if args.output_file:
            output = {
                "query": args.query,
                "answer": answer,
                "processing_time": total_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
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
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
