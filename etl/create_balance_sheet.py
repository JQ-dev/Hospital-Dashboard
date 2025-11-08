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
    BALANCE_SHEET_OUTPUT,
    FILTER_STATES)

# Setup logging
logger = setup_logging('create_balance_sheet', log_file='logs/create_balance_sheet.log')

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

        # Filter to balance sheet worksheet (G000000) and exclude NULL worksheets
        alpha_df = alpha_df[(alpha_df.Worksheet == 'G000000') & (alpha_df.Worksheet.notna())]
        nmrc_df = nmrc_df[(nmrc_df.Worksheet == 'G000000') & (nmrc_df.Worksheet.notna())]

        logger.debug(f"After filtering: alpha_df has {len(alpha_df)} records, nmrc_df has {len(nmrc_df)} records")

        # Read df_names (using centralized config)
        col_names_file = get_col_names_file('balance_sheet')
        df_names = pd.read_csv(
            col_names_file,
            converters={
                'Line': lambda x: str(x).strip().zfill(5),
                'Column': lambda x: str(x).strip().zfill(5)
            }
        )

        # Standardize column names to use underscores (already uses underscores but this ensures consistency)
        df_names.columns = df_names.columns.str.replace(' ', '_')

        # Load column mapping file for Column_name descriptions
        column_mapping_file = PROJECT_ROOT / 'data' / 'other_data' / 'balance_sheet_columns.csv'
        df_column_names = pd.read_csv(
            column_mapping_file,
            converters={
                'Column': lambda x: str(x).strip().zfill(5)
            }
        )
        logger.info(f"Loaded column mapping with {len(df_column_names)} column definitions")

        # Merge nmrc_df with df_names
        merged_df = pd.merge(nmrc_df, df_names, on=['Worksheet', 'Line', 'Column'], how='left')

        # Validate merge: Check for null Line_Name values
        null_count = merged_df['Line_Name'].isna().sum()
        if null_count > 0:
            logger.warning(f"{null_count} records with null Line_Name after merge in year {year}")
            # Log sample of unmatched records
            unmatched = merged_df[merged_df['Line_Name'].isna()][['Worksheet', 'Line', 'Column']].drop_duplicates().head(5)
            logger.warning(f"Sample unmatched records:\n{unmatched}")

        # Merge with column mapping to add Column_name
        merged_df = pd.merge(merged_df, df_column_names, on='Column', how='left')
        logger.info(f"Added Column_name field via merge")

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
balance_sheet = pd.concat(all_dfs, ignore_index=True)

logger.info(f"Total records before deduplication: {len(balance_sheet):,}")

# DEDUPLICATION: Keep only the most recent report for each Provider/Fiscal_Year/Line/Column
# Process_Date needs to be datetime for sorting
balance_sheet['Process_Date'] = pd.to_datetime(balance_sheet['Process_Date'], errors='coerce')
balance_sheet['FY_End_dt'] = pd.to_datetime(balance_sheet['FY_End'], errors='coerce')
balance_sheet['Fiscal_Year_temp'] = balance_sheet['FY_End_dt'].dt.year

# Sort by Provider, Fiscal_Year, Line, Column, then Report_Status (desc) and Process_Date (desc)
# This ensures the most recent/highest status report is first
balance_sheet = balance_sheet.sort_values(
    ['Provider_Number', 'Fiscal_Year_temp', 'Line', 'Column', 'Report_Status', 'Process_Date'],
    ascending=[True, True, True, True, False, False]
)

# Keep first occurrence (most recent report with highest status)
balance_sheet = balance_sheet.drop_duplicates(
    subset=['Provider_Number', 'Fiscal_Year_temp', 'Line', 'Column'],
    keep='first'
)

balance_sheet = balance_sheet.drop('Fiscal_Year_temp', axis=1)
logger.info(f"Total records after deduplication: {len(balance_sheet):,}")

