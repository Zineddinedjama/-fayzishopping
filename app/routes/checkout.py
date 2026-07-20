from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.extensions import db
from app.models import Cart, CartItem, Order, OrderItem, Product, ProductVariant, ShippingRate
from app.utils.helpers import generate_order_number
from app.utils.shipping import ALGERIAN_WILAYAS, get_shipping_cost

checkout_bp = Blueprint("checkout", __name__)


@checkout_bp.route("/checkout")
def checkout():
    cart_id = session.get("cart_id")
    cart = Cart.query.get(cart_id) if cart_id else None
    if not cart or cart.items.count() == 0:
        return redirect(url_for("cart.view_cart"))

    wilayas = [(w[1], w[1], get_shipping_cost(w[1])) for w in ALGERIAN_WILAYAS]
    subtotal = cart.total()

    saved_name = session.get("checkout_name", "")
    saved_phone = session.get("checkout_phone", "")
    saved_wilaya = session.get("checkout_wilaya", "")

    return render_template(
        "checkout.html",
        cart=cart,
        wilayas=wilayas,
        subtotal=subtotal,
        saved_name=saved_name,
        saved_phone=saved_phone,
        saved_wilaya=saved_wilaya,
    )


@checkout_bp.route("/order/confirm", methods=["POST"])
def confirm_order():
    cart_id = session.get("cart_id")
    cart = Cart.query.get(cart_id) if cart_id else None
    if not cart or cart.items.count() == 0:
        flash("Votre panier est vide.", "warning")
        return redirect(url_for("cart.view_cart"))

    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    phone_secondary = request.form.get("phone_secondary", "").strip()
    wilaya = request.form.get("wilaya", "").strip()
    commune = request.form.get("commune", "").strip()
    address = request.form.get("address", "").strip()
    notes = request.form.get("notes", "").strip()

    errors = []
    if not full_name:
        errors.append("Le nom complet est requis.")
    if not phone or len(phone) < 8:
        errors.append("Numéro de téléphone invalide.")
    if not wilaya:
        errors.append("La wilaya est requise.")
    if not commune:
        errors.append("La commune est requise.")
    if not address:
        errors.append("L'adresse est requise.")

    if errors:
        for e in errors:
            flash(e, "danger")
        return redirect(url_for("checkout.checkout"))

    session["checkout_name"] = full_name
    session["checkout_phone"] = phone
    session["checkout_wilaya"] = wilaya

    shipping_cost = get_shipping_cost(wilaya)
    subtotal = cart.total()
    total = subtotal + shipping_cost

    order = Order(
        order_number=generate_order_number(),
        full_name=full_name,
        phone=phone,
        phone_secondary=phone_secondary,
        wilaya=wilaya,
        commune=commune,
        address=address,
        notes=notes,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
        status="pending",
        payment_method="cod",
    )
    db.session.add(order)
    db.session.flush()

    for cart_item in cart.items.all():
        product = cart_item.product
        variant = cart_item.variant
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            variant_id=variant.id if variant else None,
            product_name=product.name,
            variant_name=variant.display_name() if variant else "",
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price(),
        )
        db.session.add(order_item)

        if variant:
            variant.stock = max(0, variant.stock - cart_item.quantity)
        else:
            product.stock = max(0, product.stock - cart_item.quantity)

    for cart_item in cart.items.all():
        db.session.delete(cart_item)
    db.session.delete(cart)
    session.pop("cart_id", None)

    db.session.commit()

    return redirect(url_for("checkout.order_confirmation", order_number=order.order_number))


@checkout_bp.route("/order/<order_number>")
def order_confirmation(order_number):
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template("order_confirmation.html", order=order)


@checkout_bp.route("/suivi")
def track_order():
    phone = request.args.get("phone", "").strip()
    orders = []
    if phone and len(phone) >= 8:
        orders = Order.query.filter(
            Order.phone.contains(phone)
        ).order_by(Order.created_at.desc()).limit(10).all()
    return render_template("track_order.html", orders=orders, search_phone=phone)


@checkout_bp.route("/api/shipping/cost")
def shipping_cost():
    wilaya = request.args.get("wilaya", "")
    if not wilaya:
        return jsonify({"cost": 0})
    cost = get_shipping_cost(wilaya)
    return jsonify({"cost": cost})
