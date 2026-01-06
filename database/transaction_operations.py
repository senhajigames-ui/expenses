"""
Transaction Operations
CRUD operations for transactions using Supabase.
"""

import streamlit as st
import pandas as pd
from typing import Optional, List
from datetime import datetime
import logging
from database.supabase_client import get_supabase_client, get_user_id

logger = logging.getLogger(__name__)


def add_transaction(
    date: str,
    description: str,
    amount: float,
    category: str,
    source: str = "",
    is_refund: bool = False,
    month: str = "",
    card: str = "",
    transaction_type: str = "",
    transaction_code: str = ""
) -> bool:
    """Add a single transaction to Supabase."""
    try:
        user_id = get_user_id()
        if not user_id:
            raise ValueError("User not authenticated")
            
        supabase = get_supabase_client()
        
        data = {
            "user_id": user_id,
            "date": date,
            "description": description,
            "amount": amount,
            "category": category,
            "source": source,
            "is_refund": is_refund,
            "month": month,
            "card": card,
            "transaction_type": transaction_type,
            "transaction_code": transaction_code,
            "processed_date": datetime.now().isoformat()
        }
        
        result = supabase.table('transactions').insert(data).execute()
        return True
        
    except ValueError as e:
        logger.error(f"Validation error adding transaction: {e}")
        st.error("❌ Please log in to save transactions.")
        return False
    except Exception as e:
        error_msg = str(e).lower()
        if "network" in error_msg or "connection" in error_msg or "timeout" in error_msg:
            st.error("🌐 Connection error. Please check your internet and try again.")
        else:
            st.error("❌ Could not save transaction. Please try again.")
        logger.error(f"Failed to add transaction: {e}")
        return False


def bulk_add_transactions(transactions: List[dict]) -> bool:
    """Add multiple transactions to Supabase."""
    try:
        user_id = get_user_id()
        if not user_id:
            raise ValueError("User not authenticated")
            
        supabase = get_supabase_client()
        
        # Add user_id and processed_date to each transaction
        for txn in transactions:
            txn['user_id'] = user_id
            txn['processed_date'] = datetime.now().isoformat()
        
        result = supabase.table('transactions').insert(transactions).execute()
        return True
        
    except ValueError as e:
        logger.error(f"Validation error in bulk add: {e}")
        st.error("❌ Please log in to import transactions.")
        return False
    except Exception as e:
        error_msg = str(e).lower()
        if "network" in error_msg or "connection" in error_msg or "timeout" in error_msg:
            st.error("🌐 Connection error during import. Please check your internet and try again.")
        else:
            st.error(f"❌ Import failed. {len(transactions)} transactions could not be saved.")
        logger.error(f"Failed to bulk add transactions: {e}")
        return False


def get_transactions(conn = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get transactions from Supabase with pagination support.
    Bypasses the default 1000-row API limit.
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return pd.DataFrame()
            
        supabase = get_supabase_client()
        
        all_transactions = []
        batch_size = 1000
        offset = 0
        
        while True:
            # Build query
            query = supabase.table('transactions').select("*").eq('user_id', user_id)
            
            if start_date:
                query = query.gte('date', start_date)
            if end_date:
                query = query.lte('date', end_date)
            
            # Add range/pagination
            # Supabase uses .range(start, end) inclusive
            batch_result = query.range(offset, offset + batch_size - 1).execute()
            
            if not batch_result.data:
                break
                
            all_transactions.extend(batch_result.data)
            
            # If we got fewer rows than the batch size, we're done
            if len(batch_result.data) < batch_size:
                break
                
            # Move to next batch
            offset += batch_size
        
        if not all_transactions:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_transactions)
        return df
        
    except Exception as e:
        error_msg = str(e).lower()
        if "network" in error_msg or "connection" in error_msg or "timeout" in error_msg:
            st.error("🌐 Could not load transactions. Please check your internet connection.")
        else:
            st.error("❌ Error loading transactions. Please refresh the page.")
        logger.error(f"Failed to get transactions: {e}")
        return pd.DataFrame()


