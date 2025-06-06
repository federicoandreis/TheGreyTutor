"""
Conversation repositories for The Grey Tutor database.

This module provides repository classes for conversation-related models.
"""
import logging
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from database.models.conversation import Conversation, ConversationParameters, Message, Question, Answer
from database.repositories.base import BaseRepository

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConversationRepository(BaseRepository[Conversation]):
    """Repository for Conversation model."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(Conversation, db)
    
    def get_by_user_id(self, user_id: str) -> List[Conversation]:
        """
        Get all conversations for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of Conversation instances
        """
        return self.db.query(Conversation).filter(Conversation.user_id == user_id).all()
    
    def get_by_session_id(self, session_id: str) -> List[Conversation]:
        """
        Get all conversations for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of Conversation instances
        """
        return self.db.query(Conversation).filter(Conversation.session_id == session_id).all()
    
    def get_by_type(self, conversation_type: str) -> List[Conversation]:
        """
        Get all conversations of a specific type.
        
        Args:
            conversation_type: Conversation type
            
        Returns:
            List of Conversation instances
        """
        return self.db.query(Conversation).filter(Conversation.conversation_type == conversation_type).all()
    
    def get_by_quiz_id(self, quiz_id: str) -> List[Conversation]:
        """
        Get all conversations for a quiz.
        
        Args:
            quiz_id: Quiz ID
            
        Returns:
            List of Conversation instances
        """
        return self.db.query(Conversation).filter(Conversation.quiz_id == quiz_id).all()
    
    def create_with_parameters(self, conversation_data: Dict[str, Any], parameters_data: Dict[str, Any]) -> Conversation:
        """
        Create a new conversation with parameters.
        
        Args:
            conversation_data: Conversation data
            parameters_data: Parameters data
            
        Returns:
            Created Conversation instance
        """
        # Create conversation
        conversation = self.create(conversation_data)
        
        # Create parameters
        parameters_data["conversation_id"] = conversation.id
        parameters = ConversationParameters(**parameters_data)
        self.db.add(parameters)
        self.db.commit()
        self.db.refresh(parameters)
        
        return conversation
    
    def end_conversation(self, id: str) -> Optional[Conversation]:
        """
        End a conversation.
        
        Args:
            id: Conversation ID
            
        Returns:
            Updated Conversation instance if found, None otherwise
        """
        conversation = self.get_by_id(id)
        if not conversation:
            return None
        
        # Set end time
        conversation.end_time = datetime.utcnow()
        
        # Calculate duration
        if conversation.start_time:
            conversation.duration_seconds = (conversation.end_time - conversation.start_time).total_seconds()
        
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

class MessageRepository(BaseRepository[Message]):
    """Repository for Message model."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(db, Message)
    
    def get_by_conversation_id(self, conversation_id: str) -> List[Message]:
        """
        Get all messages for a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of Message instances
        """
        return self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp).all()
    
    def get_by_role(self, conversation_id: str, role: str) -> List[Message]:
        """
        Get all messages for a conversation with a specific role.
        
        Args:
            conversation_id: Conversation ID
            role: Message role
            
        Returns:
            List of Message instances
        """
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == role
        ).order_by(Message.timestamp).all()
    
    def get_last_message(self, conversation_id: str) -> Optional[Message]:
        """
        Get the last message for a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Message instance if found, None otherwise
        """
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp.desc()).first()

class QuestionRepository(BaseRepository[Question]):
    """Repository for Question model."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(db, Question)
    
    def get_by_message_id(self, message_id: str) -> Optional[Question]:
        """
        Get a question by message ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            Question instance if found, None otherwise
        """
        return self.db.query(Question).filter(Question.message_id == message_id).first()
    
    def get_by_type(self, question_type: str) -> List[Question]:
        """
        Get all questions of a specific type.
        
        Args:
            question_type: Question type
            
        Returns:
            List of Question instances
        """
        return self.db.query(Question).filter(Question.type == question_type).all()
    
    def get_by_difficulty(self, difficulty: str) -> List[Question]:
        """
        Get all questions of a specific difficulty.
        
        Args:
            difficulty: Difficulty level
            
        Returns:
            List of Question instances
        """
        return self.db.query(Question).filter(Question.difficulty == difficulty).all()
    
    def get_by_entity(self, entity: str) -> List[Question]:
        """
        Get all questions for a specific entity.
        
        Args:
            entity: Entity
            
        Returns:
            List of Question instances
        """
        return self.db.query(Question).filter(Question.entity == entity).all()
    
    def get_by_community_id(self, community_id: str) -> List[Question]:
        """
        Get all questions for a specific community.
        
        Args:
            community_id: Community ID
            
        Returns:
            List of Question instances
        """
        return self.db.query(Question).filter(Question.community_id == community_id).all()

class AnswerRepository(BaseRepository[Answer]):
    """Repository for Answer model."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(db, Answer)
    
    def get_by_message_id(self, message_id: str) -> Optional[Answer]:
        """
        Get an answer by message ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            Answer instance if found, None otherwise
        """
        return self.db.query(Answer).filter(Answer.message_id == message_id).first()
    
    def get_by_question_id(self, question_id: str) -> List[Answer]:
        """
        Get all answers for a question.
        
        Args:
            question_id: Question ID
            
        Returns:
            List of Answer instances
        """
        return self.db.query(Answer).filter(Answer.question_id == question_id).all()
    
    def get_correct_answers(self, question_id: str) -> List[Answer]:
        """
        Get all correct answers for a question.
        
        Args:
            question_id: Question ID
            
        Returns:
            List of Answer instances
        """
        return self.db.query(Answer).filter(
            Answer.question_id == question_id,
            Answer.correct == True
        ).all()
    
    def get_incorrect_answers(self, question_id: str) -> List[Answer]:
        """
        Get all incorrect answers for a question.
        
        Args:
            question_id: Question ID
            
        Returns:
            List of Answer instances
        """
        return self.db.query(Answer).filter(
            Answer.question_id == question_id,
            Answer.correct == False
        ).all()
