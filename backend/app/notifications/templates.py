class EmailTemplateEngine:
    """Renders responsive HTML email templates for alerts, onboarding, and reports."""

    @staticmethod
    def render(template_name: str, context: dict) -> str:
        title = context.get("title", "SocialPilot Notification")
        message = context.get("message", "")
        recipient_name = context.get("name", "User")

        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"><title>{title}</title></head>
        <body style="font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px;">
          <div style="max-width: 600px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 12px;">
            <h2 style="color: #6366f1;">SocialPilot Platform</h2>
            <h3>{title}</h3>
            <p>Hello {recipient_name},</p>
            <p style="font-size: 16px; line-height: 1.5;">{message}</p>
            <hr style="border: 0; border-top: 1px solid #334155; margin: 20px 0;" />
            <p style="font-size: 12px; color: #94a3b8;">Sent automatically by SocialPilot SaaS System.</p>
          </div>
        </body>
        </html>
        """
