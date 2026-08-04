import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models import PostMedia

logger = logging.getLogger("socialpilot.publishing.media_service")

class PublishingMediaService:
    """Links validated media assets to posts in PostgreSQL post_media table."""

    @staticmethod
    def attach_media_to_post(
        db: Session,
        post_id: str,
        media_url: str,
        media_type: str = "image",
        filesize: int = None,
        width: int = None,
        height: int = None,
        mime_type: str = "image/jpeg"
    ) -> PostMedia:
        post_media = PostMedia(
            post_id=post_id,
            media_url=media_url,
            media_type=media_type,
            filesize=filesize,
            width=width,
            height=height,
            mime_type=mime_type
        )
        db.add(post_media)
        db.commit()
        db.refresh(post_media)
        return post_media
