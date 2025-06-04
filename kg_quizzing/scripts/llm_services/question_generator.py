"""
Question Generator Module for LLM Services.

This module provides the main LLMQuestionGenerator class for generating questions
using LLMs for the adaptive quizzing system.
"""
import os
import logging
import random
from typing import Dict, List, Any, Optional, Tuple

# Import from llm_services package
from kg_quizzing.scripts.llm_services.openai_client import (
    get_openai_client,
    is_openai_available,
    get_default_model
)
from kg_quizzing.scripts.llm_services.cache_manager import create_question_cache
from kg_quizzing.scripts.llm_services.prompt_templates import (
    QUESTION_SYSTEM_PROMPT,
    generate_question_prompt
)
from kg_quizzing.scripts.llm_services.response_parser import parse_question_response

# Import from quiz_utils
from kg_quizzing.scripts.quiz_utils import (
    execute_query,
    get_entity_by_name,
    get_entity_relationships,
    get_entities_in_community,
    get_available_communities
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LLMQuestionGenerator:
    """Service for LLM-based generation of quiz questions."""
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the LLM question generator.
        
        Args:
            model: The LLM model to use (defaults to the value from environment variables)
        """
        self.model = model or get_default_model()
        self.cache = create_question_cache()
        self.client = get_openai_client()
        
        logger.info(f"Initialized LLM Question Generator with model {self.model}")
    
    def _generate_cache_key(self, question_type: str, entity_name: str, difficulty: int) -> str:
        """
        Generate a cache key for a question request.
        
        Args:
            question_type: The type of question
            entity_name: The entity name
            difficulty: The difficulty level
            
        Returns:
            Cache key string
        """
        return f"{question_type}_{entity_name}_{difficulty}"
    
    def generate_question(self, 
                         question_type: str = "factual", 
                         difficulty: int = 3,
                         entity_data: Optional[Dict[str, Any]] = None,
                         community_id: Optional[int] = None,
                         theme: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a question using an LLM.
        
        Args:
            question_type: Type of question to generate
            difficulty: Target difficulty level (1-10)
            entity_data: Optional entity data to use for the question
            community_id: Optional community ID to use for the question
            theme: Optional theme to filter/select entities
            
        Returns:
            Dictionary containing the generated question
        """
        # If no entity data is provided, get a random entity from the specified community
        if not entity_data:
            if community_id is None:
                # Get a random community
                communities = get_available_communities()
                if not communities:
                    raise ValueError("No communities found in the knowledge graph")
                
                community = random.choice(communities)
                community_id = community["id"]
            
            # Get entities in the community
            entities = get_entities_in_community(community_id)
            if not entities:
                raise ValueError(f"No entities found in community {community_id}")
            
            # Filter entities by theme if provided
            if theme:
                theme_lower = theme.lower()
                themed_entities = [e for e in entities if theme_lower in e.get("name", "").lower() or any(theme_lower in str(v).lower() for v in e.values())]
                if themed_entities:
                    entities = themed_entities
            
            # Select a random entity
            entity = random.choice(entities)
            entity_name = entity["name"]
            
            # Get full entity data
            entity_data = get_entity_by_name(entity_name)
            if not entity_data:
                raise ValueError(f"Entity {entity_name} not found")
        else:
            entity_name = entity_data.get("n", {}).get("name", "Unknown")
        
        # Check if the question is already in the cache
        cache_key = self._generate_cache_key(question_type, entity_name, difficulty)
        if self.cache.has(cache_key):
            logger.info("Using cached question")
            return self.cache.get(cache_key)
        
        # Get entity properties and relationships
        entity_properties = entity_data.get("n", {})
        
        # Handle entity ID - could be in different formats depending on source
        entity_id = None
        if isinstance(entity_properties, dict):
            # Try different possible ID fields
            entity_id = entity_properties.get("id") or entity_properties.get("_id") or entity_properties.get("neo4j_id")
            
            # If we still don't have an ID but have a name, try to get the entity by name
            if not entity_id and "name" in entity_properties:
                entity_name = entity_properties["name"]
                try:
                    full_entity = get_entity_by_name(entity_name)
                    if full_entity and "n" in full_entity:
                        entity_id = full_entity["n"].get("id") or full_entity["n"].get("_id") or full_entity["n"].get("neo4j_id")
                except Exception as e:
                    logger.warning(f"Failed to get entity by name: {e}")
        
        # Get relationships if we have an entity ID
        relationships = []
        if entity_id:
            try:
                relationships = get_entity_relationships(entity_id)
            except Exception as e:
                logger.warning(f"Failed to get relationships: {e}")
        
        # Filter out technical properties
        excluded_properties = [
            "complexity", "is_bridge", "bridge_communities", "id", "community_id",
            "identifier", "community", "belongs_to_community", "community_membership",
            "neo4j_id", "uuid", "internal_id", "chunk_index", "chunk", "embedding", 
            "vector", "index", "position", "offset", "token_count", "chunk_id", 
            "page", "paragraph", "section", "subsection", "url", "source", 
            "reference_id", "external_id", "timestamp", "date_added",
            "last_modified", "version", "status", "flag", "metadata", "data_source"
        ]
        
        filtered_properties = {}
        for prop, value in entity_properties.items():
            if (prop not in excluded_properties and 
                "id" not in prop.lower() and 
                "community" not in prop.lower() and
                value is not None and
                "None" not in str(value)):
                filtered_properties[prop] = value
        
        # Filter out technical relationships
        filtered_relationships = []
        for rel in relationships:
            if (rel["relationship_type"] is not None and 
                rel["related_entity_name"] is not None and
                "None" not in str(rel["relationship_type"]) and
                "None" not in str(rel["related_entity_name"])):
                
                rel_type = rel["relationship_type"].lower()
                if not any(term in rel_type for term in ["id", "community", "identifier", "belongs_to", "member_of"]):
                    filtered_relationships.append(rel)
        
        # Generate the question prompt
        prompt = generate_question_prompt(
            question_type, entity_name, filtered_properties, filtered_relationships, difficulty, theme=theme
        )
        
        # Call the LLM API
        if not is_openai_available() or not self.client:
            logger.error("OpenAI client not available. Cannot generate question.")
            return {
                "question": f"What do you know about {entity_name}?",
                "text": f"What do you know about {entity_name}?",
                "type": question_type,
                "difficulty": difficulty,
                "entity": entity_name,
            }
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Call OpenAI API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": QUESTION_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,  # Slightly higher temperature for more creative responses
                    max_tokens=1200   # Increased token limit for more detailed questions
                )
                # Log raw LLM output for debugging
                logger.info(f"Raw LLM output (attempt {attempt+1}) for '{entity_name}': {response.choices[0].message.content}")
                # Parse the response
                question_text = response.choices[0].message.content
                question = parse_question_response(question_text, question_type, entity_name, difficulty, community_id)

                # Check if the question is valid (non-empty question field, not fallback)
                if question.get("question") and question.get("question").strip() and not question["question"].startswith("What do you know about"):
                    self.cache.set(cache_key, question)
                    return question
                else:
                    logger.warning(f"Attempt {attempt+1}: LLM returned invalid or blank question for '{entity_name}'. Retrying...")
            except Exception as e:
                logger.error(f"Attempt {attempt+1}: Failed to generate question: {e}")
        # Fallback after all retries
        logger.error(f"All {max_retries} attempts failed to generate a valid question for '{entity_name}'. Using fallback.")
        # Use canonical Tolkien MCQ fallback for basic tier, generic fallback otherwise
        if question_type == "multiple_choice" and difficulty <= 3:
            return {
                "question": "Which realm is ruled by Aragorn after the War of the Ring?",
                "text": "Which realm is ruled by Aragorn after the War of the Ring?",
                "type": question_type,
                "difficulty": difficulty,
                "entity": "Aragorn",
                "options": ["Gondor", "Rohan", "Mordor", "The Shire"],
                "answer": "Gondor",
                "correct_answer": "Gondor"
            }
        else:
            return {
                "question": f"What do you know about {entity_name}?",
                "text": f"What do you know about {entity_name}?",
                "type": question_type,
                "difficulty": difficulty,
                "entity": entity_name,
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "answer": "Option 1",
                "correct_answer": "Option 1"
            }


