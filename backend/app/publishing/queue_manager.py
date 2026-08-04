import logging
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Post
from app.publishing.publisher import RealPublisher

logger = logging.getLogger("socialpilot.publishing.queue_manager")

class QueueManager:
    """Manages publishing queue, publish-now dispatches, and schedule queue inspection."""

    @staticmethod
    def publish_now(db: Session, post_id: str) -> Dict[str, Any]:
        return RealPublisher.publish_post_to_channels(db, post_id)

    @staticmethod
    def get_pending_queue(db: Session, team_id: str) -> List[Dict[str, Any]]:
        posts = db.query(Post).filter(
            Post.team_id == team_id,
            Post.status == "scheduled"
        ).order_by(Post.scheduled_at.asc()).all()

        queue_items = []
        for p in posts:
            queue_items.append({
                "post_id": p.id,
                "team_id": p.team_id,
                "content_text": p.content_text,
                "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None,
                "status": p.status
            })
        return queue_items

    @staticmethod
    def get_history(db: Session, team_id: str) -> List[Dict[str, Any]]:
        posts = db.query(Post).filter(
            Post.team_id == team_id,
            Post.status.in_(["published", "failed"])
        ).order_by(Post.updated_at.desc()).all()

        history_items = []
        for p in posts:
            history_items.append({
                "post_id": p.id,
                "team_id": p.team_id,
                "content_text": p.content_text,
                "status": p.status,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            })
        return history_items
