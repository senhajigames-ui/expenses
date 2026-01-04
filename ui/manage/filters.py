"""
Transaction Filtering Logic - Manage Tab Component

This module handles all transaction filtering functionality:
- Month, type, category, and search filters
- Filter persistence via URL query parameters
- Dynamic category filtering based on type
"""

import streamlit as st
import pandas as pd
from typing import List
from config import (
    EXPENSE_CATEGORIES, INCOME_CATEGORIES, 
    TRANSFER_CATEGORIES, PAYMENT_CATEGORIES
)


class TransactionFilter:
    """Handle transaction filtering logic."""
    
    @staticmethod
    def render(all_transactions: pd.DataFrame):
        """Render filter widgets with persistence."""
        # Restore filters from query params on first load
        TransactionFilter._restore_from_query_params()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            TransactionFilter._render_month_filter(all_transactions)
        
        with col2:
            TransactionFilter._render_type_filter()
        
        with col3:
            TransactionFilter._render_category_filter(all_transactions)
        
        with col4:
            TransactionFilter._render_search_filter()
        
        # Update query params when filters change
        TransactionFilter._update_query_params()
    
    @staticmethod
    def _restore_from_query_params():
        """Restore filter values from URL query parameters."""
        query_params = st.query_params
        
        # Restore month filter
        if 'month' in query_params and 'manage_month' not in st.session_state:
            st.session_state.manage_month = query_params['month']
        
        # Restore type filter
        if 'type' in query_params and 'manage_type' not in st.session_state:
            st.session_state.manage_type = query_params['type']
        
        # Restore category filter
        if 'category' in query_params and 'manage_cat' not in st.session_state:
            st.session_state.manage_cat = query_params['category']
        
        # Restore search filter
        if 'search' in query_params and 'manage_search' not in st.session_state:
            st.session_state.manage_search = query_params['search']
    
    @staticmethod
    def _update_query_params():
        """Update URL query parameters with current filter values."""
        month = st.session_state.get('manage_month', 'All')
        type_filter = st.session_state.get('manage_type', 'All')
        category = st.session_state.get('manage_cat', 'All')
        search = st.session_state.get('manage_search', '')
        
        # Only add to URL if not default value
        if month != 'All':
            st.query_params['month'] = month
        elif 'month' in st.query_params:
            del st.query_params['month']
        
        if type_filter != 'All':
            st.query_params['type'] = type_filter
        elif 'type' in st.query_params:
            del st.query_params['type']
        
        if category != 'All':
            st.query_params['category'] = category
        elif 'category' in st.query_params:
            del st.query_params['category']
        
        if search:
            st.query_params['search'] = search
        elif 'search' in st.query_params:
            del st.query_params['search']
    
    
    @staticmethod
    def _render_month_filter(all_transactions: pd.DataFrame):
        """Render month filter dropdown."""
        months = ["All"] + sorted(
            all_transactions['month'].unique().tolist(), 
            reverse=True
        )
        st.selectbox("Month", months, key='manage_month')
    
    
    @staticmethod
    def _render_type_filter():
        """Render transaction type filter."""
        st.selectbox(
            "Type",
            ["All", "Expenses", "Income", "Transfers", "Payments"],
            key='manage_type'
        )
    
    
    @staticmethod
    def _render_category_filter(all_transactions: pd.DataFrame):
        """Render category filter (dynamic based on type)."""
        type_filter = st.session_state.get('manage_type', 'All')
        
        if type_filter == "All":
            # Show all categories but disabled
            categories = ["All"] + sorted(
                all_transactions['category'].unique().tolist()
            )
            st.selectbox(
                "Category", 
                categories, 
                key='manage_cat',
                disabled=True,
                help="Select a Type first to filter by Category"
            )
        else:
            # Show filtered categories
            categories = TransactionFilter._get_categories_for_type(
                type_filter, 
                all_transactions
            )
            st.selectbox("Category", categories, key='manage_cat')
    
    
    @staticmethod
    def _render_search_filter():
        """Render search input."""
        st.text_input(
            "🔎 Search", 
            placeholder="Description...", 
            key='manage_search'
        )
    
    
    @staticmethod
    def _get_categories_for_type(
        type_filter: str, 
        all_transactions: pd.DataFrame
    ) -> List[str]:
        """Get available categories for selected transaction type."""
        type_to_categories = {
            "Expenses": EXPENSE_CATEGORIES,
            "Income": INCOME_CATEGORIES,
            "Transfers": TRANSFER_CATEGORIES,
            "Payments": PAYMENT_CATEGORIES
        }
        
        category_list = type_to_categories.get(type_filter, [])
        
        # Only show categories that exist in transactions
        available = [
            cat for cat in category_list 
            if cat in all_transactions['category'].values
        ]
        
        return ["All"] + available
    
    
    @staticmethod
    def apply(all_transactions: pd.DataFrame) -> pd.DataFrame:
        """Apply all active filters and return filtered DataFrame."""
        filtered = all_transactions.copy()
        
        # Month filter
        month = st.session_state.get('manage_month', 'All')
        if month != 'All':
            filtered = filtered[filtered['month'] == month]
        
        # Type filter
        type_filter = st.session_state.get('manage_type', 'All')
        if type_filter != 'All':
            type_map = {
                'Expenses': 'expense',
                'Income': 'income',
                'Transfers': 'transfer',
                'Payments': 'payment'
            }
            filtered = filtered[
                filtered['transaction_type'] == type_map[type_filter]
            ]
        
        # Category filter
        category = st.session_state.get('manage_cat', 'All')
        if category != 'All':
            filtered = filtered[filtered['category'] == category]
        
        # Search filter
        search = st.session_state.get('manage_search', '')
        if search:
            filtered = filtered[
                filtered['description'].str.contains(search, case=False, na=False)
            ]
        
        return filtered
