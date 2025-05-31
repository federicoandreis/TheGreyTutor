#!/usr/bin/env python3
"""
Save Improved PathRAG LLM Prompt

This script demonstrates the improved prompt formatting for the LLM
and saves it to a file for inspection.
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, Any

from graphrag_retriever import GraphRAGRetriever

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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

def create_improved_prompt(query: str, result: Any) -> str:
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
            
            # Add categorized entities to prompt
            if character_entities:
                prompt_parts.append(f"- **Folk of Middle-earth**: {', '.join(character_entities)}")
            if location_entities:
                prompt_parts.append(f"- **Realms and Places**: {', '.join(location_entities)}")
            if object_entities:
                prompt_parts.append(f"- **Treasures and Artifacts**: {', '.join(object_entities)}")
            if event_entities:
                prompt_parts.append(f"- **Tales and Histories**: {', '.join(event_entities)}")
            if other_entities:
                prompt_parts.append(f"- **Other Matters**: {', '.join(other_entities)}")
        else:
            prompt_parts.append("No specific entities were extracted from the query.")
    
    # Add key nodes with detailed information
    if result.nodes:
        prompt_parts.append("")
        prompt_parts.append("### CHRONICLES OF IMPORTANT MATTERS")
        
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
            prompt_parts.append("#### Characters")
            for node in characters[:5]:  # Limit to 5 per category
                prompt_parts.append(format_node_for_prompt(node))
        
        if locations:
            prompt_parts.append("#### Locations")
            for node in locations[:5]:
                prompt_parts.append(format_node_for_prompt(node))
        
        if artifacts:
            prompt_parts.append("#### Objects/Artifacts")
            for node in artifacts[:5]:
                prompt_parts.append(format_node_for_prompt(node))
        
        if events:
            prompt_parts.append("#### Events")
            for node in events[:5]:
                prompt_parts.append(format_node_for_prompt(node))
        
        if other_nodes:
            prompt_parts.append("#### Other Entities")
            for node in other_nodes[:5]:
                prompt_parts.append(format_node_for_prompt(node))
    
    # Add paths with clear relationship descriptions
    if result.paths:
        prompt_parts.append("")
        prompt_parts.append("### RELATIONSHIP PATHS")
        prompt_parts.append("The following paths show how entities are connected in the knowledge graph:")
        
        for path_idx, path in enumerate(result.paths[:5]):  # Limit to 5 paths
            prompt_parts.append(f"")
            prompt_parts.append(f"**Path {path_idx+1}** (length: {path['length']} hops)")
            
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

def get_system_prompt() -> str:
    """Get the improved system prompt for the LLM."""
    return (
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
        "\n\n"
        "RESPONSE FORMAT:\n"
        "- Begin with a direct answer to the question in Gandalf's voice\n"
        "- Elaborate with relevant details from your vast experience and knowledge\n"
        "- Explain significant connections between people, places, and events as if recounting tales you have witnessed\n"
        "- Refer to specific histories, scrolls, or personal observations to support your explanations\n"
        "- End with a brief Gandalf-like reflection or piece of wisdom related to the question\n"
    )

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Save Improved PathRAG LLM Prompt")
    parser.add_argument("query", help="Question to answer")
    parser.add_argument("--output-dir", default="./prompt_examples", help="Directory to save output files")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching for retrieval")
    args = parser.parse_args()
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Initialize GraphRAG retriever with optimized PathRAG parameters
        logger.info(f"Initializing GraphRAG retriever with optimized PathRAG parameters")
        retriever = GraphRAGRetriever(
            use_cache=not args.no_cache,
            pathrag_max_communities=5,
            pathrag_max_path_length=3,
            pathrag_max_paths_per_entity=5
        )
        
        # Execute retrieval
        logger.info(f"Executing PathRAG retrieval for query: {args.query}")
        result = retriever.retrieve(args.query, strategy="pathrag")
        logger.info(f"Retrieval completed with {result.total_results} results")
        
        # Create improved prompt
        user_prompt = create_improved_prompt(args.query, result)
        system_prompt = get_system_prompt()
        
        # Create safe filename from query (limit to 30 chars to avoid truncation issues)
        safe_filename = args.query.replace(" ", "_").replace("?", "").replace("!", "")[:30]
        safe_filename = ''.join(c for c in safe_filename if c.isalnum() or c in "_-")
        
        # Save prompts to files with proper extensions
        user_prompt_file = os.path.join(args.output_dir, f"{safe_filename}_user_prompt.md")
        system_prompt_file = os.path.join(args.output_dir, f"{safe_filename}_system_prompt.md")
        combined_file = os.path.join(args.output_dir, f"{safe_filename}_combined.md")
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Write files with proper encoding
        with open(user_prompt_file, "w", encoding="utf-8") as f:
            f.write(user_prompt)
        
        with open(system_prompt_file, "w", encoding="utf-8") as f:
            f.write(system_prompt)
        
        logger.info(f"User prompt saved to: {user_prompt_file}")
        logger.info(f"System prompt saved to: {system_prompt_file}")
        with open(combined_file, "w", encoding="utf-8") as f:
            f.write("# Improved PathRAG LLM Prompts\n\n")
            f.write(f"Query: \"{args.query}\"\n\n")
            f.write("## System Prompt\n\n")
            f.write("```\n")
            f.write(system_prompt)
            f.write("\n```\n\n")
            f.write("## User Prompt\n\n")
            f.write("```\n")
            f.write(user_prompt)
            f.write("\n```\n")
        
        logger.info(f"Combined prompts saved to: {combined_file}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
