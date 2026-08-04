import logging
from celery import shared_task
from app.database.session import SessionLocal
from app.social.publisher import PublishingEngine
from app.social.token_manager import TokenManager
from app.workers.scheduler import PostScheduler
from app.workers.retry import RetryPolicyManager
from app.core.redis_lock import RedisLock

logger = logging.getLogger("socialpilot.workers.tasks")

# Priority Queue Mapping: Immediate -> critical, Scheduled -> normal, Analytics/Token -> low
QUEUE_PRIORITIES = {
    "immediate": "critical",
    "scheduled": "normal",
    "background": "low"
}

@shared_task(bind=True, max_retries=5)
def publish_scheduled_post_task(self, post_id: str, oauth_account_id: str, priority: str = "normal"):
    """Celery async task to execute multi-channel post publishing with Redis distributed lock & exponential backoff."""
    lock_key = f"post_publish:{post_id}"
    with RedisLock(lock_key, timeout_seconds=120) as lock:
        if not lock.acquired:
            logger.warning(f"Concurrent publishing lock active for post {post_id}. Skipping execution.")
            return {"status": "skipped_locked", "post_id": post_id}

        db = SessionLocal()
        try:
            logger.info(f"Executing Celery task [Priority: {priority}] for post {post_id} on channel {oauth_account_id}.")
            res = PublishingEngine.publish_post_to_channel(db, post_id, oauth_account_id)
            return res
        except Exception as exc:
            logger.error(f"Task failed for post {post_id}: {exc}")
            if RetryPolicyManager.should_retry(self.request.retries, exc):
                delay = RetryPolicyManager.calculate_exponential_backoff(self.request.retries)
                logger.info(f"Retrying task in {delay} seconds (Attempt {self.request.retries + 1}).")
                raise self.retry(exc=exc, countdown=delay)
            else:
                RetryPolicyManager.route_to_dead_letter_queue(
                    task_name="publish_scheduled_post_task",
                    payload={"post_id": post_id, "oauth_account_id": oauth_account_id},
                    exception=exc
                )
                raise exc
        finally:
            db.close()

@shared_task
def scan_and_dispatch_due_posts_task():
    """Celery Beat scheduled task scanning database every minute for due posts."""
    db = SessionLocal()
    try:
        due_posts = PostScheduler.get_due_posts(db)
        dispatched_count = 0
        for post in due_posts:
            PostScheduler.mark_post_processing(db, post.id)
            social_channel_id = getattr(post, "social_account_id", None) or getattr(post, "oauth_account_id", None)
            if social_channel_id:
                publish_scheduled_post_task.apply_async(
                    args=[post.id, social_channel_id],
                    priority=5  # Normal priority
                )
                dispatched_count += 1
        return {"scanned": len(due_posts), "dispatched": dispatched_count}
    finally:
        db.close()

@shared_task
def refresh_social_tokens_task():
    """Celery Beat daily background task refreshing near-expiry OAuth tokens."""
    db = SessionLocal()
    try:
        count = TokenManager.refresh_all_expiring_tokens(db)
        logger.info(f"Refreshed {count} expiring OAuth tokens.")
        return {"refreshed": count}
    finally:
        db.close()
