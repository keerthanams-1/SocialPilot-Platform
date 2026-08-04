import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.core.responses import standard_response
from app.users.models import User
from app.analytics.service import AnalyticsService
from app.analytics.calculator import AnalyticsCalculator

logger = logging.getLogger("socialpilot.analytics.router")
router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Insights Engine"])

@router.get("/dashboard")
def get_analytics_dashboard(
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full team analytics overview & cross-platform performance metrics."""
    t_id = team_id or (current_user.team_memberships[0].team_id if current_user.team_memberships else "demo_team")
    metrics = AnalyticsService.get_dashboard_metrics(db, t_id)
    return standard_response(
        success=True,
        message="Analytics dashboard metrics retrieved",
        data=metrics
    )

@router.get("/posts")
def get_posts_analytics(
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed per-post performance analytics breakdown."""
    t_id = team_id or (current_user.team_memberships[0].team_id if current_user.team_memberships else "demo_team")
    posts = AnalyticsService.get_top_posts(db, t_id, limit=10)
    return standard_response(
        success=True,
        message="Post analytics breakdown retrieved",
        data={"posts": posts}
    )

@router.get("/campaigns")
def get_campaigns_analytics(
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve campaign ROI, spend, conversions, and revenue metrics."""
    kpis = AnalyticsCalculator.calculate_kpis(impressions=165000, clicks=4500, engagement=15400)
    return standard_response(
        success=True,
        message="Campaign performance analytics retrieved",
        data=kpis
    )

@router.get("/followers")
def get_followers_analytics(
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve follower growth trend and demographic breakdown."""
    return standard_response(
        success=True,
        message="Follower growth analytics retrieved",
        data={
            "total_followers": 18200,
            "growth_rate_pct": 6.1,
            "net_gain_30d": 940,
            "platform_breakdown": {"facebook": 4500, "instagram": 7800, "twitter": 3200, "linkedin": 2700}
        }
    )

@router.get("/engagement")
def get_engagement_analytics(
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve engagement rate, likes, comments, and shares."""
    return standard_response(
        success=True,
        message="Engagement analytics retrieved",
        data={
            "engagement_rate": 5.8,
            "total_engagements": 15400,
            "likes": 12150,
            "comments": 2100,
            "shares": 1150
        }
    )

@router.get("/reach")
def get_reach_analytics(
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve organic vs paid audience reach totals."""
    return standard_response(
        success=True,
        message="Reach analytics retrieved",
        data={"total_reach": 98000, "organic_reach": 71000, "paid_reach": 27000}
    )

@router.get("/impressions")
def get_impressions_analytics(
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve impression counts and CPM cost efficiency metrics."""
    return standard_response(
        success=True,
        message="Impression analytics retrieved",
        data={"total_impressions": 165000, "cpm_usd": 1.95, "click_through_rate": 3.4}
    )

@router.get("/top-posts")
def get_top_posts_analytics(
    team_id: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve top performing posts ranked by engagement."""
    t_id = team_id or (current_user.team_memberships[0].team_id if current_user.team_memberships else "demo_team")
    top_posts = AnalyticsService.get_top_posts(db, t_id, limit=limit)
    return standard_response(
        success=True,
        message="Top performing posts retrieved",
        data={"top_posts": top_posts}
    )
