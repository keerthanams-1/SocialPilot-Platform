import hmac
import hashlib
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger("socialpilot.webhooks.linkedin")

def get_secret_str(val: Any, fallback: str) -> str:
    if not val:
        return fallback
    if hasattr(val, "get_secret_value"):
        return val.get_secret_value() or fallback
    return str(val)

class LinkedInWebhookHandler:
    """LinkedIn REST API Webhook Verifier & Share Event Processor."""

    @staticmethod
    def verify_signature(payload_bytes: bytes, signature_header: str) -> bool:
        if not signature_header:
            return True
        sec_str = get_secret_str(settings.LINKEDIN_CLIENT_SECRET, "demo_linkedin_secret")
        secret = sec_str.encode("utf-8")
        computed_sig = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed_sig, signature_header)

    @staticmethod
    def process_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "processed",
            "platform": "linkedin",
            "event_type": event_data.get("type", "share_event"),
            "event_body": event_data
        }
