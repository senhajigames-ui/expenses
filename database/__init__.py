"""
Database Operations Package

This package exposes all database interactions for the application.
The backend is powered by Supabase.
"""

from .transaction_operations import (
    get_transactions, 
    add_transaction, 
    bulk_add_transactions,
    delete_transaction,
    clear_all_transactions,
    check_duplicates,
    update_transaction
)
from .budget_operations import (
    get_budgets,
    save_budget,
    load_merchant_rules,
    save_merchant_rule
)
from .import_history import (
    calculate_file_hash,
    check_file_already_imported,
    record_file_import,
    clear_import_history,
    get_import_history,
    get_import_stats
)

__all__ = [
    # Transaction operations
    'get_transactions',
    'add_transaction',
    'bulk_add_transactions',
    'delete_transaction',
    'clear_all_transactions',
    'check_duplicates',
    'update_transaction',
    
    # Budget operations
    'get_budgets',
    'save_budget',
    'load_merchant_rules',
    'save_merchant_rule',
    
    # Import history
    'calculate_file_hash',
    'check_file_already_imported',
    'record_file_import',
    'clear_import_history',
    'get_import_history',
    'get_import_stats'
]
