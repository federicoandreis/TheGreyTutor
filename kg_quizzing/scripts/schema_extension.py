"""
Schema Extension Module for Adaptive Quizzing.

This module extends the existing Neo4j GraphRAG schema with educational metadata
to support adaptive quizzing functionality.
"""
import os
import logging
import argparse
from typing import Dict, List, Any, Optional

from quiz_utils import execute_query, check_educational_metadata_exists, get_available_communities

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_educational_schema():
    """
    Create the educational metadata schema in the Neo4j database.
    This includes QuestionTemplate, LearningObjective, and StudentModel nodes
    and their relationships.
    
    Returns:
        bool: True if successful, False otherwise
    """
    if check_educational_metadata_exists():
        logger.info("Educational metadata schema already exists.")
        return True
    
    logger.info("Creating educational metadata schema...")
    
    # Define the schema creation queries
    queries = [
        # Create constraint for QuestionTemplate
        "CREATE CONSTRAINT question_template_id IF NOT EXISTS FOR (qt:QuestionTemplate) REQUIRE qt.id IS UNIQUE",
        
        # Create constraint for LearningObjective
        "CREATE CONSTRAINT learning_objective_id IF NOT EXISTS FOR (lo:LearningObjective) REQUIRE lo.id IS UNIQUE",
        
        # Create constraint for StudentModel
        "CREATE CONSTRAINT student_model_id IF NOT EXISTS FOR (sm:StudentModel) REQUIRE sm.id IS UNIQUE"
    ]
    
    try:
        # Execute each query separately
        for query in queries:
            execute_query(query)
        
        logger.info("Successfully created educational metadata schema constraints.")
        return True
    except Exception as e:
        logger.error(f"Failed to create educational metadata schema: {e}")
        return False

