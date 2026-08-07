import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_active_user, get_db
from app.database.models import User
from app.database.repositories import TeamRepository, SocialAccountRepository, PostRepository, PublishingLogRepository, NotificationRepository
from app.database.schemas import PostCreate, PostUpdate, PostOut, PublishingLogCreate, NotificationCreate

router = APIRouter(prefix="/posts", tags=["Content Scheduling"])

@router.post("", response_model=PostOut)
def create_scheduled_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 1. Resolve team_id automatically if missing or invalid
    t_id = payload.team_id
    if not t_id or t_id == "demo_team" or t_id == "":
        if current_user.team_memberships:
            t_id = current_user.team_memberships[0].team_id
        else:
            t_id = "team_enterprise_workspace_default"
    payload.team_id = t_id

    # 2. Time validations & auto-adjustment for scheduled posts
    if payload.schedule_type == "scheduled":
        if not payload.scheduled_at:
            payload.scheduled_at = datetime.utcnow() + timedelta(hours=1)
        else:
            # Ensure naive UTC timestamp comparison to prevent offset-naive vs offset-aware TypeError
            scheduled_naive = payload.scheduled_at.replace(tzinfo=None)
            now_naive = datetime.utcnow()
            if scheduled_naive < now_naive:
                payload.scheduled_at = now_naive + timedelta(minutes=5)

    # 3. Channel targets verification & fallback
    if not payload.platform_targets:
        payload.platform_targets = ["linkedin", "facebook", "instagram"]
        
    # Ensure platform_targets is a valid list of strings
    valid_targets = []
    for acc_id in payload.platform_targets:
        acc = SocialAccountRepository.get_by_id(db, account_id=acc_id)
        if acc:
            valid_targets.append(acc.id)
        else:
            # Check if it's a platform name string like "facebook", "linkedin", "instagram"
            valid_targets.append(str(acc_id))
    payload.platform_targets = valid_targets

    post = PostRepository.create_post(db, post_data=payload, user_id=current_user.id)
    return post

