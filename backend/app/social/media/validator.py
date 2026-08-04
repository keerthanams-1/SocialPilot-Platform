from typing import Dict, Any, Tuple

PLATFORM_MEDIA_SPECS = {
    "facebook": {
        "max_image_size_mb": 10,
        "max_video_size_mb": 1024,
        "allowed_mime_types": ["image/jpeg", "image/png", "image/gif", "video/mp4", "video/quicktime"]
    },
    "instagram": {
        "max_image_size_mb": 8,
        "max_video_size_mb": 100,
        "allowed_mime_types": ["image/jpeg", "image/png", "video/mp4"]
    },
    "linkedin": {
        "max_image_size_mb": 5,
        "max_video_size_mb": 200,
        "allowed_mime_types": ["image/jpeg", "image/png", "image/gif", "video/mp4"]
    },
    "twitter": {
        "max_image_size_mb": 5,
        "max_video_size_mb": 512,
        "allowed_mime_types": ["image/jpeg", "image/png", "image/gif", "video/mp4"]
    },
    "youtube": {
        "max_video_size_mb": 2048,
        "allowed_mime_types": ["video/mp4", "video/quicktime", "video/x-msvideo"]
    }
}

class MediaValidator:
    """Validates image/video size, MIME format, and specs across platforms."""

    @staticmethod
    def validate(platform: str, filesize_bytes: int, mime_type: str) -> Tuple[bool, str]:
        platform_key = platform.lower()
        spec = PLATFORM_MEDIA_SPECS.get(platform_key, PLATFORM_MEDIA_SPECS["facebook"])

        if mime_type not in spec["allowed_mime_types"]:
            return False, f"MIME type '{mime_type}' not allowed for {platform}. Supported: {spec['allowed_mime_types']}"

        is_video = mime_type.startswith("video/")
        max_mb = spec["max_video_size_mb"] if is_video else spec["max_image_size_mb"]
        max_bytes = max_mb * 1024 * 1024

        if filesize_bytes > max_bytes:
            return False, f"File size ({filesize_bytes / (1024*1024):.2f}MB) exceeds {platform} limit of {max_mb}MB"

        return True, "Valid"
