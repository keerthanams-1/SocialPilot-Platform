import io
from PIL import Image, ImageDraw

class VideoThumbnailGenerator:
    """Generates preview thumbnails for video posts."""

    @staticmethod
    def generate_thumbnail(title: str = "Video Preview") -> bytes:
        img = Image.new("RGB", (1280, 720), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)
        draw.text((450, 340), f"Play: {title[:30]}", fill=(255, 255, 255))
        out = io.BytesIO()
        img.save(out, format="JPEG")
        return out.getvalue()
