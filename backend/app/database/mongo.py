import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from app.core.config import settings

logger = logging.getLogger("socialpilot.database.mongo")

class MongoDatabaseManager:
    """Production MongoDB Client Manager for unstructured payloads, raw analytics, and audit traces."""
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    @classmethod
    def get_client(cls) -> MongoClient:
        if cls._client is None:
            try:
                cls._client = MongoClient(
                    settings.MONGODB_URL,
                    serverSelectionTimeoutMS=3000,
                    connectTimeoutMS=3000
                )
                logger.info("Successfully initialized MongoDB Client instance.")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB at {settings.MONGODB_URL}: {e}")
                raise e
        return cls._client

    @classmethod
    def get_db(cls) -> Database:
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[settings.MONGODB_DB_NAME]
        return cls._db

    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            logger.info("MongoDB client connection closed.")

def get_mongo_db() -> Database:
    """Dependency providing MongoDB database instance for FastAPI routes."""
    return MongoDatabaseManager.get_db()
