import sys
import os
import streamlit as st
import pandas as pd
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from database.transaction_operations import bulk_add_transactions, get_transactions
from logic.csv_import import parse_csv_transactions

# Mock Streamlit secrets availability
if not os.path.exists(".streamlit/secrets.toml"):
    print("❌ No secrets.toml found, cannot run test")
    sys.exit(1)

def test_import_logic():
    print("🚀 Starting Backend Import Test")
    
    # 1. Mock dependencies
    user_id = "test_user_import_fix"
    
    import io
    
    # Mock get_user_id to return our test user
    with patch('database.transaction_operations.get_user_id', return_value=user_id):
        
        # 2. Parse Mock CSV (WealthSimple format)
        print("📂 Parsing Mock CSV...")
        csv_content = """transaction_date,details,amount,type
2024-11-01,Test Transaction,100.00,PURCHASE
2024-11-02,Salary,2000.00,DEPOSIT"""
        
        # Mock uploaded file object
        class MockFile:
            def __init__(self, content, name):
                self.content = content.encode('utf-8')
                self.name = name
                self.current_pos = 0
            
            def read(self):
                return self.content
            
            def seek(self, pos):
                self.current_pos = pos
                
            def __iter__(self):
                return iter(self.content.decode('utf-8').splitlines())
        
        # We need to pass an object that pandas.read_csv accepts.
        # Streamlit passes a file-like object.
        f = io.StringIO(csv_content)
        f.name = "test_wealthsimple.csv"
        
        transactions = parse_csv_transactions(f, {})
            
        print(f"✅ Parsed {len(transactions)} transactions")
        
        if not transactions:
            print("❌ No transactions parsed")
            return
            
        # 3. Simulate Import Tab Logic (Cleaning)
        print("🧹 Cleaning transactions (removing _source_file)...")
        # Add a dummy internal field to ensure our cleaning logic works
        for txn in transactions:
            txn['_source_file'] = 'dummy.csv'
            
        db_transactions = []
        for txn in transactions:
            # THIS IS THE FIX WE WANT TO TEST
            clean_txn = {k: v for k, v in txn.items() if not k.startswith('_') and k != 'is_negative'}
            db_transactions.append(clean_txn)
            
        print(f"✅ Cleaned {len(db_transactions)} transactions")
        # Verify no _underscore keys
        for txn in db_transactions:
            for k in txn.keys():
                if k.startswith('_'):
                    print(f"❌ Failed cleaning: Found key {k}")
                    return

        # 4. Insert to Database
        print("💾 Inserting to Supabase...")
        success = bulk_add_transactions(db_transactions)
        
        if success:
            print("✅ Bulk add returned Success")
        else:
            print("❌ Bulk add failed")
            return
            
        # 5. Verify Insertion
        print("🔍 Verifying data in database...")
        # We need to mock get_user_id inside get_transactions too
        # But we simply query for this user
        from database.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        result = supabase.table('transactions').select('*').eq('user_id', user_id).execute()
        saved_txns = result.data
        
        print(f"📊 Found {len(saved_txns)} transactions in DB for user {user_id}")
        
        if len(saved_txns) == len(db_transactions):
            print("✅ SUCCESS: All transactions saved correctly!")
        else:
            print(f"❌ MISMATCH: Expected {len(db_transactions)}, found {len(saved_txns)}")
            
        # 6. Cleanup
        print("🧹 Cleaning up test data...")
        supabase.table('transactions').delete().eq('user_id', user_id).execute()
        print("✅ Test data deleted")

if __name__ == "__main__":
    test_import_logic()
