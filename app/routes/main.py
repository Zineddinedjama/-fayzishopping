from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Product, Category, SiteSettings, ContactMessage

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    from app.models import Product
    featured = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
    new_products = Product.query.filter_by(is_new=True, is_active=True).order_by(
        Product.created_at.desc()
    ).limit(8).all()
    promo_products = Product.query.filter(
        Product.compare_price > 0, Product.is_active == True
    ).limit(8).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.order).all()

    banner_title = SiteSettings.get("banner_title", "Accessoires Tech au Meilleur Prix")
    banner_subtitle = SiteSettings.get("banner_subtitle", "Coques, chargeurs, écouteurs et plus encore. Livraison dans toute l'Algérie.")
    promo_banner = SiteSettings.get("promo_banner", "")

    return render_template(
        "index.html",
        featured=featured,
        new_products=new_products,
        promo_products=promo_products,
        categories=categories,
        banner_title=banner_title,
        banner_subtitle=banner_subtitle,
        promo_banner=promo_banner,
    )


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not message:
            flash("Le nom et le message sont requis.", "danger")
            return redirect(url_for("main.contact"))

        msg = ContactMessage(
            name=name, email=email, phone=phone, subject=subject, message=message
        )
        from app.extensions import db
        db.session.add(msg)
        db.session.commit()
        flash("Message envoyé ! On vous répondra très vite.", "success")
        return redirect(url_for("main.contact"))

    whatsapp = SiteSettings.get("whatsapp_number", "")
    return render_template("contact.html", whatsapp_number=whatsapp)
