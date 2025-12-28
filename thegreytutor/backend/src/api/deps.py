"""
API Dependencies for FastAPI.

Provides dependency injection for authentication, database sessions, etc.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import structlog

from ..services.auth_service import auth_service
from ..database.connection import get_db

logger = structlog.get_logger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Get the current authenticated user's ID from JWT token.
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        
    Returns:
        User ID string
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = auth_service.verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Get the current user's ID if authenticated, None otherwise.
    
    This is useful for endpoints that work for both authenticated and anonymous users.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = auth_service.verify_token(token, token_type="access")
    
    if not payload:
        return None
    
    return payload.get("sub")


async def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Get the full token payload for the current user.
    
    Returns:
        Dictionary with user_id, email, role, etc.
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = auth_service.verify_token(token, token_type="access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.
    
    Args:
        required_role: The role required to access the endpoint
        
    Returns:
        Dependency function that validates the user's role
    """
    async def role_checker(payload: dict = Depends(get_current_user_payload)) -> dict:
        user_role = payload.get("role", "user")
        if user_role != required_role and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return payload
    
    return role_checker
