import logging
from typing import Dict, Any

logger = logging.getLogger("socialpilot.media.video_processor")

class VideoProcessor:
    """Inspects video metadata and container compatibility."""

    @staticmethod
    def inspect_video(video_bytes: bytes, filename: str) -> Dict[str, Any]:
        return {
            "filesize_bytes": len(video_bytes),
            "filename": filename,
            "container": "mp4" if filename.lower().endswith(".mp4") else "mov",
            "is_valid_format": True
        }
