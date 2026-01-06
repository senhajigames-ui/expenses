
import unittest
from unittest.mock import MagicMock, patch
import streamlit as st

# Mock st.secrets before importing supabase_client
# This is a bit tricky because we want the REAL client if possible to test the REAL database.
# But I can't easily get the real secrets in this environment if they are only in .streamlit/secrets.toml
# and running via 'python' might not load them automatically unless I load them manually.

import toml
import os

def load_secrets():
    try:
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            return toml.load(secrets_path)
    except Exception as e:
        print(f"Could not load secrets: {e}")
    return None

def verify_rls():
    secrets = load_secrets()
    if not secrets:
        print("SKIPPING: Could not load secrets.toml")
        return

    # Manually configure st.secrets for the module
    st.secrets = secrets
    
    from database.supabase_client import get_supabase_client
    
    import base64
    import json
    
    try:
        supabase = get_supabase_client()
        
        # 1. Check Key Role (Anon vs Service)
        key = st.secrets["supabase"]["key"]
        try:
            # Simple JWT decode (middle part)
            payload_segment = key.split('.')[1]
            # Add padding if needed
            padded = payload_segment + '=' * (4 - len(payload_segment) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded))
            role = payload.get('role', 'unknown')
            print(f"INFO: API Key Role is '{role}'")
            
            if role == 'service_role':
                print("WARNING: You are using the SERVICE_ROLE key. This bypasses RLS!")
                print("       This test cannot verify RLS enforcement because existing as Admin.")
                return
        except Exception as e:
            print(f"INFO: Could not decode key role: {e}")
        
        # 2. Probe RLS
        print("Attempting to fetch transactions without user_id filter (Anon access)...")
        # Try to get ANY row
        response = supabase.table('transactions').select("*").limit(1).execute()
        
        if response.data and len(response.data) > 0:
            print("CRITICAL: RLS IS LIKELY DISABLED! Data returned for unauthenticated request.")
            print(f"Data sample keys: {list(response.data[0].keys())}")
        else:
            print("SUCCESS: No data returned. RLS appears to be preventing unauthorized access.")
            
    except Exception as e:
        print(f"Error checking RLS: {e}")

if __name__ == "__main__":
    verify_rls()
