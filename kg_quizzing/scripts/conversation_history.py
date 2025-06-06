"""
Conversation History Module for Adaptive Quizzing.

This module provides functionality for storing and retrieving conversation history
from quiz sessions, including questions, answers, and feedback.
"""
import os
import logging
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if database should be used
USE_DATABASE = os.getenv("USE_DATABASE", "false").lower() in ("true", "1", "yes")

class ConversationMessage:
    """Class representing a message in a conversation."""
    
    def __init__(self, 
                role: str, 
                content: str, 
                timestamp: Optional[float] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a conversation message.
        
        Args:
            role: The role of the message sender (e.g., "system", "user", "assistant")
            content: The content of the message
            timestamp: Optional timestamp for the message (defaults to current time)
            metadata: Optional metadata for the message
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.metadata = metadata if metadata is not None else {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.
        
        Returns:
            Dictionary representation of the message
        """
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "timestamp_formatted": datetime.fromtimestamp(self.timestamp).isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """
        Create a message from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            ConversationMessage instance
        """
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {})
        )


class QuizConversation:
    """Class representing a conversation in a quiz session."""
    
    def __init__(self, 
                conversation_id: Optional[str] = None,
                student_id: Optional[str] = None,
                quiz_id: Optional[str] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a quiz conversation.
        
        Args:
            conversation_id: Optional unique identifier for the conversation
            student_id: Optional identifier for the student
            quiz_id: Optional identifier for the quiz
            metadata: Optional metadata for the conversation
        """
        self.conversation_id = conversation_id if conversation_id else str(uuid.uuid4())
        self.student_id = student_id
        self.quiz_id = quiz_id
        self.metadata = metadata if metadata is not None else {}
        self.messages: List[ConversationMessage] = []
        self.start_time = time.time()
        self.end_time: Optional[float] = None
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Add a message to the conversation.
        
        Args:
            role: The role of the message sender
            content: The content of the message
            metadata: Optional metadata for the message
            
        Returns:
            The created ConversationMessage
        """
        message = ConversationMessage(role, content, metadata=metadata)
        self.messages.append(message)
        return message
    
    def add_system_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Add a system message to the conversation.
        
        Args:
            content: The content of the message
            metadata: Optional metadata for the message
            
        Returns:
            The created ConversationMessage
        """
        return self.add_message("system", content, metadata)
    
    def add_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Add a user message to the conversation.
        
        Args:
            content: The content of the message
            metadata: Optional metadata for the message
            
        Returns:
            The created ConversationMessage
        """
        return self.add_message("user", content, metadata)
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Add an assistant message to the conversation.
        
        Args:
            content: The content of the message
            metadata: Optional metadata for the message
            
        Returns:
            The created ConversationMessage
        """
        return self.add_message("assistant", content, metadata)
    
    def add_question(self, question: Dict[str, Any]) -> ConversationMessage:
        """
        Add a question to the conversation.
        
        Args:
            question: The question dictionary
            
        Returns:
            The created ConversationMessage
        """
        question_text = question.get("text", "")
        
        # Add options if it's a multiple-choice question
        if "options" in question:
            options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(question["options"])])
            question_text = f"{question_text}\n\n{options_text}"
        
        return self.add_assistant_message(question_text, {
            "question_type": question.get("type"),
            "difficulty": question.get("difficulty"),
            "community_id": question.get("community_id"),
            "question_id": question.get("id", str(uuid.uuid4())),
            "is_question": True
        })
    
    def add_answer(self, answer: str, correct: bool, 
                 quality_score: Optional[int] = None,
                 feedback: Optional[Dict[str, Any]] = None) -> ConversationMessage:
        """
        Add an answer to the conversation.
        
        Args:
            answer: The student's answer
            correct: Whether the answer was correct
            quality_score: Optional quality score for the answer
            feedback: Optional feedback for the answer
            
        Returns:
            The created ConversationMessage
        """
        return self.add_user_message(answer, {
            "correct": correct,
            "quality_score": quality_score,
            "feedback": feedback,
            "is_answer": True
        })
    
    def add_feedback(self, feedback: Dict[str, Any]) -> ConversationMessage:
        """
        Add feedback to the conversation.
        
        Args:
            feedback: The feedback dictionary
            
        Returns:
            The created ConversationMessage
        """
        feedback_text = feedback.get("message", "")
        
        if feedback.get("explanation"):
            feedback_text += f"\n\n{feedback['explanation']}"
        
        if feedback.get("next_steps"):
            next_steps = "\n".join([f"- {step}" for step in feedback["next_steps"]])
            feedback_text += f"\n\n{next_steps}"
        
        return self.add_assistant_message(feedback_text, {
            "correct": feedback.get("correct"),
            "quality_score": feedback.get("quality_score"),
            "is_feedback": True
        })
    
    def end_conversation(self) -> None:
        """End the conversation and record the end time."""
        self.end_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the conversation to a dictionary.
        
        Returns:
            Dictionary representation of the conversation
        """
        return {
            "conversation_id": self.conversation_id,
            "student_id": self.student_id,
            "quiz_id": self.quiz_id,
            "metadata": self.metadata,
            "messages": [message.to_dict() for message in self.messages],
            "start_time": self.start_time,
            "start_time_formatted": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": self.end_time,
            "end_time_formatted": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration_seconds": self.end_time - self.start_time if self.end_time else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuizConversation':
        """
        Create a conversation from a dictionary.
        
        Args:
            data: Dictionary representation of the conversation
            
        Returns:
            QuizConversation instance
        """
        conversation = cls(
            conversation_id=data.get("conversation_id"),
            student_id=data.get("student_id"),
            quiz_id=data.get("quiz_id"),
            metadata=data.get("metadata", {})
        )
        
        conversation.start_time = data.get("start_time", time.time())
        conversation.end_time = data.get("end_time")
        
        for message_data in data.get("messages", []):
            message = ConversationMessage.from_dict(message_data)
            conversation.messages.append(message)
        
        return conversation


class ConversationHistoryManager:
    """Manager for storing and retrieving conversation history."""
    
    def __init__(self, storage_dir: str = "conversation_history", use_database: Optional[bool] = None):
        """
        Initialize the conversation history manager.
        
        Args:
            storage_dir: Directory to store conversation history
            use_database: Whether to use the database (defaults to USE_DATABASE environment variable)
        """
        self.storage_dir = storage_dir
        self.use_database = use_database if use_database is not None else USE_DATABASE
        self.db_manager = None
        
        # Create the storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize database manager if needed
        if self.use_database:
            try:
                from .database_adapter import DatabaseConversationManager
                self.db_manager = DatabaseConversationManager(storage_dir)
                logger.info(f"Initialized ConversationHistoryManager with database and storage directory: {storage_dir}")
            except ImportError as e:
                logger.warning(f"Failed to import DatabaseConversationManager: {e}")
                logger.warning("Falling back to file-based storage")
                self.use_database = False
                logger.info(f"Initialized ConversationHistoryManager with storage directory: {storage_dir}")
        else:
            logger.info(f"Initialized ConversationHistoryManager with storage directory: {storage_dir}")
    
    def save_conversation(self, conversation: QuizConversation) -> str:
        """
        Save a conversation to storage.
        
        Args:
            conversation: The conversation to save
            
        Returns:
            Path to the saved conversation file or database ID
        """
        # Use database if enabled
        if self.use_database and self.db_manager:
            try:
                result = self.db_manager.save_conversation(conversation)
                logger.info(f"Saved conversation {conversation.conversation_id} to database")
                return result
            except Exception as e:
                logger.error(f"Failed to save conversation to database: {e}")
                logger.info("Falling back to file-based storage")
        
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
        # Use database if enabled and the file_path looks like a UUID
        if self.use_database and self.db_manager and len(file_path) == 36 and '-' in file_path:
            try:
                # This is a database ID, not a file path
                # For now, we don't have a direct method to load from database ID
                # This would need to be implemented in the database adapter
                pass
            except Exception as e:
                logger.error(f"Failed to load conversation from database: {e}")
                logger.info("Falling back to file-based storage")
        
        # Load from file
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
        # Use database if enabled
        if self.use_database and self.db_manager:
            try:
                return self.db_manager.get_conversations_for_student(student_id)
            except Exception as e:
                logger.error(f"Failed to get conversations from database: {e}")
                logger.info("Falling back to file-based storage")
        
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
        # Use database if enabled
        if self.use_database and self.db_manager:
            try:
                return self.db_manager.get_all_conversations()
            except Exception as e:
                logger.error(f"Failed to get all conversations from database: {e}")
                logger.info("Falling back to file-based storage")
        
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
        # Use database if enabled and the file_path looks like a UUID
        if self.use_database and self.db_manager and len(file_path) == 36 and '-' in file_path:
            try:
                # This is a database ID, not a file path
                # For now, we don't have a direct method to delete from database ID
                # This would need to be implemented in the database adapter
                pass
            except Exception as e:
                logger.error(f"Failed to delete conversation from database: {e}")
                logger.info("Falling back to file-based storage")
        
        try:
            os.remove(file_path)
            logger.info(f"Deleted conversation file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete conversation file {file_path}: {e}")
            return False
    
    def __del__(self):
        """Clean up resources when the object is destroyed."""
        if self.use_database and self.db_manager:
            try:
                self.db_manager.close()
            except Exception as e:
                logger.error(f"Failed to close database connection: {e}")


class ConversationExporter:
    """Utility for exporting conversations in different formats."""
    
    @staticmethod
    def export_to_json(conversation: QuizConversation, file_path: str) -> bool:
        """
        Export a conversation to a JSON file.
        
        Args:
            conversation: The conversation to export
            file_path: Path to save the JSON file
            
        Returns:
            True if the export was successful, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(conversation.to_dict(), f, indent=2, default=str)
            
            logger.info(f"Exported conversation to JSON: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export conversation to JSON: {e}")
            return False
    
    @staticmethod
    def export_to_text(conversation: QuizConversation, file_path: str) -> bool:
        """
        Export a conversation to a text file.
        
        Args:
            conversation: The conversation to export
            file_path: Path to save the text file
            
        Returns:
            True if the export was successful, False otherwise
        """
        try:
            with open(file_path, 'w') as f:
                # Write header
                f.write(f"Conversation ID: {conversation.conversation_id}\n")
                f.write(f"Student ID: {conversation.student_id}\n")
                f.write(f"Quiz ID: {conversation.quiz_id}\n")
                f.write(f"Start Time: {datetime.fromtimestamp(conversation.start_time).isoformat()}\n")
                if conversation.end_time:
                    f.write(f"End Time: {datetime.fromtimestamp(conversation.end_time).isoformat()}\n")
                    duration = conversation.end_time - conversation.start_time
                    f.write(f"Duration: {duration:.2f} seconds\n")
                f.write("\n")
                
                # Write messages
                for message in conversation.messages:
                    timestamp = datetime.fromtimestamp(message.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"[{timestamp}] {message.role.upper()}:\n")
                    f.write(f"{message.content}\n\n")
                    
                    # Write metadata if available
                    if message.metadata:
                        if "is_question" in message.metadata and message.metadata["is_question"]:
                            f.write(f"Question Type: {message.metadata.get('question_type')}\n")
                            f.write(f"Difficulty: {message.metadata.get('difficulty')}\n")
                        elif "is_answer" in message.metadata and message.metadata["is_answer"]:
                            f.write(f"Correct: {message.metadata.get('correct')}\n")
                            if "quality_score" in message.metadata:
                                f.write(f"Quality Score: {message.metadata.get('quality_score')}\n")
                        
                        f.write("\n")
            
            logger.info(f"Exported conversation to text: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export conversation to text: {e}")
            return False
    
    @staticmethod
    def export_to_csv(conversation: QuizConversation, file_path: str) -> bool:
        """
        Export a conversation to a CSV file.
        
        Args:
            conversation: The conversation to export
            file_path: Path to save the CSV file
            
        Returns:
            True if the export was successful, False otherwise
        """
        try:
            import csv
            
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    "Timestamp", "Role", "Content", "Question Type", 
                    "Difficulty", "Correct", "Quality Score"
                ])
                
                # Write messages
                for message in conversation.messages:
                    timestamp = datetime.fromtimestamp(message.timestamp).isoformat()
                    
                    # Extract metadata
                    question_type = message.metadata.get("question_type", "")
                    difficulty = message.metadata.get("difficulty", "")
                    correct = message.metadata.get("correct", "")
                    quality_score = message.metadata.get("quality_score", "")
                    
                    writer.writerow([
                        timestamp, message.role, message.content, 
                        question_type, difficulty, correct, quality_score
                    ])
            
            logger.info(f"Exported conversation to CSV: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export conversation to CSV: {e}")
            return False


