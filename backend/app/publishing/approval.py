import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database.models import Post, Approval, Notification

logger = logging.getLogger("socialpilot.publishing.approval")

class ApprovalWorkflowEngine:
    """Manages post submission for review, approvals, and rejections."""

    @staticmethod
    def submit_for_approval(db: Session, post_id: str) -> Approval:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise ValueError(f"Post {post_id} not found.")

        post.status = "pending_approval"
        approval = Approval(
            post_id=post_id,
            status="pending"
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        return approval

    @staticmethod
    def approve_post(db: Session, post_id: str, reviewer_id: str, comments: Optional[str] = None) -> Approval:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise ValueError(f"Post {post_id} not found.")

        approval = db.query(Approval).filter(Approval.post_id == post_id, Approval.status == "pending").first()
        if not approval:
            approval = Approval(post_id=post_id)
            db.add(approval)

        approval.status = "approved"
        approval.reviewer_id = reviewer_id
        approval.comments = comments
        approval.reviewed_at = datetime.utcnow()

        post.status = "scheduled" if post.scheduled_at else "draft"
        db.commit()
        db.refresh(approval)
        return approval

    @staticmethod
    def reject_post(db: Session, post_id: str, reviewer_id: str, comments: str) -> Approval:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise ValueError(f"Post {post_id} not found.")

        approval = db.query(Approval).filter(Approval.post_id == post_id, Approval.status == "pending").first()
        if not approval:
            approval = Approval(post_id=post_id)
            db.add(approval)

        approval.status = "rejected"
        approval.reviewer_id = reviewer_id
        approval.comments = comments
        approval.reviewed_at = datetime.utcnow()

        post.status = "rejected"
        db.commit()
        db.refresh(approval)
        return approval
