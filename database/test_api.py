"""
Test script for The Grey Tutor database API.

This script tests the database API functions.
"""
import logging
import json
from database.api import DatabaseAPI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_api() -> None:
    """Test the database API."""
    try:
        # Initialize API
        api = DatabaseAPI()
        
        # Test user methods
        username = "test_api_user"
        logger.info(f"Testing user methods with username: {username}")
        
        # Get user (should not exist yet)
        user = api.get_user(username)
        logger.info(f"User exists: {user is not None}")
        
        if user is None:
            # Create user via CLI (this is just for testing)
            import subprocess
            import sys
            
            logger.info(f"Creating user {username} via CLI...")
            subprocess.run([
                sys.executable, "-m", "database.cli", "create-user", 
                username, "--password", "password", "--role", "user"
            ])
            
            # Get user again
            user = api.get_user(username)
            logger.info(f"User created: {user is not None}")
            
            if user:
                logger.info(f"User data: {json.dumps(user, indent=2)}")
        
        # Get user profile
        profile = api.get_user_profile(username)
        logger.info(f"User profile exists: {profile is not None}")
        
        if profile:
            logger.info(f"User profile data: {json.dumps(profile, indent=2)}")
            
            # Update user profile
            logger.info("Updating user profile...")
            updated = api.update_user_profile(username, {
                "overall_mastery": 0.5,
                "current_objective": "Test objective"
            })
            logger.info(f"Profile updated: {updated}")
            
            # Get updated profile
            profile = api.get_user_profile(username)
            logger.info(f"Updated profile data: {json.dumps(profile, indent=2)}")
        
        # Test session methods
        logger.info("Testing session methods...")
        
        # Create session
        session = api.create_session(username, {
            "session_type": "test",
            "strategy": "test_strategy",
            "theme": "test_theme",
            "fussiness": 3,
            "tier": "basic",
            "use_llm": True,
            "parameters": {"test_param": "test_value"}
        })
        
        if session:
            logger.info(f"Session created: {json.dumps(session, indent=2)}")
            session_id = session["id"]
            
            # Test conversation methods
            logger.info("Testing conversation methods...")
            
            # Create conversation
            conversation = api.create_conversation(
                username,
                {
                    "conversation_type": "test",
                    "session_id": session_id,
                    "metadata": {"test_meta": "test_value"}
                },
                {
                    "parameter_type": "test",
                    "max_communities": 5,
                    "max_path_length": 3,
                    "use_cache": True,
                    "verbose": False,
                    "llm_model": "test_model",
                    "temperature": 0.7
                }
            )
            
            if conversation:
                logger.info(f"Conversation created: {json.dumps(conversation, indent=2)}")
                conversation_id = conversation["id"]
                
                # Add messages
                logger.info("Adding messages...")
                
                # Add assistant message
                assistant_message = api.add_message(conversation_id, {
                    "role": "assistant",
                    "content": "This is a test assistant message.",
                    "metadata": {"test_meta": "test_value"}
                })
                
                if assistant_message:
                    logger.info(f"Assistant message added: {json.dumps(assistant_message, indent=2)}")
                    assistant_message_id = assistant_message["id"]
                    
                    # Add question
                    question = api.add_question(assistant_message_id, {
                        "type": "multiple_choice",
                        "difficulty": 2,
                        "entity": "test_entity",
                        "tier": "basic",
                        "options": ["Option 1", "Option 2", "Option 3"],
                        "correct_answer": "Option 2",
                        "community_id": "test_community",
                        "metadata": {"test_meta": "test_value"}
                    })
                    
                    if question:
                        logger.info(f"Question added: {json.dumps(question, indent=2)}")
                        question_id = question["id"]
                
                # Add user message
                user_message = api.add_message(conversation_id, {
                    "role": "user",
                    "content": "This is a test user message.",
                    "metadata": {"test_meta": "test_value"}
                })
                
                if user_message:
                    logger.info(f"User message added: {json.dumps(user_message, indent=2)}")
                    user_message_id = user_message["id"]
                    
                    # Add answer
                    if 'question_id' in locals():
                        answer = api.add_answer(user_message_id, {
                            "question_id": question_id,
                            "content": "Option 2",
                            "correct": True,
                            "quality_score": 0.9,
                            "feedback": {"comment": "Good answer!"}
                        })
                        
                        if answer:
                            logger.info(f"Answer added: {json.dumps(answer, indent=2)}")
                
                # End conversation
                logger.info("Ending conversation...")
                conversation_ended = api.end_conversation(conversation_id)
                logger.info(f"Conversation ended: {conversation_ended}")
            
            # End session
            logger.info("Ending session...")
            session_ended = api.end_session(session_id, {
                "questions_asked": 1,
                "correct_answers": 1,
                "accuracy": 1.0,
                "mastery_before": 0.5,
                "mastery_after": 0.6
            })
            logger.info(f"Session ended: {session_ended}")
        
        # Test cache methods
        logger.info("Testing cache methods...")
        
        # Set cache
        cache_type = "test_cache"
        cache_key = "test_key"
        cache_value = {"test_data": "test_value", "numbers": [1, 2, 3]}
        
        cache_entry = api.set_cache(cache_type, cache_key, cache_value)
        if cache_entry:
            logger.info(f"Cache entry set: {json.dumps(cache_entry, indent=2)}")
            
            # Get cache
            retrieved_entry = api.get_cache(cache_type, cache_key)
            if retrieved_entry:
                logger.info(f"Cache entry retrieved: {json.dumps(retrieved_entry, indent=2)}")
                
                # Delete cache
                deleted = api.delete_cache(cache_type, cache_key)
                logger.info(f"Cache entry deleted: {deleted}")
        
        # Close API session
        api.close()
        logger.info("API test completed successfully!")
        
    except Exception as e:
        logger.error(f"API test failed: {e}")


if __name__ == "__main__":
    test_api()
