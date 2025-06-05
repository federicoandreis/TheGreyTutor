"""
Cache models for The Grey Tutor.

This module contains SQLAlchemy models for cache data.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.orm import relationship

from database.connection import Base


class CacheEntry(Base):
    """Cache entry model."""
    __tablename__ = "cache_entries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cache_type = Column(String, nullable=False)
    key = Column(String, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=False, default=datetime.utcnow)
    access_count = Column(Integer, nullable=False, default=0)
    
    def __repr__(self) -> str:
        return f"<CacheEntry {self.id}>"
