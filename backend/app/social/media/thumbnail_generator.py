import io
import logging
from PIL import Image, ImageDraw

logger = logging.getLogger("socialpilot.media.thumbnail_generator")

class ThumbnailGenerator:
    """Generates preview thumbnail images for video uploads."""

    @staticmethod
    def generate_video_thumbnail(video_filename: str) -> bytes:
        img = Image.new("RGB", (640, 360), color=(30, 41, 59))
        draw = ImageDraw.Draw(img)
        draw.text((240, 170), f"Video Preview: {video_filename[:20]}", fill=(255, 255, 255))
        output = io.BytesIO()
        img.save(output, format="JPEG")
        return output.getvalue()
