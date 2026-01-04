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
    # Groceries
    "LOBLAWS": "Groceries",
    "NO FRILLS": "Groceries",
    "METRO": "Groceries",
    "SOBEYS": "Groceries",
    "LONGO": "Groceries",
    "FRESHCO": "Groceries",
    "VALU-MART": "Groceries",
    "RABBA": "Groceries",
    "FARM BOY": "Groceries",
    "WHOLE FOODS": "Groceries",
    "INSTACART": "Groceries",
    "COSTCO": "Groceries",
    "WALMART": "Groceries",
    
    # Dining / Fast Food
    "MCDONALD": "Dining/Restaurants",
    "BURGER KING": "Dining/Restaurants",
    "SUBWAY": "Dining/Restaurants",
    "TIM HORTONS": "Dining/Restaurants",
    "STARBUCKS": "Dining/Restaurants",
    "A&W": "Dining/Restaurants",
    "KFC": "Dining/Restaurants",
    "POPEYES": "Dining/Restaurants",
    "DOMINO": "Dining/Restaurants",
    "PIZZA": "Dining/Restaurants",
    "UBER EATS": "Dining/Restaurants",
    "SKIPTHEDISHES": "Dining/Restaurants",
    "DOORDASH": "Dining/Restaurants",
    "CHIPOTLE": "Dining/Restaurants",
    "KEG": "Dining/Restaurants",
    "CACTUS CLUB": "Dining/Restaurants",
    
    # Transportation
    "UBER": "Transportation",
    "LYFT": "Transportation",
    "PRESTO": "Transportation",
    "GO TRANSIT": "Transportation",
    "UP EXPRESS": "Transportation",
    "TTC": "Transportation",
    "PARKING": "Transportation",
    "GREEN P": "Transportation",
    "IMPARK": "Transportation",
    
    # Gas
    "ESSO": "Gas/Fuel",
    "SHELL": "Gas/Fuel",
    "PETRO": "Gas/Fuel",
    "CANADIAN TIRE GAS": "Gas/Fuel",
    "MOBIL": "Gas/Fuel",
    
    # Shopping / Retail
    "AMAZON": "Shopping/Retail",
    "APPLE": "Shopping/Retail",
    "DOLLARAMA": "Shopping/Retail",
    "CANADIAN TIRE": "Shopping/Retail",
    "WINNERS": "Shopping/Retail",
    "MARSHALLS": "Shopping/Retail",
    "HUDSON": "Shopping/Retail",
    "UNIQLO": "Shopping/Retail",
    "ZARA": "Shopping/Retail",
    "H&M": "Shopping/Retail",
    "IKEA": "Shopping/Retail",
    "BEST BUY": "Shopping/Retail",
    "LCBO": "Shopping/Retail",
    "BEER STORE": "Shopping/Retail",
    
    # Health
    "SHOPPERS DRUG MART": "Health/Wellness",
    "REXALL": "Health/Wellness",
    "GOODLIFE": "Health/Wellness",
    "GYM": "Health/Wellness",
    
    # Subscriptions
    "NETFLIX": "Subscriptions",
    "SPOTIFY": "Subscriptions",
    "DISNEY": "Subscriptions",
    "PRIME MEMBER": "Subscriptions",
    "APPLE.COM/BILL": "Subscriptions",
    "GOOGLE DAZI": "Subscriptions",
    "YOUTUBE": "Subscriptions"
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