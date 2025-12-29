"""
Authentication API routes.

Provides endpoints for user registration, login, token refresh, and logout.
"""

from datetime import datetime
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import structlog

from ..schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    AuthResponse,
    LogoutRequest,
    PasswordChangeRequest,
    UserUpdateRequest,
    ErrorResponse,
)
from ..deps import get_current_user_id, get_current_user_payload
from ...services.auth_service import auth_service
from ...database.connection import get_db

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    Creates a new user account with the provided credentials.
    Returns access and refresh tokens upon successful registration.
    """
    from database.models.user import User, UserProfile
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == request.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    password_hash = auth_service.hash_password(request.password)
    
    new_user = User(
        id=user_id,
        username=request.username,
        email=request.email,
        password_hash=password_hash,
        name=request.name or request.username,
        role="user",
        created_at=datetime.utcnow(),
    )
    
    # Create user profile
    new_profile = UserProfile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        overall_mastery=0.0,
        last_updated=datetime.utcnow(),
    )
    
    try:
        db.add(new_user)
        db.add(new_profile)
        db.commit()
        db.refresh(new_user)
        
        logger.info("User registered", user_id=user_id, username=request.username)
        
    except Exception as e:
        db.rollback()
        logger.error("Registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account"
        )
    
    # Generate tokens
    tokens = auth_service.generate_token_pair(user_id, request.email, "user")
    
    return AuthResponse(
        success=True,
        message="Registration successful. Welcome to The Grey Tutor!",
        user=UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            name=new_user.name,
            role=new_user.role,
            created_at=new_user.created_at,
            last_login=None,
        ),
        tokens=TokenResponse(**tokens),
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user.
    
    Validates credentials and returns access and refresh tokens.
    """
    from database.models.user import User
    
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        logger.warning("Login attempt for non-existent email", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not user.password_hash or not auth_service.verify_password(request.password, user.password_hash):
        logger.warning("Failed login attempt", user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info("User logged in", user_id=user.id, username=user.username)
    
    # Generate tokens
    tokens = auth_service.generate_token_pair(user.id, user.email, user.role)
    
    return AuthResponse(
        success=True,
        message="Login successful. Welcome back!",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            name=user.name,
            role=user.role,
            created_at=user.created_at,
            last_login=user.last_login,
        ),
        tokens=TokenResponse(**tokens),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using a valid refresh token.
    """
    from database.models.user import User
    
    # Verify refresh token
    payload = auth_service.verify_token(request.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    logger.info("Token refreshed", user_id=user_id)
    
    # Generate new token pair
    tokens = auth_service.generate_token_pair(user.id, user.email, user.role)
    
    return TokenResponse(**tokens)


@router.post("/logout")
async def logout(
    request: LogoutRequest = None,
    user_id: str = Depends(get_current_user_id)
):
    """
    Logout the current user.
    
    Invalidates the refresh token if provided.
    """
    # In a full implementation, we would add the refresh token to a blacklist
    # For now, we just acknowledge the logout
    logger.info("User logged out", user_id=user_id)
    
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get the current authenticated user's profile.
    """
    from database.models.user import User
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.name,
        role=user.role,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UserUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile information.

    Allows updating username, email, name, and avatar.
    """
    from database.models.user import User

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if new username is already taken by another user
    if request.username and request.username != user.username:
        existing_user = db.query(User).filter(
            User.username == request.username,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

    # Check if new email is already taken by another user
    if request.email and request.email != user.email:
        existing_email = db.query(User).filter(
            User.email == request.email,
            User.id != user_id
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Update user fields if provided
    if request.username is not None:
        user.username = request.username
    if request.email is not None:
        user.email = request.email
    if request.name is not None:
        user.name = request.name
    if request.avatar is not None:
        user.avatar = request.avatar

    try:
        db.commit()
        db.refresh(user)
        logger.info("Profile updated", user_id=user_id, fields_updated={
            "username": request.username is not None,
            "email": request.email is not None,
            "name": request.name is not None,
            "avatar": request.avatar is not None
        })
    except Exception as e:
        db.rollback()
        logger.error("Profile update failed", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        name=user.name,
        avatar=user.avatar,
        role=user.role,
        created_at=user.created_at,
        last_login=user.last_login,
    )


@router.put("/me/password")
async def change_password(
    request: PasswordChangeRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Change the current user's password.
    """
    from database.models.user import User

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify current password
    if not auth_service.verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    user.password_hash = auth_service.hash_password(request.new_password)
    db.commit()

    logger.info("Password changed", user_id=user_id)

    return {"success": True, "message": "Password changed successfully"}
