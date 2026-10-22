"""Admin-side data operations (no Streamlit dependency)."""
import secrets
import sqlite3
from pathlib import Path

from db import execute, get_conn, query, query_one
from orders import ORDER_STAGES
from utils.images import save_upload

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = "assets/products/uploads"
# An order counts as sales once its payment is approved and it has not been cancelled.
PAID = "o.payment_status = 'Approved' AND o.order_status NOT IN ('Cancelled', 'Payment rejected')"


def _remove_file(rel_path):
    """Delete an uploaded file, but never the shipped placeholders or anything outside uploads."""
    if rel_path and (rel_path.startswith(UPLOAD_DIR) or rel_path.startswith("assets/qr/payment-qr-")):
        try:
            (BASE_DIR / rel_path).unlink()
        except OSError:
            pass


# ---------------------------------------------------------------- stats
def stats():
    sales = query_one(f"SELECT COALESCE(SUM(o.total), 0) AS revenue, COUNT(*) AS n FROM orders o WHERE {PAID}")
    return {
        "revenue": sales["revenue"],
        "paid_orders": sales["n"],
        "orders": query_one("SELECT COUNT(*) AS n FROM orders")["n"],
        "pending_payments": len(pending_payments()),
        "refunds_due": len(refunds_due()),
        "customers": query_one("SELECT COUNT(*) AS n FROM users WHERE role = 'customer'")["n"],
        "products": query_one("SELECT COUNT(*) AS n FROM products")["n"],
    }


def daily_revenue(days=14):
    return query(
        f"""SELECT date(o.created_at, '+330 minutes') AS day, SUM(o.total) AS revenue
            FROM orders o WHERE {PAID} AND o.created_at >= datetime('now', ?)
            GROUP BY day ORDER BY day""", (f"-{int(days)} days",))


def orders_by_status():
    return query("SELECT order_status AS status, COUNT(*) AS n FROM orders GROUP BY order_status ORDER BY n DESC")


def top_products(limit=5):
    return query(
        f"""SELECT oi.product_name AS name, SUM(oi.quantity) AS units, SUM(oi.quantity * oi.unit_price) AS revenue
            FROM order_items oi JOIN orders o ON o.id = oi.order_id WHERE {PAID}
            GROUP BY oi.product_name ORDER BY units DESC LIMIT ?""", (limit,))


def low_stock(threshold=5):
    return query("SELECT id, name, stock FROM products WHERE is_active = 1 AND stock <= ? ORDER BY stock, name",
                 (threshold,))


# ------------------------------------------------------------ products
def list_products_admin(search=""):
    sql = ("SELECT p.*, c.name AS category_name FROM products p "
           "LEFT JOIN categories c ON c.id = p.category_id")
    params = []
    if search.strip():
        sql += " WHERE p.name LIKE ?"
        params.append(f"%{search.strip()}%")
    return query(sql + " ORDER BY p.id DESC", params)


def validate_product(data):
    errors = []
    if not str(data.get("name", "")).strip():
        errors.append("Enter a product name.")
    try:
        if float(data.get("price", -1)) < 0:
            errors.append("Price cannot be negative.")
    except (TypeError, ValueError):
        errors.append("Enter a valid price.")
    try:
        if int(data.get("stock", -1)) < 0:
            errors.append("Stock cannot be negative.")
    except (TypeError, ValueError):
        errors.append("Enter a valid stock number.")
    return errors


def _product_values(d):
    return (d.get("category_id"), d["name"].strip(), (d.get("description") or "").strip(),
            float(d["price"]), int(d["stock"]), int(bool(d.get("is_bundle"))),
            int(bool(d.get("is_featured"))), int(bool(d.get("is_active", True))))


def create_product(data):
    errors = validate_product(data)
    if errors:
        return False, errors
    pid = execute("INSERT INTO products (category_id, name, description, price, stock, is_bundle, "
                  "is_featured, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", _product_values(data))
    return True, pid


def update_product(pid, data):
    errors = validate_product(data)
    if errors:
        return False, errors
    execute("UPDATE products SET category_id = ?, name = ?, description = ?, price = ?, stock = ?, "
            "is_bundle = ?, is_featured = ?, is_active = ? WHERE id = ?", _product_values(data) + (pid,))
    return True, pid


def delete_product(pid):
    """Delete a product. Past orders keep the name and price they were bought at."""
    paths = [r["image_path"] for r in query("SELECT image_path FROM product_images WHERE product_id = ?", (pid,))]
    execute("DELETE FROM products WHERE id = ?", (pid,))
    for p in paths:
        _remove_file(p)


def product_images(pid):
    return query("SELECT * FROM product_images WHERE product_id = ? ORDER BY is_primary DESC, id", (pid,))


