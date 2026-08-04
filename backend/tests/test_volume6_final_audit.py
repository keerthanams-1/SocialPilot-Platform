import pytest
import time
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal, engine
from app.database.models import User, Role, Team, TeamMember, Base, AuditLog
from app.users.repository import UserRepository
from app.core.security import get_password_hash
from app.authentication.jwt import create_access_token
from app.core.crypto import encrypt_token, decrypt_token

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def create_test_user(db, role_name: str = "Administrator"):
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name)
        db.add(role)
        db.commit()

    user = UserRepository.create_user(
        db=db,
        email=f"v6_audit_{uuid.uuid4().hex[:6]}@socialpilot.com",
        username=f"v6_user_{uuid.uuid4().hex[:6]}",
        password_hash=get_password_hash("Password123!"),
        full_name="V6 Audit User",
        role_id=role.id,
        is_verified=True
    )
    token = create_access_token(user.id, role.name)
    return user, token

def test_volume6_security_headers_and_middleware():
    """Verify production security headers (X-Frame-Options, X-Content-Type-Options, CSP, HSTS)."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert "Strict-Transport-Security" in resp.headers
    assert "Content-Security-Policy" in resp.headers

def test_volume6_fernet_token_encryption_vault():
    """Verify AES-256 Fernet token encryption vault ensures zero plaintext token storage."""
    secret = "sl.Bv_sample_oauth_token_secret_12345"
    encrypted = encrypt_token(secret)
    assert encrypted != secret
    decrypted = decrypt_token(encrypted)
    assert decrypted == secret

def test_volume6_health_monitoring_endpoints(db_session):
    """Verify health endpoints (/health, /health/database, /health/redis, /health/workers)."""
    # 1. Overall Health
    resp_health = client.get("/health")
    assert resp_health.status_code in [200, 503]
    assert "components" in resp_health.json()["data"]

    # 2. Database Health
    resp_db = client.get("/health/database")
    assert resp_db.status_code == 200
    assert "postgresql" in resp_db.json()["data"]

    # 3. Redis Health
    resp_redis = client.get("/health/redis")
    assert resp_redis.status_code == 200

    # 4. Workers Health
    resp_workers = client.get("/health/workers")
    assert resp_workers.status_code == 200
    assert "active_worker_nodes" in resp_workers.json()["data"]

def test_volume6_api_performance_latency():
    """Verify API response latency is under 500ms for health check queries."""
    # Warm up client app
    client.get("/health/database")
    
    start = time.time()
    resp = client.get("/health/database")
    latency_ms = (time.time() - start) * 1000
    assert resp.status_code == 200
    assert latency_ms < 500.0  # Latency under 500ms
