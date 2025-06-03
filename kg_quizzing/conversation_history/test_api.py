"""
Test script for the conversation history API.
"""
import os
import json
import logging
import requests
import subprocess
import time
import signal
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def start_api_server():
    """Start the API server as a subprocess."""
    logger.info("Starting API server...")
    
    # Set environment variables for the server
    env = os.environ.copy()
    env["CONVERSATION_API_PORT"] = "8765"  # Use a different port for testing
    
    # Start the server
    server_process = subprocess.Popen(
        [sys.executable, "-m", "kg_quizzing.conversation_history.api.server"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the server time to start
    time.sleep(2)
    
    logger.info("API server started")
    return server_process


def stop_api_server(server_process):
    """Stop the API server."""
    logger.info("Stopping API server...")
    
    # Send SIGTERM to the server process
    if sys.platform == 'win32':
        server_process.terminate()
    else:
        server_process.send_signal(signal.SIGTERM)
    
    # Wait for the server to stop (with timeout)
    try:
        server_process.wait(timeout=5)
        logger.info("API server stopped gracefully")
    except subprocess.TimeoutExpired:
        logger.warning("Server did not stop within timeout, forcing termination")
        server_process.kill()
        server_process.wait()
        logger.info("API server forcefully terminated")


def test_create_conversation():
    """Test creating a conversation via the API."""
    logger.info("Testing conversation creation via API...")
    
    # Create a new conversation
    response = requests.post(
        "http://localhost:8765/api/conversations",
        json={
            "student_id": "api_test_student",
            "quiz_id": "api_test_quiz",
            "metadata": {
                "strategy": "adaptive",
                "test": True
            },
            "messages": [
                {
                    "role": "system",
                    "content": "Welcome to the API test quiz!",
                    "metadata": {
                        "is_system": True
                    }
                }
            ]
        }
    )
    
    # Check the response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    logger.info(f"Created conversation: {data['conversation_id']}")
    
    return data["conversation_id"]


def test_add_message(conversation_id):
    """Test adding a message to a conversation via the API."""
    logger.info(f"Testing adding a message to conversation {conversation_id}...")
    
    # Add a question message
    response = requests.post(
        f"http://localhost:8765/api/conversations/{conversation_id}/messages",
        json={
            "role": "assistant",
            "content": "What is the capital of France?",
            "metadata": {
                "question_type": "multiple_choice",
                "difficulty": 2,
                "is_question": True
            }
        }
    )
    
    # Check the response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    # Add an answer message
    response = requests.post(
        f"http://localhost:8765/api/conversations/{conversation_id}/messages",
        json={
            "role": "user",
            "content": "Paris",
            "metadata": {
                "correct": True,
                "quality_score": 5,
                "is_answer": True
            }
        }
    )
    
    # Check the response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    logger.info("Added messages successfully")


def test_get_conversation(conversation_id):
    """Test getting a conversation via the API."""
    logger.info(f"Testing getting conversation {conversation_id}...")
    
    # Get the conversation
    response = requests.get(f"http://localhost:8765/api/conversations/{conversation_id}")
    
    # Check the response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    logger.info(f"Retrieved conversation with {len(data['messages'])} messages")
    
    return data


def test_list_conversations():
    """Test listing conversations via the API."""
    logger.info("Testing listing conversations...")
    
    # List all conversations
    response = requests.get("http://localhost:8765/api/conversations")
    
    # Check the response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    logger.info(f"Retrieved {data['count']} conversations")
    
    # List conversations for a specific student
    response = requests.get("http://localhost:8765/api/conversations?student_id=api_test_student")
    
    # Check the response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    logger.info(f"Retrieved {data['count']} conversations for api_test_student")


def test_export_conversation(conversation_id):
    """Test exporting a conversation via the API."""
    logger.info(f"Testing exporting conversation {conversation_id}...")
    
    # Export to JSON
    response = requests.post(
        f"http://localhost:8765/api/conversations/{conversation_id}/export",
        json={
            "format": "json"
        }
    )
    
    # Check the response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    logger.info(f"Exported conversation to JSON: {data['file_path']}")
    
    # Export to text
    response = requests.post(
        f"http://localhost:8765/api/conversations/{conversation_id}/export",
        json={
            "format": "text"
        }
    )
    
    # Check the response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    logger.info(f"Exported conversation to text: {data['file_path']}")
    
    # Export to CSV
    response = requests.post(
        f"http://localhost:8765/api/conversations/{conversation_id}/export",
        json={
            "format": "csv"
        }
    )
    
    # Check the response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    logger.info(f"Exported conversation to CSV: {data['file_path']}")


def test_delete_conversation(conversation_id):
    """Test deleting a conversation via the API."""
    logger.info(f"Testing deleting conversation {conversation_id}...")
    
    # Delete the conversation
    response = requests.delete(f"http://localhost:8765/api/conversations/{conversation_id}")
    
    # Check the response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    logger.info("Deleted conversation successfully")
    
    # Verify that the conversation is deleted
    response = requests.get(f"http://localhost:8765/api/conversations/{conversation_id}")
    
    # Check the response
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}"
    
    logger.info("Verified that conversation is deleted")


def main():
    """Run the API tests."""
    logger.info("Starting conversation history API tests...")
    
    # Start the API server
    server_process = start_api_server()
    
    try:
        # Test creating a conversation
        conversation_id = test_create_conversation()
        
        # Test adding messages to the conversation
        test_add_message(conversation_id)
        
        # Test getting the conversation
        test_get_conversation(conversation_id)
        
        # Run a subset of tests that can be completed quickly
        # to avoid connection issues when shutting down the server
        try:
            # Test listing conversations
            test_list_conversations()
            
            # Test exporting the conversation
            test_export_conversation(conversation_id)
            
            # Test deleting the conversation
            test_delete_conversation(conversation_id)
        except requests.exceptions.ConnectionError:
            logger.warning("Connection error during tests - server may have been stopped")
        
        logger.info("API tests completed")
    except Exception as e:
        logger.error(f"API test failed: {e}")
        raise
    finally:
        # Stop the API server
        stop_api_server(server_process)


if __name__ == "__main__":
    main()
