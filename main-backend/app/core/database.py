"""
MongoDB connection manager using Motor (async driver).
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient = None
_db: AsyncIOMotorDatabase = None


async def connect_db():
    global _client, _db
    logger.info(f"Connecting to MongoDB: {settings.MONGO_URI}")
    _client = AsyncIOMotorClient(settings.MONGO_URI)
    _db = _client[settings.MONGO_DB_NAME]

    # Create indexes
    await _db.sessions.create_index("session_id", unique=True)
    await _db.answers.create_index([("session_id", 1), ("user_name", 1)])
    logger.info(f"Connected to database: {settings.MONGO_DB_NAME}")


async def close_db():
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _db
