import logging
from celery import shared_task
from app.database.session import SessionLocal
from app.reports.scheduler import ReportSchedulerEngine

logger = logging.getLogger("socialpilot.workers.reports")

@shared_task(name="app.workers.report_tasks.execute_scheduled_reports_task")
def execute_scheduled_reports_task():
    """Celery task processing due scheduled report dispatches and email deliveries."""
    db = SessionLocal()
    try:
        res = ReportSchedulerEngine.process_due_report_schedules(db)
        return res
    finally:
        db.close()
