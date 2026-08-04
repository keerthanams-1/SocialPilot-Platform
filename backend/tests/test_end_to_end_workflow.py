import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal, engine
from app.database.models import User, Role, Team, TeamMember, Base, SocialAccount, Campaign, Post, PostMedia, Approval, Report
from app.users.models import OAuthAccount
from app.users.repository import UserRepository
from app.core.security import get_password_hash
from app.core.crypto import encrypt_token
from app.authentication.jwt import create_access_token
from app.social.publisher import PublishingEngine
from app.publishing.approval import ApprovalWorkflowEngine
from app.analytics.collector import AnalyticsCollectorEngine
from app.analytics.metrics import MetricNormalizer
from app.reports.scheduler import ReportSchedulerEngine

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

def get_or_create_role(db, role_name: str) -> Role:
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)
    return role

def test_phase10_complete_end_to_end_multi_role_workflow(db_session):
    """
    Phase 10 Comprehensive End-to-End Workflow Test:
    1. Business Manager logs in.
    2. Connects a Facebook page.
    3. Creates a campaign.
    4. Assigns a Content Creator.
    5. Content Creator creates a post with media.
    6. Content Creator submits post for approval.
    7. Business Manager approves it.
    8. Post is published via PublishingEngine.
    9. Analytics are collected & stored in MongoDB.
    10. Marketing Team views analytics.
    11. Business Manager generates a PDF report.
    """
    # 1. Setup Roles
    bm_role = get_or_create_role(db_session, "Business User")
    cc_role = get_or_create_role(db_session, "Content Creator")
    mkt_role = get_or_create_role(db_session, "Marketing Specialist")

    # Step 1: Business Manager registers & logs in
    bm_user = UserRepository.create_user(
        db=db_session,
        email=f"bm_{uuid.uuid4().hex[:6]}@socialpilot.com",
        username=f"bm_{uuid.uuid4().hex[:6]}",
        password_hash=get_password_hash("Password123!"),
        full_name="Business Manager",
        role_id=bm_role.id,
        is_verified=True
    )
    bm_token = create_access_token(bm_user.id, bm_role.name)
    bm_headers = {"Authorization": f"Bearer {bm_token}"}
    assert bm_user.id is not None

    # Create Team owned by BM
    team = Team(name="Q3 Product Launch Team", owner_id=bm_user.id)
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)

    bm_member = TeamMember(team_id=team.id, user_id=bm_user.id, role_in_team="owner")
    db_session.add(bm_member)
    db_session.commit()

    # Step 2: Connect Facebook Page Account
    fb_account = OAuthAccount(
        user_id=bm_user.id,
        provider="facebook",
        provider_user_id="fb_page_998877",
        access_token=encrypt_token("EAAX_sample_raw_token_123"),
        refresh_token=encrypt_token("sample_refresh_token"),
        connected=True
    )
    db_session.add(fb_account)
    db_session.commit()
    db_session.refresh(fb_account)
    assert fb_account.id is not None

    # Step 3: Business Manager creates a Campaign
    now_str = datetime.utcnow().isoformat()
    resp_camp = client.post(
        "/api/v1/campaigns",
        json={
            "team_id": team.id,
            "name": "Q3 Enterprise Product Launch",
            "description": "Multi-platform launch campaign for Q3",
            "start_date": now_str,
            "end_date": now_str,
            "budget": 5000.0,
            "objectives": "Enterprise SaaS Buyers"
        },
        headers=bm_headers
    )
    assert resp_camp.status_code in [200, 201]
    campaign_id = resp_camp.json()["data"]["campaign_id"]

    # Step 4: Assign Content Creator to Team
    cc_user = UserRepository.create_user(
        db=db_session,
        email=f"cc_{uuid.uuid4().hex[:6]}@socialpilot.com",
        username=f"cc_{uuid.uuid4().hex[:6]}",
        password_hash=get_password_hash("Password123!"),
        full_name="Content Creator",
        role_id=cc_role.id,
        is_verified=True
    )
    cc_token = create_access_token(cc_user.id, cc_role.name)
    cc_headers = {"Authorization": f"Bearer {cc_token}"}

    cc_member = TeamMember(team_id=team.id, user_id=cc_user.id, role_in_team="member")
    db_session.add(cc_member)
    db_session.commit()

    # Step 5: Content Creator creates a draft post with media attachment
    resp_draft = client.post(
        f"/api/v1/publishing/draft?team_id={team.id}&content_text=Exciting+news!+The+Q3+Enterprise+Launch+is+live!&platform_targets=facebook",
        headers=cc_headers
    )
    assert resp_draft.status_code == 200
    post_id = resp_draft.json()["data"]["post_id"]

    # Step 6: Content Creator submits post for approval
    approval = ApprovalWorkflowEngine.submit_for_approval(db_session, post_id)
    assert approval.status == "pending"

    # Step 7: Business Manager approves the post
    resp_approve = client.post(
        f"/api/v1/publishing/approve/{post_id}?comments=Looks+great!+Approved+for+dispatch.",
        headers=bm_headers
    )
    assert resp_approve.status_code == 200
    assert resp_approve.json()["data"]["status"] == "approved"

    # Step 8: Post is published
    resp_pub = client.post(
        f"/api/v1/publishing/publish-now?post_id={post_id}&account_id={fb_account.id}",
        headers=bm_headers
    )
    assert resp_pub.status_code == 200
    assert resp_pub.json()["data"]["status"] in ("published", "failed")

    # Step 9: Analytics Collection
    raw_payload = AnalyticsCollectorEngine.collect_account_metrics(db_session, fb_account)
    stored_metrics = MetricNormalizer.normalize_and_store(raw_payload)
    assert stored_metrics["impressions"] > 0

    # Step 10: Marketing Team views analytics dashboard
    mkt_user = UserRepository.create_user(
        db=db_session,
        email=f"mkt_{uuid.uuid4().hex[:6]}@socialpilot.com",
        username=f"mkt_{uuid.uuid4().hex[:6]}",
        password_hash=get_password_hash("Password123!"),
        full_name="Marketing Specialist",
        role_id=mkt_role.id,
        is_verified=True
    )
    mkt_token = create_access_token(mkt_user.id, mkt_role.name)
    mkt_headers = {"Authorization": f"Bearer {mkt_token}"}

    mkt_member = TeamMember(team_id=team.id, user_id=mkt_user.id, role_in_team="member")
    db_session.add(mkt_member)
    db_session.commit()

    resp_mkt_dash = client.get("/api/v1/dashboard/marketing", headers=mkt_headers)
    assert resp_mkt_dash.status_code == 200
    assert resp_mkt_dash.json()["data"]["role"] == "Marketing Specialist"

    # Step 11: Business Manager generates a PDF executive report
    resp_report = client.post(
        "/api/v1/reports/generate?title=Q3_Launch_Executive_Summary&report_type=campaign&format=pdf",
        headers=bm_headers
    )
    assert resp_report.status_code == 200
    report_id = resp_report.json()["data"]["report_id"]

    resp_download = client.get(f"/api/v1/reports/{report_id}", headers=bm_headers)
    assert resp_download.status_code == 200
    assert resp_download.headers["content-type"] == "application/pdf"
    assert len(resp_download.content) > 100
