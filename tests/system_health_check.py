
import unittest
import pandas as pd
import io
from unittest.mock import MagicMock, patch

# Import core modules
from logic.csv_import import parse_csv_transactions
from database.transaction_operations import add_transaction, get_transactions, update_transaction, delete_transaction
from database.supabase_client import get_supabase_client
from auth.auth_handler import save_user_to_supabase

class SystemHealthCheck(unittest.TestCase):
    
    def setUp(self):
        # Universal Mock for Supabase to prevent polluting Prod DB
        self.mock_supabase = MagicMock()
        self.mock_user_id = "test_system_health_user"
        
    @patch('database.transaction_operations.get_supabase_client')
    @patch('database.transaction_operations.get_user_id')
    def test_end_to_end_transaction_flow(self, mock_get_uid, mock_get_client):
        """
        Verify the full lifecycle of a transaction:
        Import -> Add -> Read -> Update -> Delete
        """
        print("\n🔹 Testing Transaction Lifecycle (CRUD)...")
        
        # Setup Mocks
        mock_get_uid.return_value = self.mock_user_id
        mock_get_client.return_value = self.mock_supabase
        
        
        # Setup Universal Chainable Mock
        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query  # Allow multiple .eq().eq()
        mock_query.gte.return_value = mock_query
        mock_query.lte.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.range.return_value = mock_query  # For pagination
        
        # Link table operations to this query mock
        mock_table = MagicMock()
        mock_table.select.return_value = mock_query
        mock_table.insert.return_value = mock_query
        mock_table.update.return_value = mock_query
        mock_table.delete.return_value = mock_query
        
        self.mock_supabase.table.return_value = mock_table
        
        # 1. Simulate CSV Import
        csv_content = "Date,Description,Amount\n2024-01-15,WALMART STORE #123,-50.25"
        file_obj = io.BytesIO(csv_content.encode('utf-8'))
        file_obj.name = "test_bank.csv"
        
        # Test Parsing - Returns List of Dicts now
        txns_list = parse_csv_transactions(file_obj)
        self.assertTrue(len(txns_list) > 0, "CSV Parsing failed")
        
        row = txns_list[0]
        
        # 2. Add to Database
        # Configure execute() for INSERT
        mock_query.execute.return_value.data = [{'id': 999}]
        
        success = add_transaction(
            None, 
            row['date'], 
            row['description'], 
            row['amount'], 
            row['transaction_type'], 
            row['category']
        )
        self.assertTrue(success, "Add Transaction failed")
        
        # 3. Read from Database
        # Configure execute() for SELECT
        mock_query.execute.return_value.data = [{
            'id': 999,
            'date': '2024-01-15',
            'description': 'WALMART STORE #123',
            'amount': -50.25,
            'category': 'Groceries', 
            'transaction_type': 'expense',
            'user_id': self.mock_user_id
        }]
        
        txns = get_transactions()
        self.assertFalse(txns.empty, "Get Transactions failed")
        self.assertEqual(txns.iloc[0]['id'], 999)
        
        # 4. Update Transaction
        self.mock_supabase.table().update().eq().execute().data = [{'id': 999}]
        
        update_success = update_transaction(999, {'category': 'Shopping/Retail'})
        self.assertTrue(update_success, "Update Transaction failed")
        
        # 5. Delete Transaction
        self.mock_supabase.table().delete().eq().eq().execute().data = [{'id': 999}]
        
        delete_success = delete_transaction(None, 999)
        self.assertTrue(delete_success, "Delete Transaction failed")
        
        print("✅ Transaction Lifecycle Checks Passed")

    @patch('database.transaction_operations.get_supabase_client')
    @patch('database.transaction_operations.get_user_id')
    def test_csv_format_compatibility(self, mock_get_uid, mock_get_client):
        """Verify parsing of different bank formats."""
        print("\n🔹 Testing CSV Compatibility...")
        
        formats = [
            ("RBC", "Transaction Date,Description,CAD$\n1/15/2024,UBER TRIP,-25.00"),
            ("Generic", "Date,Description,Amount\n2024-01-15,Generic Expense,-50.00"),
        ]
        
        for bank, content in formats:
            file_obj = io.BytesIO(content.encode('utf-8'))
            file_obj.name = f"{bank}.csv"
            # Updated to use new parser
            txns = parse_csv_transactions(file_obj)
            self.assertTrue(len(txns) > 0, f"Failed to parse {bank} format")
            print(f"  - {bank}: OK ({len(txns)} records)")
            
        print("✅ CSV Compatibility Checks Passed")

    @patch('auth.auth_handler.get_supabase_client')
    def test_auth_registration_logic(self, mock_get_client):
        """Verify registration logic (hashing and user creation)."""
        print("\n🔹 Testing Auth Registration...")
        
        mock_get_client.return_value = self.mock_supabase
        
        # Simulate saving user
        save_success = save_user_to_supabase("testuser", "test@example.com", "Test User", "hashed_pw")
        
        # Verify Supabase call
        self.mock_supabase.table.assert_called_with('app_users')
        self.mock_supabase.table().insert.assert_called()
        
        self.assertTrue(save_success, "User registration logic failed")
        print("✅ Auth Registration Logic Passed")

if __name__ == '__main__':
    unittest.main()
