import pandas as pd
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging
from config.paths import (
    get_year_directory,
    FISCAL_YEARS,
    ensure_output_dir,
    PROJECT_ROOT,
    FILTER_STATES)

# Setup logging
logger = setup_logging('create_income_statement', log_file='logs/create_income_statement.log')

def get_files_from_folder(year, base_path):
    """Get alpha, nmrc, rpt files for a given year"""
    folder_name = f"HOSP10FY{year}"
    target_files = {
        'alpha.csv': None,
        'nmrc.csv': None,
        'rpt.csv': None
    }

    try:
        for root, dirs, files in os.walk(base_path):
            if os.path.basename(root) == folder_name:
                for file in files:
                    if file.endswith('alpha.csv'):
                        target_files['alpha.csv'] = os.path.join(root, file)
                    elif file.endswith('nmrc.csv'):
                        target_files['nmrc.csv'] = os.path.join(root, file)
                    elif file.endswith('rpt.csv'):
                        target_files['rpt.csv'] = os.path.join(root, file)

                return [
                    target_files['alpha.csv'],
                    target_files['nmrc.csv'],
                    target_files['rpt.csv']
                ]

        return f"No folder named {folder_name} found in {base_path}"

    except Exception as e:
        return f"An error occurred: {str(e)}"

# Define line mappings for Worksheet G-3 (Income Statement)
INCOME_STATEMENT_LINES = {
    # Revenue Section
    '00100': {'name': 'Total_Patient_Revenue_Gross', 'section': 'Revenue', 'subsection': 'Gross_Revenue'},
    '00200': {'name': 'Total_Allowances_And_Discounts', 'section': 'Revenue', 'subsection': 'Deductions'},
    '00300': {'name': 'Net_Patient_Revenue', 'section': 'Revenue', 'subsection': 'Net_Revenue', 'key_metric': True},

    # Operating Expenses
    '00400': {'name': 'Total_Operating_Expenses', 'section': 'Operating_Expenses', 'subsection': 'Total_Expenses'},

    # Operating Income
    '00500': {'name': 'Operating_Income', 'section': 'Operating_Income', 'subsection': 'Operating_Income', 'key_metric': True},

    # Other Income (Non-Operating)
    '00600': {'name': 'Investment_Income', 'section': 'Other_Income', 'subsection': 'Investment'},
    '00700': {'name': 'Purchase_Discounts', 'section': 'Other_Income', 'subsection': 'Operational'},
    '00800': {'name': 'Income_From_Rentals', 'section': 'Other_Income', 'subsection': 'Property'},
    '00900': {'name': 'Income_From_Scrap_Salvage', 'section': 'Other_Income', 'subsection': 'Operational'},
    '01000': {'name': 'Proceeds_From_Asset_Sales', 'section': 'Other_Income', 'subsection': 'Asset_Disposal'},
    '01100': {'name': 'Cafeteria_Income_Visitors', 'section': 'Other_Income', 'subsection': 'Operational'},
    '01200': {'name': 'Medical_Pharmacy_Supply_Sales', 'section': 'Other_Income', 'subsection': 'Operational'},
    '01300': {'name': 'Vending_Machine_Income', 'section': 'Other_Income', 'subsection': 'Operational'},
    '01400': {'name': 'Gift_Flower_Shop_Income', 'section': 'Other_Income', 'subsection': 'Operational'},
    '01500': {'name': 'Contributions_Donations_Bequests', 'section': 'Other_Income', 'subsection': 'Donations'},
    '01600': {'name': 'Educational_Program_Income', 'section': 'Other_Income', 'subsection': 'Education'},
    '01700': {'name': 'Research_Grants', 'section': 'Other_Income', 'subsection': 'Research'},
    '01800': {'name': 'Miscellaneous_Income', 'section': 'Other_Income', 'subsection': 'Miscellaneous'},
    '01900': {'name': 'Related_Organization_Income', 'section': 'Other_Income', 'subsection': 'Related_Organizations'},
    '02000': {'name': 'Transfers_From_Restricted_Funds', 'section': 'Other_Income', 'subsection': 'Fund_Transfers'},
    '02100': {'name': 'EHR_Incentive_Payments', 'section': 'Other_Income', 'subsection': 'Government_Programs'},
    '02200': {'name': 'COVID_Relief_Funds', 'section': 'Other_Income', 'subsection': 'COVID_Related'},
    '02300': {'name': 'Other_Funding', 'section': 'Other_Income', 'subsection': 'Government_Programs'},
    '02400': {'name': 'Other_Specify', 'section': 'Other_Income', 'subsection': 'Miscellaneous'},
    '02450': {'name': 'COVID_PHE_Funding', 'section': 'Other_Income', 'subsection': 'COVID_Related'},
    '02451': {'name': 'Provider_Relief_Fund', 'section': 'Other_Income', 'subsection': 'COVID_Related'},
    '02452': {'name': 'Accelerated_Medicare_Payments', 'section': 'Other_Income', 'subsection': 'COVID_Related'},
    '02500': {'name': 'Total_Other_Income', 'section': 'Other_Income', 'subsection': 'Total_Other_Income'},

    # Total Income
    '02600': {'name': 'Total_Income_Before_Other_Expenses', 'section': 'Total_Income', 'subsection': 'Total_Income'},

    # Other Expenses (Non-Operating)
    '02700': {'name': 'Other_Expenses_Specify', 'section': 'Other_Expenses', 'subsection': 'Other_Expenses'},
    '02800': {'name': 'Total_Other_Expenses', 'section': 'Other_Expenses', 'subsection': 'Total_Other_Expenses'},

    # Net Income
    '02900': {'name': 'Net_Income', 'section': 'Net_Income', 'subsection': 'Net_Income', 'key_metric': True},
}

