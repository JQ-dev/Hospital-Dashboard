import pandas as pd
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging
from config.paths import (
    get_year_directory,
    get_col_names_file,
    FISCAL_YEARS,
    ensure_output_dir,
    PROJECT_ROOT,
    FUND_BALANCE_CHANGES_OUTPUT,
    FILTER_STATES)

# Setup logging
logger = setup_logging('create_fund_balance_changes', log_file='logs/create_fund_balance_changes.log')

def get_files_from_folder(year, base_path):
    # Construct the folder name based on the year
    folder_name = f"HOSP10FY{year}"

    # Initialize list to store specific files
    target_files = {
        'alpha.csv': None,
        'nmrc.csv': None,
        'rpt.csv': None
    }

    try:
        # Walk through the directory tree starting from base_path
        for root, dirs, files in os.walk(base_path):
            # Check if the folder name matches
            if os.path.basename(root) == folder_name:
                # Look for specific files
                for file in files:
                    if file.endswith('alpha.csv'):
                        target_files['alpha.csv'] = os.path.join(root, file)
                    elif file.endswith('nmrc.csv'):
                        target_files['nmrc.csv'] = os.path.join(root, file)
                    elif file.endswith('rpt.csv'):
                        target_files['rpt.csv'] = os.path.join(root, file)

                # Create ordered list of found files (None for missing files)
                result = [
                    target_files['alpha.csv'],
                    target_files['nmrc.csv'],
                    target_files['rpt.csv']
                ]
                return result

        # If folder not found
        return f"No folder named {folder_name} found in {base_path}"

    except Exception as e:
        return f"An error occurred: {str(e)}"

# Years to process (from config)
years = FISCAL_YEARS
base_path = str(PROJECT_ROOT)

all_dfs = []

for year in years:
    try:
        logger.info(f"Processing year {year}")
        hosp10_files = get_files_from_folder(year, base_path)

        if isinstance(hosp10_files, str):
            # Error occurred or folder not found
            logger.warning(f"Skipping year {year}: {hosp10_files}")
            continue

        if not isinstance(hosp10_files, list):
            logger.warning(f"Skipping year {year}: Invalid return type from get_files_from_folder")
            continue

        alpha_file, nmrc_file, rpt_file = hosp10_files

        # Validate files exist
        if not alpha_file or not nmrc_file or not rpt_file:
            logger.warning(f"Skipping year {year}: Missing required files")
            continue

        # Read alpha_df
        logger.debug(f"Reading alpha file for {year}")
        alpha_df = pd.read_csv(
            alpha_file,
            header=None,
            names=['Report_Record_Number', 'Worksheet', 'Line', 'Column', 'Description'],
            converters={
                'Line': lambda x: str(x).strip().zfill(5),
                'Column': lambda x: str(x).strip().zfill(5)
            }
        )

        # Read nmrc_df
        nmrc_df = pd.read_csv(
            nmrc_file,
            header=None,
            names=['Report_Record_Number', 'Worksheet', 'Line', 'Column', 'Value'],
            converters={
                'Line': lambda x: str(x).strip().zfill(5),
                'Column': lambda x: str(x).strip().zfill(5)
            }
        )

        # Read rpt_df
        rpt_df = pd.read_csv(
            rpt_file,
            header=None,
            names=['Report_Record_Number', 'Control_Type', 'Provider_Number', 'NPI', 'Report_Status',
                   'FY_Begin', 'FY_End', 'Process_Date', 'Initial_Report_SW', 'Last_Report_SW', 'Transmit_number',
                   'Geographic_Code', 'ADR_VNDR_CD', 'File_Date', 'UTIL_CD', 'NPR_date', 'SPEC_IND', 'Fiscal_Receipt_Date']
        )

        # Filter to fund balance changes worksheet (G100000) and exclude NULL worksheets
        alpha_df = alpha_df[(alpha_df.Worksheet == 'G100000') & (alpha_df.Worksheet.notna())]
        nmrc_df = nmrc_df[(nmrc_df.Worksheet == 'G100000') & (nmrc_df.Worksheet.notna())]

        logger.debug(f"After filtering: alpha_df has {len(alpha_df)} records, nmrc_df has {len(nmrc_df)} records")

        # Read df_names (using centralized config)
        col_names_file = get_col_names_file('fund_balance_changes')
        df_names = pd.read_csv(
            col_names_file,
            converters={
                'Line': lambda x: str(x).strip().zfill(5),
                'Column': lambda x: str(x).strip().zfill(5)
            }
        )

        # Filter df_names to only G100000
        df_names = df_names[df_names['Worksheet'] == 'G100000']

        # Standardize column names to use underscores
        df_names.columns = df_names.columns.str.replace(' ', '_')

        # Merge nmrc_df with df_names
        merged_df = pd.merge(nmrc_df, df_names, on=['Worksheet', 'Line', 'Column'], how='left')

        # Validate merge: Check for null values
        null_count = merged_df['Acc_name'].isna().sum()
        if null_count > 0:
            logger.warning(f"{null_count} records with null Acc_name after merge in year {year}")
            # Log sample of unmatched records
            unmatched = merged_df[merged_df['Acc_name'].isna()][['Worksheet', 'Line', 'Column']].drop_duplicates().head(5)
            logger.warning(f"Sample unmatched records:\n{unmatched}")

        # Merge with rpt_df
        merged_df = pd.merge(merged_df, rpt_df, on=['Report_Record_Number'], how='left')
        # APPLY STATE FILTER (if configured)
        if FILTER_STATES:
            before_filter = len(merged_df)
            merged_df = merged_df[merged_df['Provider_Number'].astype(str).str[:2].isin(FILTER_STATES)]
            logger.info(f"State filter applied: {before_filter:,} -> {len(merged_df):,} records (kept {len(FILTER_STATES)} states)")

        # Add year column
        merged_df['year'] = year

        all_dfs.append(merged_df)
        logger.info(f"Successfully processed year {year}: {len(merged_df)} records")

    except FileNotFoundError as e:
        logger.error(f"File not found for year {year}: {e}")
        continue
    except pd.errors.ParserError as e:
        logger.error(f"CSV parsing error for year {year}: {e}")
        continue
    except KeyError as e:
        logger.error(f"Missing column in data for year {year}: {e}")
        continue
    except Exception as e:
        logger.error(f"Unexpected error processing year {year}: {e}", exc_info=True)
        continue

