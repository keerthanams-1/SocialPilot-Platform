from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Campaign, CampaignMember, Post
from app.campaigns.schemas import CampaignCreate, CampaignUpdate

class CampaignRepository:
    """Database repository for multi-platform campaigns and campaign members."""

    @staticmethod
    def create_campaign(db: Session, data: CampaignCreate) -> Campaign:
        campaign = Campaign(
            team_id=data.team_id,
            name=data.name,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            budget=data.budget,
            objectives=data.objectives,
            status="active"
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def get_by_id(db: Session, campaign_id: str) -> Optional[Campaign]:
        return db.query(Campaign).filter(Campaign.id == campaign_id).first()

    @staticmethod
    def list_by_team(db: Session, team_id: str) -> List[Campaign]:
        return db.query(Campaign).filter(Campaign.team_id == team_id).all()

    @staticmethod
    def update_campaign(db: Session, campaign_id: str, updates: CampaignUpdate) -> Optional[Campaign]:
        campaign = CampaignRepository.get_by_id(db, campaign_id)
        if not campaign:
            return None

        update_dict = updates.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(campaign, key, val)

        campaign.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def delete_campaign(db: Session, campaign_id: str) -> bool:
        campaign = CampaignRepository.get_by_id(db, campaign_id)
        if not campaign:
            return False
        from app.database.models import Post
        db.query(Post).filter(Post.campaign_id == campaign_id).update({"campaign_id": None})
        db.delete(campaign)
        db.commit()
        return True

    @staticmethod
    def add_member(db: Session, campaign_id: str, user_id: str, role_in_campaign: str = "contributor") -> CampaignMember:
        member = CampaignMember(
            campaign_id=campaign_id,
            user_id=user_id,
            role_in_campaign=role_in_campaign
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member
