"""
Supabase Import History Operations
Import history tracking using Supabase as backend.
"""

import streamlit as st
import hashlib
import logging
from datetime import datetime
from typing import Dict, List
from database.supabase_client import get_supabase_client, get_user_id

logger = logging.getLogger(__name__)


# Note: calculate_file_hash is defined in import_history.py and should be imported from there if needed


def check_file_already_imported_supabase(filename: str, file_hash: str) -> bool:
    """Check if a file has already been imported in Supabase."""
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        
        # Count matching records
        result = supabase.table('import_history')\
            .select("id", count='exact')\
            .eq('user_id', user_id)\
            .eq('filename', filename)\
            .eq('file_hash', file_hash)\
            .execute()
            
        return result.count > 0
    except Exception as e:
        logger.error(f"Error checking import history: {e}")
        return False


def record_file_import_supabase(filename: str, file_hash: str, transactions_imported: int) -> bool:
    """Record a file import in Supabase."""
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        
        data = {
            "user_id": user_id,
            "filename": filename,
            "file_hash": file_hash,
            "transactions_imported": transactions_imported,
            "import_date": datetime.now().isoformat()
        }
        
        result = supabase.table('import_history').insert(data).execute()
        return True
    except Exception as e:
        logger.error(f"Error recording import: {e}")
        return False


def get_import_history_supabase(limit: int = 10) -> List[Dict]:
    """Get recent import history from Supabase."""
    try:
        user_id = get_user_id()
        if not user_id:
            return []
            
        supabase = get_supabase_client()
        
        result = supabase.table('import_history')\
            .select("filename, import_date, transactions_imported")\
            .eq('user_id', user_id)\
            .order('import_date', desc=True)\
            .limit(limit)\
            .execute()
            
        if not result.data:
            return []
            
        # Format dates nicely or keep as ISO string depending on UI needs
        # For now return raw data to match DB structure
        return result.data
        
    except Exception as e:
        logger.error(f"Error getting import history: {e}")
        return []


def get_import_stats_supabase() -> Dict:
    """Get import statistics from Supabase."""
    try:
        user_id = get_user_id()
        if not user_id:
            return {'total_files': 0, 'total_transactions': 0, 'last_import': None}
            
        supabase = get_supabase_client()
        
        # We need multiple queries or a stored procedure ideally
        # For now doing separate queries
        
        # 1. Total files
        files_result = supabase.table('import_history')\
            .select("id", count='exact')\
            .eq('user_id', user_id)\
            .execute()
        total_files = files_result.count
        
        # 2. Total transactions (sum)
        # Supabase doesn't support sum() in JS library easily without rpc
        # So we fetch column and sum in python (not efficient for large data but ok for now)
        # OR use a raw SQL/RPC if enabled
        
        txn_result = supabase.table('import_history')\
            .select("transactions_imported")\
            .eq('user_id', user_id)\
            .execute()
            
        total_transactions = sum(row['transactions_imported'] for row in txn_result.data) if txn_result.data else 0
        
        # 3. Last import
        last_import = None
        last_result = supabase.table('import_history')\
            .select("import_date")\
            .eq('user_id', user_id)\
            .order("import_date", desc=True)\
            .limit(1)\
            .execute()
            
        if last_result.data:
            last_import = last_result.data[0]['import_date']
            
        return {
            'total_files': total_files,
            'total_transactions': total_transactions,
            'last_import': last_import
        }
    except Exception as e:
        logger.error(f"Error getting import stats: {e}")
        return {'total_files': 0, 'total_transactions': 0, 'last_import': None}


def clear_import_history_supabase() -> bool:
    """Clear all import history for user."""
    try:
        user_id = get_user_id()
        if not user_id:
            return False
            
        supabase = get_supabase_client()
        
        result = supabase.table('import_history')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
            
        return True
    except Exception as e:
        logger.error(f"Error clearing import history: {e}")
        return False
