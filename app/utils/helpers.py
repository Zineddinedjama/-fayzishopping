import uuid
import string
import random


def generate_session_id():
    return str(uuid.uuid4())


def generate_order_number():
    prefix = "FZ"
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=6))
    return f"{prefix}-{suffix}"


def format_price(amount):
    return f"{amount:,.0f} DA"


def slugify(text):
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text
