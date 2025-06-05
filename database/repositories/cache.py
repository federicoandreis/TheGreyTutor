"""
Cache repository for The Grey Tutor.

This module provides repository classes for cache data.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

from database.models.cache import CacheEntry
from database.repositories.base import BaseRepository

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CacheRepository(BaseRepository[CacheEntry]):
    """Repository for cache data."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(CacheEntry, db)
    
    def get_by_key(self, cache_type: str, key: str) -> Optional[CacheEntry]:
        """
        Get a cache entry by type and key.
        
        Args:
            cache_type: Cache type
            key: Cache key
            
        Returns:
            Cache entry if found, None otherwise
        """
        try:
            entry = (
                self.db.query(CacheEntry)
                .filter(CacheEntry.cache_type == cache_type, CacheEntry.key == key)
                .first()
            )
            
            if entry:
                # Update last accessed time and access count
                entry.last_accessed = datetime.utcnow()
                entry.access_count += 1
                self.db.commit()
            
            return entry
        except SQLAlchemyError as e:
            logger.error(f"Error getting cache entry by key: {e}")
            self.db.rollback()
            return None
    
    def get_by_type(self, cache_type: str) -> List[CacheEntry]:
        """
        Get cache entries by type.
        
        Args:
            cache_type: Cache type
            
        Returns:
            List of cache entries
        """
        try:
            return self.db.query(CacheEntry).filter(CacheEntry.cache_type == cache_type).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting cache entries by type: {e}")
            return []
    
    def set(self, cache_type: str, key: str, value: Any) -> Optional[CacheEntry]:
        """
        Set a cache entry.
        
        Args:
            cache_type: Cache type
            key: Cache key
            value: Cache value
            
        Returns:
            Cache entry if successful, None otherwise
        """
        try:
            # Check if entry already exists
            entry = self.get_by_key(cache_type, key)
            
            if entry:
                # Update existing entry
                entry.value = value
                entry.last_accessed = datetime.utcnow()
                entry.access_count += 1
                self.db.commit()
                return entry
            else:
                # Create new entry
                entry = CacheEntry(
                    cache_type=cache_type,
                    key=key,
                    value=value,
                    created_at=datetime.utcnow(),
                    last_accessed=datetime.utcnow(),
                    access_count=1
                )
                self.db.add(entry)
                self.db.commit()
                self.db.refresh(entry)
                return entry
        except SQLAlchemyError as e:
            logger.error(f"Error setting cache entry: {e}")
            self.db.rollback()
            return None
    
    def delete_by_key(self, cache_type: str, key: str) -> bool:
        """
        Delete a cache entry by type and key.
        
        Args:
            cache_type: Cache type
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = (
                self.db.query(CacheEntry)
                .filter(CacheEntry.cache_type == cache_type, CacheEntry.key == key)
                .delete()
            )
            self.db.commit()
            return result > 0
        except SQLAlchemyError as e:
            logger.error(f"Error deleting cache entry by key: {e}")
            self.db.rollback()
            return False
    
    def delete_by_type(self, cache_type: str) -> bool:
        """
        Delete all cache entries of a specific type.
        
        Args:
            cache_type: Cache type
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.db.query(CacheEntry).filter(CacheEntry.cache_type == cache_type).delete()
            self.db.commit()
            return result > 0
        except SQLAlchemyError as e:
            logger.error(f"Error deleting cache entries by type: {e}")
            self.db.rollback()
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.db.query(CacheEntry).delete()
            self.db.commit()
            return result > 0
        except SQLAlchemyError as e:
            logger.error(f"Error clearing cache: {e}")
            self.db.rollback()
            return False