def add_images(pid, files):
    """files: list of (filename, bytes). Returns (number_added, error_messages)."""
    added, errors = 0, []
    for filename, data in files:
        try:
            rel = save_upload(data, UPLOAD_DIR, f"p{pid}-{secrets.token_hex(4)}")
        except ValueError as e:
            errors.append(f"{filename}: {e}")
            continue
        with get_conn() as conn:
            existing = conn.execute("SELECT is_primary, is_placeholder FROM product_images WHERE product_id = ?",
                                    (pid,)).fetchall()
            # The first real photo becomes the main image when only placeholders exist so far.
            primary = 1 if all(r["is_placeholder"] for r in existing) else 0
            if primary:
                conn.execute("DELETE FROM product_images WHERE product_id = ? AND is_placeholder = 1", (pid,))
                conn.execute("UPDATE product_images SET is_primary = 0 WHERE product_id = ?", (pid,))
            conn.execute("INSERT INTO product_images (product_id, image_path, is_primary, is_placeholder) "
                         "VALUES (?, ?, ?, 0)", (pid, rel, primary))
        added += 1
    return added, errors


def set_primary_image(pid, image_id):
    with get_conn() as conn:
        conn.execute("UPDATE product_images SET is_primary = 0 WHERE product_id = ?", (pid,))
        conn.execute("UPDATE product_images SET is_primary = 1 WHERE id = ? AND product_id = ?", (image_id, pid))


def delete_image(pid, image_id):
    with get_conn() as conn:
        row = conn.execute("SELECT image_path, is_primary FROM product_images WHERE id = ? AND product_id = ?",
                           (image_id, pid)).fetchone()
        if not row:
            return
        conn.execute("DELETE FROM product_images WHERE id = ?", (image_id,))
        if row["is_primary"]:
            conn.execute("UPDATE product_images SET is_primary = 1 WHERE id = "
                         "(SELECT id FROM product_images WHERE product_id = ? ORDER BY id LIMIT 1)", (pid,))
    _remove_file(row["image_path"])


# ---------------------------------------------------------- categories
def create_category(name, description, image=None):
    name = (name or "").strip()
    if not name:
        return False, "Enter a category name."
    path = None
    try:
        if image:
            path = save_upload(image, UPLOAD_DIR, f"cat-{secrets.token_hex(4)}")
        execute("INSERT INTO categories (name, description, image_path) VALUES (?, ?, ?)",
                (name, (description or "").strip(), path))
    except ValueError as e:
        return False, str(e)
    except sqlite3.IntegrityError:
        _remove_file(path)
        return False, "A category with this name already exists."
    return True, "Category added."


def update_category(cid, name, description, image=None):
    name = (name or "").strip()
    if not name:
        return False, "Enter a category name."
    old = query_one("SELECT image_path FROM categories WHERE id = ?", (cid,))
    new_path = None
    try:
        if image:
            new_path = save_upload(image, UPLOAD_DIR, f"cat-{secrets.token_hex(4)}")
        execute("UPDATE categories SET name = ?, description = ?, image_path = COALESCE(?, image_path) WHERE id = ?",
                (name, (description or "").strip(), new_path, cid))
    except ValueError as e:
        return False, str(e)
    except sqlite3.IntegrityError:
        _remove_file(new_path)
        return False, "A category with this name already exists."
    if new_path and old:
        _remove_file(old["image_path"])
    return True, "Category saved."


def delete_category(cid):
    """Products in the category stay in the shop and become uncategorised."""
    old = query_one("SELECT image_path FROM categories WHERE id = ?", (cid,))
    execute("DELETE FROM categories WHERE id = ?", (cid,))
    if old:
        _remove_file(old["image_path"])


def category_counts():
    return {r["category_id"]: r["n"] for r in
            query("SELECT category_id, COUNT(*) AS n FROM products GROUP BY category_id")}


# -------------------------------------------------------------- orders
_ORDER_SELECT = """SELECT o.*, u.name AS customer_name, u.email AS customer_email, u.phone AS customer_phone
                   FROM orders o JOIN users u ON u.id = o.user_id"""


def list_orders(status=None, search=""):
    sql, params = _ORDER_SELECT + " WHERE 1 = 1", []
    if status:
        sql += " AND o.order_status = ?"
        params.append(status)
    if search.strip():
        like = f"%{search.strip()}%"
        sql += " AND (o.order_number LIKE ? OR u.email LIKE ? OR u.name LIKE ?)"
        params += [like, like, like]
    return query(sql + " ORDER BY o.id DESC", params)


def _restore_stock(conn, order_id):
    for it in conn.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)):
        if it["product_id"] is not None:
            conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (it["quantity"], it["product_id"]))