# Add Column_name mapping after deduplication (in case it was lost during concat)
column_mapping_file = PROJECT_ROOT / 'data' / 'other_data' / 'balance_sheet_columns.csv'
df_column_names_final = pd.read_csv(
    column_mapping_file,
    converters={
        'Column': lambda x: str(x).strip().zfill(5)
    }
)
balance_sheet = pd.merge(balance_sheet, df_column_names_final, on='Column', how='left', suffixes=('', '_new'))
# If Column_name exists twice (once from year loop, once from here), keep the new one
if 'Column_name_new' in balance_sheet.columns:
    balance_sheet['Column_name'] = balance_sheet['Column_name_new']
    balance_sheet = balance_sheet.drop('Column_name_new', axis=1)
logger.info(f"Verified Column_name field exists")

# Create KPI column for long format
balance_sheet['Major'] = balance_sheet['Line_Name'].str.split().str[0]
balance_sheet['Subcategory'] = balance_sheet['Line_Name'].str.split().str[1]
balance_sheet['Item'] = balance_sheet['Line_Name'].str.split(n=2).str[2].str.replace(' ', '_').str.replace(',', '').str.replace('(', '').str.replace(')', '').str.replace('"', '')
balance_sheet['Fund'] = balance_sheet['Column_name'].str.replace(' ', '_')
balance_sheet['KPI'] = balance_sheet['Fund'] + '_' + balance_sheet['Major'] + '_' + balance_sheet['Subcategory'] + '_' + balance_sheet['Item']

# Keep in long format - select relevant columns (including Column_name for dashboard)
long_df = balance_sheet[['Provider_Number', 'year', 'KPI', 'Value', 'NPI', 'Control_Type', 'Report_Status', 'FY_Begin', 'FY_End', 'Geographic_Code', 'Worksheet', 'Line', 'Column', 'Column_name', 'Acc_level1', 'Acc_level2', 'Acc_level3', 'Acc_name']].copy()

# Rename columns for clarity
long_df = long_df.rename(columns={
    'year': 'Year',
    'KPI': 'Account_Name'
})

# Extract fiscal year from FY_End (convert to datetime and get year)
long_df['FY_End'] = pd.to_datetime(long_df['FY_End'], errors='coerce')
long_df['Fiscal_Year'] = long_df['FY_End'].dt.year

# Extract state code from Provider_Number (first 2 characters)
long_df['State_Code'] = long_df['Provider_Number'].astype(str).str[:2]

# Filter out null and zero values
# NOTE: This removes accounts with no activity. If you need to preserve zero balances,
# comment out the zero filter: (long_df['Value'] != 0)
long_df = long_df[long_df['Value'].notna() & (long_df['Value'] != 0)]

# Sort for better organization
long_df = long_df.sort_values(['Provider_Number', 'Year', 'Account_Name'])

# Reset index
long_df = long_df.reset_index(drop=True)

# Save to Parquet with partitioning by Fiscal_Year and State_Code (ensure output directory exists)
try:
    ensure_output_dir()
    output_dir = BALANCE_SHEET_OUTPUT

    # Save with partitioning for better query performance
    long_df.to_parquet(
        output_dir,
        partition_cols=['Fiscal_Year', 'State_Code'],
        index=False,
        engine='pyarrow'
    )

    logger.info(f"Long-format balance sheet created and saved to {output_dir}")
    logger.info(f"Total records: {len(long_df)}")
    logger.info(f"Years covered: {sorted(long_df['Year'].unique())}")
    logger.info(f"Fiscal years: {sorted(long_df['Fiscal_Year'].dropna().unique())}")
    logger.info(f"States: {sorted(long_df['State_Code'].unique())}")
    logger.info(f"Unique providers: {long_df['Provider_Number'].nunique()}")
    logger.info(f"Unique accounts: {long_df['Account_Name'].nunique()}")
    logger.info("Data partitioned by Fiscal_Year and State_Code for optimized queries")
except Exception as e:
    logger.error(f"Error saving parquet file: {e}", exc_info=True)
    raise