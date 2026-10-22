"""Landing page: every flower in one scrollable grid. Also shows Product Details when one is selected."""
import streamlit as st

import catalog
from utils.components import product_card, product_detail

if st.session_state.get("selected_product"):
    product_detail(st.session_state["selected_product"])
    st.stop()

categories = catalog.categories_in_use()
by_name = {c["name"]: c["id"] for c in categories}


def _clear():
    st.session_state["shop_search"] = ""
    st.session_state["shop_sort"] = "Newest"
    st.session_state["shop_instock"] = False
    st.session_state.pop("shop_price", None)
    st.session_state["shop_cat"] = "All"


chosen = st.pills("Category", ["All"] + list(by_name), selection_mode="single", default="All",
                  key="shop_cat", label_visibility="collapsed") or "All"

lo, hi = catalog.price_bounds()
with st.container(key="toolbar"):
    s1, s2, s3 = st.columns([4, 1.6, 1.2])
    search = s1.text_input("Search", key="shop_search", placeholder="Search flowers, e.g. rose or bouquet",
                           label_visibility="collapsed")
    sort = s2.selectbox("Sort by", list(catalog.SORT_OPTIONS), key="shop_sort", label_visibility="collapsed")
    with s3.popover("Filters", use_container_width=True):
        if hi > lo:
            price_min, price_max = st.slider("Price (₹)", lo, hi, (lo, hi), step=1, key="shop_price")
        else:
            price_min, price_max = None, None
        in_stock = st.checkbox("In stock only", key="shop_instock")
        st.button("Clear all", on_click=_clear)

products = catalog.list_products(
    search=search, category_id=by_name.get(chosen), price_min=price_min,
    price_max=price_max, sort=sort, in_stock_only=in_stock)

st.markdown(f'<p class="count-line">{len(products)} flower{"s" if len(products) != 1 else ""}</p>',
            unsafe_allow_html=True)

if not products:
    st.info("No flowers match your search.")
    st.button("Clear filters", on_click=_clear, key="clear_empty")
    st.stop()

for start in range(0, len(products), 4):
    cols = st.columns(4, gap="large")
    for col, p in zip(cols, products[start:start + 4]):
        with col:
            product_card(p, "shop")
    st.write("")
