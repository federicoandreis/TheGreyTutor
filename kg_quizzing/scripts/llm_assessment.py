"""
LLM Assessment Service for Adaptive Quizzing.

This module provides LLM-based assessment of student answers for the adaptive quizzing system,
providing detailed feedback in the voice of Gandalf.

This is a compatibility wrapper around the new modular LLM services.
"""
import os
import logging
from typing import Dict, List, Any, Optional, Tuple

# Import from the new modular structure
from kg_quizzing.scripts.llm_services.assessment_service import LLMAssessmentService
from kg_quizzing.scripts.llm_services.openai_client import is_openai_available, get_default_model

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure OpenAI API
DEFAULT_MODEL = get_default_model()
OPENAI_AVAILABLE = is_openai_available()

# Create a global instance of the assessment service for backward compatibility
_assessment_service = LLMAssessmentService()


def assess_answer(question: Dict[str, Any], answer: str) -> Tuple[bool, int, Dict[str, Any]]:
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
    return _assessment_service.assess_answer(question, answer)


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
    
    # Create a question dictionary
    question = {
        "text": args.question,
        "type": args.type,
        "difficulty": args.difficulty
    }
    
    if args.correct_answer:
        question["answer"] = args.correct_answer
    
    # Assess the answer
    correct, quality_score, assessment_details = assess_answer(question, args.answer)
    
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
