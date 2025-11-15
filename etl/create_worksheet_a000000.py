"""
ETL Script: Create Worksheet A000000 (General Service Cost Centers)

This script extracts worksheet A000000 data from CMS HCRIS source files,
joins with line/column names, and creates a parquet table partitioned by state and fiscal year.

Input:
- data/source_data/HOSP10FY20XX/HOSP10_20XX_nmrc.csv (numeric data)
- data/source_data/HOSP10FY20XX/HOSP10_20XX_rpt.csv (report metadata)
- data/Col_Names/HCRIS_LINE_COL_NAMES.csv (line/column descriptive names)
- data/other_data/ccn_state_codes.csv (state code mapping)

Output:
- data/worksheets/a000000/ (parquet files partitioned by state_code and fiscal_year)

Author: JQ-dev
Date: 2025-11-08
"""

import duckdb
import pandas as pd
from pathlib import Path
import sys
import logging
from datetime import datetime

# Setup logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'create_worksheet_a000000_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Configuration
WORKSHEET_CODE = 'A000000'
STATE_CODES = ['31', '34']  # 31=New Jersey, 34=North Carolina
STATE_NAMES = {'31': 'New Jersey', '34': 'North Carolina'}
FISCAL_YEARS = [2020, 2021, 2022, 2023, 2024]
BASE_DIR = Path(__file__).parent.parent
SOURCE_DATA_DIR = BASE_DIR / 'data' / 'source_data'
COL_NAMES_DIR = BASE_DIR / 'data' / 'Col_Names'
OTHER_DATA_DIR = BASE_DIR / 'data' / 'other_data'
OUTPUT_DIR = BASE_DIR / 'data' / 'worksheets' / 'a000000'

