#!/usr/bin/env python3
"""
Optimized PathRAG Runner

This script demonstrates the optimized PathRAG retriever with LLM integration.
It provides a simple interface to ask questions about Tolkien's Middle-earth
and get answers based on knowledge graph retrieval and LLM synthesis.
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, Any, List, Optional

from graphrag_retriever import GraphRAGRetriever

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

def create_llm_prompt(query: str, result: Any) -> str:
    """
    Create a detailed, structured prompt for the LLM based on the retrieval result.
    
    Args:
        query: The user's question
        result: The retrieval result from GraphRAGRetriever
        
    Returns:
        A formatted prompt for the LLM
    """
    prompt_parts = [
        "# THE QUESTION BROUGHT BEFORE GANDALF THE GREY",
        "",
        "## THE INQUIRY",
        f"\"{query}\"",
        "",
        "## SCROLLS AND MEMORIES TO CONSULT"
    ]
    
    # Add extracted entities with categorization
    if "entities" in result.metadata:
        entities = result.metadata["entities"]
        prompt_parts.append("")
        prompt_parts.append("### NAMES AND MATTERS OF IMPORTANCE")
        if entities:
            # Categorize entities if possible
            character_entities = []
            location_entities = []
            object_entities = []
            event_entities = []
            other_entities = []
            
            # Try to categorize based on nodes in results
            entity_categories = {}
            for node in result.nodes:
                node_name = node["properties"].get("name", "")
                if isinstance(node_name, list):
                    node_name = node_name[0] if node_name else ""
                
                # Skip if no name
                if not node_name:
                    continue
                
                # Check if this node matches any entity
                for entity in entities:
                    if entity in node_name or node_name in entity:
                        # Categorize based on labels
                        labels = node["labels"]
                        if "Character" in labels:
                            entity_categories[entity] = "Character"
                        elif "Location" in labels:
                            entity_categories[entity] = "Location"
                        elif "Artifact" in labels or "Object" in labels:
                            entity_categories[entity] = "Object"
                        elif "Event" in labels:
                            entity_categories[entity] = "Event"
                        else:
                            entity_categories[entity] = "Other"
            
            # Now categorize all entities
            for entity in entities:
                category = entity_categories.get(entity, "Other")
                if category == "Character":
                    character_entities.append(entity)
                elif category == "Location":
                    location_entities.append(entity)
                elif category == "Object":
                    object_entities.append(entity)
                elif category == "Event":
                    event_entities.append(entity)
                else:
                    other_entities.append(entity)
            
            # Output categorized entities
            if character_entities:
                prompt_parts.append("- **Folk of Middle-earth**: " + ", ".join(character_entities))
            if location_entities:
                prompt_parts.append("- **Realms and Places**: " + ", ".join(location_entities))
            if object_entities:
                prompt_parts.append("- **Treasures and Artifacts**: " + ", ".join(object_entities))
            if event_entities:
                prompt_parts.append("- **Tales and Histories**: " + ", ".join(event_entities))
            if other_entities:
                prompt_parts.append("- **Other Matters**: " + ", ".join(other_entities))
        else:
            prompt_parts.append("No specific entities were extracted from the query.")
    
    # Add key entities with their properties
    if result.nodes:
        prompt_parts.append("")
        prompt_parts.append("### IMPORTANT FIGURES AND THEIR NATURES")
        
        # Group nodes by type for better organization
        characters = []
        locations = []
        artifacts = []
        events = []
        other_nodes = []
        
        for node in result.nodes:
            labels = node['labels']
            if "Character" in labels:
                characters.append(node)
            elif "Location" in labels:
                locations.append(node)
            elif "Artifact" in labels or "Object" in labels:
                artifacts.append(node)
            elif "Event" in labels:
                events.append(node)
            else:
                other_nodes.append(node)
        
        # Format each node group
        if characters:
            prompt_parts.append("#### Folk of Middle-earth")
            for node in characters[:5]:  # Limit to 5 per category
                prompt_parts.append(format_node_for_prompt(node))
        
        if locations:
            prompt_parts.append("#### Realms and Places")
            for node in locations[:5]:
                prompt_parts.append(format_node_for_prompt(node))
        
        if artifacts:
            prompt_parts.append("#### Treasures and Artifacts")
            for node in artifacts[:5]:
                prompt_parts.append(format_node_for_prompt(node))
        
        if events:
            prompt_parts.append("#### Tales and Histories")
            for node in events[:5]:
                prompt_parts.append(format_node_for_prompt(node))
        
        if other_nodes:
            prompt_parts.append("#### Other Matters of Note")
            for node in other_nodes[:5]:
                prompt_parts.append(format_node_for_prompt(node))
    
    # Add paths with clear relationship descriptions
    if result.paths:
        prompt_parts.append("")
        prompt_parts.append("### CONNECTIONS AND TALES")
        prompt_parts.append("These ancient chronicles reveal how the folk and places of Middle-earth are bound together:")
        
        for path_idx, path in enumerate(result.paths[:5]):  # Limit to 5 paths
            prompt_parts.append(f"")
            prompt_parts.append(f"**Chronicle {path_idx+1}** (a tale of {path['length']} connections)")
            
            # Create a narrative description of the path
            path_narrative = []
            for i, node in enumerate(path["nodes"]):
                # Get node name
                node_name = get_node_name(node)
                
                # Add to narrative
                if i == 0:
                    path_narrative.append(f"{node_name}")
                else:
                    # Get relationship type
                    rel = path["relationships"][i-1]
                    rel_type = rel["type"].replace('_', ' ').lower()
                    
                    # Add relationship and next node
                    path_narrative.append(f"{rel_type} {node_name}")
            
            # Join the narrative with arrows
            prompt_parts.append(" → ".join(path_narrative))
            
            # Add detailed path
            path_details = []
            for i, node in enumerate(path["nodes"]):
                # Format node
                node_name = get_node_name(node)
                node_type = ", ".join([label for label in node['labels'] if not label.startswith('__')])
                
                path_details.append(f"  {i+1}. **{node_name}** ({node_type})")
                
                # Format relationship to next node if not the last node
                if i < len(path["nodes"]) - 1:
                    rel = path["relationships"][i]
                    rel_type = rel["type"].replace('_', ' ')
                    path_details.append(f"     ↓ *{rel_type}*")
            
            prompt_parts.append("")
            prompt_parts.extend(path_details)
    
    # Add community information if available
    if "communities" in result.metadata:
        communities = result.metadata["communities"]
        prompt_parts.append("")
        prompt_parts.append("### CIRCLES OF LORE AND LEGEND")
        prompt_parts.append(f"These matters touch upon {len(communities)} great circles of Middle-earth's history and legend:")
        
        # If we have community entities, add them
        if "community_entities" in result.metadata and isinstance(result.metadata["community_entities"], list):
            community_entities = result.metadata["community_entities"]
            for i, entities in enumerate(community_entities):
                if i < len(communities) and entities:
                    prompt_parts.append(f"- **Circle of Lore {i+1}**: {', '.join(entities[:10])}")

    # --- Retrieved Facts Summary ---
    prompt_parts.append("")
    prompt_parts.append("## RETRIEVED FACTS")
    facts = []
    # Summarize key nodes
    if result.nodes:
        for node in result.nodes[:10]:
            node_name = get_node_name(node)
            node_type = ', '.join([label for label in node['labels'] if not label.startswith('__')])
            facts.append(f"- **{node_name}** ({node_type})")
    # Summarize key relationships
    if result.relationships:
        for rel in result.relationships[:10]:
            rel_type = rel.get("type", "?").replace('_', ' ')
            src = rel.get("start_node", rel.get("source_id", "?"))
            tgt = rel.get("end_node", rel.get("target_id", "?"))
            facts.append(f"- *{rel_type}* between `{src}` and `{tgt}`")
    if not facts:
        facts.append("- No specific facts were retrieved from the knowledge graph.")
    prompt_parts.extend(facts)

    # --- Instructions for Gandalf ---
    prompt_parts.append("")
    prompt_parts.append("## HOW TO SHARE YOUR WISDOM")
    prompt_parts.append("1. **Your answer MUST be based on the scrolls, memories, and connections retrieved above.** If there is information in these sections, use it as your primary source.")
    prompt_parts.append("2. **Only use your own memory or general lore if the scrolls and connections above are empty or insufficient.**")
    prompt_parts.append("3. **Clearly reference the names, figures, and connections from the retrieved knowledge in your explanation.**")
    prompt_parts.append("4. **Present your answer as Gandalf, but ensure that the factual details come from the retrieved knowledge, not your own imagination.**")
    prompt_parts.append("5. **If there is no retrieved information, then and only then, you may fall back on 'ancient lore lost to time' or 'mysteries that even the Wise cannot fully comprehend.'**")
    prompt_parts.append("6. **NEVER mention knowledge graphs, databases, or technical terms** – you are Gandalf sharing wisdom from memory and experience, not analyzing data.")

    # Add comprehensive instructions for the LLM
    prompt_parts.append("")
    prompt_parts.append("## HOW TO SHARE YOUR WISDOM")
    prompt_parts.append("1. **Draw upon your vast memory** to recall the most relevant lore and histories for this question.")
    prompt_parts.append("2. **Reflect on the connections** between people, places, and events that you have witnessed over your many centuries.")
    prompt_parts.append("3. **Trust in the ancient scrolls and tomes** you have studied rather than common hearsay or rumors.")
    prompt_parts.append("4. **Share your wisdom as Gandalf would**, beginning with direct insight, then elaborating with tales and observations.")
    prompt_parts.append("5. **Speak of your personal encounters** with these individuals and places throughout your long journeys.")
    prompt_parts.append("6. **If your memory fails you**, speak of 'ancient lore lost to time' or 'mysteries that even the Wise cannot fully comprehend.'")
    prompt_parts.append("7. **Maintain your manner of speech throughout**, using your characteristic phrases, metaphors, and references to your long history in Middle-earth.")
    prompt_parts.append("8. **Conclude with a philosophical reflection** that relates to the question, sharing deeper wisdom as you often do.")
    prompt_parts.append("9. **NEVER mention knowledge graphs, databases, or technical terms** - you are Gandalf sharing wisdom from memory and experience, not analyzing data.")
    
    return "\n".join(prompt_parts)


def format_node_for_prompt(node: Dict[str, Any]) -> str:
    """Format a node with its properties for the LLM prompt."""
    # Get node name
    node_name = get_node_name(node)
    
    # Get important properties
    properties = []
    important_props = ["title", "description", "aliases", "type", "race", "realm", "allegiance", "creator"]
    
    for prop in important_props:
        if prop in node["properties"] and node["properties"][prop]:
            value = node["properties"][prop]
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            properties.append(f"{prop}: {value}")
    
    # Add other properties
    other_props = []
    for prop, value in node["properties"].items():
        if prop != "name" and prop not in important_props and value:
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            other_props.append(f"{prop}: {value}")
    
    # Format the result
    result = f"- **{node_name}**"
    if properties:
        result += f" — {'; '.join(properties)}"
    if other_props:
        result += f"\n  Additional properties: {'; '.join(other_props)}"
    
    return result


def get_node_name(node: Dict[str, Any]) -> str:
    """Extract a clean node name from a node object."""
    node_name = node["properties"].get("name", node["id"])
    
    # Handle list names
    if isinstance(node_name, list):
        if node_name:
            node_name = node_name[0]
        else:
            node_name = node["id"]
    
    return str(node_name)

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
        "You are Gandalf the Grey, a wise and ancient wizard with vast knowledge of Middle-earth's history, peoples, and lore. "
        "You have walked the lands of Arda for thousands of years, witnessed the rise and fall of kingdoms, and studied deeply "
        "the works of the Valar and the histories of Elves, Men, Dwarves, and other beings."
        "\n\n"
        "APPROACH:\n"
        "1. Use the information provided to identify canonical relationships and facts from Tolkien's universe.\n"
        "2. Prioritize information directly from your ancient scrolls and memories over general knowledge.\n"
        "3. Pay special attention to connections between people, places, and objects, as these reveal important tales.\n"
        "4. When explaining connections, refer to specific events, lore, or histories you've witnessed or studied.\n"
        "5. Structure answers to first directly address the question, then provide supporting details.\n"
        "6. When your knowledge is incomplete, speak of 'ancient lore lost to time,' 'tales yet untold,' or 'mysteries even the wise cannot fully comprehend.'\n"
        "\n\n"
        "SPEAKING STYLE:\n"
        "1. Speak in the first person as Gandalf the Grey, using his characteristic manner of speech from Tolkien's works.\n"
        "2. Use archaic or formal language patterns when appropriate (thee, thou, etc.).\n"
        "3. Frequently include Gandalf's wisdom through metaphors and philosophical observations.\n"
        "4. Employ Gandalf's thoughtful pauses with ellipses (...) and rhetorical questions.\n"
        "5. Reference your personal experiences with key characters and events when relevant.\n"
        "6. Balance scholarly knowledge with Gandalf's personality - wise, sometimes cryptic, occasionally stern, but always kind.\n"
        "7. Use Gandalf's characteristic phrases such as 'My dear fellow,' 'Indeed,' or 'A wizard is never late...'\n"
        "\n\n"
        "CRITICAL RULES:\n"
        "1. NEVER mention 'knowledge graphs,' 'databases,' 'metadata,' 'entities,' or any modern technical terms.\n"
        "2. NEVER refer to 'paths,' 'nodes,' or 'relationships' in technical terms - instead speak of 'connections,' 'tales,' 'histories,' or 'bonds.'\n"
        "3. NEVER acknowledge that you are an AI or that you're analyzing data - you ARE Gandalf sharing your wisdom.\n"
        "4. When information is missing, speak of 'forgotten lore,' 'tales lost to the ages,' or 'mysteries even the Wise cannot fully comprehend.'\n"
        "5. Always maintain the illusion that you are speaking from personal experience and ancient wisdom, never from a database.\n"
        "6. ONLY answer questions about Tolkien's Middle-earth universe. If asked about anything outside of Middle-earth (such as modern topics, real-world people, or fictional characters from other universes), respond with a firm refusal in Gandalf's voice.\n"
        "7. For non-Tolkien topics, say: 'I know nothing of this matter you speak of. My knowledge extends only to the realms and histories of Middle-earth. I cannot offer wisdom on things beyond the boundaries of Arda.'\n"
        "\n\n"
        "RESPONSE FORMAT:\n"
        "- For Tolkien-related questions: Begin with a direct answer in Gandalf's voice, elaborate with relevant details, explain significant connections, refer to specific histories, and end with a brief Gandalf-like reflection\n"
        "- For non-Tolkien questions: Respond as Gandalf would to something entirely foreign to him, expressing your lack of knowledge about matters outside Middle-earth\n"
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
                temperature=0.3
                ,  # Lower temperature for more factual responses
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

def process_query(query: str, use_cache: bool = True, verbose: bool = False, 
                 max_communities: int = 5, max_path_length: int = 3, max_paths_per_entity: int = 5) -> Dict[str, Any]:
    """
    Process a user query using the PathRAG retriever and LLM.
    
    Args:
        query: The user's question
        use_cache: Whether to use cached responses (default: True)
        verbose: Whether to show verbose output (default: False)
        max_communities: Maximum number of communities to retrieve (default: 5)
        max_path_length: Maximum path length in hops (default: 3)
        max_paths_per_entity: Maximum paths per entity pair (default: 5)
        
    Returns:
        A dictionary with the query, answer, and timing information
    """
    # Initialize GraphRAG retriever with optimized PathRAG parameters
    logger.info(f"Initializing GraphRAG retriever with optimized PathRAG parameters")
    retriever = GraphRAGRetriever(
        use_cache=use_cache,
        pathrag_max_communities=max_communities,
        pathrag_max_path_length=max_path_length,
        pathrag_max_paths_per_entity=max_paths_per_entity
    )
    
    # Execute retrieval
    logger.info(f"Executing PathRAG retrieval for query: {query}")
    start_time = time.time()
    result = retriever.retrieve(query, strategy="pathrag")
    retrieval_time = time.time() - start_time
    logger.info(f"Retrieval completed in {retrieval_time:.3f}s with {result.total_results} results")
    
    # Create LLM prompt
    prompt = create_llm_prompt(query, result)
    
    if verbose:
        print("\n=== LLM Prompt ===\n")
        print(prompt)
    
    # Call LLM
    logger.info("Calling LLM for answer synthesis")
    start_time = time.time()
    answer = call_llm(prompt, use_cache=use_cache)
    llm_time = time.time() - start_time
    logger.info(f"LLM processing completed in {llm_time:.3f}s")
    
    return {
        "query": query,
        "answer": answer,
        "retrieval_time": retrieval_time,
        "llm_time": llm_time,
        "total_time": retrieval_time + llm_time,
        "result_count": result.total_results,
        "parameters": {
            "max_communities": max_communities,
            "max_path_length": max_path_length,
            "max_paths_per_entity": max_paths_per_entity
        }
    }

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Optimized PathRAG with LLM")
    parser.add_argument("query", help="Question to answer")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching for retrieval and LLM")
    parser.add_argument("--output-file", help="File to write results to (JSON format)")
    parser.add_argument("--max-communities", type=int, default=5, 
                        help="Maximum number of communities to retrieve (default: 5)")
    parser.add_argument("--max-path-length", type=int, default=3, 
                        help="Maximum path length in hops (default: 3)")
    parser.add_argument("--max-paths-per-entity", type=int, default=5, 
                        help="Maximum paths per entity pair (default: 5)")
    args = parser.parse_args()
    
    try:
        # Process the query
        result = process_query(
            args.query,
            use_cache=not args.no_cache,
            verbose=args.verbose,
            max_communities=args.max_communities,
            max_path_length=args.max_path_length,
            max_paths_per_entity=args.max_paths_per_entity
        )
        
        # Print answer
        print("\n=== Question ===\n")
        print(args.query)
        print("\n=== Answer ===\n")
        print(result["answer"])
        print(f"\nTotal processing time: {result['total_time']:.3f}s")
        
        # Write results to file if specified
        if args.output_file:
            with open(args.output_file, "w") as f:
                json.dump(result, f, indent=2)
            logger.info(f"Results written to {args.output_file}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