def create_question_templates():
    """
    Create basic question templates for different question types.
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Creating question templates...")
    
    # Define question templates for different question types
    templates = [
        # Factual questions about entity properties
        {
            "id": "factual_property_1",
            "type": "factual",
            "difficulty": 1,
            "template": "In the ancient scrolls of Gondor, what is recorded as the {property} of {entity}?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        {
            "id": "factual_property_2",
            "type": "factual",
            "difficulty": 2,
            "template": "According to the lore kept in the libraries of Rivendell, what is the {property} of {entity}?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        {
            "id": "factual_property_3",
            "type": "factual",
            "difficulty": 1,
            "template": "What name do the Elves give to {entity} in the chronicles of the Elder Days?",
            "applicable_labels": ["Character", "Location", "Artifact"]
        },
        {
            "id": "factual_property_4",
            "type": "factual",
            "difficulty": 2,
            "template": "The White Council's records describe what {property} for {entity}?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        # Relationship questions
        {
            "id": "relationship_1",
            "type": "relationship",
            "difficulty": 3,
            "template": "How are {entity1} and {entity2} connected in the histories of Middle-earth?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        {
            "id": "relationship_2",
            "type": "relationship",
            "difficulty": 4,
            "template": "What bond exists between {entity1} and {entity2} in the chronicles of the Third Age?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        {
            "id": "relationship_3",
            "type": "relationship",
            "difficulty": 3,
            "template": "In what way is {entity1} linked to {entity2} in the tales told by the Eldar?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        # Multiple-choice questions
        {
            "id": "multiple_choice_1",
            "type": "multiple_choice",
            "difficulty": 2,
            "template": "Which of these is {relationship_type} {entity} in the lore of Middle-earth?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        {
            "id": "multiple_choice_2",
            "type": "multiple_choice",
            "difficulty": 3,
            "template": "According to the archives of Minas Tirith, which one of these is {relationship_type} {entity}?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        {
            "id": "multiple_choice_3",
            "type": "multiple_choice",
            "difficulty": 2,
            "template": "The scrolls of Erebor mention one of these beings as {relationship_type} {entity}. Which is it?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        # Synthesis questions across communities
        {
            "id": "synthesis_1",
            "type": "synthesis",
            "difficulty": 7,
            "template": "Compare the roles of {entity1} and {entity2} in shaping the history of Middle-earth. How did their actions influence the events of their age?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        {
            "id": "synthesis_2",
            "type": "synthesis",
            "difficulty": 8,
            "template": "How do the stories of {entity1} and {entity2} reflect the eternal struggle between light and shadow that runs through all the tales of Middle-earth?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        {
            "id": "synthesis_3",
            "type": "synthesis",
            "difficulty": 7,
            "template": "What common themes can be found in the lore surrounding both {entity1} and {entity2}, despite their different origins in Middle-earth?",
            "applicable_labels": ["Character", "Location", "Artifact", "Organization", "Event"]
        },
        # Application questions
        {
            "id": "application_1",
            "type": "application",
            "difficulty": 8,
            "template": "If {entity1} had encountered {entity2} during the War of the Ring, how might the course of history have changed?",
            "applicable_labels": ["Character", "Event"]
        },
        {
            "id": "application_2",
            "type": "application",
            "difficulty": 9,
            "template": "Imagine {entity1} had possessed the same wisdom as {entity2}. How might their fate have differed in the tales of Middle-earth?",
            "applicable_labels": ["Character", "Event"]
        },
        {
            "id": "application_3",
            "type": "application",
            "difficulty": 8,
            "template": "What lessons from the tale of {entity1} might have benefited {entity2} in their own journey?",
            "applicable_labels": ["Character", "Event"]
        }
    ]
    
    # Create query to insert templates
    query = """
    UNWIND $templates AS template
    MERGE (qt:QuestionTemplate {id: template.id})
    SET qt.type = template.type,
        qt.difficulty = template.difficulty,
        qt.template = template.template,
        qt.applicable_labels = template.applicable_labels
    """
    
    try:
        execute_query(query, {"templates": templates})
        logger.info(f"Successfully created {len(templates)} question templates.")
        return True
    except Exception as e:
        logger.error(f"Failed to create question templates: {e}")
        return False

def create_learning_objectives():
    """
    Create learning objectives based on communities in the knowledge graph.
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Creating learning objectives based on communities...")
    
    # Get available communities
    communities = get_available_communities()
    
    if not communities:
        logger.warning("No communities found in the knowledge graph.")
        return False
    
    # Create learning objectives based on communities
    learning_objectives = []
    
    for community in communities:
        community_id = community["id"]
        community_name = community.get("name", f"Community {community_id}")
        
        # Create a learning objective for the community
        learning_objectives.append({
            "id": f"lo_community_{community_id}",
            "description": f"Understand the key entities and relationships in {community_name}",
            "community_id": community_id,
            "difficulty": 5,  # Medium difficulty by default
            "prerequisite_ids": []  # No prerequisites by default
        })
    
    # Create query to insert learning objectives
    query = """
    UNWIND $objectives AS objective
    MERGE (lo:LearningObjective {id: objective.id})
    SET lo.description = objective.description,
        lo.community_id = objective.community_id,
        lo.difficulty = objective.difficulty,
        lo.prerequisite_ids = objective.prerequisite_ids
    WITH lo
    MATCH (c:Community {community_id: lo.community_id})
    MERGE (lo)-[:ASSOCIATED_WITH]->(c)
    """
    
    try:
        execute_query(query, {"objectives": learning_objectives})
        logger.info(f"Successfully created {len(learning_objectives)} learning objectives.")
        
        # Now create prerequisite relationships between communities
        # This is a simplified approach - in a real system, this would be more sophisticated
        if len(communities) > 1:
            logger.info("Creating prerequisite relationships between learning objectives...")
            
            # Create a simple chain of prerequisites
            prerequisite_query = """
            MATCH (lo:LearningObjective)
            WITH lo ORDER BY lo.community_id
            WITH collect(lo) AS objectives
            UNWIND range(1, size(objectives)-1) AS i
            WITH objectives[i-1] AS prereq, objectives[i] AS current
            MERGE (current)-[:HAS_PREREQUISITE]->(prereq)
            """
            
            execute_query(prerequisite_query)
            logger.info("Successfully created prerequisite relationships.")
        
        return True
    except Exception as e:
        logger.error(f"Failed to create learning objectives: {e}")
        return False

