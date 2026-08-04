import logging
from typing import Dict, Any
from celery import shared_task
from app.notifications.email import EmailSender

logger = logging.getLogger("socialpilot.workers.notifications")

@shared_task(name="app.workers.notification_tasks.process_email_notification_queue_task")
def process_email_notification_queue_task(to_email: str, subject: str, template_name: str, context: Dict[str, Any]):
    """Celery worker task handling email queue processing and delivery retries."""
    ok = EmailSender.send_email(to_email, subject, template_name, context)
    return {"status": "delivered" if ok else "failed", "to_email": to_email}
