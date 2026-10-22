"""Cart: change quantities, remove items, see subtotal and total."""
import streamlit as st

import auth
import cart
from utils.components import show_image
from utils.format import money
from utils.styles import stock_badge

auth.require_login()
user = auth.current_user()

st.title("Your cart")
items = cart.get_cart(user["id"])

if not items:
    st.info("Your cart is empty. Find something lovely in the shop.")
    st.page_link("views/shop.py", label="Browse flowers")
    st.stop()


def _update(product_id):
    cart.set_quantity(user["id"], product_id, int(st.session_state[f"cartqty_{product_id}"]))


def _remove(product_id):
    cart.remove_item(user["id"], product_id)


left, right = st.columns([2, 1], gap="large")

with left:
    for it in items:
        c_img, c_info, c_qty, c_total = st.columns([1, 2.2, 1.4, 1.2], vertical_alignment="center")
        with c_img:
            show_image(it["image_path"])
        with c_info:
            st.markdown(f'<p class="pname">{it["name"]}</p>', unsafe_allow_html=True)
            st.markdown(f'{money(it["price"])} each {stock_badge(it["stock"])}', unsafe_allow_html=True)
        with c_qty:
            if it["stock"] <= 0 or not it["is_active"]:
                st.markdown("**Out of stock**")
            else:
                cap = it["stock"]
                st.number_input("Quantity", min_value=1, max_value=cap, value=min(it["quantity"], cap),
                                step=1, key=f"cartqty_{it['product_id']}", on_change=_update,
                                args=(it["product_id"],))
        with c_total:
            st.markdown(f"**{money(it['price'] * it['quantity'])}**")
            st.button("Remove", key=f"rm_{it['product_id']}", on_click=_remove, args=(it["product_id"],))
        st.divider()

with right:
    t = cart.totals(items)
    st.subheader("Order summary")
    st.markdown(f"Subtotal: **{money(t['subtotal'])}**")
    st.markdown("Delivery: **Free**" if t["delivery_fee"] == 0 else f"Delivery: **{money(t['delivery_fee'])}**")
    st.markdown(f"### Total: {money(t['total'])}")
    problems = cart.cart_problems(items)
    unavailable = cart.has_unavailable(items)
    for msg in problems:
        st.error(msg)
    if unavailable:
        st.caption("Remove out-of-stock items to continue.")
    if st.button("Proceed to checkout", type="primary", disabled=bool(problems) or unavailable,
                 use_container_width=True):
        st.session_state["checkout_step"] = "address"
        st.switch_page("views/checkout.py")
