"""
Business Logic Package

This package contains core business logic:
- categorization: AI-powered transaction categorization engine
- csv_import: CSV file parsing and import logic
"""

from .categorization import (
    CategorizationEngine,
    MerchantExtractor,
    RuleManager,
    categorize_transaction_unified,
    extract_merchant_name,
    auto_create_rule,
    batch_categorize_transactions
)
from .csv_import import (
    detect_csv_format,
    parse_csv_transactions,
    process_transactions_batch
)

__all__ = [
    # Categorization
    'CategorizationEngine',
    'MerchantExtractor',
    'RuleManager',
    'categorize_transaction_unified',
    'extract_merchant_name',
    'auto_create_rule',
    'batch_categorize_transactions',
    # CSV Import
    'detect_csv_format',
    'parse_csv_transactions',
    'process_transactions_batch'
]
