import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Table, Boolean, UniqueConstraint, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.session import Base

# Helper to support UUID in both PostgreSQL and SQLite
class GUID(String):
    """Placeholder for Postgres UUID or string representation in SQLite."""
    impl = String
    cache_ok = True

def generate_uuid():
    return str(uuid.uuid4())

# Many-to-many relationship mapping roles to permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), unique=True, nullable=False, index=True)

    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", back_populates="role")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), unique=True, nullable=False, index=True)

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

from app.users.models import (
    User, UserSession, UserLoginHistory,
    EmailVerification, PasswordReset, OAuthAccount
)

class Team(Base):
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="owned_teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    social_accounts = relationship("SocialAccount", back_populates="team", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="team", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="team", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="team", cascade="all, delete-orphan")

class TeamMember(Base):
    __tablename__ = "team_members"

    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_in_team = Column(String(50), default="member")  # admin, member, viewer, etc.
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_team_user"),
    )

class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Who connected it
    platform = Column(String(50), nullable=False)  # facebook, instagram, linkedin, twitter, youtube, pinterest
    platform_account_id = Column(String(100), nullable=False)  # external id
    account_name = Column(String(150), nullable=False)  # handle or name
    avatar_url = Column(String(255), nullable=True)
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="social_accounts")

class Post(Base):
    __tablename__ = "posts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # Author
    content_text = Column(String(2000), nullable=False)
    media_urls = Column(String(1000), nullable=True)  # JSON array string
    platform_targets = Column(String(1000), nullable=False)  # JSON array of connected account IDs
    schedule_type = Column(String(50), nullable=False, default="scheduled")  # scheduled, draft, recurring
    recurrence_pattern = Column(String(50), nullable=True)  # daily, weekly, monthly
    scheduled_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="scheduled")  # scheduled, published, failed, cancelled
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="posts")
    user = relationship("User", back_populates="posts")
    campaign = relationship("Campaign", back_populates="posts")
    publishing_logs = relationship("PublishingLog", back_populates="post", cascade="all, delete-orphan")
    metrics = relationship("PostMetric", back_populates="post", cascade="all, delete-orphan")

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(String(1000), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    budget = Column(Float, nullable=True)
    objectives = Column(String(1000), nullable=True)
    status = Column(String(50), nullable=False, default="active")  # active, completed, draft
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="campaigns")
    posts = relationship("Post", back_populates="campaign")
    members = relationship("CampaignMember", back_populates="campaign", cascade="all, delete-orphan")

class CampaignMember(Base):
    __tablename__ = "campaign_members"

    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_in_campaign = Column(String(50), default="contributor")  # manager, contributor, reviewer
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    campaign = relationship("Campaign", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("campaign_id", "user_id", name="uq_campaign_user"),
    )

class PostMedia(Base):
    __tablename__ = "post_media"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    media_url = Column(String(500), nullable=False)
    media_type = Column(String(50), nullable=False, default="image")  # image, video, thumbnail
    filesize = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post")

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, approved, rejected
    comments = Column(String(1000), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post")
    reviewer = relationship("User")

class RecurringJob(Base):
    __tablename__ = "recurring_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    cron_pattern = Column(String(100), nullable=False)  # e.g. "0 9 * * 1" (every Monday 9 AM)
    next_run_at = Column(DateTime, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="active")  # active, paused, completed
    total_runs = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post")

class PublishingLog(Base):
    __tablename__ = "publishing_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    platform = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)  # success, failed
    error_message = Column(String(1000), nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="publishing_logs")

class PostMetric(Base):
    __tablename__ = "post_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    engagements = Column(Integer, default=0)
    retrieved_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="metrics")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(String(1000), nullable=False)
    type = Column(String(50), nullable=False, default="info")  # success, error, info
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="notifications")
    user = relationship("User", back_populates="notifications")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_name = Column(String(100), nullable=False)
    user_email = Column(String(150), nullable=False)
    role_name = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)  # LOGIN, LOGOUT
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    report_type = Column(String(50), nullable=False)  # campaign, post, analytics, custom, system, audit
    format = Column(String(20), nullable=False, default="pdf")  # pdf, csv, xlsx
    file_url = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="completed")  # pending, completed, failed
    generated_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

class ReportSchedule(Base):
    __tablename__ = "report_schedules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_type = Column(String(50), nullable=False)
    frequency = Column(String(50), nullable=False, default="weekly")  # daily, weekly, monthly, quarterly, yearly
    recipient_email = Column(String(150), nullable=False)
    format = Column(String(20), nullable=False, default="pdf")
    cron_pattern = Column(String(100), nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="active")  # active, paused
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    widget_key = Column(String(100), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)  # analytics, publishing, system, business
    allowed_roles_json = Column(String(500), nullable=False)  # e.g. ["Administrator", "Business User"]
    created_at = Column(DateTime, default=datetime.utcnow)

class DashboardLayout(Base):
    __tablename__ = "dashboard_layouts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_name = Column(String(50), nullable=False)
    layout_json = Column(String(2000), nullable=False, default="[]")
    theme = Column(String(50), default="light")
    default_date_range = Column(String(50), default="30d")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")

class WidgetPreference(Base):
    __tablename__ = "widget_preferences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    widget_id = Column(String(36), ForeignKey("dashboard_widgets.id", ondelete="CASCADE"), nullable=False)
    is_visible = Column(Boolean, default=True)
    position_order = Column(Integer, default=0)
    config_json = Column(String(1000), nullable=True)

    # Relationships
    user = relationship("User")
    widget = relationship("DashboardWidget")

class DashboardTheme(Base):
    __tablename__ = "dashboard_themes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    theme_name = Column(String(50), default="default")
    primary_color = Column(String(20), default="#4F46E5")
    is_dark_mode = Column(Boolean, default=False)

    # Relationships
    user = relationship("User")

class SavedFilter(Base):
    __tablename__ = "saved_filters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filter_name = Column(String(150), nullable=False)
    filter_params_json = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")

class DashboardSetting(Base):
    __tablename__ = "dashboard_settings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    config_json = Column(String(2000), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")

class WorkspaceInvitation(Base):
    __tablename__ = "workspace_invitations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role_name = Column(String(50), nullable=False, default="Marketing Team")
    token = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=False, default="pending")  # pending, accepted, expired, cancelled
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team")



