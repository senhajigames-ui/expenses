
import unittest
import pandas as pd
import sys
import os
import random
import string
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.manage.updater import TransactionUpdater

class TestMonkeyUpdater(unittest.TestCase):
    """
    Monkey Testing for TransactionUpdater.
    Throws random/malformed data at the critical update function 
    to ensure it handles garbage gracefully without crashing.
    """
    
    def setUp(self):
        self.mock_conn = MagicMock()
        self.updater = TransactionUpdater(self.mock_conn)
        
        # valid basic frames
        self.original_df = pd.DataFrame({
            'id': [1, 2, 3],
            'description': ['Test 1', 'Test 2', 'Test 3'],
            'transaction_type': ['expense', 'income', 'expense'],
            'category': ['Other', 'Salary', 'Rent']
        })
        self.display_df = pd.DataFrame({
            'ID': [1, 2, 3], # Hidden ID column
            'Description': ['Test 1', 'Test 2', 'Test 3']
        })

    def generate_random_string(self, length=10):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def test_garbage_editor_state(self):
        """Test with completely random types passed as editor_state"""
        garbage_inputs = [
            None,
            [],
            "Some String",
            12345,
            pd.DataFrame({'a': [1, 2]}), # The specific bug we fixed!
            {'edited_rows': None},
            {'edited_rows': "Not a dict"},
            {'edited_rows': {1: "Not a dict"}}, # Row content malformed
        ]
        
        for garbage in garbage_inputs:
            try:
                # Should NOT raise exception
                self.updater.process_data_editor_changes(
                    self.original_df,
                    self.display_df,
                    garbage
                )
            except Exception as e:
                self.fail(f"Crashed on garbage input: {garbage} -> {e}")

    def test_edge_case_rows(self):
        """Test with random row indices and content"""
        # Case 1: Row index out of bounds
        state_oob = {'edited_rows': {999: {'Category': 'New Cat'}}} 
        self.updater.process_data_editor_changes(self.original_df, self.display_df, state_oob)
        
        # Case 2: Negative index
        state_neg = {'edited_rows': {-1: {'Category': 'New Cat'}}}
        self.updater.process_data_editor_changes(self.original_df, self.display_df, state_neg)
        
        # Case 3: Malformed keys
        state_bad_keys = {'edited_rows': {0: {'NotAColumn': 'Value'}}}
        self.updater.process_data_editor_changes(self.original_df, self.display_df, state_bad_keys)

    @patch('streamlit.error')
    def test_dataframe_pass_specifically(self, mock_error):
        """Verify the specific safeguard we added against passing DataFrames"""
        df_input = pd.DataFrame({'a': [1]})
        self.updater.process_data_editor_changes(self.original_df, self.display_df, df_input)
        
        # Should have called st.error with "Programmer Error"
        called = False
        for call in mock_error.call_args_list:
            if "Programmer Error" in str(call):
                called = True
                break
        
        self.assertTrue(called, "Did not catch DataFrame input with specific error message")

if __name__ == '__main__':
    print("🙈 Running Monkey Tests...")
    unittest.main()
