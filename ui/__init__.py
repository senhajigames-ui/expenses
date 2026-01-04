"""
UI Components Package

This package contains all user interface components:
- sidebar: Navigation and user management
- tab_import: CSV import interface
- tab_overview: Financial summary dashboard
- tab_analysis: Detailed analytics and charts
- tab_manage: Transaction management (main orchestrator)
- aggrid_table: Modern table component wrapper
- manage: Modular components for transaction management
"""

# Main tab renderers
from .sidebar import render_sidebar
from .tab_import import render_import_tab
from .tab_overview import render_overview_tab
from .tab_analysis import render_analysis_tab
from .tab_manage import render_manage_tab

# Grid component
from .aggrid_table import render_aggrid_table

# Manage tab components
from .manage import TransactionFilter, TransactionUpdater

__all__ = [
    # Tab renderers
    'render_sidebar',
    'render_import_tab',
    'render_overview_tab',
    'render_analysis_tab',
    'render_manage_tab',
    # Components
    'render_aggrid_table',
    'TransactionFilter',
    'TransactionUpdater'
]
