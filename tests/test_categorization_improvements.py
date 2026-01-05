#!/usr/bin/env python3
"""
Quick test to demonstrate categorization improvements.
Shows before/after behavior for common edge cases.
"""

import sys
sys.path.insert(0, '.')

from logic.categorization import CategorizationEngine, MerchantExtractor

def test_improvements():
    print("🧪 Testing Categorization Improvements\n")
    print("=" * 60)
    
    # Test 1: Merchant Extraction with Aliases
    print("\n1️⃣  Merchant Extraction (with fuzzy matching)")
    print("-" * 60)
    test_descriptions = [
        "AMAZN MKTP CA",
        "CSTCO WHOLESALE #123",
        "TIMS #4567",
        "SBUX STORE 890"
    ]
    
    for desc in test_descriptions:
        merchant = MerchantExtractor.extract(desc)
        print(f"   '{desc}' → '{merchant}'")
    
    # Test 2: Interac E-Transfer Edge Cases
    print("\n2️⃣  Interac E-Transfer Detection")
    print("-" * 60)
    engine = CategorizationEngine({})
    
    interac_tests = [
        ("INTERAC E-TRANSFER RECEIVED FROM JOHN", "Should be income"),
        ("INTERAC E-TRF- RCVD", "Should be income (abbreviation)"),
        ("INTERAC E-TRANSFER SENT TO JANE", "Should be expense"),
        ("INTERAC E-TRF- OUT", "Should be expense (abbreviation)")
    ]
    
    for desc, expected in interac_tests:
        category, txn_type = engine.categorize(desc, 50.0, False)
        status = "✅" if txn_type in expected.lower() else "❌"
        print(f"   {status} '{desc[:35]}...' → {txn_type}")
        print(f"      Expected: {expected}")
    
    # Test 3: Pattern Matching Performance
    print("\n3️⃣  Pattern Caching (performance)")
    print("-" * 60)
    
    import time
    
    # Simulate batch categorization
    test_txns = [
        {"description": f"UBER EATS ORDER #{i}", "amount": 25.0, "is_negative": False, "transaction_code": ""}
        for i in range(100)
    ]
    
    from logic.categorization import batch_categorize_transactions
    
    start = time.time()
    results = batch_categorize_transactions(test_txns, {})
    elapsed = time.time() - start
    
    print(f"   ✅ Categorized 100 transactions in {elapsed*1000:.2f}ms")
    print(f"   Average: {elapsed*10:.2f}ms per transaction")
    print(f"   All correctly categorized: {all(r[0] == 'Dining/Restaurants' for r in results)}")
    
    # Test 4: Smart Fallback (Generic Keywords)
    print("\n4️⃣  Smart Fallback (Generic Keywords)")
    print("-" * 60)
    
    fallback_tests = [
        ("LOCAL MARKET", "Groceries"),
        ("CORNER CAFE", "Dining/Restaurants"),
        ("SHELL GAS BAR", "Gas/Fuel"),
        ("CITY PARKING", "Transportation"),
        ("UNKNOWN VENDOR", "Other")  # Should still fall back to default
    ]
    
    for desc, expected_cat in fallback_tests:
        cat, _ = engine.categorize(desc, 10.0, False)
        status = "✅" if cat == expected_cat else "❌"
        print(f"   {status} '{desc}' → '{cat}'")
        if cat != expected_cat:
            print(f"      Expected: '{expected_cat}'")
            
    print("\n" + "=" * 60)
    print("✅ All tests completed!\n")

if __name__ == "__main__":
    test_improvements()
