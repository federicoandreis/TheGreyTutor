#!/usr/bin/env python3
"""
Test script for the improved PathRAG LLM prompt.

This script demonstrates the improved prompt formatting for the LLM
without actually making API calls. It shows how the prompt is structured
and formatted for better answer synthesis.
"""

import argparse
import json
import logging
import sys
from typing import Dict, Any

# Update import to use parent directory
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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
        "# KNOWLEDGE GRAPH QUERY ANALYSIS",
        "",
        "## USER QUESTION",
        f"\"{query}\"",
        "",
        "## RETRIEVED KNOWLEDGE GRAPH INFORMATION"
    ]
    
    # Add extracted entities with categorization
    if "entities" in result.metadata:
        entities = result.metadata["entities"]
        prompt_parts.append("")
        prompt_parts.append("### EXTRACTED QUERY ENTITIES")
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
                prompt_parts.append(f"- **Characters**: {', '.join(character_entities)}")
            if location_entities:
                prompt_parts.append(f"- **Locations**: {', '.join(location_entities)}")
            if object_entities:
                prompt_parts.append(f"- **Objects/Artifacts**: {', '.join(object_entities)}")
            if event_entities:
                prompt_parts.append(f"- **Events**: {', '.join(event_entities)}")
            if other_entities:
                prompt_parts.append(f"- **Other Entities**: {', '.join(other_entities)}")
        else:
            prompt_parts.append("No specific entities were extracted from the query.")
    
    # Add key nodes with detailed information
    if result.nodes:
        prompt_parts.append("")
        prompt_parts.append("### KEY ENTITIES AND THEIR PROPERTIES")
        
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
        prompt_parts.append("### RELEVANT THEMATIC COMMUNITIES")
        prompt_parts.append(f"The entities in this query belong to {len(communities)} thematic communities in the Tolkien universe:")
        prompt_parts.append(f"Community IDs: {', '.join(str(c) for c in communities)}")
        
        # If we have community entities, add them
        if "community_entities" in result.metadata and isinstance(result.metadata["community_entities"], list):
            community_entities = result.metadata["community_entities"]
            for i, entities in enumerate(community_entities):
                if i < len(communities) and entities:
                    prompt_parts.append(f"- Community {communities[i]}: {', '.join(entities[:10])}")
    
    # Add comprehensive instructions for the LLM
    prompt_parts.append("")
    prompt_parts.append("## ANSWER SYNTHESIS INSTRUCTIONS")
    prompt_parts.append("1. **Analyze the knowledge graph data** above to identify the most relevant information for answering the user's question.")
    prompt_parts.append("2. **Focus on relationships between entities** shown in the paths, as these reveal how entities are connected in Tolkien's universe.")
    prompt_parts.append("3. **Prioritize canonical information** from the knowledge graph over general knowledge about Tolkien's works.")
    prompt_parts.append("4. **Structure your answer** to first directly address the question, then provide supporting details from the knowledge graph.")
    prompt_parts.append("5. **Cite specific paths or entities** from the knowledge graph to support your explanations.")
    prompt_parts.append("6. **If information is insufficient**, acknowledge this and explain what specific information would be needed.")
    prompt_parts.append("7. **Maintain the tone** of a knowledgeable Tolkien scholar while being accessible to readers of all familiarity levels.")
    
    return "\n".join(prompt_parts)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test Improved PathRAG LLM Prompt")
    parser.add_argument("query", help="Question to answer")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching for retrieval")
    args = parser.parse_args()
    
    try:
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
        prompt = create_improved_prompt(args.query, result)
        
        # Print the prompt
        print("\n=== IMPROVED LLM PROMPT ===\n")
        print(prompt)
        
        # Print system prompt
        system_prompt = (
            "You are a scholarly expert on J.R.R. Tolkien's Middle-earth legendarium with deep knowledge of the lore, characters, "
            "geography, artifacts, and history of Tolkien's universe. Your expertise spans The Silmarillion, The Hobbit, "
            "The Lord of the Rings, and supplementary works."
            "\n\n"
            "APPROACH:\n"
            "1. Analyze the knowledge graph data provided to identify canonical relationships and facts from Tolkien's works.\n"
            "2. Prioritize information directly extracted from the knowledge graph over general knowledge.\n"
            "3. Pay special attention to relationship paths between entities, as these reveal how characters, objects, and locations interact.\n"
            "4. When explaining connections, cite specific evidence from the knowledge graph.\n"
            "5. Structure answers to first directly address the question, then provide supporting details.\n"
            "6. Use formal, scholarly language while remaining accessible to readers of varying familiarity with Tolkien's works.\n"
            "7. Acknowledge limitations in the available information when necessary.\n"
            "\n\n"
            "RESPONSE FORMAT:\n"
            "- Begin with a direct answer to the question\n"
            "- Elaborate with relevant details from the knowledge graph\n"
            "- Explain significant relationships between entities\n"
            "- Cite specific paths or connections from the knowledge graph\n"
            "- Maintain an authoritative but accessible tone\n"
        )
        
        print("\n=== SYSTEM PROMPT ===\n")
        print(system_prompt)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
