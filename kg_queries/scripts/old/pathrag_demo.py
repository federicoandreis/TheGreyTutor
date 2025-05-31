#!/usr/bin/env python3
"""
PathRAG Demo Script

This script demonstrates the optimized PathRAG retriever with LLM integration.
It provides a simple interface to ask questions about Tolkien's Middle-earth
and get answers based on knowledge graph retrieval.
"""

import argparse
import json
import logging
import sys
import time
import os
from typing import Dict, Any, List, Optional

from graphrag_retriever import GraphRAGRetriever

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
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

def create_llm_prompt(query: str, retrieval_result: Any) -> str:
    """
    Create a prompt for the LLM based on the retrieval result.
    
    Args:
        query: The user's question
        retrieval_result: The retrieval result from GraphRAGRetriever
        
    Returns:
        A formatted prompt for the LLM
    """
    prompt_parts = [
        "You are an AI assistant with access to a knowledge graph about Tolkien's Middle-earth.",
        "Use the following information from the knowledge graph to answer the user's question.",
        f"\nUser Question: {query}\n",
        "\n=== Knowledge Graph Information ===\n"
    ]
    
    # Add extracted entities
    if "entities" in retrieval_result.metadata:
        entities = retrieval_result.metadata["entities"]
        prompt_parts.append(f"Extracted Entities: {', '.join(entities)}\n")
    
    # Add community information
    if "communities" in retrieval_result.metadata:
        communities = retrieval_result.metadata["communities"]
        community_entities = retrieval_result.metadata.get("community_entities", {})
        
        prompt_parts.append(f"Relevant Communities: {', '.join(str(c) for c in communities)}")
        
        if isinstance(community_entities, dict):
            for community_id in communities:
                entities = community_entities.get(str(community_id), [])
                if entities:
                    prompt_parts.append(f"Community {community_id} entities: {', '.join(str(e) for e in entities[:10])}")
    
    # Add key nodes
    if retrieval_result.nodes:
        prompt_parts.append("\nKey Entities:")
        for node in retrieval_result.nodes[:10]:  # Limit to first 10 nodes
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
            prompt_parts.append(f"{node_name} ({labels}): {properties_str}")
    
    # Add paths
    if retrieval_result.paths:
        prompt_parts.append("\nRelevant Paths:")
        for path_idx, path in enumerate(retrieval_result.paths):
            path_str = [f"Path {path_idx+1} (length {path['length']}):"]
            
            for i, node in enumerate(path["nodes"]):
                # Format node
                node_name = node["properties"].get("name", node["id"])
                if isinstance(node_name, list):
                    node_name = ', '.join(str(n) for n in node_name)
                
                path_str.append(f"  Node {i+1}: {node_name} ({', '.join(node['labels'])})")
                
                # Format relationship to next node if not the last node
                if i < path["length"]:
                    rel = path["relationships"][i]
                    rel_type = rel["type"]
                    path_str.append(f"  → {rel_type} →")
            
            prompt_parts.append("\n".join(path_str))
    
    # Add instructions for the LLM
    prompt_parts.append("\n=== Instructions ===")
    prompt_parts.append("Based on the knowledge graph information above, please answer the user's question.")
    prompt_parts.append("If the information is insufficient, say so and explain what's missing.")
    prompt_parts.append("Focus on the relationships and paths between entities to provide a comprehensive answer.")
    
    return "\n".join(prompt_parts)

def call_llm(prompt: str) -> str:
    """
    Call the LLM API to generate a response.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        The LLM's response
    """
    # System prompt for the LLM
    system_prompt = (
        "You are a knowledgeable assistant with expertise in Tolkien's Middle-earth. "
        "Your task is to provide comprehensive, accurate answers about the Lord of the Rings universe "
        "based on the knowledge graph information provided. Focus on relationships between entities "
        "and use the path information to explain connections. Be detailed but concise."
    )
    
    if OPENAI_AVAILABLE:
        try:
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            return f"[API ERROR] Failed to get response from LLM API: {str(e)}"
    else:
        # Use mock implementation
        logger.warning("Using mock LLM implementation")
        return "[MOCK] This is a mock LLM response. Install the OpenAI package for real responses."

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PathRAG Demo")
    parser.add_argument("query", help="Question to answer")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching for retrieval")
    parser.add_argument("--output-file", help="File to write results to (JSON format)")
    args = parser.parse_args()
    
    try:
        # Initialize GraphRAG retriever with optimized PathRAG parameters
        logger.info(f"Initializing GraphRAG retriever with optimized PathRAG parameters")
        retriever = GraphRAGRetriever(
            use_cache=not args.no_cache,
            pathrag_max_communities=5,  # Optimized value from parameter tuning
            pathrag_max_path_length=3,
            pathrag_max_paths_per_entity=5
        )
        
        # Execute retrieval
        logger.info(f"Executing PathRAG retrieval for query: {args.query}")
        start_time = time.time()
        result = retriever.retrieve(args.query, strategy="pathrag")
        retrieval_time = time.time() - start_time
        logger.info(f"Retrieval completed in {retrieval_time:.3f}s with {result.total_results} results")
        
        # Create LLM prompt
        prompt = create_llm_prompt(args.query, result)
        
        if args.verbose:
            print("\n=== LLM Prompt ===\n")
            print(prompt)
        
        # Call LLM
        logger.info("Calling LLM for answer synthesis")
        start_time = time.time()
        answer = call_llm(prompt)
        llm_time = time.time() - start_time
        logger.info(f"LLM processing completed in {llm_time:.3f}s")
        
        # Print answer
        print("\n=== LLM Answer ===\n")
        print(answer)
        print(f"\nTotal processing time: {retrieval_time + llm_time:.3f}s")
        
        # Write results to file if specified
        if args.output_file:
            output = {
                "query": args.query,
                "answer": answer,
                "retrieval_time": retrieval_time,
                "llm_time": llm_time,
                "total_time": retrieval_time + llm_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "parameters": {
                    "max_communities": 5,
                    "max_path_length": 3,
                    "max_paths_per_entity": 5,
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
