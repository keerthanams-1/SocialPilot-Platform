from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "socialpilot_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Celery production configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,        # 5 minutes max per task
    task_soft_time_limit=240,   # 4 minutes soft limit
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
)

# Celery Beat periodic scheduler configuration
celery_app.conf.beat_schedule = {
    "scan-scheduled-posts-every-minute": {
        "task": "app.publishing.tasks.dispatch_due_posts",
        "schedule": crontab(minute="*"),  # Every 1 minute
    },
    "refresh-expiring-social-tokens-daily": {
        "task": "app.social.tasks.refresh_expiring_tokens",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3:00 AM UTC
    },
    "sync-real-analytics-hourly": {
        "task": "app.analytics.tasks.fetch_social_analytics_job",
        "schedule": crontab(minute=0),  # Top of every hour
    },
}
