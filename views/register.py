"""Customer registration (email + password)."""
import streamlit as st

import auth
from accounts import authenticate, create_user
from utils.validation import normalize_phone, password_problem, valid_email

st.title("Create your account")

if auth.is_logged_in():
    st.switch_page("views/admin_dashboard.py" if auth.is_admin() else "views/shop.py")

with st.form("register_form"):
    name = st.text_input("Full name")
    email = st.text_input("Email")
    phone = st.text_input("Mobile number (optional)")
    password = st.text_input("Password", type="password", help="At least 8 characters, with letters and numbers.")
    confirm = st.text_input("Confirm password", type="password")
    submitted = st.form_submit_button("Create account", type="primary")

if submitted:
    errors = []
    if not name.strip():
        errors.append("Enter your name.")
    if not valid_email(email):
        errors.append("Enter a valid email address.")
    clean_phone = ""
    if phone.strip():
        clean_phone = normalize_phone(phone)
        if clean_phone is None:
            errors.append("Enter a valid 10-digit mobile number, or leave it blank.")
    problem = password_problem(password)
    if problem:
        errors.append(problem)
    elif password != confirm:
        errors.append("Passwords do not match.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        ok, msg = create_user(name, email, clean_phone or "", password)
        if ok:
            auth.login(authenticate(email, password, "customer"))
            st.rerun()
        else:
            st.error(msg)

st.caption("Already have an account?")
st.page_link("views/login.py", label="Sign in")
