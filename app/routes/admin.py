import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import (
    Admin, Product, ProductImage, ProductVariant, Category,
    Order, ShippingRate, SiteSettings, ContactMessage,
)
from app.utils.cloudinary_utils import upload_image, delete_image as cloudinary_delete, get_public_id_from_url
from app.utils.helpers import slugify

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__)


def _generate_sku(name):
    import re
    import time
    base = re.sub(r'[^A-Z0-9]', '', name.upper().replace(' ', ''))[:8]
    return f"{base}-{int(time.time()) % 100000}"


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = Admin.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin.dashboard"))
        flash("Identifiants incorrects.", "danger")
    return render_template("admin/login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    from datetime import datetime, timedelta, timezone
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status="pending").count()
    total_products = Product.query.filter_by(is_active=True).count()
    total_revenue = db.session.query(db.func.sum(Order.total)).filter(
        Order.status.in_(["confirmed", "shipped", "delivered"])
    ).scalar() or 0

    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)
    orders_this_week = Order.query.filter(
        Order.created_at >= week_ago.isoformat()
    ).count()
    revenue_this_week = db.session.query(db.func.sum(Order.total)).filter(
        Order.status.in_(["confirmed", "shipped", "delivered"]),
        Order.created_at >= week_ago.isoformat(),
    ).scalar() or 0

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    unread_messages = ContactMessage.query.filter_by(is_read=False).count()

    return render_template(
        "admin/dashboard.html",
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_products=total_products,
        total_revenue=total_revenue,
        orders_this_week=orders_this_week,
        revenue_this_week=revenue_this_week,
        recent_orders=recent_orders,
        unread_messages=unread_messages,
    )


@admin_bp.route("/products")
@admin_required
def products_list():
    page = request.args.get("page", 1, type=int)
    search = request.form.get("q", "") if request.method == "POST" else request.args.get("q", "")
    category_id = request.args.get("category_id", type=int)
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter_by(category_id=category_id)
    pagination = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20)
    categories = Category.query.order_by(Category.name).all()
    return render_template(
        "admin/products.html",
        products=pagination.items, pagination=pagination,
        search=search, categories=categories,
        current_category_id=category_id,
    )


@admin_bp.route("/products/new", methods=["GET", "POST"])
@admin_required
def product_new():
    if request.method == "POST":
        try:
            product = Product(
                name=request.form["name"],
                slug=slugify(request.form["name"]),
                description=request.form.get("description", ""),
                price=int(request.form["price"]),
                compare_price=int(request.form.get("compare_price", 0) or 0),
                stock=int(request.form.get("stock", 0) or 0),
                sku=request.form.get("sku", "").strip() or _generate_sku(request.form["name"]),
                category_id=int(request.form["category_id"]),
                is_active="is_active" in request.form,
                is_featured="is_featured" in request.form,
                is_new="is_new" in request.form,
                compatible_phones=request.form.get("compatible_phones", ""),
            )
            db.session.add(product)
            db.session.flush()

            files = request.files.getlist("images")
            uploaded = 0
            for i, f in enumerate(files):
                if f and f.filename:
                    url, err = upload_image(f)
                    if url:
                        img = ProductImage(
                            product_id=product.id, url=url, alt_text=product.name,
                            is_primary=(i == 0), order=i,
                        )
                        db.session.add(img)
                        uploaded += 1
                    else:
                        logger.error("Image upload failed for %s: %s", f.filename, err)
                        flash(f"Erreur upload '{f.filename}' : {err}", "danger")

            _save_variants(product, request)
            db.session.commit()
            if uploaded:
                flash("Produit créé avec succès.", "success")
            else:
                flash("Produit créé (images non uploadées).", "warning")
            return redirect(url_for("admin.products_list"))
        except Exception as e:
            db.session.rollback()
            logger.exception("Error creating product")
            flash(f"Erreur lors de la création : {str(e)}", "danger")

    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return render_template("admin/product_form.html", product=None, categories=categories)


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    logger.debug("product_edit %s %s", product_id, request.method)
    if request.method == "POST":
        try:
            product.name = request.form["name"]
            product.slug = slugify(request.form["name"])
            product.description = request.form.get("description", "")
            product.price = int(request.form["price"])
            product.compare_price = int(request.form.get("compare_price", 0) or 0)
            product.stock = int(request.form.get("stock", 0) or 0)
            product.sku = request.form.get("sku", "").strip() or product.sku or _generate_sku(request.form["name"])
            product.category_id = int(request.form["category_id"])
            product.is_active = "is_active" in request.form
            product.is_featured = "is_featured" in request.form
            product.is_new = "is_new" in request.form
            product.compatible_phones = request.form.get("compatible_phones", "")

            files = request.files.getlist("images")
            uploaded = 0
            for i, f in enumerate(files):
                if f and f.filename:
                    url, err = upload_image(f)
                    if url:
                        img = ProductImage(
                            product_id=product.id, url=url, alt_text=product.name,
                            is_primary=(i == 0 and product.images.count() == 0),
                            order=product.images.count() + i,
                        )
                        db.session.add(img)
                        uploaded += 1
                    else:
                        logger.error("Image upload failed for %s: %s", f.filename, err)
                        flash(f"Erreur upload '{f.filename}' : {err}", "danger")

            _save_variants(product, request)
            db.session.commit()
            if uploaded:
                flash("Produit mis à jour.", "success")
            else:
                flash("Produit mis à jour (images non uploadées).", "warning")
            return redirect(url_for("admin.products_list"))
        except Exception as e:
            db.session.rollback()
            logger.exception("Error updating product")
            flash(f"Erreur lors de la mise à jour : {str(e)}", "danger")

    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return render_template("admin/product_form.html", product=product, categories=categories)


