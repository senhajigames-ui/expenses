"""
Authentication Integration
Handles Streamlit Authenticator + Supabase Auth integration.
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from database.supabase_client import set_user_session, clear_user_session, get_supabase_client
import logging

logger = logging.getLogger(__name__)


def load_auth_config():
    """Load authentication configuration from YAML."""
    try:
        with open('auth_config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)
        return config
    except Exception as e:
        logger.error(f"Failed to load auth config: {e}")
        st.error("Authentication configuration error")
        st.stop()


def create_authenticator(config):
    """Create Streamlit authenticator instance."""
    return stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )


def handle_authentication():
    """
    Handle authentication flow.
    
    Returns:
        tuple: (name, authentication_status, username, authenticator)
    """
    # Load config
    config = load_auth_config()
    
    # Create authenticator
    authenticator = create_authenticator(config)
    
    # Render login form (new API stores in session state)
    authenticator.login(location='main')
    
    # Get values from session state (new API)
    name = st.session_state.get('name')
    authentication_status = st.session_state.get('authentication_status')
    username = st.session_state.get('username')
    
    if authentication_status == False:
        st.error('Username/password is incorrect')
        return None, False, None, authenticator
        
    elif authentication_status == None:
        st.warning('Please enter your username and password')
        st.info("**Default credentials:**\n- Username: `demo_user`\n- Password: `DemoPassword123!`")
        return None, None, None, authenticator
        
    else:
        # Authenticated successfully
        # Get or create user in Supabase
        try:
            supabase = get_supabase_client()
            
            # For now, use username as user_id (simplified)
            user_id = username
            email = config['credentials']['usernames'][username]['email']
            
            # Store in session
            set_user_session(user_id, email, name)
            
            return name, True, username, authenticator
            
        except Exception as e:
            logger.error(f"Auth session error: {e}")
            st.error("Session error")
            return None, False, None, authenticator


def render_logout_button(authenticator):
    """Render logout button in sidebar."""
    if st.session_state.get('authentication_status'):
        authenticator.logout('Logout', 'sidebar')
    
    # Clear session on logout
    if not st.session_state.get('authentication_status'):
        clear_user_session()
