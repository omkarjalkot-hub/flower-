"""Cart logic (no Streamlit dependency). The cart lives in the database per user."""
from db import execute, get_conn, get_setting, query, query_one

_IMG = ("(SELECT image_path FROM product_images WHERE product_id = p.id "
        "ORDER BY is_primary DESC, id LIMIT 1)")


def get_cart(user_id):
    return query(
        f"""SELECT ci.id AS cart_item_id, ci.quantity, p.id AS product_id, p.name, p.price,
                   p.stock, p.is_active, {_IMG} AS image_path
            FROM cart_items ci JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = ? ORDER BY ci.id""", (user_id,))


def cart_quantity(user_id, product_id):
    row = query_one("SELECT quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
                    (user_id, product_id))
    return row["quantity"] if row else 0


def cart_count(user_id):
    row = query_one("SELECT COALESCE(SUM(quantity), 0) AS n FROM cart_items WHERE user_id = ?", (user_id,))
    return row["n"]


def add_to_cart(user_id, product_id, qty):
    """Add qty to the cart without exceeding stock. Returns (ok, message)."""
    product = query_one("SELECT name, stock, is_active FROM products WHERE id = ?", (product_id,))
    if not product or not product["is_active"]:
        return False, "This flower is no longer available."
    if product["stock"] <= 0:
        return False, "Out of stock."
    if qty < 1:
        return False, "Choose at least 1."
    have = cart_quantity(user_id, product_id)
    if have + qty > product["stock"]:
        left = product["stock"] - have
        if left <= 0:
            return False, f"All {product['stock']} available are already in your cart."
        return False, f"Only {product['stock']} available and {have} already in your cart. You can add {left} more."
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = quantity + excluded.quantity",
            (user_id, product_id, qty))
    return True, f"Added {qty} × {product['name']} to your cart."


def set_quantity(user_id, product_id, qty):
    """Set an exact quantity, capped at stock. qty <= 0 removes the item."""
    if qty <= 0:
        remove_item(user_id, product_id)
        return
    product = query_one("SELECT stock FROM products WHERE id = ?", (product_id,))
    if not product:
        remove_item(user_id, product_id)
        return
    qty = min(qty, max(product["stock"], 1))
    execute("UPDATE cart_items SET quantity = ? WHERE user_id = ? AND product_id = ?",
            (qty, user_id, product_id))


def remove_item(user_id, product_id):
    execute("DELETE FROM cart_items WHERE user_id = ? AND product_id = ?", (user_id, product_id))


def has_unavailable(items):
    """True if any item is out of stock or no longer sold."""
    return any((not it["is_active"]) or it["stock"] <= 0 for it in items)


def cart_problems(items):
    """Messages for items whose quantity is above the remaining stock.
    (Out-of-stock items are not listed here; the cart just labels them 'Out of stock'.)"""
    return [f"Only {it['stock']} of {it['name']} left. Lower the quantity to continue."
            for it in items if it["is_active"] and 0 < it["stock"] < it["quantity"]]


def totals(items):
    subtotal = sum(it["price"] * it["quantity"] for it in items)
    try:
        fee = float(get_setting("delivery_fee", "0") or 0)
    except ValueError:
        fee = 0.0
    fee = fee if items else 0.0
    return {"subtotal": subtotal, "delivery_fee": fee, "total": subtotal + fee}
