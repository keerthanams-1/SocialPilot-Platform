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
    draft_posts_count: int
    scheduled_posts_count: int
    rejected_posts_count: int
    pending_approval_count: int
    publishing_calendar: List[Dict[str, Any]]
    media_library_count: int
    personal_analytics: Dict[str, Any]
    assigned_campaigns: List[Dict[str, Any]]
    widgets: List[WidgetItem]

class MarketingDashboardOut(BaseModel):
    role: str = "Marketing Specialist"
    engagement_rate: float
    reach: int
    impressions: int
    ctr: float
    audience_growth: Dict[str, Any]
    campaign_roi: Dict[str, Any]
    top_performing_posts: List[Dict[str, Any]]
    best_posting_time: Dict[str, Any]
    platform_comparison: Dict[str, Any]
    widgets: List[WidgetItem]

class DashboardLayoutUpdate(BaseModel):
    layout_json: str
    theme: Optional[str] = "light"
    default_date_range: Optional[str] = "30d"

class DashboardLayoutOut(BaseModel):
    user_id: str
    role_name: str
    layout_json: str
    theme: str
    default_date_range: str
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
