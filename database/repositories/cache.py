"""
Cache repositories for The Grey Tutor database.

This module provides repository classes for interacting with cache models.
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models.cache import Cache, QuestionCache, AssessmentCache

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CacheRepository:
    """Repository for Cache model."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    def get_by_id(self, cache_id: str) -> Optional[Cache]:
        """
        Get a cache entry by ID.
        
        Args:
            cache_id: Cache ID
            
        Returns:
            Cache if found, None otherwise
        """
        return self.db.query(Cache).filter(Cache.id == cache_id).first()
    
    def get_by_key(self, cache_type: str, key: str) -> Optional[Cache]:
        """
        Get a cache entry by type and key.
        
        Args:
            cache_type: Cache type
            key: Cache key
            
        Returns:
            Cache if found, None otherwise
        """
        return self.db.query(Cache).filter(Cache.cache_type == cache_type, Cache.key == key).first()
    
    def get_by_type(self, cache_type: str) -> List[Cache]:
        """
        Get cache entries by type.
        
        Args:
            cache_type: Cache type
            
        Returns:
            List of Cache
        """
        return self.db.query(Cache).filter(Cache.cache_type == cache_type).all()
    
    def create(self, data: Dict[str, Any]) -> Cache:
        """
        Create a new cache entry.
        
        Args:
            data: Cache data
            
        Returns:
            Created cache entry
        """
        try:
            cache = Cache(**data)
            self.db.add(cache)
            self.db.commit()
            self.db.refresh(cache)
            return cache
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating cache entry: {e}")
            raise
    
    def update(self, cache_id: str, data: Dict[str, Any]) -> Optional[Cache]:
        """
        Update a cache entry.
        
        Args:
            cache_id: Cache ID
            data: Cache data
            
        Returns:
            Updated cache entry if found, None otherwise
        """
        try:
            cache = self.get_by_id(cache_id)
            if not cache:
                return None
            
            for key, value in data.items():
                setattr(cache, key, value)
            
            self.db.commit()
            self.db.refresh(cache)
            return cache
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating cache entry: {e}")
            raise
    
    def update_by_key(self, cache_type: str, key: str, value: Any) -> Optional[Cache]:
        """
        Update a cache entry by type and key.
        
        Args:
            cache_type: Cache type
            key: Cache key
            value: Cache value
            
        Returns:
            Updated cache entry if found, None otherwise
        """
        try:
            cache = self.get_by_key(cache_type, key)
            if not cache:
                return None
            
            cache.value = value
            cache.last_accessed = datetime.utcnow()
            cache.access_count += 1
            
            self.db.commit()
            self.db.refresh(cache)
            return cache
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating cache entry by key: {e}")
            raise
    
    def get_or_create(self, cache_type: str, key: str, default_value: Any = None) -> Cache:
        """
        Get a cache entry by type and key, or create it if it doesn't exist.
        
        Args:
            cache_type: Cache type
            key: Cache key
            default_value: Default value if cache entry doesn't exist
            
        Returns:
            Cache entry
        """
        try:
            cache = self.get_by_key(cache_type, key)
            if cache:
                cache.last_accessed = datetime.utcnow()
                cache.access_count += 1
                self.db.commit()
                self.db.refresh(cache)
                return cache
            
            # Create new cache entry
            cache_data = {
                "cache_type": cache_type,
                "key": key,
                "value": default_value if default_value is not None else {},
            }
            return self.create(cache_data)
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error getting or creating cache entry: {e}")
            raise
    
    def delete(self, cache_id: str) -> bool:
        """
        Delete a cache entry.
        
        Args:
            cache_id: Cache ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            cache = self.get_by_id(cache_id)
            if not cache:
                return False
            
            self.db.delete(cache)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting cache entry: {e}")
            raise
    
    def delete_by_key(self, cache_type: str, key: str) -> bool:
        """
        Delete a cache entry by type and key.
        
        Args:
            cache_type: Cache type
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            cache = self.get_by_key(cache_type, key)
            if not cache:
                return False
            
            self.db.delete(cache)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting cache entry by key: {e}")
            raise
    
    def delete_by_type(self, cache_type: str) -> int:
        """
        Delete cache entries by type.
        
        Args:
            cache_type: Cache type
            
        Returns:
            Number of deleted entries
        """
        try:
            count = self.db.query(Cache).filter(Cache.cache_type == cache_type).delete()
            self.db.commit()
            return count
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting cache entries by type: {e}")
            raise

