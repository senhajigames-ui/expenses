"""
CSV import and parsing logic.
Handles different bank CSV formats (RBC credit cards, RBC checking, WealthSimple).
"""


import pandas as pd
from datetime import datetime
import streamlit as st
from logic.categorization import categorize_transaction_unified


def detect_csv_format(df, filename):
    """
    Detect CSV format based on columns.
    
    Args:
        df: DataFrame
        filename: Original filename
        
    Returns:
        tuple: (csv_type, card_type, date_col, desc_col, amount_col, txn_code_col)
    """
    filename_upper = filename.upper()
    
    # Create lowercase column mapping for case-insensitive matching
    # Create lowercase column mapping for case-insensitive matching
    col_lower_map = {}
    for col in df.columns:
        lower_col = col.lower()
        col_lower_map[lower_col] = col
        # Add aliases
        if lower_col == "transaction date":
            col_lower_map["date"] = col
        elif lower_col == "description 1":
            col_lower_map["description"] = col
        elif lower_col == "cad$":
            col_lower_map["amount"] = col
    
    
    # Check most specific formats first!
    
    # RBC Checking format (MOST SPECIFIC - has 'transaction' column)
    if "transaction" in col_lower_map and "description" in col_lower_map and "amount" in col_lower_map and "date" in col_lower_map:
        # RBC Checking is typically MM/DD/YYYY
        return "checking", "Checking", col_lower_map["date"], col_lower_map["description"], col_lower_map["amount"], col_lower_map["transaction"], "%m/%d/%Y"
    
    # WealthSimple format (SPECIFIC - has 'transaction_date' and 'type')
    elif "transaction_date" in col_lower_map and "details" in col_lower_map and "amount" in col_lower_map and "type" in col_lower_map:
        # WealthSimple is YYYY-MM-DD
        return "wealthsimple", "WealthSimple", col_lower_map["transaction_date"], col_lower_map["details"], col_lower_map["amount"], col_lower_map["type"], "%Y-%m-%d"
    
    # RBC Credit Card format (GENERIC - only has basic columns)
    elif "description" in col_lower_map and "amount" in col_lower_map and "date" in col_lower_map:
        card_type = "Cobalt" if "AMEX" in filename_upper or "COBALT" in filename_upper else "Visa"
        # RBC Credit is typically MM/DD/YYYY or YYYY-MM-DD depending on user settings, but MM/DD/YYYY is standard download
        # If ambiguous, we default to MM/DD/YYYY (US/Canada standard)
        return "creditcard", card_type, col_lower_map["date"], col_lower_map["description"], col_lower_map["amount"], None, "%m/%d/%Y"
    
    return None, None, None, None, None, None, None


