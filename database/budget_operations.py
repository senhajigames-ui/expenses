"""
Budget Operations
Budget management and merchant rules using Supabase.
"""

import streamlit as st
from typing import Dict
import logging
from database.supabase_client import get_supabase_client, get_user_id

logger = logging.getLogger(__name__)

# Cache TTL in seconds (5 minutes)
CACHE_TTL = 300


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_budgets(_conn = None) -> Dict[str, float]:
    """
    Get all budget settings from Supabase.
    Args:
        _conn: Ignored (legacy compatibility)
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return {}
            
        supabase = get_supabase_client()
        result = supabase.table('budgets').select("*").eq('user_id', user_id).execute()
        
        budgets = {}
        if result.data:
            for row in result.data:
                budgets[row['category']] = row['monthly_budget']
                
        return budgets
    except Exception as e:
        logger.error(f"Error getting budgets: {e}")
        return {}


def save_budget(conn, category: str, amount: float) -> bool:
    """
    Save or update a budget for a category in Supabase.
    Args:
        conn: Ignored
        category: Category name
        amount: Budget amount
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        
        # Upsert budget
        data = {
            "user_id": user_id,
            "category": category,
            "monthly_budget": amount
        }
        
        # On conflict is handled by having a unique constraint on (user_id, category)
        result = supabase.table('budgets').upsert(data, on_conflict="user_id, category").execute()
        
        # Clear cache
        get_budgets.clear()
        return True
    except Exception as e:
        logger.error(f"Error saving budget: {e}")
        return False


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_merchant_rules(_conn = None) -> Dict[str, str]:
    """
    Load merchant categorization rules from Supabase.
    Args:
        _conn: Ignored
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return {}
            
        supabase = get_supabase_client()
        result = supabase.table('merchant_rules').select("*").eq('user_id', user_id).execute()
        
        rules = {}
        if result.data:
            for row in result.data:
                # Store merchant pattern in uppercase for case-insensitive matching logic
                rules[row['merchant_pattern'].upper()] = row['category']
                
        return rules
    except Exception as e:
        logger.error(f"Error loading merchant rules: {e}")
        return {}


def save_merchant_rule(conn, merchant: str, category: str) -> bool:
    """
    Save a merchant categorization rule in Supabase.
    Args:
        conn: Ignored
        merchant: Merchant pattern
        category: Category
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        
        # Upsert rule
        data = {
            "user_id": user_id,
            "merchant_pattern": merchant.upper(),
            "category": category
        }
        
        # On conflict is handled by having a unique constraint on (user_id, merchant_pattern)
        result = supabase.table('merchant_rules').upsert(data, on_conflict="user_id, merchant_pattern").execute()
        
        # Clear cache
        load_merchant_rules.clear()
        return True
    except Exception as e:
        logger.error(f"Error saving merchant rule: {e}")
        return False


def delete_budget(conn, budget_id: int) -> bool:
    """
    Delete a budget from Supabase.
    Args:
        conn: Ignored
        budget_id: Budget ID to delete
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        result = supabase.table('budgets').delete().eq('id', budget_id).eq('user_id', user_id).execute()
        
        # Clear cache
        get_budgets.clear()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Error deleting budget: {e}")
        st.error("❌ Could not delete budget. Please try again.")
        return False


def delete_merchant_rule(conn, merchant: str) -> bool:
    """
    Delete a merchant rule from Supabase.
    Args:
        conn: Ignored
        merchant: Merchant pattern to delete
    """
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        result = supabase.table('merchant_rules').delete().eq('merchant_pattern', merchant.upper()).eq('user_id', user_id).execute()
        
        # Clear cache
        load_merchant_rules.clear()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Error deleting merchant rule: {e}")
        st.error("❌ Could not delete rule. Please try again.")
        return False