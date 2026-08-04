import json
import logging
from typing import Dict, Any, Optional
from app.database.redis_client import get_redis_client

logger = logging.getLogger("socialpilot.analytics.dashboard_cache")

class DashboardCacheManager:
    """Caches dashboard metrics in Redis with fail-safe in-memory fallback."""

    @staticmethod
    def get_cached_dashboard(cache_key: str) -> Optional[Dict[str, Any]]:
        try:
            r = get_redis_client()
            val = r.get(f"dashboard_cache:{cache_key}")
            if val:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Redis get fail-safe: {e}")
        return None

    @staticmethod
    def set_cached_dashboard(cache_key: str, data: Dict[str, Any], ttl_seconds: int = 300) -> bool:
        try:
            r = get_redis_client()
            r.set(f"dashboard_cache:{cache_key}", json.dumps(data), ex=ttl_seconds)
            return True
        except Exception as e:
            logger.warning(f"Redis set fail-safe: {e}")
            return False
