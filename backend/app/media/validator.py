from typing import Tuple, Dict, Any

class MediaValidatorEngine:
    """Validates media resolution, aspect ratio, filesize, and MIME formats for social channels."""

    @staticmethod
    def validate_media_asset(
        platform: str,
        filesize_bytes: int,
        mime_type: str,
        width: int = 1080,
        height: int = 1080
    ) -> Tuple[bool, str]:
        platform_key = platform.lower()
        if filesize_bytes <= 0:
            return False, "Empty or invalid file size."

        if not (mime_type.startswith("image/") or mime_type.startswith("video/")):
            return False, f"Unsupported MIME type: {mime_type}"

        if platform_key == "instagram":
            if filesize_bytes > 100 * 1024 * 1024:
                return False, "Instagram file size exceeds 100MB limit."
            aspect_ratio = width / height if height > 0 else 1.0
            if aspect_ratio < 0.8 or aspect_ratio > 1.91:
                return False, f"Instagram aspect ratio {aspect_ratio:.2f} out of bounds [0.8, 1.91]."

        elif platform_key == "twitter":
            if filesize_bytes > 512 * 1024 * 1024:
                return False, "Twitter file size exceeds 512MB limit."

        return True, "Media asset complies with platform specifications."
