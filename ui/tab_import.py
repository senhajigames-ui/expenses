"""
Import Tab - CSV file upload and transaction import.

Handles:
- Multi-file CSV upload
- Format detection (RBC Credit, RBC Checking, WealthSimple)
- Duplicate detection
- Batch categorization
- Progress tracking
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Tuple
from logic.csv_import import parse_csv_transactions
from logic.categorization import batch_categorize_transactions
from database.transaction_operations import check_duplicates, add_transaction
from database.budget_operations import load_merchant_rules
from database.import_history import (
    calculate_file_hash,
    check_file_already_imported,
    record_file_import
)


class ImportProgress:
    """Track and display import progress."""
    
    def __init__(self):
        self.progress_bar = None
        self.status_text = None
    
    def initialize(self):
        """Initialize progress UI elements."""
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
    
    def update(self, progress: float, message: str):
        """Update progress bar and message."""
        if self.progress_bar:
            self.progress_bar.progress(min(progress, 1.0))
        if self.status_text:
            self.status_text.text(message)
    
    def complete(self):
        """Complete and hide progress indicators."""
        if self.progress_bar:
            self.progress_bar.empty()
        if self.status_text:
            self.status_text.empty()


class MultiFileImporter:
    """Handle multi-file transaction import workflow."""
    
    def __init__(self, conn):
        self.conn = conn  # Legacy - not used with Supabase
        self.custom_rules = load_merchant_rules(None)
    
    def import_files(self, uploaded_files: List) -> Dict[str, int]:
        """
        Import multiple CSV files with progress tracking and duplicate file detection.
        
        Returns:
            Dict with counts: {imported, skipped, duplicates, total_files, already_imported_files}
        """
        
        progress = ImportProgress()
        progress.initialize()
        
        all_transactions = []
        file_count = len(uploaded_files)
        already_imported_files = []
        files_to_process = []
        file_transaction_counts = {}  # Track transactions per file
        
        # Step 0: Check for already imported files
        st.markdown("### 🔍 Step 1: Checking File History")
        for idx, file in enumerate(uploaded_files):
            progress.update(
                (idx / file_count) * 0.15,
                f"🔍 Checking {file.name}... ({idx + 1}/{file_count})"
            )
            
            # Calculate file hash
            file_content = file.read()
            file_hash = calculate_file_hash(file_content)
            file.seek(0)  # Reset file pointer
            
            # Check if already imported
            if check_file_already_imported(file.name, file_hash):
                st.warning(f"⚠️ **{file.name}**: Already imported (skipping)")
                already_imported_files.append(file.name)
            else:
                files_to_process.append((file, file_hash))
        
        if not files_to_process:
            progress.complete()
            if already_imported_files:
                st.info(f"ℹ️ All {len(already_imported_files)} file(s) were previously imported. No new files to process.")
            return {
                'imported': 0, 
                'skipped': 0, 
                'duplicates': 0, 
                'total_files': file_count,
                'already_imported_files': len(already_imported_files)
            }
        
        st.divider()
        
        # Step 1: Parse files that haven't been imported
        st.markdown(f"### 📄 Step 2: Parsing {len(files_to_process)} New File(s)")
        for idx, (file, file_hash) in enumerate(files_to_process):
            file_progress = 0.15 + ((idx / len(files_to_process)) * 0.15)
            progress.update(
                file_progress,
                f"📄 Reading {file.name}... ({idx + 1}/{len(files_to_process)})"
            )
            
            try:
                transactions = parse_csv_transactions(file, self.custom_rules)
                if transactions:
                    # Tag each transaction with its source file for tracking
                    for txn in transactions:
                        txn['_source_file'] = file.name
                    all_transactions.extend(transactions)
                    file_transaction_counts[file.name] = len(transactions)
                    st.success(f"✅ **{file.name}**: {len(transactions)} transactions found")
                else:
                    st.warning(f"⚠️ **{file.name}**: No valid transactions")
                    file_transaction_counts[file.name] = 0
            except Exception as e:
                st.error(f"❌ **{file.name}**: {str(e)}")
                file_transaction_counts[file.name] = 0
        
        if not all_transactions:
            progress.complete()
            st.error("❌ No valid transactions found in any file")
            return {'imported': 0, 'skipped': 0, 'duplicates': 0, 'total_files': file_count}
        
        st.divider()
        
        # Step 2: Check duplicates
        st.markdown("### 🔍 Step 2: Checking for Duplicates")
        progress.update(0.30, f"🔍 Scanning {len(all_transactions)} transactions...")
        duplicates = check_duplicates(None, all_transactions)
        
        duplicate_count = 0
        if not duplicates.empty:
            duplicate_count = len(duplicates)
            st.warning(f"⚠️ Found **{duplicate_count}** duplicate transactions (will skip)")
            # Convert duplicates to list of dicts for comparison
            dup_records = duplicates.to_dict('records') if hasattr(duplicates, 'to_dict') else []
            all_transactions = [t for t in all_transactions if t not in dup_records]
        else:
            st.success(f"✅ No duplicates found - all {len(all_transactions)} transactions are new!")
        
        if not all_transactions:
            progress.complete()
            st.info("ℹ️ All transactions were duplicates - nothing new to import")
            return {'imported': 0, 'skipped': 0, 'duplicates': duplicate_count, 'total_files': file_count}
        
        st.divider()
        
        # Step 3: Batch categorize
        needs_categorization = [t for t in all_transactions if t.get('category') is None]
        
        if needs_categorization:
            st.markdown("### 🏷️ Step 3: Categorization")
            
            progress.update(
                0.40,
                f"🏷️ Categorizing {len(needs_categorization)} transactions..."
            )
            
            categories_and_types = batch_categorize_transactions(
                needs_categorization,
                self.custom_rules
            )
            
            # Apply categories
            cat_idx = 0
            for txn in all_transactions:
                if txn.get('category') is None:
                    try:
                        category, txn_type = categories_and_types[cat_idx]
                        txn['category'] = category if category else 'Other'
                        txn['transaction_type'] = txn_type if txn_type else 'expense'
                        cat_idx += 1
                    except (TypeError, IndexError):
                        txn['category'] = 'Other'
                        txn['transaction_type'] = 'expense'
            
            st.success(f"✅ Categorized {len(needs_categorization)} transactions using Smart Rules")
        else:
            st.markdown("### ✅ Step 3: Categorization")
            st.info("ℹ️ All transactions already categorized")
        
        st.divider()
        
        # Step 4: Import to database
        st.markdown("### 💾 Step 4: Saving to Database")
        progress.update(0.50, f"💾 Importing {len(all_transactions)} transactions...")
        
        imported = 0
        skipped = 0
        total = len(all_transactions)
        
        # Track imported count per file
        file_imported_counts = {name: 0 for name in file_transaction_counts.keys()}
        
        # Create a placeholder for live updates
        status_placeholder = st.empty()
        
        # Clean transactions for database insert (remove internal tracking fields)
        db_transactions = []
        for txn in all_transactions:
            clean_txn = {k: v for k, v in txn.items() if not k.startswith('_')}
            db_transactions.append(clean_txn)
            
        # DEBUG: Show what we're trying to insert
        st.write(f"DEBUG: Attempting to insert {len(db_transactions)} transactions")
        if db_transactions:
            st.write("First transaction sample:", db_transactions[0])
            
        # Use bulk insert for performance
        from database.transaction_operations import bulk_add_transactions
        success = bulk_add_transactions(db_transactions)
        
        # bulk_add_transactions returns bool, so count based on success
        imported = len(db_transactions) if success else 0
        skipped = 0 if success else len(db_transactions)
        
        # If successful, we need to attribute counts to files for history tracking
        if success:
            for txn in all_transactions:
                source_file = txn.get('_source_file')
                if source_file and source_file in file_imported_counts:
                    file_imported_counts[source_file] += 1
        
        progress.update(1.0, "✅ Import complete!")
        
        status_placeholder.empty()
        progress.complete()
        
        st.success(f"✅ **Import complete!** Saved {imported} transactions to database")
        
        # Record successfully imported files with accurate per-file counts
        for file, file_hash in files_to_process:
            file_imported = file_imported_counts.get(file.name, 0)
            if file_imported > 0:
                record_file_import(file.name, file_hash, file_imported)
        
        return {
            'imported': imported,
            'skipped': skipped,
            'duplicates': duplicate_count,
            'total_files': file_count,
            'already_imported_files': len(already_imported_files)
        }


def render_import_tab(conn, all_transactions: pd.DataFrame):
    """
    Main entry point for Import tab.
    
    Args:
        conn: Database connection
        all_transactions: Current transactions DataFrame
    """
    # Initialize file uploader key to allow clearing after import
    if 'file_uploader_key' not in st.session_state:
        st.session_state.file_uploader_key = 0
    
    st.subheader("📥 Import Transactions")
    
    # Instructions
    with st.expander("ℹ️ How to Import", expanded=False):
        st.markdown("""
        ### Quick Start
        1. **Select one or more CSV files** from your bank
        2. Click **"Import All Files"**
        3. Wait for processing to complete
        
        ### Supported Formats
        - RBC Credit Card statements
        - RBC Checking Account statements
        - WealthSimple transaction exports
        
        ### Features
        - ✅ Automatic duplicate detection
        - ✅ Smart categorization
        - ✅ Multi-file batch import
        - ✅ Progress tracking
        """)
    
    st.divider()
    
    # Multi-file upload
    uploaded_files = st.file_uploader(
        "📁 Choose CSV file(s)",
        type=['csv'],
        accept_multiple_files=True,
        help="Select one or more bank statement CSV files. You can select multiple files at once!",
        key=f"file_uploader_{st.session_state.file_uploader_key}"
    )
    
    if not uploaded_files:
        _show_recent_imports(all_transactions)
        return
    
    # Show file list
    st.markdown(f"### 📋 Selected Files ({len(uploaded_files)})")
    
    total_size = sum(file.size for file in uploaded_files)
    
    for file in uploaded_files:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(f"📄 {file.name}")
        with col2:
            st.caption(f"{file.size:,} bytes")
    
    st.caption(f"**Total size:** {total_size:,} bytes")
    
    st.divider()
    
    # Import button
    if st.button(
        f"🚀 Import All Files ({len(uploaded_files)})",
        type="primary",
        width="stretch",
        key="import_all_btn"
    ):
        st.divider()
        st.markdown("## 🔄 Processing Import")
        
        importer = MultiFileImporter(conn)
        results = importer.import_files(uploaded_files)
        
        # Show results
        st.divider()
        st.markdown("## 🎉 Import Complete!")
        
        # Summary metrics with color coding
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="📁 Files Processed",
                value=results['total_files'],
                delta=None
            )
        
        with col2:
            st.metric(
                label="✅ Successfully Imported",
                value=results['imported'],
                delta=f"+{results['imported']}" if results['imported'] > 0 else None,
                delta_color="normal"
            )
        
        with col3:
            st.metric(
                label="⏭️ Skipped",
                value=results['skipped'],
                delta=None
            )
        
        with col4:
            st.metric(
                label="🔄 Duplicates Found",
                value=results['duplicates'],
                delta=None
            )
        
        with col5:
            st.metric(
                label="📋 Already Imported",
                value=results.get('already_imported_files', 0),
                delta=None,
                help="Files that were previously imported"
            )
        
        # Success message and next steps
        if results['imported'] > 0:
            st.balloons()
            
            st.success(
                f"**🎊 Success!** {results['imported']} new transactions added to your account!"
            )
            
            # Next steps
            st.info(
                "💡 **Next Steps:**\n"
                "- Navigate to **Overview** to see your spending summary\n"
                "- Check **Analysis** for detailed insights\n"
                "- Use **Manage** to edit or categorize transactions"
            )
            
            # Clear file uploader by incrementing key
            st.session_state.file_uploader_key += 1
            st.rerun()
        elif results['duplicates'] > 0:
            st.info(
                f"ℹ️ All {results['duplicates']} transactions were already in your database. "
                "No new data to import."
            )
        else:
            st.warning(
                "⚠️ No transactions were imported. Please check your CSV files and try again."
            )
            st.rerun()


def _show_recent_imports(all_transactions: pd.DataFrame):
    """Show recent import statistics."""
    if all_transactions.empty:
        st.info("👋 **No transactions yet!**\n\nUpload one or more CSV files to get started.")
        
        # Show example
        with st.expander("💡 Example: What to expect"):
            st.markdown("""
            After importing, you'll see:
            - 📊 Transaction summaries and charts
            - 🏷️ Auto-categorized expenses
            - 📈 Spending trends over time
            - 💰 Budget tracking
            """)
        return
    
    st.divider()
    st.subheader("📊 Your Data")
    
    # Data Summary - Consolidated
    from database.import_history import get_import_history, get_import_stats
    from datetime import datetime, timedelta
    
    st.divider()
    
    try:
        # Get import stats
        stats = get_import_stats(None)
        
        # Get all imports for dropdown
        all_imports = get_import_history(None, limit=50)  # Last 50 files
        
        # Transaction date info
        all_transactions['date_parsed'] = pd.to_datetime(all_transactions['date'])
        latest_date = all_transactions['date_parsed'].max() if not all_transactions.empty else None
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        col1.metric("💳 Total Transactions", f"{len(all_transactions):,}")
        
        if stats['last_import']:
            try:
                last_import_dt = datetime.fromisoformat(stats['last_import'])
                col2.metric("🕐 Last Import", last_import_dt.strftime("%b %d, %Y"))  # Date only, no time
            except:
                col2.metric("🕐 Last Import", "Recently")
        else:
            col2.metric("🕐 Last Import", "Never")
        
        if latest_date:
            col3.metric("🗓️ Latest Transaction", latest_date.strftime("%b %d, %Y"))
        
        # Show imported files in a compact dropdown
        if all_imports:
            with st.expander(f"📄 Imported Files ({len(all_imports)})", expanded=False):
                for imp in all_imports:
                    import_date = pd.to_datetime(imp['import_date']).strftime('%b %d, %Y')
                    st.caption(f"• {imp['filename']} — {import_date} ({imp['transactions_imported']} txns)")
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
