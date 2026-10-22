"""Petal & Bloom flower shop: entry point.  Run:  streamlit run app.py
No sidebar: the shop name and buttons live in a top bar."""
from pathlib import Path

import streamlit as st
from PIL import Image

import auth
import cart
from db import get_setting, init_db
from utils.images import make_logo
from utils.styles import apply_theme

LOGO = Path(__file__).resolve().parent / "assets" / "logo.png"
if not LOGO.exists():
    make_logo("assets/logo.png")

st.set_page_config(page_title="Petal & Bloom", page_icon=Image.open(LOGO), layout="wide",
                   initial_sidebar_state="collapsed")


@st.cache_resource
def _boot():
    init_db()  # creates the SQLite file, tables, demo flowers and placeholder images on first run
    return True


_boot()
apply_theme()


def logout_page():
    auth.logout()
    st.rerun()


shop = st.Page("views/shop.py", title="Petal & Bloom", default=True)
cart_pg = st.Page("views/cart_page.py", title="Cart", url_path="cart")
checkout = st.Page("views/checkout.py", title="Checkout", url_path="checkout")
my_orders = st.Page("views/my_orders.py", title="Track order", url_path="orders")
profile = st.Page("views/profile.py", title="My profile", url_path="profile")
login = st.Page("views/login.py", title="Sign in", url_path="login")
register = st.Page("views/register.py", title="Create account", url_path="register")
contact = st.Page("views/contact.py", title="Contact", url_path="contact")
admin_login = st.Page("views/admin_login.py", title="Admin sign in", url_path="admin-login")
admin_dash = st.Page("views/admin_dashboard.py", title="Dashboard", url_path="admin")
admin_orders = st.Page("views/admin_orders.py", title="Orders", url_path="admin-orders")
admin_pay = st.Page("views/admin_payments.py", title="Payments", url_path="admin-payments")
admin_prod = st.Page("views/admin_products.py", title="Products", url_path="admin-products")
admin_cats = st.Page("views/admin_categories.py", title="Categories", url_path="admin-categories")
admin_qr = st.Page("views/admin_qr.py", title="Payment QR", url_path="admin-qr")
admin_cust = st.Page("views/admin_customers.py", title="Customers", url_path="admin-customers")
admin_msgs = st.Page("views/admin_messages.py", title="Messages", url_path="admin-messages")
admin_set = st.Page("views/admin_settings.py", title="Settings", url_path="admin-settings")
logout = st.Page(logout_page, title="Sign out", url_path="logout")

ADMIN_NAV = [admin_dash, admin_orders, admin_pay, admin_prod, admin_cats, admin_qr, admin_cust, admin_msgs, admin_set]

if auth.is_admin():
    all_pages = [*ADMIN_NAV, logout]
elif auth.is_logged_in():
    all_pages = [shop, cart_pg, checkout, my_orders, profile, contact, logout]
else:
    all_pages = [shop, cart_pg, my_orders, login, register, contact, admin_login]

# position="hidden": pages still work, but no page list is drawn anywhere.
nav = st.navigation(all_pages, position="hidden")

shop_name = get_setting("shop_name", "Petal & Bloom")
user = auth.current_user()

with st.container(key="topbar"):
    if auth.is_admin():
        top = st.columns([3, 5])
        with top[0], st.container(key="brand"):
            st.page_link(admin_dash, label=f"{shop_name} · Admin")
        st.write("")
        with st.container(key="adminnav"):
            links = ADMIN_NAV + [logout]
            for col, pg in zip(st.columns(len(links)), links):
                with col:
                    st.page_link(pg)
    else:
        left, right = st.columns([5, 4], vertical_alignment="center")
        with left:
            logo_col, name_col = st.columns([1, 9], vertical_alignment="center", gap="small")
            with logo_col:
                st.image(str(LOGO), width=64)
            with name_col, st.container(key="brand"):
                st.page_link(shop, label=shop_name)
        with right, st.container(key="navlinks"):
            st.page_link(my_orders, label="Track order")
            n = cart.cart_count(user["id"]) if user else 0
            st.page_link(cart_pg, label=f"Cart ({n})" if n else "Cart")
            if user:
                with st.popover(f"Hi, {user['name'].split()[0]}"):
                    st.page_link(profile, label="My profile")
                    st.page_link(my_orders, label="Track order")
                    st.page_link(contact, label="Contact")
                    st.page_link(logout, label="Sign out")
            else:
                with st.container(key="signin"):
                    st.page_link(login, label="Sign in")

nav.run()

if not auth.is_admin():
    st.write("")
    st.divider()
    with st.container(key="footlinks"):
        st.page_link(contact, label="Contact")
        st.page_link(my_orders, label="Track order")
        if not user:
            st.page_link(admin_login, label="Admin sign in")
