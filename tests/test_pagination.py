
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from database.transaction_operations import get_transactions

class TestPagination(unittest.TestCase):
    
    @patch('database.transaction_operations.get_supabase_client')
    @patch('database.transaction_operations.get_user_id')
    def test_get_transactions_pagination(self, mock_user_id, mock_client_getter):
        """Test that get_transactions automatically follows pagination."""
        
        mock_user_id.return_value = "test_user_pagination"
        
        # Setup Client
        mock_client = MagicMock()
        mock_client_getter.return_value = mock_client
        
        mock_query = MagicMock()
        mock_client.table('transactions').select().eq.return_value = mock_query
        
        # We need to mock the chain: query.range().execute()
        # Since logic creates a NEW query object inside the loop, we must ensure
        # the chain works for multiple iterations.
        
        # Mocking chain
        # 1. query object is created (mock_query)
        # 2. .range(start, end) called on it
        # 3. .execute() called on result of range()
        
        # We need side_effect for execute() to return different data on consecutive calls
        
        # Create dummy data batches
        batch_1 = [{'id': i, 'desc': f'txn_{i}'} for i in range(1000)] # 0 to 999
        batch_2 = [{'id': i, 'desc': f'txn_{i}'} for i in range(1000, 1200)] # 1000 to 1199
        
        # Setup mock for range() to return a mock that has an execute() method
        mock_range_result = MagicMock()
        mock_query.range.return_value = mock_range_result
        
        # Define side effect for execute
        # First call: Batch 1 (1000 items)
        # Second call: Batch 2 (200 items) -> should break loop after this because len < 1000
        
        response_1 = MagicMock()
        response_1.data = batch_1
        
        response_2 = MagicMock()
        response_2.data = batch_2
        
        mock_range_result.execute.side_effect = [response_1, response_2]
        
        # Mock .gte and .lte simply returning the query itself to support chaining
        mock_query.gte.return_value = mock_query
        mock_query.lte.return_value = mock_query
        
        # Also handle the initial chain of .select("*").eq(...)
        # The logic is: supabase.table('transactions').select("*").eq('user_id', user_id)
        # mock_client.table().select().eq() is already returning mock_query
        
        # Run function
        df = get_transactions()
        
        # Assertions
        self.assertEqual(len(df), 1200)
        self.assertEqual(df.iloc[0]['id'], 0)
        self.assertEqual(df.iloc[1199]['id'], 1199)
        
        # Verify range calls
        # We expect 2 calls
        # 1. range(0, 999)
        # 2. range(1000, 1999)
        
        calls = mock_query.range.call_args_list
        print(f"DEBUG: Actual calls: {calls}")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], unittest.mock.call(0, 999))
        self.assertEqual(calls[1], unittest.mock.call(1000, 1999))
        
if __name__ == '__main__':
    unittest.main()
