import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from app.database.models import Post, SocialAccount
from app.users.models import OAuthAccount

logger = logging.getLogger("socialpilot.workers.scheduler")

class PostScheduler:
    """Scans relational database minute-by-minute for due posts and dispatches worker tasks."""

    @staticmethod
    def get_due_posts(db: Session) -> List[Post]:
        """Fetch all posts with scheduled_at <= now and status == 'scheduled'."""
        now = datetime.utcnow()
        due_posts = db.query(Post).filter(
            Post.status == "scheduled",
            Post.scheduled_at <= now
        ).all()
        logger.info(f"PostScheduler found {len(due_posts)} due posts for dispatch.")
        return due_posts

    @staticmethod
    def mark_post_processing(db: Session, post_id: str) -> None:
        """Mark post status as 'processing' to prevent duplicate execution across workers."""
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.status = "processing"
            db.commit()
