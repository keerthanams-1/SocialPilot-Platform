from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class WidgetItem(BaseModel):
    widget_key: str
    name: str
    category: str
    data: Dict[str, Any]

class AdminDashboardOut(BaseModel):
    role: str = "Administrator"
    total_users: int
    total_businesses: int
    active_campaigns: int
    system_health: Dict[str, Any]
    worker_status: Dict[str, Any]
    redis_status: Dict[str, Any]
    postgres_status: Dict[str, Any]
    mongodb_status: Dict[str, Any]
    api_health: Dict[str, Any]
    failed_publishing_jobs: int
    audit_logs: List[Dict[str, Any]]
    security_alerts: List[Dict[str, Any]]
    subscription_stats: Dict[str, Any]
    widgets: List[WidgetItem]

class BusinessDashboardOut(BaseModel):
    role: str = "Business User"
    campaign_overview: Dict[str, Any]
    scheduled_posts_count: int
    pending_approvals_count: int
    team_performance: Dict[str, Any]
    budget_tracking: Dict[str, Any]
    roi: Dict[str, Any]
    publishing_stats: Dict[str, Any]
    connected_accounts_count: int
    top_campaigns: List[Dict[str, Any]]
    monthly_growth: Dict[str, Any]
    widgets: List[WidgetItem]

class CreatorDashboardOut(BaseModel):
    role: str = "Content Creator"
    total_submitted_posts: int = 28
    scheduled_posts_count: int = 8
    published_posts_count: int = 15
    draft_posts_count: int = 4
    failed_posts_count: int = 1
    total_likes: int = 42100
    total_comments: int = 5850
    total_shares: int = 6850
    total_views: int = 485200
    engagement_rate: float = 8.42
    total_reach: int = 380000
    avg_engagement: float = 7.92
    best_performing_post: Optional[Dict[str, Any]] = None
    most_active_platform: str = "Instagram"
    highest_engagement_day: str = "Thursday"
    recent_posts: List[Dict[str, Any]] = []
    upcoming_scheduled_posts: List[Dict[str, Any]] = []
    monthly_published_trend: List[Dict[str, Any]] = []
    likes_trend: List[Dict[str, Any]] = []
    comments_trend: List[Dict[str, Any]] = []
    platform_engagement: List[Dict[str, Any]] = []
    weekly_activity: List[Dict[str, Any]] = []
    recent_notifications: List[Dict[str, Any]] = []
    media_library_count: int = 18
    assigned_campaigns: List[Dict[str, Any]] = []
    widgets: List[WidgetItem] = []

class MarketingDashboardOut(BaseModel):
    role: str = "Marketing Specialist"
    engagement_rate: float
    reach: int
    impressions: int
    ctr: float
    audience_growth: Dict[str, Any]
    top_performing_channels: List[Dict[str, Any]]
    campaign_roi_breakdown: List[Dict[str, Any]]
    scheduled_posts: List[Dict[str, Any]]
    widgets: List[WidgetItem]

class DashboardLayoutOut(BaseModel):
    user_id: str
    role_name: str
    layout_json: str
    theme: str
    default_date_range: str
    updated_at: datetime

class DashboardLayoutUpdate(BaseModel):
    layout_json: str
    theme: Optional[str] = "light"
    default_date_range: Optional[str] = "30d"
