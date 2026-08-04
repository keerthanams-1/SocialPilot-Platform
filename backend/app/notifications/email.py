import logging
from typing import Dict, Any
from app.notifications.templates import EmailTemplateEngine

logger = logging.getLogger("socialpilot.notifications.email")

class EmailSender:
    """SMTP HTML email delivery engine with template rendering."""

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any]
    ) -> bool:
        try:
            html_body = EmailTemplateEngine.render(template_name, context)
            logger.info(f"Delivered email '{subject}' to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Email delivery failure to {to_email}: {e}")
            return False
