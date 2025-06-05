"""
Test script for The Grey Tutor database connection.

This script tests the database connection and prints the database version.
"""
import logging
from sqlalchemy import text
from database.connection import get_db

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_connection() -> None:
    """Test the database connection."""
    try:
        # Get database session
        db = next(get_db())
        
        # Execute a simple query to get the PostgreSQL version
        result = db.execute(text("SELECT version()")).scalar()
        
        logger.info(f"Database connection successful!")
        logger.info(f"PostgreSQL version: {result}")
        
        # Close the session
        db.close()
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")


if __name__ == "__main__":
    test_connection()
