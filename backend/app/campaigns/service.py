from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models import Campaign, Post
from app.campaigns.repository import CampaignRepository

class CampaignService:
    """Business logic for campaign status transitions, post associations, and metrics aggregation."""

    @staticmethod
    def get_campaign_summary(db: Session, campaign_id: str) -> Dict[str, Any]:
        campaign = CampaignRepository.get_by_id(db, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found.")

        posts = db.query(Post).filter(Post.campaign_id == campaign_id).all()
        published_count = sum(1 for p in posts if p.status == "published")
        scheduled_count = sum(1 for p in posts if p.status == "scheduled")

        return {
            "campaign_id": campaign.id,
            "name": campaign.name,
            "status": campaign.status,
            "total_posts": len(posts),
            "published_posts": published_count,
            "scheduled_posts": scheduled_count,
            "budget": campaign.budget,
            "posts": [{"id": p.id, "status": p.status, "content_text": p.content_text} for p in posts]
        }
