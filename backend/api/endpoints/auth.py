"""
Authentication Endpoints

Handles user registration, login, token refresh, and logout
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.services.auth_service import AuthService, get_current_user
from backend.database.postgres import get_db
from backend.models.postgres_models import User


router = APIRouter()


# Request/Response schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    age: Optional[int] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user

    Creates a new user account and returns authentication tokens
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash the password
    password_hash = AuthService.hash_password(request.password)

    # Create user in database
    new_user = User(
        email=request.email,
        name=request.name,
        password_hash=password_hash,
        age=request.age
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generate tokens
    user_data = {
        "user_id": new_user.id,
        "email": new_user.email,
        "name": new_user.name
    }

    tokens = AuthService.create_token_pair(user_data)

    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password

    Returns authentication tokens on success
    """
    # Authenticate user
    user = await AuthService.authenticate_user(
        email=request.email,
        password=request.password,
        db_session=db
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    # Create tokens
    tokens = AuthService.create_token_pair(user)

    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token

    Returns new token pair
    """
    # Decode refresh token
    try:
        payload = AuthService.decode_token(request.refresh_token)

        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )

        # Create new token pair
        user_data = {
            "user_id": payload["user_id"],
            "email": payload.get("email"),
            "name": payload.get("name")
        }

        tokens = AuthService.create_token_pair(user_data)

        return tokens

    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user

    In a full implementation, would:
    - Blacklist the token
    - Clear server-side session
    - Invalidate refresh token
    """
    # For stateless JWT, logout is handled client-side
    # by deleting the tokens

    return {
        "message": "Successfully logged out",
        "user_id": current_user["user_id"]
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information

    Requires valid access token
    """
    return UserResponse(
        user_id=current_user["user_id"],
        email=current_user.get("email", "unknown"),
        name=current_user.get("name", "Unknown User")
    )


@router.post("/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    Verify that a token is valid

    Returns user info if token is valid, 401 otherwise
    """
    return {
        "valid": True,
        "user_id": current_user["user_id"],
        "email": current_user.get("email")
    }
