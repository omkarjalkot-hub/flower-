"""My Orders: status tracking, delivery address, cancellation."""
import streamlit as st

import addresses
import auth
import orders
from utils.format import fmt_time, money

auth.require_login()
user = auth.current_user()

st.title("My orders")
rows = orders.get_orders(user["id"])
if not rows:
    st.info("You have not placed any orders yet.")
    st.page_link("views/shop.py", label="Browse flowers")
    st.stop()


def _timeline(status):
    if status not in orders.ORDER_STAGES:
        return ""
    current = orders.ORDER_STAGES.index(status)
    parts = []
    for i, stage in enumerate(orders.ORDER_STAGES):
        if i < current:
            parts.append(f"✅ {stage}")
        elif i == current:
            parts.append(f"🟠 **{stage}**")
        else:
            parts.append(f"⚪ {stage}")
    return "  →  ".join(parts)


for idx, o in enumerate(rows):
    title = f"{o['order_number']}  ·  {money(o['total'])}  ·  {o['order_status']}"
    with st.expander(title, expanded=(idx == 0)):
        st.caption(f"Placed on {fmt_time(o['created_at'])}")
        if o["order_status"] == "Cancelled":
            pay = orders.order_payment(o["id"])
            if pay and pay["refunded_at"]:
                st.info(f"This order was cancelled. Your refund of {money(pay['amount'])} was sent on "
                        f"{fmt_time(pay['refunded_at'])}.")
            else:
                st.info("This order was cancelled. " + orders.REFUND_MESSAGE)
        elif o["order_status"] == "Payment rejected":
            pay = orders.order_payment(o["id"])
            st.warning("Your payment could not be verified."
                       + (f" Shop note: {pay['admin_note']}" if pay and pay["admin_note"] else ""))
        else:
            st.markdown(_timeline(o["order_status"]))

        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("**Items**")
            for it in orders.order_items(o["id"]):
                st.markdown(f"{it['quantity']} × {it['product_name']} — {money(it['unit_price'] * it['quantity'])}")
            st.markdown(f"**Total: {money(o['total'])}**")
        with right:
            st.markdown("**Delivery address**")
            st.text(addresses.format_address(orders.order_address(o)))
            if o["delivery_note"]:
                st.caption(f"Note: {o['delivery_note']}")
            pay = orders.order_payment(o["id"])
            if pay:
                st.caption(f"Payment: {pay['status']} · Transaction ID {pay['transaction_id']}")

        if o["order_status"] in orders.CANCELLABLE:
            with st.popover("Cancel this order"):
                st.write("Cancel this order? " + orders.REFUND_MESSAGE)
                if st.button("Yes, cancel order", key=f"cancel_{o['id']}"):
                    ok, msg = orders.cancel_order(user["id"], o["id"])
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)
