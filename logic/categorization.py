"""
Transaction Categorization Engine
Handles rule-based transaction categorization with priority hierarchy.

Priority Order:
1. Checking account specific rules (hardcoded)
2. Custom user rules (database)
3. Merchant patterns (config)
4. WealthSimple stock tickers
5. Fallback: "Other" / expense
"""

import logging
import time
from typing import Tuple, List, Dict, Optional
from config import (
    WS_TICKERS, MERCHANT_PATTERNS, 
    EXPENSE_CATEGORIES, INCOME_CATEGORIES, 
    TRANSFER_CATEGORIES, PAYMENT_CATEGORIES
)

logger = logging.getLogger(__name__)


class CategorizationEngine:
    """
    Main categorization engine using strategy pattern.
    Encapsulates all categorization logic in one place.
    """
    
    def __init__(self, custom_rules: Dict[str, str] = None):
        """
        Initialize categorization engine.
        
        Args:
            custom_rules: Dictionary of merchant -> category mappings from database
        """
        self.custom_rules = custom_rules or {}
        
        # Cache sorted merchant patterns for performance (sort once, not on every call)
        self._sorted_patterns = sorted(
            MERCHANT_PATTERNS.items(), 
            key=lambda x: len(x[0]), 
            reverse=True
        )
    
    
    def categorize(
        self, 
        description: str, 
        amount: float, 
        is_negative: bool,
        transaction_code: str = None
    ) -> Tuple[str, str]:
        """
        Categorize a transaction using priority hierarchy.
        
        Args:
            description: Transaction description
            amount: Transaction amount
            is_negative: Whether amount is negative
            transaction_code: Bank transaction code (AFTOUT, AFTIN, etc.)
        
        Returns:
            Tuple of (category, transaction_type)
        """
        desc_upper = description.upper()
        
        # Priority 1: Checking account rules
        result = self._check_account_rules(desc_upper, amount, transaction_code)
        if result:
            return result
        
        # Priority 2: Custom rules
        result = self._check_custom_rules(description)
        if result:
            return result
        
        # Priority 3: Merchant patterns
        result = self._check_merchant_patterns(desc_upper)
        if result:
            return result
        
        # Priority 4: WealthSimple tickers
        result = self._check_ws_tickers(desc_upper)
        if result:
            return result
            
        # Priority 5: Smart Fallback (Generic keywords)
        result = self._check_smart_fallback(desc_upper)
        if result:
            return result
        
        # Priority 6: Final Fallback
        return "Other", "expense"
    
    
    def _check_account_rules(
        self, 
        desc_upper: str, 
        amount: float, 
        txn_code: str
    ) -> Optional[Tuple[str, str]]:
        """
        Universal checking account rules based on keywords and patterns.
        Works for any bank by analyzing description content.
        """
        
        # INCOME DETECTION (keywords that indicate money coming in)
        income_keywords = {
            'salary': ["SALARY", "PAY", "PAYROLL", "DEPOSIT", "DIRECT DEPOSIT", "OPERATION", "EMPLOYMENT"],
            'interest': ["INTEREST", "INT PAID"],
            'cashback': ["CASHBACK", "CASH BACK", "REWARD"],
            'refund': ["REFUND", "RETURN", "REIMBURSEMENT"]
        }
        
        for income_type, keywords in income_keywords.items():
            if any(kw in desc_upper for kw in keywords):
                if income_type == 'salary':
                    return "Income - Salary", "income"
                elif income_type == 'interest':
                    return "Income - Interest", "income"
                elif income_type == 'cashback':
                    return "Income - Cashback", "income"
                elif income_type == 'refund':
                    return "Income - Other", "income"
        
        # INTERAC E-TRANSFER DETECTION (handle various formats)
        interac_keywords = ["INTERAC", "E-TRANSFER", "E-TRF", "ETRANSFER"]
        if any(kw in desc_upper for kw in interac_keywords):
            # Check direction
            received_keywords = ["RECEIVED", "FROM", "RCVD", "DEPOSIT"]
            sent_keywords = ["SENT", "OUT", "PAYMENT"]
            
            if any(kw in desc_upper for kw in received_keywords):
                return "Other", "income"
            elif any(kw in desc_upper for kw in sent_keywords):
                return "Other", "expense"
        
        # TRANSFER DETECTION (money moving between your own accounts)
        transfer_keywords = ["TFSA", "FHSA", "TAX-FREE", "FIRST HOME", "SAVINGS", "INVESTMENT"]
        if any(kw in desc_upper for kw in transfer_keywords):
            # Determine specific transfer type
            if "TFSA" in desc_upper or "FHSA" in desc_upper:
                return "TFSA/FHSA", "transfer"
            else:
                return "Other Transfer", "transfer"
        
        # Amount-based transfer detection (for recurring transfers)
        if 10 <= amount <= 30:
            if any(kw in desc_upper for kw in ["TRANSFER", "TRF"]):
                return "TFSA/FHSA", "transfer"
        elif amount == 50:
            if any(kw in desc_upper for kw in ["TRANSFER", "TRF", "EMERGENCY"]):
                return "Emergency Fund", "transfer"
        elif amount == 75:
            if any(kw in desc_upper for kw in ["TRANSFER", "TRF", "MOROCCO"]):
                return "Morocco", "transfer"
        
        # PAYMENT DETECTION (paying off credit cards)
        payment_keywords = ["AMEX", "VISA", "MASTERCARD", "CREDIT CARD", "CC PAYMENT", "CARD PAYMENT"]
        if any(kw in desc_upper for kw in payment_keywords):
            return "Payment", "payment"
        
        # EXPENSE DETECTION (specific categories)
        expense_patterns = {
            "Rent": ["RENT", "BAYTREE", "APARTMENT", "LANDLORD"],
            "Insurance": ["INSURANCE", "COOPERATORS"],
            "Utilities": ["UTILITIES", "UTILITY", "METERGY", "HYDRO", "ELECTRIC", "GAS BILL", "WATER"]
        }
        
        for category, keywords in expense_patterns.items():
            if any(kw in desc_upper for kw in keywords):
                return category, "expense"
        
        # If we have a transaction code, use it as a hint
        if txn_code:
            txn_code_clean = txn_code.upper().strip().replace('_', '')
            
            # Generic income codes
            if any(code in txn_code_clean for code in ["AFTIN", "CREDIT", "DEP", "DEPOSIT"]):
                return "Income - Other", "income"
            
            # Generic transfer codes
            if any(code in txn_code_clean for code in ["TRF", "TRANSFER", "XFER"]):
                return "Other Transfer", "transfer"
        
        return None
    
    
    def _check_custom_rules(self, description: str) -> Optional[Tuple[str, str]]:
        """Check user-defined custom rules (case-insensitive)."""
        merchant = MerchantExtractor.extract(description)
        
        # Case-insensitive lookup
        for rule_merchant, category in self.custom_rules.items():
            if rule_merchant.upper() == merchant.upper():
                return category, self._get_transaction_type(category)
        
        return None
    
    
    def _check_merchant_patterns(self, desc_upper: str) -> Optional[Tuple[str, str]]:
        """
        Check predefined merchant patterns.
        Uses cached sorted patterns for performance.
        Example: Matches 'UBER EATS' (Dining) before 'UBER' (Transport).
        """
        # Use pre-sorted cached patterns (sorted once in __init__)
        for pattern, category in self._sorted_patterns:
            if pattern.upper() in desc_upper:
                return category, self._get_transaction_type(category)
        
        return None
    
    
    def _check_ws_tickers(self, desc_upper: str) -> Optional[Tuple[str, str]]:
        """Check WealthSimple stock tickers."""
        for ticker in WS_TICKERS:
            if ticker in desc_upper:
                return "Investment", "expense"
        
        return None
    
    

    
    
    def _check_smart_fallback(self, desc_upper: str) -> Optional[Tuple[str, str]]:
        """
        Smart fallback based generic generic keywords when no specific merchant matches.
        """
        keywords = {
            "GROCERY": "Groceries",
            "MARKET": "Groceries",
            "FOOD": "Groceries",
            "RESTAURANT": "Dining/Restaurants",
            "CAFE": "Dining/Restaurants",
            "COFFEE": "Dining/Restaurants",
            "BAR": "Dining/Restaurants",
            "PUB": "Dining/Restaurants",
            "KITCHEN": "Dining/Restaurants",
            "PIZZERIA": "Dining/Restaurants",
            "GAS": "Gas/Fuel",
            "FUEL": "Gas/Fuel",
            "PETRO": "Gas/Fuel",
            "PARKING": "Transportation",
            "TRANSIT": "Transportation",
            "TAXI": "Transportation",
            "MOBILE": "Bills/Utilities",
            "WIRELESS": "Bills/Utilities",
            "HYDRO": "Utilities",
            "ENERGY": "Utilities",
            "PHARMACY": "Health/Wellness",
            "DRUG": "Health/Wellness",
            "FITNESS": "Health/Wellness",
            "DONATION": "Donations/Charity",
            "CHARITY": "Donations/Charity"
        }
        
        for kw, category in keywords.items():
            if kw in desc_upper:
                return category, self._get_transaction_type(category)
        
        return None


    def _get_transaction_type(self, category: str) -> str:
        """Map category to transaction type."""
        if category in INCOME_CATEGORIES:
            return "income"
        elif category in TRANSFER_CATEGORIES:
            return "transfer"
        elif category in PAYMENT_CATEGORIES:
            return "payment"
        else:
            return "expense"


