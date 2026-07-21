import logging

try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

from flask import current_app

logger = logging.getLogger(__name__)


def configure_cloudinary():
    if not CLOUDINARY_AVAILABLE:
        logger.error("cloudinary SDK not installed")
        return False

    cloud_url = current_app.config.get("CLOUDINARY_URL", "")
    if cloud_url:
        cloudinary.config(cloudinary_url=cloud_url, secure=True)
        return True

    cloud_name = current_app.config.get("CLOUDINARY_CLOUD_NAME", "")
    api_key = current_app.config.get("CLOUDINARY_API_KEY", "")
    api_secret = current_app.config.get("CLOUDINARY_API_SECRET", "")
    if not cloud_name or not api_key or not api_secret:
        logger.error("Cloudinary config missing: CLOUDINARY_URL or CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET required")
        return False
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    return True


def upload_image(file, folder="fayzishopping/products"):
    if not file or not file.filename:
        logger.warning("upload_image called with empty file")
        return None
    if not configure_cloudinary():
        logger.error("upload_image aborted: Cloudinary not configured")
        return None
    try:
        logger.info("Uploading %s to Cloudinary folder=%s", file.filename, folder)
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            transformation=[
                {"width": 800, "height": 800, "crop": "limit"},
                {"quality": "auto"},
                {"fetch_format": "auto"},
            ],
        )
        url = result.get("secure_url")
        logger.info("Upload OK: %s -> %s", file.filename, url)
        return url
    except Exception as e:
        logger.exception("Cloudinary upload failed for %s: %s", file.filename, e)
        return None


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
