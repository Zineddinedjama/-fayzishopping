from flask import Blueprint, request, jsonify, session
from app.extensions import db
from app.models import Product, Category, WishlistItem, ProductVisit
import hashlib
import re

api_bp = Blueprint("api", __name__)


def _get_session_id():
    if "sid" not in session:
        import uuid
        session["sid"] = str(uuid.uuid4())
    return session["sid"]


@api_bp.route("/products/search")
def search_products():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    products = Product.query.filter(
        Product.is_active == True,
        Product.name.ilike(f"%{q}%")
    ).limit(6).all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "slug": p.slug,
        "price": p.price,
        "image": p.primary_image(),
        "url": f"/product/{p.slug}",
    } for p in products])


@api_bp.route("/categories")
def get_categories():
    cats = Category.query.filter_by(is_active=True).order_by(Category.order).all()
    return jsonify([{
        "id": c.id,
        "name": c.name,
        "slug": c.slug,
        "count": c.product_count(),
    } for c in cats])


@api_bp.route("/wishlist/toggle", methods=["POST"])
def wishlist_toggle():
    data = request.get_json()
    product_id = data.get("product_id")
    sid = _get_session_id()

    existing = WishlistItem.query.filter_by(
        session_id=sid, product_id=product_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"success": True, "wishlisted": False})
    else:
        item = WishlistItem(session_id=sid, product_id=product_id)
        db.session.add(item)
        db.session.commit()
        return jsonify({"success": True, "wishlisted": True})


@api_bp.route("/wishlist/check/<int:product_id>")
def wishlist_check(product_id):
    sid = _get_session_id()
    exists = WishlistItem.query.filter_by(
        session_id=sid, product_id=product_id
    ).first() is not None
    return jsonify({"wishlisted": exists})


@api_bp.route("/wishlist/count")
def wishlist_count():
    sid = _get_session_id()
    count = WishlistItem.query.filter_by(session_id=sid).count()
    return jsonify({"count": count})


BOT_PATTERNS = re.compile(
    r"bot|crawl|spider|slurp|baiduspider|googlebot|bingbot|yandexbot|"
    r"sogou|exabot|facebot|facebookexternalhit|ia_archiver|semrush|ahrefs",
    re.IGNORECASE,
)


@api_bp.route("/product/<int:product_id>/visit", methods=["POST"])
def record_visit(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"ok": False}), 404

    user_agent = request.headers.get("User-Agent", "")
    if BOT_PATTERNS.search(user_agent):
        return jsonify({"ok": True, "skipped": "bot"})

    ip = request.remote_addr or ""
    raw = f"{product_id}-{ip}-{user_agent[:80]}"
    visitor_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

    existing = ProductVisit.query.filter_by(
        product_id=product_id, visitor_id=visitor_id
    ).first()
    if existing:
        return jsonify({"ok": True, "skipped": "duplicate"})

    visit = ProductVisit(
        product_id=product_id,
        visitor_id=visitor_id,
        ip_address=ip,
        user_agent=user_agent[:500],
        gender="unknown",
    )
    db.session.add(visit)
    db.session.commit()
    return jsonify({"ok": True})
