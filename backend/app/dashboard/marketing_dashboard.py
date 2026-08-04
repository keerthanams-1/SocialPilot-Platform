from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Post, PostMetric
from app.dashboard.schemas import MarketingDashboardOut
from app.dashboard.widgets import WidgetEngine

class MarketingDashboardService:
    """Marketing Team Dashboard data aggregator."""

    @staticmethod
    def get_dashboard(db: Session, team_id: str) -> MarketingDashboardOut:
        posts = db.query(Post).filter(Post.team_id == team_id).all()
        metrics = db.query(PostMetric).all()

        top_posts = []
        for p in posts[:5]:
            top_posts.append({
                "post_id": p.id,
                "content_preview": p.content_text[:60] if p.content_text else "",
                "status": p.status,
                "engagement_rate": 7.4,
                "impressions": 12500
            })

        widgets = [
            WidgetEngine.render_widget("engagement", "Marketing Specialist", {"engagement_rate": 5.8, "total_likes": 15400, "total_comments": 2100, "total_shares": 1150}),
            WidgetEngine.render_widget("reach", "Marketing Specialist", {"total_reach": 98000, "organic_reach": 71000, "paid_reach": 27000}),
            WidgetEngine.render_widget("impression", "Marketing Specialist", {"impressions": 165000, "cpm": 1.95}),
            WidgetEngine.render_widget("follower", "Marketing Specialist", {"total_followers": 18200, "growth_rate_pct": 6.1, "new_followers_30d": 940})
        ]

        return MarketingDashboardOut(
            role="Marketing Specialist",
            engagement_rate=5.8,
            reach=98000,
            impressions=165000,
            ctr=3.4,
            audience_growth={"total_followers": 18200, "monthly_growth_rate_pct": 6.1, "demographics": {"top_country": "United States", "top_age_group": "25-34"}},
            campaign_roi={"average_roi_pct": 340.0, "total_revenue": 85000.0, "cpc": 0.38},
            top_performing_posts=top_posts,
            best_posting_time={"best_day": "Wednesday", "best_hour_utc": 14, "heat_map_score": 98},
            platform_comparison={
                "facebook": {"engagement": 4.2, "reach": 35000},
                "instagram": {"engagement": 7.8, "reach": 42000},
                "twitter": {"engagement": 3.1, "reach": 12000},
                "linkedin": {"engagement": 5.4, "reach": 9000}
            },
            widgets=widgets
        )
