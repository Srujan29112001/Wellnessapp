"""
Integration tests for authentication system

Tests JWT token generation, validation, and protected endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.models.postgres_models import User, Base
from backend.database.postgres import get_db
from backend.services.auth_service import AuthService


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create test client with test database"""
    from main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestAuthService:
    """Test AuthService methods"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("WrongPassword", hashed)

    def test_create_access_token(self):
        """Test JWT access token creation"""
        user_data = {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "name": "Test User"
        }

        token = AuthService.create_access_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        payload = AuthService.decode_token(token)
        assert payload["user_id"] == user_data["user_id"]
        assert payload["email"] == user_data["email"]
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        """Test JWT refresh token creation"""
        user_data = {
            "user_id": "test_user_123",
            "email": "test@example.com"
        }

        token = AuthService.create_refresh_token(user_data)

        assert isinstance(token, str)
        payload = AuthService.decode_token(token)
        assert payload["type"] == "refresh"

    def test_create_token_pair(self):
        """Test creating access and refresh token pair"""
        user_data = {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "name": "Test User"
        }

        tokens = AuthService.create_token_pair(user_data)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

        # Verify both tokens
        access_payload = AuthService.decode_token(tokens["access_token"])
        refresh_payload = AuthService.decode_token(tokens["refresh_token"])

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"


class TestRegistrationEndpoint:
    """Test user registration"""

    def test_register_new_user(self, client, db_session):
        """Test successful user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "name": "New User",
                "age": 30
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        # Verify user was created in database
        user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.name == "New User"
        assert user.age == 30

    def test_register_duplicate_email(self, client, db_session):
        """Test registration with existing email"""
        # Create first user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "Password123!",
                "name": "First User"
            }
        )

        # Try to register with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "Password456!",
                "name": "Second User"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "weak",  # Less than 8 characters
                "name": "User"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "Password123!",
                "name": "User"
            }
        )

        assert response.status_code == 422


class TestLoginEndpoint:
    """Test user login"""

    def test_login_success(self, client, db_session):
        """Test successful login"""
        # Register user first
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "LoginPass123!",
                "name": "Login User"
            }
        )

        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "LoginPass123!"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_demo_user(self, client):
        """Test demo user login"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "demo@wellnessai.com",
                "password": "demo123"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data

    def test_login_wrong_password(self, client, db_session):
        """Test login with incorrect password"""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "CorrectPass123!",
                "name": "User"
            }
        )

        # Try to login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "doesnotexist@example.com",
                "password": "AnyPassword123!"
            }
        )

        assert response.status_code == 401


class TestProtectedEndpoints:
    """Test protected endpoints with authentication"""

    def test_access_protected_route_with_valid_token(self, client, db_session):
        """Test accessing protected route with valid token"""
        # Register and get token
        reg_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "protected@example.com",
                "password": "Password123!",
                "name": "Protected User"
            }
        )
        access_token = reg_response.json()["access_token"]

        # Access protected route
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == "protected@example.com"
        assert data["name"] == "Protected User"

    def test_access_protected_route_without_token(self, client):
        """Test accessing protected route without token"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403  # Forbidden

    def test_access_protected_route_with_invalid_token(self, client):
        """Test accessing protected route with invalid token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401


class TestTokenRefresh:
    """Test token refresh functionality"""

    def test_refresh_token_success(self, client, db_session):
        """Test refreshing access token"""
        # Register and get tokens
        reg_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "Password123!",
                "name": "Refresh User"
            }
        )
        refresh_token = reg_response.json()["refresh_token"]

        # Refresh token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_with_access_token_fails(self, client, db_session):
        """Test that access token cannot be used for refresh"""
        # Register and get tokens
        reg_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "norefresh@example.com",
                "password": "Password123!",
                "name": "User"
            }
        )
        access_token = reg_response.json()["access_token"]

        # Try to refresh with access token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token}
        )

        assert response.status_code == 401


class TestLogout:
    """Test logout functionality"""

    def test_logout_success(self, client, db_session):
        """Test successful logout"""
        # Register and get token
        reg_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout@example.com",
                "password": "Password123!",
                "name": "Logout User"
            }
        )
        access_token = reg_response.json()["access_token"]

        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()


class TestTokenVerification:
    """Test token verification endpoint"""

    def test_verify_valid_token(self, client, db_session):
        """Test verifying a valid token"""
        # Register and get token
        reg_response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "verify@example.com",
                "password": "Password123!",
                "name": "Verify User"
            }
        )
        access_token = reg_response.json()["access_token"]

        # Verify token
        response = client.post(
            "/api/v1/auth/verify-token",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert "user_id" in data

    def test_verify_invalid_token(self, client):
        """Test verifying an invalid token"""
        response = client.post(
            "/api/v1/auth/verify-token",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401


# Run tests with: pytest tests/test_authentication.py -v
