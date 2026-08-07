import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_active_user
from app.users.models import User

logger = logging.getLogger("socialpilot.analytics.router")
router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Insights Engine"])

DEMO_PAYLOAD = {
  "summary": {
    "total_impressions": 485200,
    "total_clicks": 38450,
    "total_engagements": 54800,
    "average_ctr": 7.92,
    "total_followers": 128400,
    "total_reach": 380000,
    "total_likes": 42100,
    "total_shares": 6850,
    "total_comments": 5850,
    "estimated_roi": "485%"
  },
  "timeframe": "30d",
  "timeline_trends": [
    { "date": "Mon 1", "impressions": 28500, "clicks": 2120, "engagements": 3400 },
    { "date": "Tue 1", "impressions": 36100, "clicks": 3150, "engagements": 4800 },
    { "date": "Wed 1", "impressions": 32800, "clicks": 2710, "engagements": 4150 },
    { "date": "Thu 1", "impressions": 48900, "clicks": 4150, "engagements": 6200 },
    { "date": "Fri 1", "impressions": 42400, "clicks": 3400, "engagements": 5300 },
    { "date": "Sat 1", "impressions": 31200, "clicks": 2250, "engagements": 3900 },
    { "date": "Sun 1", "impressions": 35500, "clicks": 2670, "engagements": 4250 },
    { "date": "Mon 2", "impressions": 41200, "clicks": 3180, "engagements": 5100 },
    { "date": "Tue 2", "impressions": 49800, "clicks": 4210, "engagements": 6450 },
    { "date": "Wed 2", "impressions": 44500, "clicks": 3890, "engagements": 5800 },
    { "date": "Thu 2", "impressions": 52100, "clicks": 4650, "engagements": 7100 },
    { "date": "Fri 2", "impressions": 47800, "clicks": 4120, "engagements": 6250 },
    { "date": "Sat 2", "impressions": 38400, "clicks": 2950, "engagements": 4800 },
    { "date": "Sun 2", "impressions": 42900, "clicks": 3450, "engagements": 5400 }
  ],
  "platform_breakdown": [
    { "platform": "facebook", "name": "Facebook Pages", "posts_count": 34, "impressions": 168500, "engagements": 21400, "share_pct": 35 },
    { "platform": "instagram", "name": "Instagram Business", "posts_count": 42, "impressions": 146200, "engagements": 19800, "share_pct": 30 },
    { "platform": "linkedin", "name": "LinkedIn Company", "posts_count": 28, "impressions": 94100, "engagements": 11200, "share_pct": 20 },
    { "platform": "twitter", "name": "X / Twitter Profile", "posts_count": 56, "impressions": 58200, "engagements": 6100, "share_pct": 12 },
    { "platform": "youtube", "name": "YouTube Channel", "posts_count": 12, "impressions": 42100, "engagements": 4800, "share_pct": 8 }
  ],
  "audience_geo": [
    { "country": "United States", "code": "US", "flag": "🇺🇸", "percentage": 38, "count": "184,376" },
    { "country": "India", "code": "IN", "flag": "🇮🇳", "percentage": 26, "count": "126,152" },
    { "country": "United Kingdom", "code": "UK", "flag": "🇬🇧", "percentage": 16, "count": "77,632" },
    { "country": "Germany", "code": "DE", "flag": "🇩🇪", "percentage": 12, "count": "58,224" },
    { "country": "Canada", "code": "CA", "flag": "🇨🇦", "percentage": 8, "count": "38,816" }
  ],
  "audience_demographics": [
    { "group": "25 – 34 yrs", "percentage": 42 },
    { "group": "35 – 44 yrs", "percentage": 28 },
    { "group": "18 – 24 yrs", "percentage": 18 },
    { "group": "45 – 54 yrs", "percentage": 8 },
    { "group": "55+ yrs", "percentage": 4 }
  ],
  "top_performing_posts": [
    {
      "id": "1",
      "content_text": "🚀 SocialPilot 2.0 Feature Release: Multi-Channel Publishing, Automated Calendars & Real-Time Analytics!",
      "platform": "linkedin",
      "impressions": 84500,
      "clicks": 6420,
      "engagements": 9800,
      "ctr": "7.60%",
      "scheduled_at": "2026-08-05T10:00:00Z"
    },
    {
      "id": "2",
      "content_text": "💡 5 Proven Social Media Growth Strategies for Enterprise SaaS Teams. Check out our breakdown!",
      "platform": "instagram",
      "impressions": 72400,
      "clicks": 5890,
      "engagements": 8300,
      "ctr": "8.13%",
      "scheduled_at": "2026-08-03T14:30:00Z"
    },
    {
      "id": "3",
      "content_text": "🎉 Live Q&A Stream: Scaling Brand Awareness & Lead Generation across Meta & LinkedIn.",
      "platform": "facebook",
      "impressions": 59100,
      "clicks": 4150,
      "engagements": 6200,
      "ctr": "7.02%",
      "scheduled_at": "2026-08-01T16:00:00Z"
    }
  ]
}

@router.get("/dashboard")
def get_analytics_dashboard(
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve full team analytics overview & cross-platform performance metrics."""
    return {"status": "success", "data": DEMO_PAYLOAD}

@router.get("/posts")
def get_posts_analytics(
    team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve detailed per-post performance analytics breakdown."""
    return {"status": "success", "data": DEMO_PAYLOAD["top_performing_posts"]}
