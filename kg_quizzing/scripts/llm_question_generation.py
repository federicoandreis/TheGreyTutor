"""
LLM Question Generation Service for Adaptive Quizzing.

This module provides LLM-based generation of questions for the adaptive quizzing system,
creating more natural, contextually appropriate, and immersive Tolkien-themed questions.

This is a compatibility wrapper around the new modular LLM services.
"""
import os
import logging
from typing import Dict, List, Any, Optional, Tuple

# Import from the new modular structure
from llm_services.question_generator import LLMQuestionGenerator
from llm_services.openai_client import is_openai_available, get_default_model

# Import from quiz_utils for backward compatibility
from quiz_utils import (
    execute_query,
    get_entity_by_name,
    get_entity_relationships,
    get_entities_in_community
)

from question_generation import (
    get_available_communities
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure OpenAI API
DEFAULT_MODEL = get_default_model()
OPENAI_AVAILABLE = is_openai_available()

# Create a global instance of the question generator for backward compatibility
_question_generator = LLMQuestionGenerator()


def generate_question(
    question_type: str = "factual", 
    difficulty: int = 3,
    entity_data: Optional[Dict[str, Any]] = None,
    community_id: Optional[int] = None,
    theme: Optional[str] = None
) -> Dict[str, Any]:
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
    return _question_generator.generate_question(
        question_type=question_type,
        difficulty=difficulty,
        entity_data=entity_data,
        community_id=community_id,
        theme=theme
    )


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
    
    # Get the entity data
    entity_data = get_entity_by_name(args.entity)
    if not entity_data:
        print(f"Entity {args.entity} not found")
        return
    
    # Generate a question
    question = generate_question(
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
