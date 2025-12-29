"""
Tests for authentication service and API endpoints.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.models.user import User, UserProfile


class TestAuthService:
    """Tests for the AuthService class."""
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed and verified."""
        from src.services.auth_service import auth_service
        
        password = "TestPassword123"
        hashed = auth_service.hash_password(password)
        
        # Hash should be different from original
        assert hashed != password
        
        # Should verify correctly
        assert auth_service.verify_password(password, hashed) is True
        
        # Wrong password should fail
        assert auth_service.verify_password("WrongPassword123", hashed) is False
    
    def test_access_token_creation(self):
        """Test JWT access token creation."""
        from src.services.auth_service import auth_service
        
        user_id = "test-user-123"
        email = "test@example.com"
        role = "user"
        
        token = auth_service.create_access_token(user_id, email, role)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Token should be verifiable
        payload = auth_service.verify_token(token, token_type="access")
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["role"] == role
        assert payload["type"] == "access"
    
    def test_refresh_token_creation(self):
        """Test JWT refresh token creation."""
        from src.services.auth_service import auth_service
        
        user_id = "test-user-123"
        
        token, expires = auth_service.create_refresh_token(user_id)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Expiration should be in the future
        assert expires > datetime.utcnow()
        
        # Token should be verifiable
        payload = auth_service.verify_token(token, token_type="refresh")
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
    
    def test_token_pair_generation(self):
        """Test generation of access and refresh token pair."""
        from src.services.auth_service import auth_service
        
        user_id = "test-user-123"
        email = "test@example.com"
        role = "admin"
        
        tokens = auth_service.generate_token_pair(user_id, email, role)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert "expires_in" in tokens
        assert "refresh_expires_at" in tokens
    
    def test_invalid_token_verification(self):
        """Test that invalid tokens are rejected."""
        from src.services.auth_service import auth_service
        
        # Invalid token string
        result = auth_service.verify_token("invalid-token-string", "access")
        assert result is None
        
        # Empty token
        result = auth_service.verify_token("", "access")
        assert result is None
    
    def test_token_type_mismatch(self):
        """Test that token type verification works."""
        from src.services.auth_service import auth_service
        
        # Create access token but verify as refresh
        access_token = auth_service.create_access_token("user-123", "test@example.com", "user")
        result = auth_service.verify_token(access_token, token_type="refresh")
        assert result is None
        
        # Create refresh token but verify as access
        refresh_token, _ = auth_service.create_refresh_token("user-123")
        result = auth_service.verify_token(refresh_token, token_type="access")
        assert result is None


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database override."""
    from src.main import app
    from src.database.connection import get_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


class TestAuthEndpoints:
    """Tests for authentication API endpoints."""
    
    def test_register_success(self, client, test_db):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
                "name": "Test User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
        assert "access_token" in data["tokens"]
        assert "refresh_token" in data["tokens"]
    
    def test_register_duplicate_email(self, client, test_db):
        """Test registration with duplicate email fails."""
        # Register first user
        client.post(
            "/auth/register",
            json={
                "username": "testuser1",
                "email": "test@example.com",
                "password": "TestPass123",
            }
        )
        
        # Try to register with same email
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser2",
                "email": "test@example.com",
                "password": "TestPass123",
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_register_duplicate_username(self, client, test_db):
        """Test registration with duplicate username fails."""
        # Register first user
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test1@example.com",
                "password": "TestPass123",
            }
        )
        
        # Try to register with same username
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test2@example.com",
                "password": "TestPass123",
            }
        )
        
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"]
    
    def test_register_weak_password(self, client, test_db):
        """Test registration with weak password fails."""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "weak",
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_login_success(self, client, test_db):
        """Test successful login."""
        # Register first
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
            }
        )
        
        # Login
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPass123",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["email"] == "test@example.com"
        assert "access_token" in data["tokens"]
    
    def test_login_wrong_password(self, client, test_db):
        """Test login with wrong password fails."""
        # Register first
        client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
            }
        )
        
        # Login with wrong password
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123",
            }
        )
        
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client, test_db):
        """Test login with non-existent user fails."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "TestPass123",
            }
        )
        
        assert response.status_code == 401
    
    def test_get_current_user(self, client, test_db):
        """Test getting current user profile."""
        # Register and get token
        register_response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
            }
        )
        
        token = register_response.json()["tokens"]["access_token"]
        
        # Get current user
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
    
    def test_get_current_user_no_auth(self, client, test_db):
        """Test getting current user without auth fails."""
        response = client.get("/auth/me")
        
        assert response.status_code == 401
    
    def test_refresh_token(self, client, test_db):
        """Test token refresh."""
        # Register and get tokens
        register_response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
            }
        )
        
        refresh_token = register_response.json()["tokens"]["refresh_token"]
        
        # Refresh token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_refresh_token_invalid(self, client, test_db):
        """Test refresh with invalid token fails."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid-token"}
        )
        
        assert response.status_code == 401
    
    def test_change_password(self, client, test_db):
        """Test password change."""
        # Register
        register_response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
            }
        )
        
        token = register_response.json()["tokens"]["access_token"]
        
        # Change password
        response = client.put(
            "/auth/me/password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "TestPass123",
                "new_password": "NewTestPass456",
            }
        )
        
        assert response.status_code == 200
        
        # Login with new password
        login_response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "NewTestPass456",
            }
        )
        
        assert login_response.status_code == 200
    
    def test_change_password_wrong_current(self, client, test_db):
        """Test password change with wrong current password fails."""
        # Register
        register_response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
            }
        )

        token = register_response.json()["tokens"]["access_token"]

        # Try to change password with wrong current password
        response = client.put(
            "/auth/me/password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "WrongPassword123",
                "new_password": "NewTestPass456",
            }
        )

        assert response.status_code == 400

    def test_update_profile_success(self, client, test_db):
        """Test successful profile update."""
        # Register
        register_response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
                "name": "Original Name"
            }
        )

        token = register_response.json()["tokens"]["access_token"]

        # Update profile
        response = client.put(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "updateduser",
                "email": "updated@example.com",
                "name": "Updated Name",
                "avatar": "🧙‍♂️"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updateduser"
        assert data["email"] == "updated@example.com"
        assert data["name"] == "Updated Name"
        assert data["avatar"] == "🧙‍♂️"

    def test_update_profile_partial(self, client, test_db):
        """Test partial profile update."""
        # Register
        register_response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
                "name": "Test User"
            }
        )

        token = register_response.json()["tokens"]["access_token"]

        # Update only name
        response = client.put(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "New Name Only"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name Only"
        assert data["username"] == "testuser"  # Should remain unchanged
        assert data["email"] == "test@example.com"  # Should remain unchanged

    def test_update_profile_duplicate_username(self, client, test_db):
        """Test profile update with duplicate username fails."""
        # Register two users
        client.post(
            "/auth/register",
            json={
                "username": "user1",
                "email": "user1@example.com",
                "password": "TestPass123",
            }
        )

        register_response = client.post(
            "/auth/register",
            json={
                "username": "user2",
                "email": "user2@example.com",
                "password": "TestPass123",
            }
        )

        token = register_response.json()["tokens"]["access_token"]

        # Try to update to user1's username
        response = client.put(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "user1"
            }
        )

        assert response.status_code == 400
        assert "already taken" in response.json()["detail"]

    def test_update_profile_duplicate_email(self, client, test_db):
        """Test profile update with duplicate email fails."""
        # Register two users
        client.post(
            "/auth/register",
            json={
                "username": "user1",
                "email": "user1@example.com",
                "password": "TestPass123",
            }
        )

        register_response = client.post(
            "/auth/register",
            json={
                "username": "user2",
                "email": "user2@example.com",
                "password": "TestPass123",
            }
        )

        token = register_response.json()["tokens"]["access_token"]

        # Try to update to user1's email
        response = client.put(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "email": "user1@example.com"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_update_profile_invalid_username(self, client, test_db):
        """Test profile update with invalid username fails validation."""
        # Register
        register_response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
            }
        )

        token = register_response.json()["tokens"]["access_token"]

        # Try to update with invalid username (contains spaces)
        response = client.put(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "invalid username"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_update_profile_no_auth(self, client, test_db):
        """Test profile update without authentication fails."""
        response = client.put(
            "/auth/me",
            json={
                "name": "New Name"
            }
        )

        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