def parse_csv_transactions(uploaded_file, custom_rules=None):
    """
    Parse CSV file and extract transactions.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        custom_rules: Custom merchant rules dict (optional)
        
    Returns:
        list: List of transaction dictionaries
    """
    if custom_rules is None:
        custom_rules = {}
    
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read CSV: {e}")
        return []
    
    filename = uploaded_file.name.upper()
    
    # Detect format
    csv_type, card_type, date_col, desc_col, amount_col, txn_code_col, date_fmt = detect_csv_format(df, filename)
    
    if not csv_type:
        st.error("Unknown CSV format")
        return []
    
    # Show preview
    with st.expander("Preview", expanded=False):
        preview_cols = [date_col, desc_col, amount_col]
        if txn_code_col:
            preview_cols.insert(1, txn_code_col)
        st.dataframe(df[preview_cols].head(5), width="stretch")
    
    transactions = []
    
    for idx, row in df.iterrows():
        try:
            amount_raw = float(str(row[amount_col]).replace('$', '').replace(',', '').strip())
            
            # Parse date safely with explicit format if available
            try:
                if date_fmt:
                    dt_obj = pd.to_datetime(row[date_col], format=date_fmt)
                else:
                    # Fallback to smart parsing (preferring Month-First for North America)
                    dt_obj = pd.to_datetime(row[date_col], dayfirst=False)
                    
                formatted_date = dt_obj.strftime("%Y-%m-%d")
                month = dt_obj.strftime("%Y-%m")
            except Exception as e:
                # If Strict parsing fails, try fallback
                if date_fmt:
                    try:
                         # Retry without strict format (maybe user has different settings)
                         dt_obj = pd.to_datetime(row[date_col], dayfirst=False)
                         formatted_date = dt_obj.strftime("%Y-%m-%d")
                         month = dt_obj.strftime("%Y-%m")
                    except:
                        continue
                else:
                    continue
            
            description = str(row[desc_col]).strip()
            is_negative = amount_raw < 0
            
            # Get transaction code using the column name from format detection
            if txn_code_col and txn_code_col in df.columns:
                transaction_code = str(row[txn_code_col]).strip()
            else:
                transaction_code = ""
            
            # WealthSimple-specific pre-categorization
            # This ensures correct transaction type detection
            if csv_type == "wealthsimple":
                ws_type = transaction_code.upper()
                desc_upper = description.upper()
                
                # Income detection (negative amount = money IN)
                if is_negative:
                    if any(kw in desc_upper for kw in ["PAYROLL", "SALARY", "PAY", "DEPOSIT"]):
                        category, txn_type = "Income - Salary", "income"
                    elif any(kw in desc_upper for kw in ["CASHBACK", "CASH BACK", "REFUND"]):
                        category, txn_type = "Income - Cashback", "income"
                    elif "INTEREST" in desc_upper or "INT" in desc_upper:
                        category, txn_type = "Income - Interest", "income"
                    elif "INTERAC E-TRANSFER" in desc_upper and "RECEIVED" in desc_upper:
                        category, txn_type = "Other", "income"
                    else:
                        # Negative amount but not recognized income = likely refund
                        category, txn_type = categorize_transaction_unified(
                            description=description,
                            amount=abs(amount_raw),
                            is_negative=is_negative,
                            custom_rules=custom_rules,
                            transaction_code=transaction_code
                        )
                
                # Payment detection (positive amount = money OUT)
                elif any(kw in desc_upper for kw in ["AMEX", "CREDIT CARD", "CC PAYMENT", "VISA", "MASTERCARD"]):
                    category, txn_type = "Payment", "payment"
                
                # Transfer detection
                elif any(kw in desc_upper for kw in ["TFSA", "FHSA", "TAX-FREE", "FIRST HOME"]):
                    category, txn_type = "TFSA/FHSA", "transfer"
                
                # Morocco transfer (by amount or keyword)
                elif abs(amount_raw) == 75 or "MOROCCO" in desc_upper:
                    category, txn_type = "Morocco", "transfer"
                
                # Interac e-Transfer Out (expense)
                elif "INTERAC E-TRANSFER" in desc_upper and "OUT" in desc_upper:
                    category, txn_type = "Other", "expense"
                
                # Interac e-Transfer Received (income)
                elif "INTERAC E-TRANSFER" in desc_upper and "RECEIVED" in desc_upper:
                    category, txn_type = "Other", "income"
                
                # Regular expense (positive amount, not payment/transfer)
                else:
                    category, txn_type = categorize_transaction_unified(
                        description=description,
                        amount=abs(amount_raw),
                        is_negative=is_negative,
                        custom_rules=custom_rules,
                        transaction_code=transaction_code
                    )
            else:
                # Use unified categorization for non-WealthSimple
                category, txn_type = categorize_transaction_unified(
                    description=description,
                    amount=abs(amount_raw),
                    is_negative=is_negative,
                    custom_rules=custom_rules,
                    transaction_code=transaction_code
                )
            
            # Skip ignored transactions
            if txn_type == "ignore":
                continue
            
            # Handle expense splitting for rent/insurance/utilities (checking only)
            actual_amount = abs(amount_raw)
            if csv_type == "checking":
                if category == "Rent":
                    actual_amount = actual_amount / 2
                elif category in ["Insurance", "Utilities"]:
                    actual_amount = actual_amount / 4
            
            transactions.append({
                "date": formatted_date,
                "description": description,
                "amount": actual_amount,
                "is_negative": is_negative,
                "month": month,
                "card": card_type,
                "transaction_type": txn_type,
                "transaction_code": transaction_code,
                "category": category
            })
                
        except Exception as e:
            continue
    
    return transactions


def process_transactions_batch(transactions, conn, custom_rules):
    """
    Process and categorize a batch of transactions.
    
    Args:
        transactions: List of transaction dictionaries
        conn: Database connection
        custom_rules: Custom merchant rules
        
    Returns:
        tuple: (processed_count, skipped_count, errors)
    """
    from database.transaction_operations import add_transaction
    from logic.categorization import categorize_transaction_unified
    
    processed = 0
    skipped = 0
    errors = []
    
    for txn in transactions:
        try:
            # Re-categorize if needed (shouldn't happen but safe fallback)
            if txn.get('category') is None:
                category, txn_type = categorize_transaction_unified(
                    description=txn['description'],
                    amount=txn['amount'],
                    is_negative=txn.get('is_negative', False),
                    custom_rules=custom_rules,
                    transaction_code=txn.get('transaction_code', '')
                )
                txn['category'] = category
                txn['transaction_type'] = txn_type
            
            # Add to database
            if add_transaction(
                conn,
                txn['date'],
                txn['description'],
                txn['amount'],
                txn['category'],
                f"{txn['card']} CSV Import",
                txn['month'],
                txn['card'],
                txn['transaction_type'],
                txn.get('transaction_code', '')
            ):
                processed += 1
            else:
                skipped += 1
                
        except Exception as e:
            errors.append(f"Error: {str(e)}")
            skipped += 1
    
    return processed, skipped, errors