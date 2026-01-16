
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

from database.supabase_client import get_supabase_client

def check_schema():
    print("--- Checking Column Types ---")
    try:
        supabase = get_supabase_client()
        # We can't query information_schema directly with supabase-py usually easily unless we have direct SQL access
        # But we can try to fetch one row and check the type of user_id in Python, 
        # OR just use an RPC if we had one.
        # Actually simplest is to just assume text if we see it as string in python.
        
        res = supabase.table('transactions').select('user_id').limit(1).execute()
        if res.data:
            uid = res.data[0]['user_id']
            print(f"Sample user_id: {uid}")
            print(f"Type in Python: {type(uid)}")
            
            # Simple heuristic
            import uuid
            try:
                uuid.UUID(uid)
                print("Looks like valid UUID format.")
            except:
                print("Does NOT look like UUID format.")
        else:
            print("No data in transactions table.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
