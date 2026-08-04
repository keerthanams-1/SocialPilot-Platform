import hmac
import hashlib
import logging
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger("socialpilot.webhooks.facebook")

def get_secret_str(val: Any, fallback: str) -> str:
    if not val:
        return fallback
    if hasattr(val, "get_secret_value"):
        return val.get_secret_value() or fallback
    return str(val)

class FacebookWebhookHandler:
    """Facebook Graph API HMAC-SHA256 Webhook Verifier & Event Processor."""

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
        object_type = event_data.get("object")
        entries = event_data.get("entry", [])
        events_parsed = []

        for entry in entries:
            page_id = entry.get("id")
            for change in entry.get("changes", []):
                field = change.get("field")
                value = change.get("value", {})
                events_parsed.append({
                    "platform": "facebook",
                    "page_id": page_id,
                    "field": field,
                    "post_id": value.get("post_id"),
                    "verb": value.get("verb"),
                    "item": value.get("item")
                })
        return {"status": "processed", "parsed_events": events_parsed}
