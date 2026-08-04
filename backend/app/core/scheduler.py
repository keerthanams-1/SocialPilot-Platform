import asyncio
import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.database.models import Post, SocialAccount
from app.database.repositories import PublishingLogRepository, NotificationRepository
from app.database.schemas import PublishingLogCreate, NotificationCreate

async def publish_pending_posts(db: Session = None):
    is_local_session = False
    if db is None:
        db = SessionLocal()
        is_local_session = True
        
    try:
        now = datetime.utcnow()
        # Find scheduled posts where scheduled_at <= now and status == "scheduled"
        pending_posts = db.query(Post).filter(
            Post.status == "scheduled",
            Post.scheduled_at <= now
        ).all()

        for post in pending_posts:
            # Parse platforms
            try:
                platform_ids = json.loads(post.platform_targets)
            except Exception:
                platform_ids = []

            if not platform_ids:
                post.status = "failed"
                post.updated_at = datetime.utcnow()
                db.add(post)
                continue

            post_failed = False
            for ch_id in platform_ids:
                # Resolve account
                acc = db.query(SocialAccount).filter(SocialAccount.id == ch_id).first()
                if not acc:
                    # Log failure
                    PublishingLogRepository.create_log(db, PublishingLogCreate(
                        post_id=post.id,
                        team_id=post.team_id,
                        platform="unknown",
                        status="failed",
                        error_message=f"Target social account {ch_id} not found."
                    ))
                    post_failed = True
                    continue

                # Check credentials health
                is_expired = acc.expires_at is not None and acc.expires_at < datetime.utcnow()
                if is_expired:
                    # Log failure
                    PublishingLogRepository.create_log(db, PublishingLogCreate(
                        post_id=post.id,
                        team_id=post.team_id,
                        platform=acc.platform,
                        status="failed",
                        error_message=f"Connection expired for channel {acc.account_name}. Please re-authenticate."
                    ))
                    # Trigger failure notification
                    NotificationRepository.create_notification(db, NotificationCreate(
                        team_id=post.team_id,
                        user_id=post.user_id,
                        title="Publishing Dispatch Failed",
                        message=f"We were unable to publish your post to {acc.platform.capitalize()} because the connection expired.",
                        type="error"
                    ))
                    post_failed = True
                else:
                    # Log success (Simulated publication)
                    PublishingLogRepository.create_log(db, PublishingLogCreate(
                        post_id=post.id,
                        team_id=post.team_id,
                        platform=acc.platform,
                        status="success",
                        error_message=None
                    ))
                    # Trigger success notification
                    NotificationRepository.create_notification(db, NotificationCreate(
                        team_id=post.team_id,
                        user_id=post.user_id,
                        title="Post Published Successfully",
                        message=f"Your scheduled post was successfully published to {acc.platform.capitalize()}!",
                        type="success"
                    ))

            post.status = "failed" if post_failed else "published"
            post.updated_at = datetime.utcnow()
            db.add(post)

        db.commit()
    except Exception as e:
        print(f"Error in background publisher task: {e}")
        db.rollback()
        raise e
    finally:
        if is_local_session:
            db.close()

async def scheduler_loop():
    # Wait initially for startup to settle
    await asyncio.sleep(5)
    while True:
        try:
            await publish_pending_posts()
        except Exception:
            pass
        await asyncio.sleep(10)
