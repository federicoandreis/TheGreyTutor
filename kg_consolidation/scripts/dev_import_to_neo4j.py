import os
import logging
import glob
import asyncio
import mimetypes
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

from neo4j import GraphDatabase
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm.openai_llm import OpenAILLM
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import FixedSizeSplitter
from neo4j_graphrag.generation.prompts import ERExtractionTemplate
from neo4j_graphrag.experimental.components.entity_relation_extractor import LLMEntityRelationExtractor
from neo4j_graphrag.experimental.components.schema import SchemaConfig

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Configuration from environment variables
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')

# Tolkien-specific schema for Middle-earth entities
ENTITIES = [
    {
        "label": "Character",
        "description": "Any named individual in Middle-earth including humans, elves, dwarves, hobbits, wizards, and other sentient beings",
        "properties": [
            {"name": "name", "type": "STRING"},
            {"name": "aliases", "type": "LIST"},  # Explicit aliases field for entity resolution
            {"name": "race", "type": "STRING"},
            {"name": "title", "type": "STRING"},
            {"name": "status", "type": "STRING"},
            {"name": "home_region", "type": "STRING"}
        ]
    },
    {
        "label": "Location",
        "description": "Any named place in Middle-earth including realms, cities, regions, mountains, rivers, forests, and landmarks",
        "properties": [
            {"name": "name", "type": "STRING"},
            {"name": "aliases", "type": "LIST"},  # Explicit aliases field for entity resolution
            {"name": "location_type", "type": "STRING"},
            {"name": "region", "type": "STRING"},
            {"name": "significance", "type": "STRING"}
        ]
    },
    {
        "label": "Artifact",
        "description": "Significant objects including rings, weapons, jewelry, books, and other items of power or importance",
        "properties": [
            {"name": "name", "type": "STRING"},
            {"name": "aliases", "type": "LIST"},  # Explicit aliases field for entity resolution
            {"name": "artifact_type", "type": "STRING"},
            {"name": "material", "type": "STRING"},
            {"name": "powers", "type": "STRING"},
            {"name": "current_status", "type": "STRING"}
        ]
    },
    {
        "label": "Organization",
        "description": "Groups, kingdoms, fellowships, armies, councils, and other collective entities",
        "properties": [
            {"name": "name", "type": "STRING"},
            {"name": "aliases", "type": "LIST"},  # Explicit aliases field for entity resolution
            {"name": "organization_type", "type": "STRING"},
            {"name": "purpose", "type": "STRING"},
            {"name": "status", "type": "STRING"}
        ]
    },
    {
        "label": "Event",
        "description": "Significant occurrences including battles, councils, journeys, and other notable happenings",
        "properties": [
            {"name": "name", "type": "STRING"},
            {"name": "aliases", "type": "LIST"},  # Explicit aliases field for entity resolution
            {"name": "event_type", "type": "STRING"},
            {"name": "age", "type": "STRING"},
            {"name": "outcome", "type": "STRING"},
            {"name": "significance", "type": "STRING"}
        ]
    }
]

RELATIONS = [
    {"label": "PARENT_OF", "description": "Direct parent-child relationship"},
    {"label": "CHILD_OF", "description": "Direct child-parent relationship"},
    {"label": "MARRIED_TO", "description": "Spouse relationship"},
    {"label": "RULES", "description": "Governs or has authority over a location or organization"},
    {"label": "SERVES", "description": "Serves under or works for another entity"},
    {"label": "ALLIES_WITH", "description": "Allied or friendly relationship"},
    {"label": "OPPOSES", "description": "Enemy or antagonistic relationship"},
    {"label": "MEMBER_OF", "description": "Belongs to or is part of an organization"},
    {"label": "LEADS", "description": "Commands or directs an organization or group"},
    {"label": "LOCATED_IN", "description": "Is situated within or part of a larger location"},
    {"label": "DWELLS_IN", "description": "Lives or resides in a location"},
    {"label": "TRAVELS_TO", "description": "Journeys or moves to a location"},
    {"label": "OWNS", "description": "Possesses or has ownership of an artifact"},
    {"label": "WIELDS", "description": "Uses or carries an artifact, especially weapons"},
    {"label": "CREATES", "description": "Makes or forges an artifact"},
    {"label": "PARTICIPATES_IN", "description": "Takes part in an event"},
    {"label": "TAKES_PLACE_IN", "description": "Event or action that occurs at a specific location"},
    {"label": "MENTORS", "description": "Teaches, guides, or advises another character"},
    {"label": "KNOWS_ABOUT", "description": "Has knowledge or information about another entity"},
    {"label": "CREATED_BY", "description": "Was made or forged by another entity"}
]

POTENTIAL_SCHEMA = [
    ("Character", "PARENT_OF", "Character"),
    ("Character", "MARRIED_TO", "Character"),
    ("Character", "SERVES", "Character"),
    ("Character", "ALLIES_WITH", "Character"),
    ("Character", "OPPOSES", "Character"),
    ("Character", "MENTORS", "Character"),
    ("Character", "RULES", "Location"),
    ("Character", "DWELLS_IN", "Location"),
    ("Character", "TRAVELS_TO", "Location"),
    ("Character", "OWNS", "Artifact"),
    ("Character", "WIELDS", "Artifact"),
    ("Character", "CREATES", "Artifact"),
    ("Character", "MEMBER_OF", "Organization"),
    ("Character", "LEADS", "Organization"),
    ("Character", "PARTICIPATES_IN", "Event"),
    ("Location", "LOCATED_IN", "Location"),
    ("Organization", "LOCATED_IN", "Location"),
    ("Organization", "ALLIES_WITH", "Organization"),
    ("Organization", "OPPOSES", "Organization"),
    ("Organization", "PARTICIPATES_IN", "Event"),
    ("Event", "TAKES_PLACE_IN", "Location"),
    ("Artifact", "LOCATED_IN", "Location"),
    ("Artifact", "CREATED_BY", "Character")
]

