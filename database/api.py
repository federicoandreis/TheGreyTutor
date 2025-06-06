"""
Database API module for The Grey Tutor.

This module provides a simple API for interacting with the database.
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.connection import get_db_session
from database.models.user import User, UserProfile, UserSession
from database.models.conversation import Conversation, ConversationParameters, Message, Question, Answer
from database.models.cache import Cache, QuestionCache, AssessmentCache
from database.repositories.user import UserRepository, UserProfileRepository, UserSessionRepository
from database.repositories.conversation import ConversationRepository, MessageRepository, QuestionRepository, AnswerRepository
from database.repositories.cache import CacheRepository, QuestionCacheRepository, AssessmentCacheRepository

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseAPI:
    """Database API for The Grey Tutor."""
    
    def __init__(self):
        """Initialize the database API."""
        self.db = get_db_session()
        
        # Create repositories
        self.user_repo = UserRepository(self.db)
        self.profile_repo = UserProfileRepository(self.db)
        self.session_repo = UserSessionRepository(self.db)
        self.conversation_repo = ConversationRepository(self.db)
        self.message_repo = MessageRepository(self.db)
        self.question_repo = QuestionRepository(self.db)
        self.answer_repo = AnswerRepository(self.db)
        self.cache_repo = CacheRepository(self.db)
        self.question_cache_repo = QuestionCacheRepository(self.db)
        self.assessment_cache_repo = AssessmentCacheRepository(self.db)
    
    def close(self):
        """Close the database connection."""
        self.db.close()
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.close()
    
    # User methods
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User data if found, None otherwise
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        # Get user profile
        profile = self.profile_repo.get_by_user_id(user.id)
        
        # Convert to dict
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "profile": {
                "id": profile.id,
                "community_mastery": profile.community_mastery,
                "entity_familiarity": profile.entity_familiarity,
                "question_type_performance": profile.question_type_performance,
                "difficulty_performance": profile.difficulty_performance,
                "overall_mastery": profile.overall_mastery,
                "mastered_objectives": profile.mastered_objectives,
                "current_objective": profile.current_objective,
                "last_updated": profile.last_updated.isoformat() if profile.last_updated else None,
            } if profile else None,
        }
        
        return user_data
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
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
        
        return self.get_user(user.id)
    
    def get_users(self) -> List[Dict[str, Any]]:
        """
        Get all users.
        
        Returns:
            List of user data
        """
        users = self.user_repo.get_all()
        return [self.get_user(user.id) for user in users]
    
    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            data: User data
            
        Returns:
            Created user data
        """
        try:
            # Extract profile data
            profile_data = data.pop("profile", {})
            
            # Create user
            user = self.user_repo.create(data)
            
            # Create profile
            if profile_data:
                profile_data["user_id"] = user.id
                self.profile_repo.create(profile_data)
            else:
                # Create default profile
                self.profile_repo.create({
                    "user_id": user.id,
                })
            
            return self.get_user(user.id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    def update_user(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a user.
        
        Args:
            user_id: User ID
            data: User data
            
        Returns:
            Updated user data if found, None otherwise
        """
        try:
            # Extract profile data
            profile_data = data.pop("profile", None)
            
            # Update user
            user = self.user_repo.update(user_id, data)
            if not user:
                return None
            
            # Update profile
            if profile_data:
                self.profile_repo.update_by_user_id(user.id, profile_data)
            
            return self.get_user(user.id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating user: {e}")
            raise
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            return self.user_repo.delete(user_id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting user: {e}")
            raise
    
    # Session methods
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data if found, None otherwise
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            return None
        
        # Convert to dict
        session_data = {
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
            "parameters": session.parameters,
        }
        
        return session_data
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get sessions by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of session data
        """
        sessions = self.session_repo.get_by_user_id(user_id)
        return [self.get_session(session.id) for session in sessions]
    
    def create_session(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new session.
        
        Args:
            data: Session data
            
        Returns:
            Created session data
        """
        try:
            session = self.session_repo.create(data)
            return self.get_session(session.id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating session: {e}")
            raise
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a session.
        
        Args:
            session_id: Session ID
            data: Session data
            
        Returns:
            Updated session data if found, None otherwise
        """
        try:
            session = self.session_repo.update(session_id, data)
            if not session:
                return None
            
            return self.get_session(session.id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating session: {e}")
            raise
    
    def end_session(self, session_id: str, data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        End a session.
        
        Args:
            session_id: Session ID
            data: Session data (optional)
            
        Returns:
            Updated session data if found, None otherwise
        """
        try:
            session = self.session_repo.end_session(session_id, data)
            if not session:
                return None
            
            return self.get_session(session.id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error ending session: {e}")
            raise
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            return self.session_repo.delete(session_id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting session: {e}")
            raise
    
    # Conversation methods
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation data if found, None otherwise
        """
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            return None
        
        # Get messages
        messages = self.message_repo.get_by_conversation_id(conversation.id)
        
        # Convert to dict
        conversation_data = {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "session_id": conversation.session_id,
            "conversation_type": conversation.conversation_type,
            "quiz_id": conversation.quiz_id,
            "start_time": conversation.start_time.isoformat() if conversation.start_time else None,
            "end_time": conversation.end_time.isoformat() if conversation.end_time else None,
            "duration_seconds": conversation.duration_seconds,
            "meta_data": conversation.meta_data,
            "messages": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat() if message.timestamp else None,
                    "meta_data": message.meta_data,
                }
                for message in messages
            ],
        }
        
        return conversation_data
    
    def get_user_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get conversations by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of conversation data
        """
        conversations = self.conversation_repo.get_by_user_id(user_id)
        return [self.get_conversation(conversation.id) for conversation in conversations]
    
    def get_session_conversations(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversations by session ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of conversation data
        """
        conversations = self.conversation_repo.get_by_session_id(session_id)
        return [self.get_conversation(conversation.id) for conversation in conversations]
    
    def create_conversation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new conversation.
        
        Args:
            data: Conversation data
            
        Returns:
            Created conversation data
        """
        try:
            # Extract messages
            messages = data.pop("messages", [])
            
            # Extract parameters
            parameters = data.pop("parameters", None)
            
            # Create conversation
            if parameters:
                conversation = self.conversation_repo.create_with_parameters(data, parameters)
            else:
                conversation = self.conversation_repo.create(data)
            
            # Create messages
            for message_data in messages:
                message_data["conversation_id"] = conversation.id
                self.message_repo.create(message_data)
            
            return self.get_conversation(conversation.id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating conversation: {e}")
            raise
    
    def update_conversation(self, conversation_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a conversation.
        
        Args:
            conversation_id: Conversation ID
            data: Conversation data
            
        Returns:
            Updated conversation data if found, None otherwise
        """
        try:
            conversation = self.conversation_repo.update(conversation_id, data)
            if not conversation:
                return None
            
            return self.get_conversation(conversation.id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating conversation: {e}")
            raise
    
    def end_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        End a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Updated conversation data if found, None otherwise
        """
        try:
            conversation = self.conversation_repo.end_conversation(conversation_id)
            if not conversation:
                return None
            
            return self.get_conversation(conversation.id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error ending conversation: {e}")
            raise
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            return self.conversation_repo.delete(conversation_id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting conversation: {e}")
            raise
    
    # Message methods
    
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a message by ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            Message data if found, None otherwise
        """
        message = self.message_repo.get_by_id(message_id)
        if not message:
            return None
        
        # Get question and answer
        question = self.question_repo.get_by_message_id(message.id)
        answer = self.answer_repo.get_by_message_id(message.id)
        
        # Convert to dict
        message_data = {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None,
            "meta_data": message.meta_data,
            "question": {
                "id": question.id,
                "type": question.type,
                "difficulty": question.difficulty,
                "entity": question.entity,
                "tier": question.tier,
                "options": question.options,
                "correct_answer": question.correct_answer,
                "community_id": question.community_id,
                "meta_data": question.meta_data,
            } if question else None,
            "answer": {
                "id": answer.id,
                "question_id": answer.question_id,
                "content": answer.content,
                "correct": answer.correct,
                "quality_score": answer.quality_score,
                "feedback": answer.feedback,
            } if answer else None,
        }
        
        return message_data
    
    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get messages by conversation ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of message data
        """
        messages = self.message_repo.get_by_conversation_id(conversation_id)
        return [self.get_message(message.id) for message in messages]
    
    def create_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new message.
        
        Args:
            data: Message data
            
        Returns:
            Created message data
        """
        try:
            # Extract question and answer
            question_data = data.pop("question", None)
            answer_data = data.pop("answer", None)
            
            # Create message
            message = self.message_repo.create(data)
            
            # Create question
            if question_data:
                question_data["message_id"] = message.id
                self.question_repo.create(question_data)
            
            # Create answer
            if answer_data:
                answer_data["message_id"] = message.id
                self.answer_repo.create(answer_data)
            
            return self.get_message(message.id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating message: {e}")
            raise
    
    def update_message(self, message_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a message.
        
        Args:
            message_id: Message ID
            data: Message data
            
        Returns:
            Updated message data if found, None otherwise
        """
        try:
            # Extract question and answer
            question_data = data.pop("question", None)
            answer_data = data.pop("answer", None)
            
            # Update message
            message = self.message_repo.update(message_id, data)
            if not message:
                return None
            
            # Update question
            if question_data:
                question = self.question_repo.get_by_message_id(message.id)
                if question:
                    self.question_repo.update(question.id, question_data)
                else:
                    question_data["message_id"] = message.id
                    self.question_repo.create(question_data)
            
            # Update answer
            if answer_data:
                answer = self.answer_repo.get_by_message_id(message.id)
                if answer:
                    self.answer_repo.update(answer.id, answer_data)
                else:
                    answer_data["message_id"] = message.id
                    self.answer_repo.create(answer_data)
            
            return self.get_message(message.id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating message: {e}")
            raise
    
    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message.
        
        Args:
            message_id: Message ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            return self.message_repo.delete(message_id)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting message: {e}")
            raise
    
    # Cache methods
    
    def get_cache(self, cache_type: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a cache entry by type and key.
        
        Args:
            cache_type: Cache type
            key: Cache key
            
        Returns:
            Cache data if found, None otherwise
        """
        cache = self.cache_repo.get_by_key(cache_type, key)
        if not cache:
            return None
        
        # Convert to dict
        cache_data = {
            "id": cache.id,
            "cache_type": cache.cache_type,
            "key": cache.key,
            "value": cache.value,
            "created_at": cache.created_at.isoformat() if cache.created_at else None,
            "last_accessed": cache.last_accessed.isoformat() if cache.last_accessed else None,
            "access_count": cache.access_count,
        }
        
        return cache_data
    
    def get_cache_by_type(self, cache_type: str) -> List[Dict[str, Any]]:
        """
        Get cache entries by type.
        
        Args:
            cache_type: Cache type
            
        Returns:
            List of cache data
        """
        caches = self.cache_repo.get_by_type(cache_type)
        return [
            {
                "id": cache.id,
                "cache_type": cache.cache_type,
                "key": cache.key,
                "value": cache.value,
                "created_at": cache.created_at.isoformat() if cache.created_at else None,
                "last_accessed": cache.last_accessed.isoformat() if cache.last_accessed else None,
                "access_count": cache.access_count,
            }
            for cache in caches
        ]
    
    def set_cache(self, cache_type: str, key: str, value: Any) -> Dict[str, Any]:
        """
        Set a cache entry.
        
        Args:
            cache_type: Cache type
            key: Cache key
            value: Cache value
            
        Returns:
            Cache data
        """
        try:
            cache = self.cache_repo.get_by_key(cache_type, key)
            if cache:
                cache = self.cache_repo.update_by_key(cache_type, key, value)
            else:
                cache = self.cache_repo.create({
                    "cache_type": cache_type,
                    "key": key,
                    "value": value,
                })
            
            return {
                "id": cache.id,
                "cache_type": cache.cache_type,
                "key": cache.key,
                "value": cache.value,
                "created_at": cache.created_at.isoformat() if cache.created_at else None,
                "last_accessed": cache.last_accessed.isoformat() if cache.last_accessed else None,
                "access_count": cache.access_count,
            }
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error setting cache: {e}")
            raise
    
    def delete_cache(self, cache_type: str, key: str) -> bool:
        """
        Delete a cache entry.
        
        Args:
            cache_type: Cache type
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            return self.cache_repo.delete_by_key(cache_type, key)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting cache: {e}")
            raise
    
    def clear_cache(self, cache_type: str) -> int:
        """
        Clear cache entries by type.
        
        Args:
            cache_type: Cache type
            
        Returns:
            Number of deleted entries
        """
        try:
            return self.cache_repo.delete_by_type(cache_type)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error clearing cache: {e}")
            raise
