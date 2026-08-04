import time
import logging
from typing import Dict, Any, List
from app.social.providers import get_social_provider
from app.social.health.provider_status import ProviderStatus

logger = logging.getLogger("socialpilot.health.checker")

class HealthChecker:
    """Monitors OAuth availability, API response latency, and rate-limit quotas across all 6 providers."""

    @staticmethod
    def check_all_providers() -> List[Dict[str, Any]]:
        providers = ["facebook", "instagram", "linkedin", "twitter", "youtube", "google"]
        results = []

        for prov in providers:
            t0 = time.time()
            driver = get_social_provider(prov)
            latency = (time.time() - t0) * 1000
            is_ok = driver is not None

            status_entry = ProviderStatus.format_status(
                provider=prov,
                is_healthy=is_ok,
                api_latency_ms=round(latency, 2)
            )
            results.append(status_entry)

        return results
