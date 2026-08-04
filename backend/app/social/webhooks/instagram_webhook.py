import hmac
import hashlib
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger("socialpilot.webhooks.instagram")

def get_secret_str(val: Any, fallback: str) -> str:
    if not val:
        return fallback
    if hasattr(val, "get_secret_value"):
        return val.get_secret_value() or fallback
    return str(val)

class InstagramWebhookHandler:
    """Instagram Graph API Webhook Verifier & Container/Mention Processor."""

    @staticmethod
    def verify_signature(payload_bytes: bytes, signature_header: str) -> bool:
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        expected_sig = signature_header.split("sha256=")[1]
        sec_str = get_secret_str(settings.FACEBOOK_APP_SECRET, "demo_fb_secret")
        secret = sec_str.encode("utf-8")
        computed_sig = hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed_sig, expected_sig)

    @staticmethod
    def process_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
        entries = event_data.get("entry", [])
        events_parsed = []
        for entry in entries:
            ig_id = entry.get("id")
            for change in entry.get("changes", []):
                field = change.get("field")
                value = change.get("value", {})
                events_parsed.append({
                    "platform": "instagram",
                    "instagram_user_id": ig_id,
                    "field": field,
                    "media_id": value.get("media_id"),
                    "comment_id": value.get("comment_id")
                })
        return {"status": "processed", "parsed_events": events_parsed}