# Years to process
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
            logger.warning(f"Skipping year {year}: Invalid return type")
            continue

        alpha_file, nmrc_file, rpt_file = hosp10_files

        if not alpha_file or not nmrc_file or not rpt_file:
            logger.warning(f"Skipping year {year}: Missing required files")
            continue

        # Read nmrc_df (numeric data)
        logger.debug(f"Reading nmrc file for {year}")
        nmrc_df = pd.read_csv(
            nmrc_file,
            header=None,
            names=['Report_Record_Number', 'Worksheet', 'Line', 'Column', 'Value'],
            converters={
                'Line': lambda x: str(x).strip().zfill(5),
                'Column': lambda x: str(x).strip().zfill(5)
            }
        )

        # Read rpt_df (metadata)
        rpt_df = pd.read_csv(
            rpt_file,
            header=None,
            names=['Report_Record_Number', 'Control_Type', 'Provider_Number', 'NPI', 'Report_Status',
                   'FY_Begin', 'FY_End', 'Process_Date', 'Initial_Report_SW', 'Last_Report_SW', 'Transmit_number',
                   'Geographic_Code', 'ADR_VNDR_CD', 'File_Date', 'UTIL_CD', 'NPR_date', 'SPEC_IND', 'Fiscal_Receipt_Date']
        )

        # Filter to Worksheet G-3 (Income Statement), Column 1 (General Fund)
        nmrc_df = nmrc_df[
            (nmrc_df.Worksheet == 'G300000') &
            (nmrc_df.Column == '00100') &
            (nmrc_df.Worksheet.notna())
        ]

        logger.debug(f"After filtering: nmrc_df has {len(nmrc_df)} records")

        # Merge with rpt_df
        merged_df = pd.merge(nmrc_df, rpt_df, on=['Report_Record_Number'], how='left')

        # Apply state filter
        if FILTER_STATES:
            before_filter = len(merged_df)
            merged_df = merged_df[merged_df['Provider_Number'].astype(str).str[:2].isin(FILTER_STATES)]
            logger.info(f"State filter applied: {before_filter:,} -> {len(merged_df):,} records")

        # Add year column
        merged_df['year'] = year

        all_dfs.append(merged_df)
        logger.info(f"Successfully processed year {year}: {len(merged_df)} records")

    except Exception as e:
        logger.error(f"Error processing year {year}: {e}", exc_info=True)
        continue

# Concatenate all years
if not all_dfs:
    logger.error("No data processed successfully. Exiting.")
    exit(1)

logger.info(f"Concatenating data from {len(all_dfs)} years")
income_statement = pd.concat(all_dfs, ignore_index=True)

logger.info(f"Total records before deduplication: {len(income_statement):,}")

# DEDUPLICATION
income_statement['Process_Date'] = pd.to_datetime(income_statement['Process_Date'], errors='coerce')
income_statement['FY_End_dt'] = pd.to_datetime(income_statement['FY_End'], errors='coerce')
income_statement['Fiscal_Year_temp'] = income_statement['FY_End_dt'].dt.year

income_statement = income_statement.sort_values(
    ['Provider_Number', 'Fiscal_Year_temp', 'Line', 'Report_Status', 'Process_Date'],
    ascending=[True, True, True, False, False]
)

