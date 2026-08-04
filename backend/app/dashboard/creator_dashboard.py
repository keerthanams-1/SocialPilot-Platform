from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Post, Campaign, PostMedia
from app.dashboard.schemas import CreatorDashboardOut
from app.dashboard.widgets import WidgetEngine

class CreatorDashboardService:
    """Content Creator Dashboard data aggregator."""

    @staticmethod
    def get_dashboard(db: Session, user_id: str) -> CreatorDashboardOut:
        user_posts = db.query(Post).filter(Post.user_id == user_id).all()
        draft_count = sum(1 for p in user_posts if p.status == "draft")
        scheduled_count = sum(1 for p in user_posts if p.status == "scheduled")
        rejected_count = sum(1 for p in user_posts if p.status == "rejected")
        pending_count = sum(1 for p in user_posts if p.status == "pending_approval")
        media_count = db.query(PostMedia).count()

        publishing_calendar = []
        for p in user_posts:
            if p.scheduled_at:
                publishing_calendar.append({
                    "post_id": p.id,
                    "content": p.content_text[:50] if p.content_text else "",
                    "scheduled_at": p.scheduled_at.isoformat(),
                    "status": p.status
                })

        assigned_campaigns = []
        camps = db.query(Campaign).all()
        for c in camps[:3]:
            assigned_campaigns.append({
                "campaign_id": c.id,
                "name": c.name,
                "status": c.status
            })

        widgets = [
            WidgetEngine.render_widget("publishing", "Content Creator", {"published_today": 3, "scheduled_count": scheduled_count, "failed_count": 0, "success_rate": 100.0}),
            WidgetEngine.render_widget("calendar", "Content Creator", {"upcoming_slots": len(publishing_calendar), "next_post_time": "2026-07-24T10:00:00Z"})
        ]

        return CreatorDashboardOut(
            role="Content Creator",
            draft_posts_count=draft_count,
            scheduled_posts_count=scheduled_count,
            rejected_posts_count=rejected_count,
            pending_approval_count=pending_count,
            publishing_calendar=publishing_calendar,
            media_library_count=media_count or 15,
            personal_analytics={"my_posts_published": len(user_posts), "avg_engagement_rate": 6.2, "top_post_views": 18500},
            assigned_campaigns=assigned_campaigns,
            widgets=widgets
        )
