"""Customer list with saved addresses."""
import pandas as pd
import streamlit as st

import addresses
import admin_ops
import auth
from utils.format import fmt_time, money

auth.require_admin()
st.title("Customers")

rows = admin_ops.list_customers()
if not rows:
    st.info("No customers have registered yet.")
    st.stop()

df = pd.DataFrame(rows)
df["joined"] = df["created_at"].map(fmt_time)
df["spent"] = df["spent"].map(money)
st.dataframe(
    df[["name", "email", "phone", "orders", "spent", "joined"]].rename(columns={
        "name": "Name", "email": "Email", "phone": "Phone", "orders": "Orders", "spent": "Paid orders total",
        "joined": "Joined"}),
    hide_index=True, use_container_width=True)

st.subheader("Saved addresses")
who = st.selectbox("Customer", rows, format_func=lambda r: f"{r['name']} ({r['email']})")
saved = addresses.list_addresses(who["id"])
if not saved:
    st.caption("This customer has no saved addresses.")
for a in saved:
    st.text(addresses.format_address(a) + ("\n(default)" if a["is_default"] else ""))
