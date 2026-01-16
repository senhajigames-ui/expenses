
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock streamlit secrets since we are running as script
import streamlit as st
import toml

try:
    with open(".streamlit/secrets.toml", "r") as f:
        secrets = toml.load(f)
        st.secrets = secrets
except Exception as e:
    print(f"Could not load secrets: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database.supabase_client import get_supabase_client

def test_registration():
    print("--- Starting Registration Debug ---")
    
    # 1. Check Client Connection
    try:
        supabase = get_supabase_client()
        print("✅ Supabase client initialized")
    except Exception as e:
        print(f"❌ Failed to init client: {e}")
        return

    # 2. Check Table Access (Read)
    print("\n--- Testing Read Permission (app_users) ---")
    try:
        # Try to select count
        res = supabase.table('app_users').select("count", count="exact").execute()
        print(f"✅ Read access confirmed. User count: {res.count}")
    except Exception as e:
        print(f"❌ Read access FAILED: {e}")
        print("Possible causes: Table doesn't exist, or RLS denies SELECT to anon/service role.")

    # 3. Check Write Permission
    print("\n--- Testing Write Permission (app_users) ---")
    import time
    test_username = f"debug_user_{int(time.time())}"
    data = {
        'username': test_username,
        'email': f"{test_username}@example.com",
        'name': "Debug User",
        'password_hash': "dummy_hash_for_testing"
    }
    
    try:
        # res = supabase.table('app_users').insert(data).execute()
        # Update to test RPC
        print("Testing RPC 'register_user'...")
        res = supabase.rpc('register_user', data).execute()
        
        if res.data is True:
             print(f"✅ RPC Success. User '{test_username}' created.")
        else:
             print(f"❌ RPC returned False.")
        
        # Cleanup
        print("Cleaning up test user...")
        # We still need direct delete access for cleanup?
        # Actually, we might not have DELETE access if we locked it down. 
        # But for this test, we are likely using the service_role key in secrets.toml?
        # If using SERVICE_ROLE key, RLS is bypassed, so DELETE should work.
        # If using ANON key, DELETE will fail (good!).
        try:
            supabase.table('app_users').delete().eq('username', test_username).execute()
            print("✅ Cleanup successful (Service Role used)")
        except Exception as e:
            print(f"⚠️ Cleanup failed (Expected if using Anon Key): {e}")
        
    except Exception as e:
        print(f"❌ RPC Call FAILED: {e}")

if __name__ == "__main__":
    test_registration()
