"""
Test script for the LLM-based question generation in the Tolkien quiz system.
This script demonstrates the new immersive, narrative-driven questions.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))  

# Load environment variables
load_dotenv()

# Import the required modules
# Import the required modules - use direct imports since we're in the same directory
from quiz_session import QuizSession
from llm_question_generation import LLMQuestionGenerator

def test_llm_question_generation():
    """Test the LLM question generation with different question types and topics."""
    print("\n===== TESTING LLM QUESTION GENERATION =====\n")
    
    # Create a question generator
    llm_generator = LLMQuestionGenerator()
    
    # Test topics from Tolkien's world
    test_topics = [
        "Frodo Baggins",
        "The One Ring",
        "Gandalf",
        "Mordor",
        "Rivendell"
    ]
    
    # Test different question types
    question_types = ["factual", "relationship", "multiple_choice", "synthesis", "application"]
    
    # Generate and display questions
    for topic in test_topics:
        print(f"\n----- Questions about {topic} -----\n")
        
        # Try different question types for this topic
        for q_type in question_types:
            print(f"\n* {q_type.upper()} QUESTION:")
            
            try:
                # Generate the question
                question = llm_generator.generate_question(
                    question_type=q_type,
                    difficulty=3,  # Moderate difficulty
                    entity_data={"n": {"name": topic}}  # Simplified entity data
                )
                
                # Display the question
                print(f"Q: {question['text']}")
                print(f"A: {question['answer']}")
                
                # Display options for multiple choice
                if q_type == "multiple_choice" and "options" in question:
                    print("Options:")
                    for i, option in enumerate(question["options"]):
                        print(f"  {chr(65+i)}) {option}")
                
            except Exception as e:
                logger.error(f"Error generating {q_type} question for {topic}: {e}")
                print(f"Error generating question: {e}")
            
            print("\n" + "-"*50)

def test_quiz_session():
    """Test the quiz session with LLM-generated questions."""
    print("\n===== TESTING QUIZ SESSION WITH LLM QUESTIONS =====\n")
    
    # Create a quiz session
    session = QuizSession(
        student_id="test_student_001",
        student_name="Samwise Gamgee"
    )
    
    # Generate 3 questions
    print("Generating 3 questions from the quiz session...\n")
    for i in range(3):
        print(f"\n----- QUESTION {i+1} -----\n")
        
        # Get the next question
        question = session.next_question()
        
        # Display the question
        print(f"Type: {question['type']}")
        print(f"Difficulty: {question['difficulty']}")
        print(f"Entity: {question['entity']}")
        print(f"Q: {question['text']}")
        
        # Display options for multiple choice
        if question['type'] == "multiple_choice" and "options" in question:
            print("\nOptions:")
            for i, option in enumerate(question["options"]):
                print(f"  {chr(65+i)}) {option}")
        
        print("\n" + "-"*50)

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("Please set it in your .env file or environment variables.")
        sys.exit(1)
    
    # Run the tests
    try:
        # Test individual question generation
        test_llm_question_generation()
        
        # Test the quiz session
        test_quiz_session()
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"Test failed: {e}")
