import logging
from datetime import datetime
from typing import Dict, Any
from app.database.mongo import get_mongo_db

logger = logging.getLogger("socialpilot.analytics.metrics")

class MetricNormalizer:
    """Normalizes platform-specific metrics into standardized unified metrics schemas."""

    @staticmethod
    def normalize_and_store(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        metrics = raw_data.get("metrics", {})
        likes = int(metrics.get("likes", 0))
        comments = int(metrics.get("comments", 0))
        shares = int(metrics.get("shares", 0))
        views = int(metrics.get("views", 0))
        reach = int(metrics.get("reach", 0))
        impressions = int(metrics.get("impressions", 0))
        clicks = int(metrics.get("clicks", 0))
        followers = int(metrics.get("followers", 0))

        total_engagement = likes + comments + shares
        ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
        engagement_rate = (total_engagement / impressions * 100) if impressions > 0 else 0.0

        normalized = {
            "account_id": raw_data.get("account_id"),
            "provider": raw_data.get("provider"),
            "followers": followers,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "views": views,
            "reach": reach,
            "impressions": impressions,
            "clicks": clicks,
            "total_engagement": total_engagement,
            "ctr": round(ctr, 2),
            "engagement_rate": round(engagement_rate, 2),
            "timestamp": datetime.utcnow()
        }

        # Store in MongoDB analytics_metrics & time_series collections
        try:
            mongo = get_mongo_db()
            if mongo:
                mongo.analytics_metrics.insert_one(normalized.copy())
                mongo.time_series.insert_one({
                    "metadata": {"account_id": raw_data.get("account_id"), "provider": raw_data.get("provider")},
                    "timestamp": datetime.utcnow(),
                    "metrics": normalized
                })
        except Exception as e:
            logger.warning(f"MongoDB storage fail-safe: {e}")

        return normalized
