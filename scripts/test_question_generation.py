"""
Test script for Tolkien-themed question generation.
This script tests if community-related questions are properly themed.
"""
import sys
import os
from kg_quizzing.scripts.question_generation import generate_question
from kg_quizzing.scripts.quiz_utils import get_available_communities

def test_community_questions():
    """Test if community-related questions use Tolkien-themed language."""
    print("\n" + "="*80)
    print("TESTING TOLKIEN-THEMED COMMUNITY QUESTIONS")
    print("="*80 + "\n")
    
    # Get available communities
    communities = get_available_communities()
    if not communities:
        print("No communities found. Please ensure the database is properly set up.")
        return
    
    # Select the first community for testing
    community_id = communities[0]["id"]
    print(f"Using community ID: {community_id}\n")
    
    # Generate different types of questions
    question_types = ["factual", "relationship", "multiple_choice"]
    
    for q_type in question_types:
        print(f"\n--- Testing {q_type.upper()} questions ---\n")
        
        # Generate a few questions of each type
        for _ in range(3):
            try:
                question = generate_question(q_type, community_id=community_id)
                print(f"Question: {question.get('text', 'No question text')}")
                print(f"Answer: {question.get('answer', 'No answer provided')}")
                print("-" * 50)
            except Exception as e:
                print(f"Error generating {q_type} question: {str(e)}")
                print("-" * 50)

if __name__ == "__main__":
    test_community_questions()