@router.get("", response_model=List[PostOut])
def get_scheduled_posts(
    team_id: Optional[str] = Query(None),
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    t_id = team_id
    if not t_id or t_id == "demo_team" or t_id == "":
        if current_user.team_memberships:
            t_id = current_user.team_memberships[0].team_id
        else:
            t_id = "team_enterprise_workspace_default"

    return PostRepository.get_by_team(
        db, team_id=t_id, status=status, start_date=start_date, end_date=end_date
    )

@router.put("/{id}", response_model=PostOut)
def update_scheduled_post(
    id: str,
    payload: PostUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    post = PostRepository.get_by_id(db, post_id=id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
        
    # Enforce membership to post's team
    member = TeamRepository.get_member(db, team_id=post.team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to target post"
        )

    # Time validation if updating schedule times
    if payload.scheduled_at and payload.schedule_type != "draft":
        if payload.scheduled_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Publish date cannot be set in the past"
            )

    updated_post = PostRepository.update_post(db, post_id=id, updates=payload)
    return updated_post

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_scheduled_post(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    post = PostRepository.get_by_id(db, post_id=id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
        
    # Check authorization permissions
    member = TeamRepository.get_member(db, team_id=post.team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to target post"
        )

    PostRepository.delete_post(db, post_id=id)
    return {"detail": "Scheduled post deleted successfully"}

@router.post("/{id}/publish", response_model=PostOut)
def publish_post_now(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Instantly dispatches post publishing simulation. Checks credentials validity."""
    post = PostRepository.get_by_id(db, post_id=id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
        
    member = TeamRepository.get_member(db, team_id=post.team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to target post"
        )

    # 1. Parse target platforms list from model string
    try:
        targets = json.loads(post.platform_targets)
    except Exception:
        targets = []

    # 2. Check channel connection health
    for acc_id in targets:
        acc = SocialAccountRepository.get_by_id(db, account_id=acc_id)
        if not acc:
            # Mark post as failed
            PostRepository.update_post(db, post_id=id, updates=PostUpdate(status="failed"))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target channel connection not found in team workspace."
            )
        # Check if the connection has expired
        if acc.expires_at and acc.expires_at < datetime.utcnow():
            PostRepository.update_post(db, post_id=id, updates=PostUpdate(status="failed"))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Publishing failed: Target connection '{acc.account_name}' has expired. Re-authenticate in Social Channels."
            )

    # 3. Mark post as published
    updated = PostRepository.update_post(db, post_id=id, updates=PostUpdate(status="published"))
    return updated

@router.post("/{id}/retry", response_model=PostOut)
def retry_failed_post(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    post = PostRepository.get_by_id(db, post_id=id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
        
    member = TeamRepository.get_member(db, team_id=post.team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to team workspace"
        )
        
    if post.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed posts can be retried"
        )

    # Re-publish logic
    try:
        platform_ids = json.loads(post.platform_targets)
    except Exception:
        platform_ids = []

    if not platform_ids:
        post.status = "failed"
        db.add(post)
        db.commit()
        return post

    post_failed = False
    for ch_id in platform_ids:
        acc = SocialAccountRepository.get_by_id(db, account_id=ch_id)
        if not acc:
            PublishingLogRepository.create_log(db, PublishingLogCreate(
                post_id=post.id,
                team_id=post.team_id,
                platform="unknown",
                status="failed",
                error_message=f"Target social account {ch_id} not found."
            ))
            post_failed = True
            continue

        # Check health
        is_expired = acc.expires_at is not None and acc.expires_at < datetime.utcnow()
        if is_expired:
            PublishingLogRepository.create_log(db, PublishingLogCreate(
                post_id=post.id,
                team_id=post.team_id,
                platform=acc.platform,
                status="failed",
                error_message=f"Connection expired for channel {acc.account_name}. Please re-authenticate."
            ))
            # Trigger failure notification
            NotificationRepository.create_notification(db, NotificationCreate(
                team_id=post.team_id,
                user_id=post.user_id,
                title="Publishing Dispatch Failed",
                message=f"We were unable to publish your post to {acc.platform.capitalize()} because the connection expired.",
                type="error"
            ))
            post_failed = True
        else:
            PublishingLogRepository.create_log(db, PublishingLogCreate(
                post_id=post.id,
                team_id=post.team_id,
                platform=acc.platform,
                status="success",
                error_message=None
            ))
            # Trigger success notification
            NotificationRepository.create_notification(db, NotificationCreate(
                team_id=post.team_id,
                user_id=post.user_id,
                title="Post Published Successfully",
                message=f"Your scheduled post was successfully published to {acc.platform.capitalize()}!",
                type="success"
            ))

    post.status = "failed" if post_failed else "published"
    post.updated_at = datetime.utcnow()
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@router.post("/cancel/{id}")
@router.post("/{id}/cancel")
def cancel_scheduled_post(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel a scheduled post."""
    post = PostRepository.get_by_id(db, post_id=id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    member = TeamRepository.get_member(db, team_id=post.team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    post.status = "cancelled"
    db.commit()
    return {"detail": f"Post {id} cancelled successfully", "status": "cancelled"}

@router.get("/queue")
def get_publishing_queue(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve scheduled/pending publishing queue."""
    member = TeamRepository.get_member(db, team_id=team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    posts = PostRepository.get_by_team(db, team_id=team_id, status="scheduled")
    return {"queue": [PostOut.model_validate(p) for p in posts]}

@router.get("/history")
def get_publishing_history(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve published/failed publishing history."""
    member = TeamRepository.get_member(db, team_id=team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(status_code=403, detail="Access denied")

    pub_posts = PostRepository.get_by_team(db, team_id=team_id, status="published")
    fail_posts = PostRepository.get_by_team(db, team_id=team_id, status="failed")
    return {
        "published": [PostOut.model_validate(p) for p in pub_posts],
        "failed": [PostOut.model_validate(p) for p in fail_posts]
    }

