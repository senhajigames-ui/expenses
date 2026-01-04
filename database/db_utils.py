"""
Shared database utilities.
Common functions used across database operation modules.
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)


def should_use_supabase() -> bool:
    """
    Check if Supabase should be used for data operations.
    
    Returns True if:
    1. Supabase is configured in secrets
    2. User is authenticated (Supabase requires user_id)
    """
    try:
        if "supabase" in st.secrets and st.session_state.get('authentication_status'):
            return True
    except (FileNotFoundError, AttributeError):
        pass
    return False


def get_cache_key_suffix() -> str:
    """
    Get a cache key suffix for user-specific caching.
    
    This ensures cached data is isolated per user.
    """
    user_id = st.session_state.get('user_id', 'anonymous')
    return f"_{user_id}"
