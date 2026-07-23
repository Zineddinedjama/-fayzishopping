import io
import logging
import re

from PIL import Image

logger = logging.getLogger(__name__)

MAX_DIMENSION = 1200
WEBP_QUALITY = 82
JPEG_QUALITY = 85

HEIC_MAGIC = b"ftypheic"
HEIF_MAGIC = b"ftypmif1"


def _is_heic(data):
    return HEIC_MAGIC in data[:32] or HEIF_MAGIC in data[:32]


def _try_heic_to_pil(data):
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        return Image.open(io.BytesIO(data))
    except ImportError:
        logger.warning("pillow-heif not installed — cannot convert HEIC")
        return None
    except Exception as e:
        logger.warning("HEIC conversion failed: %s", e)
        return None


def optimize_image(file, max_dimension=MAX_DIMENSION):
    try:
        file.seek(0)
        original_bytes = file.read()
        original_size = len(original_bytes)
        file.seek(0)

        if _is_heic(original_bytes):
            logger.info("Detected HEIC/HEIF image, attempting conversion")
            img = _try_heic_to_pil(original_bytes)
            if img is None:
                logger.warning("HEIC conversion unavailable, uploading original")
                file.seek(0)
                return file, None
        else:
            img = Image.open(io.BytesIO(original_bytes))

        original_fmt = img.format

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
