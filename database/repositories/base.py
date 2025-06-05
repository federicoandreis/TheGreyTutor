"""
Base repository for The Grey Tutor.

This module provides a base repository class for database access.
"""
from typing import Generic, TypeVar, Type, List, Optional, Any, Dict, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from database.connection import Base

# Type variable for SQLAlchemy models
T = TypeVar('T', bound=Base)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    """Base repository for database access."""
    
    def __init__(self, model: Type[T], db: Session):
        """
        Initialize the repository.
        
        Args:
            model: SQLAlchemy model class
            db: SQLAlchemy session
        """
        self.model = model
        self.db = db
    
    def get_by_id(self, id: str) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            id: Entity ID
            
        Returns:
            Entity if found, None otherwise
        """
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model.__name__} by ID: {e}")
            return None
    
    def get_all(self) -> List[T]:
        """
        Get all entities.
        
        Returns:
            List of entities
        """
        try:
            return self.db.query(self.model).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model.__name__}s: {e}")
            return []
    
    def create(self, entity: Union[T, Dict[str, Any]]) -> Optional[T]:
        """
        Create a new entity.
        
        Args:
            entity: Entity to create or dictionary of entity attributes
            
        Returns:
            Created entity if successful, None otherwise
        """
        try:
            if isinstance(entity, dict):
                entity = self.model(**entity)
            
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            self.db.rollback()
            return None
    
    def update(self, id: str, attributes: Dict[str, Any], pk_name: str = "id") -> Optional[T]:
        """
        Update an entity.
        Args:
            id: Entity ID (or primary key value)
            attributes: Dictionary of attributes to update
            pk_name: Name of the primary key field (default: 'id')
        Returns:
            Updated entity if successful, None otherwise
        Note:
            For models like UserProfile where the PK is not 'id', set pk_name appropriately (e.g., 'user_id').
        """
        try:
            entity = self.db.query(self.model).filter(getattr(self.model, pk_name) == id).first()
            if not entity:
                return None
            for key, value in attributes.items():
                setattr(entity, key, value)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            self.db.rollback()
            return None
    
    def delete(self, id: str) -> bool:
        """
        Delete an entity.
        
        Args:
            id: Entity ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            entity = self.get_by_id(id)
            if not entity:
                return False
            
            self.db.delete(entity)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            self.db.rollback()
            return False
    
    def count(self) -> int:
        """
        Count all entities.
        
        Returns:
            Number of entities
        """
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model.__name__}s: {e}")
            return 0
