import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import Post, PublishingLog
from app.database.mongo import get_mongo_db
from app.users.models import OAuthAccount
from app.social.providers import get_social_provider
from app.social.token_manager import TokenManager
from app.core.redis_lock import RedisLock

logger = logging.getLogger("socialpilot.publishing.publisher")

class RealPublisher:
    """Production real publishing engine with Redis distributed locking and MongoDB trace logging."""

    @staticmethod
    def publish_post_to_channels(
        db: Session,
        post_id: str,
        account_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise ValueError(f"Post {post_id} not found.")

        # Redis distributed lock to prevent multi-worker duplicate publishing
        lock_key = f"real_publisher:{post.id}"
        with RedisLock(lock_key, timeout_seconds=120) as lock:
            if not lock.acquired:
                logger.warning(f"Lock active for post {post.id}, skipping duplicate dispatch.")
                return {"status": "skipped_locked", "post_id": post.id}

            import json
            target_ids = account_ids
            if not target_ids:
                try:
                    target_ids = json.loads(post.platform_targets)
                except Exception:
                    target_ids = [post.platform_targets] if post.platform_targets else []

            results = []
            overall_success = True

            for acc_id in target_ids:
                account = db.query(OAuthAccount).filter(OAuthAccount.id == acc_id).first()
                if not account or not account.connected:
                    overall_success = False
                    continue

                provider_name = account.provider
                try:
                    valid_token = TokenManager.get_valid_access_token(db, account)
                    driver = get_social_provider(provider_name)

                    media_list = []
                    if post.media_urls:
                        try:
                            media_list = json.loads(post.media_urls)
                        except Exception:
                            media_list = [post.media_urls]

                    content_str = getattr(post, "content_text", None) or getattr(post, "content", "")
                    title_str = content_str[:100]

                    res = driver.publish_post(
                        access_token_val=valid_token,
                        content=content_str,
                        media_urls=media_list,
                        target_id=account.provider_user_id,
                        title=title_str
                    )

                    pub_log = PublishingLog(
                        post_id=post.id,
                        team_id=post.team_id,
                        platform=provider_name,
                        status="published",
                        published_at=datetime.utcnow()
                    )
                    db.add(pub_log)
                    results.append({"account_id": acc_id, "provider": provider_name, "status": "published", "response": res})

                except Exception as exc:
                    logger.error(f"Publishing failed on {provider_name} for post {post.id}: {exc}")
                    overall_success = False
                    pub_log = PublishingLog(
                        post_id=post.id,
                        team_id=post.team_id,
                        platform=provider_name,
                        status="failed",
                        error_message=str(exc)
                    )
                    db.add(pub_log)
                    results.append({"account_id": acc_id, "provider": provider_name, "status": "failed", "error": str(exc)})

            post.status = "published" if overall_success else "failed"
            db.commit()

            # Archive trace in MongoDB
            try:
                mongo_db = get_mongo_db()
                if mongo_db:
                    mongo_db.publishing_traces.insert_one({
                        "post_id": post.id,
                        "overall_success": overall_success,
                        "results": results,
                        "timestamp": datetime.utcnow()
                    })
            except Exception:
                pass

            return {"post_id": post.id, "status": post.status, "channel_results": results}
