"""
User repository for The Grey Tutor.

This module provides repository classes for user data.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from database.models.user import User, UserProfile, UserSession
from database.repositories.base import BaseRepository

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for user data."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(User, db)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            username: Username
            
        Returns:
            User if found, None otherwise
        """
        try:
            return self.db.query(User).filter(User.username == username).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: Email address
            
        Returns:
            User if found, None otherwise
        """
        try:
            return self.db.query(User).filter(User.email == email).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    def create_with_profile(self, user_data: Dict[str, Any], profile_data: Dict[str, Any]) -> Optional[User]:
        """
        Create a new user with a profile.
        
        Args:
            user_data: User data
            profile_data: Profile data
            
        Returns:
            Created user if successful, None otherwise
        """
        try:
            user = User(**user_data)
            self.db.add(user)
            self.db.flush()  # Flush to get the user ID
            
            profile = UserProfile(user_id=user.id, **profile_data)
            self.db.add(profile)
            
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            logger.error(f"Error creating user with profile: {e}")
            self.db.rollback()
            return None


class UserProfileRepository(BaseRepository[UserProfile]):
    """Repository for user profile data."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(UserProfile, db)
    
    def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """
        Get a user profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User profile if found, None otherwise
        """
        try:
            return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user profile by user ID: {e}")
            return None


class UserSessionRepository(BaseRepository[UserSession]):
    """Repository for user session data."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        super().__init__(UserSession, db)
    
    def get_by_user_id(self, user_id: str) -> List[UserSession]:
        """
        Get user sessions by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of user sessions
        """
        try:
            return self.db.query(UserSession).filter(UserSession.user_id == user_id).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user sessions by user ID: {e}")
            return []
    
    def get_active_sessions(self, user_id: Optional[str] = None) -> List[UserSession]:
        """
        Get active user sessions.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            List of active user sessions
        """
        try:
            query = self.db.query(UserSession).filter(UserSession.end_time.is_(None))
            
            if user_id:
                query = query.filter(UserSession.user_id == user_id)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active user sessions: {e}")
            return []
