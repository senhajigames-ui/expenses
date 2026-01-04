"""
Budget management database operations.
Handles budget setting and retrieval, and merchant categorization rules.
"""

import sqlite3
import logging
import streamlit as st
import pandas as pd

from database.budget_operations_supabase import (
    get_budgets_supabase,
    save_budget_supabase,
    load_merchant_rules_supabase,
    save_merchant_rule_supabase
)
from database.db_utils import should_use_supabase

logger = logging.getLogger(__name__)

# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300


def get_budgets(_conn):
    """
    Get all budget settings.
    
    Args:
        _conn: Database connection (underscore prefix for st.cache_data)
        
    Returns:
        dict: Dictionary mapping category to budget amount
    """
    # Check Supabase BEFORE cache to avoid returning stale cached SQLite data
    if should_use_supabase():
        return get_budgets_supabase()
    
    return _get_budgets_sqlite(_conn)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _get_budgets_sqlite(_conn):
    """Internal cached SQLite query for budgets."""
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
        _get_budgets_sqlite.clear()
        return True
    except sqlite3.Error as e:
        logger.warning(f"Error saving budget: {e}")
        return False


def load_merchant_rules(_conn):
    """
    Load merchant categorization rules.
    
    Args:
        _conn: Database connection (underscore prefix for st.cache_data)
        
    Returns:
        dict: Dictionary mapping merchant pattern to category
    """
    # Check Supabase BEFORE cache to avoid returning stale cached SQLite data
    if should_use_supabase():
        return load_merchant_rules_supabase()
    
    return _load_merchant_rules_sqlite(_conn)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _load_merchant_rules_sqlite(_conn):
    """Internal cached SQLite query for merchant rules."""
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
        _load_merchant_rules_sqlite.clear()
        return True
    except sqlite3.Error as e:
        logger.warning(f"Error saving merchant rule: {e}")
        return False