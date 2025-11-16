"""
User Service Layer

Handles user management and profiles
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import logging
import bcrypt

from backend.models.postgres_models import User
from backend.database.mongo import get_collection
from backend.models.mongo_schemas import UserContext, COLLECTION_USER_CONTEXT

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users"""

    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        name: str,
        password: str = None,
        **kwargs
    ) -> User:
        """
        Create a new user

        Args:
            db: Database session
            email: User email (unique)
            name: User name
            password: Optional password (will be hashed)
            **kwargs: Additional user fields

        Returns:
            Created User object
        """
        try:
            # Check if user exists
            existing = await UserService.get_user_by_email(db, email)
            if existing:
                raise ValueError(f"User with email {email} already exists")

            # Hash password if provided
            password_hash = None
            if password:
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Create user
            user = User(
                email=email,
                name=name,
                password_hash=password_hash,
                **kwargs
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Initialize user context in MongoDB
            await UserService.init_user_context(user.id)

            logger.info(f"Created user: {email}")
            return user

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating user: {e}")
            raise

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching user by ID: {e}")
            raise

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching user by email: {e}")
            raise

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: str,
        **kwargs
    ) -> Optional[User]:
        """Update user profile"""
        try:
            user = await UserService.get_user_by_id(db, user_id)

            if not user:
                return None

            # Update fields
            for key, value in kwargs.items():
                if hasattr(user, key) and value is not None:
                    setattr(user, key, value)

            user.updated_at = datetime.now()
            await db.commit()
            await db.refresh(user)

            logger.info(f"Updated user {user_id}")
            return user

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user: {e}")
            raise

    @staticmethod
    async def verify_password(user: User, password: str) -> bool:
        """Verify user password"""
        if not user.password_hash:
            return False

        return bcrypt.checkpw(
            password.encode('utf-8'),
            user.password_hash.encode('utf-8')
        )

    @staticmethod
    async def update_last_login(db: AsyncSession, user_id: str):
        """Update user's last login timestamp"""
        try:
            user = await UserService.get_user_by_id(db, user_id)
            if user:
                user.last_login = datetime.now()
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating last login: {e}")

    @staticmethod
    async def init_user_context(user_id: str):
        """
        Initialize user context in MongoDB for AI memory
        """
        try:
            collection = get_collection(COLLECTION_USER_CONTEXT)

            # Check if context exists
            existing = await collection.find_one({"user_id": user_id})
            if existing:
                return

            # Create initial context
            context = {
                "user_id": user_id,
                "patterns": {},
                "insights": [],
                "communication_style": None,
                "preferred_interventions": [],
                "topics_of_interest": [],
                "active_goals": [],
                "completed_goals": [],
                "milestones": [],
                "key_memories": [],
                "updated_at": datetime.now()
            }

            await collection.insert_one(context)
            logger.info(f"Initialized user context for {user_id}")

        except Exception as e:
            logger.error(f"Error initializing user context: {e}")

    @staticmethod
    async def get_user_context(user_id: str) -> Optional[dict]:
        """Get user's AI context from MongoDB"""
        try:
            collection = get_collection(COLLECTION_USER_CONTEXT)
            context = await collection.find_one({"user_id": user_id})
            return context
        except Exception as e:
            logger.error(f"Error fetching user context: {e}")
            return None

    @staticmethod
    async def update_user_context(user_id: str, updates: dict):
        """Update user's AI context"""
        try:
            collection = get_collection(COLLECTION_USER_CONTEXT)

            await collection.update_one(
                {"user_id": user_id},
                {"$set": {**updates, "updated_at": datetime.now()}},
                upsert=True
            )

            logger.info(f"Updated user context for {user_id}")

        except Exception as e:
            logger.error(f"Error updating user context: {e}")
            raise
