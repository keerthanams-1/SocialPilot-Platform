import logging
import math
from typing import Dict, Any, Optional

logger = logging.getLogger("socialpilot.workers.retry")

class RetryPolicyManager:
    """Manages exponential backoff, rate-limit retry delay calculations, and Dead-Letter Queue (DLQ) transfers."""

    BASE_DELAY_SECONDS = 5
    MAX_DELAY_SECONDS = 3600  # 1 hour max
    MAX_RETRY_ATTEMPTS = 5

    @staticmethod
    def calculate_exponential_backoff(retry_count: int, factor: float = 2.0) -> int:
        """Compute delay = min(BASE_DELAY * (factor ^ retry_count), MAX_DELAY)."""
        if retry_count < 0:
            retry_count = 0
        delay = int(RetryPolicyManager.BASE_DELAY_SECONDS * math.pow(factor, retry_count))
        return min(delay, RetryPolicyManager.MAX_DELAY_SECONDS)

    @staticmethod
    def parse_rate_limit_reset(response_headers: Dict[str, str]) -> Optional[int]:
        """Extract Retry-After header or X-RateLimit-Reset timestamp if available."""
        if not response_headers:
            return None
        
        # Standard HTTP Retry-After
        retry_after = response_headers.get("Retry-After") or response_headers.get("retry-after")
        if retry_after and retry_after.isdigit():
            return int(retry_after)

        return None

    @staticmethod
    def should_retry(retry_count: int, exception: Exception) -> bool:
        """Determine if task should retry or be routed to DLQ."""
        if retry_count >= RetryPolicyManager.MAX_RETRY_ATTEMPTS:
            return False
        
        # Permanent authentication error or invalid parameters shouldn't retry infinitely
        err_msg = str(exception).lower()
        if "invalid_grant" in err_msg or "unauthorized" in err_msg:
            return False
            
        return True

    @staticmethod
    def route_to_dead_letter_queue(task_name: str, payload: Dict[str, Any], exception: Exception) -> Dict[str, Any]:
        """Format task error payload for Dead Letter Queue (DLQ) inspection."""
        dlq_entry = {
            "task_name": task_name,
            "payload": payload,
            "error": str(exception),
            "status": "DLQ_PENDING_REVIEW"
        }
        logger.error(f"Routing task '{task_name}' to Dead Letter Queue (DLQ): {dlq_entry}")
        return dlq_entry
