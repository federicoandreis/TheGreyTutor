"""
Assessment Service Module for LLM Services.

This module provides the main LLMAssessmentService class for assessing student answers
using LLMs for the adaptive quizzing system.
"""
import os
import logging
import json
from typing import Dict, List, Any, Optional, Tuple

# Import from llm_services package
from kg_quizzing.scripts.llm_services.openai_client import (
    get_openai_client,
    is_openai_available,
    get_default_model
)
from kg_quizzing.scripts.llm_services.cache_manager import create_assessment_cache
from kg_quizzing.scripts.llm_services.prompt_templates import (
    ASSESSMENT_SYSTEM_PROMPT,
    generate_assessment_prompt
)
from kg_quizzing.scripts.llm_services.response_parser import parse_assessment_response

# Import from quiz_utils
from kg_quizzing.scripts.quiz_utils import (
    execute_query,
    get_entity_by_name
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LLMAssessmentService:
    """Service for LLM-based assessment of student answers."""
    
    def __init__(self, model: Optional[str] = None, fussiness: int = 3):
        """
        Initialize the LLM assessment service.
        
        Args:
            model: The LLM model to use (defaults to the value from environment variables)
            fussiness: Gandalf's fussiness (1=very lenient, 10=very strict)
        """
        self.model = model or get_default_model()
        self.fussiness = fussiness
        self.cache = create_assessment_cache()
        self.client = get_openai_client()
        
        logger.info(f"Initialized LLM Assessment Service with model {self.model}, fussiness={fussiness}")
    
    def _generate_cache_key(self, question: Dict[str, Any], answer: str) -> str:
        """
        Generate a cache key for a question-answer pair.
        
        Args:
            question: The question dictionary
            answer: The student's answer
            
        Returns:
            Cache key string
        """
        # Use the question text and answer to generate a cache key
        question_text = question.get("text", "")
        return f"{hash(question_text)}_{hash(answer)}"
    
    def assess_answer(self, question: Dict[str, Any], answer: str) -> Tuple[bool, int, Dict[str, Any]]:
        """
        Assess a student's answer to a question using an LLM.
        
        Args:
            question: The question dictionary
            answer: The student's answer
            
        Returns:
            Tuple of (correct, quality_score, assessment_details)
            correct: Whether the answer was correct
            quality_score: Quality score for the answer (0-100)
            assessment_details: Dictionary containing detailed assessment information
        """
        # Check if the assessment is already in the cache
        cache_key = self._generate_cache_key(question, answer)
        if self.cache.has(cache_key):
            logger.info("Using cached assessment")
            return self.cache.get(cache_key)
        
        # Get the question type
        question_type = question.get("type", "unknown")
        
        # Get the question text
        question_text = question.get("text", question.get("question", ""))
        
        # Get the correct answer if available
        correct_answer = question.get("answer", question.get("correct_answer", ""))
        
        # Get the question difficulty
        difficulty = question.get("difficulty", 5)
        
        # Get the entity information if available
        entity_info = {}
        for entity_key in ["entity", "entity1", "entity2"]:
            if entity_key in question:
                entity_name = question[entity_key]
                entity_data = get_entity_by_name(entity_name)
                if entity_data:
                    entity_info[entity_key] = entity_data
        
        # Generate the assessment prompt
        prompt = generate_assessment_prompt(
            question_type, question_text, answer, correct_answer, difficulty, entity_info
        )
        
        # Call the LLM API
        if not is_openai_available() or not self.client:
            logger.error("OpenAI client not available. Cannot assess answer.")
            return False, 0, {"error": "OpenAI client not available"}
            
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ASSESSMENT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            # Parse the response
            assessment_text = response.choices[0].message.content
            assessment = parse_assessment_response(assessment_text)
            
            # Cache the assessment
            self.cache.set(cache_key, assessment)
            
            return assessment
        
        except Exception as e:
            logger.error(f"Failed to assess answer: {e}")
            # Return a default assessment
            return False, 0, {
                "explanation": "Failed to assess answer due to an error.",
                "strengths": [],
                "weaknesses": [],
                "suggestions": ["Please try again later."]
            }


def main():
    """Main function for testing the LLM assessment service."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the LLM assessment service")
    parser.add_argument("--question", type=str, required=True,
                       help="Question text")
    parser.add_argument("--answer", type=str, required=True,
                       help="Student's answer")
    parser.add_argument("--type", type=str, default="synthesis",
                       choices=["factual", "relationship", "multiple_choice", "synthesis", "application"],
                       help="Question type")
    parser.add_argument("--difficulty", type=int, default=5,
                       help="Question difficulty (1-10)")
    parser.add_argument("--correct-answer", type=str, default="",
                       help="Correct answer (if available)")
    args = parser.parse_args()
    
    # Create the LLM assessment service
    service = LLMAssessmentService()
    
    # Create a question dictionary
    question = {
        "text": args.question,
        "type": args.type,
        "difficulty": args.difficulty
    }
    
    if args.correct_answer:
        question["answer"] = args.correct_answer
    
    # Assess the answer
    correct, quality_score, assessment_details = service.assess_answer(question, args.answer)
    
    # Print the assessment
    print(f"\nAssessment Results:")
    print(f"Correct: {correct}")
    print(f"Quality Score: {quality_score}/100")
    print(f"\nExplanation: {assessment_details['explanation']}")
    
    print("\nStrengths:")
    for strength in assessment_details["strengths"]:
        print(f"- {strength}")
    
    print("\nWeaknesses:")
    for weakness in assessment_details["weaknesses"]:
        print(f"- {weakness}")
    
    print("\nSuggestions:")
    for suggestion in assessment_details["suggestions"]:
        print(f"- {suggestion}")


if __name__ == "__main__":
    main()