def detect_communities(driver, llm):
    """Run community detection on the knowledge graph and generate community summaries."""
    logging.info("Running community detection...")
    
    with driver.session() as session:
        # First, check what node labels actually exist in the database
        result = session.run("""
            CALL db.labels() YIELD label
            RETURN collect(label) AS labels
        """)
        available_labels = result.single()["labels"]
        logging.info(f"Available node labels in database: {available_labels}")
        
        # Check if we have any entity labels to work with
        entity_labels = [label for label in available_labels 
                         if label not in ['__KGBuilder__', 'Document', 'Chunk', 'Community']]
        
        if not entity_labels:
            logging.error("No entity labels found in the database. Cannot run community detection.")
            return
        
        logging.info(f"Using entity labels for community detection: {entity_labels}")
        
        # Get available relationship types
        result = session.run("""
            CALL db.relationshipTypes() YIELD relationshipType
            RETURN collect(relationshipType) AS types
        """)
        available_rel_types = result.single()["types"]
        logging.info(f"Available relationship types in database: {available_rel_types}")
        
        # Filter relationship types to exclude lexical graph relationships
        entity_rel_types = [rel_type for rel_type in available_rel_types 
                           if rel_type not in ['CONTAINS', 'PART_OF', 'BELONGS_TO_COMMUNITY']]
        
        if not entity_rel_types:
            logging.error("No entity relationship types found in the database. Cannot run community detection.")
            return
        
        # First, check if the graph exists and drop it if it does
        try:
            # Check if the graph exists
            result = session.run("""
                CALL gds.graph.exists('entity-graph')
                YIELD exists
                RETURN exists
            """)
            graph_exists = result.single()["exists"]
            
            # Drop the graph if it exists
            if graph_exists:
                session.run("""
                    CALL gds.graph.drop('entity-graph')
                    YIELD graphName
                    RETURN graphName
                """)
                logging.info("Dropped existing graph projection")
        except Exception as e:
            logging.warning(f"Error checking/dropping graph: {e}")
            # Continue anyway
        
        # Create graph projection including all entity nodes and their relationships
        labels_str = ", ".join([f"'{label}'" for label in entity_labels])
        
        # Build the relationship config as individual entries in Cypher
        rel_config_parts = []
        for rel_type in entity_rel_types:
            rel_config_parts.append(f"{rel_type}: {{orientation: 'UNDIRECTED'}}")
        
        rel_config_str = "{" + ", ".join(rel_config_parts) + "}"
        
        projection_query = f"""
            CALL gds.graph.project(
                'entity-graph',
                [{labels_str}],
                {rel_config_str}
            )
        """
        logging.debug(f"Running projection query: {projection_query}")
        try:
            session.run(projection_query)
            logging.info("Graph projection created successfully")
        except Exception as e:
            logging.error(f"Failed to create graph projection: {e}")
            raise
        
        # Run Louvain community detection with lower resolution for fewer, more meaningful communities
        result = session.run("""
            CALL gds.louvain.write('entity-graph', {
                writeProperty: 'community_id',
                relationshipWeightProperty: null,
                includeIntermediateCommunities: false,
                tolerance: 0.0001,
                maxLevels: 10,
                maxIterations: 10
            })
            YIELD communityCount, modularity
            RETURN communityCount, modularity
        """)
        
        community_stats = result.single()
        num_communities = community_stats['communityCount']
        logging.info(f"Detected {num_communities} communities with modularity {community_stats['modularity']:.3f}")
        
        # Create Community nodes and relationships
        session.run("""
            MATCH (n) WHERE n.community_id IS NOT NULL
            WITH DISTINCT n.community_id AS communityId
            CREATE (c:Community {id: communityId, name: 'Community ' + toString(communityId)})
        """)
        
        session.run("""
            MATCH (n) WHERE n.community_id IS NOT NULL
            MATCH (c:Community {id: n.community_id})
            CREATE (n)-[:BELONGS_TO_COMMUNITY]->(c)
        """)
        
        # Verify community assignments and log statistics
        result = session.run("""
            MATCH (c:Community)
            OPTIONAL MATCH (n)-[:BELONGS_TO_COMMUNITY]->(c)
            WITH c, count(n) AS nodeCount
            RETURN c.id AS communityId, nodeCount
            ORDER BY nodeCount DESC
        """)
        
        community_stats = []
        for record in result:
            community_id = record["communityId"]
            node_count = record["nodeCount"]
            community_stats.append((community_id, node_count))
            logging.info(f"Community {community_id} has {node_count} nodes")
        
        # Generate summaries for each community
        logging.info("Generating community summaries...")
        
        for community_id, node_count in community_stats:
            if node_count == 0:
                logging.warning(f"Community {community_id} has no nodes, skipping summary generation")
                continue
                
            # Get all entities and relationships in this community
            query = """
                MATCH (n)-[:BELONGS_TO_COMMUNITY]->(c:Community {id: $community_id})
                WITH n
                OPTIONAL MATCH (n)-[r]-(m)
                WHERE EXISTS((m)-[:BELONGS_TO_COMMUNITY]->(:Community {id: $community_id}))
                RETURN collect(DISTINCT n) AS nodes, collect(DISTINCT r) AS relationships
            """
            result = session.run(query, community_id=community_id)
            record = result.single()
            
            if not record or not record["nodes"] or len(record["nodes"]) == 0:
                logging.warning(f"No nodes found for community {community_id} in detailed query")
                continue
                
            nodes = record["nodes"]
            relationships = record["relationships"]
            
            # Get the most common entity types in this community
            node_types = {}
            for node in nodes:
                for label in node.labels:
                    if label not in ['__Entity__', '__KGBuilder__']:
                        node_types[label] = node_types.get(label, 0) + 1
            
            # Sort node types by frequency
            sorted_types = sorted(node_types.items(), key=lambda x: x[1], reverse=True)
            type_summary = ", ".join([f"{label} ({count})" for label, count in sorted_types])
            
            # Get the most common relationship types
            rel_types = {}
            for rel in relationships:
                if rel is not None:
                    rel_types[rel.type] = rel_types.get(rel.type, 0) + 1
            
            # Sort relationship types by frequency
            sorted_rel_types = sorted(rel_types.items(), key=lambda x: x[1], reverse=True)
            rel_type_summary = ", ".join([f"{rel_type} ({count})" for rel_type, count in sorted_rel_types])
            
            # Prepare community data for summary generation
            community_data = {
                "nodes": [],
                "relationships": [],
                "statistics": {
                    "node_count": len(nodes),
                    "relationship_count": len([r for r in relationships if r is not None]),
                    "node_types": dict(sorted_types),
                    "relationship_types": dict(sorted_rel_types)
                }
            }
            
            for node in nodes:
                node_data = {
                    "id": node.element_id,
                    "labels": list(node.labels),
                    "properties": dict(node)
                }
                community_data["nodes"].append(node_data)
            
            for rel in relationships:
                if rel is None:
                    continue
                rel_data = {
                    "type": rel.type,
                    "start_node": rel.start_node.element_id,
                    "end_node": rel.end_node.element_id,
                    "properties": dict(rel)
                }
                community_data["relationships"].append(rel_data)
            
            # Generate summary using LLM
            summary = generate_community_summary(llm, community_data, community_id)
            
            # Create a descriptive name for the community based on its content
            community_name = generate_community_name(community_data, community_id)
            
            # Update Community node with summary and name
            session.run("""
                MATCH (c:Community {id: $community_id})
                SET c.summary = $summary,
                    c.name = $name,
                    c.node_count = $node_count,
                    c.node_types = $node_types,
                    c.relationship_types = $relationship_types
            """, 
                community_id=community_id, 
                summary=summary,
                name=community_name,
                node_count=len(nodes),
                node_types=type_summary,
                relationship_types=rel_type_summary
            )
            
            logging.info(f"Generated summary for community {community_id}: {community_name}")
        
        # Clean up the graph projection
        session.run("""
            CALL gds.graph.drop('entity-graph')
            YIELD graphName
            RETURN graphName
        """)
        
        logging.info("Community detection and summarization completed successfully")

