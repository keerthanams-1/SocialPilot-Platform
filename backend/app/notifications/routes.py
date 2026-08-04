from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_active_user, get_db
from app.database.models import User
from app.database.repositories import TeamRepository, NotificationRepository
from app.database.schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications Hub"])

@router.get("", response_model=List[NotificationOut])
def list_notifications(
    team_id: str,
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    member = TeamRepository.get_member(db, team_id=team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to team workspace"
        )
    return NotificationRepository.get_user_notifications(db, user_id=current_user.id, team_id=team_id, unread_only=unread_only)

@router.post("/{id}/read", response_model=NotificationOut)
def mark_notification_read(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify owner of notification
    notif = NotificationRepository.mark_as_read(db, notification_id=id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    if notif.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return notif

@router.post("/read-all")
def mark_all_notifications_read(
    team_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    member = TeamRepository.get_member(db, team_id=team_id, user_id=current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to team workspace"
        )
    count = NotificationRepository.mark_all_read(db, user_id=current_user.id, team_id=team_id)
    return {"count": count}
