from datetime import datetime, timezone
from app.extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    image_url = db.Column(db.String(500), default="")
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    products = db.relationship("Product", backref="category", lazy="dynamic")

    def product_count(self):
        return self.products.filter_by(is_active=True).count()


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Integer, nullable=False)
    compare_price = db.Column(db.Integer, default=0)
    stock = db.Column(db.Integer, default=0)
    sku = db.Column(db.String(50), unique=True, default="")
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_new = db.Column(db.Boolean, default=True)
    compatible_phones = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    images = db.relationship("ProductImage", backref="product", lazy="dynamic",
                             order_by="ProductImage.order", cascade="all, delete-orphan")
    variants = db.relationship("ProductVariant", backref="product", lazy="dynamic",
                               cascade="all, delete-orphan")

    def primary_image(self):
        img = self.images.filter_by(is_primary=True).first()
        if img:
            return img.url
        first = self.images.first()
        return first.url if first else ""

    def all_images(self):
        return self.images.order_by(ProductImage.order).all()

    def has_variants(self):
        return self.variants.count() > 0

    def min_price(self):
        if self.variants.count() > 0:
            prices = [v.price if v.price else self.price for v in self.variants.all()]
            return min(prices)
        return self.price

    def get_variant(self, phone_model=None, color=None):
        q = self.variants
        if phone_model:
            q = q.filter_by(phone_model=phone_model)
        if color:
            q = q.filter_by(color=color)
        return q.first()

    def in_stock(self):
        if self.has_variants():
            return any(v.stock > 0 for v in self.variants.all())
        return self.stock > 0

    def phone_models_list(self):
        models = db.session.query(ProductVariant.phone_model).filter(
            ProductVariant.product_id == self.id,
            ProductVariant.phone_model.isnot(None),
            ProductVariant.phone_model != ""
        ).distinct().all()
        return [m[0] for m in models if m[0]]


class ProductImage(db.Model):
    __tablename__ = "product_images"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    alt_text = db.Column(db.String(200), default="")
    is_primary = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)


class ProductVariant(db.Model):
    __tablename__ = "product_variants"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    phone_model = db.Column(db.String(100), default="")
    color = db.Column(db.String(50), default="")
    stock = db.Column(db.Integer, default=0)
    price = db.Column(db.Integer, nullable=True)
    sku = db.Column(db.String(50), default="")

    def display_name(self):
        parts = [p for p in [self.phone_model, self.color] if p]
        return " - ".join(parts) if parts else "Standard"


class Cart(db.Model):
    __tablename__ = "carts"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    items = db.relationship("CartItem", backref="cart", lazy="dynamic",
                            cascade="all, delete-orphan")

    def total(self):
        return sum(item.subtotal() for item in self.items.all())

    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(db.Model):
    __tablename__ = "cart_items"
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey("product_variants.id"), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship("Product")
    variant = db.relationship("ProductVariant")

    def subtotal(self):
        if self.variant and self.variant.price:
            return self.variant.price * self.quantity
        return self.product.price * self.quantity

    def unit_price(self):
        if self.variant and self.variant.price:
            return self.variant.price
        return self.product.price


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    phone_secondary = db.Column(db.String(20), default="")
    wilaya = db.Column(db.String(100), nullable=False)
    commune = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, default="")
    subtotal = db.Column(db.Integer, default=0)
    shipping_cost = db.Column(db.Integer, default=0)
    total = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="pending")
    payment_method = db.Column(db.String(20), default="cod")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    items = db.relationship("OrderItem", backref="order", lazy="dynamic",
                            cascade="all, delete-orphan")

    STATUSES = {
        "pending": "En attente",
        "confirmed": "Confirmée",
        "shipped": "Expédiée",
        "delivered": "Livrée",
        "cancelled": "Annulée",
    }

    def status_label(self):
        return self.STATUSES.get(self.status, self.status)

    def item_count(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey("product_variants.id"), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)
    variant_name = db.Column(db.String(150), default="")
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Integer, nullable=False)
    product = db.relationship("Product")
    variant = db.relationship("ProductVariant")

    def subtotal(self):
        return self.unit_price * self.quantity


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(200), default="")
    phone = db.Column(db.String(20), default="")
    subject = db.Column(db.String(200), default="")
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class WishlistItem(db.Model):
    __tablename__ = "wishlist_items"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    product = db.relationship("Product")
    __table_args__ = (db.UniqueConstraint("session_id", "product_id"),)


class ShippingRate(db.Model):
    __tablename__ = "shipping_rates"
    id = db.Column(db.Integer, primary_key=True)
    wilaya_code = db.Column(db.String(5), unique=True, nullable=False)
    wilaya_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    home_delivery_price = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)


class SiteSettings(db.Model):
    __tablename__ = "site_settings"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, default="")
    description = db.Column(db.String(200), default="")

    @staticmethod
    def get(key, default=""):
        setting = SiteSettings.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value, description=""):
        setting = SiteSettings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = SiteSettings(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()
