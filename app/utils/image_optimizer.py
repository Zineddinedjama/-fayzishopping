import io
import logging
import re

from PIL import Image

logger = logging.getLogger(__name__)

MAX_DIMENSION = 1200
WEBP_QUALITY = 82
JPEG_QUALITY = 85
JPEG_FALLBACK_THRESHOLD = 4 * 1024 * 1024


def optimize_image(file, max_dimension=MAX_DIMENSION):
    try:
        file.seek(0)
        original_bytes = file.read()
        original_size = len(original_bytes)
        file.seek(0)

        img = Image.open(io.BytesIO(original_bytes))
        original_fmt = img.format
        original_dimensions = img.size

        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        if img.width > max_dimension or img.height > max_dimension:
            img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

        buf = io.BytesIO()

        try:
            img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=6)
            webp_size = buf.tell()
            buf.seek(0)

            if webp_size < original_size:
                logger.info(
                    "Optimized %s -> WebP: %dx%d %dKB -> %dKB (%.0f%% smaller)",
                    original_fmt,
                    img.width, img.height,
                    original_size // 1024,
                    webp_size // 1024,
                    (1 - webp_size / original_size) * 100,
                )
                return buf, "webp"
        except Exception as webp_err:
            logger.warning("WebP save failed: %s — falling back to JPEG", webp_err)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        jpeg_size = buf.tell()
        buf.seek(0)

        if jpeg_size < original_size:
            logger.info(
                "Optimized %s -> JPEG: %dx%d %dKB -> %dKB (%.0f%% smaller)",
                original_fmt,
                img.width, img.height,
                original_size // 1024,
                jpeg_size // 1024,
                (1 - jpeg_size / original_size) * 100,
            )
            return buf, "jpeg"

        logger.info("Original already optimal, uploading as-is (%dKB)", original_size // 1024)
        return io.BytesIO(original_bytes), _ext_for(original_fmt)

    except Exception as e:
        logger.exception("Image optimization failed: %s — uploading original", e)
        file.seek(0)
        return file, None


def _ext_for(fmt):
    mapping = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp", "GIF": "gif"}
    return mapping.get(fmt, "jpg")


def sanitize_filename(filename):
    return re.sub(r"[^\w\-_\. ]", "_", filename)
