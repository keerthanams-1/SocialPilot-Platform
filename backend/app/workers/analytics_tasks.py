import logging
from celery import shared_task
from app.database.session import SessionLocal
from app.users.models import OAuthAccount
from app.analytics.collector import AnalyticsCollectorEngine
from app.analytics.metrics import MetricNormalizer

logger = logging.getLogger("socialpilot.workers.analytics")

@shared_task(name="app.workers.analytics_tasks.collect_all_social_metrics_task")
def collect_all_social_metrics_task():
    """Celery periodic task executing every 15 minutes to collect raw metrics across connected accounts."""
    db = SessionLocal()
    collected_count = 0
    try:
        accounts = db.query(OAuthAccount).filter(OAuthAccount.connected == True).all()
        for account in accounts:
            try:
                raw_data = AnalyticsCollectorEngine.collect_account_metrics(db, account)
                MetricNormalizer.normalize_and_store(raw_data)
                collected_count += 1
            except Exception as e:
                logger.error(f"Failed metric collection for account {account.id}: {e}")
        return {"status": "success", "collected_accounts": collected_count}
    finally:
        db.close()