class QuestionCacheRepository:
    """Repository for QuestionCache model."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    def get_by_id(self, cache_id: str) -> Optional[QuestionCache]:
        """
        Get a question cache entry by ID.
        
        Args:
            cache_id: Cache ID
            
        Returns:
            QuestionCache if found, None otherwise
        """
        return self.db.query(QuestionCache).filter(QuestionCache.id == cache_id).first()
    
    def get_by_question_id(self, question_id: str) -> Optional[QuestionCache]:
        """
        Get a question cache entry by question ID.
        
        Args:
            question_id: Question ID
            
        Returns:
            QuestionCache if found, None otherwise
        """
        return self.db.query(QuestionCache).filter(QuestionCache.question_id == question_id).first()
    
    def get_by_entity(self, entity: str) -> List[QuestionCache]:
        """
        Get question cache entries by entity.
        
        Args:
            entity: Entity
            
        Returns:
            List of QuestionCache
        """
        return self.db.query(QuestionCache).filter(QuestionCache.entity == entity).all()
    
    def get_by_community_id(self, community_id: str) -> List[QuestionCache]:
        """
        Get question cache entries by community ID.
        
        Args:
            community_id: Community ID
            
        Returns:
            List of QuestionCache
        """
        return self.db.query(QuestionCache).filter(QuestionCache.community_id == community_id).all()
    
    def create(self, data: Dict[str, Any]) -> QuestionCache:
        """
        Create a new question cache entry.
        
        Args:
            data: Question cache data
            
        Returns:
            Created question cache entry
        """
        try:
            cache = QuestionCache(**data)
            self.db.add(cache)
            self.db.commit()
            self.db.refresh(cache)
            return cache
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating question cache entry: {e}")
            raise
    
    def update(self, cache_id: str, data: Dict[str, Any]) -> Optional[QuestionCache]:
        """
        Update a question cache entry.
        
        Args:
            cache_id: Cache ID
            data: Question cache data
            
        Returns:
            Updated question cache entry if found, None otherwise
        """
        try:
            cache = self.get_by_id(cache_id)
            if not cache:
                return None
            
            for key, value in data.items():
                setattr(cache, key, value)
            
            cache.last_accessed = datetime.utcnow()
            cache.access_count += 1
            
            self.db.commit()
            self.db.refresh(cache)
            return cache
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating question cache entry: {e}")
            raise
    
    def delete(self, cache_id: str) -> bool:
        """
        Delete a question cache entry.
        
        Args:
            cache_id: Cache ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            cache = self.get_by_id(cache_id)
            if not cache:
                return False
            
            self.db.delete(cache)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting question cache entry: {e}")
            raise
    
    def delete_by_question_id(self, question_id: str) -> bool:
        """
        Delete a question cache entry by question ID.
        
        Args:
            question_id: Question ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            cache = self.get_by_question_id(question_id)
            if not cache:
                return False
            
            self.db.delete(cache)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting question cache entry by question ID: {e}")
            raise

class AssessmentCacheRepository:
    """Repository for AssessmentCache model."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    def get_by_id(self, cache_id: str) -> Optional[AssessmentCache]:
        """
        Get an assessment cache entry by ID.
        
        Args:
            cache_id: Cache ID
            
        Returns:
            AssessmentCache if found, None otherwise
        """
        return self.db.query(AssessmentCache).filter(AssessmentCache.id == cache_id).first()
    
    def get_by_assessment_id(self, assessment_id: str) -> Optional[AssessmentCache]:
        """
        Get an assessment cache entry by assessment ID.
        
        Args:
            assessment_id: Assessment ID
            
        Returns:
            AssessmentCache if found, None otherwise
        """
        return self.db.query(AssessmentCache).filter(AssessmentCache.assessment_id == assessment_id).first()
    
    def get_by_user_id(self, user_id: str) -> List[AssessmentCache]:
        """
        Get assessment cache entries by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of AssessmentCache
        """
        return self.db.query(AssessmentCache).filter(AssessmentCache.user_id == user_id).all()
    
    def create(self, data: Dict[str, Any]) -> AssessmentCache:
        """
        Create a new assessment cache entry.
        
        Args:
            data: Assessment cache data
            
        Returns:
            Created assessment cache entry
        """
        try:
            cache = AssessmentCache(**data)
            self.db.add(cache)
            self.db.commit()
            self.db.refresh(cache)
            return cache
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating assessment cache entry: {e}")
            raise
    
    def update(self, cache_id: str, data: Dict[str, Any]) -> Optional[AssessmentCache]:
        """
        Update an assessment cache entry.
        
        Args:
            cache_id: Cache ID
            data: Assessment cache data
            
        Returns:
            Updated assessment cache entry if found, None otherwise
        """
        try:
            cache = self.get_by_id(cache_id)
            if not cache:
                return None
            
            for key, value in data.items():
                setattr(cache, key, value)
            
            cache.last_accessed = datetime.utcnow()
            cache.access_count += 1
            
            self.db.commit()
            self.db.refresh(cache)
            return cache
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating assessment cache entry: {e}")
            raise
    
    def delete(self, cache_id: str) -> bool:
        """
        Delete an assessment cache entry.
        
        Args:
            cache_id: Cache ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            cache = self.get_by_id(cache_id)
            if not cache:
                return False
            
            self.db.delete(cache)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting assessment cache entry: {e}")
            raise
    
    def delete_by_assessment_id(self, assessment_id: str) -> bool:
        """
        Delete an assessment cache entry by assessment ID.
        
        Args:
            assessment_id: Assessment ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            cache = self.get_by_assessment_id(assessment_id)
            if not cache:
                return False
            
            self.db.delete(cache)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting assessment cache entry by assessment ID: {e}")
            raise
