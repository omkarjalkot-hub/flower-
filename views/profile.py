"""My Profile: personal details, saved addresses, password."""
import streamlit as st

import accounts
import addresses
import auth
import db
from utils.components import address_fields
from utils.validation import normalize_phone, password_problem

auth.require_login()
user = auth.current_user()
if user["role"] != "customer":
    st.info("Profiles are for customer accounts.")
    st.stop()

st.title("My profile")
tab_details, tab_addr, tab_pw = st.tabs(["Details", "Saved addresses", "Password"])

# ---- Details ----
with tab_details:
    row = db.query_one("SELECT name, email, phone FROM users WHERE id = ?", (user["id"],))
    with st.form("profile_form"):
        name = st.text_input("Full name", value=row["name"])
        st.text_input("Email", value=row["email"], disabled=True)
        phone = st.text_input("Mobile number", value=row["phone"] or "")
        if st.form_submit_button("Save changes", type="primary"):
            clean = normalize_phone(phone) if phone.strip() else ""
            if not name.strip():
                st.error("Enter your name.")
            elif clean is None:
                st.error("Enter a valid 10-digit mobile number, or leave it blank.")
            else:
                accounts.update_profile(user["id"], name, clean)
                st.session_state["user"]["name"] = name.strip()
                st.success("Profile updated.")

# ---- Addresses ----
with tab_addr:
    saved = addresses.list_addresses(user["id"])
    if not saved:
        st.info("You have no saved addresses yet. Add one below and pick it at checkout.")
    for a in saved:
        title = (a["label"] or a["recipient_name"]) + ("  (default)" if a["is_default"] else "")
        with st.expander(title):
            with st.form(f"edit_addr_{a['id']}"):
                label = st.text_input("Label (optional)", value=a["label"] or "", key=f"lbl_{a['id']}")
                values = address_fields(f"ea{a['id']}", a)
                if st.form_submit_button("Save address", type="primary"):
                    ok, res = addresses.update_address(user["id"], a["id"], values, label)
                    if ok:
                        st.success("Address updated.")
                        st.rerun()
                    else:
                        for e in res:
                            st.error(e)
            b1, b2, _ = st.columns([1, 1, 2])
            if not a["is_default"]:
                if b1.button("Make default", key=f"def_{a['id']}"):
                    addresses.set_default(user["id"], a["id"])
                    st.rerun()
            if b2.button("Delete", key=f"del_{a['id']}"):
                addresses.delete_address(user["id"], a["id"])
                st.rerun()

    with st.expander("Add a new address", expanded=not saved):
        with st.form("add_addr_form", clear_on_submit=True):
            label = st.text_input("Label (optional)", placeholder="Home, Office…", key="new_lbl")
            values = address_fields("na")
            make_default = st.checkbox("Make this my default address", key="na_default")
            if st.form_submit_button("Save address", type="primary"):
                ok, res = addresses.add_address(user["id"], values, label, make_default)
                if ok:
                    st.rerun()
                else:
                    for e in res:
                        st.error(e)

# ---- Password ----
with tab_pw:
    with st.form("password_form", clear_on_submit=True):
        current = st.text_input("Current password", type="password")
        new = st.text_input("New password", type="password", help="At least 8 characters, with letters and numbers.")
        confirm = st.text_input("Confirm new password", type="password")
        if st.form_submit_button("Change password", type="primary"):
            problem = password_problem(new)
            if problem:
                st.error(problem)
            elif new != confirm:
                st.error("The new passwords do not match.")
            else:
                ok, msg = accounts.change_password(user["id"], current, new)
                (st.success if ok else st.error)(msg)
