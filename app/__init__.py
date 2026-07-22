from flask import Flask
from app.config import Config
from app.extensions import db, migrate, login_manager, csrf


def _auto_migrate(app):
    with app.app_context():
        from sqlalchemy import inspect, text
        try:
            inspector = inspect(db.engine)
            columns = [c["name"] for c in inspector.get_columns("orders")]
            if "delivery_type" not in columns:
                db.session.execute(text("ALTER TABLE orders ADD COLUMN delivery_type VARCHAR(20) DEFAULT 'bureau'"))
                db.session.commit()
                print("[migrate] Added orders.delivery_type column")
        except Exception as e:
            db.session.rollback()
            print(f"[migrate] Skipped: {e}")

        try:
            inspector = inspect(db.engine)
            cols = {c["name"]: c for c in inspector.get_columns("order_items")}
            pid = cols.get("product_id")
            if pid and not pid["nullable"]:
                db.session.execute(text("ALTER TABLE order_items ALTER COLUMN product_id DROP NOT NULL"))
                db.session.commit()
                print("[migrate] Made order_items.product_id nullable")
        except Exception as e:
            db.session.rollback()
            print(f"[migrate] Skipped: {e}")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    _auto_migrate(app)

    login_manager.login_view = "admin.login"
    login_manager.login_message_category = "info"

    from app.routes.main import main_bp
    from app.routes.shop import shop_bp
    from app.routes.cart import cart_bp
    from app.routes.checkout import checkout_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    csrf.exempt(admin_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.context_processor
    def inject_globals():
        try:
            from app.models import Category
            categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
        except Exception:
            categories = []
        return dict(categories=categories, meta_pixel_id=app.config["META_PIXEL_ID"])

    return app
