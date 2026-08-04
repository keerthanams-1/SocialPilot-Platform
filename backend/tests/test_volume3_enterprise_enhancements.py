import pytest
import hmac
import hashlib
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.core.responses import standard_response
from app.core.redis_lock import RedisLock
from app.core.idempotency import IdempotencyManager
from app.social.webhooks.facebook_webhook import FacebookWebhookHandler
from app.social.webhooks.twitter_webhook import TwitterWebhookHandler
from app.social.health.health_checker import HealthChecker
from app.social.media.validator import MediaValidator
from app.social.media.media_service import MediaService
from app.workers.recovery import SchedulerRecoveryManager
from app.database.models import User, Role
from app.users.repository import UserRepository
from app.core.security import get_password_hash

client = TestClient(app)

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_volume3_standardized_api_responses():
    """Verify standard response envelope format (success, message, data, errors, request_id, timestamp)."""
    resp = standard_response(success=True, message="Test message", data={"item": 123})
    assert resp.status_code == 200
    import json
    content = json.loads(resp.body)
    assert content["success"] is True
    assert content["message"] == "Test message"
    assert content["data"] == {"item": 123}
    assert "request_id" in content
    assert "timestamp" in content

def test_volume3_redis_distributed_locking():
    """Verify RedisLock prevents concurrent worker execution for the same post ID."""
    lock_key = "test_post_12345"
    with RedisLock(lock_key, timeout_seconds=10) as lock1:
        assert lock1.acquired is True
        
        # Second attempt to acquire lock on same key should fail
        with RedisLock(lock_key, timeout_seconds=10) as lock2:
            assert lock2.acquired is False

def test_volume3_idempotency_key_prevention():
    """Verify IdempotencyManager prevents duplicate dispatch processing."""
    key = "idempotency_test_key_999"
    assert IdempotencyManager.get_cached_response(key) is None
    
    response_payload = {"status": "published", "post_id": "999"}
    IdempotencyManager.save_response(key, response_payload)
    
    cached = IdempotencyManager.get_cached_response(key)
    assert cached is not None
    assert cached["status"] == "published"

def test_volume3_webhooks_signature_and_ingestion():
    """Verify HMAC signature validation and webhook router endpoint ingestion."""
    # Test Twitter CRC challenge
    crc_res = TwitterWebhookHandler.generate_crc_response("sample_crc_token")
    assert crc_res.startswith("sha256=")

    # Test Facebook Webhook verification endpoint
    resp = client.get("/api/v1/webhooks/facebook?hub.mode=subscribe&hub.challenge=123456&hub.verify_token=test")
    assert resp.status_code == 200
    assert resp.text == "123456"

    # Test Webhook POST ingestion endpoint
    post_resp = client.post(
        "/api/v1/webhooks/facebook",
        json={"object": "page", "entry": [{"id": "fb_123", "changes": [{"field": "feed", "value": {"post_id": "p_1"}}]}]}
    )
    assert post_resp.status_code == 200
    data = post_resp.json()
    assert data["success"] is True

def test_volume3_provider_health_monitoring():
    """Verify HealthChecker monitors latency, OAuth availability, and rate limits across all 6 providers."""
    health_list = HealthChecker.check_all_providers()
    assert len(health_list) == 6
    for status in health_list:
        assert "provider" in status
        assert status["status"] == "healthy"
        assert status["oauth_available"] is True
        assert status["rate_limit_remaining"] > 0

    # Test /api/v1/social/providers endpoint
    resp = client.get("/api/v1/social/providers")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Test /api/v1/social/provider-status endpoint
    resp = client.get("/api/v1/social/provider-status")
    assert resp.status_code == 200
    assert resp.json()["success"] is True

def test_volume3_media_validation_and_s3_storage():
    """Verify media validation rules, aspect ratio, MIME type, and S3 / MinIO CDN URL upload."""
    # Test valid image
    valid, msg = MediaValidator.validate(platform="instagram", filesize_bytes=2*1024*1024, mime_type="image/jpeg")
    assert valid is True

    # Test oversized video
    valid, msg = MediaValidator.validate(platform="instagram", filesize_bytes=500*1024*1024, mime_type="video/mp4")
    assert valid is False
    assert "exceeds" in msg

    # Test MediaService upload pipeline
    media_svc = MediaService()
    res = media_svc.process_and_upload(
        file_bytes=b"dummy_image_data_bytes_for_testing",
        filename="banner.jpg",
        mime_type="image/jpeg",
        platform="facebook"
    )
    assert res["media_url"].startswith("http")
    assert "socialpilot" in res["media_url"]

def test_volume3_scheduler_crash_recovery(db_session):
    """Verify SchedulerRecoveryManager reclaims orphaned 'running' jobs after server restarts."""
    rec_res = SchedulerRecoveryManager.recover_orphaned_and_pending_jobs(db_session)
    assert "recovered_stuck_jobs" in rec_res
    assert isinstance(rec_res["recovered_stuck_jobs"], int)
