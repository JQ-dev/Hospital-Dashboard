"""
Load Income Statement and Expense Detail data into DuckDB for the valuation dashboard
"""

import duckdb
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging
from config.paths import PROJECT_ROOT

logger = setup_logging('load_valuation_data', log_file='logs/load_valuation_data.log')

# Database path
DB_PATH = PROJECT_ROOT / "hospital_analytics.duckdb"

# Data paths
INCOME_STATEMENT_LONG_PATH = PROJECT_ROOT / 'data' / 'output' / 'income_statement_long'
INCOME_STATEMENT_WIDE_PATH = PROJECT_ROOT / 'data' / 'output' / 'income_statement_wide'
EXPENSE_DETAIL_PATH = PROJECT_ROOT / 'data' / 'output' / 'expense_detail'

def create_tables():
    """Create tables in DuckDB and load data from parquet files"""
    logger.info(f"Connecting to database at {DB_PATH}")
    conn = duckdb.connect(str(DB_PATH))

    try:
        # Drop existing tables if they exist
        logger.info("Dropping existing tables if they exist...")
        conn.execute("DROP TABLE IF EXISTS income_statement_long")
        conn.execute("DROP TABLE IF EXISTS income_statement_wide")
        conn.execute("DROP TABLE IF EXISTS expense_detail")

        # Create and load income_statement_long table
        if INCOME_STATEMENT_LONG_PATH.exists():
            logger.info(f"Loading income_statement_long from {INCOME_STATEMENT_LONG_PATH}")
            conn.execute(f"""
                CREATE TABLE income_statement_long AS
                SELECT * FROM read_parquet('{INCOME_STATEMENT_LONG_PATH}/**/*.parquet', hive_partitioning=true)
            """)

            count = conn.execute("SELECT COUNT(*) FROM income_statement_long").fetchone()[0]
            providers = conn.execute("SELECT COUNT(DISTINCT Provider_Number) FROM income_statement_long").fetchone()[0]
            years = conn.execute("SELECT COUNT(DISTINCT Fiscal_Year) FROM income_statement_long").fetchone()[0]
            logger.info(f"Loaded income_statement_long: {count:,} records, {providers} providers, {years} years")

            # Create indexes for better query performance
            conn.execute("CREATE INDEX idx_income_provider_year ON income_statement_long(Provider_Number, Fiscal_Year)")
            logger.info("Created index on income_statement_long")
        else:
            logger.warning(f"Income statement long path not found: {INCOME_STATEMENT_LONG_PATH}")

        # Create and load income_statement_wide table
        if INCOME_STATEMENT_WIDE_PATH.exists():
            logger.info(f"Loading income_statement_wide from {INCOME_STATEMENT_WIDE_PATH}")
            conn.execute(f"""
                CREATE TABLE income_statement_wide AS
                SELECT * FROM read_parquet('{INCOME_STATEMENT_WIDE_PATH}/**/*.parquet', hive_partitioning=true)
            """)

            count = conn.execute("SELECT COUNT(*) FROM income_statement_wide").fetchone()[0]
            logger.info(f"Loaded income_statement_wide: {count:,} records")

            # Create indexes
            conn.execute("CREATE INDEX idx_income_wide_provider_year ON income_statement_wide(Provider_Number, Fiscal_Year)")
            logger.info("Created index on income_statement_wide")
        else:
            logger.warning(f"Income statement wide path not found: {INCOME_STATEMENT_WIDE_PATH}")

        # Create and load expense_detail table
        if EXPENSE_DETAIL_PATH.exists():
            logger.info(f"Loading expense_detail from {EXPENSE_DETAIL_PATH}")
            conn.execute(f"""
                CREATE TABLE expense_detail AS
                SELECT * FROM read_parquet('{EXPENSE_DETAIL_PATH}/**/*.parquet', hive_partitioning=true)
            """)

            count = conn.execute("SELECT COUNT(*) FROM expense_detail").fetchone()[0]
            providers = conn.execute("SELECT COUNT(DISTINCT Provider_Number) FROM expense_detail").fetchone()[0]
            categories = conn.execute("SELECT COUNT(DISTINCT Expense_Category) FROM expense_detail").fetchone()[0]
            logger.info(f"Loaded expense_detail: {count:,} records, {providers} providers, {categories} expense categories")

            # Create indexes
            conn.execute("CREATE INDEX idx_expense_provider_year ON expense_detail(Provider_Number, Fiscal_Year)")
            conn.execute("CREATE INDEX idx_expense_category ON expense_detail(Expense_Category)")
            logger.info("Created indexes on expense_detail")
        else:
            logger.warning(f"Expense detail path not found: {EXPENSE_DETAIL_PATH}")

        # Print summary statistics
        logger.info("\n" + "="*60)
        logger.info("DATABASE SUMMARY")
        logger.info("="*60)

        tables = conn.execute("SHOW TABLES").fetchall()
        logger.info(f"\nTables created: {len(tables)}")
        for table in tables:
            table_name = table[0]
            count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            logger.info(f"  - {table_name}: {count:,} records")

        # Sample query to verify data
        logger.info("\nSample query - Top 5 hospitals by Net Patient Revenue:")
        sample = conn.execute("""
            SELECT
                Provider_Number,
                Fiscal_Year,
                Value as Net_Patient_Revenue
            FROM income_statement_long
            WHERE Line_Name = 'Net_Patient_Revenue'
            ORDER BY Value DESC
            LIMIT 5
        """).fetchdf()

        if not sample.empty:
            logger.info("\n" + sample.to_string())
        else:
            logger.warning("No sample data found")

        logger.info("\n" + "="*60)
        logger.info("Data loading completed successfully!")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Error loading data: {e}", exc_info=True)
        raise
    finally:
        conn.close()
        logger.info("Database connection closed")


if __name__ == '__main__':
    logger.info("Starting data load process...")
    create_tables()
    logger.info("Data load process completed")
