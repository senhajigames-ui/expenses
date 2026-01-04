import sys
import os
import logging
from datetime import datetime
from unittest.mock import MagicMock

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_runner")

print("🔹 Starting Standalone Backend Test...")

# 1. Load Secrets
# fast and dirty toml parser to avoid dependency if toml package not executing
def load_secrets():
    secrets = {}
    current_section = None
    try:
        with open(".streamlit/secrets.toml", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1]
                    if current_section not in secrets:
                        secrets[current_section] = {}
                elif "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if current_section:
                        secrets[current_section][key] = value
                    else:
                        secrets[key] = value
        return secrets
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        sys.exit(1)

secrets = load_secrets()
# print(f"DEBUG: Loaded secrets keys: {secrets.keys()}")

# 2. Mock Streamlit
mock_st = MagicMock()
mock_st.secrets = secrets
mock_st.session_state = {}

# Mock basic functions
def mock_write(*args):
    print("ST_WRITE:", *args)

def mock_error(msg):
    print(f"❌ ST_ERROR: {msg}")

def mock_success(msg):
    print(f"✅ ST_SUCCESS: {msg}")

mock_st.write = mock_write
mock_st.error = mock_error
mock_st.success = mock_success
mock_st.info = lambda x: print(f"ℹ️ ST_INFO: {x}")

# Mock cache_data decorator
def mock_cache_data(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

mock_st.cache_data = mock_cache_data

# Inject into sys.modules
sys.modules["streamlit"] = mock_st

# 3. Import Database Modules (Now they use the mock)
try:
    from database.transaction_operations import add_transaction, get_transactions, delete_transaction
    from database.supabase_client import get_supabase_client, get_user_id
except ImportError as e:
    print(f"❌ ImportError: {e}")
    sys.exit(1)

# 4. Run Verification Logic
def run_test():
    user_a = "test_user_A_standalone"
    user_b = "test_user_B_standalone"
    
    # --- SETUP USER A ---
    print(f"\n--- Testing User A: {user_a} ---")
    mock_st.session_state['user_id'] = user_a
    mock_st.session_state['authentication_status'] = True
    mock_st.session_state['username'] = "UserA"
    
    # Verify get_user_id() works
    uid = get_user_id()
    if uid != user_a:
        print(f"❌ User ID Mismatch: got {uid}, expected {user_a}")
        return False
        
    date = datetime.now().strftime("%Y-%m-%d")
    desc = f"Standalone Secret {datetime.now().timestamp()}"
    amount = 50.00
    category = "Test"
    
    # Add Transaction
    print("🔹 Adding transaction...")
    if not add_transaction(date, desc, amount, category):
        print("❌ Failed to add transaction")
        return False
    print("✅ Transaction added")
    
    # Read Data
    print("🔹 Reading data...")
    df = get_transactions()
    if df.empty:
        print("❌ Returned empty dataframe")
        return False
        
    if desc not in df['description'].values:
        print(f"❌ Transaction '{desc}' not found in dataframe")
        print(df)
        return False
        
    txn_id = df[df['description'] == desc].iloc[0]['id']
    print(f"✅ Found transaction ID: {txn_id}")
    
    # --- SECURITY CHECK USER B ---
    print(f"\n--- Testing Security (User B: {user_b}) ---")
    mock_st.session_state['user_id'] = user_b
    
    print("🔹 Reading data as User B...")
    df_b = get_transactions()
    if not df_b.empty and desc in df_b['description'].values:
        print("🚨 CRITICAL SECURITY FAIL: User B sees User A's data!")
        return False
    print("✅ PASS: User B sees nothing")
    
    print(f"🔹 Attempting delete of ID {txn_id} as User B...")
    if delete_transaction(None, txn_id):
        print("🚨 CRITICAL SECURITY FAIL: User B deleted User A's data!")
        return False
    print("✅ PASS: Deletion blocked")
    
    # --- CLEANUP ---
    print(f"\n--- Cleanup (User A) ---")
    mock_st.session_state['user_id'] = user_a
    if delete_transaction(None, txn_id):
        print("✅ Cleanup successful")
    else:
        print("⚠️ Cleanup failed (could not delete test row)")
        
    return True

if __name__ == "__main__":
    try:
        if run_test():
            print("\n🎉 ALL CHECKS PASSED (Standalone)")
        else:
            print("\n❌ CHECKS FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