def _save_variants(product, req):
    variant_ids = req.form.getlist("variant_id[]")
    phones = req.form.getlist("variant_phone[]")
    colors = req.form.getlist("variant_color[]")
    stocks = req.form.getlist("variant_stock[]")
    prices = req.form.getlist("variant_price[]")
    skus = req.form.getlist("variant_sku[]")
    deletes = req.form.getlist("variant_delete[]")

    for vid in deletes:
        v = ProductVariant.query.get(int(vid))
        if v and v.product_id == product.id:
            db.session.delete(v)

    existing_ids = set()
    for i in range(len(phones)):
        if i < len(variant_ids) and variant_ids[i]:
            vid = int(variant_ids[i])
            v = ProductVariant.query.get(vid)
            if v and v.product_id == product.id:
                v.phone_model = phones[i].strip()
                v.color = colors[i].strip() if i < len(colors) else ""
                v.stock = int(stocks[i] or 0) if i < len(stocks) else 0
                v.price = int(prices[i]) if i < len(prices) and prices[i].strip() else None
                v.sku = skus[i].strip() if i < len(skus) else ""
                existing_ids.add(vid)
        else:
            if phones[i].strip() or (i < len(colors) and colors[i].strip()):
                v = ProductVariant(
                    product_id=product.id,
                    phone_model=phones[i].strip(),
                    color=colors[i].strip() if i < len(colors) else "",
                    stock=int(stocks[i] or 0) if i < len(stocks) else 0,
                    price=int(prices[i]) if i < len(prices) and prices[i].strip() else None,
                    sku=skus[i].strip() if i < len(skus) else "",
                )
                db.session.add(v)


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)

    for img in product.images.all():
        if img.url:
            public_id = get_public_id_from_url(img.url)
            if public_id:
                try:
                    cloudinary_delete(public_id)
                except Exception:
                    pass

    from app.models import CartItem, WishlistItem, OrderItem
    CartItem.query.filter_by(product_id=product.id).delete()
    WishlistItem.query.filter_by(product_id=product.id).delete()
    OrderItem.query.filter_by(product_id=product.id).update({"product_id": None, "variant_id": None})

    db.session.delete(product)
    db.session.commit()
    flash("Produit supprimé définitivement.", "success")
    return redirect(url_for("admin.products_list"))


@admin_bp.route("/products/<int:product_id>/images/<int:image_id>/delete", methods=["POST"])
@admin_required
def delete_image(product_id, image_id):
    logger.debug("delete_image product=%s image=%s", product_id, image_id)
    img = ProductImage.query.filter_by(id=image_id, product_id=product_id).first_or_404()
    if img.url:
        public_id = get_public_id_from_url(img.url)
        if public_id:
            try:
                cloudinary_delete(public_id)
                logger.debug("Cloudinary delete OK: %s", public_id)
            except Exception:
                logger.exception("Cloudinary delete failed for %s", public_id)
    db.session.delete(img)
    db.session.commit()
    logger.debug("Image %s deleted from DB", image_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True})
    flash("Image supprimée.", "success")
    return redirect(url_for("admin.product_edit", product_id=product_id))


