import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.core.responses import standard_response
from app.users.models import User
from app.database.models import Post
from app.publishing.publisher import RealPublisher
from app.publishing.queue_manager import QueueManager
from app.publishing.approval import ApprovalWorkflowEngine
from app.publishing.recurring import RecurringJobEngine

logger = logging.getLogger("socialpilot.publishing.router")
router = APIRouter(prefix="/api/v1/publishing", tags=["Real Publishing & Workflow"])

@router.post("/draft")
def create_draft_post(
    team_id: str,
    content_text: str,
    platform_targets: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save content draft without scheduling."""
    post = Post(
        team_id=team_id,
        user_id=current_user.id,
        content_text=content_text,
        platform_targets=platform_targets,
        status="draft",
        schedule_type="draft"
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return standard_response(
        success=True,
        message="Draft post created successfully",
        data={"post_id": post.id, "status": post.status}
    )

@router.post("/publish-now")
def publish_now_endpoint(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Publish post immediately to all target channels using real drivers and Redis locks."""
    res = QueueManager.publish_now(db, post_id)
    return standard_response(
        success=True,
        message="Post publish-now dispatch completed",
        data=res
    )

@router.post("/schedule")
def schedule_post_endpoint(
    team_id: str,
    content_text: str,
    platform_targets: str,
    scheduled_at: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schedule post for future automated Celery dispatch."""
    post = Post(
        team_id=team_id,
        user_id=current_user.id,
        content_text=content_text,
        platform_targets=platform_targets,
        scheduled_at=scheduled_at,
        status="scheduled",
        schedule_type="scheduled"
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    return standard_response(
        success=True,
        message="Post scheduled successfully",
        data={"post_id": post.id, "scheduled_at": scheduled_at.isoformat(), "status": post.status}
    )

@router.post("/approve/{id}")
def approve_post_endpoint(
    id: str,
    comments: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve a post submitted for review."""
    approval = ApprovalWorkflowEngine.approve_post(db, post_id=id, reviewer_id=current_user.id, comments=comments)
    return standard_response(
        success=True,
        message="Post approved successfully",
        data={"approval_id": approval.id, "post_id": id, "status": approval.status}
    )

@router.post("/reject/{id}")
def reject_post_endpoint(
    id: str,
    comments: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject a post with mandatory feedback comments."""
    approval = ApprovalWorkflowEngine.reject_post(db, post_id=id, reviewer_id=current_user.id, comments=comments)
    return standard_response(
        success=True,
        message="Post rejected",
        data={"approval_id": approval.id, "post_id": id, "status": approval.status, "reason": comments}
    )

@router.get("/queue")
def get_queue_endpoint(
    team_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve scheduled publishing queue for team workspace."""
    queue_items = QueueManager.get_pending_queue(db, team_id)
    return standard_response(
        success=True,
        message="Publishing queue retrieved",
        data={"queue": queue_items}
    )

@router.get("/history")
def get_history_endpoint(
    team_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve published and failed post history for audit."""
    history_items = QueueManager.get_history(db, team_id)
    return standard_response(
        success=True,
        message="Publishing history retrieved",
        data={"history": history_items}
    )
