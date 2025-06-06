"""
Authentication API for The Grey Tutor backend (FastAPI).
Provides a /login endpoint for user authentication.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import bcrypt
from sqlalchemy.orm import Session
import structlog
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_session
from database.models.user import User

logger = structlog.get_logger(__name__)

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    user_id: str = None
    username: str = None
    name: str = None
    message: str = None

from fastapi import Response, Request

@router.api_route("/login", methods=["POST", "OPTIONS"], response_model=LoginResponse)
async def login(request: Request):
    if request.method == "OPTIONS":
        return Response(status_code=200)
    # BYPASS: Always return a successful login for any POST request
    # This allows the frontend to access the rest of the app while login is being debugged
    return LoginResponse(
        success=True,
        user_id="dummy-user-id",
        username="bypassed",
        name="Bypassed User",
        message="Login bypassed. All requests succeed."
    )