def generate_community_name(community_data, community_id):
    """Generate a descriptive name for a community based on its content."""
    # Extract the most common entity types
    node_types = community_data["statistics"]["node_types"]
    if not node_types:
        return f"Community {community_id}"
    
    # Get the most common entity type
    primary_type = max(node_types.items(), key=lambda x: x[1])[0]
    
    # Extract entity names for the primary type
    primary_entities = []
    for node in community_data["nodes"]:
        if primary_type in node["labels"]:
            name = node["properties"].get("name", "")
            if name and isinstance(name, str):
                primary_entities.append(name)
            elif name and isinstance(name, list) and len(name) > 0:
                primary_entities.append(name[0])
    
    # If we have primary entities, use them in the name
    if primary_entities:
        if len(primary_entities) == 1:
            return f"{primary_entities[0]} ({primary_type})"
        elif len(primary_entities) == 2:
            return f"{primary_entities[0]} & {primary_entities[1]} ({primary_type}s)"
        else:
            return f"{primary_entities[0]} & Others ({primary_type}s)"
    
    # Fallback to a generic name
    return f"{primary_type} Community {community_id}"

def generate_community_summary(llm, community_data, community_id):
    """Generate a summary for a community using the LLM."""
    # Extract entity names and types
    entity_info = []
    for node in community_data["nodes"]:
        name = node["properties"].get("name", "Unnamed entity")
        entity_type = next((label for label in node["labels"] if label not in ["__Entity__", "__KGBuilder__"]), "Entity")
        description = node["properties"].get("description", "")
        
        # Handle case where name is a list
        if isinstance(name, list) and name:
            name = name[0]
            
        # Add race and other properties if available
        race = node["properties"].get("race", "")
        title = node["properties"].get("title", "")
        status = node["properties"].get("status", "")
        
        entity_details = f"{name} ({entity_type})"
        if race:
            entity_details += f", Race: {race}"
        if title:
            entity_details += f", Title: {title}"
        if status:
            entity_details += f", Status: {status}"
        if description:
            entity_details += f" - {description}"
            
        entity_info.append(entity_details)
    
    # Extract relationship information
    relationship_info = []
    for rel in community_data["relationships"]:
        start_node_id = rel["start_node"]
        end_node_id = rel["end_node"]
        
        # Find the corresponding nodes
        start_node = next((n for n in community_data["nodes"] if n["id"] == start_node_id), None)
        end_node = next((n for n in community_data["nodes"] if n["id"] == end_node_id), None)
        
        if start_node and end_node:
            start_name = start_node["properties"].get("name", "Unnamed entity")
            end_name = end_node["properties"].get("name", "Unnamed entity")
            
            # Handle case where name is a list
            if isinstance(start_name, list) and start_name:
                start_name = start_name[0]
            if isinstance(end_name, list) and end_name:
                end_name = end_name[0]
                
            rel_type = rel["type"]
            description = rel["properties"].get("description", "")
            relationship_info.append(f"{start_name} {rel_type} {end_name}: {description}")
    
    # Get statistics about the community
    node_types = community_data["statistics"]["node_types"]
    relationship_types = community_data["statistics"]["relationship_types"]
    
    # Create a detailed summary based on the community content
    if not entity_info:
        return f"Community {community_id} is empty."
    
    # Generate a summary based on the community content without using LLM
    primary_type = max(node_types.items(), key=lambda x: x[1])[0] if node_types else "Unknown"
    
    # Get the most common relationship type
    primary_rel_type = max(relationship_types.items(), key=lambda x: x[1])[0] if relationship_types else "Unknown"
    
    # Create a summary based on the community content
    summary = f"Community {community_id} focuses on {primary_type}s in Tolkien's Middle-earth. "
    
    # Add information about the entities
    if len(entity_info) == 1:
        summary += f"It contains a single {primary_type}: {entity_info[0].split('(')[0].strip()}. "
    elif len(entity_info) == 2:
        names = [info.split('(')[0].strip() for info in entity_info]
        summary += f"It contains two {primary_type}s: {names[0]} and {names[1]}. "
    else:
        names = [info.split('(')[0].strip() for info in entity_info]
        summary += f"It contains {len(names)} {primary_type}s including {names[0]}, {names[1]}, and others. "
    
    # Add information about relationships
    if relationship_info:
        summary += f"The primary relationship type is {primary_rel_type}, "
        if primary_rel_type == "DWELLS_IN":
            summary += "showing where characters live or reside. "
        elif primary_rel_type == "LOCATED_IN":
            summary += "showing geographical relationships between locations. "
        elif primary_rel_type == "KNOWS_ABOUT":
            summary += "showing knowledge relationships between characters. "
        elif primary_rel_type == "PARTICIPATES_IN":
            summary += "showing character participation in events. "
        elif primary_rel_type == "PARENT_OF" or primary_rel_type == "CHILD_OF":
            summary += "showing family relationships. "
        else:
            summary += f"connecting the {primary_type}s in this community. "
    
    # Add information about the significance
    if primary_type == "Character":
        summary += "These characters play important roles in the narrative of Middle-earth, "
        if "Bilbo" in summary and "Frodo" in summary:
            summary += "particularly in the events surrounding the One Ring and the War of the Ring."
        else:
            summary += "contributing to the rich tapestry of Tolkien's world."
    elif primary_type == "Location":
        summary += "These locations form an important part of Middle-earth's geography, "
        if "Hobbiton" in summary or "Bag End" in summary:
            summary += "particularly in the Shire region where hobbits dwell."
        else:
            summary += "providing the setting for key events in Tolkien's legendarium."
    elif primary_type == "Event":
        summary += "These events are significant occurrences in the history of Middle-earth, "
        if "Birthday" in summary:
            summary += "particularly related to Bilbo Baggins' famous eleventy-first birthday celebration."
        else:
            summary += "shaping the course of its history and the fates of its inhabitants."
    
    # Try to use OpenAI LLM if the above summary is too generic
    try:
        # Prepare prompt for LLM
        prompt = f"""
You are an expert in Tolkien's Middle-earth lore. Your task is to generate a concise summary for a community of related entities from Middle-earth.

Community ID: {community_id}
Primary Entity Type: {primary_type}

Entities in this community:
{chr(10).join(entity_info)}

Relationships in this community:
{chr(10).join(relationship_info)}

Based on the above information, provide a concise summary (2-3 paragraphs) that:
1. Identifies the main theme or focus of this community
2. Explains how these entities are related to each other
3. Highlights the significance of this community in the broader context of Middle-earth

Summary:
"""
        # Use the OpenAI API directly
        from openai import OpenAI
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in Tolkien's Middle-earth lore."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        
        llm_summary = response.choices[0].message.content.strip()
        if llm_summary and len(llm_summary) > len(summary):
            return llm_summary
        
    except Exception as e:
        logging.warning(f"Failed to generate LLM summary for community {community_id}: {e}")
    
    return summary

