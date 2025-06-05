"""
API module for The Grey Tutor database.

This module provides API functions for interacting with the database.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import json

from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.user import User, UserProfile, UserSession
from database.models.conversation import Conversation, Message, Question, Answer
from database.repositories.user import UserRepository, UserProfileRepository, UserSessionRepository
from database.repositories.conversation import (
    ConversationRepository, MessageRepository, QuestionRepository, AnswerRepository
)
from database.repositories.cache import CacheRepository

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseAPI:
    """API for interacting with the database."""
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize the API.
        
        Args:
            db: SQLAlchemy session (optional, will create one if not provided)
        """
        self.db = db or next(get_db())
        self.user_repo = UserRepository(self.db)
        self.profile_repo = UserProfileRepository(self.db)
        self.session_repo = UserSessionRepository(self.db)
        self.conversation_repo = ConversationRepository(self.db)
        self.message_repo = MessageRepository(self.db)
        self.question_repo = QuestionRepository(self.db)
        self.answer_repo = AnswerRepository(self.db)
        self.cache_repo = CacheRepository(self.db)
    
    def close(self) -> None:
        """Close the database session."""
        self.db.close()
    
    # User methods
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by username.
        
        Args:
            username: Username
            
        Returns:
            User data if found, None otherwise
        """
        user = self.user_repo.get_by_username(username)
        if not user:
            return None
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    
    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a user profile by username.
        
        Args:
            username: Username
            
        Returns:
            User profile data if found, None otherwise
        """
        user = self.user_repo.get_by_username(username)
        if not user:
            return None
        
        profile = self.profile_repo.get_by_user_id(user.id)
        if not profile:
            return None
        
        return {
            "user_id": profile.user_id,
            "community_mastery": profile.community_mastery,
            "entity_familiarity": profile.entity_familiarity,
            "question_type_performance": profile.question_type_performance,
            "difficulty_performance": profile.difficulty_performance,
            "overall_mastery": profile.overall_mastery,
            "mastered_objectives": profile.mastered_objectives,
            "current_objective": profile.current_objective,
            "last_updated": profile.last_updated.isoformat() if profile.last_updated else None
        }
    
    def update_user_profile(self, username: str, profile_data: Dict[str, Any]) -> bool:
        """
        Update a user profile.
        
        Args:
            username: Username
            profile_data: Profile data to update
            
        Returns:
            True if successful, False otherwise
        """
        user = self.user_repo.get_by_username(username)
        if not user:
            return False
        
        profile = self.profile_repo.get_by_user_id(user.id)
        if not profile:
            return False
        
        # Update profile
        profile_data["last_updated"] = datetime.utcnow()
        updated_profile = self.profile_repo.update(profile.user_id, profile_data, pk_name="user_id")
        
        return updated_profile is not None
    
    # Session methods
    
    def create_session(self, username: str, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new user session.
        
        Args:
            username: Username
            session_data: Session data
            
        Returns:
            Session data if successful, None otherwise
        """
        user = self.user_repo.get_by_username(username)
        if not user:
            return None
        
        # Create session
        session_data["user_id"] = user.id
        session_data["start_time"] = datetime.utcnow()
        session = self.session_repo.create(session_data)
        
        if not session:
            return None
        
        return {
            "id": session.id,
            "user_id": session.user_id,
            "session_type": session.session_type,
            "start_time": session.start_time.isoformat() if session.start_time else None,
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "questions_asked": session.questions_asked,
            "correct_answers": session.correct_answers,
            "accuracy": session.accuracy,
            "mastery_before": session.mastery_before,
            "mastery_after": session.mastery_after,
            "strategy": session.strategy,
            "theme": session.theme,
            "fussiness": session.fussiness,
            "tier": session.tier,
            "use_llm": session.use_llm,
            "parameters": session.parameters
        }
    
    def end_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        End a user session.
        
        Args:
            session_id: Session ID
            session_data: Session data to update
            
        Returns:
            True if successful, False otherwise
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            return False
        
        # Update session
        session_data["end_time"] = datetime.utcnow()
        updated_session = self.session_repo.update(session_id, session_data)
        
        return updated_session is not None
    
    # Conversation methods
    
    def create_conversation(
        self, username: str, conversation_data: Dict[str, Any], parameters_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new conversation.
        
        Args:
            username: Username
            conversation_data: Conversation data
            parameters_data: Parameters data
            
        Returns:
            Conversation data if successful, None otherwise
        """
        user = self.user_repo.get_by_username(username)
        if not user:
            return None
        
        # Create conversation
        conversation_data["user_id"] = user.id
        conversation_data["start_time"] = datetime.utcnow()
        conversation = self.conversation_repo.create_with_parameters(conversation_data, parameters_data)
        
        if not conversation:
            return None
        
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "session_id": conversation.session_id,
            "conversation_type": conversation.conversation_type,
            "quiz_id": conversation.quiz_id,
            "start_time": conversation.start_time.isoformat() if conversation.start_time else None,
            "end_time": conversation.end_time.isoformat() if conversation.end_time else None,
            "duration_seconds": conversation.duration_seconds,
            "meta_data": conversation.meta_data
        }
    
    def end_conversation(self, conversation_id: str) -> bool:
        """
        End a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if successful, False otherwise
        """
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            return False
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration_seconds = (end_time - conversation.start_time).total_seconds() if conversation.start_time else 0
        
        # Update conversation
        updated_conversation = self.conversation_repo.update(
            conversation_id, 
            {
                "end_time": end_time,
                "duration_seconds": duration_seconds
            }
        )
        
        return updated_conversation is not None
    
    def add_message(self, conversation_id: str, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            message_data: Message data
            
        Returns:
            Message data if successful, None otherwise
        """
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            return None
        
        # Create message
        message_data["conversation_id"] = conversation_id
        message_data["timestamp"] = datetime.utcnow()
        message = self.message_repo.create(message_data)
        
        if not message:
            return None
        
        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
            "meta_data": message.meta_data
        }
    
    def add_question(self, message_id: str, question_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a question to a message.
        
        Args:
            message_id: Message ID
            question_data: Question data
            
        Returns:
            Question data if successful, None otherwise
        """
        message = self.message_repo.get_by_id(message_id)
        if not message:
            return None
        
        # Create question
        question_data["message_id"] = message_id
        question = self.question_repo.create(question_data)
        
        if not question:
            return None
        
        return {
            "id": question.id,
            "message_id": question.message_id,
            "type": question.type,
            "difficulty": question.difficulty,
            "entity": question.entity,
            "tier": question.tier,
            "options": question.options,
            "correct_answer": question.correct_answer,
            "community_id": question.community_id,
            "meta_data": question.meta_data
        }
    
    def add_answer(self, message_id: str, answer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add an answer to a message.
        
        Args:
            message_id: Message ID
            answer_data: Answer data
            
        Returns:
            Answer data if successful, None otherwise
        """
        message = self.message_repo.get_by_id(message_id)
        if not message:
            return None
        
        # Create answer
        answer_data["message_id"] = message_id
        answer = self.answer_repo.create(answer_data)
        
        if not answer:
            return None
        
        return {
            "id": answer.id,
            "message_id": answer.message_id,
            "question_id": answer.question_id,
            "content": answer.content,
            "correct": answer.correct,
            "quality_score": answer.quality_score,
            "feedback": answer.feedback
        }
    
    # Cache methods
    
    def get_cache(self, cache_type: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a cache entry.
        
        Args:
            cache_type: Cache type
            key: Cache key
            
        Returns:
            Cache entry if found, None otherwise
        """
        entry = self.cache_repo.get_by_key(cache_type, key)
        if not entry:
            return None
        
        return {
            "id": entry.id,
            "cache_type": entry.cache_type,
            "key": entry.key,
            "value": entry.value,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None,
            "access_count": entry.access_count
        }
    
    def set_cache(self, cache_type: str, key: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        Set a cache entry.
        
        Args:
            cache_type: Cache type
            key: Cache key
            value: Cache value
            
        Returns:
            Cache entry if successful, None otherwise
        """
        entry = self.cache_repo.set(cache_type, key, value)
        if not entry:
            return None
        
        return {
            "id": entry.id,
            "cache_type": entry.cache_type,
            "key": entry.key,
            "value": entry.value,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None,
            "access_count": entry.access_count
        }
    
    def delete_cache(self, cache_type: str, key: str) -> bool:
        """
        Delete a cache entry.
        
        Args:
            cache_type: Cache type
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        return self.cache_repo.delete_by_key(cache_type, key)
