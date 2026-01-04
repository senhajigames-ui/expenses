"""
Supabase Transaction Operations
CRUD operations for transactions using Supabase as backend.
"""

import streamlit as st
import pandas as pd
from typing import Optional, List
from datetime import datetime
import logging
from database.supabase_client import get_supabase_client, get_user_id

logger = logging.getLogger(__name__)


def add_transaction_supabase(
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
        
    except Exception as e:
        logger.error(f"Failed to add transaction: {e}")
        return False


def bulk_add_transactions_supabase(transactions: List[dict]) -> bool:
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
        
    except Exception as e:
        logger.error(f"Failed to bulk add transactions: {e}")
        return False


def get_transactions_supabase(start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """Get transactions from Supabase."""
    try:
        user_id = get_user_id()
        if not user_id:
            return pd.DataFrame()
            
        supabase = get_supabase_client()
        
        query = supabase.table('transactions').select("*").eq('user_id', user_id)
        
        if start_date:
            query = query.gte('date', start_date)
        if end_date:
            query = query.lte('date', end_date)
            
        result = query.execute()
        
        if not result.data:
            return pd.DataFrame()
            
        df = pd.DataFrame(result.data)
        return df
        
    except Exception as e:
        logger.error(f"Failed to get transactions: {e}")
        return pd.DataFrame()


def check_duplicates_supabase(transactions_df: pd.DataFrame) -> pd.DataFrame:
    """Check for duplicate transactions."""
    try:
        user_id = get_user_id()
        if not user_id or transactions_df.empty:
            return pd.DataFrame()
            
        supabase = get_supabase_client()
        
        # Get existing transactions
        existing = get_transactions_supabase()
        
        if existing.empty:
            return pd.DataFrame()
            
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
                
        return pd.DataFrame(duplicates) if duplicates else pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Failed to check duplicates: {e}")
        return pd.DataFrame()


def delete_transaction_supabase(transaction_id: int) -> bool:
    """Delete a transaction from Supabase."""
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        
        # Delete with RLS check (user can only delete their own)
        result = supabase.table('transactions').delete().eq('id', transaction_id).eq('user_id', user_id).execute()
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete transaction: {e}")
        return False


def clear_all_transactions_supabase() -> bool:
    """Clear all transactions for current user."""
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        
        # Delete all user's transactions
        result = supabase.table('transactions').delete().eq('user_id', user_id).execute()
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear transactions: {e}")
        return False


def update_transaction_supabase(transaction_id: int, updates: dict) -> bool:
    """Update a transaction in Supabase."""
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        
        # Update with RLS check
        result = supabase.table('transactions').update(updates).eq('id', transaction_id).eq('user_id', user_id).execute()
        return True
        
    except Exception as e:
        logger.error(f"Failed to update transaction: {e}")
        return False
