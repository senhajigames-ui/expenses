"""
Database initialization and connection management.
Handles database setup, table creation, and connection pooling.
"""

import sqlite3
import os


def init_users_db():
    """Initialize the central users database."""
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            created_date TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def init_db(username):
    """
    Initialize user-specific expense database.
    
    Args:
        username: Username for the database
        
    Returns:
        sqlite3.Connection: Database connection object
    """
    # Sanitize username to prevent directory traversal
    safe_username = "".join(c for c in username if c.isalnum() or c in ('-', '_'))
    if not safe_username:
        raise ValueError("Invalid username")
        
    conn = sqlite3.connect(f"{safe_username}_expenses.db")
    c = conn.cursor()
    
    # Transactions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            amount REAL,
            category TEXT,
            source TEXT,
            processed_date TEXT,
            is_refund INTEGER DEFAULT 0,
            month TEXT,
            card TEXT,
            transaction_type TEXT,
            transaction_code TEXT
        )
    """)
    
    # Merchant rules table
    c.execute("""
        CREATE TABLE IF NOT EXISTS merchant_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_pattern TEXT UNIQUE,
            category TEXT
        )
    """)
    
    # Budgets table
    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE,
            monthly_budget REAL
        )
    """)
    
    # Import history table
    c.execute("""
        CREATE TABLE IF NOT EXISTS import_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            import_date TEXT NOT NULL,
            transactions_imported INTEGER,
            file_hash TEXT,
            UNIQUE(filename, file_hash)
        )
    """)
    
    conn.commit()
    return conn


def delete_user_database(username):
    """
    Delete user's database file.
    
    Args:
        username: Username whose database to delete
    """
    db_file = f"{username}_expenses.db"
    if os.path.exists(db_file):
        os.remove(db_file)