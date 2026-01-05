"""
Authentication UI Components
Helpers for rendering polished, centered authentication interfaces.
"""

import streamlit as st

def render_centered_auth_container():
    """
    Creates a centered container for authentication forms.
    Returns:
        width-constrained container
    """
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        return st.container()

def render_auth_header(title: str, subtitle: str = None):
    """
    Renders a standard auth header.
    """
    st.markdown(f"<h2 style='text-align: center;'>{title}</h2>", unsafe_allow_html=True)
    if subtitle:
        st.markdown(f"<p style='text-align: center; color: gray;'>{subtitle}</p>", unsafe_allow_html=True)
    st.divider()
