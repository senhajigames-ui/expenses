"""
Expense Tracker - Main Application
A Streamlit-based expense tracking app with local AI categorization.

Architecture:
- ui/          - All UI components (tabs, sidebar, widgets)
- logic/       - Business logic (categorization, analytics)
- database/    - Data access layer (CRUD operations)
- utils/       - Helper functions (date, validation)
- config.py    - Configuration constants
"""

import streamlit as st
import pandas as pd
import sqlite3

# Authentication
from auth.auth_handler import handle_authentication, load_auth_config, create_authenticator

# Database initialization
from database.db_manager import init_users_db, init_db
from database.transaction_operations import get_transactions
from database.supabase_client import get_user_id

# UI components
from ui.sidebar import render_sidebar
from ui.tab_import import render_import_tab
from ui.tab_overview import render_overview_tab
from ui.tab_analysis import render_analysis_tab
from ui.tab_manage import render_manage_tab


def initialize_app() -> None:
    """Initialize application state and databases."""
    # Page config
    st.set_page_config(
        page_title="Expense Tracker",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize central users database only
    init_users_db()


def get_user_connection(user_name: str) -> sqlite3.Connection:
    """
    Get and initialize database connection for the specific user.
    
    Args:
        user_name: The username string
    
    Returns:
        sqlite3.Connection: Initialized connection object
    """
    # Initialize or open the user's expense DB
    conn = init_db(user_name)
    return conn


def load_transactions(conn: sqlite3.Connection) -> pd.DataFrame:
    """Load all transactions from database."""
    try:
        # get_transactions returns a DataFrame
        df = get_transactions(conn)
        
        if df.empty:
            return df
        
        # Normalize date column to datetime.date
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Ensure 'month' column exists (YYYY-MM) for filters and charts
        if 'month' not in df.columns or df['month'].isna().all():
            df['month'] = pd.to_datetime(df['date']).astype('datetime64[ns]').dt.strftime('%Y-%m')
        
        return df
    
    except sqlite3.Error as e:
        st.error(f"Database error loading transactions: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Unexpected error loading transactions: {e}")
        return pd.DataFrame()



def render_active_tab(conn: sqlite3.Connection, all_transactions: pd.DataFrame):
    """Route to active tab renderer."""
    active_tab = st.session_state.get('active_tab', 0)
    
    if active_tab == 0:
        render_import_tab(conn, all_transactions)
    elif active_tab == 1:
        render_overview_tab(conn, all_transactions)
    elif active_tab == 2:
        render_analysis_tab(conn, all_transactions)
    elif active_tab == 3:
        render_manage_tab(conn, all_transactions)
    else:
        st.error(f"Invalid tab: {active_tab}")


def main():
    """Main application entry point."""
    # Initialize app configuration
    initialize_app()
    
    # Handle authentication FIRST
    name, authentication_status, username, authenticator = handle_authentication()
    
    # Stop if not authenticated
    if not authentication_status:
        st.stop()
    
    # Show logout in sidebar
    authenticator.logout('Logout', 'sidebar')
    
    # Welcome message
    st.sidebar.success(f'Welcome **{name}**!')
    
    # Continue with app (now using Supabase for authenticated user)
    
    # Get query parameters for persistence across refreshes
    query_params = st.query_params
    
    # Restore user from query params if available
    if 'user' in query_params and 'current_user' not in st.session_state:
        st.session_state.current_user = query_params['user']
    
    # Restore tab from query params if available
    if 'tab' in query_params and 'active_tab' not in st.session_state:
        try:
            st.session_state.active_tab = int(query_params['tab'])
        except (ValueError, TypeError):
            st.session_state.active_tab = 0
            
    # Determine user (from session or query params)
    current_user = st.session_state.get('current_user')
    if not current_user and 'user' in query_params:
        current_user = query_params['user']
        st.session_state.current_user = current_user
        
    # Load transactions early if user is selected
    transaction_count = 0
    all_transactions = pd.DataFrame()
    conn = None
    
    if current_user:
        try:
            conn = get_user_connection(current_user)
            all_transactions = load_transactions(conn)
            transaction_count = len(all_transactions)
        except Exception as e:
            st.error(f"Error loading user data: {e}")
    
    # Render sidebar with accurate count
    selected_user = render_sidebar(transaction_count)
    
    # Handle user switch
    if selected_user != current_user:
        st.session_state.current_user = selected_user
        st.rerun()
    
    # Update query params when user changes
    if selected_user:
        st.query_params['user'] = selected_user
        st.query_params['tab'] = str(st.session_state.get('active_tab', 0))
    
    # Show welcome if no user selected
    if not selected_user:
        st.title("👋 Welcome to Expense Tracker!")
        st.markdown("""
        ### Get Started:
        1. Create a user in the sidebar ←
        2. Import your bank transactions (CSV)
        3. Let AI categorize your spending
        4. Analyze your finances with visual insights
        
        ### Features:
        - 🤖 **Smart AI Categorization** - Automatic expense categorization
        - 📊 **Visual Analytics** - Interactive charts and dashboards
        - 💰 **Budget Tracking** - Set and monitor spending goals
        - 🏪 **Merchant Rules** - Learn from your edits
        - 📥 **Multi-Bank Support** - RBC, WealthSimple, and more
        """)
        if conn:
            conn.close()
        return
    
    # Render active tab content
    if conn and not all_transactions.empty:
        render_active_tab(conn, all_transactions)
    elif conn:
        render_active_tab(conn, pd.DataFrame())
        
    # Close connection cleanly
    if conn:
        conn.close()


if __name__ == "__main__":
    main()