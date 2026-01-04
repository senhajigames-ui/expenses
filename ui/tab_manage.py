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
from ui.manage.components import prepare_aggrid_data
from ui.aggrid_table import render_aggrid_table


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
        
    # Separate Transfer transactions from the common filtered set
    # This ensures they are always visible regardless of Type/Category selection
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
    # If user selects "Transfers" type, they show up in main table AND bottom section (which is fine)
    # But if user selects "All" or "Expenses", we usually want to hide transfers from main table
    # to keep it clean, since they have their own section.
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
    
    st.caption("💡 **Tip:** Click any cell to edit • Changes save automatically • Sort by clicking column headers")
    
    # Prepare data for AG Grid
    aggrid_df = main_transactions.copy()
    aggrid_df = aggrid_df.sort_values('date', ascending=False)
    
    # Format for display
    display_df = prepare_aggrid_data(aggrid_df)
    
    # Render AG Grid
    grid_response = render_aggrid_table(display_df, key="main_aggrid")
    
    # Process changes for main table (tracks in session state)
    updater.process_aggrid_changes(aggrid_df, display_df, grid_response)
    
    # Render minimal action buttons below the table
    st.divider()
    updater.render_action_buttons()
    
    # Show Transfer transactions separately - ALWAYS show, but collapsed by default
    st.divider()
    
    with st.expander(f"↔️ Transfers ({len(all_transfers)})", expanded=False):
        if not all_transfers.empty:
            st.caption("TFSA/FHSA contributions, Morocco, and other transfers shown separately")
            
            # Prepare transfer data
            transfer_aggrid_df = all_transfers.copy()
            transfer_aggrid_df = transfer_aggrid_df.sort_values('date', ascending=False)
            transfer_display_df = prepare_aggrid_data(transfer_aggrid_df)
            
            # Render transfers table using AG Grid
            transfer_grid_response = render_aggrid_table(transfer_display_df, key="transfer_aggrid")
            
            # Process changes for transfers table
            updater.process_aggrid_changes(transfer_aggrid_df, transfer_display_df, transfer_grid_response)
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
                help="Find the ID in the first column of the table above"
            )
        
        with col2:
            st.write("")  # Spacer
            st.write("")  # Spacer
            if st.button("🗑️ Delete", type="primary", width="stretch", key="delete_btn"):
                result = updater._delete_transaction(int(delete_id))
                if result['success']:
                    st.success(f"✅ Deleted transaction ID {delete_id}")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to delete transaction ID {delete_id}")
        
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
                        c = conn.cursor()
                        c.execute("DELETE FROM transactions")
                        conn.commit()
                        count = c.rowcount
                        
                        # Also clear import history so files can be re-imported
                        clear_import_history(conn)
                        
                        st.success(f"✅ Deleted all {count} transactions and cleared import history!")
                        st.session_state.confirm_delete_all = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to delete transactions: {e}")
            
            with col2:
                if st.button("❌ Cancel", width="stretch", key="confirm_delete_all_no"):
                    st.session_state.confirm_delete_all = False
                    st.rerun()