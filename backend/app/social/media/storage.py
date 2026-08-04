import os
import uuid
import logging
from typing import Dict, Any

logger = logging.getLogger("socialpilot.media.storage")

class ObjectStorageClient:
    """AWS S3 / MinIO Compatible Cloud Storage Client."""

    def __init__(self):
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "socialpilot-media")
        self.cdn_base_url = os.getenv("CDN_BASE_URL", "https://media.socialpilot.io")

    def upload_file(self, file_bytes: bytes, filename: str, mime_type: str) -> Dict[str, Any]:
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        public_url = f"{self.cdn_base_url}/{self.bucket_name}/{unique_name}"
        return {
            "key": unique_name,
            "bucket": self.bucket_name,
            "media_url": public_url,
            "filesize": len(file_bytes),
            "mime_type": mime_type
        }
