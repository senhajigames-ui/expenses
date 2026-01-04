"""
Transaction Updater - Manage Tab Component

This module handles all transaction update operations:
- Processing AG Grid changes
- Validating updates
- Creating merchant rules
- Finding and applying to similar transactions
- Bulk updates
- Delete operations
"""

import streamlit as st
import pandas as pd
import sqlite3
from typing import Dict, List, Tuple, Optional
from logic.categorization import extract_merchant_name, auto_create_rule
from config import (
    EXPENSE_CATEGORIES, INCOME_CATEGORIES, 
    TRANSFER_CATEGORIES, PAYMENT_CATEGORIES
)


class TransactionUpdater:
    """Handle transaction updates and bulk operations."""
    
    def __init__(self, conn):
        """Initialize with database connection."""
        self.conn = conn
    
    def process_aggrid_changes(
        self,
        original_df: pd.DataFrame,
        display_df: pd.DataFrame,
        grid_response: Dict,
        grid_key: str = "main"
    ):
        """
        Track changes from AG Grid without auto-saving.
        
        Args:
            original_df: The original DataFrame (with 'id', 'description', etc.)
            display_df: The DataFrame currently displayed in the grid
            grid_response: The response object from AG Grid
            grid_key: Unique key for this grid (to track multiple grids)
        """
        try:
            # Validate inputs
            if original_df is None or original_df.empty:
                return
            
            if display_df is None or display_df.empty:
                return
            
            # Initialize storage for this grid's initial state
            initial_state_key = f'grid_initial_state_{grid_key}'
            
            # Get current IDs from display_df
            current_ids = set()
            if 'ID' in display_df:
                # Handle potential non-numeric IDs safely
                current_ids = set(pd.to_numeric(display_df['ID'], errors='coerce').dropna().astype(int))
            
            # Get stored IDs
            stored_ids = set()
            if initial_state_key in st.session_state:
                stored_ids = set(st.session_state[initial_state_key].keys())
            
            # Re-initialize if keys don't match (filter changed) OR if key missing
            if initial_state_key not in st.session_state or stored_ids != current_ids:
                initial_state_dict = {}
                try:
                    for idx, row in display_df.iterrows():
                        # Safely get ID
                        if 'ID' not in row:
                            continue
                        
                        try:
                            txn_id = int(row['ID'])
                        except (ValueError, TypeError):
                            continue
                        
                        initial_state_dict[txn_id] = {
                            'Type': str(row.get('Type', 'expense')),
                            'Category': str(row.get('Category', 'Other'))
                        }
                    st.session_state[initial_state_key] = initial_state_dict
                except Exception as e:
                    st.error(f"Error initializing grid state: {e}")
                    return
            
            # Check grid response validity
            if not grid_response or not isinstance(grid_response, dict):
                # AgGridReturn object - access via attributes
                if hasattr(grid_response, 'data'):
                    grid_data = grid_response.data
                else:
                    return
            else:
                # Dict format
                if 'data' not in grid_response or grid_response['data'] is None:
                    return
                grid_data = grid_response['data']

            # Safely create DataFrame from grid data
            try:
                edited_data = pd.DataFrame(grid_data)
            except Exception as e:
                st.error(f"Error parsing grid data: {e}")
                return
            
            initial_state_dict = st.session_state.get(initial_state_key, {})
            
            # Compare with initial state to detect changes
            if not edited_data.empty:
                pending_changes = []
                validation_errors = []
                
                for idx, edited_row in edited_data.iterrows():
                    try:
                        # Safely get transaction ID
                        if 'ID' not in edited_row:
                            continue
                        
                        try:
                            txn_id = int(edited_row['ID'])
                        except (ValueError, TypeError):
                            continue
                        
                        # Get initial state for this transaction
                        if txn_id not in initial_state_dict:
                            continue
                        
                        initial_state = initial_state_dict[txn_id]
                        
                        # Safely get current values
                        current_type = str(edited_row.get('Type', 'expense'))
                        current_category = str(edited_row.get('Category', 'Other'))
                        
                        # Check for changes against initial state
                        type_changed = initial_state['Type'] != current_type
                        category_changed = initial_state['Category'] != current_category
                        
                        if type_changed or category_changed:
                            new_type = current_type
                            new_category = current_category
                            
                            # Validate category is not empty
                            if not new_category or new_category.strip() == '':
                                validation_errors.append(f"Transaction ID {txn_id}: Category cannot be empty")
                                continue
                            
                            # Validate category matches type
                            if not self._validate_category_type(new_category, new_type):
                                validation_errors.append(
                                    f"Transaction ID {txn_id}: Category '{new_category}' doesn't match type '{new_type}'"
                                )
                                continue
                            
                            # Get original transaction data safely
                            try:
                                matching_txns = original_df[original_df['id'] == txn_id]
                                if matching_txns.empty:
                                    st.warning(f"Transaction {txn_id} not found in original data")
                                    continue
                                
                                orig_txn = matching_txns.iloc[0]
                                description = str(orig_txn.get('description', ''))
                                
                            except Exception as e:
                                st.error(f"Error retrieving transaction {txn_id}: {e}")
                                continue
                            
                            pending_changes.append({
                                'txn_id': txn_id,
                                'description': description,
                                'new_type': new_type,
                                'new_category': new_category,
                                'type_changed': type_changed,
                                'category_changed': category_changed,
                                'grid_key': grid_key
                            })
                    
                    except Exception as e:
                        st.error(f"Error processing row {idx}: {e}")
                        continue
                
                # Show validation errors if any
                if validation_errors:
                    for error in validation_errors:
                        st.error(f"⚠️ {error}")
                
                # Store pending changes in session state
                if pending_changes:
                    st.session_state['pending_changes'] = pending_changes
                elif 'pending_changes' in st.session_state:
                    del st.session_state['pending_changes']
        
        except Exception as e:
            st.error(f"Critical error in process_aggrid_changes: {e}")
            # Clear any partial state to prevent corruption
            if 'pending_changes' in st.session_state:
                del st.session_state['pending_changes']

    
    def _update_transaction(
        self,
        txn_id: int,
        edited_row: pd.Series,
        original_data: pd.DataFrame,
        category_changed: bool,
        type_changed: bool,
        exact_rule: bool = False
    ) -> Dict:
        """Update a single transaction."""
        new_type = str(edited_row['Type'])
        new_category = str(edited_row['Category'])
        
        # Get original description
        description = original_data[
            original_data['id'] == txn_id
        ]['description'].iloc[0]
        
        # Validate category matches type
        if not self._validate_category_type(new_category, new_type):
            st.error(
                f"⚠️ Category '{new_category}' doesn't match type '{new_type}'"
            )
            return {'success': False}
        
        # Update database
        try:
            c = self.conn.cursor()
            c.execute("""
                UPDATE transactions 
                SET category = ?, transaction_type = ? 
                WHERE id = ?
            """, (new_category, new_type, txn_id))
            
            self.conn.commit()
            
            # Verify update
            c.execute(
                "SELECT category, transaction_type FROM transactions WHERE id = ?",
                (txn_id,)
            )
            verify = c.fetchone()
            
            if not verify or verify[0] != new_category:
                return {'success': False}
            
            # Find similar transactions and create rule if category OR type changed
            similar_transactions = []
            merchant = None
            rule_created = False
            
            # Trigger bulk update prompt if EITHER category OR type changed
            if category_changed or type_changed:
                if exact_rule:
                    # Create exact-match rule using full description
                    if category_changed:
                        c.execute("""
                            INSERT OR REPLACE INTO merchant_rules (merchant_pattern, category)
                            VALUES (?, ?)
                        """, (description, new_category))
                        self.conn.commit()
                        rule_created = True
                        merchant = description  # Use full description as "merchant" for display
                else:
                    # Create fuzzy rule using extracted merchant name
                    merchant = extract_merchant_name(description)
                    
                    if merchant and len(merchant) >= 2:
                        # Find similar transactions
                        similar_transactions = self._find_similar_transactions(
                            merchant, 
                            txn_id, 
                            new_category,
                            new_type
                        )
                        
                        # Create rule (only if category changed, as rules are category-based)
                        if category_changed:
                            success, _ = auto_create_rule(
                                self.conn, 
                                description, 
                                new_category
                            )
                            rule_created = success
            
            return {
                'success': True,
                'transaction_id': txn_id,
                'category': new_category,
                'txn_type': new_type,
                'type_changed': type_changed,
                'category_changed': category_changed,
                'merchant': merchant,
                'rule_created': rule_created,
                'similar_transactions': similar_transactions
            }
        
        except Exception as e:
            st.error(f"❌ Update failed: {e}")
            return {'success': False}
    
    
    def _delete_transaction(self, txn_id: int) -> Dict:
        """Delete a transaction with verification."""
        try:
            # Validate transaction ID
            if not txn_id or txn_id <= 0:
                st.error("Invalid transaction ID")
                return {'success': False}
            
            c = self.conn.cursor()
            
            # Check if transaction exists
            c.execute("SELECT id FROM transactions WHERE id = ?", (txn_id,))
            exists = c.fetchone()
            
            if not exists:
                st.error(f"Transaction {txn_id} not found")
                return {'success': False}
            
            # Delete the transaction
            c.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
            self.conn.commit()
            
            # Verify deletion
            c.execute("SELECT id FROM transactions WHERE id = ?", (txn_id,))
            still_exists = c.fetchone()
            
            if still_exists:
                st.error(f"Failed to delete transaction {txn_id} - still exists after deletion")
                self.conn.rollback()
                return {'success': False}
            
            return {'success': True}
            
        except sqlite3.Error as e:
            st.error(f"❌ Database error during deletion: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            return {'success': False}
        except Exception as e:
            st.error(f"❌ Unexpected error during deletion: {e}")
            return {'success': False}
    
    
    def _validate_category_type(self, category: str, txn_type: str) -> bool:
        """Validate that category matches transaction type."""
        type_to_categories = {
            'expense': EXPENSE_CATEGORIES,
            'income': INCOME_CATEGORIES,
            'transfer': TRANSFER_CATEGORIES,
            'payment': PAYMENT_CATEGORIES
        }
        
        valid_categories = type_to_categories.get(txn_type, [])
        return category in valid_categories
    
    
    def _find_similar_transactions(
        self,
        merchant: str,
        exclude_id: int,
        new_category: str,
        new_type: str
    ) -> List[Tuple]:
        """Find similar transactions using improved fuzzy matching."""
        c = self.conn.cursor()
        
        # Get all transactions that might be similar
        c.execute("""
            SELECT id, description, category, transaction_type, amount, date
            FROM transactions 
            WHERE id != ?
            AND (category != ? OR transaction_type != ?)
        """, (exclude_id, new_category, new_type))
        
        all_txns = c.fetchall()
        similar = []
        
        # Use fuzzy matching to find similar descriptions
        merchant_lower = merchant.lower()
        
        for txn in all_txns:
            txn_id, description, category, txn_type, amount, date = txn
            desc_lower = description.lower()
            
            # Check if merchant name is in description
            if merchant_lower in desc_lower:
                similar.append((txn_id, description, category, txn_type, amount, date))
                continue
            
            # Check for partial word matches (e.g., "AMAZON" matches "AMAZON.CA")
            merchant_words = set(merchant_lower.split())
            desc_words = set(desc_lower.split())
            
            # If 80% of merchant words are in description, consider it similar
            if merchant_words and len(merchant_words & desc_words) / len(merchant_words) >= 0.8:
                similar.append((txn_id, description, category, txn_type, amount, date))
        
        return similar
    
    def _show_success_message(self, changes: List[Dict]):
        """Show success message with rules created."""
        st.success(f"✅ Updated {len(changes)} transaction(s)!")
        
        # Show auto-learned rules
        rules_created = [
            c['merchant'] for c in changes 
            if c.get('rule_created')
        ]
        
        if rules_created:
            st.info(
                f"🧠 **Auto-learned rules:** {', '.join(rules_created)}"
            )
    
    def apply_pending_changes(self, apply_to_similar: bool = False, exact_rule: bool = False):
        """Apply pending changes from session state with transaction safety."""
        if 'pending_changes' not in st.session_state:
            st.warning("No pending changes to apply")
            return
        
        pending = st.session_state['pending_changes']
        if not pending or len(pending) == 0:
            st.warning("No pending changes to apply")
            return
        
        changes_made = []
        similar_updates = []
        grid_keys_to_clear = set()
        failed_updates = []
        
        # Process each change with individual error handling
        for change in pending:
            try:
                grid_keys_to_clear.add(change.get('grid_key', 'main'))
                
                # Validate change data
                if 'txn_id' not in change or 'description' not in change:
                    failed_updates.append(f"Invalid change data: {change}")
                    continue
                
                # Create a mini DataFrame with the transaction info
                txn_df = pd.DataFrame([{
                    'id': change['txn_id'],
                    'description': change['description']
                }])
                
                # Apply the change with exact_rule flag
                result = self._update_transaction(
                    change['txn_id'],
                    pd.Series({
                        'Type': change.get('new_type', 'expense'),
                        'Category': change.get('new_category', 'Other')
                    }),
                    txn_df,
                    change.get('category_changed', False),
                    change.get('type_changed', False),
                    exact_rule=exact_rule
                )
                
                if result.get('success'):
                    changes_made.append(result)
                    
                    # If apply_to_similar is True, also update similar transactions
                    if apply_to_similar and result.get('similar_transactions'):
                        try:
                            self._execute_bulk_update(
                                result['similar_transactions'],
                                change['new_category'],
                                change['new_type']
                            )
                            similar_updates.extend(result['similar_transactions'])
                        except Exception as e:
                            st.error(f"Error applying to similar transactions: {e}")
                else:
                    failed_updates.append(f"Transaction {change['txn_id']}")
            
            except Exception as e:
                st.error(f"Error processing change for transaction {change.get('txn_id', 'unknown')}: {e}")
                failed_updates.append(f"Transaction {change.get('txn_id', 'unknown')}")
                continue
        
        # Clear pending changes and grid states
        try:
            del st.session_state['pending_changes']
        except KeyError:
            pass
        
        # Clear grid initial states to force fresh comparison
        for grid_key in grid_keys_to_clear:
            initial_state_key = f'grid_initial_state_{grid_key}'
            if initial_state_key in st.session_state:
                try:
                    del st.session_state[initial_state_key]
                except KeyError:
                    pass
        
        # Show comprehensive results
        if changes_made:
            st.success(f"✅ Successfully updated {len(changes_made)} transaction(s)!")
            
            # Show which rules were created
            rules_created = [c for c in changes_made if c.get('rule_created')]
            if rules_created:
                merchants = [c.get('merchant', 'Unknown') for c in rules_created]
                st.info(f"🧠 **Auto-learned rules for future transactions:** {', '.join(merchants)}")
            
            if similar_updates:
                st.success(f"✅ Also updated {len(similar_updates)} similar transaction(s)!")
        
        if failed_updates:
            st.error(f"❌ Failed to update {len(failed_updates)} transaction(s): {', '.join(failed_updates[:5])}")
        
        if not changes_made and not failed_updates:
            st.info("No changes were applied")
        
        st.rerun()
    
    def render_action_buttons(self):
        """Render minimal action buttons for pending changes."""
        pending = st.session_state.get('pending_changes', [])
        has_changes = len(pending) > 0
        
        # Count similar transactions across all pending changes
        total_similar = 0
        if has_changes:
            for change in pending:
                merchant = extract_merchant_name(change['description'])
                if merchant and len(merchant) >= 2:
                    similar = self._find_similar_transactions(
                        merchant,
                        change['txn_id'],
                        change['new_category'],
                        change['new_type']
                    )
                    total_similar += len(similar)
        
        # Action bar - 4 columns for 3 buttons + caption
        col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
        
        with col1:
            st.caption(f"📝 {len(pending)} pending change(s)" if has_changes else "No pending changes")
        
        with col2:
            save_help = "Save this change only (creates fuzzy rule for similar merchants)"
            if st.button(
                "💾 Save",
                disabled=not has_changes,
                type="primary",
                width="stretch",
                help=save_help,
                key="save_changes_btn"
            ):
                self.apply_pending_changes(apply_to_similar=False, exact_rule=False)
        
        with col3:
            exact_help = "Save + create exact-match rule (only for this exact description)"
            if st.button(
                "🎯 Save Exact",
                disabled=not has_changes,
                type="secondary",
                width="stretch",
                help=exact_help,
                key="save_exact_btn"
            ):
                self.apply_pending_changes(apply_to_similar=False, exact_rule=True)
        
        with col4:
            similar_help = f"Save and apply to {total_similar} similar transaction(s)" if total_similar > 0 else "No similar transactions found"
            if st.button(
                f"🔄 Similar ({total_similar})",
                disabled=total_similar == 0,
                type="secondary",
                width="stretch",
                help=similar_help,
                key="apply_similar_btn"
            ):
                self.apply_pending_changes(apply_to_similar=True, exact_rule=False)
        
        # Show preview of similar transactions if any exist
        if total_similar > 0 and has_changes:
            with st.expander(f"👀 Preview Similar Transactions ({total_similar})", expanded=False):
                st.caption("These transactions will be updated if you click 'Apply to Similar'")
                
                for change in pending:
                    merchant = extract_merchant_name(change['description'])
                    if merchant and len(merchant) >= 2:
                        similar = self._find_similar_transactions(
                            merchant,
                            change['txn_id'],
                            change['new_category'],
                            change['new_type']
                        )
                        
                        if similar:
                            st.markdown(f"**Merchant Pattern:** `{merchant}`")
                            st.markdown(f"**Will change to:** {change['new_type']} → {change['new_category']}")
                            
                            # Show up to 10 similar transactions
                            preview_df = pd.DataFrame(similar[:10], columns=['ID', 'Description', 'Current Category', 'Current Type', 'Amount', 'Date'])
                            preview_df['Amount'] = preview_df['Amount'].apply(lambda x: f"${x:,.2f}")
                            preview_df = preview_df[['Date', 'Description', 'Amount', 'Current Category', 'Current Type']]
                            
                            st.dataframe(
                                preview_df,
                                width="stretch",
                                hide_index=True
                            )
                            
                            if len(similar) > 10:
                                st.caption(f"... and {len(similar) - 10} more")
                            
                            st.divider()
    
    def _execute_bulk_update(
        self, 
        transactions: List[Tuple], 
        new_category: str,
        new_type: Optional[str] = None
    ):
        """Execute bulk category/type update."""
        c = self.conn.cursor()
        
        for txn in transactions:
            # Unpack tuple (id, description, category, type, amount, date)
            txn_id = txn[0]
            
            if new_type:
                c.execute(
                    "UPDATE transactions SET category = ?, transaction_type = ? WHERE id = ?",
                    (new_category, new_type, txn_id)
                )
            else:
                c.execute(
                    "UPDATE transactions SET category = ? WHERE id = ?",
                    (new_category, txn_id)
                )
        
        self.conn.commit()
        
        st.success(f"✅ Updated {len(transactions)} similar transactions!")
