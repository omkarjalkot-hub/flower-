"""Separate admin sign in. Customer accounts cannot sign in here."""
import streamlit as st

import auth
from accounts import authenticate

st.title("Admin sign in")

if auth.is_logged_in():
    st.switch_page("views/admin_dashboard.py" if auth.is_admin() else "views/shop.py")

with st.form("admin_login_form"):
    email = st.text_input("Admin email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Sign in", type="primary")

if submitted:
    user = authenticate(email, password, "admin")
    if user:
        auth.login(user)
        st.rerun()
    else:
        st.error("That email and password do not match an admin account.")
