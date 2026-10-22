"""Payment review: approve or reject, send refunds."""
import streamlit as st

import addresses
import admin_ops
import auth
import orders
from utils.format import fmt_time, money

auth.require_admin()
st.title("Payments")

pending = admin_ops.pending_payments()
refunds = admin_ops.refunds_due()
tab_review, tab_refund, tab_history = st.tabs(
    [f"To review ({len(pending)})", f"Refunds to send ({len(refunds)})", "History"])


def _address_of(p):
    return {"recipient_name": p["ship_name"], "phone": p["ship_phone"], "house_flat": p["ship_house_flat"],
            "street": p["ship_street"], "area_landmark": p["ship_area"], "city": p["ship_city"],
            "state": p["ship_state"], "pin_code": p["ship_pin"]}


def _details(p):
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown(f"**Customer:** {p['customer_name']} ({p['customer_email']})")
        st.markdown(f"**Amount:** {money(p['amount'])}")
        st.markdown(f"**Transaction ID:** `{p['transaction_id']}`")
        st.caption(f"Submitted {fmt_time(p['submitted_at'])}")
        for it in orders.order_items(p["order_id"]):
            st.markdown(f"{it['quantity']} × {it['product_name']} — {money(it['unit_price'] * it['quantity'])}")
    with right:
        st.markdown("**Deliver to**")
        st.text(addresses.format_address(_address_of(p)))
        if p["delivery_note"]:
            st.caption(f"Note: {p['delivery_note']}")


with tab_review:
    if not pending:
        st.info("No payments are waiting for review.")
    for p in pending:
        with st.expander(f"{p['order_number']} · {money(p['amount'])} · {p['customer_name']}", expanded=True):
            _details(p)
            note = st.text_input("Note to customer (shown if rejected)", key=f"note_{p['id']}")
            b1, b2, _ = st.columns([1, 1, 3])
            if b1.button("Approve", type="primary", key=f"ap_{p['id']}"):
                ok, msg = admin_ops.approve_payment(p["id"])
                st.toast(msg)
                st.rerun()
            if b2.button("Reject", key=f"rj_{p['id']}"):
                ok, msg = admin_ops.reject_payment(p["id"], note)
                st.toast(msg)
                st.rerun()

with tab_refund:
    st.caption("These orders were cancelled after the customer paid. Send the money back, then mark it done.")
    if not refunds:
        st.info("No refunds are waiting.")
    for p in refunds:
        with st.expander(f"{p['order_number']} · {money(p['amount'])} · {p['customer_name']}", expanded=True):
            _details(p)
            if st.button("Mark refunded", key=f"rf_{p['id']}", type="primary"):
                admin_ops.mark_refunded(p["id"])
                st.rerun()

with tab_history:
    history = admin_ops.reviewed_payments()
    if not history:
        st.info("Reviewed payments will appear here.")
    for p in history:
        label = f"{p['order_number']} · {money(p['amount'])} · {p['status']}"
        with st.expander(label):
            _details(p)
            st.caption(f"Reviewed {fmt_time(p['reviewed_at'])}"
                       + (f" · Note: {p['admin_note']}" if p["admin_note"] else "")
                       + (f" · Refunded {fmt_time(p['refunded_at'])}" if p["refunded_at"] else ""))
