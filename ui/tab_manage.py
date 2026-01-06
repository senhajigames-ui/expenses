"""
Manage Tab - Transaction editing and bulk update management.

This module is the main orchestrator for the Manage tab.
The actual logic has been split into focused modules:
- manage.filters: Transaction filtering
- manage.updater: Transaction updates and bulk operations
- manage.components: Reusable UI components
"""

import streamlit as st
import pandas as pd
from ui.manage import TransactionFilter, TransactionUpdater
from ui.manage.components import prepare_table_data
from config import (
    EXPENSE_CATEGORIES, INCOME_CATEGORIES, 
    TRANSFER_CATEGORIES, PAYMENT_CATEGORIES
)

def render_manage_tab(conn, all_transactions: pd.DataFrame):
    """
    Main entry point for Manage Transactions tab.
    
    Args:
        conn: Database connection
        all_transactions: DataFrame with all transactions
    """
    from database.import_history import clear_import_history
    
    st.subheader("🔧 Manage Transactions")
    
    # Initialize updater early
    updater = TransactionUpdater(conn)
    
    # Render filters
    TransactionFilter.render(all_transactions)
    
    # Apply common filters (Month, Search) first
    # This ensures Transfers section respects date/search but ignores Type/Category filters
    common_filtered = all_transactions.copy()
    
    # Month filter
    month = st.session_state.get('manage_month', 'All')
    if month != 'All':
        common_filtered = common_filtered[common_filtered['month'] == month]
    
    # Search filter
    search = st.session_state.get('manage_search', '')
    if search:
        common_filtered = common_filtered[
            common_filtered['description'].str.contains(search, case=False, na=False)
        ]
    
    # Handle empty state after filtering
    if common_filtered.empty:
        st.info("📭 No transactions found. Try adjusting filters or import some data!")
        return
        
    # Separate Transfer transactions from the common filtered set
    transfer_mask = common_filtered['transaction_type'] == 'transfer'
    all_transfers = common_filtered[transfer_mask].copy()
    
    # Now apply Type and Category filters to the remaining transactions for the main table
    main_filtered = common_filtered.copy()
    
    # Type filter
    type_filter = st.session_state.get('manage_type', 'All')
    if type_filter != 'All':
        type_map = {
            'Expenses': 'expense',
            'Income': 'income',
            'Transfers': 'transfer',
            'Payments': 'payment'
        }
        main_filtered = main_filtered[
            main_filtered['transaction_type'] == type_map[type_filter]
        ]
    
    # Category filter
    category = st.session_state.get('manage_cat', 'All')
    if category != 'All':
        main_filtered = main_filtered[main_filtered['category'] == category]
        
    # Exclude transfers from main table unless explicitly selected
    if type_filter != 'Transfers':
        main_transactions = main_filtered[main_filtered['transaction_type'] != 'transfer'].copy()
    else:
        main_transactions = main_filtered.copy()

    
    # Show dynamic title based on what's in the main table
    type_filter = st.session_state.get('manage_type', 'All')
    title_emoji = {
        'All': '📋',
        'Expenses': '💳',
        'Income': '💵',
        'Transfers': '↔️',
    }
    title_text = type_filter if type_filter != 'All' else 'Transactions'
    
    st.markdown(
        f"### {title_emoji.get(type_filter, '📋')} {title_text} ({len(main_transactions)})"
    )
    
    st.caption("💡 **Tip:** Edit directly in the table below. Changes are saved when you click 'Save'.")
    
    # Prepare data using existing helper (returns ID, Date, Description, Amount, Type, Category, Card)
    # We rename 'prepare_aggrid_data' conceptually to 'prepare_table_data' but reuse the function
    with st.spinner("Loading transactions..."):
        # Reset index to ensure 0..N sequence matching data_editor rows
        aggrid_df = main_transactions.copy().sort_values('date', ascending=False)
        display_df = prepare_table_data(aggrid_df).reset_index(drop=True)
    
    # Combine all categories for the dropdown
    all_categories = sorted(list(set(
        EXPENSE_CATEGORIES + INCOME_CATEGORIES + TRANSFER_CATEGORIES + PAYMENT_CATEGORIES + ["Other"]
    )))

    # Configure columns for st.data_editor
    column_config = {
        "ID": None,  # Hide ID column
        "Date": st.column_config.TextColumn("📅 Date", disabled=True),
        "Description": st.column_config.TextColumn("📝 Description", disabled=True),
        "Amount": st.column_config.TextColumn("💰 Amount", disabled=True),
        "Card": st.column_config.TextColumn("💳 Card", disabled=True),
        "Type": st.column_config.SelectboxColumn(
            "✏️ Type",
            options=['expense', 'income', 'transfer', 'payment'],
            required=True
        ),
        "Category": st.column_config.SelectboxColumn(
            "✏️ Category",
            options=all_categories,
            required=True
        )
    }

    # Render Native Data Editor
    # Key must be unique to prevent state conflicts
    editor_state = st.data_editor(
        display_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        key="main_editor"
    )
    
    # Process changes
    updater.process_data_editor_changes(aggrid_df, display_df, editor_state, grid_key="main")
    
    # Render action buttons
    st.divider()
    updater.render_action_buttons()
    
    # Show Transfer transactions separately
    st.divider()
    
    with st.expander(f"↔️ Transfers ({len(all_transfers)})", expanded=False):
        if not all_transfers.empty:
            st.caption("TFSA/FHSA contributions, Morocco, and other transfers")
            
            # Prepare transfer data
            transfer_df = all_transfers.copy().sort_values('date', ascending=False)
            transfer_display = prepare_table_data(transfer_df).reset_index(drop=True)
            
            # Render transfers editor
            transfer_editor_state = st.data_editor(
                transfer_display,
                column_config=column_config,
                hide_index=True,
                use_container_width=True,
                num_rows="fixed",
                key="transfer_editor"
            )
            
            # Process changes
            updater.process_data_editor_changes(transfer_df, transfer_display, transfer_editor_state, grid_key="transfer")
        else:
            st.info("No transfer transactions found")
    
    # Simple Delete Section
    st.divider()
    with st.expander("🗑️ Delete Transactions", expanded=False):
        st.caption("Delete individual transactions or clear all data")
        
        # Delete single transaction
        st.markdown("#### Delete Single Transaction")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            delete_id = st.number_input(
                "Transaction ID",
                min_value=1,
                step=1,
                key="delete_transaction_id",
                help="Enter the ID of the transaction to delete"
            )
        
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if st.button("🗑️ Delete", type="primary", width="stretch", key="delete_btn"):
                if delete_id < 1:
                    st.error("❌ Please enter a valid Transaction ID")
                else:
                    result = updater._delete_transaction(int(delete_id))
                    if result['success']:
                        st.success(f"✅ Deleted transaction ID {delete_id}")
                        st.rerun()
                    else:
                        st.warning(f"⚠️ ID {delete_id} not found")
        
        # Delete all transactions
        st.divider()
        st.markdown("#### 🚨 Delete All Transactions")
        st.warning("⚠️ This will permanently delete ALL transactions for the current user!")
        
        if st.button("🔥 Delete All Transactions", type="secondary", width="stretch", key="delete_all_btn"):
            st.session_state.confirm_delete_all = True
        
        if st.session_state.get('confirm_delete_all'):
            st.error("⚠️ **Are you absolutely sure?** This action cannot be undone!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Yes, Delete Everything", type="primary", width="stretch", key="confirm_delete_all_yes"):
                    try:
                        from database.transaction_operations import clear_all_transactions
                        success = clear_all_transactions(conn)
                        if success:
                            clear_import_history(conn)
                            st.success("✅ Deleted all transactions!")
                            st.session_state.confirm_delete_all = False
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete transactions")
                    except Exception as e:
                        st.error(f"❌ Failed to delete transactions: {e}")
            
            with col2:
                if st.button("❌ Cancel", width="stretch", key="confirm_delete_all_no"):
                    st.session_state.confirm_delete_all = False
                    st.rerun()