import pandas as pd
import os
import sys
from pathlib import Path

# Optional: small perf win, safer assignment semantics (pandas 2.1+)
pd.options.mode.copy_on_write = True

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging
from config.paths import (
    get_year_directory,
    get_col_names_file,
    FISCAL_YEARS,
    ensure_output_dir,
    PROJECT_ROOT,
    COSTS_B100_OUTPUT,
    FILTER_STATES)

# Setup logging
logger = setup_logging('create_costs_b100', log_file='logs/create_costs_b100.log')

def rollup_to_hundred(value):
    """Roll up a number to the nearest hundred (downward)
    Examples: 101 -> 100, 102 -> 100, 199 -> 100, 200 -> 200, 1250 -> 1200
    """
    return (int(value) // 100) * 100

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

                # Create ordered list of found files
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

        # Filter to costs B000001 worksheet
        alpha_df = alpha_df[(alpha_df.Worksheet == 'B000001') & (alpha_df.Worksheet.notna())]
        nmrc_df = nmrc_df[(nmrc_df.Worksheet == 'B000001') & (nmrc_df.Worksheet.notna())]

        logger.debug(f"After filtering: alpha_df has {len(alpha_df)} records, nmrc_df has {len(nmrc_df)} records")

        # IMPLEMENT ROLL-UP LOGIC BEFORE MERGING
        # Convert Line and Column to integers for roll-up (coerce non-numeric to NaN)
        nmrc_df['Line_Int'] = pd.to_numeric(nmrc_df['Line'], errors='coerce')
        nmrc_df['Column_Int'] = pd.to_numeric(nmrc_df['Column'], errors='coerce')

        # Filter out rows with non-numeric Line or Column values
        before_filter = len(nmrc_df)
        nmrc_df = nmrc_df[nmrc_df['Line_Int'].notna() & nmrc_df['Column_Int'].notna()]
        filtered_count = before_filter - len(nmrc_df)
        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} records with non-numeric Line/Column values")

        # Vectorized roll-up to hundreds (faster than .apply)
        nmrc_df['Line_Rollup'] = (nmrc_df['Line_Int'] // 100).astype('int64') * 100
        nmrc_df['Column_Rollup'] = (nmrc_df['Column_Int'] // 100).astype('int64') * 100

        # Group by Report_Record_Number, Worksheet, rolled-up Line and Column, and sum values
        logger.info(f"Applying roll-up aggregation for year {year}...")
        nmrc_rollup = nmrc_df.groupby(
            ['Report_Record_Number', 'Worksheet', 'Line_Rollup', 'Column_Rollup'],
            as_index=False
        ).agg({'Value': 'sum'})

        # Convert rolled-up Line and Column back to 5-digit strings for matching
        nmrc_rollup['Line'] = nmrc_rollup['Line_Rollup'].astype(str).str.zfill(5)
        nmrc_rollup['Column'] = nmrc_rollup['Column_Rollup'].astype(str).str.zfill(5)

        # Drop the intermediate columns
        nmrc_rollup = nmrc_rollup.drop(['Line_Rollup', 'Column_Rollup'], axis=1)

        logger.info(f"After roll-up: {len(nmrc_rollup)} records (reduced from {len(nmrc_df)})")

        # Read df_names (using centralized config)
        col_names_file = get_col_names_file('costs_b100')
        df_names = pd.read_csv(
            col_names_file,
            converters={
                'Line': lambda x: str(x).strip().zfill(5),
                'Column': lambda x: str(x).strip().zfill(5)
            }
        )

        # Filter df_names to only B000001
        df_names = df_names[df_names['Worksheet'] == 'B000001']

        # Standardize column names
        df_names.columns = df_names.columns.str.replace(' ', '_')

        # Merge nmrc_rollup with df_names
        merged_df = pd.merge(nmrc_rollup, df_names, on=['Worksheet', 'Line', 'Column'], how='left')

        # Validate merge
        null_count = merged_df['Account_name'].isna().sum()
        if null_count > 0:
            logger.warning(f"{null_count} records with null Account_name after merge in year {year}")

        # Merge with rpt_df
        merged_df = pd.merge(merged_df, rpt_df, on=['Report_Record_Number'], how='left')
        # APPLY STATE FILTER (if configured)
        if FILTER_STATES:
            before_filter = len(merged_df)
            merged_df = merged_df[merged_df['Provider_Number'].astype(str).str[:2].isin(FILTER_STATES)]
            logger.info(f"State filter applied: {before_filter:,} -> {len(merged_df):,} records (kept {len(FILTER_STATES)} states)")

        # Add year column
        merged_df['year'] = year

        # CALCULATE COLUMNS 02400 and 02600 — vectorized (replaces slow Python loop)
        logger.info(f"Calculating columns 02400 (Subtotal) and 02600 (Total) for year {year}...")

        keys = ['Report_Record_Number', 'Worksheet', 'Line']

        # 02400 = sum of column 00000 + 00100..02300
        subtotal_cols = ['00000'] + [f'{i:05d}' for i in range(100, 2400, 100)]

        # Sum only needed columns for 02400
        subtotals = (
            merged_df.loc[merged_df['Column'].isin(subtotal_cols), keys + ['Value']]
            .groupby(keys, as_index=False, sort=False)['Value']
            .sum()
            .rename(columns={'Value': 'Value_02400'})
        )

        # Sum 02500 if present
        c025 = (
            merged_df.loc[merged_df['Column'].eq('02500'), keys + ['Value']]
            .groupby(keys, as_index=False, sort=False)['Value']
            .sum()
            .rename(columns={'Value': 'Value_02500'})
        )

        # Combine and compute 02600
        add = subtotals.merge(c025, on=keys, how='left')
        add['Value_02500'] = add['Value_02500'].fillna(0)
        add['02400'] = add['Value_02400']
        add['02600'] = add['Value_02400'] + add['Value_02500']

        # Long format; keep only non-zero rows
        add_long = add.melt(id_vars=keys, value_vars=['02400', '02600'],
                            var_name='Column', value_name='Value')
        add_long = add_long[add_long['Value'] != 0]

        # Attach metadata columns (take first occurrence per key, same as your iloc[0] behavior)
        meta_cols = ['Account_group', 'Account_name', 'Overhead_center']
        meta = merged_df.drop_duplicates(subset=keys, keep='first')[keys + meta_cols]
        add_long = add_long.merge(meta, on=keys, how='left')

        # Set Overhead_center labels for the two new columns
        add_long['Overhead_center'] = add_long['Column'].map({'02400': 'Subtotal', '02600': 'Total'})

        # Append
        merged_df = pd.concat([merged_df, add_long], ignore_index=True)
        logger.info(f"Added {len(add_long):,} calculated rows for columns 02400 and 02600")

        all_dfs.append(merged_df)
        logger.info(f"Successfully processed year {year}: {len(merged_df)} records")

    except Exception as e:
        logger.error(f"Unexpected error processing year {year}: {e}", exc_info=True)
        continue

# Concatenate all years
if not all_dfs:
    logger.error("No data processed successfully. Exiting.")
    exit(1)

logger.info(f"Concatenating data from {len(all_dfs)} years")
costs_b100 = pd.concat(all_dfs, ignore_index=True)

logger.info(f"Total records before deduplication: {len(costs_b100):,}")

# DEDUPLICATION: Keep only the most recent report for each Provider/Fiscal_Year/Line/Column
# Process_Date needs to be datetime for sorting
costs_b100['Process_Date'] = pd.to_datetime(costs_b100['Process_Date'], errors='coerce')
costs_b100['FY_End_dt'] = pd.to_datetime(costs_b100['FY_End'], errors='coerce')
costs_b100['Fiscal_Year_temp'] = costs_b100['FY_End_dt'].dt.year

# Sort by Provider, Fiscal_Year, Line, Column, then Report_Status (desc) and Process_Date (desc)
# This ensures the most recent/highest status report is first
costs_b100 = costs_b100.sort_values(
    ['Provider_Number', 'Fiscal_Year_temp', 'Line', 'Column', 'Report_Status', 'Process_Date'],
    ascending=[True, True, True, True, False, False]
)

# Keep first occurrence (most recent report with highest status)
costs_b100 = costs_b100.drop_duplicates(
    subset=['Provider_Number', 'Fiscal_Year_temp', 'Line', 'Column'],
    keep='first'
)

costs_b100 = costs_b100.drop('Fiscal_Year_temp', axis=1)
logger.info(f"Total records after deduplication: {len(costs_b100):,}")

# Keep in long format - select relevant columns (NO Line_Name or Column_name)
long_df = costs_b100[[
    'Provider_Number', 'year', 'NPI', 'Control_Type', 'Report_Status',
    'FY_Begin', 'FY_End', 'Geographic_Code', 'Worksheet', 'Line', 'Column',
    'Account_group', 'Account_name', 'Overhead_center', 'Value'
]].copy()

# Rename columns for clarity
long_df = long_df.rename(columns={'year': 'Year'})

# Extract fiscal year from FY_End
long_df['FY_End'] = pd.to_datetime(long_df['FY_End'], errors='coerce')
long_df['Fiscal_Year'] = long_df['FY_End'].dt.year

# Extract state code from Provider_Number
long_df['State_Code'] = long_df['Provider_Number'].astype(str).str[:2]

# Filter out null values
long_df = long_df[long_df['Value'].notna()]

# Sort for better organization
long_df = long_df.sort_values(['Provider_Number', 'Year', 'Line', 'Column'])

# Reset index
long_df = long_df.reset_index(drop=True)

# Save to Parquet with partitioning
try:
    ensure_output_dir()
    output_dir = COSTS_B100_OUTPUT

    # Save with partitioning for better query performance
    long_df.to_parquet(
        output_dir,
        partition_cols=['Fiscal_Year', 'State_Code'],
        index=False,
        engine='pyarrow'
    )

    logger.info(f"Costs B100 (rolled-up) created and saved to {output_dir}")
    logger.info(f"Total records: {len(long_df):,}")
    logger.info(f"Years covered: {sorted(long_df['Year'].unique())}")
    logger.info(f"Fiscal years: {sorted(long_df['Fiscal_Year'].dropna().unique())}")
    logger.info(f"States: {sorted(long_df['State_Code'].unique())}")
    logger.info(f"Unique providers: {long_df['Provider_Number'].nunique()}")
    logger.info("Data partitioned by Fiscal_Year and State_Code for optimized queries")
except Exception as e:
    logger.error(f"Error saving parquet file: {e}", exc_info=True)
    raise
