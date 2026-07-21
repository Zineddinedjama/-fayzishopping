import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to sys.path so 'app' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db

app = create_app()

@app.before_request
def _ensure_db():
    """Run create_all only once per cold start, guarded by a flag."""
    pass

# Create tables and seed admin on cold start
try:
    db_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_url.startswith("sqlite"):
        logger.error(
            "DATABASE_URL is sqlite — sqlite is not supported on Vercel serverless. "
            "Set DATABASE_URL to a PostgreSQL connection string."
        )
    with app.app_context():
        db.create_all()
        from app.models import Admin
        if not Admin.query.first():
            admin = Admin(username=app.config["ADMIN_USERNAME"])
            admin.set_password(app.config["ADMIN_PASSWORD"])
            db.session.add(admin)
            db.session.commit()
            logger.info("Default admin user created.")
except Exception:
    logger.exception("Failed to initialize database during cold start")
