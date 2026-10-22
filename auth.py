"""Session-based access control for Streamlit pages."""
import streamlit as st


def current_user():
    return st.session_state.get("user")


def is_logged_in() -> bool:
    return current_user() is not None


def is_admin() -> bool:
    user = current_user()
    return bool(user and user["role"] == "admin")


def login(user: dict):
    st.session_state["user"] = {
        "id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"],
    }


def logout():
    st.session_state.clear()


def require_login():
    """Stop the page unless a customer or admin is signed in."""
    if not is_logged_in():
        st.warning("Please sign in to see this page.")
        st.page_link("views/login.py", label="Go to sign in")
        st.stop()


def require_admin():
    """Stop the page unless an admin is signed in. Checked on every admin page."""
    if not is_admin():
        st.error("This page is for shop admins only.")
        st.stop()
