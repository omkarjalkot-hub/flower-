"""Shop name, delivery fee and contact details."""
import streamlit as st

import auth
import db

auth.require_admin()
st.title("Shop settings")

with st.form("settings_form"):
    name = st.text_input("Shop name", value=db.get_setting("shop_name", "Petal & Bloom"))
    tagline = st.text_input("Tagline", value=db.get_setting("tagline"))
    try:
        fee_now = float(db.get_setting("delivery_fee", "0") or 0)
    except ValueError:
        fee_now = 0.0
    fee = st.number_input("Delivery fee (₹)", min_value=0.0, value=fee_now, step=10.0,
                          help="0 means delivery is free for every order.")
    st.markdown("**Contact details shown on the Contact page**")
    phone = st.text_input("Phone", value=db.get_setting("contact_phone"))
    email = st.text_input("Email", value=db.get_setting("contact_email"))
    address = st.text_area("Shop address", value=db.get_setting("contact_address"))
    hours = st.text_input("Opening hours", value=db.get_setting("opening_hours"), placeholder="Daily, 8 AM to 8 PM")
    if st.form_submit_button("Save settings", type="primary"):
        if not name.strip():
            st.error("Enter a shop name.")
        else:
            for key, val in {"shop_name": name.strip(), "tagline": tagline.strip(), "delivery_fee": str(fee),
                             "contact_phone": phone.strip(), "contact_email": email.strip(),
                             "contact_address": address.strip(), "opening_hours": hours.strip()}.items():
                db.set_setting(key, val)
            st.success("Settings saved.")
            st.rerun()
