"""
User management database operations.
Handles user creation, deletion, and retrieval.
"""

import sqlite3
from datetime import datetime


def get_all_users():
    """
    Get list of all usernames.
    
    Returns:
        list: List of username strings
    """
    conn = None
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT username FROM users ORDER BY username")
        users = [row[0] for row in c.fetchall()]
        return users
    except sqlite3.Error as e:
        print(f"Database error in get_all_users: {e}")
        return []
    finally:
        if conn:
            conn.close()


def add_user(username):
    """
    Add a new user to the system.
    
    Args:
        username: Username to create
        
    Returns:
        bool: True if user created, False if username already exists
    """
    conn = None
    try:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (username, created_date) VALUES (?, ?)",
            (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Username already exists
        return False
    except sqlite3.Error as e:
        print(f"Database error in add_user: {e}")
        return False
    finally:
        if conn:
            conn.close()


def delete_user(username):
    """
    Delete a user and their associated database.
    
    Args:
        username: Username to delete
    """
    import os
    
    conn = None
    try:
        # Delete from users.db
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        
        # Delete user's database file
        from database.db_manager import delete_user_database
        delete_user_database(username)
        
    except sqlite3.Error as e:
        print(f"Database error in delete_user: {e}")
    finally:
        if conn:
            conn.close()