# Example usage
def main():
    """Example usage of the conversation history module."""
    # Create a conversation
    conversation = QuizConversation(
        student_id="test_student",
        quiz_id="test_quiz"
    )
    
    # Add a system message
    conversation.add_system_message("Welcome to the adaptive quiz!")
    
    # Add a question
    question = {
        "text": "Who is the author of The Lord of the Rings?",
        "type": "multiple_choice",
        "difficulty": 1,
        "community_id": 1,
        "options": ["J.K. Rowling", "J.R.R. Tolkien", "George R.R. Martin", "C.S. Lewis"],
        "correct_answer": "J.R.R. Tolkien"
    }
    conversation.add_question(question)
    
    # Add an answer
    conversation.add_answer("J.R.R. Tolkien", True)
    
    # Add feedback
    feedback = {
        "message": "Correct!",
        "explanation": "J.R.R. Tolkien is the author of The Lord of the Rings.",
        "next_steps": ["Let's try a more difficult question."],
        "correct": True
    }
    conversation.add_feedback(feedback)
    
    # End the conversation
    conversation.end_conversation()
    
    # Save the conversation
    manager = ConversationHistoryManager()
    file_path = manager.save_conversation(conversation)
    
    # Load the conversation
    loaded_conversation = manager.load_conversation(file_path)
    
    # Export the conversation
    exporter = ConversationExporter()
    exporter.export_to_text(loaded_conversation, "test_conversation.txt")
    exporter.export_to_csv(loaded_conversation, "test_conversation.csv")

if __name__ == "__main__":
    main()
