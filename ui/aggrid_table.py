"""
Modern AG Grid implementation for transaction management.
Provides a sleek, professional table with better UX.
"""

import streamlit as st
import pandas as pd
import json
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
from config import EXPENSE_CATEGORIES, INCOME_CATEGORIES, TRANSFER_CATEGORIES, PAYMENT_CATEGORIES


def render_aggrid_table(df: pd.DataFrame, key: str = "aggrid"):
    """
    Render a modern AG Grid table with custom styling and interactions.
    
    Args:
        df: DataFrame with transaction data
        key: Unique key for the grid
        
    Returns:
        Grid response object
    """
    # Help banner  - Guide users on editing
    st.info("💡 **Tip**: Click on **Type** or **Category** cells to edit them. Changes are tracked automatically - just click Save when ready!", icon="ℹ️")
    
    # Build grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configure columns with optimized widths
    # ID column: Make it visible but very narrow (hiding it prevents it from being returned)
    gb.configure_column("ID", 
                       header_name="ID",
                       width=60,
                       editable=False,
                       pinned='left',
                       cellStyle={'fontSize': '11px', 'color': '#888'})
    
    gb.configure_column("Date", 
                       header_name="📅 Date", 
                       width=115, 
                       editable=False,
                       cellStyle={'fontWeight': '500', 'fontSize': '13px'})
    
    gb.configure_column("Description", 
                       header_name="📝 Description", 
                       flex=1,  # Take remaining space
                       minWidth=250,
                       editable=False,
                       cellStyle={'fontWeight': '400'},
                       wrapText=False,
                       autoHeight=False)
    
    gb.configure_column("Amount", 
                       header_name="💰 Amount", 
                       width=130, 
                       editable=False,
                       cellStyle={
                           'fontWeight': '600', 
                           'textAlign': 'right',
                           'fontSize': '14px'
                       })
    
    # Type dropdown - EDITABLE
    gb.configure_column("Type", 
                       header_name="✏️ Type", 
                       width=125, 
                       editable=True,
                       cellEditor='agSelectCellEditor',
                       cellEditorParams={'values': ['expense', 'income', 'transfer', 'payment']},
                       cellStyle={'fontWeight': '500', 'backgroundColor': '#f0f8ff'})
    
    # Dynamic category dropdown based on type
    expenses_js = json.dumps(EXPENSE_CATEGORIES)
    income_js = json.dumps(INCOME_CATEGORIES)
    transfers_js = json.dumps(TRANSFER_CATEGORIES)
    payments_js = json.dumps(PAYMENT_CATEGORIES)
    
    category_selector_js = JsCode(f"""
    function(params) {{
        const type = params.data.Type;
        let values = [];
        
        if (type === 'expense') values = {expenses_js};
        else if (type === 'income') values = {income_js};
        else if (type === 'transfer') values = {transfers_js};
        else if (type === 'payment') values = {payments_js};
        else values = {expenses_js};  // Default
        
        return {{
            component: 'agSelectCellEditor',
            params: {{
                values: values
            }}
        }};
    }}
    """)
    
    gb.configure_column("Category", 
                       header_name="✏️ Category", 
                       width=190, 
                       editable=True,
                       cellEditorSelector=category_selector_js,
                       cellStyle={'fontWeight': '500', 'backgroundColor': '#f0f8ff'})
    
    gb.configure_column("Card", 
                       header_name="💳 Card", 
                       width=140, 
                       editable=False,
                       cellStyle={'fontSize': '13px'})
    
    # Add event handler to clear Category when Type changes
    on_cell_value_changed = JsCode("""
    function(params) {
        if (params.colDef.field === 'Type') {
            // When Type changes, clear the Category to force user to select a valid one
            params.node.setDataValue('Category', '');
        }
    }
    """)
    
    # Grid options
    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=False
    )
    
    gb.configure_grid_options(
        domLayout='normal',
        enableRangeSelection=False,
        rowSelection='single',
        suppressRowClickSelection=True,
        animateRows=True,
        pagination=True,
        paginationPageSize=25,
        suppressMovableColumns=True,
        singleClickEdit=True,
        stopEditingWhenCellsLoseFocus=True,
        onCellValueChanged=on_cell_value_changed
    )
    
    # Enhanced custom CSS for better aesthetics
    custom_css = {
        ".ag-header-cell-label": {
            "justify-content": "center",
            "font-weight": "600",
            "font-size": "13px",
            "letter-spacing": "0.3px"
        },
        ".ag-theme-streamlit": {
            "--ag-font-size": "14px",
            "--ag-font-family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            "--ag-row-height": "42px",
            "--ag-header-height": "44px",
            "--ag-borders": "solid 1px",
            "--ag-row-border-width": "1px"
        },
        ".ag-cell": {
            "display": "flex",
            "align-items": "center",
            "padding": "0 12px"
        },
        ".ag-header": {
            "border-bottom": "2px solid"
        },
        ".ag-row": {
            "transition": "background-color 0.15s ease"
        },
        ".ag-row:hover": {
            "cursor": "pointer"
        },
        # Hide ID column completely using CSS
        ".ag-header-cell[col-id='ID']": {
            "display": "none !important"
        },
        ".ag-cell[col-id='ID']": {
            "display": "none !important"
        }
    }
    
    grid_options = gb.build()
    
    # Render grid with optimized settings
    # Using AS_INPUT to ensure all columns (including hidden ID) are returned
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        data_return_mode=DataReturnMode.AS_INPUT,  # Changed from FILTERED_AND_SORTED to ensure ID is returned
        fit_columns_on_grid_load=True,  # Auto-fit columns to container
        theme='streamlit',
        height=600,
        width='100%',
        custom_css=custom_css,
        allow_unsafe_jscode=True,
        reload_data=False,
        key=key
    )
    
    return grid_response
