import io
import logging
from PIL import Image

logger = logging.getLogger("socialpilot.media.image_processor")

class ImageProcessorEngine:
    """Pillow-based image optimization, auto-cropping, and resizing."""

    @staticmethod
    def process_and_resize(image_bytes: bytes, target_width: int = 1080) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            width, height = img.size
            if width > target_width:
                aspect = height / width
                target_height = int(target_width * aspect)
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

            out = io.BytesIO()
            img.save(out, format="JPEG", quality=85)
            return out.getvalue()
        except Exception as e:
            logger.warning(f"Image processing fallback: {e}")
            return image_bytes