def update_order_status(order_id, new_status):
    """Move an order along the delivery stages. Only possible once the payment is approved."""
    if new_status not in ORDER_STAGES[1:]:
        return False, "Choose a delivery stage."
    o = query_one("SELECT order_status, payment_status FROM orders WHERE id = ?", (order_id,))
    if not o or o["payment_status"] != "Approved" or o["order_status"] not in ORDER_STAGES[1:]:
        return False, "Approve the payment first, or the order is closed."
    execute("UPDATE orders SET order_status = ? WHERE id = ?", (new_status, order_id))
    return True, f"Order marked {new_status}."


def admin_cancel_order(order_id):
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        o = conn.execute("SELECT order_status FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not o or o["order_status"] in ("Delivered", "Cancelled", "Payment rejected"):
            return False, "This order cannot be cancelled."
        _restore_stock(conn, order_id)
        conn.execute("UPDATE orders SET order_status = 'Cancelled', cancelled_at = CURRENT_TIMESTAMP WHERE id = ?",
                     (order_id,))
    return True, "Order cancelled and stock restored. Refund the customer, then mark it refunded under Payments."


# ------------------------------------------------------------ payments
_PAY_SELECT = """SELECT pay.*, o.order_number, o.order_status, o.total, o.delivery_note, o.created_at AS order_date,
                        o.ship_name, o.ship_phone, o.ship_house_flat, o.ship_street, o.ship_area,
                        o.ship_city, o.ship_state, o.ship_pin,
                        u.name AS customer_name, u.email AS customer_email
                 FROM payments pay JOIN orders o ON o.id = pay.order_id JOIN users u ON u.id = o.user_id"""


def pending_payments():
    return query(_PAY_SELECT + " WHERE pay.status = 'Pending verification' "
                 "AND o.order_status = 'Pending verification' ORDER BY pay.id")


def reviewed_payments(limit=50):
    return query(_PAY_SELECT + " WHERE pay.status IN ('Approved', 'Rejected') ORDER BY pay.reviewed_at DESC, pay.id DESC LIMIT ?",
                 (limit,))


def refunds_due():
    """Cancelled orders whose customer paid (or claimed to) and has not been refunded yet."""
    return query(_PAY_SELECT + " WHERE o.order_status = 'Cancelled' AND pay.refunded_at IS NULL "
                 "AND pay.status IN ('Pending verification', 'Approved') ORDER BY pay.id")


def mark_refunded(payment_id):
    execute("UPDATE payments SET refunded_at = CURRENT_TIMESTAMP WHERE id = ?", (payment_id,))


def approve_payment(payment_id):
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        p = conn.execute("SELECT p.order_id, p.status, o.order_status FROM payments p "
                         "JOIN orders o ON o.id = p.order_id WHERE p.id = ?", (payment_id,)).fetchone()
        if not p or p["status"] != "Pending verification" or p["order_status"] != "Pending verification":
            return False, "This payment is no longer waiting for review."
        conn.execute("UPDATE payments SET status = 'Approved', reviewed_at = CURRENT_TIMESTAMP WHERE id = ?",
                     (payment_id,))
        conn.execute("UPDATE orders SET payment_status = 'Approved', order_status = 'Confirmed' WHERE id = ?",
                     (p["order_id"],))
    return True, "Payment approved. The order is now Confirmed."


def reject_payment(payment_id, note=""):
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        p = conn.execute("SELECT p.order_id, p.status, o.order_status FROM payments p "
                         "JOIN orders o ON o.id = p.order_id WHERE p.id = ?", (payment_id,)).fetchone()
        if not p or p["status"] != "Pending verification" or p["order_status"] != "Pending verification":
            return False, "This payment is no longer waiting for review."
        _restore_stock(conn, p["order_id"])
        conn.execute("UPDATE payments SET status = 'Rejected', admin_note = ?, reviewed_at = CURRENT_TIMESTAMP "
                     "WHERE id = ?", ((note or "").strip(), payment_id))
        conn.execute("UPDATE orders SET payment_status = 'Rejected', order_status = 'Payment rejected' WHERE id = ?",
                     (p["order_id"],))
    return True, "Payment rejected and stock restored."


# ----------------------------------------------------------- customers
def list_customers():
    return query(
        f"""SELECT u.id, u.name, u.email, u.phone, u.created_at,
                   COUNT(o.id) AS orders,
                   COALESCE(SUM(CASE WHEN {PAID} THEN o.total END), 0) AS spent
            FROM users u LEFT JOIN orders o ON o.user_id = u.id
            WHERE u.role = 'customer' GROUP BY u.id ORDER BY u.id DESC""")


# ------------------------------------------------------------ messages
def list_messages():
    return query("SELECT * FROM contact_messages ORDER BY id DESC")


def add_message(name, email, message):
    execute("INSERT INTO contact_messages (name, email, message) VALUES (?, ?, ?)",
            (name.strip(), email.strip(), message.strip()))


def delete_message(message_id):
    execute("DELETE FROM contact_messages WHERE id = ?", (message_id,))
