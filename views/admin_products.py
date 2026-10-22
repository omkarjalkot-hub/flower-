"""Manage products: add, edit, stock, images, delete."""
from pathlib import Path

import streamlit as st

import admin_ops
import auth
import catalog
from utils.format import money

auth.require_admin()
ROOT = Path(__file__).resolve().parent.parent
st.title("Products")

cats = catalog.categories()
cat_ids = [None] + [c["id"] for c in cats]
cat_names = {None: "No category", **{c["id"]: c["name"] for c in cats}}


def _fields(prefix, p=None):
    p = p or {}
    c1, c2 = st.columns([2, 1])
    name = c1.text_input("Name", value=p.get("name", ""), key=f"{prefix}_name")
    cat = c2.selectbox("Category", cat_ids, format_func=cat_names.get,
                       index=cat_ids.index(p.get("category_id")) if p.get("category_id") in cat_ids else 0,
                       key=f"{prefix}_cat")
    desc = st.text_area("Description", value=p.get("description") or "", key=f"{prefix}_desc")
    d1, d2 = st.columns(2)
    price = d1.number_input("Price (₹)", min_value=0.0, value=float(p.get("price", 0)), step=10.0, key=f"{prefix}_price")
    stock = d2.number_input("Stock", min_value=0, value=int(p.get("stock", 0)), step=1, key=f"{prefix}_stock")
    e1, e2, e3 = st.columns(3)
    bundle = e1.checkbox("Bouquet / combo", value=bool(p.get("is_bundle")), key=f"{prefix}_bundle")
    featured = bool(p.get("is_featured"))
    active = e3.checkbox("Visible in shop", value=bool(p.get("is_active", 1)), key=f"{prefix}_active")
    return {"name": name, "category_id": cat, "description": desc, "price": price, "stock": int(stock),
            "is_bundle": bundle, "is_featured": featured, "is_active": active}


tab_all, tab_add = st.tabs(["All products", "Add product"])

with tab_add:
    with st.form("add_product", clear_on_submit=False):
        data = _fields("new")
        photos = st.file_uploader("Photos (PNG, JPG or WEBP)", type=["png", "jpg", "jpeg", "webp"],
                                  accept_multiple_files=True, key="new_photos")
        if st.form_submit_button("Add product", type="primary"):
            ok, res = admin_ops.create_product(data)
            if not ok:
                for e in res:
                    st.error(e)
            else:
                if photos:
                    added, errs = admin_ops.add_images(res, [(f.name, f.getvalue()) for f in photos])
                    for e in errs:
                        st.warning(e)
                st.success(f"{data['name']} added.")

with tab_all:
    search = st.text_input("Search products", key="adm_psearch")
    for p in admin_ops.list_products_admin(search):
        flags = ("" if p["is_active"] else " · Hidden") + (" · Out of stock" if p["stock"] <= 0 else "")
        with st.expander(f"{p['name']} · {money(p['price'])} · {p['stock']} in stock{flags}"):
            with st.form(f"edit_{p['id']}"):
                data = _fields(f"e{p['id']}", p)
                if st.form_submit_button("Save changes", type="primary"):
                    ok, res = admin_ops.update_product(p["id"], data)
                    if ok:
                        st.success("Saved.")
                        st.rerun()
                    else:
                        for e in res:
                            st.error(e)

            st.markdown("**Photos**")
            images = admin_ops.product_images(p["id"])
            if not images:
                st.caption("No photos yet.")
            for col, img in zip(st.columns(max(len(images), 1)), images):
                with col:
                    path = ROOT / img["image_path"]
                    if path.exists():
                        st.image(str(path), use_container_width=True)
                    tag = ("Main" if img["is_primary"] else "") + (" · Placeholder" if img["is_placeholder"] else "")
                    if tag.strip(" ·"):
                        st.caption(tag.strip(" ·"))
                    if not img["is_primary"]:
                        if st.button("Make main", key=f"mp_{img['id']}"):
                            admin_ops.set_primary_image(p["id"], img["id"])
                            st.rerun()
                    if st.button("Remove", key=f"di_{img['id']}"):
                        admin_ops.delete_image(p["id"], img["id"])
                        st.rerun()

            n = st.session_state.get(f"upn_{p['id']}", 0)
            files = st.file_uploader("Add photos", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True,
                                     key=f"up_{p['id']}_{n}")
            if files and st.button("Upload photos", key=f"upb_{p['id']}"):
                added, errs = admin_ops.add_images(p["id"], [(f.name, f.getvalue()) for f in files])
                for e in errs:
                    st.warning(e)
                st.session_state[f"upn_{p['id']}"] = n + 1
                if added:
                    st.rerun()

            with st.popover("Delete product"):
                st.write("Delete this product for good? Past orders keep their details.")
                if st.button("Yes, delete", key=f"dp_{p['id']}"):
                    admin_ops.delete_product(p["id"])
                    st.rerun()