@admin_bp.route("/orders")
@admin_required
def orders_list():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "")
    search = request.args.get("q", "")
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            (Order.order_number.ilike(f"%{search}%")) |
            (Order.full_name.ilike(f"%{search}%")) |
            (Order.phone.ilike(f"%{search}%"))
        )
    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20)
    return render_template("admin/orders.html", orders=pagination.items, pagination=pagination, current_status=status, search=search)


@admin_bp.route("/orders/<int:order_id>", methods=["GET", "POST"])
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if request.method == "POST":
        new_status = request.form.get("status")
        if new_status in Order.STATUSES:
            order.status = new_status
            db.session.commit()
            flash(f"Statut mis à jour : {order.status_label()}", "success")
        return redirect(url_for("admin.order_detail", order_id=order.id))
    return render_template("admin/order_detail.html", order=order)


@admin_bp.route("/shipping", methods=["GET", "POST"])
@admin_required
def shipping_list():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "import_excel":
            file = request.files.get("shipping_file")
            if file:
                count = _import_shipping_excel(file)
                flash(f"{count} tarifs importés avec succès.", "success")
            else:
                flash("Aucun fichier sélectionné.", "danger")
        elif action == "update_one":
            wilaya_code = request.form.get("wilaya_code")
            price = int(request.form.get("price", 600))
            home_price = request.form.get("home_delivery_price")
            home_price = int(home_price) if home_price else None
            rate = ShippingRate.query.filter_by(wilaya_code=wilaya_code).first()
            if rate:
                rate.price = price
                if home_price is not None:
                    rate.home_delivery_price = home_price
            else:
                wilaya_name = request.form.get("wilaya_name", "")
                rate = ShippingRate(wilaya_code=wilaya_code, wilaya_name=wilaya_name, price=price, home_delivery_price=home_price)
                db.session.add(rate)
            db.session.commit()
            flash("Tarif mis à jour.", "success")
        elif action == "update_all":
            default_price = int(request.form.get("default_price", 600))
            default_home = int(request.form.get("default_home_price", default_price + 150))
            ShippingRate.query.update({ShippingRate.price: default_price, ShippingRate.home_delivery_price: default_home})
            db.session.commit()
            flash(f"Tous les tarifs mis à {default_price} DA.", "success")
        return redirect(url_for("admin.shipping_list"))

    rates = ShippingRate.query.order_by(ShippingRate.wilaya_code).all()
    return render_template("admin/shipping.html", rates=rates)


def _import_shipping_excel(file):
    import csv
    import io

    count = 0
    try:
        content = file.read().decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        header = next(reader, None)
        for row in reader:
            if len(row) < 3:
                continue
            code, name, price = row[0].strip(), row[1].strip(), int(row[2].strip())
            home_price = int(row[3].strip()) if len(row) > 3 and row[3].strip() else None
            existing = ShippingRate.query.filter_by(wilaya_code=code).first()
            if existing:
                existing.price = price
                existing.wilaya_name = name
                if home_price is not None:
                    existing.home_delivery_price = home_price
            else:
                db.session.add(ShippingRate(wilaya_code=code, wilaya_name=name, price=price, home_delivery_price=home_price))
            count += 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        count = 0
    return count


@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_required
def categories_list():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            cat = Category(name=name, slug=slugify(name), description=request.form.get("description", ""))
            db.session.add(cat)
            db.session.commit()
            flash("Catégorie créée.", "success")
        return redirect(url_for("admin.categories_list"))
    cats = Category.query.order_by(Category.order).all()
    return render_template("admin/categories.html", categories=cats)


@admin_bp.route("/categories/<int:cat_id>/toggle", methods=["POST"])
@admin_required
def category_toggle(cat_id):
    cat = Category.query.get_or_404(cat_id)
    cat.is_active = not cat.is_active
    db.session.commit()
    flash("Catégorie mise à jour.", "success")
    return redirect(url_for("admin.categories_list"))


@admin_bp.route("/messages")
@admin_required
def messages_list():
    page = request.args.get("page", 1, type=int)
    pagination = ContactMessage.query.order_by(ContactMessage.created_at.desc()).paginate(page=page, per_page=20)
    return render_template("admin/messages.html", messages=pagination.items, pagination=pagination)


@admin_bp.route("/messages/<int:msg_id>/read", methods=["POST"])
@admin_required
def message_read(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    flash("Message marqué comme lu.", "success")
    return redirect(url_for("admin.messages_list"))
