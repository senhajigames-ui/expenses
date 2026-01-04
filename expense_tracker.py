"""
Expense Tracker - Main Application
A Streamlit-based expense tracking app with Supabase backend.

Architecture:
- ui/          - All UI components (tabs, sidebar, widgets)
- logic/       - Business logic (categorization, analytics)
- database/    - Data access layer (Supabase operations)
- auth/        - Authentication (login, register)
- config.py    - Configuration constants
"""

import streamlit as st
import pandas as pd

# Authentication
from auth.auth_handler import handle_authentication

# Database operations (routes to Supabase when authenticated)
from database.transaction_operations import get_transactions

# UI components
from ui.sidebar import render_sidebar
from ui.tab_import import render_import_tab
from ui.tab_overview import render_overview_tab
from ui.tab_analysis import render_analysis_tab
from ui.tab_manage import render_manage_tab


def initialize_app() -> None:
    """Initialize application state."""
    st.set_page_config(
        page_title="Expense Tracker",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def load_transactions() -> pd.DataFrame:
    """Load all transactions from Supabase."""
    try:
        # get_transactions routes to Supabase when authenticated
        df = get_transactions(None)  # conn not needed for Supabase
        
        if df.empty:
            return df
        
        # Normalize date column to datetime.date
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Ensure 'month' column exists (YYYY-MM) for filters and charts
        if 'month' not in df.columns or df['month'].isna().all():
            df['month'] = pd.to_datetime(df['date']).astype('datetime64[ns]').dt.strftime('%Y-%m')
        
        return df
    
    except Exception as e:
        st.error(f"Error loading transactions: {e}")
        return pd.DataFrame()


def render_active_tab(all_transactions: pd.DataFrame):
    """Route to active tab renderer."""
    active_tab = st.session_state.get('active_tab', 0)
    
    # Pass None for conn - Supabase operations don't need it
    if active_tab == 0:
        render_import_tab(None, all_transactions)
    elif active_tab == 1:
        render_overview_tab(None, all_transactions)
    elif active_tab == 2:
        render_analysis_tab(None, all_transactions)
    elif active_tab == 3:
        render_manage_tab(None, all_transactions)
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
    
    # Restore tab from query params
    query_params = st.query_params
    if 'tab' in query_params and 'active_tab' not in st.session_state:
        try:
            st.session_state.active_tab = int(query_params['tab'])
        except (ValueError, TypeError):
            st.session_state.active_tab = 0
    
    # Load transactions for authenticated user
    all_transactions = load_transactions()
    transaction_count = len(all_transactions)
    
    # Render sidebar with navigation
    render_sidebar(transaction_count)
    
    # Update query params for tab persistence
    st.query_params['tab'] = str(st.session_state.get('active_tab', 0))
    
    # Render active tab content
    render_active_tab(all_transactions)


if __name__ == "__main__":
    main()