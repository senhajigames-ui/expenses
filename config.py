"""
Configuration file for Expense Tracker application.
Contains all constants, categories, and patterns used throughout the app.
"""

import os

# Database Configuration
USERS_DB = "users.db"

# WealthSimple Stock Tickers
WS_TICKERS = [
    "AMD", "AEM", "CNQ", "LRCX", "TSM", "ASML", "ADBE", "CCO", 
    "REGN", "CEG", "BTCX", "PLD", "WCN", "KILO", "GILD", "SNPS"
]

# Transaction Categories
EXPENSE_CATEGORIES = [
    "Groceries", "Dining/Restaurants", "Transportation", "Bills/Utilities",
    "Entertainment", "Shopping/Retail", "Health/Wellness", "Donations/Charity",
    "Soccer", "Education", "Personal Care", "Gas/Fuel", "Subscriptions",
    "Other", "Rent", "Insurance", "Utilities", "Investment"
]

FIXED_EXPENSE_CATEGORIES = [
    "Rent", "Bills/Utilities", "Insurance", "Subscriptions", "Education", "Utilities"
]

INCOME_CATEGORIES = [
    "Income - Salary", "Income - Cashback", "Income - Interest", "Income - Other"
]

TRANSFER_CATEGORIES = [
    "TFSA/FHSA",
    "Morocco"
]

PAYMENT_CATEGORIES = [
    "Payment"
]

# Combined categories list (for backwards compatibility)
CATEGORIES = (
    EXPENSE_CATEGORIES + 
    INCOME_CATEGORIES + 
    TRANSFER_CATEGORIES + 
    PAYMENT_CATEGORIES
)

# Transaction Type Mappings
TRANSACTION_TYPES = {
    "income": INCOME_CATEGORIES,
    "expense": EXPENSE_CATEGORIES,
    "transfer": TRANSFER_CATEGORIES,
    "payment": PAYMENT_CATEGORIES
}

# Merchant Pattern Matching
MERCHANT_PATTERNS = {
    "CHIPOTLE": "Dining/Restaurants",
    "WALMART": "Groceries",
    "COSTCO": "Groceries",
    "UBER": "Transportation",
    "NETFLIX": "Subscriptions",
    "SPOTIFY": "Subscriptions",
    "AMAZON": "Shopping/Retail",
    "TIM HORTONS": "Dining/Restaurants",
    "STARBUCKS": "Dining/Restaurants",
    "ESSO": "Gas/Fuel",
    "SHELL": "Gas/Fuel",
    "PETRO": "Gas/Fuel"
}

# Validation Rules
MIN_TRANSACTION_AMOUNT = 0.01
MAX_TRANSACTION_AMOUNT = 999999.99
MAX_DESCRIPTION_LENGTH = 200

# UI Configuration
DEFAULT_CURRENCY = "CAD"
CURRENCY_SYMBOL = "$"
DATE_FORMAT = "%Y-%m-%d"
MONTH_FORMAT = "%Y-%m"