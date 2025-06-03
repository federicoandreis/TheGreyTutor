"""
LLM Assessment Service for Adaptive Quizzing.

This module provides LLM-based assessment of student answers, particularly
for open-ended questions like synthesis and application questions.
"""
import os
import logging
import argparse
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# LLM API integration
try:
    import openai
    load_dotenv()
    OPENAI_AVAILABLE = True
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("OpenAI client initialized successfully")
except ImportError as e:
    logger.warning(f"OpenAI package or dotenv not found: {e}. LLM features will not work.")
    OPENAI_AVAILABLE = False
except Exception as e:
    logger.warning(f"Error initializing OpenAI client: {e}. LLM features will not work.")
    OPENAI_AVAILABLE = False

from kg_quizzing.scripts.quiz_utils import (
    execute_query,
    get_entity_by_name
)

# Load environment variables
load_dotenv()

# Configure OpenAI API
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4")


class LLMAssessmentService:
    """Service for LLM-based assessment of student answers."""
    
    def __init__(self, model: str = DEFAULT_MODEL, cache_dir: str = "assessment_cache", fussiness: int = 3):
        """
        Initialize the LLM assessment service.
        
        Args:
            model: The LLM model to use
            cache_dir: Directory to store assessment cache
            fussiness: Gandalf's fussiness (1=very lenient, 10=very strict)
        """
        self.model = model
        self.cache_dir = cache_dir
        self.fussiness = fussiness
        
        # Create the cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load the assessment cache
        self.cache = self._load_cache()
        
        logger.info(f"Initialized LLM Assessment Service with model {model}, fussiness={fussiness}")
    
    def _load_cache(self) -> Dict[str, Any]:
        """
        Load the assessment cache from disk.
        
        Returns:
            Dictionary containing the assessment cache
        """
        cache_path = os.path.join(self.cache_dir, "assessment_cache.json")
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load assessment cache: {e}")
        
        return {}
    
    def _save_cache(self):
        """Save the assessment cache to disk."""
        cache_path = os.path.join(self.cache_dir, "assessment_cache.json")
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save assessment cache: {e}")
    
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
        if cache_key in self.cache:
            logger.info("Using cached assessment")
            return self.cache[cache_key]
        
        # Get the question type
        question_type = question.get("type", "unknown")
        
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
        prompt = self._generate_assessment_prompt(
            question_type, question["question"], answer, correct_answer, difficulty, entity_info
        )
        
        # Call the LLM API
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI client not available. Cannot assess answer.")
            return False, 0, {"error": "OpenAI client not available"}
            
        try:
            # Call OpenAI API using the global client
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Gandalf the Grey, a wise wizard from Middle-earth with extensive knowledge of Tolkien's legendarium. You are evaluating a student's understanding of Middle-earth lore."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            # Parse the response
            assessment_text = response.choices[0].message.content
            assessment = self._parse_assessment_response(assessment_text)
            
            # Cache the assessment
            self.cache[cache_key] = assessment
            self._save_cache()
            
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
    
    def _generate_assessment_prompt(self, question_type: str, question_text: str, 
                                  student_answer: str, correct_answer: str, 
                                  difficulty: int, entity_info: Dict[str, Any]) -> str:
        """
        Generate a prompt for the LLM to assess a student's answer.
        
        Args:
            question_type: The type of question
            question_text: The text of the question
            student_answer: The student's answer
            correct_answer: The correct answer (if available)
            difficulty: The difficulty level of the question
            entity_info: Information about entities mentioned in the question
            
        Returns:
            Prompt string for the LLM
        """
        prompt = f"""
Please assess the following student answer to a {question_type} question.

Question: {question_text}
Difficulty Level (1-10): {difficulty}

"""
        
        if correct_answer:
            prompt += f"Reference Answer: {correct_answer}\n\n"
        
        if entity_info:
            prompt += "Entity Information:\n"
            def _safe_json(obj):
                # Try to convert Neo4j Node or other objects to dict, else string
                try:
                    if hasattr(obj, 'items'):
                        return dict(obj)
                    elif hasattr(obj, '__dict__'):
                        return obj.__dict__
                    else:
                        return str(obj)
                except Exception:
                    return str(obj)

            for entity_key, entity_data in entity_info.items():
                prompt += f"- {entity_key}: {json.dumps(entity_data, default=_safe_json, indent=2)}\n"
            prompt += "\n"
        
        prompt += f"""
Student Answer: {student_answer}

Instructions for Gandalf:
- Always address the student directly (use 'you') as Gandalf would.
- Use Tolkien-themed encouragement or correction in your feedback.
- Do NOT write a generic essay or third-person analysis—speak to the student about their answer.
- Keep your feedback concise, clear, and in-character as Gandalf.

Please provide a comprehensive and educational assessment with the following components:
1. Is the answer correct? (Yes/No)
2. Quality score (0-100)
3. Explanation of your assessment. If the student's answer is incorrect or incomplete, ALWAYS state the correct answer explicitly and provide a brief educational explanation or lore/context about it, as Gandalf would. The explanation should be constructive, informative, and in the spirit of Tolkien's world.
4. Strengths of the answer
5. Weaknesses of the answer
6. Suggestions for improvement

Format your response as a JSON object with the following structure:
{{
  "correct": true/false,
  "quality_score": 0-100,
  "explanation": "Your explanation here. If the answer is incorrect, always reveal the correct answer and provide a brief lore/context.",
  "strengths": ["Strength 1", "Strength 2", ...],
  "weaknesses": ["Weakness 1", "Weakness 2", ...],
  "suggestions": ["Suggestion 1", "Suggestion 2", ...]
}}
"""
        
        return prompt
    
    def _parse_assessment_response(self, response_text: str) -> Tuple[bool, int, Dict[str, Any]]:
        """
        Parse the LLM's response to an assessment prompt.
        
        Args:
            response_text: The LLM's response text
            
        Returns:
            Tuple of (correct, quality_score, assessment_details)
            correct: Whether the answer was correct
            quality_score: Quality score for the answer (0-100)
            assessment_details: Dictionary containing detailed assessment information
        """
        try:
            # Extract the JSON object from the response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON object found in the response")
            
            json_str = response_text[json_start:json_end]
            assessment = json.loads(json_str)
            
            # Extract the assessment components
            correct = assessment.get("correct", False)
            quality_score = assessment.get("quality_score", 0)
            
            # Ensure quality score is within range
            quality_score = max(0, min(100, quality_score))
            
            # Extract the assessment details
            assessment_details = {
                "explanation": assessment.get("explanation", ""),
                "strengths": assessment.get("strengths", []),
                "weaknesses": assessment.get("weaknesses", []),
                "suggestions": assessment.get("suggestions", [])
            }
            
            return correct, quality_score, assessment_details
        
        except Exception as e:
            logger.error(f"Failed to parse assessment response: {e}")
            logger.debug(f"Response text: {response_text}")
            
            # Try to extract information from the text directly
            correct = "yes" in response_text.lower() and "correct" in response_text.lower()
            
            # Try to extract a quality score
            quality_score = 0
            try:
                import re
                score_match = re.search(r"quality score:?\s*(\d+)", response_text, re.IGNORECASE)
                if score_match:
                    quality_score = int(score_match.group(1))
                    quality_score = max(0, min(100, quality_score))
            except:
                pass
            
            # Return a basic assessment
            return correct, quality_score, {
                "explanation": "The assessment could not be parsed correctly.",
                "strengths": [],
                "weaknesses": [],
                "suggestions": ["Please provide a more detailed answer."]
            }


def main():
    """Main function for testing the LLM assessment service."""
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
