"""Manage categories."""
from pathlib import Path

import streamlit as st

import admin_ops
import auth
import catalog

auth.require_admin()
ROOT = Path(__file__).resolve().parent.parent
st.title("Categories")

counts = admin_ops.category_counts()

with st.expander("Add a category", expanded=False):
    with st.form("add_category", clear_on_submit=True):
        name = st.text_input("Name")
        desc = st.text_input("Short description")
        img = st.file_uploader("Image (optional)", type=["png", "jpg", "jpeg", "webp"], key="newcat_img")
        if st.form_submit_button("Add category", type="primary"):
            ok, msg = admin_ops.create_category(name, desc, img.getvalue() if img else None)
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

for c in catalog.categories():
    with st.expander(f"{c['name']} · {counts.get(c['id'], 0)} product(s)"):
        left, right = st.columns([1, 3], gap="large")
        with left:
            path = ROOT / (c["image_path"] or "")
            if c["image_path"] and path.exists():
                st.image(str(path), use_container_width=True)
        with right:
            with st.form(f"cat_{c['id']}"):
                name = st.text_input("Name", value=c["name"], key=f"cn_{c['id']}")
                desc = st.text_input("Short description", value=c["description"] or "", key=f"cd_{c['id']}")
                img = st.file_uploader("Replace image", type=["png", "jpg", "jpeg", "webp"], key=f"ci_{c['id']}")
                if st.form_submit_button("Save category", type="primary"):
                    ok, msg = admin_ops.update_category(c["id"], name, desc, img.getvalue() if img else None)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()
            with st.popover("Delete category"):
                st.write("Products in this category stay in the shop but will have no category.")
                if st.button("Yes, delete", key=f"dc_{c['id']}"):
                    admin_ops.delete_category(c["id"])
                    st.rerun()
