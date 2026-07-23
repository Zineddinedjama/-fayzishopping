import logging
import os
import re

try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

logger = logging.getLogger(__name__)


def configure_cloudinary():
    if not CLOUDINARY_AVAILABLE:
        logger.error("cloudinary SDK not installed — run: pip install cloudinary")
        return False

    cloud_url = os.environ.get("CLOUDINARY_URL", "")
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    api_key = os.environ.get("CLOUDINARY_API_KEY", "")
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", "")

    logger.debug("Cloudinary env: CLOUDINARY_URL=%s CLOUDINARY_CLOUD_NAME=%s CLOUDINARY_API_KEY=%s CLOUDINARY_API_SECRET=%s",
                 "SET" if cloud_url else "EMPTY",
                 "SET" if cloud_name else "EMPTY",
                 "SET" if api_key else "EMPTY",
                 "SET" if api_secret else "EMPTY")

    if cloud_url:
        cloudinary.config(cloudinary_url=cloud_url, secure=True)
        logger.info("Cloudinary configured via CLOUDINARY_URL")
        return True

    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )
        logger.info("Cloudinary configured via individual env vars")
        return True

    logger.error("Cloudinary config missing — set CLOUDINARY_URL or CLOUDINARY_CLOUD_NAME+API_KEY+API_SECRET in Vercel env vars")
    return False


def upload_image(file, folder="fayzishopping/products"):
    if not file or not file.filename:
        logger.warning("upload_image called with empty file")
        return None, "Fichier vide"

    if not configure_cloudinary():
        return None, "Cloudinary non configuré — vérifie les env vars Vercel"

    try:
        file.seek(0, 2)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        logger.info("Uploading %s (%.1f MB) to Cloudinary folder=%s", file.filename, size_mb, folder)

        if size_mb > 10:
            return None, f"Fichier trop volumineux ({size_mb:.1f} MB, max 10 MB)"

        from app.utils.image_optimizer import optimize_image, sanitize_filename

        optimized_file, used_format = optimize_image(file)
        if optimized_file is not file:
            optimized_file.seek(0, 2)
            new_size = optimized_file.tell() / (1024 * 1024)
            optimized_file.seek(0)
            logger.info("Upload after optimization: %.2f MB (was %.1f MB)", new_size, size_mb)

        safe_name = sanitize_filename(file.filename)
        base_name = safe_name.rsplit('.', 1)[0] if '.' in safe_name else safe_name

        optimized_file.seek(0)

        upload_params = {
            "folder": folder,
            "public_id": base_name,
            "resource_type": "image",
            "transformation": [
                {"width": 800, "height": 800, "crop": "limit"},
                {"quality": "auto"},
                {"fetch_format": "auto"},
            ],
        }

        result = cloudinary.uploader.upload(optimized_file, **upload_params)
        url = result.get("secure_url")
        logger.info("Upload OK: %s -> %s", file.filename, url)
        return url, None
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        logger.exception("Cloudinary upload failed for %s: %s", file.filename, error_msg)
        return None, error_msg


def delete_image(public_id):
    if not configure_cloudinary():
        return
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception:
        pass


def get_public_id_from_url(url):
    if not url or "cloudinary" not in url:
        return None
    parts = url.split("/")
    try:
        upload_idx = parts.index("upload")
        public_id_with_ext = "/".join(parts[upload_idx + 2:])
        public_id = ".".join(public_id_with_ext.split(".")[:-1])
        return public_id
    except (ValueError, IndexError):
        return None