def main():
    """Main function for testing the LLM question generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the LLM question generator")
    parser.add_argument("--entity", type=str, required=True,
                       help="Entity name")
    parser.add_argument("--type", type=str, default="factual",
                       choices=["factual", "relationship", "multiple_choice", "synthesis", "application"],
                       help="Question type")
    parser.add_argument("--difficulty", type=int, default=5,
                       help="Question difficulty (1-10)")
    args = parser.parse_args()
    
    # Create the LLM question generator
    generator = LLMQuestionGenerator()
    
    # Get the entity data
    entity_data = get_entity_by_name(args.entity)
    if not entity_data:
        print(f"Entity {args.entity} not found")
        return
    
    # Generate a question
    question = generator.generate_question(
        question_type=args.type,
        difficulty=args.difficulty,
        entity_data=entity_data
    )
    
    # Print the question
    print(f"\nGenerated Question:")
    print(f"Type: {question['type']}")
    print(f"Difficulty: {question['difficulty']}")
    print(f"\nQuestion: {question['text']}")
    
    if question['type'] == "multiple_choice" and "options" in question:
        print("\nOptions:")
        for i, option in enumerate(question["options"]):
            print(f"{i+1}. {option}")
    
    print(f"\nAnswer: {question.get('answer', question.get('correct_answer', 'No answer provided'))}")


if __name__ == "__main__":
    main()
