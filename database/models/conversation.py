"""
Conversation models for The Grey Tutor.

This module contains SQLAlchemy models for conversation data.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship

from database.connection import Base


class Conversation(Base):
    """Conversation model."""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, ForeignKey("user_sessions.id"), nullable=True)
    conversation_type = Column(String, nullable=False)
    quiz_id = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    meta_data = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    session = relationship("UserSession", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    parameters = relationship("ConversationParameters", back_populates="conversation", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Conversation {self.id}>"


class Message(Base):
    """Message model."""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    meta_data = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    questions = relationship("Question", back_populates="message", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Message {self.id}>"


class Question(Base):
    """Question model."""
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    type = Column(String, nullable=False)
    difficulty = Column(Integer, nullable=False)
    entity = Column(String, nullable=False)
    tier = Column(String, nullable=True)
    options = Column(JSON, nullable=True)
    correct_answer = Column(String, nullable=True)
    community_id = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    message = relationship("Message", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Question {self.id}>"


class Answer(Base):
    """Answer model."""
    __tablename__ = "answers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    question_id = Column(String, ForeignKey("questions.id"), nullable=True)
    content = Column(Text, nullable=False)
    correct = Column(Boolean, nullable=True)
    quality_score = Column(Float, nullable=True)
    feedback = Column(JSON, nullable=True)
    
    # Relationships
    message = relationship("Message", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    
    def __repr__(self) -> str:
        return f"<Answer {self.id}>"


class ConversationParameters(Base):
    """Conversation parameters model."""
    __tablename__ = "conversation_parameters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    parameter_type = Column(String, nullable=False)
    max_communities = Column(Integer, nullable=True)
    max_path_length = Column(Integer, nullable=True)
    max_paths_per_entity = Column(Integer, nullable=True)
    use_cache = Column(Boolean, nullable=True)
    verbose = Column(Boolean, nullable=True)
    llm_model = Column(String, nullable=True)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    strategy = Column(String, nullable=True)
    tier = Column(String, nullable=True)
    use_llm = Column(Boolean, nullable=True)
    fussiness = Column(Integer, nullable=True)
    theme = Column(String, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="parameters")
    
    def __repr__(self) -> str:
        return f"<ConversationParameters {self.id}>"
