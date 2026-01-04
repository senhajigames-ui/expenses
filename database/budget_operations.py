"""
Budget management database operations.
Handles budget setting and retrieval, and merchant categorization rules.
"""

import sqlite3
import logging
import streamlit as st
import pandas as pd

# Import Supabase operations
from database.budget_operations_supabase import (
    get_budgets_supabase,
    save_budget_supabase,
    load_merchant_rules_supabase,
    save_merchant_rule_supabase
)

# Reuse the helper from transaction_operations or define it here
# Defining it here to avoid circular imports if transaction_operations imports this
def should_use_supabase() -> bool:
    try:
        if "supabase" in st.secrets and st.session_state.get('authentication_status'):
            return True
    except (FileNotFoundError, AttributeError):
        pass
    return False

logger = logging.getLogger(__name__)

# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_budgets(_conn):
    """
    Get all budget settings.
    
    Args:
        _conn: Database connection (underscore prefix for st.cache_data)
        
    Returns:
        dict: Dictionary mapping category to budget amount
    """
    if should_use_supabase():
        return get_budgets_supabase()

    try:
        df = pd.read_sql("SELECT * FROM budgets", _conn)
        budgets = {}
        for _, row in df.iterrows():
            budgets[row['category']] = row['monthly_budget']
        return budgets
    except Exception as e:
        logger.warning(f"Error getting budgets: {e}")
        return {}


def save_budget(conn, category, amount):
    """
    Save or update a budget for a category.
    
    Args:
        conn: Database connection
        category: Category name
        amount: Monthly budget amount
        
    Returns:
        bool: True if saved successfully
    """
    if should_use_supabase():
        return save_budget_supabase(category, amount)

    try:
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO budgets (category, monthly_budget) 
            VALUES (?, ?)
        """, (category, amount))
        conn.commit()
        # Clear cache after saving
        get_budgets.clear()
        return True
    except sqlite3.Error as e:
        logger.warning(f"Error saving budget: {e}")
        return False


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_merchant_rules(_conn):
    """
    Load merchant categorization rules.
    
    Args:
        _conn: Database connection (underscore prefix for st.cache_data)
        
    Returns:
        dict: Dictionary mapping merchant pattern to category
    """
    if should_use_supabase():
        return load_merchant_rules_supabase()

    try:
        df = pd.read_sql("SELECT * FROM merchant_rules", _conn)
        rules = {}
        for _, row in df.iterrows():
            rules[row['merchant_pattern'].upper()] = row['category']
        return rules
    except Exception as e:
        logger.warning(f"Error loading merchant rules: {e}")
        return {}


def save_merchant_rule(conn, merchant, category):
    """
    Save a merchant categorization rule.
    
    Args:
        conn: Database connection
        merchant: Merchant name/pattern
        category: Category to assign
        
    Returns:
        bool: True if saved successfully
    """
    if should_use_supabase():
        return save_merchant_rule_supabase(merchant, category)

    try:
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO merchant_rules (merchant_pattern, category) 
            VALUES (?, ?)
        """, (merchant.upper(), category))
        conn.commit()
        # Clear cache after saving
        load_merchant_rules.clear()
        return True
    except sqlite3.Error as e:
        logger.warning(f"Error saving merchant rule: {e}")
        return False