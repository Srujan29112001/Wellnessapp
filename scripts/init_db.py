"""
Database Initialization Script

Creates all database tables and initializes with sample data
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.postgres import init_db as init_postgres, close_db as close_postgres
from backend.database.mongo import init_mongo, close_mongo
from backend.models.postgres_models import User, Dosha, Gender
from backend.database.postgres import AsyncSessionLocal
from datetime import datetime

async def create_sample_user():
    """Create a sample demo user"""
    async with AsyncSessionLocal() as session:
        # Check if demo user exists
        from sqlalchemy import select
        stmt = select(User).where(User.id == "demo_user")
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Demo user already exists")
            return

        # Create demo user
        demo_user = User(
            id="demo_user",
            email="demo@wellnessai.com",
            name="Demo User",
            age=30,
            gender=Gender.PREFER_NOT_TO_SAY,
            dosha_type=Dosha.VATA_PITTA,
            health_goals=["reduce_stress", "improve_sleep", "increase_energy"],
            dietary_restrictions=["vegetarian"],
            medical_conditions=[],
            current_medications=[],
            preferences={"notifications": True, "privacy_mode": False}
        )

        session.add(demo_user)
        await session.commit()
        print(f"Created demo user: {demo_user.email}")


async def main():
    """Initialize all databases"""
    print("Initializing databases...")

    # Initialize PostgreSQL
    print("\n1. Initializing PostgreSQL...")
    await init_postgres()
    print("✓ PostgreSQL tables created")

    # Create sample user
    print("\n2. Creating sample user...")
    await create_sample_user()
    print("✓ Sample user created")

    # Initialize MongoDB
    print("\n3. Initializing MongoDB...")
    await init_mongo()
    print("✓ MongoDB collections and indexes created")

    print("\n✅ Database initialization complete!")
    print("\nYou can now start the application with:")
    print("  uvicorn backend.main:app --reload")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
