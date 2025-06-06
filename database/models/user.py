"""
User models for The Grey Tutor database.

This module defines the SQLAlchemy models for users, user profiles, and user sessions.
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from database.connection import Base
from .conversation import Conversation

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)
    name = Column(String, nullable=True)
    role = Column(String, nullable=False, default="user")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', role='{self.role}')>"

class UserProfile(Base):
    """User profile model."""
    
    __tablename__ = "user_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    community_mastery = Column(JSON, nullable=False, default=dict)
    entity_familiarity = Column(JSON, nullable=False, default=dict)
    question_type_performance = Column(JSON, nullable=False, default=dict)
    difficulty_performance = Column(JSON, nullable=False, default=dict)
    overall_mastery = Column(Float, nullable=False, default=0.0)
    mastered_objectives = Column(JSON, nullable=False, default=list)
    current_objective = Column(String, nullable=True)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile(id='{self.id}', user_id='{self.user_id}', overall_mastery={self.overall_mastery})>"

class UserSession(Base):
    """User session model."""
    
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_type = Column(String, nullable=False, default="quiz")
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    questions_asked = Column(Integer, nullable=False, default=0)
    correct_answers = Column(Integer, nullable=False, default=0)
    accuracy = Column(Float, nullable=False, default=0.0)
    mastery_before = Column(Float, nullable=False, default=0.0)
    mastery_after = Column(Float, nullable=False, default=0.0)
    strategy = Column(String, nullable=True)
    theme = Column(String, nullable=True)
    fussiness = Column(Integer, nullable=True)
    tier = Column(String, nullable=True)
    use_llm = Column(Boolean, nullable=True)
    parameters = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    conversations = relationship("Conversation", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserSession(id='{self.id}', user_id='{self.user_id}', session_type='{self.session_type}')>"