def create_difficulty_progression_paths():
    """
    Create difficulty progression paths between entities in the knowledge graph.
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Creating difficulty progression paths...")
    
    # This is a simplified approach - in a real system, this would be more sophisticated
    # We'll create DIFFICULTY_PROGRESSION relationships between entities in the same community
    # based on their complexity (number of relationships)
    
    # Split the query into two separate queries to avoid syntax error
    queries = [
        # Query 1: Calculate complexity for each entity based on relationship count
        # Using COUNT instead of size() function for better compatibility
        """
        MATCH (n)
        WHERE NOT n:Community AND NOT n:Document AND NOT n:Chunk
          AND NOT n:QuestionTemplate AND NOT n:LearningObjective AND NOT n:StudentModel
        MATCH (n)-[r]-()
        WITH n, COUNT(r) AS complexity
        SET n.complexity = complexity
        """,
        
        # Query 2: Create DIFFICULTY_PROGRESSION relationships within communities
        """
        MATCH (n1)-[:BELONGS_TO_COMMUNITY]->(c:Community)<-[:BELONGS_TO_COMMUNITY]-(n2)
        WHERE n1.complexity < n2.complexity
          AND NOT n1:Community AND NOT n1:Document AND NOT n1:Chunk
          AND NOT n2:Community AND NOT n2:Document AND NOT n2:Chunk
          AND NOT n1:QuestionTemplate AND NOT n1:LearningObjective AND NOT n1:StudentModel
          AND NOT n2:QuestionTemplate AND NOT n2:LearningObjective AND NOT n2:StudentModel
        MERGE (n1)-[:DIFFICULTY_PROGRESSION]->(n2)
        """
    ]
    
    try:
        # Execute each query separately
        for query in queries:
            execute_query(query)
        logger.info("Successfully created difficulty progression paths.")
        return True
    except Exception as e:
        logger.error(f"Failed to create difficulty progression paths: {e}")
        return False

def create_community_bridges():
    """
    Identify and mark bridge nodes that connect different communities.
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Identifying and marking community bridges...")
    
    # Find entities that belong to multiple communities and mark them as bridges
    query = """
    MATCH (n)-[:BELONGS_TO_COMMUNITY]->(c:Community)
    WHERE NOT n:Community AND NOT n:Document AND NOT n:Chunk
      AND NOT n:QuestionTemplate AND NOT n:LearningObjective AND NOT n:StudentModel
    WITH n, collect(c.community_id) AS community_ids
    WHERE size(community_ids) > 1
    SET n.is_bridge = true,
        n.bridge_communities = community_ids
    
    // Create COMMUNITY_BRIDGE relationships between communities through bridge nodes
    WITH n, community_ids
    UNWIND community_ids AS community_id1
    UNWIND community_ids AS community_id2
    WITH n, community_id1, community_id2
    WHERE community_id1 < community_id2
    MATCH (c1:Community {community_id: community_id1})
    MATCH (c2:Community {community_id: community_id2})
    MERGE (c1)-[:COMMUNITY_BRIDGE {bridge_node_id: elementId(n)}]->(c2)
    """
    
    try:
        execute_query(query)
        logger.info("Successfully identified and marked community bridges.")
        return True
    except Exception as e:
        logger.error(f"Failed to identify and mark community bridges: {e}")
        return False

def main():
    """Main function to extend the schema for adaptive quizzing."""
    parser = argparse.ArgumentParser(description="Extend Neo4j schema for adaptive quizzing")
    parser.add_argument("--force", action="store_true", help="Force schema creation even if it already exists")
    args = parser.parse_args()
    
    if args.force or not check_educational_metadata_exists():
        # Create the educational schema
        if create_educational_schema():
            # Create question templates
            create_question_templates()
            
            # Create learning objectives
            create_learning_objectives()
            
            # Create difficulty progression paths
            create_difficulty_progression_paths()
            
            # Create community bridges
            create_community_bridges()
            
            logger.info("Schema extension for adaptive quizzing completed successfully.")
        else:
            logger.error("Failed to create educational schema.")
    else:
        logger.info("Educational metadata schema already exists. Use --force to recreate.")

if __name__ == "__main__":
    main()