def is_pdf_file(file_path):
    """
    Determine if a file is a PDF using both file extension and MIME type.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if the file is a PDF, False otherwise
    """
    # Check file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext == '.pdf':
        return True
    
    # Check MIME type as a backup
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type == 'application/pdf':
        return True
    
    # If we have a Path object, try to read the first few bytes to check for PDF signature
    try:
        with open(file_path, 'rb') as f:
            header = f.read(5)
            if header == b'%PDF-':
                return True
    except Exception:
        pass
    
    return False

def resolve_duplicate_entities(driver):
    """
    Post-processing function to resolve duplicate entities like 'Bilbo' and 'Bilbo Baggins'.
    This function identifies potential duplicates and merges them.
    """
    logging.info("Running custom entity resolution to merge duplicates...")
    
    with driver.session() as session:
        # First, check if APOC is available
        try:
            session.run("CALL apoc.help('refactor')")
            logging.info("APOC is available for node merging")
        except Exception as e:
            logging.error(f"APOC is not available, cannot merge nodes: {e}")
            logging.info("Will attempt to use manual merging instead")
            use_apoc = False
        else:
            use_apoc = True
        
        # Process each entity type
        for entity_type in ["Character", "Location", "Organization", "Artifact", "Event"]:
            # 1. Find all entities of this type with their names and aliases
            result = session.run(f"""
                MATCH (e:{entity_type})
                RETURN e.name AS name, elementId(e) AS element_id, e.aliases AS aliases
            """)
            
            entities = [(record["name"], record["element_id"], record["aliases"] or []) for record in result]
            logging.info(f"Found {len(entities)} {entity_type} nodes")
            
            if not entities:
                continue
                
            # Print all entity names and aliases for debugging
            entity_info = [f"{name} (aliases: {aliases})" for name, _, aliases in entities if name]
            logging.info(f"Entity info: {entity_info}")
            
            # 2. First pass: Find potential duplicates based on first name match
            first_name_groups = {}
            for name, node_id, aliases in entities:
                if not name:
                    continue
                
                # Handle case where name is a list
                if isinstance(name, list):
                    # Use the first name in the list
                    if name:
                        canonical_name = name[0]
                        # Extract first name from canonical name
                        first_name = canonical_name.split()[0] if canonical_name else ""
                        if first_name:
                            first_name_groups.setdefault(first_name, []).append((canonical_name, node_id, aliases))
                else:
                    # Extract first name
                    first_name = name.split()[0] if name else ""
                    if first_name:
                        first_name_groups.setdefault(first_name, []).append((name, node_id, aliases))
            
            # Log potential duplicate groups
            for first_name, group in first_name_groups.items():
                if len(group) > 1:
                    logging.info(f"Potential duplicates with first name '{first_name}': {[name for name, _, _ in group]}")
            
            # 3. First pass: Merge duplicates within each first name group
            merged_count = 0
            for first_name, nodes in first_name_groups.items():
                if len(nodes) <= 1:
                    continue
                
                # Sort nodes so that the full name is first (it will be the primary node)
                nodes.sort(key=lambda x: len(x[0]), reverse=True)
                primary_name, primary_id, primary_aliases = nodes[0]
                
                logging.info(f"Merging duplicates for '{first_name}': {[name for name, _, _ in nodes]}")
                
                # For each duplicate, merge it into the primary node
                for name, node_id, aliases in nodes[1:]:
                    if name == primary_name:
                        continue
                    
                    logging.info(f"Merging '{name}' into '{primary_name}'")
                    
                    if use_apoc:
                        # Use APOC for merging if available
                        try:
                            # Add the duplicate name as an alias to the primary node
                            session.run("""
                                MATCH (primary) WHERE elementId(primary) = $primary_element_id
                                MATCH (duplicate) WHERE elementId(duplicate) = $duplicate_element_id
                                
                                // Add the duplicate name as an alias if not already present
                                WITH primary, duplicate
                                SET primary.aliases = 
                                    CASE 
                                        WHEN primary.aliases IS NULL THEN [$duplicate_name] 
                                        WHEN NOT $duplicate_name IN primary.aliases THEN primary.aliases + $duplicate_name 
                                        ELSE primary.aliases 
                                    END
                                
                                // Also add all aliases from the duplicate node
                                WITH primary, duplicate
                                FOREACH (alias IN CASE WHEN duplicate.aliases IS NULL THEN [] ELSE duplicate.aliases END |
                                    SET primary.aliases = 
                                        CASE 
                                            WHEN primary.aliases IS NULL THEN [alias] 
                                            WHEN NOT alias IN primary.aliases THEN primary.aliases + alias 
                                            ELSE primary.aliases 
                                        END
                                )
                                
                                // Move all relationships from duplicate to primary
                                WITH primary, duplicate
                                CALL apoc.refactor.mergeNodes([primary, duplicate], {properties: 'combine', mergeRels: true})
                                YIELD node
                                RETURN node
                            """, primary_element_id=primary_id, duplicate_element_id=node_id, duplicate_name=name)
                            
                            merged_count += 1
                        except Exception as e:
                            logging.error(f"Error merging nodes with APOC: {e}")
                    else:
                        # Manual merging without APOC
                        try:
                            # Add the duplicate name as an alias to the primary node
                            session.run("""
                                MATCH (primary) WHERE elementId(primary) = $primary_element_id
                                MATCH (duplicate) WHERE elementId(duplicate) = $duplicate_element_id
                                
                                // Add the duplicate name as an alias if not already present
                                SET primary.aliases = 
                                    CASE 
                                        WHEN primary.aliases IS NULL THEN [$duplicate_name] 
                                        WHEN NOT $duplicate_name IN primary.aliases THEN primary.aliases + $duplicate_name 
                                        ELSE primary.aliases 
                                    END
                                
                                // Also add all aliases from the duplicate node
                                WITH primary, duplicate
                                FOREACH (alias IN CASE WHEN duplicate.aliases IS NULL THEN [] ELSE duplicate.aliases END |
                                    SET primary.aliases = 
                                        CASE 
                                            WHEN primary.aliases IS NULL THEN [alias] 
                                            WHEN NOT alias IN primary.aliases THEN primary.aliases + alias 
                                            ELSE primary.aliases 
                                        END
                                )
                                
                                // Copy all properties from duplicate to primary
                                WITH primary, duplicate
                                SET primary += {
                                    race: CASE WHEN primary.race IS NULL THEN duplicate.race ELSE primary.race END,
                                    title: CASE WHEN primary.title IS NULL THEN duplicate.title ELSE primary.title END,
                                    status: CASE WHEN primary.status IS NULL THEN duplicate.status ELSE primary.status END,
                                    home_region: CASE WHEN primary.home_region IS NULL THEN duplicate.home_region ELSE primary.home_region END
                                }
                                
                                // Move all relationships from duplicate to primary
                                WITH primary, duplicate
                                MATCH (duplicate)-[r]->(target)
                                WHERE NOT (primary)-[:SAME_RELATIONSHIP_TYPE]->(target)
                                WITH primary, duplicate, r, target, type(r) AS relType
                                CALL apoc.create.relationship(primary, relType, properties(r), target) YIELD rel
                                
                                // Delete the duplicate node
                                WITH duplicate
                                DETACH DELETE duplicate
                            """, primary_element_id=primary_id, duplicate_element_id=node_id, duplicate_name=name)
                            
                            merged_count += 1
                        except Exception as e:
                            logging.error(f"Error with manual merging: {e}")
            
            # Skip the second pass for now to avoid the unhashable type error
            logging.info(f"Completed first pass of entity resolution for {entity_type}")
            
            logging.info(f"Merged {merged_count} duplicate {entity_type} nodes")
        
        # 5. Final cleanup: Ensure all relationships use canonical names
        session.run("""
            MATCH (n)-[r]->(m)
            WHERE type(r) IN ['PARENT_OF', 'CHILD_OF', 'MARRIED_TO', 'SERVES', 'ALLIES_WITH', 'OPPOSES', 'MENTORS']
            RETURN n.name, type(r), m.name
        """)
        
        logging.info("Entity resolution completed")

