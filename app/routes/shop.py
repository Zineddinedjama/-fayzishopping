from flask import Blueprint, render_template, request, abort, current_app
from app.models import Product, Category
from app.utils.helpers import slugify

shop_bp = Blueprint("shop", __name__)


@shop_bp.route("/shop")
@shop_bp.route("/boutique")
def catalog():
    page = request.args.get("page", 1, type=int)
    category_slug = request.args.get("category", "")
    phone_model = request.args.get("phone", "")
    search = request.args.get("q", "").strip()
    sort = request.args.get("sort", "newest")
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)

    query = Product.query.filter_by(is_active=True)

    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(category_id=category.id)
    else:
        category = None

    if phone_model:
        query = query.filter(
            Product.compatible_phones.ilike(f"%{phone_model}%")
        )

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Product.name.ilike(search_term) |
            Product.description.ilike(search_term) |
            Product.sku.ilike(search_term)
        )

    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "name":
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    per_page = current_app.config["ITEMS_PER_PAGE"]
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    all_categories = Category.query.filter_by(is_active=True).order_by(Category.order).all()

    return render_template(
        "shop.html",
        products=pagination.items,
        pagination=pagination,
        categories=all_categories,
        current_category=category,
        current_search=search,
        current_sort=sort,
        current_phone=phone_model,
        min_price=min_price,
        max_price=max_price,
    )


@shop_bp.route("/product/<slug>")
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()

    related = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True,
    ).limit(4).all()

    all_images = product.all_images()
    phone_models = product.phone_models_list()

    return render_template(
        "product.html",
        product=product,
        related=related,
        all_images=all_images,
        phone_models=phone_models,
    )
