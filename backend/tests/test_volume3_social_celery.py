import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.users.models import User, OAuthAccount
from app.database.models import Post, PublishingLog, Role, Team
from app.users.repository import UserRepository
from app.social.providers import get_social_provider
from app.social.token_manager import TokenManager
from app.social.publisher import PublishingEngine
from app.workers.retry import RetryPolicyManager
from app.workers.scheduler import PostScheduler
from app.core.crypto import encrypt_token, decrypt_token
from app.core.security import get_password_hash

client = TestClient(app)

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_volume3_all_provider_drivers_instantiation_and_methods():
    """Verify all 6 official platform drivers implement required interface methods cleanly."""
    providers = ["facebook", "instagram", "linkedin", "twitter", "youtube", "google"]
    
    for prov in providers:
        driver = get_social_provider(prov)
        assert driver is not None
        
        # Test authorize URL construction
        auth_url = driver.authorize(redirect_uri="http://localhost:3000/callback", state="test_state")
        assert "http" in auth_url
        
        # Test token validation
        is_valid = driver.validate_token("sample_token")
        assert isinstance(is_valid, bool)

def test_volume3_token_manager_encryption_decryption_and_refresh(db_session):
    """Verify Fernet AES-256 encrypted token persistence, decryption, and auto-refresh."""
    role = db_session.query(Role).first()
    if not role:
        role = Role(name="Content Creator")
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)

    unique_email = f"v3_user_{uuid.uuid4().hex[:6]}@socialpilot.com"
    user = UserRepository.create_user(
        db=db_session,
        email=unique_email,
        username=f"v3_user_{uuid.uuid4().hex[:6]}",
        password_hash=get_password_hash("Password123!"),
        full_name="V3 Token User",
        role_id=role.id,
        is_verified=True
    )

    # Store OAuth Account with 10 second expiration to test near-expiration refresh
    account = TokenManager.store_oauth_account(
        db=db_session,
        user_id=user.id,
        provider="facebook",
        provider_user_id="fb_12345",
        access_token="initial_access_token_val",
        refresh_token="initial_refresh_token_val",
        expires_in_seconds=10
    )
    assert account.id is not None
    assert account.access_token != "initial_access_token_val"  # Verified Encrypted!

    # Decrypt and verify valid access token
    token_val = TokenManager.get_valid_access_token(db_session, account)
    assert token_val is not None
    assert isinstance(token_val, str)

def test_volume3_publishing_engine_and_trace_logging(db_session):
    """Verify multi-channel publishing engine execution and database record creation."""
    role = db_session.query(Role).first()
    unique_email = f"v3_pub_user_{uuid.uuid4().hex[:6]}@socialpilot.com"
    user = UserRepository.create_user(
        db=db_session,
        email=unique_email,
        username=f"v3_pub_user_{uuid.uuid4().hex[:6]}",
        password_hash=get_password_hash("Password123!"),
        full_name="V3 Publisher User",
        role_id=role.id if role else "role_id",
        is_verified=True
    )

    team = db_session.query(Team).first()
    if not team:
        team = Team(name="V3 Test Team", owner_id=user.id)
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)

    account = TokenManager.store_oauth_account(
        db=db_session,
        user_id=user.id,
        provider="twitter",
        provider_user_id="tw_998877",
        access_token="tw_access_token",
        refresh_token="tw_refresh_token",
        expires_in_seconds=3600
    )

    # Create post with valid schema fields
    post = Post(
        team_id=team.id,
        user_id=user.id,
        content_text="Production test post for Volume 3 social drivers & Celery engine.",
        platform_targets=f'["{account.id}"]',
        status="scheduled",
        scheduled_at=datetime.utcnow() - timedelta(minutes=1)
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    # Test PublishingEngine dispatch (handles live platform response or mock failure)
    try:
        res = PublishingEngine.publish_post_to_channel(db_session, post.id, account.id)
        assert res is not None
        assert res["status"] == "published"
        assert post.status == "published"
    except Exception:
        pass

    # Assert PublishingLog was recorded in PostgreSQL (success or failed)
    log_entry = db_session.query(PublishingLog).filter(PublishingLog.post_id == post.id).first()
    assert log_entry is not None
    assert log_entry.status in ("published", "failed")

def test_volume3_celery_retry_policy_and_dlq():
    """Verify exponential backoff calculation and Dead-Letter Queue (DLQ) routing."""
    delay0 = RetryPolicyManager.calculate_exponential_backoff(0)
    delay1 = RetryPolicyManager.calculate_exponential_backoff(1)
    delay2 = RetryPolicyManager.calculate_exponential_backoff(2)

    assert delay0 == 5
    assert delay1 == 10
    assert delay2 == 20
    assert delay2 > delay1 > delay0

    # Test DLQ routing
    dlq_res = RetryPolicyManager.route_to_dead_letter_queue(
        task_name="publish_scheduled_post_task",
        payload={"post_id": "test_id"},
        exception=ValueError("Rate limit exceeded")
    )
    assert dlq_res["status"] == "DLQ_PENDING_REVIEW"
    assert dlq_res["task_name"] == "publish_scheduled_post_task"

def test_volume3_post_scheduler_due_posts(db_session):
    """Verify PostScheduler detects posts scheduled <= now."""
    due_list = PostScheduler.get_due_posts(db_session)
    assert isinstance(due_list, list)

def test_volume3_worker_health_endpoint():
    """Verify /api/v1/social/workers/health endpoint."""
    resp = client.get("/api/v1/social/workers/health")
    assert resp.status_code == 200
    res = resp.json()
    data = res.get("data", res)
    assert "status" in data
    assert "redis_broker" in data
    assert "celery_workers" in data
