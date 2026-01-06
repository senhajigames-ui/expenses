
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import pandas as pd

# Mock streamlit before importing expense_tracker
import sys
mock_st = MagicMock()
sys.modules['streamlit'] = mock_st

# We need to mock the imports inside expense_tracker to avoid side effects
sys.modules['auth.auth_handler'] = MagicMock()
sys.modules['database.transaction_operations'] = MagicMock()
sys.modules['ui.sidebar'] = MagicMock()
sys.modules['ui.tab_import'] = MagicMock()
sys.modules['ui.tab_overview'] = MagicMock()
sys.modules['ui.tab_analysis'] = MagicMock()
sys.modules['ui.tab_manage'] = MagicMock()

from expense_tracker import load_transactions

class TestInitialization(unittest.TestCase):
    
    @patch('expense_tracker.get_transactions')
    def test_load_transactions_defaults_to_recent(self, mock_get_txns):
        """Test default behavior loads only recent history."""
        mock_get_txns.return_value = pd.DataFrame()
        
        load_transactions(load_all=False)
        
        mock_get_txns.assert_called_once()
        args, kwargs = mock_get_txns.call_args
        
        # Verify start_date is passed and is roughly 1 year ago
        self.assertIsNotNone(kwargs.get('start_date'))
        start_date = kwargs.get('start_date')
        
        # Parse date and check year
        dt = datetime.strptime(start_date, '%Y-%m-%d')
        self.assertEqual(dt.year, datetime.now().year - 1)
        
    @patch('expense_tracker.get_transactions')
    def test_load_all_transactions(self, mock_get_txns):
        """Test loading full history."""
        mock_get_txns.return_value = pd.DataFrame()
        
        load_transactions(load_all=True)
        
        mock_get_txns.assert_called_once()
        args, kwargs = mock_get_txns.call_args
        
        # Verify start_date is NOT passed (or is None)
        self.assertIsNone(kwargs.get('start_date'))

if __name__ == '__main__':
    unittest.main()
