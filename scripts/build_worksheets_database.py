"""
Build DuckDB Database from Worksheet Parquet Files

This script creates a consolidated DuckDB database from all worksheet parquet files,
with proper indexing and optimizations for fast queries.

Input:
- data/worksheets/**/**.parquet (Hive-partitioned parquet files)

Output:
- data/hospital_worksheets.duckdb (Optimized DuckDB database)

Author: JQ-dev
Date: 2025-11-08
"""

import duckdb
from pathlib import Path
import sys
import logging
from datetime import datetime
import time

# Setup logging
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f'build_database_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

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
BASE_DIR = Path(__file__).parent.parent
WORKSHEETS_DIR = BASE_DIR / 'data' / 'worksheets'
DATABASE_PATH = BASE_DIR / 'data' / 'hospital_worksheets.duckdb'

# List of worksheets to include
WORKSHEETS = [
    'a000000',  # General Service Cost Centers
    'a6000a0',  # Reclassifications
    'a700001',  # Reconciliation of Capital Costs Centers
    'a700002',  # Reconciliation of Capital Costs Centers
    'a700003',  # Reconciliation of Capital Costs Centers
    'a800000',  # Adjustments to Expenses
    'a810000',  # Costs Incurred - Related Organizations
    'a820010',  # Provider-Based Physicians Adjustments
    'b000001',  # Cost Allocation - General Service Costs
    'b000002',  # Cost Allocation - General Service Costs
    'b100000',  # Cost Allocation - General Service Costs
    'c000001',  # Cost Allocation - General Service Costs
    'g000000',  # Balance Sheet
    'g100000',  # Statement of Changes in Fund Balances
    'g200000',  # Statement of Patient Revenues
    'g300000',  # Statement of Revenues
    's000001',  # Settlement Summary
    's100001',  # Hospital Uncompensated & Indigent Care Data
    's200001',  # Hospital & Healthcare Complex ID Data
    's300001',  # Statistical Data
    's300002',  # Statistical Data
    's300004',  # Hospital Wage Related Costs
    's300005',  # Hospital Wage Related Costs
    's410000',  # Hospital Wage Related Costs
    's500000',  # Hospital Renal Dialysis Department
]


def create_worksheet_table(con, worksheet_code):
    """Create a table for a specific worksheet from parquet files"""

    worksheet_dir = WORKSHEETS_DIR / worksheet_code
    parquet_pattern = str(worksheet_dir / '**' / '*.parquet')

    table_name = f'worksheet_{worksheet_code}'

    logger.info(f"Creating table: {table_name}")

    try:
        # Check if parquet files exist
        if not worksheet_dir.exists():
            logger.warning(f"  Directory not found: {worksheet_dir}")
            return None

        # Create table from parquet files with Hive partitioning
        con.execute(f"""
            CREATE TABLE {table_name} AS
            SELECT
                state_code,
                fiscal_year,
                Provider_Number,
                FY_Begin_Date,
                FY_End_Date,
                Worksheet,
                Line,
                "Column",
                Report_Name,
                line_level1,
                line_level2,
                col_level1,
                col_level2,
                Value
            FROM read_parquet('{parquet_pattern}', hive_partitioning=1)
        """)

        # Get record count
        count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

        logger.info(f"  ✓ Created {table_name}: {count:,} records")

        return {
            'table': table_name,
            'worksheet': worksheet_code.upper(),
            'records': count
        }

    except Exception as e:
        logger.error(f"  ERROR creating {table_name}: {str(e)}")
        return None


def create_indexes(con, table_name):
    """Create indexes on a worksheet table"""

    logger.info(f"  Creating indexes on {table_name}...")

    try:
        # Index on state_code and fiscal_year (common filters)
        con.execute(f"""
            CREATE INDEX idx_{table_name}_state_year
            ON {table_name} (state_code, fiscal_year)
        """)

        # Index on Provider_Number (common join key)
        con.execute(f"""
            CREATE INDEX idx_{table_name}_provider
            ON {table_name} (Provider_Number)
        """)

        # Index on Line and Column (common filters)
        con.execute(f"""
            CREATE INDEX idx_{table_name}_line_col
            ON {table_name} (Line, "Column")
        """)

        # Composite index for common query pattern
        con.execute(f"""
            CREATE INDEX idx_{table_name}_composite
            ON {table_name} (state_code, fiscal_year, Provider_Number)
        """)

        logger.info(f"  ✓ Indexes created")

    except Exception as e:
        logger.error(f"  ERROR creating indexes: {str(e)}")


