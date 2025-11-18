"""
KPI Mappings - Database Column Names to KPI Metadata Keys

This module provides mappings between database column names and KPI metadata keys
used throughout the application.
"""

# Map database column names to KPI_METADATA keys
DB_COLUMN_TO_KPI_KEY = {
    # Level 1 KPIs - Map database columns to KPI_METADATA keys
    'Net_Margin_Pct': 'Net_Income_Margin',
    'AR_Days': 'AR_Days',  # Already matches
    'Operating_Expense_Ratio': 'Operating_Expense_per_Adjusted_Discharge',  # Maps to L1 KPI
    'Current_Ratio': 'Current_Ratio',  # Already matches
    'Medicare_CCR': 'Medicare_CCR',  # NEW: Medicare Cost-to-Charge Ratio
    'Bad_Debt_Charity_Pct': 'Bad_Debt_Charity_Pct',  # NEW: Bad Debt + Charity %

    # Level 2/3 KPIs
    'Operating_Margin_Pct': 'Operating_Expense_Ratio',  # L2 KPI
    'Total_Margin_Pct': 'Total_Margin',
    'Days_Cash_On_Hand': 'Cash_Days_on_Hand',

    # Additional KPIs that match
    'Outpatient_Revenue_Pct': 'Outpatient_Revenue_Pct',
    'Inpatient_Revenue_Pct': 'Inpatient_Revenue_Pct',
    'Asset_Turnover_Ratio': 'Asset_Turnover_Ratio',
    'Fixed_Asset_Turnover': 'Fixed_Asset_Turnover',
    'Debt_to_Equity_Ratio': 'Debt_to_Equity_Ratio',
    'Equity_Ratio_Pct': 'Equity_Ratio_Pct',
    'Debt_Ratio_Pct': 'Debt_Ratio_Pct',
    'Return_on_Assets_Pct': 'Return_on_Assets_Pct',
    'Return_on_Equity_Pct': 'Return_on_Equity_Pct',
    'Revenue_Growth_Pct': 'Revenue_Growth_Pct',
}

# Create a reverse mapping for L2/L3 KPIs
KPI_KEY_TO_DB_COLUMN = {v: k for k, v in DB_COLUMN_TO_KPI_KEY.items()}
