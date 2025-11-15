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
logger = setup_logging('create_expense_detail', log_file='logs/create_expense_detail.log')

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

# Define expense categories based on Worksheet A line numbers
EXPENSE_CATEGORIES = {
    'Capital_Costs': {
        'lines': ['00100', '00200', '00300'],
        'description': 'Building and Equipment Capital Costs',
        'category_type': 'Capital'
    },
    'Administrative_General': {
        'lines': ['00500'],
        'description': 'Administrative and General',
        'category_type': 'General_Service'
    },
    'Employee_Benefits': {
        'lines': ['00400'],
        'description': 'Employee Benefits',
        'category_type': 'General_Service'
    },
    'Plant_Operations': {
        'lines': ['00600', '00700', '00800', '00900'],
        'description': 'Maintenance, Plant Operation, Laundry, Housekeeping',
        'category_type': 'General_Service'
    },
    'Dietary_Cafeteria': {
        'lines': ['01000', '01100'],
        'description': 'Dietary and Cafeteria',
        'category_type': 'General_Service'
    },
    'Nursing_Administration': {
        'lines': ['01300'],
        'description': 'Nursing Administration',
        'category_type': 'General_Service'
    },
    'Medical_Records_Social': {
        'lines': ['01600', '01700'],
        'description': 'Medical Records and Social Services',
        'category_type': 'General_Service'
    },
    'Inpatient_Routine': {
        'lines': [f'{i:05d}' for i in range(3000, 4700)],
        'description': 'Inpatient Routine Services (General, ICU, Subproviders)',
        'category_type': 'Revenue_Producing'
    },
    'Radiology': {
        'lines': ['05000', '05100', '05200', '05300', '05400'],
        'description': 'Radiology (Diagnostic, Therapeutic, CT, MRI, Nuclear)',
        'category_type': 'Ancillary'
    },
    'Laboratory': {
        'lines': ['05500', '05600'],
        'description': 'Laboratory (Clinical, Pathology)',
        'category_type': 'Ancillary'
    },
    'Blood_Storage': {
        'lines': ['05700', '05800'],
        'description': 'Blood Storage and Processing',
        'category_type': 'Ancillary'
    },
    'Operating_Room': {
        'lines': ['06000', '06100'],
        'description': 'Operating Room and Recovery Room',
        'category_type': 'Ancillary'
    },
    'Anesthesiology': {
        'lines': ['06200'],
        'description': 'Anesthesiology',
        'category_type': 'Ancillary'
    },
    'Cardiology': {
        'lines': ['06400', '06500'],
        'description': 'Cardiology and Cardiac Catheterization',
        'category_type': 'Ancillary'
    },
    'Emergency': {
        'lines': ['09100'],
        'description': 'Emergency Services',
        'category_type': 'Outpatient'
    },
    'Pharmacy': {
        'lines': ['06800'],
        'description': 'Pharmacy',
        'category_type': 'Ancillary'
    },
    'Physical_Therapy': {
        'lines': ['07000'],
        'description': 'Physical Therapy',
        'category_type': 'Ancillary'
    },
    'Occupational_Therapy': {
        'lines': ['07100'],
        'description': 'Occupational Therapy',
        'category_type': 'Ancillary'
    },
    'Speech_Pathology': {
        'lines': ['07200'],
        'description': 'Speech Pathology',
        'category_type': 'Ancillary'
    },
    'Medical_Education': {
        'lines': ['02100', '02200', '02300'],
        'description': 'Interns, Residents, and Education Programs',
        'category_type': 'Medical_Education'
    },
    'Other_Outpatient': {
        'lines': ['08800', '08900', '09000', '09200', '09300'],
        'description': 'Clinics, RHC, FQHC, Observation',
        'category_type': 'Outpatient'
    },
    'Other_Reimbursable': {
        'lines': [f'{i:05d}' for i in range(9400, 10200)],
        'description': 'Dialysis, Ambulance, DME, Home Health',
        'category_type': 'Other_Reimbursable'
    }
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

        # Filter to Worksheet A (Trial Balance)
        nmrc_df = nmrc_df[
            (nmrc_df.Worksheet == 'A000000') &
            (nmrc_df.Worksheet.notna())
        ]

        # Keep only Column 3 (Total = Salaries + Other) and Column 7 (Final adjusted)
        nmrc_df = nmrc_df[nmrc_df.Column.isin(['00300', '00700'])]

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
expense_detail = pd.concat(all_dfs, ignore_index=True)

logger.info(f"Total records before deduplication: {len(expense_detail):,}")

# DEDUPLICATION
expense_detail['Process_Date'] = pd.to_datetime(expense_detail['Process_Date'], errors='coerce')
expense_detail['FY_End_dt'] = pd.to_datetime(expense_detail['FY_End'], errors='coerce')
expense_detail['Fiscal_Year_temp'] = expense_detail['FY_End_dt'].dt.year

expense_detail = expense_detail.sort_values(
    ['Provider_Number', 'Fiscal_Year_temp', 'Line', 'Column', 'Report_Status', 'Process_Date'],
    ascending=[True, True, True, True, False, False]
)

expense_detail = expense_detail.drop_duplicates(
    subset=['Provider_Number', 'Fiscal_Year_temp', 'Line', 'Column'],
    keep='first'
)

expense_detail = expense_detail.drop('Fiscal_Year_temp', axis=1)
logger.info(f"Total records after deduplication: {len(expense_detail):,}")

# Add expense category classification
def classify_expense_category(line):
    """Classify expense line into category"""
    for category_name, category_info in EXPENSE_CATEGORIES.items():
        if line in category_info['lines']:
            return category_name, category_info['description'], category_info['category_type']
    return 'Other', 'Other Expenses', 'Other'

expense_detail[['Expense_Category', 'Category_Description', 'Category_Type']] = expense_detail['Line'].apply(
    lambda x: pd.Series(classify_expense_category(x))
)

# Create descriptive column name
expense_detail['Column_Description'] = expense_detail['Column'].map({
    '00300': 'Total_Before_Adjustments',
    '00700': 'Final_Adjusted'
})

# Extract fiscal year
expense_detail['FY_End'] = pd.to_datetime(expense_detail['FY_End'], errors='coerce')
expense_detail['Fiscal_Year'] = expense_detail['FY_End'].dt.year

# Extract state code
expense_detail['State_Code'] = expense_detail['Provider_Number'].astype(str).str[:2]

# Filter out null and zero values
expense_detail = expense_detail[expense_detail['Value'].notna() & (expense_detail['Value'] != 0)]

# Select relevant columns
expense_detail_final = expense_detail[[
    'Provider_Number', 'year', 'Fiscal_Year', 'State_Code',
    'NPI', 'Control_Type', 'Report_Status', 'FY_Begin', 'FY_End', 'Geographic_Code',
    'Worksheet', 'Line', 'Column', 'Column_Description',
    'Expense_Category', 'Category_Description', 'Category_Type',
    'Value'
]].copy()

# Sort
expense_detail_final = expense_detail_final.sort_values(['Provider_Number', 'Fiscal_Year', 'Expense_Category'])

# Reset index
expense_detail_final = expense_detail_final.reset_index(drop=True)

# Save to Parquet
try:
    ensure_output_dir()
    output_dir = PROJECT_ROOT / 'data' / 'output' / 'expense_detail'

    # Save with partitioning
    expense_detail_final.to_parquet(
        output_dir,
        partition_cols=['Fiscal_Year', 'State_Code'],
        index=False,
        engine='pyarrow'
    )

    logger.info(f"Expense detail table created and saved to {output_dir}")
    logger.info(f"Total records: {len(expense_detail_final):,}")
    logger.info(f"Years covered: {sorted(expense_detail_final['year'].unique())}")
    logger.info(f"Fiscal years: {sorted(expense_detail_final['Fiscal_Year'].dropna().unique())}")
    logger.info(f"States: {sorted(expense_detail_final['State_Code'].unique())}")
    logger.info(f"Unique providers: {expense_detail_final['Provider_Number'].nunique()}")
    logger.info(f"Expense categories: {sorted(expense_detail_final['Expense_Category'].unique())}")

    # Print summary by category type
    summary = expense_detail_final.groupby(['Category_Type', 'Expense_Category']).agg({
        'Value': 'sum',
        'Provider_Number': 'nunique'
    }).round(0)
    logger.info(f"\nExpense summary by category:\n{summary}")

except Exception as e:
    logger.error(f"Error saving parquet file: {e}", exc_info=True)
    raise

logger.info("Expense detail ETL completed successfully")
