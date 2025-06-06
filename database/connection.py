"""
Database connection module for The Grey Tutor.

This module provides functions for connecting to the database and managing sessions.
"""
import logging
import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///thegreytutor.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_session() -> Session:
    """
    Get a database session.
    
    Returns:
        Database session
    """
    return SessionLocal()

def close_db_session(db: Session) -> None:
    """
    Close a database session.
    
    Args:
        db: Database session
    """
    db.close()

def create_tables() -> None:
    """
    Create all tables in the database.
    """
    # Import models to ensure they are registered with Base
    from database.models.user import User, UserProfile, UserSession
    from database.models.conversation import Conversation, ConversationParameters, Message, Question, Answer
    from database.models.cache import Cache, QuestionCache, AssessmentCache
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

def drop_tables() -> None:
    """
    Drop all tables in the database.
    """
    # Import models to ensure they are registered with Base
    from database.models.user import User, UserProfile, UserSession
    from database.models.conversation import Conversation, ConversationParameters, Message, Question, Answer
    from database.models.cache import Cache, QuestionCache, AssessmentCache
    
    # Drop tables
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped")

def reset_database() -> None:
    """
    Reset the database by dropping and recreating all tables.
    """
    drop_tables()
    create_tables()
    logger.info("Database reset")

def check_connection() -> bool:
    """
    Check if the database connection is working.
    
    Returns:
        True if the connection is working, False otherwise
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
