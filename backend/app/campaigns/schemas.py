from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field

class CampaignMemberCreate(BaseModel):
    user_id: str
    role_in_campaign: str = "contributor"  # manager, contributor, reviewer

class CampaignMemberOut(BaseModel):
    campaign_id: str
    user_id: str
    role_in_campaign: str
    joined_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CampaignCreate(BaseModel):
    team_id: str
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    budget: Optional[float] = 0.0
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
    budget: Optional[float] = 0.0
    objectives: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    posts_count: Optional[int] = 0
    members: Optional[List[CampaignMemberOut]] = []
    model_config = ConfigDict(from_attributes=True)
