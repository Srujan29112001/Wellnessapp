"""
Authentication and Authorization Service

Provides:
- JWT token generation and validation
- Password hashing and verification
- User authentication
- Authorization middleware
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Security scheme
security = HTTPBearer()


class AuthService:
    """Authentication service"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        data: Dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token

        Args:
            data: Payload data to encode in token
            expires_delta: Optional custom expiration time

        Returns:
            JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire, "type": "access"})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: Dict) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode.update({"exp": expire, "type": "refresh"})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Dict:
        """
        Decode and validate a JWT token

        Args:
            token: JWT token string

        Returns:
            Token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )

        except jwt.JWTError:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials"
            )

    @staticmethod
    async def authenticate_user(email: str, password: str, db_session) -> Optional[Dict]:
        """
        Authenticate a user by email and password

        Args:
            email: User email
            password: Plain text password
            db_session: SQLAlchemy async session

        Returns:
            User data if authenticated, None otherwise
        """
        from sqlalchemy import select
        from backend.models.postgres_models import User
        from datetime import datetime

        # Demo user (always works)
        if email == "demo@wellnessai.com" and password == "demo123":
            return {
                "user_id": "demo_user",
                "email": email,
                "name": "Demo User"
            }

        # Query database for user
        try:
            result = await db_session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

            if not user:
                return None

            # Verify password
            if not AuthService.verify_password(password, user.password_hash):
                return None

            # Update last login
            user.last_login = datetime.utcnow()
            await db_session.commit()

            # Return user data
            return {
                "user_id": user.id,
                "email": user.email,
                "name": user.name,
                "dosha_type": user.dosha_type.value if user.dosha_type else None
            }

        except Exception as e:
            print(f"Authentication error: {e}")
            return None

    @staticmethod
    def create_token_pair(user_data: Dict) -> Dict:
        """
        Create access and refresh token pair

        Args:
            user_data: User data to encode in tokens

        Returns:
            {
                "access_token": str,
                "refresh_token": str,
                "token_type": "bearer"
            }
        """
        access_token = AuthService.create_access_token(data=user_data)
        refresh_token = AuthService.create_refresh_token(data=user_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }


# Dependency for protected routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict:
    """
    Dependency to get current authenticated user

    Usage in FastAPI route:
        @app.get("/protected")
        async def protected_route(user: Dict = Depends(get_current_user)):
            return {"user_id": user["user_id"]}
    """
    token = credentials.credentials

    # Decode and validate token
    payload = AuthService.decode_token(token)

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type"
        )

    # Extract user info
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )

    return payload


# Optional: Dependency for admin-only routes
async def get_current_admin_user(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """Dependency to ensure user is admin"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user


# For development/demo: Allow bypassing auth
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Dict:
    """
    Optional authentication - returns demo user if no token provided

    Useful for development
    """
    if credentials is None:
        # Return demo user
        return {
            "user_id": "demo_user",
            "email": "demo@wellnessai.com",
            "name": "Demo User"
        }

    return await get_current_user(credentials)