def main():
    """Main ETL process for worksheet A000000"""

    logger.info("="*80)
    logger.info(f"Starting ETL for Worksheet {WORKSHEET_CODE}")
    logger.info(f"Target States: {', '.join([f'{code} ({STATE_NAMES[code]})' for code in STATE_CODES])}")
    logger.info(f"Fiscal Years: {FISCAL_YEARS}")
    logger.info("="*80)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize DuckDB connection
    con = duckdb.connect(':memory:')

    try:
        # Step 1: Load line/column names mapping
        logger.info("Step 1: Loading line/column names mapping...")
        line_col_names_path = COL_NAMES_DIR / 'HCRIS_LINE_COL_NAMES.csv'

        con.execute(f"""
            CREATE TABLE line_col_names AS
            SELECT
                Worksheet,
                LPAD(CAST(Line AS VARCHAR), 5, '0') as Line,
                LPAD(CAST("Column" AS VARCHAR), 5, '0') as "Column",
                Report_Name,
                line_level1,
                line_level2,
                col_level1,
                col_level2
            FROM read_csv_auto('{line_col_names_path}')
            WHERE Worksheet = '{WORKSHEET_CODE}'
        """)

        name_count = con.execute("SELECT COUNT(*) FROM line_col_names").fetchone()[0]
        logger.info(f"   Loaded {name_count} line/column combinations for worksheet {WORKSHEET_CODE}")

        # Step 2: Load state code mapping
        logger.info("Step 2: Loading state code mapping...")
        state_codes_path = OTHER_DATA_DIR / 'ccn_state_codes.csv'

        con.execute(f"""
            CREATE TABLE state_codes AS
            SELECT
                numeric_code,
                state_or_territory,
                postal_abbrev
            FROM read_csv_auto('{state_codes_path}')
        """)

        logger.info(f"   Loaded state codes")

        # Step 3: Process each state and fiscal year
        all_data = []

        for state_code in STATE_CODES:
            state_name = STATE_NAMES[state_code]
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing State {state_code} ({state_name})")
            logger.info(f"{'='*80}")

            for fiscal_year in FISCAL_YEARS:
                logger.info(f"\n  FY {fiscal_year}...")

                fy_dir = SOURCE_DATA_DIR / f'HOSP10FY{fiscal_year}'
                nmrc_file = fy_dir / f'HOSP10_{fiscal_year}_nmrc.csv'
                rpt_file = fy_dir / f'HOSP10_{fiscal_year}_rpt.csv'

                if not nmrc_file.exists():
                    logger.warning(f"    Numeric file not found: {nmrc_file}")
                    continue

                if not rpt_file.exists():
                    logger.warning(f"    Report file not found: {rpt_file}")
                    continue

                # Load report metadata for this state
                con.execute(f"""
                    CREATE OR REPLACE TABLE rpt_{state_code}_{fiscal_year} AS
                    SELECT
                        column00 as RPT_REC_NUM,
                        column01 as PRVDR_CTRL_TYPE_CD,
                        column02 as PRVDR_NUM,
                        column03 as NPI,
                        column04 as RPT_STUS_CD,
                        column05 as FY_BGN_DT,
                        column06 as FY_END_DT,
                        column07 as PROC_DT,
                        column08 as INITL_RPT_SW,
                        column09 as LAST_RPT_SW,
                        column10 as TRNSMTL_NUM,
                        column11 as FI_NUM,
                        column12 as ADR_VNDR_CD,
                        column13 as FI_CREAT_DT,
                        column14 as UTIL_CD,
                        column15 as NPR_DT,
                        column16 as SPEC_IND,
                        column17 as FI_RCPT_DT
                    FROM read_csv_auto('{rpt_file}', header=false)
                    WHERE column02 LIKE '{state_code}%'
                """)

                rpt_count = con.execute(f"SELECT COUNT(*) FROM rpt_{state_code}_{fiscal_year}").fetchone()[0]
                logger.info(f"    Loaded {rpt_count} reports")

                if rpt_count == 0:
                    logger.warning(f"    No reports found for State {state_code} in FY {fiscal_year}")
                    continue

                # Load numeric data and join with metadata and names
                logger.info(f"    Processing numeric data for worksheet {WORKSHEET_CODE}...")

                con.execute(f"""
                    CREATE OR REPLACE TABLE nmrc_{state_code}_{fiscal_year} AS
                    SELECT
                        n.column0 as RPT_REC_NUM,
                        n.column1 as WKSHT_CD,
                        n.column2 as LINE_NUM,
                        n.column3 as CLMN_NUM,
                        n.column4 as ITM_VAL_NUM
                    FROM read_csv_auto('{nmrc_file}', header=false) n
                    WHERE n.column1 = '{WORKSHEET_CODE}'
                        AND n.column0 IN (SELECT RPT_REC_NUM FROM rpt_{state_code}_{fiscal_year})
                """)

                nmrc_count = con.execute(f"SELECT COUNT(*) FROM nmrc_{state_code}_{fiscal_year}").fetchone()[0]
                logger.info(f"    Loaded {nmrc_count} numeric records")

                if nmrc_count == 0:
                    logger.warning(f"    No numeric data found for worksheet {WORKSHEET_CODE}")
                    continue

                # Join everything together
                logger.info(f"    Joining data with line/column names...")

                result = con.execute(f"""
                    SELECT
                        '{state_code}' as State_Code,
                        r.PRVDR_NUM as Provider_Number,
                        {fiscal_year} as Fiscal_Year,
                        r.FY_BGN_DT as FY_Begin_Date,
                        r.FY_END_DT as FY_End_Date,
                        n.WKSHT_CD as Worksheet,
                        n.LINE_NUM as Line,
                        n.CLMN_NUM as "Column",
                        lcn.Report_Name,
                        lcn.line_level1,
                        lcn.line_level2,
                        lcn.col_level1,
                        lcn.col_level2,
                        n.ITM_VAL_NUM as Value
                    FROM nmrc_{state_code}_{fiscal_year} n
                    INNER JOIN rpt_{state_code}_{fiscal_year} r
                        ON n.RPT_REC_NUM = r.RPT_REC_NUM
                    LEFT JOIN line_col_names lcn
                        ON n.LINE_NUM = lcn.Line
                        AND n.CLMN_NUM = lcn."Column"
                    ORDER BY r.PRVDR_NUM, n.LINE_NUM, n.CLMN_NUM
                """).df()

                logger.info(f"    Joined {len(result)} records")

                if len(result) > 0:
                    all_data.append(result)

                    # Show sample
                    logger.info(f"    Sample (first row): Provider {result.iloc[0]['Provider_Number']}, "
                              f"Line {result.iloc[0]['Line']}, Value {result.iloc[0]['Value']}")

        # Step 4: Combine all states/years and save to partitioned parquet
        if all_data:
            logger.info("\n" + "="*80)
            logger.info("Step 4: Combining all data and saving to partitioned parquet...")
            logger.info("="*80)

            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Total records across all states/years: {len(combined_df):,}")

            # Save partitioned by state_code and fiscal_year (Hive style)
            logger.info(f"Writing parquet files to: {OUTPUT_DIR}")
            logger.info(f"Partition structure: state_code=XX/fiscal_year=YYYY/")

            for state_code in combined_df['State_Code'].unique():
                state_data = combined_df[combined_df['State_Code'] == state_code]

                for fy in state_data['Fiscal_Year'].unique():
                    fy_data = state_data[state_data['Fiscal_Year'] == fy]

                    # Create Hive-style partition path
                    partition_path = OUTPUT_DIR / f'state_code={state_code}' / f'fiscal_year={fy}'
                    partition_path.mkdir(parents=True, exist_ok=True)

                    output_file = partition_path / f'data.parquet'

                    # Drop partition columns before saving (Hive partitioning adds them back)
                    save_df = fy_data.drop(columns=['State_Code', 'Fiscal_Year'])
                    save_df.to_parquet(output_file, index=False, engine='pyarrow')

                    logger.info(f"  Saved State {state_code}, FY {fy}: {len(fy_data):,} records")

            # Summary statistics
            logger.info("\n" + "="*80)
            logger.info("ETL SUMMARY")
            logger.info("="*80)
            logger.info(f"Worksheet: {WORKSHEET_CODE}")
            logger.info(f"States: {', '.join([f'{code} ({STATE_NAMES[code]})' for code in STATE_CODES])}")
            logger.info(f"Total Records: {len(combined_df):,}")
            logger.info(f"Unique Providers: {combined_df['Provider_Number'].nunique()}")
            logger.info(f"Fiscal Years: {sorted(combined_df['Fiscal_Year'].unique())}")
            logger.info(f"Output Directory: {OUTPUT_DIR}")
            logger.info(f"Partition Structure: Hive-style (state_code/fiscal_year)")

            # Show data distribution
            logger.info("\nRecords by State and Fiscal Year:")
            for state_code in sorted(combined_df['State_Code'].unique()):
                state_data = combined_df[combined_df['State_Code'] == state_code]
                logger.info(f"\n  State {state_code} ({STATE_NAMES[state_code]}):")
                for fy in sorted(state_data['Fiscal_Year'].unique()):
                    count = len(state_data[state_data['Fiscal_Year'] == fy])
                    providers = state_data[state_data['Fiscal_Year'] == fy]['Provider_Number'].nunique()
                    logger.info(f"    FY {fy}: {count:,} records, {providers} providers")

            logger.info("\n" + "="*80)
            logger.info("QUERY EXAMPLE:")
            logger.info("="*80)
            logger.info("To query this data with DuckDB:")
            logger.info(f"""
import duckdb
con = duckdb.connect(':memory:')

# Query all data
df = con.execute('''
    SELECT *
    FROM read_parquet('{OUTPUT_DIR}/**/*.parquet', hive_partitioning=1)
    LIMIT 10
''').df()

# Query specific state and year
df = con.execute('''
    SELECT *
    FROM read_parquet('{OUTPUT_DIR}/**/*.parquet', hive_partitioning=1)
    WHERE state_code = '31' AND fiscal_year = 2024
''').df()
""")

            logger.info("="*80)
            logger.info("ETL COMPLETED SUCCESSFULLY")
            logger.info("="*80)

        else:
            logger.warning("\nNo data found to process!")
            logger.warning("ETL COMPLETED WITH WARNINGS")

    except Exception as e:
        logger.error(f"\nERROR during ETL: {str(e)}", exc_info=True)
        raise

    finally:
        con.close()
        logger.info(f"\nLog file saved to: {log_file}")

if __name__ == "__main__":
    main()