def main():
    """Main function to run the Neo4j GraphRAG pipeline for Tolkien lore ingestion."""
    
    # Initialize Neo4j driver
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    # Initialize LLM and embedder with environment-specified models
    llm = OpenAILLM(model_name=LLM_MODEL)
    embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    text_splitter = FixedSizeSplitter(chunk_size=500, chunk_overlap=100)
    
    logging.info(f"Using LLM model: {LLM_MODEL}")
    logging.info(f"Using embedding model: {EMBEDDING_MODEL}")
    
    # Define custom extraction prompt for Tolkien lore
    custom_extraction_prompt = """
You are a top-tier algorithm designed for extracting information from Tolkien's Middle-earth lore to build a comprehensive knowledge graph.

-Goal-
Given a text document about Tolkien's Middle-earth (from books, forums, or scripts), identify all entities and relationships that contribute to the rich lore of this fantasy world. Focus on characters, locations, artifacts, events, and organizations that are significant to understanding Middle-earth's history, geography, and inhabitants.

-Instructions-
1. ENTITY EXTRACTION: For each identified entity, extract:
   - entity_name: CANONICAL full name as the primary identifier (e.g., "Bilbo Baggins" not just "Bilbo")
   - entity_type: One of [Character, Location, Artifact, Organization, Event]
   - entity_description: Comprehensive description including key attributes, significance, and context within Middle-earth lore
   - properties: Relevant properties based on entity type (race, title, powers, location, etc.)
   - aliases: List of alternative names, titles, or references used for this entity in the text

2. ENTITY RESOLUTION: Carefully identify when different mentions refer to the same entity:
   - ALWAYS use the most complete, canonical name as the primary identifier (e.g., "Bilbo Baggins" not just "Bilbo")
   - NEVER create separate entities for partial names - "Bilbo" and "Bilbo Baggins" are the same entity
   - First names, last names, and titles alone should ALWAYS be treated as aliases of the full canonical name
   - For characters, the canonical name should include both first and last name when available (e.g., "Bilbo Baggins", "Frodo Baggins")
   - For characters mentioned only by first name (e.g., "Bilbo"), use context to determine their full name
   - When in doubt about whether two similar names refer to the same entity, prefer to merge them rather than create duplicates
   - Include ALL discovered aliases in the entity's aliases property, including partial names, nicknames, and titles

3. RELATIONSHIP EXTRACTION: For each pair of related entities, extract:
   - source_entity: Canonical name of the source entity
   - target_entity: Canonical name of the target entity  
   - relationship_type: Specific relationship from the defined relations list
   - relationship_description: Detailed explanation of the relationship with context
   - relationship_strength: Numeric score (1-10) indicating relationship importance/certainty

4. CONTEXTUAL CONSIDERATIONS:
   - Pay attention to different Ages (First, Second, Third Age) and time periods
   - Consider the various races and their unique characteristics
   - Note the significance of locations in Middle-earth geography
   - Identify artifacts of power and their histories
   - Recognize important lineages and family connections
   - Capture the complex web of alliances and enmities
   - Include both canonical and fan-discussed elements when clearly identified

5. FORMAT: Return as JSON with nodes and relationships arrays:
   {
     "nodes": [
       {
         "id": "<canonical_entity_name>",
         "label": "<entity_type>",
         "properties": {
           "name": "<canonical_entity_name>",
           "description": "<entity_description>",
           "aliases": ["<alias1>", "<alias2>", ...],
           ... other properties based on entity type ...
         }
       },
       ...
     ],
     "relationships": [
       {
         "start_node_id": "<canonical_source_entity>",
         "end_node_id": "<canonical_target_entity>",
         "type": "<relationship_type>",
         "properties": {
           "description": "<relationship_description>",
           "strength": <relationship_strength>
         }
       },
       ...
     ]
   }

6. QUALITY GUIDELINES:
   - Always use full canonical names as primary identifiers to prevent duplicate entities
   - Prioritize named entities over generic references
   - Ensure relationship directionality is correct (e.g., Aragorn RULES Gondor, not vice versa)
   - Include both major and minor characters if they have significant connections
   - Capture both explicit and implied relationships
   - Consider the source material type (canonical vs. fan discussion vs. adaptation)
   - Fill in all required properties for each entity type

Use only the following nodes and relationships (if provided):
{schema}

Examples:
{examples}

Input text:
{text}
"""
    
    # Create example extraction for Tolkien lore
    tolkien_example = """
Text: "Aragorn, also known as Strider and heir of Isildur, was the rightful king of Gondor. He wielded the reforged sword Andúril during the War of the Ring. He was guided by Gandalf the Grey (also called Mithrandir by the Elves) and formed strong bonds with the Fellowship members, particularly Legolas of the Woodland Realm and Gimli son of Glóin."

{
  "nodes": [
    {
      "id": "Aragorn son of Arathorn",
      "label": "Character",
      "properties": {
        "name": "Aragorn son of Arathorn",
        "description": "Heir of Isildur and rightful king of Gondor who wielded Andúril during the War of the Ring",
        "aliases": ["Aragorn", "Strider", "Elessar", "Thorongil", "Estel"],
        "race": "Human",
        "title": "King of Gondor",
        "status": "alive",
        "home_region": "Gondor"
      }
    },
    {
      "id": "Isildur",
      "label": "Character",
      "properties": {
        "name": "Isildur",
        "description": "Ancient king whose heir is Aragorn, connected to the lineage of Gondor's rightful rulers",
        "aliases": ["High King Isildur", "Son of Elendil"],
        "race": "Human",
        "title": "King",
        "status": "dead",
        "home_region": "Gondor"
      }
    },
    {
      "id": "Gondor",
      "label": "Location",
      "properties": {
        "name": "Gondor",
        "description": "Kingdom in Middle-earth ruled by Aragorn as its rightful king",
        "aliases": ["South Kingdom", "Land of Stone"],
        "location_type": "kingdom",
        "region": "Middle-earth",
        "significance": "Major human kingdom"
      }
    },
    {
      "id": "Andúril",
      "label": "Artifact",
      "properties": {
        "name": "Andúril",
        "description": "Reforged sword wielded by Aragorn during the War of the Ring",
        "aliases": ["Flame of the West", "Reforged Narsil"],
        "artifact_type": "sword",
        "material": "metal",
        "powers": "reforged blade of Narsil",
        "current_status": "possessed"
      }
    },
    {
      "id": "War of the Ring",
      "label": "Event",
      "properties": {
        "name": "War of the Ring",
        "description": "Major conflict during which Aragorn wielded Andúril",
        "aliases": ["Great War", "War against Sauron"],
        "event_type": "war",
        "age": "Third Age",
        "outcome": "Victory against Sauron",
        "significance": "decisive conflict"
      }
    },
    {
      "id": "Gandalf the Grey",
      "label": "Character",
      "properties": {
        "name": "Gandalf the Grey",
        "description": "Wizard who guided Aragorn",
        "aliases": ["Mithrandir", "Olórin", "Gandalf", "Grey Pilgrim", "Tharkûn"],
        "race": "Maiar",
        "title": "Wizard",
        "status": "transformed to Gandalf the White",
        "home_region": "Valinor"
      }
    },
    {
      "id": "Fellowship of the Ring",
      "label": "Organization",
      "properties": {
        "name": "Fellowship of the Ring",
        "description": "Group that included Aragorn and formed strong bonds",
        "aliases": ["Fellowship", "Nine Walkers", "Company of the Ring"],
        "organization_type": "fellowship",
        "purpose": "destroy the One Ring",
        "status": "disbanded after completing mission"
      }
    },
    {
      "id": "Legolas Greenleaf",
      "label": "Character",
      "properties": {
        "name": "Legolas Greenleaf",
        "description": "Elf of the Woodland Realm who formed strong bonds with Aragorn",
        "aliases": ["Legolas", "Prince of Mirkwood"],
        "race": "Elf",
        "title": "Prince",
        "status": "alive",
        "home_region": "Woodland Realm"
      }
    },
    {
      "id": "Woodland Realm",
      "label": "Location",
      "properties": {
        "name": "Woodland Realm",
        "description": "Elven realm where Legolas originates",
        "aliases": ["Mirkwood", "Northern Mirkwood", "Eryn Lasgalen"],
        "location_type": "elven realm",
        "region": "Middle-earth",
        "significance": "Important Elven kingdom"
      }
    },
    {
      "id": "Gimli son of Glóin",
      "label": "Character",
      "properties": {
        "name": "Gimli son of Glóin",
        "description": "Dwarf who formed strong bonds with Aragorn",
        "aliases": ["Gimli", "Lord of the Glittering Caves", "Elf-friend"],
        "race": "Dwarf",
        "title": "Lord of the Glittering Caves",
        "status": "alive",
        "home_region": "Erebor"
      }
    }
  ],
  "relationships": [
    {
      "start_node_id": "Aragorn son of Arathorn",
      "end_node_id": "Isildur",
      "type": "CHILD_OF",
      "properties": {
        "description": "Aragorn is the heir of Isildur, indicating a direct lineage connection to the ancient king",
        "strength": 9
      }
    },
    {
      "start_node_id": "Aragorn son of Arathorn",
      "end_node_id": "Gondor",
      "type": "RULES",
      "properties": {
        "description": "Aragorn is the rightful king of Gondor, having legitimate claim to rule the kingdom",
        "strength": 10
      }
    },
    {
      "start_node_id": "Aragorn son of Arathorn",
      "end_node_id": "Andúril",
      "type": "WIELDS",
      "properties": {
        "description": "Aragorn wielded the reforged sword Andúril during the War of the Ring",
        "strength": 8
      }
    },
    {
      "start_node_id": "Aragorn son of Arathorn",
      "end_node_id": "War of the Ring",
      "type": "PARTICIPATES_IN",
      "properties": {
        "description": "Aragorn participated in the War of the Ring, wielding Andúril during this conflict",
        "strength": 9
      }
    },
    {
      "start_node_id": "Gandalf the Grey",
      "end_node_id": "Aragorn son of Arathorn",
      "type": "MENTORS",
      "properties": {
        "description": "Gandalf guided Aragorn, indicating a mentoring relationship",
        "strength": 7
      }
    },
    {
      "start_node_id": "Aragorn son of Arathorn",
      "end_node_id": "Fellowship of the Ring",
      "type": "MEMBER_OF",
      "properties": {
        "description": "Aragorn was a member of the Fellowship and formed strong bonds with other members",
        "strength": 8
      }
    },
    {
      "start_node_id": "Aragorn son of Arathorn",
      "end_node_id": "Legolas Greenleaf",
      "type": "ALLIES_WITH",
      "properties": {
        "description": "Aragorn formed strong bonds with Legolas, indicating a close alliance",
        "strength": 7
      }
    },
    {
      "start_node_id": "Legolas Greenleaf",
      "end_node_id": "Woodland Realm",
      "type": "DWELLS_IN",
      "properties": {
        "description": "Legolas is from the Woodland Realm",
        "strength": 8
      }
    },
    {
      "start_node_id": "Aragorn son of Arathorn",
      "end_node_id": "Gimli son of Glóin",
      "type": "ALLIES_WITH",
      "properties": {
        "description": "Aragorn formed strong bonds with Gimli, indicating friendship and alliance",
        "strength": 7
      }
    }
  ]
}
"""

    # Create the pipeline with standard parameters
    pipeline = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        entities=ENTITIES,
        relations=RELATIONS,
        potential_schema=POTENTIAL_SCHEMA,
        text_splitter=text_splitter,
        perform_entity_resolution=True,
        neo4j_database="neo4j",
        from_pdf=False
    )
    
    # Get list of input files (both TXT and PDF), robust to working directory
    # Use a robust relative input directory: '../../input' from this script's directory
    input_dir = (Path(__file__).parent.parent.parent / "input").resolve()
    txt_files = list(input_dir.glob("*.txt"))
    pdf_files = list(input_dir.glob("*.pdf"))
    file_list = [str(f) for f in txt_files + pdf_files]

    if not file_list:
        logging.warning(f"No .txt or .pdf files found in {input_dir} (project input directory)")
        return
    
    # Set up progress bar if available
    iterator = tqdm(file_list, desc="Ingesting files", unit="file") if tqdm else file_list
    
    # Process each file
    for file_path in iterator:
        logging.info(f"\n---\n[START] Ingesting: {file_path}")
        
        try:
            # Determine file type using our helper function
            is_pdf = is_pdf_file(file_path)
            
            # Create appropriate pipeline based on file type
            if is_pdf:
                # Create a PDF-specific pipeline
                pdf_pipeline = SimpleKGPipeline(
                    llm=llm,
                    driver=driver,
                    embedder=embedder,
                    entities=ENTITIES,
                    relations=RELATIONS,
                    potential_schema=POTENTIAL_SCHEMA,
                    text_splitter=text_splitter,
                    perform_entity_resolution=True,
                    neo4j_database="neo4j",
                    from_pdf=True  # Set to True for PDF processing
                )
                
                logging.info("[STEP] Running pipeline on PDF file...")
                # For PDFs, pass the file path directly
                result = asyncio.run(pdf_pipeline.run_async(file_path=file_path))
            else:
                # For text files, read the content and pass as text
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                logging.info("[STEP] Running pipeline on text file...")
                result = asyncio.run(pipeline.run_async(text=text))
            
            logging.info("[DONE] File ingested successfully.")
            logging.info(f"Pipeline result: {result}")
            
        except Exception as e:
            logging.error(f"[ERROR] Ingestion failed for {file_path}: {e}")
            continue
    
    # After processing all files, run custom entity resolution to merge duplicates
    try:
        logging.info("Running post-processing to resolve duplicate entities...")
        resolve_duplicate_entities(driver)
    except Exception as e:
        logging.error(f"[ERROR] Entity resolution failed: {e}")
        logging.info("Continuing without entity resolution...")
    
    # After entity resolution, run community detection
    try:
        detect_communities(driver, llm)
    except Exception as e:
        logging.error(f"[ERROR] Community detection failed: {e}")
        logging.info("Continuing without community detection...")
    
    logging.info("\nAll files processed. Check Neo4j for your knowledge graph.")
    driver.close()

if __name__ == "__main__":
    main()
