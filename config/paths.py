"""Path and file configuration for HealthVista Analytics ETL."""
from pathlib import Path
import os

# Project root directory (where this config directory is located)
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / 'data'
SOURCE_DATA_DIR = DATA_DIR / 'source_data'  # HOSP10FY folders
DB_PARQUETS_DIR = DATA_DIR / 'db_parquets'  # Parquet output folders
COL_NAMES_DIR = DATA_DIR / 'Col_Names'

# Legacy: DATA_ROOT for backward compatibility
DATA_ROOT = SOURCE_DATA_DIR
HOSP_DATA_PATTERN = os.getenv('HOSP_DATA_PATTERN', 'HOSP10FY{year}')

# Output directories
# OUTPUT_DIR points to where parquet files will be saved
OUTPUT_DIR = DB_PARQUETS_DIR
LOGS_DIR = PROJECT_ROOT / 'logs'

# Parquet output directories (created by ETL scripts)
# These are now in data/db_parquets/
BALANCE_SHEET_OUTPUT = DB_PARQUETS_DIR / 'balance_sheet_long'
FUND_BALANCE_CHANGES_OUTPUT = DB_PARQUETS_DIR / 'fund_balance_changes_long'
REVENUE_OUTPUT = DB_PARQUETS_DIR / 'revenue_long'
REVENUE_EXPENSES_OUTPUT = DB_PARQUETS_DIR / 'revenue_expenses_long'
COSTS_OUTPUT = DB_PARQUETS_DIR / 'costs_long'
COSTS_A000_OUTPUT = DB_PARQUETS_DIR / 'costs_a000_long'
COSTS_B100_OUTPUT = DB_PARQUETS_DIR / 'costs_b100_long'

# Column name mapping files
COLUMN_NAME_FILES = {
    'balance_sheet': COL_NAMES_DIR / 'Names_G000.csv',  # Includes G000000 and G100000
    'fund_balance_changes': COL_NAMES_DIR / 'Names_G000.csv',  # Same file, different worksheet
    'revenue_expenses': COL_NAMES_DIR / 'Names_G300.csv',  # Revenue & Expenses with Report, Level, Account
    'revenue': COL_NAMES_DIR / 'Names_G200.csv',  # Revenue with REV_GROUP, REVENUE_CENTER, REV_SUBGROUP
    'costs': COL_NAMES_DIR / 'Names_4_Costs.csv',
    'costs_a000': COL_NAMES_DIR / 'Names_A000.csv',  # New: Cost Centers (A000000)
    'costs_b100': COL_NAMES_DIR / 'Names_B000.csv',  # New: Overhead Costs (B000001)
}

# Fiscal years to process
FISCAL_YEARS = [2020, 2021, 2022, 2023, 2024]

# State filtering for faster development/testing
# Set to None or empty list to process all states
# State codes are the first 2 digits of Provider_Number
# Examples: '06' = Colorado, '31' = New Jersey
FILTER_STATES = ['03', '31', '01', '14']  # Connecticut and Nebraska only

# Worksheet codes for different data types
WORKSHEETS = {
    'balance_sheet': ['G000000'],
    'fund_balance_changes': ['G100000'],
    'costs_a000': ['A000000'],  # New: Cost Centers
    'costs_b100': ['B000001'],  # New: Overhead Costs
    'revenue': ['G200000'],
    'revenue_expenses': ['G300000'],
}

# Dashboard configuration
DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', '127.0.0.1')
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', '8050'))
VALUATION_PORT = int(os.getenv('VALUATION_PORT', '8051'))

# Database file paths (legacy single-file parquet paths - not used anymore)
# Current system uses partitioned directories instead (e.g., balance_sheet_long/)
PARQUET_FILES = {
    'balance_sheet': DB_PARQUETS_DIR / 'balance_sheet_long.parquet',
    'costs': DB_PARQUETS_DIR / 'costs_long.parquet',
    'revenue': DB_PARQUETS_DIR / 'revenue_long.parquet',
    'revenue_expenses': DB_PARQUETS_DIR / 'revenue_expenses_long.parquet',
}


def get_year_directory(year):
    """Get the directory path for a specific fiscal year.
    
    Args:
        year: Fiscal year (e.g., 2020)
    
    Returns:
        Path object pointing to the year's data directory
    """
    folder_name = HOSP_DATA_PATTERN.format(year=year)
    return DATA_ROOT / folder_name


def get_col_names_file(data_type):
    """Get the column names mapping file for a data type.
    
    Args:
        data_type: Type of data ('balance_sheet', 'costs', 'revenue', 'revenue_expenses')
    
    Returns:
        Path object pointing to the column names CSV file
    
    Raises:
        ValueError: If data_type is not recognized
    """
    if data_type not in COLUMN_NAME_FILES:
        raise ValueError(f"Unknown data type: {data_type}. Must be one of {list(COLUMN_NAME_FILES.keys())}")
    return COLUMN_NAME_FILES[data_type]


def ensure_output_dir():
    """Ensure output directory exists.
    
    Returns:
        Path object pointing to the output directory
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def ensure_logs_dir():
    """Ensure logs directory exists.
    
    Returns:
        Path object pointing to the logs directory
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return LOGS_DIR


def get_worksheets(data_type):
    """Get worksheet codes for a specific data type.
    
    Args:
        data_type: Type of data ('balance_sheet', 'costs', 'revenue', 'revenue_expenses')
    
    Returns:
        List of worksheet codes
    
    Raises:
        ValueError: If data_type is not recognized
    """
    if data_type not in WORKSHEETS:
        raise ValueError(f"Unknown data type: {data_type}. Must be one of {list(WORKSHEETS.keys())}")
    return WORKSHEETS[data_type]