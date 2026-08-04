import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Post, RecurringJob

logger = logging.getLogger("socialpilot.publishing.recurring")

class RecurringJobEngine:
    """Manages recurring post schedules and generates scheduled instances."""

    @staticmethod
    def create_recurring_job(
        db: Session,
        post_id: str,
        cron_pattern: str,
        interval_days: int = 1
    ) -> RecurringJob:
        next_run = datetime.utcnow() + timedelta(days=interval_days)
        job = RecurringJob(
            post_id=post_id,
            cron_pattern=cron_pattern,
            next_run_at=next_run,
            status="active",
            total_runs=0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def process_due_recurring_jobs(db: Session) -> Dict[str, Any]:
        now = datetime.utcnow()
        jobs = db.query(RecurringJob).filter(
            RecurringJob.status == "active",
            RecurringJob.next_run_at <= now
        ).all()

        executed = 0
        for job in jobs:
            job.last_run_at = now
            job.total_runs += 1
            job.next_run_at = now + timedelta(days=1)
            executed += 1

        db.commit()
        return {"processed_jobs": executed, "timestamp": now.isoformat()}
