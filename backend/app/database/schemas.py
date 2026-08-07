import json
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

# ----------------- Security & Token Schemas -----------------
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    type: Optional[str] = None

# ----------------- User Schemas -----------------
class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)

class UserRegister(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    confirm_password: str
    role_name: Optional[str] = "Content Creator"  # Default fallback role

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("passwords do not match")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str

    @field_validator("confirm_new_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("passwords do not match")
        return v

class PermissionOut(BaseModel):
    id: str
    name: str

    class Config:
        from_attributes = True

class RoleOut(BaseModel):
    id: str
    name: str
    permissions: List[PermissionOut] = []

    class Config:
        from_attributes = True

class UserOut(UserBase):
    id: str
    status: str
    role: RoleOut
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------- Team Schemas -----------------
class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)

class TeamMemberAdd(BaseModel):
    email: EmailStr
    role_in_team: Optional[str] = "member"

class TeamMemberOut(BaseModel):
    user_id: str
    name: str
    email: str
    role_in_team: str
    joined_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def populate_user_details(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            user_obj = getattr(data, "user", None)
            if user_obj:
                return {
                    "user_id": getattr(data, "user_id"),
                    "name": getattr(user_obj, "name"),
                    "email": getattr(user_obj, "email"),
                    "role_in_team": getattr(data, "role_in_team"),
                    "joined_at": getattr(data, "joined_at")
                }
        return data

class TeamOut(BaseModel):
    id: str
    name: str
    owner_id: str
    created_at: datetime
    members: List[TeamMemberOut] = []

    class Config:
        from_attributes = True

class SocialAccountOut(BaseModel):
    id: str
    team_id: str
    user_id: Optional[str]
    platform: str
    platform_account_id: str
    account_name: str
    avatar_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    status: str = "connected"
    rate_limit_remaining: int = 100

    class Config:
        from_attributes = True

class OAuthCallbackIn(BaseModel):
    code: str
    state: str
    team_id: str

class PublishingLogCreate(BaseModel):
    post_id: str
    team_id: str
    platform: str
    status: str
    error_message: Optional[str] = None

class PublishingLogOut(BaseModel):
    id: str
    post_id: str
    team_id: str
    platform: str
    status: str
    error_message: Optional[str] = None
    published_at: datetime

    class Config:
        from_attributes = True

class PostMetricCreate(BaseModel):
    post_id: str
    platform: str
    impressions: int
    clicks: int
    engagements: int

class PostMetricOut(BaseModel):
    id: str
    post_id: str
    platform: str
    impressions: int
    clicks: int
    engagements: int
    retrieved_at: datetime

    class Config:
        from_attributes = True

class NotificationCreate(BaseModel):
    team_id: str
    user_id: str
    title: str
    message: str
    type: str = "info" # success, error, info

class NotificationOut(BaseModel):
    id: str
    team_id: str
    user_id: str
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    team_id: str
    content_text: str
    media_urls: Optional[List[str]] = []
    platform_targets: List[str]
    schedule_type: str = "scheduled"  # scheduled, draft, recurring
    recurrence_pattern: Optional[str] = None  # daily, weekly, monthly
    scheduled_at: Optional[datetime] = None
    campaign_id: Optional[str] = None

class PostUpdate(BaseModel):
    content_text: Optional[str] = None
    media_urls: Optional[List[str]] = None
    platform_targets: Optional[List[str]] = None
    schedule_type: Optional[str] = None
    recurrence_pattern: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None
    campaign_id: Optional[str] = None

class PostOut(BaseModel):
    id: str
    team_id: str
    user_id: Optional[str]
    content_text: str
    media_urls: List[str] = []
    platform_targets: List[str] = []
    schedule_type: str
    recurrence_pattern: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: str
    campaign_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    publishing_logs: List[PublishingLogOut] = []
    metrics: List[PostMetricOut] = []

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, values: Any) -> Any:
        # If values is a SQLAlchemy model instance, convert to a dict to prevent write-back side-effects
        if not isinstance(values, dict):
            data = {
                "id": getattr(values, "id", None),
                "team_id": getattr(values, "team_id", None),
                "user_id": getattr(values, "user_id", None),
                "content_text": getattr(values, "content_text", None),
                "media_urls": getattr(values, "media_urls", None),
                "platform_targets": getattr(values, "platform_targets", None),
                "schedule_type": getattr(values, "schedule_type", None),
                "recurrence_pattern": getattr(values, "recurrence_pattern", None),
                "scheduled_at": getattr(values, "scheduled_at", None),
                "status": getattr(values, "status", None),
                "campaign_id": getattr(values, "campaign_id", None),
                "created_at": getattr(values, "created_at", None),
                "updated_at": getattr(values, "updated_at", None),
                "publishing_logs": getattr(values, "publishing_logs", []),
                "metrics": getattr(values, "metrics", []),
            }
            for field in ["media_urls", "platform_targets"]:
                val = data[field]
                if isinstance(val, str):
                    try:
                        data[field] = json.loads(val)
                    except Exception:
                        data[field] = []
                elif isinstance(val, list):
                    data[field] = val
                else:
                    data[field] = []
            return data
        else:
            for field in ["media_urls", "platform_targets"]:
                val = values.get(field)
                if isinstance(val, str):
                    try:
                        values[field] = json.loads(val)
                    except Exception:
                        values[field] = []
                elif isinstance(val, list):
                    values[field] = val
                else:
                    values[field] = []
            return values

    class Config:
        from_attributes = True

class CampaignCreate(BaseModel):
    team_id: str
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    budget: Optional[float] = None
    objectives: Optional[str] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    objectives: Optional[str] = None
    status: Optional[str] = None

class CampaignOut(BaseModel):
    id: str
    team_id: str
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    budget: Optional[float] = None
    objectives: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    posts: List[PostOut] = []

    class Config:
        from_attributes = True
