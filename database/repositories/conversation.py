"""
Conversation repository for The Grey Tutor.

This module provides repository classes for conversation data.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from database.models.conversation import (
    Conversation, Message, Question, Answer, ConversationParameters
)
from database.repositories.base import BaseRepository

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for conversation data."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(Conversation, db)
    
    def get_by_user_id(self, user_id: str) -> List[Conversation]:
        """
        Get conversations by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of conversations
        """
        try:
            return self.db.query(Conversation).filter(Conversation.user_id == user_id).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting conversations by user ID: {e}")
            return []
    
    def get_by_session_id(self, session_id: str) -> List[Conversation]:
        """
        Get conversations by session ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of conversations
        """
        try:
            return self.db.query(Conversation).filter(Conversation.session_id == session_id).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting conversations by session ID: {e}")
            return []
    
    def get_by_type(self, conversation_type: str) -> List[Conversation]:
        """
        Get conversations by type.
        
        Args:
            conversation_type: Conversation type
            
        Returns:
            List of conversations
        """
        try:
            return self.db.query(Conversation).filter(Conversation.conversation_type == conversation_type).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting conversations by type: {e}")
            return []
    
    def create_with_parameters(
        self, conversation_data: Dict[str, Any], parameters_data: Dict[str, Any]
    ) -> Optional[Conversation]:
        """
        Create a new conversation with parameters.
        
        Args:
            conversation_data: Conversation data
            parameters_data: Parameters data
            
        Returns:
            Created conversation if successful, None otherwise
        """
        try:
            conversation = Conversation(**conversation_data)
            self.db.add(conversation)
            self.db.flush()  # Flush to get the conversation ID
            
            parameters = ConversationParameters(
                conversation_id=conversation.id, **parameters_data
            )
            self.db.add(parameters)
            
            self.db.commit()
            self.db.refresh(conversation)
            return conversation
        except SQLAlchemyError as e:
            logger.error(f"Error creating conversation with parameters: {e}")
            self.db.rollback()
            return None


class MessageRepository(BaseRepository[Message]):
    """Repository for message data."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(Message, db)
    
    def get_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """
        Get messages by conversation ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of messages
        """
        try:
            return (
                self.db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.timestamp)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting messages by conversation ID: {e}")
            return []
    
    def get_by_role(self, conversation_id: str, role: str) -> List[Message]:
        """
        Get messages by role.
        
        Args:
            conversation_id: Conversation ID
            role: Message role
            
        Returns:
            List of messages
        """
        try:
            return (
                self.db.query(Message)
                .filter(Message.conversation_id == conversation_id, Message.role == role)
                .order_by(Message.timestamp)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Error getting messages by role: {e}")
            return []


class QuestionRepository(BaseRepository[Question]):
    """Repository for question data."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(Question, db)
    
    def get_by_message_id(self, message_id: str) -> List[Question]:
        """
        Get questions by message ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            List of questions
        """
        try:
            return self.db.query(Question).filter(Question.message_id == message_id).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting questions by message ID: {e}")
            return []
    
    def get_by_type(self, question_type: str) -> List[Question]:
        """
        Get questions by type.
        
        Args:
            question_type: Question type
            
        Returns:
            List of questions
        """
        try:
            return self.db.query(Question).filter(Question.type == question_type).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting questions by type: {e}")
            return []
    
    def get_by_entity(self, entity: str) -> List[Question]:
        """
        Get questions by entity.
        
        Args:
            entity: Entity name
            
        Returns:
            List of questions
        """
        try:
            return self.db.query(Question).filter(Question.entity == entity).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting questions by entity: {e}")
            return []


class AnswerRepository(BaseRepository[Answer]):
    """Repository for answer data."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(Answer, db)
    
    def get_by_message_id(self, message_id: str) -> List[Answer]:
        """
        Get answers by message ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            List of answers
        """
        try:
            return self.db.query(Answer).filter(Answer.message_id == message_id).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting answers by message ID: {e}")
            return []
    
    def get_by_question_id(self, question_id: str) -> List[Answer]:
        """
        Get answers by question ID.
        
        Args:
            question_id: Question ID
            
        Returns:
            List of answers
        """
        try:
            return self.db.query(Answer).filter(Answer.question_id == question_id).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting answers by question ID: {e}")
            return []
