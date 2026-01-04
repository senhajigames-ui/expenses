"""
Transaction database operations.
Handles CRUD operations for expense/income transactions.
"""

import sqlite3
import logging
import pandas as pd
import streamlit as st
from typing import Tuple, List, Dict

# Import Supabase operations
from database.transaction_operations_supabase import (
    add_transaction_supabase,
    bulk_add_transactions_supabase,
    get_transactions_supabase,
    check_duplicates_supabase,
    delete_transaction_supabase,
    clear_all_transactions_supabase
)

logger = logging.getLogger(__name__)


def should_use_supabase() -> bool:
    """Check if Supabase should be used for data operations."""
    # We use Supabase if:
    # 1. Supabase is configured in secrets
    # 2. User is authenticated (Supabase requires auth user_id)
    try:
        if "supabase" in st.secrets and st.session_state.get('authentication_status'):
            return True
    except (FileNotFoundError, AttributeError):
        pass
    return False


def add_transaction(
    conn: sqlite3.Connection, 
    date: str, 
    description: str, 
    amount: float, 
    category: str, 
    source: str, 
    month: str, 
    card: str, 
    transaction_type: str, 
    transaction_code: str = ""
) -> bool:
    """
    Add a single transaction to database.
    
    Args:
        conn: Database connection
        date: Transaction date (YYYY-MM-DD)
        description: Transaction description
        amount: Transaction amount
        category: Category name
        source: Source (e.g., 'RBC CSV Import')
        month: Month in YYYY-MM format
        card: Card type (e.g., 'Visa', 'Cobalt')
        transaction_type: Type (income/expense/transfer/payment)
        transaction_code: Optional transaction code
        
    Returns:
        bool: True if added successfully
    """

    if should_use_supabase():
        return add_transaction_supabase(
            date, description, amount, category, 
            source, False, month, card, 
            transaction_type, transaction_code
        )

    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO transactions 
            (date, description, amount, category, source, processed_date, month, card, transaction_type, transaction_code)
            VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?)
        """, (date, description, amount, category, source, month, card, transaction_type, transaction_code))
        conn.commit()
        c.close()
        return True
    except sqlite3.Error as e:
        logger.warning(f"Error adding transaction: {e}")
        return False


def bulk_add_transactions(conn: sqlite3.Connection, transactions: list) -> Tuple[int, int]:
    """
    Add multiple transactions to database efficiently.
    
    Args:
        conn: Database connection
        transactions: List of transaction dictionaries
        
    Tuple[int, int]: (success_count, fail_count)
    """
    if should_use_supabase():
        if bulk_add_transactions_supabase(transactions):
            return len(transactions), 0
        else:
            return 0, len(transactions)

    success = 0
    fail = 0
    
    try:
        c = conn.cursor()
        
        # Prepare data for executemany
        data_to_insert = []
        for txn in transactions:
            data_to_insert.append((
                txn['date'],
                txn['description'],
                txn['amount'],
                txn['category'],
                f"{txn['card']} CSV Import",
                txn['month'],
                txn['card'],
                txn['transaction_type'],
                txn.get('transaction_code', '')
            ))
            
        c.executemany("""
            INSERT INTO transactions 
            (date, description, amount, category, source, processed_date, month, card, transaction_type, transaction_code)
            VALUES (?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?)
        """, data_to_insert)
        
        conn.commit()
        success = c.rowcount
        c.close()
        
    except sqlite3.Error as e:
        logger.warning(f"Error bulk adding transactions: {e}")
        fail = len(transactions)
        
    return success, fail


def get_transactions(
    conn: sqlite3.Connection, 
    start_date: str = None, 
    end_date: str = None
) -> pd.DataFrame:
    """
    Get transactions from database with optional date filtering.
    
    Args:
        conn: Database connection
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        DataFrame: Transactions dataframe
    """
    if should_use_supabase():
        return get_transactions_supabase(start_date, end_date)

    try:
        query = "SELECT * FROM transactions"
        if start_date and end_date:
            query += f" WHERE date >= '{start_date}' AND date <= '{end_date}'"
        query += " ORDER BY date DESC"
        
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        logger.warning(f"Error getting transactions: {e}")
        return pd.DataFrame()


def check_duplicates(conn, transactions):
    """
    Check for duplicate transactions in database.
    
    Args:
        conn: Database connection
        transactions: List of transaction dictionaries
        
    Returns:
        list: List of duplicate transactions
    """
    if should_use_supabase():
        # Convert list of dicts to DataFrame for check_duplicates_supabase
        df = pd.DataFrame(transactions)
        result_df = check_duplicates_supabase(df)
        return result_df.to_dict('records')

    duplicates = []
    c = conn.cursor()
    
    for txn in transactions:
        c.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE date = ? AND description = ? AND amount = ?
        """, (txn['date'], txn['description'], txn['amount']))
        
        if c.fetchone()[0] > 0:
            duplicates.append(txn)
    
    c.close()
    return duplicates


def delete_transaction(conn, transaction_id):
    """
    Delete a transaction.
    
    Args:
        conn: Database connection
        transaction_id: ID of transaction to delete
        
    Returns:
        bool: True if deleted successfully
    """
    if should_use_supabase():
        return delete_transaction_supabase(transaction_id)

    try:
        c = conn.cursor()
        c.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
        c.close()
        return True
    except sqlite3.Error as e:
        logger.warning(f"Error deleting transaction: {e}")
        return False


def clear_all_transactions(conn):
    """
    Delete all transactions from database.
    
    Args:
        conn: Database connection
        
    Returns:
        bool: True if cleared successfully
    """
    if should_use_supabase():
        return clear_all_transactions_supabase()

    try:
        c = conn.cursor()
        c.execute("DELETE FROM transactions")
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.warning(f"Error clearing transactions: {e}")
        return False