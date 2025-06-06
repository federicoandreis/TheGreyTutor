"""
Cache models for The Grey Tutor database.

This module defines the SQLAlchemy models for caching data.
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


class Cache(Base):
    """Cache model."""
    
    __tablename__ = "cache"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cache_type = Column(String, nullable=False, index=True)
    key = Column(String, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=False, default=datetime.utcnow)
    access_count = Column(Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f"<Cache(id='{self.id}', cache_type='{self.cache_type}', key='{self.key}')>"

class QuestionCache(Base):
    """Question cache model."""
    
    __tablename__ = "question_cache"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String, nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False, default="multiple_choice")
    difficulty = Column(String, nullable=False, default="medium")
    entity = Column(String, nullable=True, index=True)
    tier = Column(String, nullable=True, index=True)
    options = Column(JSON, nullable=True)
    correct_answer = Column(String, nullable=True)
    community_id = Column(String, nullable=True, index=True)
    meta_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=False, default=datetime.utcnow)
    access_count = Column(Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f"<QuestionCache(id='{self.id}', question_id='{self.question_id}', question_type='{self.question_type}')>"

class AssessmentCache(Base):
    """Assessment cache model."""
    
    __tablename__ = "assessment_cache"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=True, index=True)
    assessment_type = Column(String, nullable=False, default="quiz")
    questions = Column(JSON, nullable=False, default=list)
    answers = Column(JSON, nullable=False, default=list)
    score = Column(Float, nullable=False, default=0.0)
    max_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=False, default=datetime.utcnow)
    access_count = Column(Integer, nullable=False, default=0)
    
    def __repr__(self):
        return f"<AssessmentCache(id='{self.id}', assessment_id='{self.assessment_id}', assessment_type='{self.assessment_type}')>"
