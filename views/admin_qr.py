"""Upload or replace the payment QR code shown at checkout."""
import secrets
from pathlib import Path

import streamlit as st

import admin_ops
import auth
import db
from utils.images import save_upload

auth.require_admin()
ROOT = Path(__file__).resolve().parent.parent
st.title("Payment QR")
st.write("Customers see this QR at checkout, pay by scanning it, then enter their transaction ID.")

current = db.get_setting("qr_image_path", "")
if current and (ROOT / current).exists():
    st.image(str(ROOT / current), width=300, caption="Current QR")
    if "placeholder" in current:
        st.warning("This is a demo image and cannot be scanned. Upload your real QR below.")
else:
    st.warning("No QR is set. Customers cannot pay until you upload one.")

with st.form("qr_form", clear_on_submit=True):
    up = st.file_uploader("New QR image (PNG, JPG or WEBP)", type=["png", "jpg", "jpeg", "webp"])
    if st.form_submit_button("Save QR", type="primary"):
        if not up:
            st.error("Choose an image first.")
        else:
            try:
                rel = save_upload(up.getvalue(), "assets/qr", f"payment-qr-{secrets.token_hex(4)}",
                                  fmt="PNG", max_side=1000)
            except ValueError as e:
                st.error(str(e))
            else:
                db.set_setting("qr_image_path", rel)
                admin_ops._remove_file(current)
                st.success("QR updated.")
                st.rerun()
