"""
Test script for the conversation history module.
"""
import os
import logging
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import conversation history components
from kg_quizzing.conversation_history.core import ConversationMessage, QuizConversation, ConversationHistoryManager
from kg_quizzing.conversation_history.exporters import ConversationExporter


def test_conversation_creation():
    """Test creating and saving a conversation."""
    logger.info("Testing conversation creation...")
    
    # Create a test storage directory
    test_dir = os.path.join("conversation_history", "test_data")
    os.makedirs(test_dir, exist_ok=True)
    
    # Initialize the conversation history manager
    manager = ConversationHistoryManager(test_dir)
    
    # Create a new conversation
    conversation = QuizConversation(
        student_id="test_student",
        quiz_id="test_quiz",
        metadata={"strategy": "adaptive", "test": True}
    )
    
    # Add some messages
    conversation.add_system_message("Welcome to the test quiz!")
    
    # Add a question
    conversation.add_question({
        "id": "q1",
        "text": "What is the capital of France?",
        "type": "multiple_choice",
        "difficulty": 2,
        "community_id": 1,
        "options": ["London", "Paris", "Berlin", "Madrid"]
    })
    
    # Add an answer
    conversation.add_answer("Paris", True, 5, {"explanation": "Correct answer!"})
    
    # Add feedback
    conversation.add_feedback({
        "message": "Great job!",
        "explanation": "Paris is indeed the capital of France.",
        "correct": True,
        "quality_score": 5,
        "next_steps": ["Continue to the next question"]
    })
    
    # End the conversation
    conversation.end_conversation()
    
    # Save the conversation
    file_path = manager.save_conversation(conversation)
    logger.info(f"Saved conversation to {file_path}")
    
    return conversation, file_path


def test_conversation_loading(file_path):
    """Test loading a conversation from a file."""
    logger.info("Testing conversation loading...")
    
    # Initialize the conversation history manager
    test_dir = os.path.join("conversation_history", "test_data")
    manager = ConversationHistoryManager(test_dir)
    
    # Load the conversation
    loaded_conversation = manager.load_conversation(file_path)
    
    # Print conversation details
    logger.info(f"Loaded conversation: {loaded_conversation.conversation_id}")
    logger.info(f"Student ID: {loaded_conversation.student_id}")
    logger.info(f"Quiz ID: {loaded_conversation.quiz_id}")
    logger.info(f"Start time: {datetime.fromtimestamp(loaded_conversation.start_time).isoformat()}")
    logger.info(f"End time: {datetime.fromtimestamp(loaded_conversation.end_time).isoformat()}")
    logger.info(f"Number of messages: {len(loaded_conversation.messages)}")
    
    return loaded_conversation


def test_conversation_export(conversation):
    """Test exporting a conversation in different formats."""
    logger.info("Testing conversation export...")
    
    # Create a test export directory
    export_dir = os.path.join("conversation_history", "test_exports")
    os.makedirs(export_dir, exist_ok=True)
    
    # Initialize the conversation exporter
    exporter = ConversationExporter()
    
    # Export to JSON
    json_path = os.path.join(export_dir, f"test_conversation_{int(time.time())}.json")
    exporter.export_to_json(conversation, json_path)
    logger.info(f"Exported conversation to JSON: {json_path}")
    
    # Export to text
    text_path = os.path.join(export_dir, f"test_conversation_{int(time.time())}.txt")
    exporter.export_to_text(conversation, text_path)
    logger.info(f"Exported conversation to text: {text_path}")
    
    # Export to CSV
    csv_path = os.path.join(export_dir, f"test_conversation_{int(time.time())}.csv")
    exporter.export_to_csv(conversation, csv_path)
    logger.info(f"Exported conversation to CSV: {csv_path}")


def test_conversation_listing():
    """Test listing conversations."""
    logger.info("Testing conversation listing...")
    
    # Initialize the conversation history manager
    test_dir = os.path.join("conversation_history", "test_data")
    manager = ConversationHistoryManager(test_dir)
    
    # Get all conversations for the test student
    conversation_files = manager.get_conversations_for_student("test_student")
    logger.info(f"Found {len(conversation_files)} conversations for test_student")
    
    # Get all conversations
    all_conversation_files = manager.get_all_conversations()
    logger.info(f"Found {len(all_conversation_files)} conversations in total")


def main():
    """Run the tests."""
    logger.info("Starting conversation history tests...")
    
    # Test conversation creation and saving
    conversation, file_path = test_conversation_creation()
    
    # Test conversation loading
    loaded_conversation = test_conversation_loading(file_path)
    
    # Test conversation export
    test_conversation_export(loaded_conversation)
    
    # Test conversation listing
    test_conversation_listing()
    
    logger.info("All tests completed successfully!")


if __name__ == "__main__":
    main()
