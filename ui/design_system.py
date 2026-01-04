"""
Minimal design improvements - typography only.
No color changes, just better font.
"""

def get_inter_font_css() -> str:
    """Add Inter font without changing any colors."""
    return """
    <style>
        /* Import Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Apply Inter font globally */
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        }
        
        /* Improve number readability */
        [data-testid="stMetricValue"] {
            font-variant-numeric: tabular-nums;
        }
    </style>
    """

def apply_typography():
    """Apply just the Inter font."""
    import streamlit as st
    st.markdown(get_inter_font_css(), unsafe_allow_html=True)
