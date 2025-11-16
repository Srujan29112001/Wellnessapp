"""
Authentication Endpoints

Handles user registration, login, token refresh, and logout
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional

from backend.services.auth_service import AuthService, get_current_user


router = APIRouter()


# Request/Response schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    age: Optional[int] = None


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
async def register(request: RegisterRequest):
    """
    Register a new user

    Creates a new user account and returns authentication tokens
    """
    # In a real implementation:
    # 1. Check if email already exists
    # 2. Hash the password
    # 3. Create user in database
    # 4. Generate tokens

    # For demo, accept any registration
    user_data = {
        "user_id": f"user_{request.email.split('@')[0]}",
        "email": request.email,
        "name": request.name
    }

    tokens = AuthService.create_token_pair(user_data)

    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login with email and password

    Returns authentication tokens on success
    """
    # Authenticate user
    user = await AuthService.authenticate_user(
        email=request.email,
        password=request.password,
        db_service=None  # Would pass real DB service here
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
