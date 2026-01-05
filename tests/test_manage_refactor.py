
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from ui.manage.updater import TransactionUpdater

class TestManageRefactor(unittest.TestCase):
    
    def setUp(self):
        self.updater = TransactionUpdater(conn=None)

    @patch('database.transaction_operations.get_supabase_client')
    @patch('database.transaction_operations.get_user_id')
    def test_search_transactions_logic(self, mock_user_id, mock_supabase):
        """Test that search_transactions calls Supabase correctly."""
        from database.transaction_operations import search_transactions
        
        mock_user_id.return_value = "user123"
        
        # Mock query chain - Supabase client returns self on most methods
        mock_client = MagicMock()
        mock_supabase.return_value = mock_client
        
        # Setup table().select().eq().ilike() chain
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        
        mock_select = MagicMock()
        mock_table.select.return_value = mock_select
        
        mock_eq = MagicMock()
        mock_select.eq.return_value = mock_eq
        
        mock_ilike = MagicMock()
        mock_eq.ilike.return_value = mock_ilike
        
        # .limit().execute()
        mock_limit = MagicMock()
        mock_ilike.limit.return_value = mock_limit
        
        mock_response = MagicMock()
        mock_response.data = [{'id': 1, 'description': 'AMAZON'}]
        mock_limit.execute.return_value = mock_response
        
        # Also need to handle the exclude_id case which adds a .neq()
        mock_neq = MagicMock()
        mock_ilike.neq.return_value = mock_neq
        mock_neq.limit.return_value = mock_limit
        
        # Run test
        results = search_transactions("AMAZON", exclude_id=None)
        
        # Verify call chain
        mock_select.eq.assert_called_with('user_id', 'user123')
        mock_eq.ilike.assert_called_with('description', '%AMAZON%')
        self.assertEqual(len(results), 1)

    @patch('database.transaction_operations.search_transactions')
    def test_find_similar_transactions(self, mock_search):
        """Test _find_similar_transactions uses server-side search."""
        
        # Mock return data from search
        mock_search.return_value = [
            {'id': 2, 'description': 'AMAZON CA', 'category': 'Shopping', 'transaction_type': 'expense', 'amount': 10.0, 'date': '2024-01-01'},
            {'id': 3, 'description': 'AMAZON UK', 'category': 'Shopping', 'transaction_type': 'expense', 'amount': 20.0, 'date': '2024-01-01'}
        ]
        
        results = self.updater._find_similar_transactions(
            merchant="AMAZON",
            exclude_id=1,
            new_category="Groceries", # Searching for things that are NOT Groceries
            new_type="expense"
        )
        
        # Should find both because their category 'Shopping' != 'Groceries'
        self.assertEqual(len(results), 2)
        mock_search.assert_called_once_with("AMAZON", exclude_id=1)

    @patch('database.transaction_operations.search_transactions')
    def test_find_similar_transactions_filters_existing(self, mock_search):
        """Test filtering out transactions that already match."""
        
        mock_search.return_value = [
            {'id': 2, 'description': 'AMAZON CA', 'category': 'Groceries', 'transaction_type': 'expense'},  # Already Groceries
            {'id': 3, 'description': 'AMAZON UK', 'category': 'Shopping', 'transaction_type': 'expense'}    # Needs update
        ]
        
        results = self.updater._find_similar_transactions(
            merchant="AMAZON",
            exclude_id=1,
            new_category="Groceries", 
            new_type="expense"
        )
        
        # Should only find id 3
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 3)

if __name__ == '__main__':
    unittest.main()
