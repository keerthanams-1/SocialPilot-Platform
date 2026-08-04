import logging
from typing import Dict, Any, Optional
from app.social.media.validator import MediaValidator
from app.social.media.image_processor import ImageProcessor
from app.social.media.video_processor import VideoProcessor
from app.social.media.thumbnail_generator import ThumbnailGenerator
from app.social.media.storage import ObjectStorageClient

logger = logging.getLogger("socialpilot.media.service")

class MediaService:
    """Unified media service orchestrating validation, optimization, thumbnail generation, and S3 storage."""

    def __init__(self):
        self.storage = ObjectStorageClient()

    def process_and_upload(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        platform: str = "facebook"
    ) -> Dict[str, Any]:
        # 1. Validate against platform specs
        is_valid, msg = MediaValidator.validate(platform, len(file_bytes), mime_type)
        if not is_valid:
            raise ValueError(f"Media validation failed: {msg}")

        # 2. Process / optimize
        processed_bytes = file_bytes
        thumbnail_url = None

        if mime_type.startswith("image/"):
            processed_bytes = ImageProcessor.optimize_image(file_bytes)
        elif mime_type.startswith("video/"):
            thumb_bytes = ThumbnailGenerator.generate_video_thumbnail(filename)
            thumb_res = self.storage.upload_file(thumb_bytes, f"thumb_{filename}.jpg", "image/jpeg")
            thumbnail_url = thumb_res["media_url"]

        # 3. Upload to S3 / MinIO storage
        upload_res = self.storage.upload_file(processed_bytes, filename, mime_type)
        upload_res["thumbnail_url"] = thumbnail_url
        return upload_res