class MerchantExtractor:
    """Extract merchant names from transaction descriptions."""
    
    NOISE_PATTERNS = [
        "STORE #", " - ", "LOCATION", "BRANCH", 
        "POS", "PURCHASE", "#", "  "
    ]
    
    # Common merchant abbreviations and variations
    MERCHANT_ALIASES = {
        "AMAZN": "AMAZON",
        "AMZ": "AMAZON",
        "MKTP": "MARKETPLACE",
        "WM": "WALMART",
        "CSTCO": "COSTCO",
        "MCDONALDS": "MCDONALD",
        "TIMS": "TIM HORTONS",
        "SQ *": "SQUARE",  # Square payment processor
        "TST*": "TOAST",   # Toast POS
    }
    
    @staticmethod
    def extract(description: str) -> str:
        """
        Extract clean merchant name with improved fuzzy matching.
        
        Args:
            description: Raw transaction description
        
        Returns:
            Cleaned merchant name (1-3 words)
        """
        desc = description.upper().strip()
        
        # Normalize common aliases first
        for abbrev, full_name in MerchantExtractor.MERCHANT_ALIASES.items():
            if abbrev in desc:
                desc = desc.replace(abbrev, full_name)
        
        # Remove noise
        for pattern in MerchantExtractor.NOISE_PATTERNS:
            if pattern in desc:
                desc = desc.split(pattern)[0]
        
        # Filter meaningful words
        words = [
            w for w in desc.split() 
            if not w.isdigit() and len(w) >= 2
        ]
        
        # Return 1-3 words (increased from 1-2 for better context)
        if len(words) >= 3:
            return " ".join(words[:3])
        elif len(words) >= 2:
            return " ".join(words[:2])
        elif words:
            return words[0]
        
        return description.strip()





# Public API Functions (for backwards compatibility)

def categorize_transaction_unified(
    description: str,
    amount: float,
    is_negative: bool,
    custom_rules: Dict[str, str],
    transaction_code: str = None
) -> Tuple[str, str]:
    """Legacy function for backwards compatibility."""
    engine = CategorizationEngine(custom_rules)
    return engine.categorize(description, amount, is_negative, transaction_code)


def extract_merchant_name(description: str) -> str:
    """Legacy function for backwards compatibility."""
    return MerchantExtractor.extract(description)





def batch_categorize_transactions(transactions, custom_rules):
    """
    Efficiently batch categorize transactions.
    
    Args:
        transactions: list of dicts with 'description', 'amount', etc.
        custom_rules: dict merchant -> category
        
    Returns:
        list of tuples (category, transaction_type)
    """
    # Create engine ONCE and reuse for all transactions (major performance improvement)
    engine = CategorizationEngine(custom_rules)
    results = []
    
    for txn in transactions:
        desc = txn['description']
        amount = txn['amount']
        is_neg = txn.get('is_negative', False)
        txn_code = txn.get('transaction_code', '')
        
        # Categorize using shared engine instance
        res = engine.categorize(desc, amount, is_neg, txn_code)
        results.append(res)
                
    return results
