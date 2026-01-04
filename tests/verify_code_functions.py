import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock streamlit secrets before importing auth_handler
import streamlit as st
if not hasattr(st, "secrets"):
    st.secrets = {}

from logic.categorization import CategorizationEngine
from auth.auth_handler import load_auth_config

def test_categorization_rules():
    print("🧪 Testing Categorization Rules...")
    engine = CategorizationEngine()
    
    # Test 1: Specific vs Generic (Longest Match First)
    # "UBER EATS" should match "Dining/Restaurants", not "UBER" (Transportation)
    cat, _ = engine.categorize("UBER EATS ORDER 234", 25.0, True)
    if cat == "Dining/Restaurants":
        print("✅ PASS: UBER EATS -> Dining (Correctly prioritized over UBER)")
    else:
        print(f"❌ FAIL: UBER EATS -> {cat} (Should be Dining)")

    # Test 2: New Canadian Rule
    cat, _ = engine.categorize("COSTCO GAS #123", 60.0, True)
    if cat == "Gas/Fuel":
        print("✅ PASS: COSTCO GAS -> Gas/Fuel (Granular rule works)")
    else:
        print(f"❌ FAIL: COSTCO GAS -> {cat} (Should be Gas/Fuel)")

    # Test 3: Amazon Prime (Granular)
    cat, _ = engine.categorize("AMAZON PRIME MEMBER", 12.99, True)
    if cat == "Subscriptions":
        print("✅ PASS: AMAZON PRIME -> Subscriptions (Correctly prioritized over AMAZON)")
    else:
        print(f"❌ FAIL: AMAZON PRIME -> {cat}")

    # Test 4: Fallback (Default)
    cat, _ = engine.categorize("UNKNOWN MYSTERY VENDOR XYZ", 10.0, True)
    if cat == "Other":
        print("✅ PASS: Unknown vendor -> Other (Fallback works, default behavior)")
    else:
        print(f"❌ FAIL: Unknown vendor -> {cat}")

def test_auth_config():
    print("\n🔐 Testing Auth Configuration...")
    try:
        config = load_auth_config()
        if config and 'cookie' in config:
            cookie_name = config['cookie']['name']
            if cookie_name == 'expense_tracker_session_safe':
                 print("✅ PASS: Cookie name updated to 'expense_tracker_session_safe'")
            else:
                 print(f"❌ FAIL: Cookie name is '{cookie_name}' (Expected 'expense_tracker_session_safe')")
        else:
            print("⚠️ Config loaded but cookie section missing")
    except Exception as e:
        print(f"⚠️ Could not load config: {e}")

if __name__ == "__main__":
    test_categorization_rules()
    test_auth_config()
