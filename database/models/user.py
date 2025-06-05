"""
User models for The Grey Tutor.

This module contains SQLAlchemy models for user data.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from database.connection import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    role = Column(String, nullable=False, default="user")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    sessions = relationship("UserSession", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"


class UserProfile(Base):
    """User profile model."""
    __tablename__ = "user_profiles"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
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
    
    def __repr__(self) -> str:
        return f"<UserProfile {self.user_id}>"


class UserSession(Base):
    """User session model."""
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_type = Column(String, nullable=False)
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
    use_llm = Column(Boolean, nullable=False, default=True)
    parameters = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    conversations = relationship("Conversation", back_populates="session")
    
    def __repr__(self) -> str:
        return f"<UserSession {self.id}>"
