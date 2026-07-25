from flask import Blueprint, request, session, jsonify, redirect, url_for, render_template
from app.extensions import db
from app.models import Cart, CartItem, Product, ProductVariant
from app.utils.helpers import generate_session_id
from app.utils.shipping import ALGERIAN_WILAYAS

cart_bp = Blueprint("cart", __name__)


def get_or_create_cart():
    cart_id = session.get("cart_id")
    if cart_id:
        cart = Cart.query.get(cart_id)
        if cart:
            return cart
    cart = Cart(session_id=generate_session_id())
    db.session.add(cart)
    db.session.commit()
    session["cart_id"] = cart.id
    return cart


@cart_bp.route("/cart")
def view_cart():
    cart = get_or_create_cart()
    wilayas = [(w[0], w[1]) for w in ALGERIAN_WILAYAS]
    return render_template(
        "cart.html",
        cart=cart,
        wilayas=wilayas,
        saved_name=session.get("checkout_name", ""),
        saved_phone=session.get("checkout_phone", ""),
        saved_wilaya=session.get("checkout_wilaya", ""),
        saved_commune=session.get("checkout_commune", ""),
        saved_delivery_type=session.get("checkout_delivery_type", "bureau"),
    )


@cart_bp.route("/api/cart/save-delivery", methods=["POST"])
def save_delivery():
    data = request.get_json()
    if data:
        if data.get("full_name"):
            session["checkout_name"] = data["full_name"]
        if data.get("phone"):
            session["checkout_phone"] = data["phone"]
        if data.get("wilaya"):
            session["checkout_wilaya"] = data["wilaya"]
        if data.get("commune"):
            session["checkout_commune"] = data["commune"]
        if data.get("delivery_type"):
            session["checkout_delivery_type"] = data["delivery_type"]
    return jsonify({"success": True})


@cart_bp.route("/api/cart/add", methods=["POST"])
def add_to_cart():
    data = request.get_json()
    product_id = data.get("product_id")
    variant_id = data.get("variant_id")
    quantity = data.get("quantity", 1)

    product = Product.query.get(product_id)
    if not product or not product.is_active:
        return jsonify({"error": "Produit introuvable"}), 404

    variant = None
    if variant_id:
        variant = ProductVariant.query.get(variant_id)
        if not variant or variant.product_id != product.id:
            return jsonify({"error": "Variante introuvable"}), 404
        if variant.stock < quantity:
            return jsonify({"error": "Stock insuffisant"}), 400
    else:
        if product.stock < quantity:
            return jsonify({"error": "Stock insuffisant"}), 400

    cart = get_or_create_cart()

    existing_item = CartItem.query.filter_by(
        cart_id=cart.id, product_id=product.id
    )
    if variant_id:
        existing_item = existing_item.filter_by(variant_id=variant_id)
    existing_item = existing_item.first()

    if existing_item:
        existing_item.quantity += quantity
    else:
        item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            variant_id=variant_id,
            quantity=quantity,
        )
        db.session.add(item)

    db.session.commit()

    return jsonify({
        "success": True,
        "total_items": cart.total_items(),
        "total": cart.total(),
        "message": "Produit ajouté au panier",
    })


@cart_bp.route("/api/cart/update", methods=["POST"])
def update_cart_item():
    data = request.get_json()
    item_id = data.get("item_id")
    quantity = data.get("quantity", 1)

    cart = get_or_create_cart()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if not item:
        return jsonify({"error": "Article introuvable"}), 404

    if quantity <= 0:
        db.session.delete(item)
    else:
        item.quantity = quantity

    db.session.commit()

    return jsonify({
        "success": True,
        "total_items": cart.total_items(),
        "total": cart.total(),
        "item_subtotal": item.subtotal() if quantity > 0 else 0,
    })


@cart_bp.route("/api/cart/remove", methods=["POST"])
def remove_cart_item():
    data = request.get_json()
    item_id = data.get("item_id")

    cart = get_or_create_cart()
    item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
    if item:
        db.session.delete(item)
        db.session.commit()

    return jsonify({
        "success": True,
        "total_items": cart.total_items(),
        "total": cart.total(),
    })


@cart_bp.route("/api/cart/count")
def cart_count():
    cart = get_or_create_cart()
    return jsonify({"count": cart.total_items()})
