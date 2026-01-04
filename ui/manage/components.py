"""
Reusable UI Components for Manage Tab

This module contains helper functions and reusable components:
- Data preparation for AG Grid
- Display formatting
- Common UI patterns
"""

import pandas as pd


def prepare_aggrid_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare DataFrame for AG Grid display."""
    display_df = df.copy()
    # Ensure date is string formatted YYYY-MM-DD to avoid timestamps
    # Convert to string first to handle both datetime objects and strings safely
    display_df['date'] = display_df['date'].astype(str)
    display_df['date'] = pd.to_datetime(display_df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    display_df['Amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
    display_df = display_df.rename(columns={
        'id': 'ID',  # Keep ID but hide it in the grid
        'date': 'Date',
        'description': 'Description',
        'transaction_type': 'Type',
        'category': 'Category',
        'card': 'Card'
    })
    # Return all columns including ID (needed for change tracking) but ID will be hidden in grid
    return display_df[['ID', 'Date', 'Description', 'Amount', 'Type', 'Category', 'Card']]
