"""
Formatting Helper Functions - Data formatting and cleaning utilities
"""

import pandas as pd


def format_currency(value):
    """Format value in millions with 2 decimals (no currency symbols)"""
    if pd.isna(value) or value == 0:
        return "0.00"
    # Convert to millions with 2 decimal places
    value_in_millions = value / 1e6
    return f"{value_in_millions:.2f}"


def clean_re_line_name(name):
    """Remove Rev&Exp prefix from revenue & expenses line names"""
    if pd.isna(name):
        return ''
    name = str(name).strip()
    # Split on first space and take the rest
    parts = name.split(maxsplit=1)
    if len(parts) > 1:
        return parts[1].strip()
    return name


def clean_cost_line_name(name):
    """Remove Cost prefix from cost line names"""
    if pd.isna(name):
        return ''
    name = str(name).strip()
    # Cost lines may have prefixes like "Cost "
    if name.startswith('Cost '):
        return name[5:].strip()
    return name


def is_subtotal_line(name):
    """Detect if a line is a subtotal/total line"""
    if pd.isna(name):
        return False
    name = str(name).lower().strip()
    subtotal_keywords = ['total', 'subtotal', 'net ', 'gross', 'sum of']
    return any(keyword in name for keyword in subtotal_keywords)


def format_number_compact(value):
    """
    Format number with K/M/B suffix, showing at most 3 digits with 1 decimal.

    Examples:
        1_234 -> "1.2K"
        2_345_678 -> "2.3M"
        1_234_567_890 -> "1.2B"
        123 -> "123"

    Args:
        value: Numeric value to format

    Returns:
        String with compact formatting
    """
    if pd.isna(value) or value == 0:
        return "0"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000:  # Billions
        formatted = f"{abs_value / 1_000_000_000:.1f}B"
    elif abs_value >= 1_000_000:  # Millions
        formatted = f"{abs_value / 1_000_000:.1f}M"
    elif abs_value >= 1_000:  # Thousands
        formatted = f"{abs_value / 1_000:.1f}K"
    else:
        # Less than 1000, show as-is with 1 decimal if needed
        if abs_value >= 10:
            formatted = f"{abs_value:.0f}"
        else:
            formatted = f"{abs_value:.1f}"

    return f"{sign}{formatted}"
