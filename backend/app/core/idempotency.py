import json
import logging
from typing import Optional, Dict, Any
from app.database.redis_client import get_redis_client

logger = logging.getLogger("socialpilot.core.idempotency")

_memory_idempotency_store = {}

class IdempotencyManager:
    """Manages request idempotency keys to prevent duplicate post dispatches."""

    @staticmethod
    def get_cached_response(key: str) -> Optional[Dict[str, Any]]:
        redis_client = get_redis_client()
        cache_key = f"idempotency:{key}"
        if redis_client:
            try:
                val = redis_client.get(cache_key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"Redis idempotency lookup warning: {e}")

        # In-memory fallback
        return _memory_idempotency_store.get(cache_key)

    @staticmethod
    def save_response(key: str, response_data: Dict[str, Any], ttl_seconds: int = 86400):
        redis_client = get_redis_client()
        cache_key = f"idempotency:{key}"
        if redis_client:
            try:
                redis_client.setex(cache_key, ttl_seconds, json.dumps(response_data))
                return
            except Exception as e:
                logger.warning(f"Redis idempotency store warning: {e}")

        _memory_idempotency_store[cache_key] = response_data
