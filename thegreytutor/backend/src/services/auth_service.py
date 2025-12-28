"""
Authentication Service for The Grey Tutor.

Provides secure password hashing (Argon2) and JWT token management.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import uuid
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import structlog

from ..core.config import settings

logger = structlog.get_logger(__name__)

# Password hashing context using Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# JWT Configuration
ALGORITHM = "HS256"


class AuthService:
    """Service for authentication operations."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using Argon2.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hash to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error("Password verification error", error=str(e))
            return False
    
    @staticmethod
    def create_access_token(
        user_id: str,
        email: str,
        role: str = "user",
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: User's unique identifier
            email: User's email
            role: User's role (default: "user")
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": user_id,
            "email": email,
            "role": role,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4()),  # JWT ID for token revocation
        }
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user_id: str) -> Tuple[str, datetime]:
        """
        Create a refresh token.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Tuple of (encoded JWT token, expiration datetime)
        """
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4()),
        }
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt, expire
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            
            # Verify token type
            if payload.get("type") != token_type:
                logger.warning("Token type mismatch", expected=token_type, got=payload.get("type"))
                return None
            
            # Verify expiration
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                logger.warning("Token expired")
                return None
            
            return payload
            
        except JWTError as e:
            logger.warning("JWT verification failed", error=str(e))
            return None
    
    @staticmethod
    def generate_token_pair(user_id: str, email: str, role: str = "user") -> dict:
        """
        Generate both access and refresh tokens.
        
        Args:
            user_id: User's unique identifier
            email: User's email
            role: User's role
            
        Returns:
            Dictionary with access_token, refresh_token, token_type, and expires_in
        """
        access_token = AuthService.create_access_token(user_id, email, role)
        refresh_token, refresh_expires = AuthService.create_refresh_token(user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
            "refresh_expires_at": refresh_expires.isoformat(),
        }


# Singleton instance
auth_service = AuthService()
