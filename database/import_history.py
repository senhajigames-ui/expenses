"""
Import history tracking operations.
Prevents duplicate file imports and maintains import logs.
"""

import sqlite3
import hashlib
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA-256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()


def check_file_already_imported(conn: sqlite3.Connection, filename: str, file_hash: str) -> bool:
    """
    Check if a file has already been imported.
    
    Args:
        conn: Database connection
        filename: Name of the file
        file_hash: SHA-256 hash of file content
        
    Returns:
        bool: True if file was already imported
    """
    try:
        c = conn.cursor()
        c.execute("""
            SELECT COUNT(*) FROM import_history 
            WHERE filename = ? AND file_hash = ?
        """, (filename, file_hash))
        
        return c.fetchone()[0] > 0
    except sqlite3.Error as e:
        logger.warning(f"Error checking import history: {e}")
        return False


def record_file_import(
    conn: sqlite3.Connection, 
    filename: str, 
    file_hash: str, 
    transactions_imported: int
) -> bool:
    """
    Record a file import in the history.
    
    Args:
        conn: Database connection
        filename: Name of the file
        file_hash: SHA-256 hash of file content
        transactions_imported: Number of transactions imported
        
    Returns:
        bool: True if recorded successfully
    """
    try:
        c = conn.cursor()
        c.execute("""
            INSERT INTO import_history (filename, import_date, transactions_imported, file_hash)
            VALUES (?, datetime('now'), ?, ?)
        """, (filename, transactions_imported, file_hash))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.warning(f"Error recording import: {e}")
        return False


def get_import_history(conn: sqlite3.Connection, limit: int = 10) -> List[Dict]:
    """
    Get recent import history.
    
    Args:
        conn: Database connection
        limit: Maximum number of records to return
        
    Returns:
        List of import history dictionaries
    """
    try:
        c = conn.cursor()
        c.execute("""
            SELECT filename, import_date, transactions_imported 
            FROM import_history 
            ORDER BY import_date DESC 
            LIMIT ?
        """, (limit,))
        
        rows = c.fetchall()
        return [
            {
                'filename': row[0],
                'import_date': row[1],
                'transactions_imported': row[2]
            }
            for row in rows
        ]
    except sqlite3.Error as e:
        logger.warning(f"Error getting import history: {e}")
        return []


def get_import_stats(conn: sqlite3.Connection) -> Dict:
    """
    Get import statistics.
    
    Returns:
        Dictionary with import stats
    """
    try:
        c = conn.cursor()
        
        # Total files imported
        c.execute("SELECT COUNT(*) FROM import_history")
        total_files = c.fetchone()[0]
        
        # Total transactions imported
        c.execute("SELECT SUM(transactions_imported) FROM import_history")
        total_transactions = c.fetchone()[0] or 0
        
        # Last import date
        c.execute("SELECT MAX(import_date) FROM import_history")
        last_import = c.fetchone()[0]
        
        return {
            'total_files': total_files,
            'total_transactions': total_transactions,
            'last_import': last_import
        }
    except sqlite3.Error as e:
        logger.warning(f"Error getting import stats: {e}")
        return {
            'total_files': 0,
            'total_transactions': 0,
            'last_import': None
        }


def clear_import_history(conn: sqlite3.Connection) -> bool:
    """
    Clear all import history records.
    
    Args:
        conn: Database connection
        
    Returns:
        bool: True if cleared successfully
    """
    try:
        c = conn.cursor()
        c.execute("DELETE FROM import_history")
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.warning(f"Error clearing import history: {e}")
        return False
