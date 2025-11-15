"""
ETL Script: Create All Worksheets with Multi-State Hive Partitioning

This script extracts all specified CMS HCRIS worksheets from source files,
joins with line/column names, and creates parquet tables partitioned by state and fiscal year.

Input:
- data/source_data/HOSP10FY20XX/HOSP10_20XX_nmrc.csv (numeric data)
- data/source_data/HOSP10FY20XX/HOSP10_20XX_rpt.csv (report metadata)
- data/Col_Names/HCRIS_LINE_COL_NAMES.csv (line/column descriptive names)
- data/other_data/ccn_state_codes.csv (state code mapping)

Output:
- data/worksheets/{worksheet_code}/ (parquet files partitioned by state_code and fiscal_year)

Author: JQ-dev
Date: 2025-11-08
"""

import duckdb
import pandas as pd
from pathlib import Path
import sys
import logging
from datetime import datetime
import time

# Setup logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'create_all_worksheets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

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
WORKSHEET_CODES = [
    'A000000',
    'A6000A0',
    'A700001',
    'A700002',
    'A700003',
    'A800000',
    'A810000',
    'A820010',
    'B000001',
    'B000002',
    'B100000',
    'C000001',
    'G000000',
    'G100000',
    'G200000',
    'G300000',
    'S000001',
    'S100001',
    'S200001',
    'S300001',
    'S300002',
    'S300004',
    'S300005',
    'S410000',
    'S500000'
]

STATE_CODES = ['31', '34']  # 31=New Jersey, 34=North Carolina
STATE_NAMES = {'31': 'New Jersey', '34': 'North Carolina'}
FISCAL_YEARS = [2020, 2021, 2022, 2023, 2024]

BASE_DIR = Path(__file__).parent.parent
SOURCE_DATA_DIR = BASE_DIR / 'data' / 'source_data'
COL_NAMES_DIR = BASE_DIR / 'data' / 'Col_Names'
OTHER_DATA_DIR = BASE_DIR / 'data' / 'other_data'
OUTPUT_BASE_DIR = BASE_DIR / 'data' / 'worksheets'


