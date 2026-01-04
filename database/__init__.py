"""
Database Operations Package

This package contains all database-related operations:
- db_manager: Database initialization and connection management
- transaction_operations: Transaction CRUD operations
- budget_operations: Budget and merchant rules operations
- user_operations: User management
- import_history: Import tracking and duplicate detection
"""

from .db_manager import init_users_db, init_db
from .transaction_operations import (
    get_transactions, 
    add_transaction, 
    bulk_add_transactions,
    delete_transaction,
    clear_all_transactions,
    check_duplicates
)
from .budget_operations import load_merchant_rules
from .user_operations import get_all_users, add_user, delete_user
from .import_history import (
    calculate_file_hash,
    check_file_already_imported,
    record_file_import,
    clear_import_history
)

__all__ = [
    # Database initialization
    'init_users_db',
    'init_db',
    # Transaction operations
    'get_transactions',
    'add_transaction',
    'bulk_add_transactions',
    'delete_transaction',
    'clear_all_transactions',
    'check_duplicates',
    # Budget operations
    'load_merchant_rules',
    # User operations
    'get_all_users',
    'add_user',
    'delete_user',
    # Import history
    'calculate_file_hash',
    'check_file_already_imported',
    'record_file_import',
    'clear_import_history'
]
