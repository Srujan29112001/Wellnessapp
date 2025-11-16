"""
Authentication Service

Handles:
- User registration and login
- JWT token generation and validation
- Password hashing
- Session management
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from backend.models.postgres_models import User
from backend.database.postgres import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Authentication service for user management
    """

    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against hash"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token

        Args:
            data: Payload data (should include user_id)
            expires_delta: Optional expiration time

        Returns:
            JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            return None

    async def register_user(
        self,
        email: str,
        password: str,
        name: str,
        **kwargs
    ) -> Optional[User]:
        """
        Register a new user

        Args:
            email: User email
            password: Plain text password
            name: User name
            **kwargs: Additional user fields

        Returns:
            Created user or None if email exists
        """
        async with AsyncSessionLocal() as session:
            # Check if email exists
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                logger.warning(f"Email {email} already registered")
                return None

            # Hash password
            password_hash = self.hash_password(password)

            # Create user
            user = User(
                email=email,
                name=name,
                password_hash=password_hash,
                **kwargs
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

            logger.info(f"Registered new user: {user.id}")

            # Create user context in MongoDB
            from backend.database.mongo import get_mongo_db
            db = get_mongo_db()
            user_context = {
                "user_id": user.id,
                "patterns": {},
                "insights": [],
                "communication_style": "empathetic",
                "preferred_interventions": [],
                "topics_of_interest": [],
                "active_goals": [],
                "completed_goals": [],
                "milestones": [],
                "key_memories": [],
                "updated_at": datetime.now()
            }
            await db.user_context.insert_one(user_context)

            return user

    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with email and password

        Args:
            email: User email
            password: Plain text password

        Returns:
            User object if authenticated, None otherwise
        """
        async with AsyncSessionLocal() as session:
            # Get user by email
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Login attempt for non-existent email: {email}")
                return None

            # Verify password
            if not self.verify_password(password, user.password_hash):
                logger.warning(f"Invalid password for email: {email}")
                return None

            # Update last login
            user.last_login = datetime.now()
            await session.commit()

            logger.info(f"User authenticated: {user.id}")
            return user

    async def login(
        self,
        email: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Login user and return access token

        Args:
            email: User email
            password: Plain text password

        Returns:
            Dict with access_token and user info, or None
        """
        user = await self.authenticate_user(email, password)

        if not user:
            return None

        # Create access token
        access_token = self.create_access_token(
            data={"sub": user.id, "email": user.email}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "dosha_type": user.dosha_type.value if user.dosha_type else None
            }
        }

    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from JWT token

        Args:
            token: JWT access token

        Returns:
            User object or None
        """
        payload = self.verify_token(token)

        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            return user


# Global auth service instance
_auth_service = None


def get_auth_service() -> AuthService:
    """Get or create auth service"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
