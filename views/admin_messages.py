"""Messages sent through the Contact page."""
import streamlit as st

import admin_ops
import auth
from utils.format import fmt_time

auth.require_admin()
st.title("Messages")

msgs = admin_ops.list_messages()
if not msgs:
    st.info("No messages yet.")
for m in msgs:
    with st.expander(f"{m['name']} · {fmt_time(m['created_at'])}"):
        st.markdown(f"**From:** {m['name']} ({m['email']})")
        st.write(m["message"])
        if st.button("Delete", key=f"dm_{m['id']}"):
            admin_ops.delete_message(m["id"])
            st.rerun()
