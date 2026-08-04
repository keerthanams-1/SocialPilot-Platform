import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models import Notification
from app.database.mongo import get_mongo_db
from app.notifications.email import EmailSender

logger = logging.getLogger("socialpilot.notifications.service")

class NotificationService:
    """Dispatches notifications across In-App DB, SMTP Email, and WebSocket channels."""

    @staticmethod
    def create_notification(
        db: Session,
        team_id: str,
        user_id: str,
        title: str,
        message: str,
        notif_type: str = "info",
        recipient_email: str = None
    ) -> Notification:
        notif = Notification(
            team_id=team_id,
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            is_read=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)

        # Send email notification if recipient email provided
        if recipient_email:
            EmailSender.send_email(
                to_email=recipient_email,
                subject=title,
                template_name=notif_type,
                context={"title": title, "message": message}
            )

        # Log event in MongoDB notification_events
        try:
            mongo = get_mongo_db()
            if mongo:
                mongo.notification_events.insert_one({
                    "notification_id": notif.id,
                    "team_id": team_id,
                    "user_id": user_id,
                    "title": title,
                    "type": notif_type,
                    "timestamp": datetime.utcnow()
                })
        except Exception as e:
            logger.warning(f"MongoDB notification archive fail-safe: {e}")

        return notif

    @staticmethod
    def get_user_notifications(db: Session, user_id: str) -> List[Notification]:
        return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()

    @staticmethod
    def mark_as_read(db: Session, notif_id: str) -> bool:
        notif = db.query(Notification).filter(Notification.id == notif_id).first()
        if not notif:
            return False
        notif.is_read = True
        db.commit()
        return True

    @staticmethod
    def delete_notification(db: Session, notif_id: str) -> bool:
        notif = db.query(Notification).filter(Notification.id == notif_id).first()
        if not notif:
            return False
        db.delete(notif)
        db.commit()
        return True
