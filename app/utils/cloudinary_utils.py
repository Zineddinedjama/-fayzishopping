import logging
import os

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
