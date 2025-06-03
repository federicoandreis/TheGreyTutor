"""
Exporter class for conversation history.
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime

from ..core.conversation import QuizConversation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
