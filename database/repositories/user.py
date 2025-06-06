"""
User repositories for The Grey Tutor database.

This module provides repository classes for interacting with user models.
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.models.user import User, UserProfile, UserSession

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserRepository:
    """Repository for User model."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            username: Username
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: Email
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self) -> List[User]:
        """
        Get all users.
        
        Returns:
            List of users
        """
        return self.db.query(User).all()
    
    def create(self, data: Dict[str, Any]) -> User:
        """
        Create a new user.
        
        Args:
            data: User data
            
        Returns:
            Created user
        """
        try:
            user = User(**data)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    def update(self, user_id: str, data: Dict[str, Any]) -> Optional[User]:
        """
        Update a user.
        
        Args:
            user_id: User ID
            data: User data
            
        Returns:
            Updated user if found, None otherwise
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                return None
            
            for key, value in data.items():
                setattr(user, key, value)
            
            self.db.commit()
            self.db.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating user: {e}")
            raise
    
    def delete(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                return False
            
            self.db.delete(user)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting user: {e}")
            raise

class UserProfileRepository:
    """Repository for UserProfile model."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    def get_by_id(self, profile_id: str) -> Optional[UserProfile]:
        """
        Get a user profile by ID.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            UserProfile if found, None otherwise
        """
        return self.db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    
    def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """
        Get a user profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile if found, None otherwise
        """
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    def create(self, data: Dict[str, Any]) -> UserProfile:
        """
        Create a new user profile.
        
        Args:
            data: Profile data
            
        Returns:
            Created profile
        """
        try:
            profile = UserProfile(**data)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating user profile: {e}")
            raise
    
    def update(self, profile_id: str, data: Dict[str, Any]) -> Optional[UserProfile]:
        """
        Update a user profile.
        
        Args:
            profile_id: Profile ID
            data: Profile data
            
        Returns:
            Updated profile if found, None otherwise
        """
        try:
            profile = self.get_by_id(profile_id)
            if not profile:
                return None
            
            for key, value in data.items():
                setattr(profile, key, value)
            
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating user profile: {e}")
            raise
    
    def update_by_user_id(self, user_id: str, data: Dict[str, Any]) -> Optional[UserProfile]:
        """
        Update a user profile by user ID.
        
        Args:
            user_id: User ID
            data: Profile data
            
        Returns:
            Updated profile if found, None otherwise
        """
        try:
            profile = self.get_by_user_id(user_id)
            if not profile:
                return None
            
            for key, value in data.items():
                setattr(profile, key, value)
            
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating user profile: {e}")
            raise
    
    def update_overall_mastery(self, user_id: str, overall_mastery: float) -> Optional[UserProfile]:
        """
        Update a user profile's overall mastery.
        
        Args:
            user_id: User ID
            overall_mastery: Overall mastery
            
        Returns:
            Updated profile if found, None otherwise
        """
        try:
            profile = self.get_by_user_id(user_id)
            if not profile:
                return None
            
            profile.overall_mastery = overall_mastery
            profile.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(profile)
            return profile
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating user profile overall mastery: {e}")
            raise
    
    def delete(self, profile_id: str) -> bool:
        """
        Delete a user profile.
        
        Args:
            profile_id: Profile ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            profile = self.get_by_id(profile_id)
            if not profile:
                return False
            
            self.db.delete(profile)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting user profile: {e}")
            raise

class UserSessionRepository:
    """Repository for UserSession model."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    def get_by_id(self, session_id: str) -> Optional[UserSession]:
        """
        Get a user session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            UserSession if found, None otherwise
        """
        return self.db.query(UserSession).filter(UserSession.id == session_id).first()
    
    def get_by_user_id(self, user_id: str) -> List[UserSession]:
        """
        Get user sessions by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of UserSession
        """
        return self.db.query(UserSession).filter(UserSession.user_id == user_id).all()
    
    def get_active_by_user_id(self, user_id: str) -> List[UserSession]:
        """
        Get active user sessions by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active UserSession
        """
        return self.db.query(UserSession).filter(UserSession.user_id == user_id, UserSession.end_time == None).all()
    
    def create(self, data: Dict[str, Any]) -> UserSession:
        """
        Create a new user session.
        
        Args:
            data: Session data
            
        Returns:
            Created session
        """
        try:
            session = UserSession(**data)
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            return session
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating user session: {e}")
            raise
    
    def update(self, session_id: str, data: Dict[str, Any]) -> Optional[UserSession]:
        """
        Update a user session.
        
        Args:
            session_id: Session ID
            data: Session data
            
        Returns:
            Updated session if found, None otherwise
        """
        try:
            session = self.get_by_id(session_id)
            if not session:
                return None
            
            for key, value in data.items():
                setattr(session, key, value)
            
            self.db.commit()
            self.db.refresh(session)
            return session
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating user session: {e}")
            raise
    
    def end_session(self, session_id: str, data: Dict[str, Any] = None) -> Optional[UserSession]:
        """
        End a user session.
        
        Args:
            session_id: Session ID
            data: Session data (optional)
            
        Returns:
            Updated session if found, None otherwise
        """
        try:
            session = self.get_by_id(session_id)
            if not session:
                return None
            
            # Update session data
            if data:
                for key, value in data.items():
                    setattr(session, key, value)
            
            # Set end time if not set
            if not session.end_time:
                session.end_time = datetime.utcnow()
            
            # Calculate accuracy
            if session.questions_asked > 0:
                session.accuracy = session.correct_answers / session.questions_asked
            
            self.db.commit()
            self.db.refresh(session)
            return session
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error ending user session: {e}")
            raise
    
    def delete(self, session_id: str) -> bool:
        """
        Delete a user session.
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            session = self.get_by_id(session_id)
            if not session:
                return False
            
            self.db.delete(session)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting user session: {e}")
            raise
