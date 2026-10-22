"""Customer sign in."""
import streamlit as st

import auth
from accounts import authenticate

st.title("Sign in")

if auth.is_logged_in():
    st.switch_page("views/admin_dashboard.py" if auth.is_admin() else "views/shop.py")

with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Sign in", type="primary")

if submitted:
    user = authenticate(email, password, "customer")
    if user:
        auth.login(user)
        st.rerun()
    else:
        st.error("That email and password do not match. Check them and try again.")

st.caption("New here?")
st.page_link("views/register.py", label="Create an account")
