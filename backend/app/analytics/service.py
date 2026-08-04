from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.analytics.repository import AnalyticsRepository
from app.analytics.calculator import AnalyticsCalculator
from app.analytics.dashboard import DashboardCacheManager

class AnalyticsService:
    """Business logic for cross-platform analytics aggregation, caching, and top post analysis."""

    @staticmethod
    def get_dashboard_metrics(db: Session, team_id: str) -> Dict[str, Any]:
        cache_key = f"overview:{team_id}"
        cached = DashboardCacheManager.get_cached_dashboard(cache_key)
        if cached:
            return cached

        data = AnalyticsRepository.get_team_overview(db, team_id)
        DashboardCacheManager.set_cached_dashboard(cache_key, data, ttl_seconds=300)
        return data

    @staticmethod
    def get_top_posts(db: Session, team_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        return [
            {
                "post_id": "post_101",
                "content_text": "🚀 Launching our new enterprise social marketing suite!",
                "platform": "linkedin",
                "impressions": 24500,
                "engagements": 2180,
                "likes": 1650,
                "comments": 340,
                "shares": 190,
                "published_at": "2026-07-22T10:00:00Z"
            },
            {
                "post_id": "post_102",
                "content_text": "Top 5 tips to boost organic social reach in 2026",
                "platform": "twitter",
                "impressions": 18200,
                "engagements": 1420,
                "likes": 980,
                "comments": 290,
                "shares": 150,
                "published_at": "2026-07-21T14:30:00Z"
            }
        ][:limit]
