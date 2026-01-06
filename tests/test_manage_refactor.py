
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import sys

# Ensure project root is in path
from ui.manage.updater import TransactionUpdater

class TestManageRefactor(unittest.TestCase):
    
    def setUp(self):
        self.updater = TransactionUpdater(conn=None)

    # Note: Patch order is bottom-up -> first arguments
    # patch get_user_id (bottom) -> mock_user_id (first arg)
    # patch get_supabase_client (top) -> mock_supabase (second arg)
    @patch('database.transaction_operations.get_supabase_client')
    @patch('database.transaction_operations.get_user_id')
    def test_search_transactions_logic(self, mock_user_id, mock_client_getter):
        """Test that search_transactions calls Supabase correctly."""
        print(f"\nDEBUG: mock_user_id type: {type(mock_user_id)}")
        print(f"DEBUG: mock_client_getter type: {type(mock_client_getter)}")
        
        # Setup mocks
        mock_user_id.return_value = "user123"
        
        mock_client = MagicMock()
        mock_client_getter.return_value = mock_client
        
        # Chain setup
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        
        mock_eq = MagicMock()
        mock_select.eq.return_value = mock_eq
        
        mock_ilike = MagicMock()
        mock_eq.ilike.return_value = mock_ilike
        
        # Handle exclude_id branch
        mock_limit = MagicMock()
        mock_ilike.limit.return_value = mock_limit
        # Also need to mock return data
        mock_response = MagicMock()
        mock_response.data = [{'id': 1, 'description': 'AMAZON MATCH'}]
        mock_limit.execute.return_value = mock_response
        
        # Import inside test to ensure patch applies to the module lookup
        from database.transaction_operations import search_transactions
        
        # Execute
        results = search_transactions("AMAZON", exclude_id=None)
        
        # Debugging call capture
        print("DEBUG: Client calls:", mock_client.mock_calls)
        print("DEBUG: Table calls:", mock_table.mock_calls)
        print("DEBUG: Select calls:", mock_select.mock_calls)
        
        # Assertions
        # Check if user_id was retrieved
        mock_user_id.assert_called()
        
        # Check chain
        mock_client.table.assert_called_with('transactions')
        
        # We expect a select call. Arguments are "id, description, ..."
        # Instead of assert_called_with which checks strict equality, let's check called
        mock_table.select.assert_called()
        
        # Check eq('user_id', 'user123')
        # If it says 'not called', it means select() didn't return mock_select
        # or mock_select was not used.
        mock_select.eq.assert_called_with('user_id', 'user123')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['description'], 'AMAZON MATCH')


    @patch('database.transaction_operations.search_transactions')
    def test_find_similar_transactions(self, mock_search):
        """Test _find_similar_transactions uses server-side search."""
        
        # Mock Data
        mock_search.return_value = [
            {'id': 2, 'description': 'AMAZON CA', 'category': 'Shopping', 'transaction_type': 'expense', 'amount': 10.0, 'date': '2024-01-01'},
            # This one matches "Shopping" so it should be filtered out if we search for "Shopping" and "expense"
            # Wait, logic is: filter out match if it ALREADY HAS target category/type
        ]
        
        # Case 1: Searching for "Groceries". Matches don't have Groceries. Should return them.
        results = self.updater._find_similar_transactions(
            merchant="AMAZON",
            exclude_id=1,
            new_category="Groceries", 
            new_type="expense"
        )
        
        print("\nDEBUG: Similar Results:", results)
        
        self.assertEqual(len(results), 1) # AMAZON CA is partial match to AMAZON?
        # Logic: if merchant_lower in desc_lower. "amazon" in "amazon ca" -> True.
        
        mock_search.assert_called_once_with("AMAZON", exclude_id=1)


    @patch('streamlit.session_state', new_callable=dict)
    @patch('streamlit.error')
    def test_process_data_editor_changes(self, mock_error, mock_state):
        """Test processing of st.data_editor changes."""
        
        # Setup Data
        original_df = pd.DataFrame([
            {'id': 101, 'description': 'Test Txn', 'category': 'Other', 'transaction_type': 'expense'}
        ])
        
        # Need 'ID' column in display_df
        display_df = pd.DataFrame([
            {'ID': 101, 'Description': 'Test Txn', 'Date': '2024-01-01'}
        ])
        
        # Simulate Editor Output 
        editor_state = {
            'edited_rows': {
                "0": {'Category': 'Groceries'} # Key is usually string in JSON/session state from widget?
                # Actually indices are integers in the dict from st.data_editor usually? 
                # Docs say {0: {...}}. 
                # Let's try int key as key is int in loop: `for row_idx, changes in edited_rows.items():`
            }
        }
        # But wait, code handles `int(row_idx)`. So it accepts strings.
        
        # We need to inject a dict wrapper that pretends to be session state?
        # The test uses patch('streamlit.session_state', {})
        # This creates a MagicMock/dict
        
        with patch('streamlit.session_state', {}) as mock_session:
             self.updater.process_data_editor_changes(
                original_df,
                display_df,
                editor_state,
                grid_key="test"
            )
             
             self.assertIn('pending_changes', mock_session)
             changes = mock_session['pending_changes']
             self.assertEqual(len(changes), 1)
             self.assertEqual(changes[0]['new_category'], 'Groceries')

if __name__ == '__main__':
    unittest.main()
