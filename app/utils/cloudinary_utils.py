try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False

from flask import current_app


def configure_cloudinary():
    if not CLOUDINARY_AVAILABLE:
        return False
    cloud_name = current_app.config.get("CLOUDINARY_CLOUD_NAME", "")
    api_key = current_app.config.get("CLOUDINARY_API_KEY", "")
    api_secret = current_app.config.get("CLOUDINARY_API_SECRET", "")
    if not cloud_name or not api_key or not api_secret:
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
        return None
    if not configure_cloudinary():
        return None
    try:
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            transformation=[
                {"width": 800, "height": 800, "crop": "limit"},
                {"quality": "auto"},
                {"fetch_format": "auto"},
            ],
        )
        return result.get("secure_url")
    except Exception:
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
