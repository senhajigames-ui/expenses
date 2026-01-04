"""
Sidebar - Navigation and app info component.

Handles:
- Tab navigation
- App info and settings
"""

import streamlit as st
from typing import Optional


class TabNavigation:
    """Handle tab navigation."""
    
    TAB_CONFIG = [
        {"name": "📥 Import", "icon": "📥", "index": 0},
        {"name": "📊 Overview", "icon": "📊", "index": 1},
        {"name": "📈 Analysis", "icon": "📈", "index": 2},
        {"name": "🔧 Manage", "icon": "🔧", "index": 3},
    ]
    
    @staticmethod
    def render():
        """Render navigation buttons."""
        st.subheader("📊 Navigation")
        
        current_tab = st.session_state.get('active_tab', 0)
        
        for tab in TabNavigation.TAB_CONFIG:
            is_active = current_tab == tab['index']
            
            button_type = "primary" if is_active else "secondary"
            
            if st.button(
                tab['name'],
                key=f"nav_btn_{tab['index']}",
                width="stretch",
                type=button_type
            ):
                if not is_active:
                    st.session_state.active_tab = tab['index']
                    # Update query param for persistence
                    st.query_params['tab'] = str(tab['index'])
                    st.rerun()


class AppInfo:
    """Display app information and stats."""
    
    @staticmethod
    def render(transaction_count: int = 0):
        """Render app info section."""
        st.divider()
        
        with st.expander("ℹ️ About"):
            st.markdown("""
            ### 💰 Expense Tracker
            
            **Version:** 2.0  
            **Backend:** Supabase
            
            #### Features:
            - 📥 Smart CSV Import
            - 🤖 AI Categorization
            - 📊 Visual Analytics
            - 💰 Budget Tracking
            - 🔧 Transaction Management
            - 🔒 Secure Authentication
            """)
            
            st.metric("Transactions", f"{transaction_count:,}")


class SettingsPanel:
    """App settings and preferences."""
    
    @staticmethod
    def render():
        """Render settings panel."""
        with st.expander("⚙️ Settings"):
            st.markdown("### Display Settings")
            
            # Theme (Streamlit handles this natively)
            st.caption("💡 Use Streamlit menu (☰) to change theme")
            
            st.divider()
            
            st.markdown("### Data Management")
            
            if st.button("🔄 Refresh Data", width="stretch"):
                st.rerun()
            
            if st.button("🗑️ Clear Cache", width="stretch"):
                st.cache_data.clear()
                st.success("Cache cleared!")


def render_sidebar(transaction_count: int = 0) -> Optional[str]:
    """
    Render complete sidebar with all components.
    
    Args:
        transaction_count: Total number of transactions for stats
    
    Returns:
        Username from session state (set by authentication)
    """
    with st.sidebar:
        # App title
        st.title("💰 Expense Tracker")
        
        # Get username from auth session
        username = st.session_state.get('username')
        
        st.divider()
        
        # Navigation (only show if authenticated)
        if username:
            TabNavigation.render()
            
            st.divider()
            
            # Settings
            SettingsPanel.render()
        
        # App info
        AppInfo.render(transaction_count)
    
    return username
