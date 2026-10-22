"""Reusable Streamlit pieces: product card and product detail view."""
from pathlib import Path

import streamlit as st

import auth
import cart
import catalog
from utils.format import money
from utils.styles import stock_badge

ROOT = Path(__file__).resolve().parent.parent


def show_image(rel_path):
    path = ROOT / (rel_path or "")
    if rel_path and path.exists():
        st.image(str(path), use_container_width=True)


def open_product(product_id):
    st.session_state["selected_product"] = product_id
    st.switch_page("views/shop.py")


def _quick_add(product_id):
    user = auth.current_user()
    if not user:
        st.toast("Please sign in to add flowers to your cart.")
        return
    ok, msg = cart.add_to_cart(user["id"], product_id, 1)
    st.toast(msg)


def product_card(p, key_prefix):
    with st.container(key=f"card_{key_prefix}_{p['id']}"):
        show_image(p.get("image_path"))
        st.markdown(f'<p class="pname">{p["name"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<span class="pprice">{money(p["price"])}</span>{stock_badge(p["stock"])}',
                    unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        if b1.button("View", key=f"{key_prefix}_v{p['id']}", use_container_width=True):
            open_product(p["id"])
        if p["stock"] <= 0:
            b2.button("Sold out", key=f"{key_prefix}_a{p['id']}", disabled=True, use_container_width=True)
        else:
            b2.button("Add to cart", key=f"{key_prefix}_a{p['id']}", type="primary", use_container_width=True,
                      on_click=_quick_add, args=(p["id"],))


def product_detail(product_id):
    p = catalog.get_product(product_id)
    if st.button("← Back to shop"):
        st.session_state["selected_product"] = None
        st.rerun()
    if not p:
        st.error("This flower is no longer available.")
        return

    left, right = st.columns([1, 1], gap="large")
    with left:
        images = catalog.product_images(product_id)
        if images:
            show_image(images[0]["image_path"])
            if len(images) > 1:
                for col, img in zip(st.columns(len(images) - 1), images[1:]):
                    with col:
                        show_image(img["image_path"])
    with right:
        st.markdown(f"## {p['name']}")
        kind = "Bouquet / combo" if p["is_bundle"] else "Single flower"
        st.caption(f"{p['category_name'] or 'Uncategorised'} · {kind}")
        st.markdown(f'<span class="pprice" style="font-size:1.6rem">{money(p["price"])}</span> '
                    f'{stock_badge(p["stock"])}', unsafe_allow_html=True)
        st.write(p["description"] or "")

        user = auth.current_user()
        in_cart = cart.cart_quantity(user["id"], p["id"]) if user else 0
        available = p["stock"] - in_cart
        if p["stock"] <= 0:
            st.button("Out of stock", disabled=True)
        else:
            qty = st.number_input("Quantity", min_value=1, max_value=max(p["stock"], 1),
                                  value=1, step=1, key=f"qty_{p['id']}")
            if in_cart:
                st.caption(f"{in_cart} already in your cart.")
            if st.button("Add to cart", type="primary", disabled=available <= 0):
                if not user:
                    st.info("Sign in to add flowers to your cart.")
                    st.page_link("views/login.py", label="Go to sign in")
                else:
                    ok, msg = cart.add_to_cart(user["id"], p["id"], int(qty))
                    (st.success if ok else st.error)(msg)
            if available <= 0:
                st.caption("You have all available stock in your cart.")

    related = catalog.related_products(p)
    if related:
        st.write("")
        st.subheader("You might also like")
        for col, r in zip(st.columns(3), related):
            with col:
                product_card(r, "rel")


def address_fields(prefix, defaults=None):
    """Draw the delivery address inputs and return their values as a dict.
    prefix keeps widget keys unique when the form appears more than once."""
    from utils.validation import INDIAN_STATES
    d = defaults or {}
    c1, c2 = st.columns(2)
    name = c1.text_input("Recipient name", value=d.get("recipient_name", ""), key=f"{prefix}_name")
    phone = c2.text_input("Phone number", value=d.get("phone", ""), key=f"{prefix}_phone",
                          placeholder="10-digit mobile number")
    house = st.text_input("House / flat no.", value=d.get("house_flat", ""), key=f"{prefix}_house")
    street = st.text_input("Street", value=d.get("street", ""), key=f"{prefix}_street")
    area = st.text_input("Area / landmark", value=d.get("area_landmark", ""), key=f"{prefix}_area")
    c3, c4, c5 = st.columns(3)
    city = c3.text_input("City", value=d.get("city", ""), key=f"{prefix}_city")
    idx = INDIAN_STATES.index(d["state"]) if d.get("state") in INDIAN_STATES else None
    state = c4.selectbox("State", INDIAN_STATES, index=idx, placeholder="Select state", key=f"{prefix}_state")
    pin = c5.text_input("PIN code", value=d.get("pin_code", ""), max_chars=6, key=f"{prefix}_pin")
    return {"recipient_name": name, "phone": phone, "house_flat": house, "street": street,
            "area_landmark": area, "city": city, "state": state or "", "pin_code": pin}
