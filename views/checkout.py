"""Checkout in three steps on one page: delivery address -> payment (QR) -> confirmation."""
from pathlib import Path

import streamlit as st

import addresses
import auth
import cart
import db
import orders
from utils.components import address_fields
from utils.format import money
from utils.validation import validate_address, valid_transaction_id

ROOT = Path(__file__).resolve().parent.parent

auth.require_login()
user = auth.current_user()
if user["role"] != "customer":
    st.info("Checkout is for customer accounts.")
    st.stop()

step = st.session_state.get("checkout_step", "address")


def _go(next_step):
    st.session_state["checkout_step"] = next_step
    st.rerun()


def _summary(items):
    t = cart.totals(items)
    st.subheader("Order summary")
    for it in items:
        st.markdown(f"{it['quantity']} × {it['name']} — {money(it['price'] * it['quantity'])}")
    st.divider()
    st.markdown(f"Subtotal: **{money(t['subtotal'])}**")
    st.markdown("Delivery: **Free**" if t["delivery_fee"] == 0 else f"Delivery: **{money(t['delivery_fee'])}**")
    st.markdown(f"### Total: {money(t['total'])}")
    return t


# ---------- Step 3: confirmation ----------
if step == "done":
    order = orders.get_order(st.session_state.get("last_order_id", 0), user["id"])
    if not order:
        _go("address")
    st.title("Thank you, your order is placed")
    st.success(f"Order {order['order_number']} is waiting for payment verification. "
               "We will confirm it as soon as we have checked your payment.")
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Items")
        for it in orders.order_items(order["id"]):
            st.markdown(f"{it['quantity']} × {it['product_name']} — {money(it['unit_price'] * it['quantity'])}")
        st.markdown(f"### Total paid: {money(order['total'])}")
        st.caption(f"Status: {order['order_status']}")
    with right:
        st.subheader("Delivering to")
        st.text(addresses.format_address(orders.order_address(order)))
        if order["delivery_note"]:
            st.caption(f"Note: {order['delivery_note']}")
    st.write("")
    b1, b2 = st.columns(2)
    if b1.button("View my orders", type="primary"):
        st.session_state["checkout_step"] = "address"
        st.switch_page("views/my_orders.py")
    if b2.button("Continue shopping"):
        st.session_state["checkout_step"] = "address"
        st.switch_page("views/shop.py")
    st.stop()

# ---------- Steps 1 and 2 need a cart ----------
items = cart.get_cart(user["id"])
if not items:
    st.title("Checkout")
    st.info("Your cart is empty. Add some flowers first.")
    st.page_link("views/shop.py", label="Browse flowers")
    st.stop()

problems = cart.cart_problems(items)
if problems or cart.has_unavailable(items):
    st.title("Checkout")
    for msg in problems:
        st.error(msg)
    if cart.has_unavailable(items):
        st.caption("Some items in your cart are out of stock. Remove them to continue.")
    st.page_link("views/cart_page.py", label="Back to cart")
    st.stop()

# ---------- Step 1: delivery address ----------
if step == "address":
    st.title("Delivery details")
    left, right = st.columns([2, 1], gap="large")
    with left:
        saved = addresses.list_addresses(user["id"])
        NEW = "Add a new address"
        labels = {}
        for a in saved:
            title = a["label"] or a["recipient_name"]
            labels[f"{title}: {a['house_flat']}, {a['street']}, {a['city']} - {a['pin_code']}"] = a
        choices = list(labels) + [NEW]
        choice = st.radio("Deliver to", choices, key="co_choice") if saved else NEW

        save_new, new_label = False, ""
        if choice == NEW:
            address = address_fields("co_new")
            save_new = st.checkbox("Save this address to my profile", value=True, key="co_save")
            if save_new:
                new_label = st.text_input("Label (optional)", placeholder="Home, Office…", key="co_label")
        else:
            address = labels[choice]
            st.text(addresses.format_address(address))

        note = st.text_area("Delivery note (optional)", max_chars=200, key="co_note",
                            placeholder="e.g. Call before arriving")
        b1, b2 = st.columns([1, 1])
        if b2.button("Continue to payment", type="primary", use_container_width=True):
            errors = validate_address(address)
            if errors:
                for e in errors:
                    st.error(e)
            else:
                st.session_state["checkout"] = {"address": {k: address[k] for k in addresses.FIELDS},
                                                "note": note, "save": save_new, "label": new_label}
                _go("payment")
        if b1.button("← Back to cart", use_container_width=True):
            st.switch_page("views/cart_page.py")
    with right:
        _summary(items)

# ---------- Step 2: payment ----------
elif step == "payment":
    draft = st.session_state.get("checkout")
    if not draft:
        _go("address")
    st.title("Pay by QR")
    left, right = st.columns([1, 1], gap="large")
    with left:
        total = _summary(items)["total"]
        st.subheader("Delivering to")
        st.text(addresses.format_address(draft["address"]))
        if draft["note"]:
            st.caption(f"Note: {draft['note']}")
    with right:
        st.markdown(f"#### Amount to pay: {money(total)}")
        qr = db.get_setting("qr_image_path", "")
        if qr and (ROOT / qr).exists():
            st.image(str(ROOT / qr), width=280)
        else:
            st.info("The shop has not set up its payment QR yet. Please contact us.")
        st.caption("Scan the QR with any UPI app, pay the exact amount, then enter the transaction ID "
                   "(UTR / reference number) below.")
        txn = st.text_input("Transaction ID", key="co_txn", max_chars=40)
        b1, b2 = st.columns(2)
        if b1.button("← Edit address", use_container_width=True):
            _go("address")
        if b2.button("I have paid", type="primary", use_container_width=True,
                     disabled=not (qr and (ROOT / qr).exists())):
            if not valid_transaction_id(txn):
                st.error("Enter the transaction ID from your payment app (6-40 letters, numbers, - or _).")
            else:
                try:
                    order_id, _ = orders.place_order(user["id"], draft["address"], draft["note"], txn)
                except orders.OrderError as e:
                    st.error(str(e))
                else:
                    if draft.get("save"):
                        addresses.add_address(user["id"], draft["address"], draft.get("label", ""))
                    st.session_state["last_order_id"] = order_id
                    st.session_state.pop("checkout", None)
                    st.session_state.pop("co_txn", None)
                    _go("done")
