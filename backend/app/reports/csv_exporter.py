import csv
import io
from typing import List, Dict, Any

class CSVReportExporter:
    """Generates RFC 4180 compliant CSV exports for social metrics and post histories."""

    @staticmethod
    def export_posts_csv(posts_data: List[Dict[str, Any]]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow(["Post ID", "Platform", "Content Preview", "Impressions", "Engagements", "Likes", "Comments", "Shares", "Published Date"])

        for item in posts_data:
            writer.writerow([
                item.get("post_id", ""),
                item.get("platform", ""),
                item.get("content_text", ""),
                item.get("impressions", 0),
                item.get("engagements", 0),
                item.get("likes", 0),
                item.get("comments", 0),
                item.get("shares", 0),
                item.get("published_at", "")
            ])

        return output.getvalue()
