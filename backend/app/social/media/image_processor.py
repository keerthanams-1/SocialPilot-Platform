import io
import logging
from PIL import Image

logger = logging.getLogger("socialpilot.media.image_processor")

class ImageProcessor:
    """Optimizes, resizes, and crops images for social network specifications."""

    @staticmethod
    def optimize_image(image_bytes: bytes, max_width: int = 1920, quality: int = 85) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            width, height = img.size
            if width > max_width:
                aspect_ratio = height / width
                new_height = int(max_width * aspect_ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            img.save(output, format="JPEG", quality=quality, optimize=True)
            return output.getvalue()
        except Exception as e:
            logger.warning(f"Image optimization fallback: {e}")
            return image_bytes
