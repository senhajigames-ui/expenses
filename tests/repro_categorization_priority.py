
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.categorization import CategorizationEngine, MerchantExtractor

def test_priority_conflict():
    print("🧪 Testing Categorization Priority...")
    
    # 1. Define a custom rule that conflicts with a hardcoded rule
    # Hardcoded rule: 'RENT' -> 'Rent' (Priority 1)
    # Custom rule: 'THE RENT SHOP' -> 'Shopping/Retail' (Priority 2)
    
    custom_rules = {
        "THE RENT SHOP": "Shopping/Retail"
    }
    
    engine = CategorizationEngine(custom_rules)
    
    # Description that triggers both
    description = "THE RENT SHOP" 
    
    # DEBUG: Check Extraction
    extracted = MerchantExtractor.extract(description)
    print(f"DEBUG: Extracted Merchant from '{description}' -> '{extracted}'")
    
    # Current behavior expectation:
    # 1. _check_account_rules sees "RENT" in description -> returns "Rent"
    # 2. _check_custom_rules is never reached (if bug exists)
    
    category, txn_type = engine.categorize(description, 100.0, True)
    
    print(f"Description: '{description}'")
    print(f"Custom Rule: 'RENT A CENTER' -> 'Shopping/Retail'")
    print(f"Result Category: '{category}'")
    
    if category == "Rent":
        print("❌ FAIL: Hardcoded 'Rent' rule overrode Custom Rule!")
        print("   (This confirms the priority inversion bug)")
    elif category == "Shopping/Retail":
        print("✅ PASS: Custom rule took precedence.")
    else:
        print(f"❓ Unexpected result: {category}")

def test_hardcoded_amounts():
    print("\n🧪 Testing Hardcoded Amounts...")
    engine = CategorizationEngine({})
    
    # Test the magic $75 Morocco rule
    cat, _ = engine.categorize("TRANSFER TO MOM", 75.0, True)
    print(f"Desc: 'TRANSFER TO MOM', Amount: $75.00 -> {cat}")
    
    if cat == "Morocco":
        print("❌ FAIL: Hardcoded $75 amount triggered 'Morocco' category (should be removed).")
    else:
        print(f"✅ PASS: Hardcoded amount ignored (Category: {cat})")

def test_keyword_safety():
    print("\n🧪 Testing Keyword Safety (Whole Word Matching)...")
    engine = CategorizationEngine({})
    
    # "PAYMENT" contains "PAY" -> Was triggering Salary
    # "RENT" is a substring of "RENTAL" -> Was triggering Rent
    
    test_cases = [
        ("CREDIT CARD PAYMENT", "Payment", "Should match Payment keyword, NOT Salary (PAY)"),
        ("RENTAL CAR", "Other", "Should NOT match Rent (RENT substring)"),
        ("PAYROLL DEPOSIT", "Income - Salary", "Should match Salary (PAYROLL)")
    ]
    
    for desc, expected, reason in test_cases:
        cat, _ = engine.categorize(desc, 50.0, True)
        print(f"Desc: '{desc}' -> {cat}")
        
        if cat == expected:
            print(f"✅ PASS: {reason}")
        else:
            print(f"❌ FAIL: Got '{cat}', Expected '{expected}'. Reason: {reason}")

if __name__ == "__main__":
    test_priority_conflict()
    test_hardcoded_amounts()
    test_keyword_safety()
