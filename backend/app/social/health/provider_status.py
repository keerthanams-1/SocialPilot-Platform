from typing import Dict, Any

class ProviderStatus:
    """Represents provider health, API latency, rate limit status, and token metrics."""

    @staticmethod
    def format_status(
        provider: str,
        is_healthy: bool = True,
        rate_limit_remaining: int = 4900,
        rate_limit_limit: int = 5000,
        api_latency_ms: float = 120.0
    ) -> Dict[str, Any]:
        return {
            "provider": provider,
            "status": "healthy" if is_healthy else "degraded",
            "oauth_available": True,
            "api_available": is_healthy,
            "rate_limit_remaining": rate_limit_remaining,
            "rate_limit_limit": rate_limit_limit,
            "api_latency_ms": api_latency_ms,
            "webhook_available": True
        }
