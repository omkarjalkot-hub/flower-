"""Contact page: shop details and a message form."""
import streamlit as st

import admin_ops
import auth
import db
from utils.validation import valid_email

st.title("Contact us")
left, right = st.columns(2, gap="large")

with left:
    st.subheader("Visit or call")
    details = [("Phone", db.get_setting("contact_phone")), ("Email", db.get_setting("contact_email")),
               ("Address", db.get_setting("contact_address")), ("Hours", db.get_setting("opening_hours"))]
    shown = [(k, v) for k, v in details if v]
    if not shown:
        st.caption("Contact details will appear here soon. Send us a message and we will reply.")
    for k, v in shown:
        st.markdown(f"**{k}:** {v}")

with right:
    st.subheader("Send a message")
    user = auth.current_user()
    with st.form("contact_form", clear_on_submit=True):
        name = st.text_input("Your name", value=user["name"] if user else "")
        email = st.text_input("Your email", value=user["email"] if user else "")
        message = st.text_area("Message", max_chars=1000)
        if st.form_submit_button("Send message", type="primary"):
            if not name.strip() or not message.strip():
                st.error("Enter your name and a message.")
            elif not valid_email(email):
                st.error("Enter a valid email address so we can reply.")
            else:
                admin_ops.add_message(name, email, message)
                st.success("Thank you. We have your message and will reply by email.")
