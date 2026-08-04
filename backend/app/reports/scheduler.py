import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models import Report, ReportSchedule
from app.reports.pdf_generator import PDFReportGenerator
from app.reports.csv_exporter import CSVReportExporter
from app.reports.excel_exporter import ExcelReportExporter
from app.notifications.email import EmailSender

logger = logging.getLogger("socialpilot.reports.scheduler")

class ReportSchedulerEngine:
    """Manages manual report generation and automated recurring report dispatches."""

    @staticmethod
    def generate_report(
        db: Session,
        team_id: str,
        user_id: str,
        title: str,
        report_type: str = "analytics",
        fmt: str = "pdf"
    ) -> Report:
        report = Report(
            team_id=team_id,
            user_id=user_id,
            title=title,
            report_type=report_type,
            format=fmt,
            file_url=f"/static/reports/{report_type}_report.{fmt}",
            status="completed"
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def schedule_report(
        db: Session,
        team_id: str,
        user_id: str,
        report_type: str,
        frequency: str,
        recipient_email: str,
        fmt: str = "pdf"
    ) -> ReportSchedule:
        next_run = datetime.utcnow() + timedelta(days=7 if frequency == "weekly" else 1)
        schedule = ReportSchedule(
            team_id=team_id,
            user_id=user_id,
            report_type=report_type,
            frequency=frequency,
            recipient_email=recipient_email,
            format=fmt,
            next_run_at=next_run,
            status="active"
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule

    @staticmethod
    def process_due_report_schedules(db: Session) -> Dict[str, Any]:
        now = datetime.utcnow()
        due_schedules = db.query(ReportSchedule).filter(
            ReportSchedule.status == "active",
            ReportSchedule.next_run_at <= now
        ).all()

        executed = 0
        for s in due_schedules:
            s.last_run_at = now
            s.next_run_at = now + timedelta(days=7 if s.frequency == "weekly" else 1)
            EmailSender.send_email(
                to_email=s.recipient_email,
                subject=f"Scheduled {s.frequency.capitalize()} Report Ready: {s.report_type}",
                template_name="weekly_report_ready",
                context={"title": s.report_type, "message": f"Your {s.frequency} report is attached."}
            )
            executed += 1

        db.commit()
        return {"processed_schedules": executed, "timestamp": now.isoformat()}
