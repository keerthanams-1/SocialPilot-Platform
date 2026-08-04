import logging
from typing import Optional
import redis
from app.core.config import settings

logger = logging.getLogger("socialpilot.database.redis")

class RedisClientManager:
    """Production Redis Client Manager for caching, OAuth state parameters, and rate-limiting."""
    _client: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        if cls._client is None:
            try:
                cls._client = redis.Redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=0.2,
                    socket_connect_timeout=0.2
                )
                logger.info(f"Initialized Redis connection pool to {settings.REDIS_URL}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis at {settings.REDIS_URL}: {e}")
                raise e
        return cls._client

    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            logger.info("Redis client connection closed.")

def get_redis_client() -> redis.Redis:
    """Dependency providing Redis client instance."""
    return RedisClientManager.get_client()

class LazyRedisClientProxy:
    def __getattr__(self, name):
        return getattr(RedisClientManager.get_client(), name)

redis_client = LazyRedisClientProxy()

