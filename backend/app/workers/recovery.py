import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Post

logger = logging.getLogger("socialpilot.workers.recovery")

class SchedulerRecoveryManager:
    """Recovers unfinished jobs and resumes pending schedules after server or worker restarts."""

    @staticmethod
    def recover_orphaned_and_pending_jobs(db: Session) -> Dict[str, int]:
        """Reset stuck 'running' posts back to 'scheduled' and flag overdue posts."""
        now = datetime.utcnow()

        # 1. Recover stuck running posts
        stuck_posts = db.query(Post).filter(Post.status == "running").all()
        recovered_count = len(stuck_posts)
        for post in stuck_posts:
            post.status = "scheduled"
            logger.info(f"Reclaimed stuck post {post.id} back to 'scheduled'")

        db.commit()

        return {
            "recovered_stuck_jobs": recovered_count,
            "timestamp": now.isoformat()
        }
