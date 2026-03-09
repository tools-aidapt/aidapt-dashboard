import streamlit as st

def init_state():
    if "page" not in st.session_state:
        st.session_state["page"] = "portfolio"
    if "selected_client" not in st.session_state:
        st.session_state["selected_client"] = "All Clients"
