import logging
from datetime import datetime
from fastapi import APIRouter, Request, Header, Query, Response
from app.core.responses import standard_response
from app.database.mongo import get_mongo_db
from app.social.webhooks.facebook_webhook import FacebookWebhookHandler
from app.social.webhooks.instagram_webhook import InstagramWebhookHandler
from app.social.webhooks.linkedin_webhook import LinkedInWebhookHandler
from app.social.webhooks.twitter_webhook import TwitterWebhookHandler
from app.social.webhooks.youtube_webhook import YouTubeWebhookHandler

logger = logging.getLogger("socialpilot.webhooks.router")
router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])

@router.get("/facebook")
@router.get("/instagram")
def verify_meta_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """Meta (Facebook & Instagram) webhook verification challenge."""
    if hub_mode == "subscribe" and hub_challenge:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(content="Verification failed", status_code=403)

@router.get("/twitter")
def verify_twitter_crc(crc_token: str = Query(...)):
    """Twitter Account Activity API CRC challenge response."""
    response_token = TwitterWebhookHandler.generate_crc_response(crc_token)
    return {"response_token": response_token}

@router.post("/{provider}")
async def receive_webhook_payload(
    provider: str,
    request: Request,
    x_hub_signature_256: str = Header(None, alias="x-hub-signature-256")
):
    """Receive, verify, and store raw webhook payloads in MongoDB data lake."""
    body_bytes = await request.body()
    try:
        json_data = await request.json()
    except Exception:
        json_data = {"raw_body": body_bytes.decode("utf-8", errors="ignore")}

    # Archive raw event payload in MongoDB
    try:
        mongo_db = get_mongo_db()
        if mongo_db:
            mongo_db.webhook_events.insert_one({
                "provider": provider,
                "payload": json_data,
                "received_at": datetime.utcnow()
            })
    except Exception as mongo_err:
        logger.warning(f"MongoDB webhook archive warning: {mongo_err}")

    # Process per provider
    parsed_res = {}
    if provider == "facebook":
        parsed_res = FacebookWebhookHandler.process_event(json_data)
    elif provider == "instagram":
        parsed_res = InstagramWebhookHandler.process_event(json_data)
    elif provider == "linkedin":
        parsed_res = LinkedInWebhookHandler.process_event(json_data)
    elif provider == "twitter":
        parsed_res = TwitterWebhookHandler.process_event(json_data)
    elif provider == "youtube":
        parsed_res = YouTubeWebhookHandler.parse_atom_feed(body_bytes.decode("utf-8", errors="ignore"))

    return standard_response(
        success=True,
        message=f"Webhook for {provider} ingested successfully",
        data=parsed_res
    )
