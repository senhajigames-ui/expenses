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
from typing import Dict, List, Tuple, Optional
from logic.categorization import extract_merchant_name
from config import (
    EXPENSE_CATEGORIES, INCOME_CATEGORIES, 
    TRANSFER_CATEGORIES, PAYMENT_CATEGORIES
)


class TransactionUpdater:
    """Handle transaction updates and bulk operations."""
    
    def __init__(self, conn):
        """Initialize with database connection."""
        self.conn = conn
    
    def process_data_editor_changes(
        self,
        original_df: pd.DataFrame,
        display_df: pd.DataFrame,
        editor_state: Dict,
        grid_key: str = "main"
    ):
        """
        Process changes from st.data_editor.
        
        Args:
            original_df: The original DataFrame (with 'id', 'description', etc.)
            display_df: The DataFrame currently displayed (must align with editor rows)
            editor_state: The session state output from data_editor (edited_rows, etc.)
            grid_key: Unique key for tracking changes
        """
        try:
            if not editor_state or 'edited_rows' not in editor_state:
                return

            edited_rows = editor_state['edited_rows']
            if not edited_rows:
                return

            pending_changes = []
            
            # Helper to get original transaction ID from display row index
            # NOTE: usage of reset_index(drop=True) in display logic is assumed!
            # display_df index must match editor row index.
            
            for row_idx, changes in edited_rows.items():
                try:
                    row_idx = int(row_idx)
                    
                    if row_idx >= len(display_df):
                        st.warning(f"Row {row_idx} out of bounds")
                        continue
                        
                    # Get ID from display DF (it has 'ID' column, even if hidden)
                    if 'ID' not in display_df.columns:
                        st.error("Display data missing ID column")
                        return
                        
                    txn_id = int(display_df.iloc[row_idx]['ID'])
                    
                    # Get current display values to fill in gaps if multiple cols edited?
                    # Actually data_editor sends delta.
                    
                    # Get original transaction data
                    matching_txns = original_df[original_df['id'] == txn_id]
                    if matching_txns.empty:
                        continue
                    orig_txn = matching_txns.iloc[0]
                    description = str(orig_txn.get('description', ''))
                    
                    # Determine what changed
                    # Default to current value if not in changes
                    current_type = str(orig_txn.get('transaction_type', 'expense'))
                    current_category = str(orig_txn.get('category', 'Other'))
                    
                    # Updates from editor
                    new_type = changes.get('Type', current_type)
                    new_category = changes.get('Category', current_category)
                    
                    type_changed = 'Type' in changes and new_type != current_type
                    category_changed = 'Category' in changes and new_category != current_category
                    
                    if type_changed or category_changed:
                         # Validate change
                        errors = self._validate_change(txn_id, new_category, new_type)
                        if errors:
                            for err in errors:
                                st.error(f"⚠️ {err}")
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
                    st.error(f"Error processing row {row_idx}: {e}")
                    continue
            
            # Update session state with pending changes
            if pending_changes:
                # Append to existing changes if any? No, usually we replace or accumulate.
                # Let's replace for simplicity of state management, user saves explicitly.
                st.session_state['pending_changes'] = pending_changes
                
        except Exception as e:
            st.error(f"Error processing editor changes: {e}")


    def _validate_change(self, txn_id: int, new_category: str, new_type: str) -> List[str]:
        """Validate a single transaction change."""
        errors = []
        # Validate category is not empty
        if not new_category or new_category.strip() == '':
            errors.append(f"Transaction ID {txn_id}: Category cannot be empty")
        
        # Validate category matches type
        elif not self._validate_category_type(new_category, new_type):
            errors.append(
                f"Transaction ID {txn_id}: Category '{new_category}' doesn't match type '{new_type}'"
            )
        return errors

    
    def _update_transaction(
        self,
        txn_id: int,
        edited_row: pd.Series,
        original_data: pd.DataFrame,
        category_changed: bool,
        type_changed: bool,
        exact_rule: bool = False
    ) -> Dict:
        """Update a single transaction using Supabase."""
        from database.transaction_operations import update_transaction
        from database.budget_operations import save_merchant_rule
        
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
        
        # Update database using Supabase
        try:
            updates = {
                'category': new_category,
                'transaction_type': new_type
            }
            
            success = update_transaction(txn_id, updates)
            
            if not success:
                return {'success': False}
            
            # Clear cache to show updates immediately
            from expense_tracker import load_transactions
            load_transactions.clear()
            
            # Find similar transactions and create rule if category OR type changed
            similar_transactions = []
            merchant = None
            rule_created = False
            
            # Trigger bulk update prompt if EITHER category OR type changed
            if category_changed or type_changed:
                if exact_rule:
                    # Create exact-match rule using full description
                    if category_changed:
                        rule_success = save_merchant_rule(None, description, new_category)
                        rule_created = rule_success
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
                            # Use save_merchant_rule (Supabase) instead of legacy auto_create_rule (SQLite)
                            # merchant variable (Line 260) holds the cleaned name
                            rule_success = save_merchant_rule(self.conn, merchant, new_category)
                            rule_created = rule_success
            
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
        """Delete a transaction using Supabase."""
        from database.transaction_operations import delete_transaction
        
        try:
            # Validate transaction ID
            if not txn_id or txn_id <= 0:
                st.error("Invalid transaction ID")
                return {'success': False}
            
            # Delete using Supabase
            success = delete_transaction(None, txn_id)
            
            if not success:
                st.error(f"Transaction {txn_id} not found or could not be deleted")
                return {'success': False}
            
            # Clear cache to show updates immediately
            from expense_tracker import load_transactions
            load_transactions.clear()
            
            return {'success': True}
            
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
        """Find similar transactions using Supabase."""
        from database.transaction_operations import search_transactions
        
        # Get candidates from Supabase using server-side search
        # This replaces loading the entire database into memory!
        candidates = search_transactions(merchant, exclude_id=exclude_id)
        
        if not candidates:
            return []
            
        # Convert to DataFrame for compatibility with existing logic
        filtered = pd.DataFrame(candidates)
        
        # Determine which columns to use (search_transactions returns specific columns)
        # Ensure we have the needed columns even if strict selection was used
        required_cols = ['id', 'description', 'category', 'transaction_type', 'amount', 'date']
        for col in required_cols:
            if col not in filtered.columns:
                filtered[col] = None

        # Filter out matches that already have the target category/type
        filtered = filtered[
            ((filtered['category'] != new_category) | (filtered['transaction_type'] != new_type))
        ]
        
        similar = []
        
        # Use fuzzy matching to find similar descriptions
        merchant_lower = merchant.lower()
        
        for _, row in filtered.iterrows():
            description = str(row.get('description', ''))
            desc_lower = description.lower()
            
            # Check if merchant name is in description
            if merchant_lower in desc_lower:
                similar.append((
                    row['id'], 
                    description, 
                    row.get('category', 'Other'), 
                    row.get('transaction_type', 'expense'), 
                    row.get('amount', 0), 
                    row.get('date', '')
                ))
                continue
            
            # Check for partial word matches (e.g., "AMAZON" matches "AMAZON.CA")
            merchant_words = set(merchant_lower.split())
            desc_words = set(desc_lower.split())
            
            # If 80% of merchant words are in description, consider it similar
            if merchant_words and len(merchant_words & desc_words) / len(merchant_words) >= 0.8:
                similar.append((
                    row['id'], 
                    description, 
                    row.get('category', 'Other'), 
                    row.get('transaction_type', 'expense'), 
                    row.get('amount', 0), 
                    row.get('date', '')
                ))
        
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
        """Execute bulk category/type update using Supabase."""
        from database.transaction_operations import update_transaction
        
        success_count = 0
        for txn in transactions:
            # Unpack tuple (id, description, category, type, amount, date)
            txn_id = txn[0]
            
            updates = {'category': new_category}
            if new_type:
                updates['transaction_type'] = new_type
            
            if update_transaction(txn_id, updates):
                success_count += 1
        
        st.success(f"✅ Updated {success_count} similar transactions!")
