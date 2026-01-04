"""
Sidebar - User selection and navigation component.

Handles:
- User management (create, select, delete)
- Tab navigation
- App info and settings
"""

import streamlit as st
from typing import Optional
from database.user_operations import get_all_users, add_user, delete_user


class UserManager:
    """Manage user selection and creation."""
    
    @staticmethod
    def render() -> Optional[str]:
        """
        Render user management UI.
        
        Returns:
            Selected username or None
        """
        st.subheader("👤 User")
        
        users = get_all_users()
        
        if users:
            return UserManager._render_user_selector(users)
        else:
            st.info("👋 No users yet. Create one to get started!")
            return None
    
    @staticmethod
    def _render_user_selector(users: list) -> Optional[str]:
        """Render user dropdown and management."""
        # users is already a list of usernames (strings)
        user_names = users
        
        # Determine default index
        default_index = 0
        if 'current_user' in st.session_state and st.session_state.current_user in user_names:
            default_index = user_names.index(st.session_state.current_user)
        
        # User selection with persistent index
        selected = st.selectbox(
            "Select User",
            options=user_names,
            index=default_index,
            key='user_select',
            help="Choose which user's data to view"
        )
        
        # Delete user option
        if len(users) > 1:
            with st.expander("⚙️ Manage Users"):
                user_to_delete = st.selectbox(
                    "Delete User",
                    options=user_names,
                    key='delete_user_select'
                )
                
                if st.button("🗑️ Delete User", type="secondary", width="stretch"):
                    if st.session_state.get('confirm_delete'):
                        if delete_user(user_to_delete):
                            st.success(f"✅ Deleted user: {user_to_delete}")
                            if selected == user_to_delete:
                                st.session_state.current_user = None
                            st.rerun()
                        else:
                            st.error("Failed to delete user")
                    else:
                        st.warning("⚠️ Click again to confirm deletion")
                        st.session_state.confirm_delete = True
        
        return selected
    
    @staticmethod
    def render_create_user():
        """Render create user form."""
        with st.expander("➕ Add New User"):
            new_name = st.text_input(
                "Name",
                key='new_user_name',
                placeholder="Enter user name",
                max_chars=50
            )
            
            if st.button("Create User", type="primary", width="stretch"):
                if new_name and len(new_name.strip()) >= 2:
                    if add_user(new_name.strip()):
                        st.success(f"✅ Created user: {new_name}")
                        st.session_state.current_user = new_name
                        st.rerun()
                    else:
                        st.error("❌ Failed to create user (may already exist)")
                elif new_name:
                    st.warning("Name must be at least 2 characters")
                else:
                    st.warning("Please enter a name")


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
            **AI Model:** Llama 3.2
            
            #### Features:
            - 📥 Smart CSV Import
            - 🤖 AI Categorization
            - 📊 Visual Analytics
            - 💰 Budget Tracking
            - 🔧 Transaction Management
            
            #### Stats:
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Transactions", f"{transaction_count:,}")
            with col2:
                users = get_all_users()
                st.metric("Users", len(users))


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
            
            st.divider()
            
            st.markdown("### Export")
            st.caption("📊 Export features coming soon!")


def render_sidebar(transaction_count: int = 0) -> Optional[str]:
    """
    Render complete sidebar with all components.
    
    Args:
        transaction_count: Total number of transactions for stats
    
    Returns:
        Selected username or None
    """
    with st.sidebar:
        # App title
        st.title("💰 Expense Tracker")
        
        # User management
        selected_user = UserManager.render()
        UserManager.render_create_user()
        
        st.divider()
        
        # Navigation
        if selected_user:
            TabNavigation.render()
            
            st.divider()
            
            # Settings
            SettingsPanel.render()
        
        # App info
        AppInfo.render(transaction_count)
    
    return selected_user
