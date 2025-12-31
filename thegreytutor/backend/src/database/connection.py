"""
Database connection module for The Grey Tutor backend.

Provides database session management and dependency injection for FastAPI.
"""

from typing import Generator
from sqlalchemy.orm import Session
import structlog

# Import from the main database module
from database.connection import SessionLocal, create_tables, check_connection, get_db_session

logger = structlog.get_logger(__name__)


async def init_db():
    """Initialize database connection and create tables if needed."""
    try:
        create_tables()
        if check_connection():
            logger.info("Database connection established")
        else:
            logger.warning("Database connection check failed")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def close_db():
    """Close database connections."""
    logger.info("Database connections closed")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    
    Yields:
        SQLAlchemy Session object
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
