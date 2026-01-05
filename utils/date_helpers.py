"""
Date utility functions for expense tracker.
Handles date range presets, quarter calculations, and date formatting.
"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def get_date_range_presets():
    """
    Returns predefined date range options.
    
    Returns:
        dict: Dictionary mapping preset names to (start_date, end_date) tuples
    """
    today = datetime.now().date()
    
    presets = {
        "Last 7 Days": (today - timedelta(days=7), today),
        "Last 30 Days": (today - timedelta(days=30), today),
        "Last 90 Days": (today - timedelta(days=90), today),
        "This Month": (today.replace(day=1), today),
        "Last Month": (
            (today.replace(day=1) - timedelta(days=1)).replace(day=1),
            today.replace(day=1) - timedelta(days=1)
        ),
        "This Quarter": (get_quarter_start(today), today),
        "Last Quarter": (
            get_quarter_start(today) - relativedelta(months=3),
            get_quarter_start(today) - timedelta(days=1)
        ),
        "This Year": (today.replace(month=1, day=1), today),
        "Last Year": (
            today.replace(year=today.year-1, month=1, day=1),
            today.replace(year=today.year-1, month=12, day=31)
        ),
        "All Time": (datetime(2000, 1, 1).date(), today),
        "Custom Range": None
    }
    
    return presets


def get_quarter_start(date):
    """
    Returns the start date of the current quarter.
    
    Args:
        date: Date object
        
    Returns:
        date: First day of the quarter
    """
    quarter = (date.month - 1) // 3 + 1
    start_month = (quarter - 1) * 3 + 1
    return date.replace(month=start_month, day=1)


def format_date_range(start_date, end_date):
    """
    Format date range for display.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        str: Formatted date range string
    """
    if start_date == end_date:
        return start_date.strftime("%b %d, %Y")
    elif start_date.year == end_date.year:
        return f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
    else:
        return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"


def format_month(month_str):
    """
    Format month string (YYYY-MM) to readable format.
    
    Args:
        month_str: Month in YYYY-MM format
        
    Returns:
        str: Formatted month string (e.g., "January 2025")
    """
    try:
        date_obj = datetime.strptime(month_str, "%Y-%m")
        return date_obj.strftime("%B %Y")
    except (ValueError, TypeError):
        return month_str