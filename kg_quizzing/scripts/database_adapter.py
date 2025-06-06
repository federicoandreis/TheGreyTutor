"""
Database adapter for KG Quizzing.

This module provides an adapter for the KG Quizzing module to use the new database.
"""
import logging
import json
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from database.api import DatabaseAPI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseAdapter:
    """Database adapter for KG Quizzing."""
    
    def __init__(self):
        """Initialize the database adapter."""
        self.api = DatabaseAPI()
    
    def close(self):
        """Close the database connection."""
        self.api.close()
    
    def __enter__(self):
        """Enter context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        self.close()
    
    # User methods
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by username.
        
        Args:
            username: Username
            
        Returns:
            User data if found, None otherwise
        """
        return self.api.get_user_by_username(username)
    
    def get_user_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a user profile by username.
        
        Args:
            username: Username
            
        Returns:
            User profile data if found, None otherwise
        """
        user = self.api.get_user_by_username(username)
        if not user:
            return None
        
        return user.get("profile")
    
    def update_user_profile(self, username: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a user profile by username.
        
        Args:
            username: Username
            profile_data: Profile data
            
        Returns:
            Updated user data if found, None otherwise
        """
        user = self.api.get_user_by_username(username)
        if not user:
            return None
        
        return self.api.update_user(user["id"], {"profile": profile_data})
    
    # Session methods
    
    def create_session(self, username: str, session_type: str = "quiz", **kwargs) -> Dict[str, Any]:
        """
        Create a new session.
        
        Args:
            username: Username
            session_type: Session type
            **kwargs: Additional session data
            
        Returns:
            Created session data
        """
        user = self.api.get_user_by_username(username)
        if not user:
            raise ValueError(f"User '{username}' not found")
        
        session_data = {
            "user_id": user["id"],
            "session_type": session_type,
            **kwargs,
        }
        
        return self.api.create_session(session_data)
    
    def end_session(self, session_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        End a session.
        
        Args:
            session_id: Session ID
            **kwargs: Additional session data
            
        Returns:
            Updated session data if found, None otherwise
        """
        return self.api.end_session(session_id, kwargs)
    
    # Conversation methods
    
    def create_conversation(self, username: str, session_id: str, conversation_type: str = "quiz", **kwargs) -> Dict[str, Any]:
        """
        Create a new conversation.
        
        Args:
            username: Username
            session_id: Session ID
            conversation_type: Conversation type
            **kwargs: Additional conversation data
            
        Returns:
            Created conversation data
        """
        user = self.api.get_user_by_username(username)
        if not user:
            raise ValueError(f"User '{username}' not found")
        
        conversation_data = {
            "user_id": user["id"],
            "session_id": session_id,
            "conversation_type": conversation_type,
            **kwargs,
        }
        
        return self.api.create_conversation(conversation_data)
    
    def add_message(self, conversation_id: str, role: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation ID
            role: Message role
            content: Message content
            **kwargs: Additional message data
            
        Returns:
            Created message data
        """
        message_data = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            **kwargs,
        }
        
        return self.api.create_message(message_data)
    
    def add_question(self, conversation_id: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a question to a conversation.
        
        Args:
            conversation_id: Conversation ID
            question_data: Question data
            
        Returns:
            Created message data with question
        """
        # Extract question-specific data
        question = {
            "type": question_data.get("type", "multiple_choice"),
            "difficulty": question_data.get("difficulty", "medium"),
            "entity": question_data.get("entity"),
            "tier": question_data.get("tier"),
            "options": question_data.get("options"),
            "correct_answer": question_data.get("correct_answer"),
            "community_id": question_data.get("community_id"),
            "meta_data": question_data.get("meta_data", {}),
        }
        
        # Create message with question
        message_data = {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": question_data.get("question_text", ""),
            "meta_data": {
                "is_question": True,
                "question": question_data,
            },
            "question": question,
        }
        
        return self.api.create_message(message_data)
    
    def add_answer(self, conversation_id: str, question_id: str, content: str, correct: bool, **kwargs) -> Dict[str, Any]:
        """
        Add an answer to a conversation.
        
        Args:
            conversation_id: Conversation ID
            question_id: Question ID
            content: Answer content
            correct: Whether the answer is correct
            **kwargs: Additional answer data
            
        Returns:
            Created message data with answer
        """
        # Create message with answer
        message_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": content,
            "meta_data": {
                "is_answer": True,
                "answer": {
                    "question_id": question_id,
                    "correct": correct,
                    **kwargs,
                },
            },
            "answer": {
                "question_id": question_id,
                "content": content,
                "correct": correct,
                **kwargs,
            },
        }
        
        return self.api.create_message(message_data)
    
    def end_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        End a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Updated conversation data if found, None otherwise
        """
        return self.api.end_conversation(conversation_id)
    
    # Cache methods
    
    def get_question_cache(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a question cache entry by question ID.
        
        Args:
            question_id: Question ID
            
        Returns:
            Question cache data if found, None otherwise
        """
        return self.api.get_cache("question", question_id)
    
    def set_question_cache(self, question_id: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set a question cache entry.
        
        Args:
            question_id: Question ID
            question_data: Question data
            
        Returns:
            Question cache data
        """
        return self.api.set_cache("question", question_id, question_data)
    
    def get_assessment_cache(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an assessment cache entry by assessment ID.
        
        Args:
            assessment_id: Assessment ID
            
        Returns:
            Assessment cache data if found, None otherwise
        """
        return self.api.get_cache("assessment", assessment_id)
    
    def set_assessment_cache(self, assessment_id: str, assessment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set an assessment cache entry.
        
        Args:
            assessment_id: Assessment ID
            assessment_data: Assessment data
            
        Returns:
            Assessment cache data
        """
        return self.api.set_cache("assessment", assessment_id, assessment_data)
    
    # Legacy compatibility methods
    
    def save_conversation(self, username: str, conversation_data: Dict[str, Any]) -> str:
        """
        Save a conversation to the database.
        
        Args:
            username: Username
            conversation_data: Conversation data
            
        Returns:
            Conversation ID
        """
        user = self.api.get_user_by_username(username)
        if not user:
            raise ValueError(f"User '{username}' not found")
        
        # Create session
        session = self.api.create_session({
            "user_id": user["id"],
            "session_type": conversation_data.get("conversation_type", "chat"),
            "start_time": conversation_data.get("start_time"),
            "end_time": conversation_data.get("end_time"),
        })
        
        # Create conversation
        conversation = self.api.create_conversation({
            "user_id": user["id"],
            "session_id": session["id"],
            "conversation_type": conversation_data.get("conversation_type", "chat"),
            "start_time": conversation_data.get("start_time"),
            "end_time": conversation_data.get("end_time"),
            "meta_data": conversation_data.get("meta_data", {}),
            "messages": conversation_data.get("messages", []),
        })
        
        return conversation["id"]
    
    def load_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a conversation from the database.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation data if found, None otherwise
        """
        return self.api.get_conversation(conversation_id)
    
    def save_user_model(self, username: str, model_data: Dict[str, Any]) -> bool:
        """
        Save a user model to the database.
        
        Args:
            username: Username
            model_data: User model data
            
        Returns:
            True if saved, False otherwise
        """
        user = self.api.get_user_by_username(username)
        if not user:
            # Create user if it doesn't exist
            user = self.api.create_user({
                "username": username,
                "name": model_data.get("name", username),
                "email": model_data.get("email"),
                "role": "user",
                "profile": {
                    "community_mastery": model_data.get("community_mastery", {}),
                    "entity_familiarity": model_data.get("entity_familiarity", {}),
                    "question_type_performance": model_data.get("question_type_performance", {}),
                    "difficulty_performance": model_data.get("difficulty_performance", {}),
                    "overall_mastery": model_data.get("overall_mastery", 0.0),
                    "mastered_objectives": model_data.get("mastered_objectives", []),
                    "current_objective": model_data.get("current_objective"),
                },
            })
            return True
        
        # Update user profile
        self.api.update_user(user["id"], {
            "profile": {
                "community_mastery": model_data.get("community_mastery", {}),
                "entity_familiarity": model_data.get("entity_familiarity", {}),
                "question_type_performance": model_data.get("question_type_performance", {}),
                "difficulty_performance": model_data.get("difficulty_performance", {}),
                "overall_mastery": model_data.get("overall_mastery", 0.0),
                "mastered_objectives": model_data.get("mastered_objectives", []),
                "current_objective": model_data.get("current_objective"),
            },
        })
        
        return True
    
    def load_user_model(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Load a user model from the database.
        
        Args:
            username: Username
            
        Returns:
            User model data if found, None otherwise
        """
        user = self.api.get_user_by_username(username)
        if not user:
            return None
        
        profile = user.get("profile")
        if not profile:
            return None
        
        # Convert to legacy format
        model_data = {
            "username": user["username"],
            "name": user["name"],
            "email": user["email"],
            "community_mastery": profile.get("community_mastery", {}),
            "entity_familiarity": profile.get("entity_familiarity", {}),
            "question_type_performance": profile.get("question_type_performance", {}),
            "difficulty_performance": profile.get("difficulty_performance", {}),
            "overall_mastery": profile.get("overall_mastery", 0.0),
            "mastered_objectives": profile.get("mastered_objectives", []),
            "current_objective": profile.get("current_objective"),
        }
        
        return model_data
