/* ========================================
   Fayzishopping — Main JS
   ======================================== */

document.addEventListener('DOMContentLoaded', function() {
    updateCartCount();
    autoDismissAlerts();
});

/* ---- Auto-dismiss flash alerts ---- */
function autoDismissAlerts() {
    document.querySelectorAll('.alert').forEach(function(alert) {
        alert.addEventListener('click', function() { this.style.display = 'none'; });
        setTimeout(function() {
            alert.style.transition = 'opacity 0.3s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

/* ---- Mobile Menu ---- */
function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    menu.classList.toggle('active');
    document.body.style.overflow = menu.classList.contains('active') ? 'hidden' : '';
}

/* ---- Cart Count (AJAX) ---- */
function updateCartCount() {
    fetch('/api/cart/count')
        .then(r => r.json())
        .then(data => {
            const el = document.getElementById('cart-count');
            if (el) {
                el.textContent = data.count || 0;
                el.style.display = data.count > 0 ? 'flex' : 'none';
            }
        })
        .catch(() => {});
}

/* ---- Add to Cart (Generic) ---- */
function addToCart(productId, variantId = null, quantity = 1) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content ||
                      document.querySelector('input[name="csrf_token"]')?.value || '';

    fetch('/api/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({
            product_id: productId,
            variant_id: variantId,
            quantity: quantity,
        }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast(data.message || 'Ajouté au panier !');
            updateCartCount();
        } else {
            showToast(data.error || 'Erreur', 'error');
        }
    })
    .catch(() => showToast("Erreur de connexion", 'error'));
}

/* ---- Update Cart Item ---- */
function updateCartItem(itemId, quantity) {
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';

    fetch('/api/cart/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ item_id: itemId, quantity: quantity }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) location.reload();
    });
}

/* ---- Remove Cart Item ---- */
function removeCartItem(itemId) {
    const csrfToken = document.querySelector('input[name="csrf_token"]')?.value || '';

    fetch('/api/cart/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ item_id: itemId }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) location.reload();
    });
}

/* ---- Product Page: Image Gallery ---- */
function changeImage(url, thumbBtn) {
    const mainImg = document.getElementById('main-product-image');
    if (mainImg) mainImg.src = url;
    document.querySelectorAll('.gallery-thumb').forEach(t => t.classList.remove('active'));
    if (thumbBtn) thumbBtn.classList.add('active');
}

/* ---- Product Page: Quantity ---- */
function changeQty(delta) {
    const input = document.getElementById('product-quantity');
    if (!input) return;
    let val = parseInt(input.value) + delta;
    if (val < 1) val = 1;
    if (val > 99) val = 99;
    input.value = val;
}

/* ---- Product Page: Variant Selection ---- */
function updateVariantOptions() {
    if (typeof VARIANTS === 'undefined') return;

    const phoneSelect = document.getElementById('phone-model-select');
    const colorSelect = document.getElementById('color-select');
    const hiddenId = document.getElementById('selected-variant-id');
    const hiddenStock = document.getElementById('selected-variant-stock');
    const addBtn = document.getElementById('add-to-cart-btn');

    const phone = phoneSelect ? phoneSelect.value : '';
    const color = colorSelect ? colorSelect.value : '';

    let match = VARIANTS.find(v => {
        let ok = true;
        if (phone) ok = ok && v.phone_model === phone;
        if (color) ok = ok && v.color === color;
        return ok;
    });

    if (match) {
        hiddenId.value = match.id;
        hiddenStock.value = match.stock;
        if (addBtn) addBtn.disabled = match.stock <= 0;

        const priceEl = document.querySelector('.product-price');
        if (priceEl && match.price) {
            priceEl.textContent = match.price.toLocaleString('fr-FR') + ' DA';
        }
    } else {
        hiddenId.value = '';
        hiddenStock.value = '';
    }
}

/* ---- Product Page: Add to Cart with variant ---- */
function addProductToCart() {
    const btn = document.getElementById('add-to-cart-btn');
    if (!btn) return;

    const productId = parseInt(btn.getAttribute('onclick')?.match(/\d+/)?.[0] || document.querySelector('[data-product-id]')?.dataset?.productId);
    const variantId = document.getElementById('selected-variant-id')?.value || null;
    const quantity = parseInt(document.getElementById('product-quantity')?.value || 1);

    addToCart(productId, variantId ? parseInt(variantId) : null, quantity);
}

/* ---- Toast Notifications ---- */
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;display:flex;flex-direction:column;gap:0.5rem;';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bg = type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#22c55e';
    toast.style.cssText = `background:${bg};color:#fff;padding:0.7rem 1.2rem;border-radius:8px;font-size:0.88rem;font-weight:500;box-shadow:0 4px 16px rgba(0,0,0,0.15);animation:slideUp 0.3s ease;max-width:320px;font-family:Inter,sans-serif;`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = '0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/* ---- Live Search ---- */
const searchInput = document.querySelector('.search-input');
if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const q = this.value.trim();
        if (q.length < 2) return;
        debounceTimer = setTimeout(() => {
            fetch(`/api/products/search?q=${encodeURIComponent(q)}`)
                .then(r => r.json())
                .then(results => {
                    let dropdown = document.getElementById('search-dropdown');
                    if (!dropdown) {
                        dropdown = document.createElement('div');
                        dropdown.id = 'search-dropdown';
                        dropdown.style.cssText = 'position:absolute;top:100%;left:0;right:0;background:#fff;border-radius:0 0 8px 8px;box-shadow:0 8px 24px rgba(0,0,0,0.15);z-index:100;max-height:300px;overflow-y:auto;';
                        searchInput.parentElement.appendChild(dropdown);
                    }
                    if (results.length === 0) {
                        dropdown.style.display = 'none';
                        return;
                    }
                    dropdown.innerHTML = results.map(p => `
                        <a href="${p.url}" style="display:flex;align-items:center;gap:0.8rem;padding:0.6rem 1rem;text-decoration:none;color:#1e293b;border-bottom:1px solid #f1f5f9;">
                            <img src="${p.image || 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2240%22 height=%2240%22%3E%3Crect width=%22100%25%22 height=%22100%25%22 fill=%22%23e2e8f0%22/%3E%3C/svg%3E'}" style="width:40px;height:40px;border-radius:6px;object-fit:cover;">
                            <div><div style="font-size:0.88rem;font-weight:600;">${p.name}</div><div style="font-size:0.8rem;color:#64748b;">${p.price.toLocaleString('fr-FR')} DA</div></div>
                        </a>
                    `).join('');
                    dropdown.style.display = 'block';
                });
        }, 300);
    });

    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-bar') && !e.target.closest('.mobile-search')) {
            const dd = document.getElementById('search-dropdown');
            if (dd) dd.style.display = 'none';
        }
    });
}

/* ---- Close mobile menu on ESC ---- */
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        const menu = document.getElementById('mobile-menu');
        if (menu && menu.classList.contains('active')) {
            toggleMobileMenu();
        }
        const dd = document.getElementById('search-dropdown');
        if (dd) dd.style.display = 'none';
    }
});

/* ---- Wishlist ---- */
function toggleWishlist(productId, btn) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

    fetch('/api/wishlist/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ product_id: productId }),
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            const icon = btn.querySelector('.heart-icon');
            if (data.wishlisted) {
                icon.innerHTML = '&#9829;';
                icon.style.color = '#ef4444';
                showToast('Ajouté aux favoris');
            } else {
                icon.innerHTML = '&#9825;';
                icon.style.color = '';
                showToast('Retiré des favoris', 'warning');
            }
        }
    });
}
