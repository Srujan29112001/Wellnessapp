"""
PostgreSQL Database Connection and Session Management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

# Convert postgres:// to postgresql+asyncpg://
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Create async engine
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def init_db():
    """
    Initialize database - create all tables
    """
    try:
        async with async_engine.begin() as conn:
            # Import all models here to register them with Base
            from backend.models.postgres_models import (
                User,
                HealthMetric,
                EEGAnalysis,
                VoiceAnalysis,
                Recommendation,
                SupplementLog
            )

            # Create tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("PostgreSQL tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing PostgreSQL database: {e}")
        raise


async def close_db():
    """
    Close database connections
    """
    await async_engine.dispose()
    logger.info("PostgreSQL connections closed")


async def get_db():
    """
    Dependency to get database session
    Usage in FastAPI endpoints:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