def create_unified_view(con):
    """Create a unified view across all worksheets"""

    logger.info("\nCreating unified view: all_worksheets")

    try:
        # Get list of all worksheet tables
        tables = con.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
                AND table_name LIKE 'worksheet_%'
            ORDER BY table_name
        """).fetchall()

        if not tables:
            logger.warning("  No worksheet tables found")
            return

        # Build UNION ALL query
        union_queries = []
        for (table_name,) in tables:
            union_queries.append(f"SELECT * FROM {table_name}")

        union_query = " UNION ALL ".join(union_queries)

        # Create view
        con.execute(f"""
            CREATE VIEW all_worksheets AS
            {union_query}
        """)

        # Get total count
        count = con.execute("SELECT COUNT(*) FROM all_worksheets").fetchone()[0]

        logger.info(f"  ✓ View created: {count:,} total records across all worksheets")

    except Exception as e:
        logger.error(f"  ERROR creating unified view: {str(e)}")


def create_summary_tables(con):
    """Create summary tables for quick lookups"""

    logger.info("\nCreating summary tables...")

    try:
        # Summary by worksheet, state, and year
        logger.info("  Creating worksheet_summary table...")
        con.execute("""
            CREATE TABLE worksheet_summary AS
            SELECT
                Worksheet,
                state_code,
                fiscal_year,
                COUNT(*) as record_count,
                COUNT(DISTINCT Provider_Number) as provider_count,
                MIN(FY_Begin_Date) as min_fy_begin,
                MAX(FY_End_Date) as max_fy_end
            FROM all_worksheets
            GROUP BY Worksheet, state_code, fiscal_year
            ORDER BY Worksheet, state_code, fiscal_year
        """)

        summary_count = con.execute("SELECT COUNT(*) FROM worksheet_summary").fetchone()[0]
        logger.info(f"  ✓ worksheet_summary: {summary_count:,} rows")

        # Provider list with state mapping
        logger.info("  Creating provider_list table...")
        con.execute("""
            CREATE TABLE provider_list AS
            SELECT DISTINCT
                Provider_Number,
                state_code,
                MIN(fiscal_year) as first_fiscal_year,
                MAX(fiscal_year) as last_fiscal_year,
                COUNT(DISTINCT fiscal_year) as fiscal_year_count
            FROM all_worksheets
            GROUP BY Provider_Number, state_code
            ORDER BY state_code, Provider_Number
        """)

        provider_count = con.execute("SELECT COUNT(*) FROM provider_list").fetchone()[0]
        logger.info(f"  ✓ provider_list: {provider_count:,} providers")

    except Exception as e:
        logger.error(f"  ERROR creating summary tables: {str(e)}")


def optimize_database(con):
    """Optimize database for query performance"""

    logger.info("\nOptimizing database...")

    try:
        # Analyze tables for query optimizer
        logger.info("  Running ANALYZE on all tables...")
        con.execute("ANALYZE")

        # Checkpoint to write all changes to disk
        logger.info("  Running CHECKPOINT...")
        con.execute("CHECKPOINT")

        logger.info("  ✓ Optimization complete")

    except Exception as e:
        logger.error(f"  ERROR optimizing database: {str(e)}")


def print_database_info(con):
    """Print database statistics"""

    logger.info("\n" + "="*80)
    logger.info("DATABASE INFORMATION")
    logger.info("="*80)

    try:
        # List all tables
        tables = con.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_type, table_name
        """).fetchall()

        logger.info(f"\nTables and Views ({len(tables)} total):")
        for table_name, table_type in tables:
            if table_type == 'BASE TABLE':
                count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                logger.info(f"  [TABLE] {table_name}: {count:,} records")
            else:
                logger.info(f"  [VIEW]  {table_name}")

        # Database file size
        import os
        if DATABASE_PATH.exists():
            size_mb = os.path.getsize(DATABASE_PATH) / (1024 * 1024)
            logger.info(f"\nDatabase file size: {size_mb:.1f} MB")

        # Sample query examples
        logger.info("\n" + "="*80)
        logger.info("QUERY EXAMPLES")
        logger.info("="*80)
        logger.info("""
# Connect to database
import duckdb
con = duckdb.connect('data/hospital_worksheets.duckdb', read_only=True)

# Query specific worksheet
df = con.execute('''
    SELECT *
    FROM worksheet_b000001
    WHERE state_code = '31' AND fiscal_year = 2024
    LIMIT 10
''').df()

# Query across all worksheets
df = con.execute('''
    SELECT *
    FROM all_worksheets
    WHERE Provider_Number = '310001'
        AND fiscal_year = 2024
''').df()

# Get summary statistics
df = con.execute('''
    SELECT *
    FROM worksheet_summary
    ORDER BY Worksheet, state_code, fiscal_year
''').df()

# List all providers
df = con.execute('''
    SELECT *
    FROM provider_list
    WHERE state_code = '31'
''').df()

# Join multiple worksheets
df = con.execute('''
    SELECT
        b1.Provider_Number,
        b1.fiscal_year,
        b1.Value as balance_sheet_value,
        b2.Value as income_stmt_value
    FROM worksheet_b000001 b1
    INNER JOIN worksheet_b000002 b2
        ON b1.Provider_Number = b2.Provider_Number
        AND b1.state_code = b2.state_code
        AND b1.fiscal_year = b2.fiscal_year
        AND b1.Line = b2.Line
    WHERE b1.state_code = '31'
        AND b1.fiscal_year = 2024
''').df()
""")

    except Exception as e:
        logger.error(f"ERROR getting database info: {str(e)}")


