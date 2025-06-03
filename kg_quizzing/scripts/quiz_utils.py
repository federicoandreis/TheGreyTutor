"""
Utility functions for the adaptive quizzing system.
Provides common functionality for connecting to Neo4j and processing quiz-related data.
"""
import os
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables from .env if available
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Neo4j connection parameters
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def get_neo4j_driver():
    """Creates and returns a Neo4j driver instance."""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def execute_query(cypher: str, params: Optional[Dict[str, Any]] = None) -> List[Dict]:
    """
    Executes a Cypher query and returns the results as a list of dictionaries.
    Handles Neo4j warnings gracefully by logging them at debug level instead of warning.
    
    Args:
        cypher: The Cypher query to execute
        params: Optional parameters for the query
        
    Returns:
        List of result records as dictionaries
    """
    # Configure Neo4j logging to be less verbose
    neo4j_logger = logging.getLogger('neo4j')
    original_level = neo4j_logger.level
    neo4j_logger.setLevel(logging.ERROR)  # Only show errors, not warnings
    
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            if params is None:
                params = {}
            result = session.run(cypher, params)
            records = [dict(record) for record in result]
        return records
    except Exception as e:
        logger.error(f"Error executing Neo4j query: {e}")
        return []
    finally:
        driver.close()
        # Restore original logging level
        neo4j_logger.setLevel(original_level)

def check_educational_metadata_exists():
    """
    Check if the educational metadata schema exists in the database.
    
    Returns:
        bool: True if the educational metadata exists, False otherwise
    """
    # Use a more robust approach that doesn't rely on labels that might not exist yet
    # Instead, check if any constraints exist with our expected names
    query = """
    SHOW CONSTRAINTS
    """
    
    try:
        results = execute_query(query)
        
        # Look for our specific constraint names
        constraint_names = ["question_template_id", "learning_objective_id", "student_model_id"]
        for record in results:
            if record.get("name") in constraint_names:
                return True
        
        return False
    except Exception as e:
        logger.warning(f"Error checking educational metadata: {e}")
        return False

def get_available_communities():
    """
    Get all available communities in the knowledge graph.
    
    Returns:
        List of community information including id, name, and summary
    """
    query = """
    MATCH (c:Community)
    RETURN id(c) AS id, c.name AS name, c.summary AS summary
    ORDER BY c.name
    """
    
    return execute_query(query)

def get_entities_in_community(community_id: int, limit: int = 10):
    """
    Get entities in a specific community.
    
    Args:
        community_id: The ID of the community
        limit: Maximum number of entities to return
        
    Returns:
        List of entities in the community
    """
    query = """
    MATCH (n)-[:BELONGS_TO_COMMUNITY]->(c:Community)
    WHERE id(c) = $community_id AND NOT n:Community AND NOT n:Document AND NOT n:Chunk
    RETURN n.name AS name, labels(n) AS labels, id(n) AS id
    LIMIT $limit
    """
    
    return execute_query(query, {"community_id": community_id, "limit": limit})

def get_entity_by_name(name: str):
    """
    Get an entity by its name.
    
    Args:
        name: The name of the entity
        
    Returns:
        Entity information if found, None otherwise
    """
    query = """
    MATCH (n)
    WHERE n.name = $name
    RETURN n, labels(n) AS labels
    LIMIT 1
    """
    
    results = execute_query(query, {"name": name})
    return results[0] if results else None

def get_entity_relationships(entity_id: str, limit: int = 10):
    """
    Get relationships for a specific entity.
    
    Args:
        entity_id: The ID of the entity
        limit: Maximum number of relationships to return
        
    Returns:
        List of relationships for the entity
    """
    query = """
    MATCH (n)-[r]-(m)
    WHERE elementId(n) = $entity_id
    RETURN type(r) AS relationship_type, m.name AS related_entity_name, 
           labels(m) AS related_entity_labels
    LIMIT $limit
    """
    
    return execute_query(query, {"entity_id": entity_id, "limit": limit})

def calculate_difficulty_score(entity_data: Dict[str, Any]) -> int:
    """
    Calculate a difficulty score for an entity based on its properties and relationships.
    
    Args:
        entity_data: Dictionary containing entity information
        
    Returns:
        Difficulty score from 1-10
    """
    # This is a placeholder implementation
    # In a real system, this would use more sophisticated metrics
    
    # Base difficulty starts at 5 (medium)
    difficulty = 5
    
    # If the entity has many relationships, it's more complex
    if "relationships" in entity_data and entity_data["relationships"]:
        relationship_count = len(entity_data["relationships"])
        # Adjust difficulty based on relationship count
        if relationship_count > 10:
            difficulty += 3
        elif relationship_count > 5:
            difficulty += 2
        elif relationship_count > 2:
            difficulty += 1
    
    # If the entity is in multiple communities, it's more complex
    if "communities" in entity_data and entity_data["communities"]:
        community_count = len(entity_data["communities"])
        if community_count > 2:
            difficulty += 2
        elif community_count > 1:
            difficulty += 1
    
    # Ensure difficulty is within 1-10 range
    return max(1, min(10, difficulty))
