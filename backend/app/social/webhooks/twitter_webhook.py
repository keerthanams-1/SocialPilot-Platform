import hmac
import hashlib
import base64
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger("socialpilot.webhooks.twitter")

def get_secret_str(val: Any, fallback: str) -> str:
    if not val:
        return fallback
    if hasattr(val, "get_secret_value"):
        return val.get_secret_value() or fallback
    return str(val)

class TwitterWebhookHandler:
    """Twitter Account Activity API Challenge-Response & Event Processor."""

    @staticmethod
    def generate_crc_response(crc_token: str) -> str:
        sec_str = get_secret_str(settings.TWITTER_CLIENT_SECRET, "demo_twitter_secret")
        secret = sec_str.encode("utf-8")
        sha256_hash = hmac.new(secret, crc_token.encode("utf-8"), hashlib.sha256).digest()
        return "sha256=" + base64.b64encode(sha256_hash).decode("utf-8")

    @staticmethod
    def verify_signature(payload_bytes: bytes, signature_header: str) -> bool:
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        expected_sig = signature_header.split("sha256=")[1]
        sec_str = get_secret_str(settings.TWITTER_CLIENT_SECRET, "demo_twitter_secret")
        secret = sec_str.encode("utf-8")
        computed_hash = hmac.new(secret, payload_bytes, hashlib.sha256).digest()
        computed_sig = base64.b64encode(computed_hash).decode("utf-8")
        return hmac.compare_digest(computed_sig, expected_sig)

    @staticmethod
    def process_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "processed",
            "platform": "twitter",
            "for_user_id": event_data.get("for_user_id"),
            "event_keys": list(event_data.keys())
        }
