"""All orders: delivery addresses, status updates, cancellation."""
import streamlit as st

import addresses
import admin_ops
import auth
import orders
from utils.format import fmt_time, money

auth.require_admin()
st.title("Orders")

STATUSES = ["All"] + orders.ORDER_STAGES + ["Cancelled", "Payment rejected"]
f1, f2 = st.columns([1, 2])
status = f1.selectbox("Status", STATUSES)
search = f2.text_input("Search by order number, customer name or email")

rows = admin_ops.list_orders(None if status == "All" else status, search)
st.caption(f"{len(rows)} order{'s' if len(rows) != 1 else ''}")
if not rows:
    st.info("No orders match.")

DELIVERY_STAGES = orders.ORDER_STAGES[1:]
for o in rows:
    with st.expander(f"{o['order_number']} · {money(o['total'])} · {o['order_status']} · {o['customer_name']}"):
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown(f"**Customer:** {o['customer_name']} ({o['customer_email']})")
            st.caption(f"Placed {fmt_time(o['created_at'])}")
            for it in orders.order_items(o["id"]):
                st.markdown(f"{it['quantity']} × {it['product_name']} — {money(it['unit_price'] * it['quantity'])}")
            st.markdown(f"**Total: {money(o['total'])}**")
            pay = orders.order_payment(o["id"])
            if pay:
                st.caption(f"Payment: {pay['status']} · Transaction ID {pay['transaction_id']}")
        with right:
            st.markdown("**Deliver to**")
            st.text(addresses.format_address(orders.order_address(o)))
            if o["delivery_note"]:
                st.caption(f"Note: {o['delivery_note']}")

        if o["order_status"] == "Pending verification":
            st.info("Waiting for payment review.")
            st.page_link("views/admin_payments.py", label="Go to payments")
        elif o["order_status"] in DELIVERY_STAGES:
            c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
            new = c1.selectbox("Delivery status", DELIVERY_STAGES, index=DELIVERY_STAGES.index(o["order_status"]),
                               key=f"st_{o['id']}")
            if c2.button("Update status", key=f"up_{o['id']}"):
                ok, msg = admin_ops.update_order_status(o["id"], new)
                st.toast(msg)
                st.rerun()

        if o["order_status"] in ["Pending verification"] + DELIVERY_STAGES[:-1]:
            with st.popover("Cancel order"):
                st.write("Cancel this order and put the stock back?")
                if st.button("Yes, cancel", key=f"cx_{o['id']}"):
                    ok, msg = admin_ops.admin_cancel_order(o["id"])
                    st.toast(msg)
                    st.rerun()
