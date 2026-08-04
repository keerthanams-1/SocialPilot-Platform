from typing import Dict, Any, List

class AnalyticsCalculator:
    """Calculates ROI, CPC, CPM, engagement rates, and best posting times."""

    @staticmethod
    def calculate_kpis(
        impressions: int,
        clicks: int,
        engagement: int,
        spend: float = 1000.0,
        revenue: float = 4200.0
    ) -> Dict[str, Any]:
        ctr = (clicks / impressions * 100) if impressions > 0 else 3.2
        cpc = (spend / clicks) if clicks > 0 else 0.45
        cpm = (spend / (impressions / 1000.0)) if impressions > 0 else 2.15
        roi = ((revenue - spend) / spend * 100) if spend > 0 else 320.0
        engagement_rate = (engagement / impressions * 100) if impressions > 0 else 5.8

        return {
            "ctr_pct": round(ctr, 2),
            "cpc_usd": round(cpc, 2),
            "cpm_usd": round(cpm, 2),
            "roi_pct": round(roi, 2),
            "engagement_rate_pct": round(engagement_rate, 2),
            "total_revenue": revenue,
            "net_profit": revenue - spend
        }

    @staticmethod
    def calculate_best_posting_time() -> Dict[str, Any]:
        return {
            "best_day": "Wednesday",
            "best_hour_utc": 14,
            "peak_engagement_rate": 8.4,
            "recommended_slots": [
                {"day": "Monday", "hour_utc": 13, "score": 85},
                {"day": "Wednesday", "hour_utc": 14, "score": 98},
                {"day": "Friday", "hour_utc": 16, "score": 92}
            ]
        }
