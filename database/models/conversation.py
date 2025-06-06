"""
Conversation models for The Grey Tutor database.

This module defines the SQLAlchemy models for conversations, messages, questions, and answers.
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from database.connection import Base

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Conversation(Base):
    """Conversation model."""
    
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, ForeignKey("user_sessions.id"), nullable=True)
    conversation_type = Column(String, nullable=False, default="chat")
    quiz_id = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    meta_data = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    session = relationship("UserSession", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    parameters = relationship("ConversationParameters", back_populates="conversation", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id='{self.id}', user_id='{self.user_id}', conversation_type='{self.conversation_type}')>"

class ConversationParameters(Base):
    """Conversation parameters model."""
    
    __tablename__ = "conversation_parameters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, unique=True)
    mode = Column(String, nullable=False, default="chat")
    strategy = Column(String, nullable=False, default="default")
    theme = Column(String, nullable=True)
    fussiness = Column(Integer, nullable=True)
    tier = Column(String, nullable=True)
    use_llm = Column(Boolean, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="parameters")
    
    def __repr__(self):
        return f"<ConversationParameters(id='{self.id}', conversation_id='{self.conversation_id}', mode='{self.mode}')>"

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
    question = relationship("Question", back_populates="message", uselist=False, cascade="all, delete-orphan")
    answer = relationship("Answer", back_populates="message", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Message(id='{self.id}', conversation_id='{self.conversation_id}', role='{self.role}')>"

class Question(Base):
    """Question model."""
    
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"), nullable=False, unique=True)
    type = Column(String, nullable=False, default="multiple_choice")
    difficulty = Column(String, nullable=False, default="medium")
    entity = Column(String, nullable=True)
    tier = Column(String, nullable=True)
    options = Column(JSON, nullable=True)
    correct_answer = Column(String, nullable=True)
    community_id = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=False, default=dict)
    
    # Relationships
    message = relationship("Message", back_populates="question")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Question(id='{self.id}', message_id='{self.message_id}', type='{self.type}')>"

class Answer(Base):
    """Answer model."""
    
    __tablename__ = "answers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"), nullable=False, unique=True)
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    content = Column(Text, nullable=False)
    correct = Column(Boolean, nullable=True)
    quality_score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    
    # Relationships
    message = relationship("Message", back_populates="answer")
    question = relationship("Question", back_populates="answers")
    
    def __repr__(self):
        return f"<Answer(id='{self.id}', message_id='{self.message_id}', question_id='{self.question_id}')>"
