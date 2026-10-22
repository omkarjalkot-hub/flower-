"""Admin dashboard: sales stats and things that need attention."""
import pandas as pd
import streamlit as st

import admin_ops
import auth
from utils.format import money

auth.require_admin()

st.title("Dashboard")
s = admin_ops.stats()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Sales (approved orders)", money(s["revenue"]))
m2.metric("Paid orders", s["paid_orders"])
m3.metric("All orders", s["orders"])
m4.metric("Customers", s["customers"])

if s["pending_payments"] or s["refunds_due"]:
    a1, a2 = st.columns(2)
    if s["pending_payments"]:
        a1.warning(f"{s['pending_payments']} payment(s) waiting for review")
        a1.page_link("views/admin_payments.py", label="Review payments")
    if s["refunds_due"]:
        a2.warning(f"{s['refunds_due']} refund(s) to send")
        a2.page_link("views/admin_payments.py", label="See refunds")

st.subheader("Sales in the last 14 days")
daily = admin_ops.daily_revenue(14)
if daily:
    df = pd.DataFrame(daily).set_index("day")
    st.bar_chart(df["revenue"])
else:
    st.caption("No approved sales yet.")

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Orders by status")
    rows = admin_ops.orders_by_status()
    if rows:
        st.dataframe(pd.DataFrame(rows).rename(columns={"status": "Status", "n": "Orders"}),
                     hide_index=True, use_container_width=True)
    else:
        st.caption("No orders yet.")
    st.subheader("Best sellers")
    top = admin_ops.top_products()
    if top:
        df = pd.DataFrame(top)
        df["revenue"] = df["revenue"].map(money)
        st.dataframe(df.rename(columns={"name": "Flower", "units": "Units sold", "revenue": "Sales"}),
                     hide_index=True, use_container_width=True)
    else:
        st.caption("Best sellers appear after the first approved order.")
with right:
    st.subheader("Low or out of stock")
    low = admin_ops.low_stock()
    if low:
        df = pd.DataFrame(low)[["name", "stock"]]
        st.dataframe(df.rename(columns={"name": "Flower", "stock": "In stock"}),
                     hide_index=True, use_container_width=True)
    else:
        st.caption("Everything is well stocked.")
    st.caption("Sales count an order once its payment is approved and it has not been cancelled.")
