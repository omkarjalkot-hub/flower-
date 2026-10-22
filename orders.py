"""Orders, payments submission and cancellation (no Streamlit dependency)."""
import secrets
import sqlite3
from datetime import datetime

from addresses import FIELDS
from db import get_conn, get_setting, query, query_one
from utils.validation import normalize_phone, validate_address, valid_transaction_id

ORDER_STAGES = ["Pending verification", "Confirmed", "Packed", "Out for delivery", "Delivered"]
CANCELLABLE = {"Pending verification", "Confirmed"}   # customers can cancel until the order is Packed
REFUND_MESSAGE = "The amount you paid will be refunded to you within 24-48 hours."


class OrderError(Exception):
    """A problem the customer can fix; the message is safe to show."""


def _delivery_fee():
    try:
        return float(get_setting("delivery_fee", "0") or 0)
    except ValueError:
        return 0.0


def place_order(user_id, address, note, transaction_id):
    """Create the order, snapshot the address, reduce stock, record the payment and empty the cart.
    Everything happens in one transaction. Returns (order_id, order_number)."""
    errors = validate_address(address)
    if errors:
        raise OrderError(errors[0])
    txn = (transaction_id or "").strip()
    if not valid_transaction_id(txn):
        raise OrderError("Enter the transaction ID from your payment app (6-40 letters, numbers, - or _).")
    fee = _delivery_fee()
    ship = {k: str(address[k]).strip() for k in FIELDS}
    ship["phone"] = normalize_phone(ship["phone"]) or ship["phone"]

    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        items = conn.execute(
            """SELECT ci.product_id, ci.quantity, p.name, p.price, p.stock, p.is_active
               FROM cart_items ci JOIN products p ON p.id = ci.product_id
               WHERE ci.user_id = ? ORDER BY ci.id""", (user_id,)).fetchall()
        if not items:
            raise OrderError("Your cart is empty.")
        for it in items:
            if not it["is_active"] or it["stock"] <= 0:
                raise OrderError(f"{it['name']} is out of stock. Go back to the cart and remove it.")
            if it["quantity"] > it["stock"]:
                raise OrderError(f"Only {it['stock']} of {it['name']} left. Lower the quantity in your cart.")
        if conn.execute("SELECT 1 FROM payments WHERE lower(transaction_id) = lower(?) AND status != 'Rejected'",
                        (txn,)).fetchone():
            raise OrderError("This transaction ID has already been used for another order.")

        subtotal = sum(it["price"] * it["quantity"] for it in items)
        total = subtotal + fee
        order_id = None
        for _ in range(5):
            number = f"PB{datetime.now():%y%m%d}-{secrets.token_hex(2).upper()}"
            try:
                order_id = conn.execute(
                    """INSERT INTO orders (user_id, order_number, subtotal, delivery_fee, total,
                           order_status, payment_status, delivery_note, ship_name, ship_phone,
                           ship_house_flat, ship_street, ship_area, ship_city, ship_state, ship_pin)
                       VALUES (?, ?, ?, ?, ?, 'Pending verification', 'Pending verification', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, number, subtotal, fee, total, (note or "").strip(),
                     ship["recipient_name"], ship["phone"], ship["house_flat"], ship["street"],
                     ship["area_landmark"], ship["city"], ship["state"], ship["pin_code"])).lastrowid
                break
            except sqlite3.IntegrityError:
                continue
        if order_id is None:
            raise OrderError("Could not create the order. Please try again.")

        for it in items:
            conn.execute("INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity) "
                         "VALUES (?, ?, ?, ?, ?)", (order_id, it["product_id"], it["name"], it["price"], it["quantity"]))
            cur = conn.execute("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
                               (it["quantity"], it["product_id"], it["quantity"]))
            if cur.rowcount != 1:
                raise OrderError(f"{it['name']} just sold out. Please review your cart.")
        conn.execute("INSERT INTO payments (order_id, amount, transaction_id, status) "
                     "VALUES (?, ?, ?, 'Pending verification')", (order_id, total, txn))
        conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
    return order_id, number


def get_orders(user_id):
    return query("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user_id,))


def get_order(order_id, user_id=None):
    if user_id is None:
        return query_one("SELECT * FROM orders WHERE id = ?", (order_id,))
    return query_one("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))


def order_items(order_id):
    return query("SELECT * FROM order_items WHERE order_id = ? ORDER BY id", (order_id,))


def order_payment(order_id):
    return query_one("SELECT * FROM payments WHERE order_id = ? ORDER BY id DESC LIMIT 1", (order_id,))


def order_address(order):
    """The delivery address saved with the order, using the same keys as saved addresses."""
    return {"recipient_name": order["ship_name"], "phone": order["ship_phone"],
            "house_flat": order["ship_house_flat"], "street": order["ship_street"],
            "area_landmark": order["ship_area"], "city": order["ship_city"],
            "state": order["ship_state"], "pin_code": order["ship_pin"]}


def cancel_order(user_id, order_id):
    """Customer cancellation. Allowed until the order is Packed. Returns (ok, message)."""
    with get_conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        order = conn.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id)).fetchone()
        if not order:
            return False, "Order not found."
        if order["order_status"] not in CANCELLABLE:
            return False, "This order can no longer be cancelled."
        for it in conn.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)):
            if it["product_id"] is not None:
                conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (it["quantity"], it["product_id"]))
        conn.execute("UPDATE orders SET order_status = 'Cancelled', cancelled_at = CURRENT_TIMESTAMP WHERE id = ?",
                     (order_id,))
    return True, "Order cancelled. " + REFUND_MESSAGE