def process_worksheet(worksheet_code, con):
    """Process a single worksheet"""

    output_dir = OUTPUT_BASE_DIR / worksheet_code.lower()

    logger.info("\n" + "="*80)
    logger.info(f"STARTING WORKSHEET: {worksheet_code}")
    logger.info("="*80)

    start_time = time.time()

    try:
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load line/column names for this worksheet
        logger.info(f"Loading line/column names for {worksheet_code}...")
        line_col_names_path = COL_NAMES_DIR / 'HCRIS_LINE_COL_NAMES.csv'

        con.execute(f"""
            CREATE OR REPLACE TABLE line_col_names_{worksheet_code} AS
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
            WHERE Worksheet = '{worksheet_code}'
        """)

        name_count = con.execute(f"SELECT COUNT(*) FROM line_col_names_{worksheet_code}").fetchone()[0]

        if name_count == 0:
            logger.warning(f"No line/column mappings found for {worksheet_code} - skipping")
            return None

        logger.info(f"  Loaded {name_count} line/column combinations")

        # Process each state and fiscal year
        all_data = []

        for state_code in STATE_CODES:
            state_name = STATE_NAMES[state_code]

            for fiscal_year in FISCAL_YEARS:
                fy_dir = SOURCE_DATA_DIR / f'HOSP10FY{fiscal_year}'
                nmrc_file = fy_dir / f'HOSP10_{fiscal_year}_nmrc.csv'
                rpt_file = fy_dir / f'HOSP10_{fiscal_year}_rpt.csv'

                if not nmrc_file.exists() or not rpt_file.exists():
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

                if rpt_count == 0:
                    continue

                # Load numeric data for this worksheet
                con.execute(f"""
                    CREATE OR REPLACE TABLE nmrc_{worksheet_code}_{state_code}_{fiscal_year} AS
                    SELECT
                        n.column0 as RPT_REC_NUM,
                        n.column1 as WKSHT_CD,
                        n.column2 as LINE_NUM,
                        n.column3 as CLMN_NUM,
                        n.column4 as ITM_VAL_NUM
                    FROM read_csv_auto('{nmrc_file}', header=false) n
                    WHERE n.column1 = '{worksheet_code}'
                        AND n.column0 IN (SELECT RPT_REC_NUM FROM rpt_{state_code}_{fiscal_year})
                """)

                nmrc_count = con.execute(f"SELECT COUNT(*) FROM nmrc_{worksheet_code}_{state_code}_{fiscal_year}").fetchone()[0]

                if nmrc_count == 0:
                    continue

                # Join everything together
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
                    FROM nmrc_{worksheet_code}_{state_code}_{fiscal_year} n
                    INNER JOIN rpt_{state_code}_{fiscal_year} r
                        ON n.RPT_REC_NUM = r.RPT_REC_NUM
                    LEFT JOIN line_col_names_{worksheet_code} lcn
                        ON n.LINE_NUM = lcn.Line
                        AND n.CLMN_NUM = lcn."Column"
                    ORDER BY r.PRVDR_NUM, n.LINE_NUM, n.CLMN_NUM
                """).df()

                if len(result) > 0:
                    all_data.append(result)

        # Save to partitioned parquet
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)

            for state_code in combined_df['State_Code'].unique():
                state_data = combined_df[combined_df['State_Code'] == state_code]

                for fy in state_data['Fiscal_Year'].unique():
                    fy_data = state_data[state_data['Fiscal_Year'] == fy]

                    # Create Hive-style partition path
                    partition_path = output_dir / f'state_code={state_code}' / f'fiscal_year={fy}'
                    partition_path.mkdir(parents=True, exist_ok=True)

                    output_file = partition_path / f'data.parquet'

                    # Drop partition columns before saving
                    save_df = fy_data.drop(columns=['State_Code', 'Fiscal_Year'])
                    save_df.to_parquet(output_file, index=False, engine='pyarrow')

            elapsed_time = time.time() - start_time

            # Summary
            summary = {
                'worksheet': worksheet_code,
                'total_records': len(combined_df),
                'unique_providers': combined_df['Provider_Number'].nunique(),
                'states': len(combined_df['State_Code'].unique()),
                'fiscal_years': len(combined_df['Fiscal_Year'].unique()),
                'output_dir': str(output_dir),
                'elapsed_time': elapsed_time
            }

            logger.info(f"  ✓ Completed: {len(combined_df):,} records, "
                       f"{combined_df['Provider_Number'].nunique()} providers, "
                       f"{elapsed_time:.1f}s")

            return summary
        else:
            logger.warning(f"  No data found for worksheet {worksheet_code}")
            return None

    except Exception as e:
        logger.error(f"  ERROR processing {worksheet_code}: {str(e)}", exc_info=True)
        return None


def main():
    """Main ETL process for all worksheets"""

    logger.info("="*80)
    logger.info("STARTING ETL FOR ALL WORKSHEETS")
    logger.info("="*80)
    logger.info(f"Worksheets to process: {len(WORKSHEET_CODES)}")
    logger.info(f"States: {', '.join([f'{code} ({STATE_NAMES[code]})' for code in STATE_CODES])}")
    logger.info(f"Fiscal Years: {FISCAL_YEARS}")
    logger.info("="*80)

    overall_start = time.time()

    # Initialize DuckDB connection
    con = duckdb.connect(':memory:')

    try:
        # Load state code mapping (once for all worksheets)
        logger.info("\nLoading state code mapping...")
        state_codes_path = OTHER_DATA_DIR / 'ccn_state_codes.csv'

        con.execute(f"""
            CREATE TABLE state_codes AS
            SELECT
                numeric_code,
                state_or_territory,
                postal_abbrev
            FROM read_csv_auto('{state_codes_path}')
        """)

        logger.info("State codes loaded\n")

        # Process each worksheet
        results = []

        for i, worksheet_code in enumerate(WORKSHEET_CODES, 1):
            logger.info(f"\n[{i}/{len(WORKSHEET_CODES)}] Processing {worksheet_code}...")

            result = process_worksheet(worksheet_code, con)

            if result:
                results.append(result)

        # Final summary
        overall_elapsed = time.time() - overall_start

        logger.info("\n" + "="*80)
        logger.info("FINAL SUMMARY")
        logger.info("="*80)
        logger.info(f"Total worksheets processed: {len(results)}/{len(WORKSHEET_CODES)}")
        logger.info(f"Total execution time: {overall_elapsed/60:.1f} minutes")
        logger.info(f"States: {', '.join([f'{code} ({STATE_NAMES[code]})' for code in STATE_CODES])}")

        if results:
            total_records = sum(r['total_records'] for r in results)
            logger.info(f"\nTotal records across all worksheets: {total_records:,}")

            logger.info("\nWorksheet Details:")
            logger.info("-" * 80)
            for r in results:
                logger.info(f"  {r['worksheet']}: {r['total_records']:,} records, "
                          f"{r['unique_providers']} providers, "
                          f"{r['elapsed_time']:.1f}s")

            logger.info("\nOutput Directory Structure:")
            logger.info(f"  {OUTPUT_BASE_DIR}/")
            for r in results:
                logger.info(f"    ├── {r['worksheet'].lower()}/")
                logger.info(f"    │   ├── state_code=31/fiscal_year=20XX/data.parquet")
                logger.info(f"    │   └── state_code=34/fiscal_year=20XX/data.parquet")

        logger.info("\n" + "="*80)
        logger.info("QUERY EXAMPLE:")
        logger.info("="*80)
        logger.info("""
import duckdb
con = duckdb.connect(':memory:')

# Query specific worksheet
df = con.execute('''
    SELECT *
    FROM read_parquet('data/worksheets/a700001/**/*.parquet', hive_partitioning=1)
    WHERE state_code = '31' AND fiscal_year = 2024
    LIMIT 10
''').df()

# Query all worksheets
df = con.execute('''
    SELECT Worksheet, state_code, fiscal_year, COUNT(*) as record_count
    FROM read_parquet('data/worksheets/**/*.parquet', hive_partitioning=1)
    GROUP BY Worksheet, state_code, fiscal_year
    ORDER BY Worksheet, state_code, fiscal_year
''').df()
""")

        logger.info("="*80)
        logger.info("ETL COMPLETED SUCCESSFULLY")
        logger.info("="*80)

    except Exception as e:
        logger.error(f"\nFATAL ERROR: {str(e)}", exc_info=True)
        raise

    finally:
        con.close()
        logger.info(f"\nLog file saved to: {log_file}")


if __name__ == "__main__":
    main()
