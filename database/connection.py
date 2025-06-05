"""
Database connection module for The Grey Tutor.

This module provides functions for connecting to the PostgreSQL database
using SQLAlchemy.
"""
import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Get database connection parameters from environment variables
DB_USER = os.getenv("DB_USER", "thegreytutor")
DB_PASSWORD = os.getenv("DB_PASSWORD", "thegreytutor")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "thegreytutor")

# Create SQLAlchemy engine
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


from contextlib import contextmanager

def get_db():
    """
    Get a database session as a generator.
    Usage:
        db = next(get_db())
        ...
        db.close()
    Or:
        with get_db() as db:
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database.
    
    This function creates all tables defined in the models.
    """
    # Import all models to ensure they are registered with the Base
    from database.models.user import User, UserProfile, UserSession
    from database.models.conversation import (
        Conversation, Message, Question, Answer, ConversationParameters
    )
    from database.models.cache import CacheEntry
    
    # Create tables
    Base.metadata.create_all(bind=engine)