# Concatenate all years
if not all_dfs:
    logger.error("No data processed successfully. Exiting.")
    exit(1)

logger.info(f"Concatenating data from {len(all_dfs)} years")
fund_balance_changes = pd.concat(all_dfs, ignore_index=True)

logger.info(f"Total records before deduplication: {len(fund_balance_changes):,}")

# DEDUPLICATION: Keep only the most recent report for each Provider/Fiscal_Year/Line/Column
# Process_Date needs to be datetime for sorting
fund_balance_changes['Process_Date'] = pd.to_datetime(fund_balance_changes['Process_Date'], errors='coerce')
fund_balance_changes['FY_End_dt'] = pd.to_datetime(fund_balance_changes['FY_End'], errors='coerce')
fund_balance_changes['Fiscal_Year_temp'] = fund_balance_changes['FY_End_dt'].dt.year

# Sort by Provider, Fiscal_Year, Line, Column, then Report_Status (desc) and Process_Date (desc)
# This ensures the most recent/highest status report is first
fund_balance_changes = fund_balance_changes.sort_values(
    ['Provider_Number', 'Fiscal_Year_temp', 'Line', 'Column', 'Report_Status', 'Process_Date'],
    ascending=[True, True, True, True, False, False]
)

# Keep first occurrence (most recent report with highest status)
fund_balance_changes = fund_balance_changes.drop_duplicates(
    subset=['Provider_Number', 'Fiscal_Year_temp', 'Line', 'Column'],
    keep='first'
)

fund_balance_changes = fund_balance_changes.drop('Fiscal_Year_temp', axis=1)
logger.info(f"Total records after deduplication: {len(fund_balance_changes):,}")

# Keep in long format - select relevant columns (omit Line_Name and Column_name as requested)
long_df = fund_balance_changes[[
    'Provider_Number', 'year', 'NPI', 'Control_Type', 'Report_Status',
    'FY_Begin', 'FY_End', 'Geographic_Code', 'Worksheet', 'Line', 'Column',
    'Acc_level1', 'Acc_level2', 'Acc_level3', 'Acc_name', 'Value'
]].copy()

# Rename columns for clarity
long_df = long_df.rename(columns={
    'year': 'Year'
})

# Extract fiscal year from FY_End (convert to datetime and get year)
long_df['FY_End'] = pd.to_datetime(long_df['FY_End'], errors='coerce')
long_df['Fiscal_Year'] = long_df['FY_End'].dt.year

# Extract state code from Provider_Number (first 2 characters)
long_df['State_Code'] = long_df['Provider_Number'].astype(str).str[:2]

# Filter out null values (keep zeros as they may be meaningful in fund balance changes)
long_df = long_df[long_df['Value'].notna()]

# Sort for better organization
long_df = long_df.sort_values(['Provider_Number', 'Year', 'Line'])

# Reset index
long_df = long_df.reset_index(drop=True)

# Save to Parquet with partitioning by Fiscal_Year and State_Code
try:
    ensure_output_dir()
    output_dir = FUND_BALANCE_CHANGES_OUTPUT

    # Save with partitioning for better query performance
    long_df.to_parquet(
        output_dir,
        partition_cols=['Fiscal_Year', 'State_Code'],
        index=False,
        engine='pyarrow'
    )

    logger.info(f"Long-format fund balance changes created and saved to {output_dir}")
    logger.info(f"Total records: {len(long_df)}")
    logger.info(f"Years covered: {sorted(long_df['Year'].unique())}")
    logger.info(f"Fiscal years: {sorted(long_df['Fiscal_Year'].dropna().unique())}")
    logger.info(f"States: {sorted(long_df['State_Code'].unique())}")
    logger.info(f"Unique providers: {long_df['Provider_Number'].nunique()}")
    logger.info("Data partitioned by Fiscal_Year and State_Code for optimized queries")
except Exception as e:
    logger.error(f"Error saving parquet file: {e}", exc_info=True)
    raise
