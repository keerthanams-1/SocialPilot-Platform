import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.core.responses import standard_response
from app.users.models import User
from app.notifications.notification_service import NotificationService

logger = logging.getLogger("socialpilot.notifications.router")
router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications Engine"])

@router.get("")
def list_user_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve in-app notifications for authenticated user."""
    notifs = NotificationService.get_user_notifications(db, current_user.id)
    n_list = []
    for n in notifs:
        n_list.append({
            "id": n.id,
            "team_id": n.team_id,
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat()
        })

    return standard_response(
        success=True,
        message="User notifications retrieved",
        data={"notifications": n_list}
    )

@router.put("/read/{id}")
def mark_notification_read(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    ok = NotificationService.mark_as_read(db, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")

    return standard_response(
        success=True,
        message="Notification marked as read",
        data={"notification_id": id}
    )

@router.delete("/{id}")
def delete_notification(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification."""
    ok = NotificationService.delete_notification(db, id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")

    return standard_response(
        success=True,
        message="Notification deleted successfully",
        data={"notification_id": id}
    )
