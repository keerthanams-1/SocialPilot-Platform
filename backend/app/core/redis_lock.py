import time
import logging
import threading
from typing import Optional
from app.database.redis_client import get_redis_client

logger = logging.getLogger("socialpilot.core.redis_lock")

# In-memory lock fallback when Redis server is unreachable
_memory_locks = {}
_memory_lock_guard = threading.Lock()

class RedisLock:
    """Distributed Redis lock context manager preventing concurrent post execution across Celery workers."""

    def __init__(self, key: str, timeout_seconds: int = 60):
        self.key = f"lock:{key}"
        self.timeout = timeout_seconds
        self.acquired = False
        self.redis = get_redis_client()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def acquire(self) -> bool:
        if self.redis:
            try:
                # SET key value NX PX timeout_ms
                res = self.redis.set(self.key, "locked", nx=True, px=self.timeout * 1000)
                self.acquired = bool(res)
                return self.acquired
            except Exception as e:
                logger.warning(f"Redis lock acquire fallback for {self.key}: {e}")

        # In-memory fallback
        with _memory_lock_guard:
            now = time.time()
            lock_exp = _memory_locks.get(self.key, 0)
            if lock_exp < now:
                _memory_locks[self.key] = now + self.timeout
                self.acquired = True
                return True
            else:
                self.acquired = False
                return False

    def release(self):
        if not self.acquired:
            return

        if self.redis:
            try:
                self.redis.delete(self.key)
            except Exception:
                pass

        with _memory_lock_guard:
            _memory_locks.pop(self.key, None)

        self.acquired = False
