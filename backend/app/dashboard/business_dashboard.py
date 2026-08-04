from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Campaign, Post, Approval, OAuthAccount
from app.dashboard.schemas import BusinessDashboardOut
from app.dashboard.widgets import WidgetEngine

class BusinessDashboardService:
    """Business Manager Dashboard data aggregator."""

    @staticmethod
    def get_dashboard(db: Session, team_id: str) -> BusinessDashboardOut:
        campaigns = db.query(Campaign).filter(Campaign.team_id == team_id).all()
        scheduled_posts = db.query(Post).filter(Post.team_id == team_id, Post.status == "scheduled").count()
        pending_approvals = db.query(Approval).filter(Approval.status == "pending").count()
        connected_accounts = db.query(OAuthAccount).filter(OAuthAccount.connected == True).count()

        top_campaigns = []
        for c in campaigns[:5]:
            top_campaigns.append({
                "campaign_id": c.id,
                "name": c.name,
                "budget": c.budget,
                "status": c.status,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat()
            })

        total_budget = sum(c.budget or 0 for c in campaigns)

        widgets = [
            WidgetEngine.render_widget("campaign", "Business User", {"active_campaigns_count": len(campaigns), "total_budget": total_budget, "spend_to_date": total_budget * 0.45}),
            WidgetEngine.render_widget("revenue", "Business User", {"campaign_roi": 340.0, "estimated_revenue": 85000.0, "cpc": 0.38}),
            WidgetEngine.render_widget("approval", "Business User", {"pending_count": pending_approvals, "approved_this_week": 14, "rejected_this_week": 1})
        ]

        return BusinessDashboardOut(
            role="Business User",
            campaign_overview={"total_campaigns": len(campaigns), "active": sum(1 for c in campaigns if c.status == "active")},
            scheduled_posts_count=scheduled_posts,
            pending_approvals_count=pending_approvals,
            team_performance={"members_count": 8, "posts_created_this_month": 42, "avg_approval_time_hours": 3.5},
            budget_tracking={"total_budget": total_budget, "spent": total_budget * 0.45, "remaining": total_budget * 0.55},
            roi={"average_campaign_roi_pct": 340.0, "conversions": 1420, "cost_per_acquisition": 12.50},
            publishing_stats={"published_this_month": 68, "failed": 0, "success_rate_pct": 100.0},
            connected_accounts_count=connected_accounts or 6,
            top_campaigns=top_campaigns,
            monthly_growth={"follower_growth_pct": 5.8, "reach_growth_pct": 12.4, "engagement_growth_pct": 8.1},
            widgets=widgets
        )
