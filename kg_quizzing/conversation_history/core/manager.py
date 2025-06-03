"""
Manager class for conversation history.
"""
import os
import json
import logging
from typing import Dict, List, Any
from datetime import datetime

from .conversation import QuizConversation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConversationHistoryManager:
    """Manager for storing and retrieving conversation history."""
    
    def __init__(self, storage_dir: str = "conversation_history/data"):
        """
        Initialize the conversation history manager.
        
        Args:
            storage_dir: Directory to store conversation history
        """
        self.storage_dir = storage_dir
        
        # Create the storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        logger.info(f"Initialized ConversationHistoryManager with storage directory: {storage_dir}")
    
    def save_conversation(self, conversation: QuizConversation) -> str:
        """
        Save a conversation to storage.
        
        Args:
            conversation: The conversation to save
            
        Returns:
            Path to the saved conversation file
        """
        # Create student directory if it doesn't exist
        student_dir = os.path.join(self.storage_dir, conversation.student_id or "anonymous")
        os.makedirs(student_dir, exist_ok=True)
        
        # Generate filename based on conversation ID and timestamp
        timestamp = datetime.fromtimestamp(conversation.start_time).strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{conversation.conversation_id}_{timestamp}.json"
        
        # Save the conversation
        file_path = os.path.join(student_dir, filename)
        with open(file_path, 'w') as f:
            json.dump(conversation.to_dict(), f, indent=2, default=str)
        
        logger.info(f"Saved conversation {conversation.conversation_id} to {file_path}")
        
        return file_path
    
    def load_conversation(self, file_path: str) -> QuizConversation:
        """
        Load a conversation from storage.
        
        Args:
            file_path: Path to the conversation file
            
        Returns:
            QuizConversation instance
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        conversation = QuizConversation.from_dict(data)
        
        logger.info(f"Loaded conversation {conversation.conversation_id} from {file_path}")
        
        return conversation
    
    def get_conversations_for_student(self, student_id: str) -> List[str]:
        """
        Get all conversation files for a student.
        
        Args:
            student_id: The student ID
            
        Returns:
            List of file paths to conversations
        """
        student_dir = os.path.join(self.storage_dir, student_id)
        
        if not os.path.exists(student_dir):
            return []
        
        # Get all JSON files in the student directory
        files = [
            os.path.join(student_dir, f) 
            for f in os.listdir(student_dir) 
            if f.endswith('.json')
        ]
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        return files
    
    def get_all_conversations(self) -> List[str]:
        """
        Get all conversation files.
        
        Returns:
            List of file paths to conversations
        """
        all_files = []
        
        # Walk through all subdirectories
        for root, _, files in os.walk(self.storage_dir):
            for file in files:
                if file.endswith('.json'):
                    all_files.append(os.path.join(root, file))
        
        # Sort by modification time (newest first)
        all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        return all_files
    
    def delete_conversation(self, file_path: str) -> bool:
        """
        Delete a conversation file.
        
        Args:
            file_path: Path to the conversation file
            
        Returns:
            True if the file was deleted, False otherwise
        """
        try:
            os.remove(file_path)
            logger.info(f"Deleted conversation file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete conversation file {file_path}: {e}")
            return False
