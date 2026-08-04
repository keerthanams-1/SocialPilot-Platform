from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AnalyticsOverviewOut(BaseModel):
    total_posts: int
    published_today: int
    scheduled: int
    failed: int
    followers: int
    engagement: int
    reach: int
    impressions: int
    comments: int
    likes: int
    shares: int
    video_views: int
    campaign_roi: float
    publishing_success_rate: float

class TopPostOut(BaseModel):
    post_id: str
    content_text: str
    platform: str
    impressions: int
    engagements: int
    likes: int
    comments: int
    shares: int
    published_at: Optional[str] = None

class SavedFilterCreate(BaseModel):
    filter_name: str
    filter_params_json: str

class SavedFilterOut(BaseModel):
    id: str
    team_id: str
    user_id: str
    filter_name: str
    filter_params_json: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
