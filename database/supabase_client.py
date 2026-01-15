"""
Supabase Database Manager
Handles connection and provides client for all database operations.
"""

import streamlit as st
from supabase import create_client, Client
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@st.cache_resource
def get_supabase_client() -> Client:
    """
    Get Supabase client from Streamlit secrets.
    
    Returns:
        Client: Supabase client instance
        
    Raises:
        ValueError: If credentials are missing
    """
    try:
        url = st.secrets["supabase"]["url"]
        
        # Prefer Service Role Key for backend operations
        key = st.secrets["supabase"].get("service_role_key", st.secrets["supabase"]["key"])
        
        if not url or not key:
            raise ValueError("Supabase credentials not configured")
            
        return create_client(url, key)
        
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {e}")
        raise


def get_user_id() -> Optional[str]:
    """
    Get current authenticated user's ID from session.
    
    Returns:
        str: User ID if authenticated, None otherwise
    """
    return st.session_state.get('user_id')


def set_user_session(user_id: str, email: str, name: str):
    """
    Store user session information.
    
    Args:
        user_id: Unique user identifier
        email: User email
        name: User display name
    """
    st.session_state.user_id = user_id
    st.session_state.user_email = email
    st.session_state.user_name = name


def clear_user_session():
    """Clear user session on logout."""
    if 'user_id' in st.session_state:
        del st.session_state.user_id
    if 'user_email' in st.session_state:
        del st.session_state.user_email
    if 'user_name' in st.session_state:
        del st.session_state.user_name
