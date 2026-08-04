from typing import Dict, Any, List

class WidgetEngine:
    """Reusable role-specific widget factory for dynamic dashboard rendering."""

    @staticmethod
    def render_widget(widget_key: str, role_name: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        key = widget_key.lower()
        if "follower" in key:
            return {
                "widget_key": "followers_widget",
                "name": "Follower Growth",
                "category": "analytics",
                "data": {
                    "total_followers": raw_data.get("total_followers", 14500),
                    "growth_rate_pct": raw_data.get("growth_rate_pct", 4.2),
                    "new_followers_30d": raw_data.get("new_followers_30d", 580)
                }
            }
        elif "engagement" in key:
            return {
                "widget_key": "engagement_widget",
                "name": "Engagement Metrics",
                "category": "analytics",
                "data": {
                    "engagement_rate": raw_data.get("engagement_rate", 5.4),
                    "total_likes": raw_data.get("total_likes", 12400),
                    "total_comments": raw_data.get("total_comments", 1850),
                    "total_shares": raw_data.get("total_shares", 920)
                }
            }
        elif "reach" in key:
            return {
                "widget_key": "reach_widget",
                "name": "Audience Reach",
                "category": "analytics",
                "data": {
                    "total_reach": raw_data.get("total_reach", 85000),
                    "organic_reach": raw_data.get("organic_reach", 62000),
                    "paid_reach": raw_data.get("paid_reach", 23000)
                }
            }
        elif "impression" in key:
            return {
                "widget_key": "impression_widget",
                "name": "Total Impressions",
                "category": "analytics",
                "data": {
                    "impressions": raw_data.get("impressions", 142000),
                    "cpm": raw_data.get("cpm", 2.15)
                }
            }
        elif "publishing" in key:
            return {
                "widget_key": "publishing_widget",
                "name": "Publishing Activity",
                "category": "publishing",
                "data": {
                    "published_today": raw_data.get("published_today", 12),
                    "scheduled_count": raw_data.get("scheduled_count", 28),
                    "failed_count": raw_data.get("failed_count", 0),
                    "success_rate": raw_data.get("success_rate", 98.5)
                }
            }
        elif "campaign" in key:
            return {
                "widget_key": "campaign_widget",
                "name": "Active Campaigns",
                "category": "business",
                "data": {
                    "active_campaigns_count": raw_data.get("active_campaigns_count", 5),
                    "total_budget": raw_data.get("total_budget", 25000.0),
                    "spend_to_date": raw_data.get("spend_to_date", 11200.0)
                }
            }
        elif "approval" in key:
            return {
                "widget_key": "approval_widget",
                "name": "Pending Approvals",
                "category": "publishing",
                "data": {
                    "pending_count": raw_data.get("pending_count", 4),
                    "approved_this_week": raw_data.get("approved_this_week", 18),
                    "rejected_this_week": raw_data.get("rejected_this_week", 2)
                }
            }
        elif "revenue" in key or "roi" in key:
            return {
                "widget_key": "revenue_widget",
                "name": "Campaign ROI & Revenue",
                "category": "business",
                "data": {
                    "campaign_roi": raw_data.get("campaign_roi", 312.5),
                    "estimated_revenue": raw_data.get("estimated_revenue", 78000.0),
                    "cpc": raw_data.get("cpc", 0.45)
                }
            }
        elif "notification" in key:
            return {
                "widget_key": "notification_widget",
                "name": "System Alerts",
                "category": "system",
                "data": {
                    "unread_count": raw_data.get("unread_count", 3),
                    "critical_alerts": raw_data.get("critical_alerts", 0)
                }
            }
        else:
            return {
                "widget_key": "calendar_widget",
                "name": "Publishing Calendar",
                "category": "publishing",
                "data": {
                    "upcoming_slots": raw_data.get("upcoming_slots", 14),
                    "next_post_time": raw_data.get("next_post_time", "2026-07-24T10:00:00Z")
                }
            }
