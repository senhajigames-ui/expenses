"""
Authentication Integration
Handles Streamlit Authenticator + Supabase Auth integration.
Now includes self-registration for friends!
"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import bcrypt
from database.supabase_client import set_user_session, clear_user_session, get_supabase_client
import logging

logger = logging.getLogger(__name__)


def load_auth_config():
    """
    Load authentication configuration.
    Tries st.secrets first (for Streamlit Cloud), falls back to YAML file (local dev).
    """
    try:
        # Try loading from secrets (Streamlit Cloud)
        if "credentials" in st.secrets:
            config = {
                'credentials': dict(st.secrets['credentials']),
                'cookie': dict(st.secrets['cookie']),
                'pre-authorized': dict(st.secrets.get('pre-authorized', {'emails': []}))
            }
            # Convert nested secrets to proper dict format
            if 'usernames' in config['credentials']:
                usernames = {}
                for username, user_data in config['credentials']['usernames'].items():
                    usernames[username] = dict(user_data)
                config['credentials']['usernames'] = usernames
            return config
    except Exception as e:
        logger.warning(f"Could not load from secrets: {e}")
    
    # Fall back to YAML file (local development)
    try:
        with open('auth_config.yaml') as file:
            config = yaml.load(file, Loader=SafeLoader)
        return config
    except Exception as e:
        logger.error(f"Failed to load auth config: {e}")
        st.error("Authentication configuration error. Check secrets or auth_config.yaml")
        st.stop()


def get_users_from_supabase():
    """Load registered users from Supabase."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return {}
        
        result = supabase.table('app_users').select('*').execute()
        users = {}
        for user in result.data:
            users[user['username']] = {
                'email': user['email'],
                'name': user['name'],
                'password': user['password_hash']
            }
        return users
    except Exception as e:
        logger.warning(f"Could not load users from Supabase: {e}")
        return {}


def save_user_to_supabase(username: str, email: str, name: str, password_hash: str) -> bool:
    """Save a new registered user to Supabase."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        data = {
            'username': username,
            'email': email,
            'name': name,
            'password_hash': password_hash
        }
        
        supabase.table('app_users').insert(data).execute()
        return True
    except Exception as e:
        logger.error(f"Failed to save user: {e}")
        return False


def create_authenticator(config):
    """Create Streamlit authenticator instance with merged users."""
    # Merge config users with Supabase users
    supabase_users = get_users_from_supabase()
    
    all_users = config['credentials'].get('usernames', {}).copy()
    all_users.update(supabase_users)
    config['credentials']['usernames'] = all_users
    
    return stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )


def handle_authentication():
    """
    Handle authentication flow with login and registration tabs.
    
    Returns:
        tuple: (name, authentication_status, username, authenticator)
    """
    # Load config
    config = load_auth_config()
    
    # Create authenticator
    authenticator = create_authenticator(config)
    
    # Get current auth status
    authentication_status = st.session_state.get('authentication_status')
    
    # If already logged in, don't show forms
    if authentication_status:
        name = st.session_state.get('name')
        username = st.session_state.get('username')
        
        user_id = username
        email = config['credentials']['usernames'].get(username, {}).get('email', '')
        set_user_session(user_id, email, name)
        
        return name, True, username, authenticator
    
    # Show login/register tabs
    login_tab, register_tab = st.tabs(["🔐 Login", "📝 Register"])
    
    with login_tab:
        authenticator.login(location='main')
        
        name = st.session_state.get('name')
        authentication_status = st.session_state.get('authentication_status')
        username = st.session_state.get('username')
        
        if authentication_status == False:
            st.error('Username/password is incorrect')
            return None, False, None, authenticator
            
        elif authentication_status == None:
            st.info('👋 Enter your credentials to login, or register for a new account!')
            return None, None, None, authenticator
            
        else:
            # Authenticated successfully
            user_id = username
            email = config['credentials']['usernames'].get(username, {}).get('email', '')
            set_user_session(user_id, email, name)
            return name, True, username, authenticator
    
    with register_tab:
        st.markdown("### Create a New Account")
        st.caption("Register to start tracking your expenses!")
        
        with st.form("register_form"):
            new_username = st.text_input("Username", placeholder="e.g., john_doe")
            new_email = st.text_input("Email", placeholder="e.g., john@example.com")
            new_name = st.text_input("Full Name", placeholder="e.g., John Doe")
            new_password = st.text_input("Password", type="password", placeholder="Min 8 characters")
            new_password_confirm = st.text_input("Confirm Password", type="password")
            
            submitted = st.form_submit_button("🚀 Create Account", use_container_width=True)
            
            if submitted:
                # Validation
                errors = []
                
                if not new_username or len(new_username) < 3:
                    errors.append("Username must be at least 3 characters")
                if not new_email or '@' not in new_email:
                    errors.append("Please enter a valid email")
                if not new_name:
                    errors.append("Please enter your name")
                if not new_password or len(new_password) < 8:
                    errors.append("Password must be at least 8 characters")
                if new_password != new_password_confirm:
                    errors.append("Passwords do not match")
                    
                # Check if username exists
                all_users = config['credentials'].get('usernames', {})
                supabase_users = get_users_from_supabase()
                all_users.update(supabase_users)
                
                if new_username.lower() in [u.lower() for u in all_users.keys()]:
                    errors.append("Username already exists")
                
                if errors:
                    for err in errors:
                        st.error(f"❌ {err}")
                else:
                    # Hash password and save
                    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                    
                    if save_user_to_supabase(new_username, new_email, new_name, password_hash):
                        st.success("✅ Account created! Please go to the Login tab to sign in.")
                        st.balloons()
                    else:
                        st.error("❌ Failed to create account. Please try again.")
    
    return None, None, None, authenticator


def render_logout_button(authenticator):
    """Render logout button in sidebar."""
    if st.session_state.get('authentication_status'):
        authenticator.logout('Logout', 'sidebar')
    
    # Clear session on logout
    if not st.session_state.get('authentication_status'):
        clear_user_session()