income_statement = income_statement.drop_duplicates(
    subset=['Provider_Number', 'Fiscal_Year_temp', 'Line'],
    keep='first'
)

income_statement = income_statement.drop('Fiscal_Year_temp', axis=1)
logger.info(f"Total records after deduplication: {len(income_statement):,}")

# Add line classifications
def classify_income_statement_line(line):
    """Classify income statement line"""
    if line in INCOME_STATEMENT_LINES:
        info = INCOME_STATEMENT_LINES[line]
        return (
            info['name'],
            info['section'],
            info['subsection'],
            info.get('key_metric', False)
        )
    return ('Unknown', 'Other', 'Other', False)

income_statement[['Line_Name', 'Section', 'Subsection', 'Key_Metric']] = income_statement['Line'].apply(
    lambda x: pd.Series(classify_income_statement_line(x))
)

# Extract fiscal year
income_statement['FY_End'] = pd.to_datetime(income_statement['FY_End'], errors='coerce')
income_statement['Fiscal_Year'] = income_statement['FY_End'].dt.year

# Extract state code
income_statement['State_Code'] = income_statement['Provider_Number'].astype(str).str[:2]

# Select relevant columns (keep long format for flexibility)
income_statement_final = income_statement[[
    'Provider_Number', 'year', 'Fiscal_Year', 'State_Code',
    'NPI', 'Control_Type', 'Report_Status', 'FY_Begin', 'FY_End', 'Geographic_Code',
    'Worksheet', 'Line', 'Line_Name', 'Section', 'Subsection', 'Key_Metric',
    'Value'
]].copy()

# Sort
income_statement_final = income_statement_final.sort_values(['Provider_Number', 'Fiscal_Year', 'Line'])

# Reset index
income_statement_final = income_statement_final.reset_index(drop=True)

# Save to Parquet (long format)
try:
    ensure_output_dir()
    output_dir_long = PROJECT_ROOT / 'data' / 'output' / 'income_statement_long'

    # Save with partitioning
    income_statement_final.to_parquet(
        output_dir_long,
        partition_cols=['Fiscal_Year', 'State_Code'],
        index=False,
        engine='pyarrow'
    )

    logger.info(f"Income statement (long format) saved to {output_dir_long}")
    logger.info(f"Total records: {len(income_statement_final):,}")

    # Also create wide format for easier dashboard use
    income_statement_wide = income_statement_final.pivot_table(
        index=['Provider_Number', 'Fiscal_Year', 'State_Code', 'NPI', 'Control_Type',
               'FY_Begin', 'FY_End', 'Geographic_Code'],
        columns='Line_Name',
        values='Value',
        aggfunc='sum'
    ).reset_index()

    # Calculate key derived metrics
    if 'Net_Patient_Revenue' in income_statement_wide.columns and 'Operating_Income' in income_statement_wide.columns:
        income_statement_wide['Operating_Margin'] = (
            income_statement_wide['Operating_Income'] /
            income_statement_wide['Net_Patient_Revenue'].replace(0, pd.NA) * 100
        )

    if 'Net_Patient_Revenue' in income_statement_wide.columns and 'Net_Income' in income_statement_wide.columns:
        income_statement_wide['Net_Margin'] = (
            income_statement_wide['Net_Income'] /
            income_statement_wide['Net_Patient_Revenue'].replace(0, pd.NA) * 100
        )

    # Save wide format
    output_dir_wide = PROJECT_ROOT / 'data' / 'output' / 'income_statement_wide'
    income_statement_wide.to_parquet(
        output_dir_wide,
        partition_cols=['Fiscal_Year', 'State_Code'],
        index=False,
        engine='pyarrow'
    )

    logger.info(f"Income statement (wide format) saved to {output_dir_wide}")
    logger.info(f"Total providers: {income_statement_wide['Provider_Number'].nunique()}")
    logger.info(f"Years covered: {sorted(income_statement_final['year'].unique())}")
    logger.info(f"Fiscal years: {sorted(income_statement_final['Fiscal_Year'].dropna().unique())}")
    logger.info(f"States: {sorted(income_statement_final['State_Code'].unique())}")

    # Print summary statistics for key metrics
    key_metrics = income_statement_final[income_statement_final['Key_Metric'] == True]
    summary = key_metrics.groupby('Line_Name')['Value'].agg(['count', 'mean', 'median', 'sum'])
    logger.info(f"\nKey metrics summary:\n{summary}")

except Exception as e:
    logger.error(f"Error saving parquet files: {e}", exc_info=True)
    raise

logger.info("Income statement ETL completed successfully")
