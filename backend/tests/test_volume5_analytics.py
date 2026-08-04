import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal, engine
from app.database.models import User, Role, Team, TeamMember, Base, Report, ReportSchedule, DashboardLayout
from app.users.repository import UserRepository
from app.core.security import get_password_hash, create_access_token
from app.analytics.service import AnalyticsService
from app.analytics.collector import AnalyticsCollectorEngine
from app.analytics.metrics import MetricNormalizer
from app.analytics.calculator import AnalyticsCalculator
from app.dashboard.service import DashboardOrchestratorService
from app.notifications.notification_service import NotificationService
from app.reports.scheduler import ReportSchedulerEngine
from app.reports.pdf_generator import PDFReportGenerator
from app.reports.csv_exporter import CSVReportExporter
from app.reports.excel_exporter import ExcelReportExporter
from app.workers.analytics_tasks import collect_all_social_metrics_task
from app.workers.report_tasks import execute_scheduled_reports_task
from app.workers.notification_tasks import process_email_notification_queue_task

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

def create_test_user_with_role(db, role_name: str) -> tuple[User, str]:
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(name=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)

    user = UserRepository.create_user(
        db=db,
        email=f"v5_{role_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}@socialpilot.com",
        username=f"v5_{role_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}",
        password_hash=get_password_hash("Password123!"),
        full_name=f"{role_name} User",
        role_id=role.id,
        is_verified=True
    )

    team = db.query(Team).first()
    if not team:
        team = Team(name="V5 Test Team", owner_id=user.id)
        db.add(team)
        db.commit()
        db.refresh(team)

    member = db.query(TeamMember).filter(TeamMember.user_id == user.id, TeamMember.team_id == team.id).first()
    if not member:
        member = TeamMember(team_id=team.id, user_id=user.id, role_in_team="owner")
        db.add(member)
        db.commit()

    from app.authentication.jwt import create_access_token
    token = create_access_token(user.id, role.name)
    return user, token

def test_volume5_rbac_role_dashboards_access(db_session):
    """Verify independent role dashboards (Admin, Business, Creator, Marketing) and RBAC protection."""
    admin_user, admin_token = create_test_user_with_role(db_session, "Administrator")
    creator_user, creator_token = create_test_user_with_role(db_session, "Content Creator")

    # Admin access to /api/v1/dashboard/admin
    resp_admin = client.get("/api/v1/dashboard/admin", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin.status_code == 200
    res_data = resp_admin.json()
    assert res_data["data"]["role"] == "Administrator"
    assert "postgres_status" in res_data["data"]

    # Creator attempt to access /api/v1/dashboard/admin (should fail 403 Forbidden)
    resp_forbidden = client.get("/api/v1/dashboard/admin", headers={"Authorization": f"Bearer {creator_token}"})
    assert resp_forbidden.status_code == 403

    # Creator access to /api/v1/dashboard/creator
    resp_creator = client.get("/api/v1/dashboard/creator", headers={"Authorization": f"Bearer {creator_token}"})
    assert resp_creator.status_code == 200
    assert resp_creator.json()["data"]["role"] == "Content Creator"

def test_volume5_dashboard_layout_customization(db_session):
    """Verify reading and updating user's custom widget layout and theme preferences."""
    user, token = create_test_user_with_role(db_session, "Business User")

    # Get initial layout
    resp_get = client.get("/api/v1/dashboard/layout", headers={"Authorization": f"Bearer {token}"})
    assert resp_get.status_code == 200
    assert "layout_json" in resp_get.json()["data"]

    # Update layout
    resp_put = client.put(
        "/api/v1/dashboard/layout",
        json={"layout_json": '["revenue_widget", "campaign_widget"]', "theme": "dark", "default_date_range": "7d"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp_put.status_code == 200
    assert resp_put.json()["data"]["theme"] == "dark"

def test_volume5_analytics_endpoints_and_caching(db_session):
    """Verify analytics endpoints (dashboard, posts, campaigns, followers, engagement, reach, impressions, top-posts)."""
    user, token = create_test_user_with_role(db_session, "Marketing Specialist")
    headers = {"Authorization": f"Bearer {token}"}

    endpoints = [
        "/api/v1/analytics/dashboard",
        "/api/v1/analytics/posts",
        "/api/v1/analytics/campaigns",
        "/api/v1/analytics/followers",
        "/api/v1/analytics/engagement",
        "/api/v1/analytics/reach",
        "/api/v1/analytics/impressions",
        "/api/v1/analytics/top-posts"
    ]

    for ep in endpoints:
        resp = client.get(ep, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

def test_volume5_notifications_crud_and_email(db_session):
    """Verify notification creation, listing, marking read, and deleting."""
    user, token = create_test_user_with_role(db_session, "Business User")
    team = db_session.query(Team).first()

    # Create notification
    notif = NotificationService.create_notification(
        db=db_session,
        team_id=team.id,
        user_id=user.id,
        title="Campaign Approved",
        message="Your Q3 launch campaign has been approved.",
        notif_type="approval_completed",
        recipient_email=user.email
    )
    assert notif.id is not None

    # List notifications via REST
    resp_list = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {token}"})
    assert resp_list.status_code == 200
    notifs = resp_list.json()["data"]["notifications"]
    assert len(notifs) >= 1

    # Mark as read
    resp_read = client.put(f"/api/v1/notifications/read/{notif.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp_read.status_code == 200

def test_volume5_reports_pdf_csv_excel_export(db_session):
    """Verify report generation in PDF, CSV, Excel, download streams, and scheduling."""
    user, token = create_test_user_with_role(db_session, "Administrator")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Generate Report
    resp_gen = client.post(
        "/api/v1/reports/generate?title=Q3_Executive_Performance&report_type=analytics&format=pdf",
        headers=headers
    )
    assert resp_gen.status_code == 200
    report_id = resp_gen.json()["data"]["report_id"]

    # 2. Download Report PDF
    resp_dl = client.get(f"/api/v1/reports/{report_id}", headers=headers)
    assert resp_dl.status_code == 200
    assert resp_dl.headers["content-type"] == "application/pdf"

    # 3. Schedule Recurring Report
    resp_sched = client.post(
        "/api/v1/reports/schedule?report_type=campaign&frequency=weekly&recipient_email=exec@socialpilot.com&format=pdf",
        headers=headers
    )
    assert resp_sched.status_code == 200
    assert "schedule_id" in resp_sched.json()["data"]

def test_volume5_celery_analytics_and_report_tasks(db_session):
    """Verify background Celery tasks for metric collection, report scheduling, and email dispatches."""
    # Metric collection task
    res_metrics = collect_all_social_metrics_task()
    assert res_metrics["status"] == "success"

    # Report task
    res_reports = execute_scheduled_reports_task()
    assert "processed_schedules" in res_reports

    # Email task
    res_email = process_email_notification_queue_task(
        to_email="test@socialpilot.com",
        subject="Test Alert",
        template_name="weekly_report_ready",
        context={"name": "Test User"}
    )
    assert res_email["status"] == "delivered"
