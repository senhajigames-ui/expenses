
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime
from database.transaction_operations import check_duplicates

class TestImportOptimization(unittest.TestCase):
    
    @patch('database.transaction_operations.get_user_id')
    @patch('database.transaction_operations.get_supabase_client')
    @patch('database.transaction_operations.get_transactions')
    def test_check_duplicates_uses_date_range(self, mock_get_txns, mock_client, mock_user):
        """Test that check_duplicates filters by date range."""
        mock_user.return_value = "user123"
        mock_get_txns.return_value = pd.DataFrame() # Return empty for this test, we just check arguments
        
        # logical date range: Jan 10 - Jan 12
        data = [
            {'date': '2024-01-10', 'description': 'Test 1', 'amount': 10.0},
            {'date': '2024-01-12', 'description': 'Test 2', 'amount': 20.0}
        ]
        df = pd.DataFrame(data)
        
        check_duplicates(None, df)
        
        # Expected range: Jan 09 to Jan 13 (buffer +/- 1 day)
        mock_get_txns.assert_called_once()
        args, kwargs = mock_get_txns.call_args
        
        self.assertEqual(kwargs['start_date'], '2024-01-09')
        self.assertEqual(kwargs['end_date'], '2024-01-13')
        
    @patch('database.transaction_operations.get_user_id')
    @patch('database.transaction_operations.get_supabase_client')
    @patch('database.transaction_operations.get_transactions')
    def test_check_duplicates_legacy_behavior(self, mock_get_txns, mock_client, mock_user):
        """Test fallback if no date column (should shouldn't happen but good for robust checks)."""
        mock_user.return_value = "user123"
        
        df = pd.DataFrame([{'description': 'No Date', 'amount': 10.0}])
        # No 'date' column
        
        result = check_duplicates(None, df)
        
        # Should return empty DF and NOT call get_transactions (based on my implementation)
        mock_get_txns.assert_not_called()
        self.assertTrue(result.empty)

if __name__ == '__main__':
    unittest.main()
