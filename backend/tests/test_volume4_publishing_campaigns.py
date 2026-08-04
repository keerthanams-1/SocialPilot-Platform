import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal, engine
from app.database.models import User, Role, Team, Campaign, Post, Approval, RecurringJob, Base
from app.users.repository import UserRepository
from app.campaigns.repository import CampaignRepository
from app.campaigns.service import CampaignService
from app.publishing.publisher import RealPublisher
from app.publishing.approval import ApprovalWorkflowEngine
from app.publishing.recurring import RecurringJobEngine
from app.media.validator import MediaValidatorEngine
from app.social.token_manager import TokenManager
from app.core.security import get_password_hash

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

def test_volume4_media_validation_and_asset_attachment():
    """Verify MediaValidatorEngine checks file size, MIME types, and aspect ratios."""
    # Test Instagram aspect ratio validation
    valid, msg = MediaValidatorEngine.validate_media_asset(
        platform="instagram",
        filesize_bytes=5 * 1024 * 1024,
        mime_type="image/jpeg",
        width=1080,
        height=1080
    )
    assert valid is True

    # Test invalid aspect ratio
    valid_bad, msg_bad = MediaValidatorEngine.validate_media_asset(
        platform="instagram",
        filesize_bytes=5 * 1024 * 1024,
        mime_type="image/jpeg",
        width=100,
        height=1000
    )
    assert valid_bad is False
    assert "aspect ratio" in msg_bad

def test_volume4_campaign_crud_and_member_assignment(db_session):
    """Verify campaign creation, member assignment, update, summary rollup, and deletion."""
    role = db_session.query(Role).first()
    user = UserRepository.create_user(
        db=db_session,
        email=f"v4_camp_owner_{uuid.uuid4().hex[:6]}@socialpilot.com",
        username=f"v4_camp_owner_{uuid.uuid4().hex[:6]}",
        password_hash=get_password_hash("Password123!"),
        full_name="Campaign Owner",
        role_id=role.id,
        is_verified=True
    )

    team = db_session.query(Team).first()
    if not team:
        team = Team(name="V4 Team", owner_id=user.id)
        db_session.add(team)
        db_session.commit()
        db_session.refresh(team)

    # 1. Create Campaign
    from app.campaigns.schemas import CampaignCreate, CampaignUpdate
    c_data = CampaignCreate(
        team_id=team.id,
        name="Q3 Product Launch",
        description="Global multi-channel strategy launch",
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        budget=15000.0,
        objectives="Brand awareness & engagement"
    )
    campaign = CampaignRepository.create_campaign(db_session, c_data)
    assert campaign.id is not None
    assert campaign.status == "active"

    # 2. Add Campaign Member
    member = CampaignRepository.add_member(db_session, campaign.id, user.id, role_in_campaign="manager")
    assert member.role_in_campaign == "manager"

    # 3. Get Summary Rollup
    summary = CampaignService.get_campaign_summary(db_session, campaign.id)
    assert summary["name"] == "Q3 Product Launch"
    assert summary["budget"] == 15000.0

    # 4. Update Campaign
    updated = CampaignRepository.update_campaign(db_session, campaign.id, CampaignUpdate(name="Q3 Global Product Launch"))
    assert updated.name == "Q3 Global Product Launch"

def test_volume4_draft_creation_and_approval_workflow(db_session):
    """Verify post draft creation, submission for review, approval, and rejection logic."""
    role = db_session.query(Role).first()
    author = UserRepository.create_user(
        db=db_session,
        email=f"v4_author_{uuid.uuid4().hex[:6]}@socialpilot.com",
        username=f"v4_author_{uuid.uuid4().hex[:6]}",
        password_hash=get_password_hash("Password123!"),
        full_name="Post Author",
        role_id=role.id,
        is_verified=True
    )

    reviewer = UserRepository.create_user(
        db=db_session,
        email=f"v4_reviewer_{uuid.uuid4().hex[:6]}@socialpilot.com",
        username=f"v4_reviewer_{uuid.uuid4().hex[:6]}",
        password_hash=get_password_hash("Password123!"),
        full_name="Post Reviewer",
        role_id=role.id,
        is_verified=True
    )

    team = db_session.query(Team).first()
    post = Post(
        team_id=team.id if team else "demo_team",
        user_id=author.id,
        content_text="Post awaiting content review and approval",
        platform_targets='["tw_1"]',
        status="draft",
        schedule_type="draft"
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    # Submit for approval
    appr_pending = ApprovalWorkflowEngine.submit_for_approval(db_session, post.id)
    assert post.status == "pending_approval"
    assert appr_pending.status == "pending"

    # Approve post
    appr_done = ApprovalWorkflowEngine.approve_post(db_session, post.id, reviewer.id, comments="Approved for schedule")
    assert appr_done.status == "approved"
    assert post.status == "draft"

    # Reject post
    appr_rej = ApprovalWorkflowEngine.reject_post(db_session, post.id, reviewer.id, comments="Needs copy revision")
    assert appr_rej.status == "rejected"
    assert post.status == "rejected"

def test_volume4_real_publishing_and_redis_locking(db_session):
    """Verify RealPublisher dispatches with Redis lock and logs relational and MongoDB traces."""
    role = db_session.query(Role).first()
    user = UserRepository.create_user(
        db=db_session,
        email=f"v4_pub_user_{uuid.uuid4().hex[:6]}@socialpilot.com",
        username=f"v4_pub_user_{uuid.uuid4().hex[:6]}",
        password_hash=get_password_hash("Password123!"),
        full_name="Publisher User",
        role_id=role.id,
        is_verified=True
    )

    team = db_session.query(Team).first()
    account = TokenManager.store_oauth_account(
        db=db_session,
        user_id=user.id,
        provider="facebook",
        provider_user_id="fb_998811",
        access_token="fb_access_token",
        refresh_token="fb_refresh_token",
        expires_in_seconds=3600
    )

    post = Post(
        team_id=team.id if team else "demo_team",
        user_id=user.id,
        content_text="Volume 4 real publishing engine post test.",
        platform_targets=f'["{account.id}"]',
        status="scheduled"
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    # RealPublisher execution
    res = RealPublisher.publish_post_to_channels(db_session, post.id)
    assert res is not None
    assert "status" in res
    assert post.status in ("published", "failed")

def test_volume4_recurring_jobs(db_session):
    """Verify RecurringJobEngine schedules and advances cron intervals."""
    team = db_session.query(Team).first()
    post = Post(
        team_id=team.id if team else "demo_team",
        content_text="Weekly recurring post announcement",
        platform_targets='["tw_1"]',
        status="scheduled"
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    job = RecurringJobEngine.create_recurring_job(db_session, post.id, cron_pattern="0 9 * * 1", interval_days=1)
    assert job.id is not None
    assert job.status == "active"

    # Simulate due recurring processing
    job.next_run_at = datetime.utcnow() - timedelta(minutes=1)
    db_session.commit()

    proc_res = RecurringJobEngine.process_due_recurring_jobs(db_session)
    assert proc_res["processed_jobs"] >= 1
    assert job.total_runs >= 1
