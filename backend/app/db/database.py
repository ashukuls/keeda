"""MongoDB database connection and management."""

from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager."""

    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None

    @classmethod
    def connect(cls) -> None:
        """Initialize MongoDB connection."""
        try:
            cls._client = MongoClient(settings.MONGODB_URL)
            cls._database = cls._client[settings.DATABASE_NAME]

            # Test connection
            cls._client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.DATABASE_NAME}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._database = None
            logger.info("Disconnected from MongoDB")

    @classmethod
    def get_database(cls) -> Database:
        """Get database instance."""
        if cls._database is None:
            cls.connect()
        return cls._database

    @classmethod
    def get_collection(cls, name: str):
        """Get collection by name."""
        db = cls.get_database()
        return db[name]


# Convenience function
def get_database() -> Database:
    """Get MongoDB database instance."""
    return MongoDB.get_database()


def get_collection(name: str):
    """Get MongoDB collection by name."""
    return MongoDB.get_collection(name)