def search_transactions(query_text: str, exclude_id: Optional[int] = None, limit: int = 50) -> List[dict]:
    """
    Search transactions using server-side filtering.
    Efficiently finds potential matches using Supabase ilike.
    
    Args:
        query_text: Text to search for in description
        exclude_id: ID to exclude from results (usually the current transaction)
        limit: Max results to return
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return []
            
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table('transactions') \
            .select('id, description, category, transaction_type, amount, date') \
            .eq('user_id', user_id) \
            .ilike('description', f'%{query_text}%')
            
        if exclude_id:
            query = query.neq('id', exclude_id)
            
        # Limit results for performance
        result = query.limit(limit).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        logger.error(f"Failed to search transactions: {e}")
        return []


def check_duplicates(conn, transactions_df):
    """
    Check for duplicate transactions.
    Args:
    Args:
        conn: Ignored (legacy compatibility)
        transactions_df: DataFrame/List of transactions
    """
    # Handle list input (legacy) convert to DF
    if isinstance(transactions_df, list):
        transactions_df = pd.DataFrame(transactions_df)

    try:
        user_id = get_user_id()
        if not user_id or transactions_df.empty:
            return pd.DataFrame() if isinstance(transactions_df, pd.DataFrame) else []
            
        supabase = get_supabase_client()
        
        # Optimize: Only fetch transactions within the date range of the import
        # Add a small buffer (e.g., +/- 1 day) to handle timezone edge cases
        if 'date' not in transactions_df.columns:
            return pd.DataFrame()
            
        dates = pd.to_datetime(transactions_df['date'])
        min_date = (dates.min() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        max_date = (dates.max() + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Get existing transactions ONLY in this range
        existing = get_transactions(start_date=min_date, end_date=max_date)
        
        if existing.empty:
            return pd.DataFrame() if isinstance(transactions_df, pd.DataFrame) else []
            
        # Find duplicates based on date, description, and amount
        duplicates = []
        for _, new_txn in transactions_df.iterrows():
            matches = existing[
                (existing['date'] == str(new_txn['date'])) &
                (existing['description'] == new_txn['description']) &
                (abs(existing['amount'] - new_txn['amount']) < 0.01)
            ]
            if not matches.empty:
                duplicates.append(new_txn)
                
        # Return format matching input type if needed, but managing consistent return type is better
        # Legacy returned list of dicts or DF. Let's return what matches input.
        result_df = pd.DataFrame(duplicates) if duplicates else pd.DataFrame()
        return result_df
        
    except Exception as e:
        logger.error(f"Failed to check duplicates: {e}")
        # Silent fail for duplicate check - doesn't block user
        return pd.DataFrame()


def delete_transaction(conn, transaction_id: int) -> bool:
    """
    Delete a transaction from Supabase.
    Args:
         conn: Ignored
         transaction_id: ID to delete
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        
        # Delete with RLS check (user can only delete their own)
        result = supabase.table('transactions').delete().eq('id', transaction_id).eq('user_id', user_id).execute()
        return len(result.data) > 0
        
    except Exception as e:
        error_msg = str(e).lower()
        if "network" in error_msg or "connection" in error_msg:
            st.error("🌐 Connection error. Could not delete transaction.")
        else:
            st.error("❌ Could not delete transaction. Please try again.")
        logger.error(f"Failed to delete transaction: {e}")
        return False


def clear_all_transactions(conn) -> bool:
    """
    Clear all transactions for current user.
    Args:
        conn: Ignored
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        
        # Delete all user's transactions
        result = supabase.table('transactions').delete().eq('user_id', user_id).execute()
        return len(result.data) > 0
        
    except Exception as e:
        error_msg = str(e).lower()
        if "network" in error_msg or "connection" in error_msg:
            st.error("🌐 Connection error. Could not clear transactions.")
        else:
            st.error("❌ Could not clear transactions. Please try again.")
        logger.error(f"Failed to clear transactions: {e}")
        return False


def update_transaction(transaction_id: int, updates: dict) -> bool:
    """Update a transaction in Supabase."""
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        
        # Update with RLS check
        result = supabase.table('transactions').update(updates).eq('id', transaction_id).eq('user_id', user_id).execute()
        return len(result.data) > 0
        
    except Exception as e:
        error_msg = str(e).lower()
        if "network" in error_msg or "connection" in error_msg:
            st.error("🌐 Connection error. Could not update transaction.")
        else:
            st.error("❌ Could not update transaction. Please try again.")
        logger.error(f"Failed to update transaction: {e}")
        return False