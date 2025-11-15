"""
MongoDB Connection and Client Management
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

# Global MongoDB client
mongo_client: AsyncIOMotorClient = None
database = None


async def init_mongo():
    """
    Initialize MongoDB connection
    """
    global mongo_client, database

    try:
        # Create async client
        mongo_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=50,
        )

        # Test connection
        await mongo_client.admin.command('ping')

        # Get database
        database = mongo_client[settings.MONGODB_DB]

        logger.info(f"Connected to MongoDB: {settings.MONGODB_DB}")

        # Create indexes
        await create_indexes()

    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Error initializing MongoDB: {e}")
        raise


async def close_mongo():
    """
    Close MongoDB connections
    """
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connections closed")


async def create_indexes():
    """
    Create database indexes for better query performance
    """
    try:
        # Journal entries
        await database.journal_entries.create_index([("user_id", 1), ("timestamp", -1)])

        # EEG raw data
        await database.eeg_raw_data.create_index([("user_id", 1), ("timestamp", -1)])

        # Voice recordings metadata
        await database.voice_recordings.create_index([("user_id", 1), ("timestamp", -1)])

        # Chat messages
        await database.chat_messages.create_index([("user_id", 1), ("timestamp", -1)])

        # Meal images
        await database.meal_images.create_index([("user_id", 1), ("timestamp", -1)])

        logger.info("MongoDB indexes created successfully")

    except Exception as e:
        logger.error(f"Error creating MongoDB indexes: {e}")


def get_mongo_db():
    """
    Get MongoDB database instance
    """
    return database


def get_collection(collection_name: str):
    """
    Get a specific collection from MongoDB
    """
    return database[collection_name]