def main():
    """Main database build process"""

    logger.info("="*80)
    logger.info("BUILDING DUCKDB DATABASE FROM WORKSHEET PARQUET FILES")
    logger.info("="*80)
    logger.info(f"Worksheets directory: {WORKSHEETS_DIR}")
    logger.info(f"Output database: {DATABASE_PATH}")
    logger.info(f"Worksheets to process: {len(WORKSHEETS)}")
    logger.info("="*80)

    start_time = time.time()

    # Remove existing database
    if DATABASE_PATH.exists():
        logger.info(f"\nRemoving existing database: {DATABASE_PATH}")
        DATABASE_PATH.unlink()

    # Create new database
    logger.info(f"\nCreating new database: {DATABASE_PATH}\n")

    try:
        # Connect to database
        con = duckdb.connect(str(DATABASE_PATH))

        # Set configuration for better performance
        con.execute("SET memory_limit='4GB'")
        con.execute("SET threads=4")

        # Create tables for each worksheet
        results = []

        for i, worksheet_code in enumerate(WORKSHEETS, 1):
            logger.info(f"\n[{i}/{len(WORKSHEETS)}] Processing {worksheet_code.upper()}...")

            result = create_worksheet_table(con, worksheet_code)

            if result:
                results.append(result)

                # Create indexes
                create_indexes(con, result['table'])

        # Create unified view
        create_unified_view(con)

        # Create summary tables
        create_summary_tables(con)

        # Optimize database
        optimize_database(con)

        # Print database info
        print_database_info(con)

        # Close connection
        con.close()

        elapsed_time = time.time() - start_time

        # Final summary
        logger.info("\n" + "="*80)
        logger.info("BUILD COMPLETE")
        logger.info("="*80)
        logger.info(f"Tables created: {len(results)}/{len(WORKSHEETS)}")
        logger.info(f"Total records: {sum(r['records'] for r in results):,}")
        logger.info(f"Database location: {DATABASE_PATH}")
        logger.info(f"Execution time: {elapsed_time/60:.1f} minutes")
        logger.info("="*80)

        logger.info("\nDatabase is ready for queries!")

    except Exception as e:
        logger.error(f"\nFATAL ERROR: {str(e)}", exc_info=True)
        raise

    finally:
        logger.info(f"\nLog file: {log_file}")


if __name__ == "__main__":
    main()
