"""
Build Optimized Hospital Analytics Database

Pre-computes KPIs and benchmarks to make dashboard queries instant.

Database Schema:
- hospital_kpis: Pre-computed KPIs for every hospital/year
- hospital_benchmarks: Pre-computed benchmarks (P25, Median, P75, Mean) by level/year
- balance_sheet, revenue, revenue_expenses, costs: Raw financial data with indexes
"""

import duckdb
import logging
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.paths import (
    BALANCE_SHEET_OUTPUT,
    FUND_BALANCE_CHANGES_OUTPUT,
    REVENUE_OUTPUT,
    REVENUE_EXPENSES_OUTPUT,
    COSTS_OUTPUT,
    COSTS_A000_OUTPUT,
    COSTS_B100_OUTPUT
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Define data paths using centralized config
BALANCE_SHEET_PATH = str(BALANCE_SHEET_OUTPUT / '**/*.parquet')
FUND_BALANCE_CHANGES_PATH = str(FUND_BALANCE_CHANGES_OUTPUT / '**/*.parquet')
REVENUE_PATH = str(REVENUE_OUTPUT / '**/*.parquet')
REVENUE_EXPENSES_PATH = str(REVENUE_EXPENSES_OUTPUT / '**/*.parquet')
COSTS_PATH = str(COSTS_OUTPUT / '**/*.parquet')
COSTS_A000_PATH = str(COSTS_A000_OUTPUT / '**/*.parquet')
COSTS_B100_PATH = str(COSTS_B100_OUTPUT / '**/*.parquet')


def classify_hospital_type(ccn):
    """Classify hospital type by CCN range"""
    if not ccn or len(str(ccn)) != 6:
        return 'Unknown'

    provider_num = int(str(ccn)[2:])

    if 1 <= provider_num <= 899:
        return 'Short Term Acute Care'
    elif 3300 <= provider_num <= 3399:
        return "Children's"
    elif 1300 <= provider_num <= 1399:
        return 'Critical Access'
    elif 2000 <= provider_num <= 2299:
        return 'Long Term'
    elif 4000 <= provider_num <= 4499:
        return 'Psychiatric'
    elif 3025 <= provider_num <= 3099:
        return 'Rehabilitation'
    else:
        return 'Other'


def build_raw_tables(con):
    """Build raw financial tables with indexes"""
    logger.info("=" * 80)
    logger.info("STEP 1: Building raw financial tables")
    logger.info("=" * 80)

    # BALANCE SHEET
    logger.info("Creating balance_sheet table...")
    con.execute(f"""
        CREATE OR REPLACE TABLE balance_sheet AS
        SELECT
            *,
            -- Fix State_Code: extract from zero-padded CCN
            CAST(SUBSTRING(LPAD(CAST(Provider_Number AS VARCHAR), 6, '0'), 1, 2) AS INTEGER) as State_Code_Fixed
        FROM read_parquet('{BALANCE_SHEET_PATH}', hive_partitioning=1, union_by_name=true)
    """)

    # Replace incorrect State_Code with fixed version
    con.execute("ALTER TABLE balance_sheet DROP COLUMN State_Code")
    con.execute("ALTER TABLE balance_sheet RENAME COLUMN State_Code_Fixed TO State_Code")

    logger.info("Creating indexes on balance_sheet...")
    con.execute("CREATE INDEX idx_bs_provider ON balance_sheet(Provider_Number)")
    con.execute("CREATE INDEX idx_bs_year ON balance_sheet(Fiscal_Year)")
    con.execute("CREATE INDEX idx_bs_provider_year ON balance_sheet(Provider_Number, Fiscal_Year)")

    count = con.execute("SELECT COUNT(*) as cnt FROM balance_sheet").fetchone()[0]
    logger.info(f"Balance sheet: {count:,} records loaded")

    # FUND BALANCE CHANGES
    logger.info("Creating fund_balance_changes table...")
    con.execute(f"""
        CREATE OR REPLACE TABLE fund_balance_changes AS
        SELECT *
        FROM read_parquet('{FUND_BALANCE_CHANGES_PATH}', hive_partitioning=1, union_by_name=true)
    """)

    logger.info("Creating indexes on fund_balance_changes...")
    con.execute("CREATE INDEX idx_fbc_provider ON fund_balance_changes(Provider_Number)")
    con.execute("CREATE INDEX idx_fbc_year ON fund_balance_changes(Fiscal_Year)")
    con.execute("CREATE INDEX idx_fbc_provider_year ON fund_balance_changes(Provider_Number, Fiscal_Year)")

    count = con.execute("SELECT COUNT(*) as cnt FROM fund_balance_changes").fetchone()[0]
    logger.info(f"Fund balance changes: {count:,} records loaded")

    # REVENUE
    logger.info("Creating revenue table...")
    con.execute(f"""
        CREATE OR REPLACE TABLE revenue AS
        SELECT *
        FROM read_parquet('{REVENUE_PATH}', hive_partitioning=1, union_by_name=true)
    """)

    logger.info("Creating indexes on revenue...")
    con.execute("CREATE INDEX idx_rev_provider ON revenue(Provider_Number)")
    con.execute("CREATE INDEX idx_rev_year ON revenue(Fiscal_Year)")
    con.execute("CREATE INDEX idx_rev_provider_year ON revenue(Provider_Number, Fiscal_Year)")

    count = con.execute("SELECT COUNT(*) as cnt FROM revenue").fetchone()[0]
    logger.info(f"Revenue: {count:,} records loaded")

    # REVENUE & EXPENSES
    logger.info("Creating revenue_expenses table...")
    con.execute(f"""
        CREATE OR REPLACE TABLE revenue_expenses AS
        SELECT *
        FROM read_parquet('{REVENUE_EXPENSES_PATH}', hive_partitioning=1, union_by_name=true)
    """)

    logger.info("Creating indexes on revenue_expenses...")
    con.execute("CREATE INDEX idx_re_provider ON revenue_expenses(Provider_Number)")
    con.execute("CREATE INDEX idx_re_year ON revenue_expenses(Fiscal_Year)")
    con.execute("CREATE INDEX idx_re_provider_year ON revenue_expenses(Provider_Number, Fiscal_Year)")

    count = con.execute("SELECT COUNT(*) as cnt FROM revenue_expenses").fetchone()[0]
    logger.info(f"Revenue & Expenses: {count:,} records loaded")

    # COSTS (Legacy - commented out, now using costs_a000 and costs_b100 separately)
    # logger.info("Creating costs table (this may take several minutes)...")
    # con.execute(f"""
    #     CREATE OR REPLACE TABLE costs AS
    #     SELECT *
    #     FROM read_parquet('{COSTS_PATH}', hive_partitioning=1, union_by_name=true)
    # """)
    #
    # logger.info("Creating indexes on costs...")
    # con.execute("CREATE INDEX idx_costs_provider ON costs(Provider_Number)")
    # con.execute("CREATE INDEX idx_costs_year ON costs(Fiscal_Year)")
    # con.execute("CREATE INDEX idx_costs_provider_year ON costs(Provider_Number, Fiscal_Year)")
    #
    # count = con.execute("SELECT COUNT(*) as cnt FROM costs").fetchone()[0]
    # logger.info(f"Costs: {count:,} records loaded")

    # COSTS A000 (Cost Centers with roll-up)
    logger.info("Creating costs_a000 table...")
    con.execute(f"""
        CREATE OR REPLACE TABLE costs_a000 AS
        SELECT *
        FROM read_parquet('{COSTS_A000_PATH}', hive_partitioning=1, union_by_name=true)
    """)

    logger.info("Creating indexes on costs_a000...")
    con.execute("CREATE INDEX idx_costs_a000_provider ON costs_a000(Provider_Number)")
    con.execute("CREATE INDEX idx_costs_a000_year ON costs_a000(Fiscal_Year)")
    con.execute("CREATE INDEX idx_costs_a000_provider_year ON costs_a000(Provider_Number, Fiscal_Year)")

    count = con.execute("SELECT COUNT(*) as cnt FROM costs_a000").fetchone()[0]
    logger.info(f"Costs A000 (rolled-up): {count:,} records loaded")

    # COSTS B100 (Overhead Costs with roll-up)
    logger.info("Creating costs_b100 table...")
    con.execute(f"""
        CREATE OR REPLACE TABLE costs_b100 AS
        SELECT *
        FROM read_parquet('{COSTS_B100_PATH}', hive_partitioning=1, union_by_name=true)
    """)

    logger.info("Creating indexes on costs_b100...")
    con.execute("CREATE INDEX idx_costs_b100_provider ON costs_b100(Provider_Number)")
    con.execute("CREATE INDEX idx_costs_b100_year ON costs_b100(Fiscal_Year)")
    con.execute("CREATE INDEX idx_costs_b100_provider_year ON costs_b100(Provider_Number, Fiscal_Year)")

    count = con.execute("SELECT COUNT(*) as cnt FROM costs_b100").fetchone()[0]
    logger.info(f"Costs B100 (rolled-up): {count:,} records loaded")


def build_kpi_table(con):
    """Build pre-computed KPI table for all hospitals and years"""
    logger.info("=" * 80)
    logger.info("STEP 2: Building hospital_kpis table (pre-computing all KPIs)")
    logger.info("=" * 80)

    logger.info("Computing KPIs for all hospital-year combinations...")

    # Build comprehensive KPI table with all metrics
    con.execute("""
        CREATE OR REPLACE TABLE hospital_kpis AS
        WITH
        -- Balance sheet metrics
        balance_metrics AS (
            SELECT
                Provider_Number,
                Fiscal_Year,
                SUM(CASE WHEN Acc_level2 = 'Assets' AND Acc_level3 LIKE '%Current%' THEN Value ELSE 0 END) as Current_Assets,
                SUM(CASE WHEN Acc_level2 = 'Assets' AND Acc_level3 LIKE '%Fixed%' THEN Value ELSE 0 END) as Fixed_Assets,
                SUM(CASE WHEN Acc_level2 = 'Assets' THEN Value ELSE 0 END) as Total_Assets,
                SUM(CASE WHEN Acc_level2 = 'Liabilities' AND Acc_level3 LIKE '%Current%' THEN Value ELSE 0 END) as Current_Liabilities,
                SUM(CASE WHEN Acc_level2 = 'Liabilities' THEN Value ELSE 0 END) as Total_Liabilities,
                SUM(CASE WHEN Acc_level1 = 'Fund Balances' OR Acc_level2 = 'Fund Balances' THEN Value ELSE 0 END) as Fund_Balance,
                SUM(CASE WHEN Acc_name LIKE '%Cash%' OR Acc_name LIKE '%Marketable%' THEN Value ELSE 0 END) as Cash_And_Securities,
                SUM(CASE WHEN Acc_name LIKE '%receivable%' THEN Value ELSE 0 END) as Accounts_Receivable
            FROM balance_sheet
            GROUP BY Provider_Number, Fiscal_Year
        ),

        -- Revenue metrics
        revenue_metrics AS (
            SELECT
                Provider_Number,
                Fiscal_Year,
                SUM(CASE WHEN Revenue_Line_Name LIKE '%Inpatient%' THEN Value ELSE 0 END) as Inpatient_Revenue,
                SUM(CASE WHEN Revenue_Line_Name LIKE '%Outpatient%' THEN Value ELSE 0 END) as Outpatient_Revenue,
                SUM(Value) as Total_Revenue
            FROM revenue
            GROUP BY Provider_Number, Fiscal_Year
        ),

        -- Expense metrics
        expense_metrics AS (
            SELECT
                Provider_Number,
                Fiscal_Year,
                SUM(Value) as Total_Operating_Expenses
            FROM revenue_expenses
            GROUP BY Provider_Number, Fiscal_Year
        ),

        -- Net Income from fund_balance_changes (actual reported net income)
        net_income_metrics AS (
            SELECT
                Provider_Number,
                Fiscal_Year,
                NULLIF(SUM(CASE WHEN Acc_name = 'Net income (loss)'
                     THEN Value ELSE 0 END), 0) as Net_Income
            FROM fund_balance_changes
            GROUP BY Provider_Number, Fiscal_Year
        ),

        -- Join all metrics
        combined AS (
            SELECT
                COALESCE(b.Provider_Number, r.Provider_Number, e.Provider_Number, n.Provider_Number) as Provider_Number,
                COALESCE(b.Fiscal_Year, r.Fiscal_Year, e.Fiscal_Year, n.Fiscal_Year) as Fiscal_Year,
                b.Current_Assets,
                b.Fixed_Assets,
                b.Total_Assets,
                b.Current_Liabilities,
                b.Total_Liabilities,
                b.Fund_Balance,
                b.Cash_And_Securities,
                b.Accounts_Receivable,
                r.Inpatient_Revenue,
                r.Outpatient_Revenue,
                r.Total_Revenue,
                e.Total_Operating_Expenses,
                COALESCE(n.Net_Income, (r.Total_Revenue - e.Total_Operating_Expenses)) as Net_Income
            FROM balance_metrics b
            FULL OUTER JOIN revenue_metrics r ON b.Provider_Number = r.Provider_Number AND b.Fiscal_Year = r.Fiscal_Year
            FULL OUTER JOIN expense_metrics e ON COALESCE(b.Provider_Number, r.Provider_Number) = e.Provider_Number
                AND COALESCE(b.Fiscal_Year, r.Fiscal_Year) = e.Fiscal_Year
            FULL OUTER JOIN net_income_metrics n ON COALESCE(b.Provider_Number, r.Provider_Number, e.Provider_Number) = n.Provider_Number
                AND COALESCE(b.Fiscal_Year, r.Fiscal_Year, e.Fiscal_Year) = n.Fiscal_Year
        )

        -- Calculate all KPIs
        SELECT
            Provider_Number,
            Fiscal_Year,

            -- Raw financial metrics
            Current_Assets,
            Fixed_Assets,
            Total_Assets,
            Current_Liabilities,
            Total_Liabilities,
            Fund_Balance,
            Cash_And_Securities,
            Accounts_Receivable,
            Inpatient_Revenue,
            Outpatient_Revenue,
            Total_Revenue,
            Total_Operating_Expenses,

            -- Calculated KPIs (Net_Income now comes from combined CTE)
            Net_Income,

            -- Profitability KPIs
            CASE WHEN Total_Revenue > 0 THEN ((Total_Revenue - Total_Operating_Expenses) / Total_Revenue) * 100 ELSE NULL END as Operating_Margin_Pct,
            CASE WHEN Total_Revenue > 0 THEN (Net_Income / Total_Revenue) * 100 ELSE NULL END as Net_Margin_Pct,
            CASE WHEN Total_Revenue > 0 THEN (Net_Income / Total_Revenue) * 100 ELSE NULL END as Total_Margin_Pct,

            -- Liquidity KPIs
            CASE WHEN Current_Liabilities > 0 THEN Current_Assets / Current_Liabilities ELSE NULL END as Current_Ratio,
            CASE WHEN Total_Operating_Expenses > 0 THEN Cash_And_Securities / (Total_Operating_Expenses / 365) ELSE NULL END as Days_Cash_On_Hand,
            (Current_Assets - Current_Liabilities) / 1000000 as Working_Capital,

            -- Efficiency KPIs
            CASE WHEN Total_Revenue > 0 THEN (Outpatient_Revenue / Total_Revenue) * 100 ELSE NULL END as Outpatient_Revenue_Pct,
            CASE WHEN Total_Revenue > 0 THEN (Inpatient_Revenue / Total_Revenue) * 100 ELSE NULL END as Inpatient_Revenue_Pct,
            CASE WHEN Total_Assets > 0 THEN Total_Revenue / Total_Assets ELSE NULL END as Asset_Turnover_Ratio,
            CASE WHEN Fixed_Assets > 0 THEN Total_Revenue / Fixed_Assets ELSE NULL END as Fixed_Asset_Turnover,
            CASE WHEN Total_Revenue > 0 THEN Accounts_Receivable / (Total_Revenue / 365) ELSE NULL END as AR_Days,
            CASE WHEN Total_Revenue > 0 THEN (Total_Operating_Expenses / Total_Revenue) * 100 ELSE NULL END as Operating_Expense_Ratio,

            -- Leverage KPIs
            CASE WHEN Fund_Balance > 0 THEN Total_Liabilities / Fund_Balance ELSE NULL END as Debt_to_Equity_Ratio,
            CASE WHEN Total_Assets > 0 THEN (Fund_Balance / Total_Assets) * 100 ELSE NULL END as Equity_Ratio_Pct,
            CASE WHEN Total_Assets > 0 THEN (Total_Liabilities / Total_Assets) * 100 ELSE NULL END as Debt_Ratio_Pct,

            -- Return KPIs
            CASE WHEN Total_Assets > 0 THEN (Net_Income / Total_Assets) * 100 ELSE NULL END as Return_on_Assets_Pct,
            CASE WHEN Fund_Balance > 0 THEN (Net_Income / Fund_Balance) * 100 ELSE NULL END as Return_on_Equity_Pct

        FROM combined
        WHERE Provider_Number IS NOT NULL AND Fiscal_Year IS NOT NULL
        ORDER BY Provider_Number, Fiscal_Year
    """)

    # Add revenue growth (requires LAG function)
    logger.info("Computing revenue growth rates...")
    con.execute("""
        CREATE OR REPLACE TABLE hospital_kpis AS
        SELECT
            *,
            CASE
                WHEN LAG(Total_Revenue) OVER (PARTITION BY Provider_Number ORDER BY Fiscal_Year) > 0
                THEN ((Total_Revenue - LAG(Total_Revenue) OVER (PARTITION BY Provider_Number ORDER BY Fiscal_Year))
                      / LAG(Total_Revenue) OVER (PARTITION BY Provider_Number ORDER BY Fiscal_Year)) * 100
                ELSE NULL
            END as Revenue_Growth_Pct
        FROM hospital_kpis
    """)

    # Create indexes
    logger.info("Creating indexes on hospital_kpis...")
    con.execute("CREATE INDEX idx_kpis_provider ON hospital_kpis(Provider_Number)")
    con.execute("CREATE INDEX idx_kpis_year ON hospital_kpis(Fiscal_Year)")
    con.execute("CREATE INDEX idx_kpis_provider_year ON hospital_kpis(Provider_Number, Fiscal_Year)")

    # Get statistics
    stats = con.execute("""
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT Provider_Number) as hospitals,
            MIN(Fiscal_Year) as min_year,
            MAX(Fiscal_Year) as max_year
        FROM hospital_kpis
    """).fetchone()

    logger.info(f"Hospital KPIs table created:")
    logger.info(f"  Records: {stats[0]:,}")
    logger.info(f"  Hospitals: {stats[1]:,}")
    logger.info(f"  Years: {stats[3] - stats[2] + 1} ({stats[2]}-{stats[3]})")


def build_benchmark_tables(con):
    """Build pre-computed benchmark tables"""
    logger.info("=" * 80)
    logger.info("STEP 3: Building hospital_benchmarks table")
    logger.info("=" * 80)

    # First, get state codes and hospital types for all providers
    logger.info("Computing hospital classifications...")

    # Get state codes from balance sheet
    state_codes = con.execute("""
        SELECT DISTINCT Provider_Number, State_Code
        FROM balance_sheet
    """).df()

    # Add hospital type classification
    logger.info("Classifying hospital types...")
    state_codes['Hospital_Type'] = state_codes['Provider_Number'].apply(
        lambda x: classify_hospital_type(str(int(x)).zfill(6))
    )

    # Create hospital metadata table
    con.execute("DROP TABLE IF EXISTS hospital_metadata")
    con.register('hospital_metadata_temp', state_codes)
    con.execute("""
        CREATE TABLE hospital_metadata AS
        SELECT * FROM hospital_metadata_temp
    """)
    con.execute("CREATE INDEX idx_meta_provider ON hospital_metadata(Provider_Number)")

    logger.info(f"Hospital metadata: {len(state_codes):,} hospitals classified")

    # Build benchmark table with all levels
    logger.info("Computing benchmarks for all levels and years...")
    logger.info("This will take several minutes...")

    # KPI columns to benchmark
    kpi_columns = [
        'Operating_Margin_Pct', 'Current_Ratio', 'Days_Cash_On_Hand',
        'Outpatient_Revenue_Pct', 'Asset_Turnover_Ratio', 'AR_Days',
        'Debt_to_Equity_Ratio', 'Equity_Ratio_Pct', 'Net_Margin_Pct',
        'Revenue_Growth_Pct', 'Inpatient_Revenue_Pct', 'Operating_Expense_Ratio',
        'Working_Capital', 'Debt_Ratio_Pct', 'Total_Margin_Pct',
        'Return_on_Assets_Pct', 'Return_on_Equity_Pct'
    ]

    # Build benchmarks for each level
    benchmark_dfs = []

    # NATIONAL BENCHMARKS
    logger.info("  Computing national benchmarks...")
    years = con.execute("SELECT DISTINCT Fiscal_Year FROM hospital_kpis ORDER BY Fiscal_Year").df()['Fiscal_Year'].tolist()

    for year in years:
        for kpi in kpi_columns:
            stats = con.execute("""
                SELECT
                    ? as KPI_Name,
                    'National' as Benchmark_Level,
                    NULL as State_Code,
                    NULL as Hospital_Type,
                    ? as Fiscal_Year,
                    COUNT(*) as Provider_Count,
                    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY value_col) as P25,
                    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY value_col) as Median,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY value_col) as P75,
                    AVG(value_col) as Mean
                FROM (
                    SELECT """ + kpi + """ as value_col
                    FROM hospital_kpis
                    WHERE Fiscal_Year = ? AND """ + kpi + """ IS NOT NULL
                )
            """, [kpi, year, year]).df()
            benchmark_dfs.append(stats)

    # STATE BENCHMARKS
    logger.info("  Computing state benchmarks...")
    states = con.execute("SELECT DISTINCT State_Code FROM hospital_metadata WHERE State_Code IS NOT NULL").df()['State_Code'].tolist()

    for state in states:
        for year in years:
            for kpi in kpi_columns:
                stats = con.execute("""
                    SELECT
                        ? as KPI_Name,
                        'State' as Benchmark_Level,
                        ? as State_Code,
                        NULL as Hospital_Type,
                        ? as Fiscal_Year,
                        COUNT(*) as Provider_Count,
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY value_col) as P25,
                        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY value_col) as Median,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY value_col) as P75,
                        AVG(value_col) as Mean
                    FROM (
                        SELECT k.""" + kpi + """ as value_col
                        FROM hospital_kpis k
                        JOIN hospital_metadata m ON k.Provider_Number = m.Provider_Number
                        WHERE k.Fiscal_Year = ? AND m.State_Code = ? AND k.""" + kpi + """ IS NOT NULL
                    )
                """, [kpi, state, year, year, state]).df()
                if len(stats) > 0 and stats['Provider_Count'].iloc[0] > 0:
                    benchmark_dfs.append(stats)

    # HOSPITAL TYPE BENCHMARKS
    logger.info("  Computing hospital type benchmarks...")
    hosp_types = con.execute("SELECT DISTINCT Hospital_Type FROM hospital_metadata WHERE Hospital_Type IS NOT NULL").df()['Hospital_Type'].tolist()

    for hosp_type in hosp_types:
        for year in years:
            for kpi in kpi_columns:
                stats = con.execute("""
                    SELECT
                        ? as KPI_Name,
                        'Hospital_Type' as Benchmark_Level,
                        NULL as State_Code,
                        ? as Hospital_Type,
                        ? as Fiscal_Year,
                        COUNT(*) as Provider_Count,
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY value_col) as P25,
                        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY value_col) as Median,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY value_col) as P75,
                        AVG(value_col) as Mean
                    FROM (
                        SELECT k.""" + kpi + """ as value_col
                        FROM hospital_kpis k
                        JOIN hospital_metadata m ON k.Provider_Number = m.Provider_Number
                        WHERE k.Fiscal_Year = ? AND m.Hospital_Type = ? AND k.""" + kpi + """ IS NOT NULL
                    )
                """, [kpi, hosp_type, year, year, hosp_type]).df()
                if len(stats) > 0 and stats['Provider_Count'].iloc[0] > 0:
                    benchmark_dfs.append(stats)

    # STATE + HOSPITAL TYPE BENCHMARKS
    logger.info("  Computing state + hospital type benchmarks...")
    for state in states:
        for hosp_type in hosp_types:
            for year in years:
                for kpi in kpi_columns:
                    stats = con.execute("""
                        SELECT
                            ? as KPI_Name,
                            'State_Hospital_Type' as Benchmark_Level,
                            ? as State_Code,
                            ? as Hospital_Type,
                            ? as Fiscal_Year,
                            COUNT(*) as Provider_Count,
                            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY value_col) as P25,
                            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY value_col) as Median,
                            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY value_col) as P75,
                            AVG(value_col) as Mean
                        FROM (
                            SELECT k.""" + kpi + """ as value_col
                            FROM hospital_kpis k
                            JOIN hospital_metadata m ON k.Provider_Number = m.Provider_Number
                            WHERE k.Fiscal_Year = ?
                                AND m.State_Code = ?
                                AND m.Hospital_Type = ?
                                AND k.""" + kpi + """ IS NOT NULL
                        )
                    """, [kpi, state, hosp_type, year, year, state, hosp_type]).df()
                    if len(stats) > 0 and stats['Provider_Count'].iloc[0] > 0:
                        benchmark_dfs.append(stats)

    # Combine all benchmarks
    logger.info("Combining all benchmark levels...")
    all_benchmarks = pd.concat(benchmark_dfs, ignore_index=True)

    # Create benchmarks table
    con.register('benchmarks_temp', all_benchmarks)
    con.execute("""
        CREATE TABLE hospital_benchmarks AS
        SELECT * FROM benchmarks_temp
    """)

    # Create indexes
    logger.info("Creating indexes on hospital_benchmarks...")
    con.execute("CREATE INDEX idx_bench_level ON hospital_benchmarks(Benchmark_Level)")
    con.execute("CREATE INDEX idx_bench_year ON hospital_benchmarks(Fiscal_Year)")
    con.execute("CREATE INDEX idx_bench_kpi ON hospital_benchmarks(KPI_Name)")
    con.execute("CREATE INDEX idx_bench_state ON hospital_benchmarks(State_Code)")
    con.execute("CREATE INDEX idx_bench_type ON hospital_benchmarks(Hospital_Type)")

    # Get statistics
    stats = con.execute("""
        SELECT
            Benchmark_Level,
            COUNT(*) as benchmark_count,
            COUNT(DISTINCT Fiscal_Year) as years
        FROM hospital_benchmarks
        GROUP BY Benchmark_Level
        ORDER BY Benchmark_Level
    """).df()

    logger.info("Benchmark statistics:")
    for _, row in stats.iterrows():
        logger.info(f"  {row['Benchmark_Level']}: {row['benchmark_count']:,} benchmarks across {row['years']} years")


def analyze_database(con):
    """Run ANALYZE on all tables for query optimization"""
    logger.info("=" * 80)
    logger.info("STEP 4: Analyzing tables for query optimization")
    logger.info("=" * 80)

    tables = ['balance_sheet', 'fund_balance_changes', 'revenue', 'revenue_expenses', 'costs_a000', 'costs_b100', 'hospital_kpis', 'hospital_benchmarks', 'hospital_metadata']

    for table in tables:
        logger.info(f"Analyzing {table}...")
        con.execute(f"ANALYZE {table}")


def print_database_summary(con, db_path):
    """Print final database summary"""
    logger.info("=" * 80)
    logger.info("DATABASE BUILD COMPLETE")
    logger.info("=" * 80)

    # Get statistics for each table
    tables_info = []
    for table in ['hospital_kpis', 'hospital_benchmarks', 'balance_sheet', 'fund_balance_changes', 'revenue', 'revenue_expenses', 'costs_a000', 'costs_b100']:
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        tables_info.append((table, count))

    logger.info("\nTABLE SUMMARY:")
    for table, count in tables_info:
        logger.info(f"  {table}: {count:,} records")

    # Get hospital stats
    kpi_stats = con.execute("""
        SELECT
            COUNT(DISTINCT Provider_Number) as hospitals,
            MIN(Fiscal_Year) as min_year,
            MAX(Fiscal_Year) as max_year
        FROM hospital_kpis
    """).fetchone()

    logger.info(f"\nHOSPITAL COVERAGE:")
    logger.info(f"  Hospitals: {kpi_stats[0]:,}")
    logger.info(f"  Years: {kpi_stats[2] - kpi_stats[1] + 1} ({kpi_stats[1]}-{kpi_stats[2]})")

    # Get database size
    db_size = Path(db_path).stat().st_size / (1024**3)
    logger.info(f"\nDATABASE FILE:")
    logger.info(f"  Path: {db_path}")
    logger.info(f"  Size: {db_size:.2f} GB")

    logger.info("=" * 80)


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/hospital_analytics.duckdb'

    logger.info(f"Building optimized database: {db_path}")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Delete existing database
    if Path(db_path).exists():
        logger.info(f"Removing existing database: {db_path}")
        Path(db_path).unlink()

    # Connect to database
    con = duckdb.connect(db_path)

    # Configure for performance
    con.execute("SET memory_limit='8GB'")
    con.execute("SET threads TO 4")

    try:
        # Build tables
        build_raw_tables(con)
        build_kpi_table(con)
        build_benchmark_tables(con)
        analyze_database(con)

        # Print summary
        print_database_summary(con, db_path)

        logger.info(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("Database build completed successfully!")

    except Exception as e:
        logger.error(f"Error building database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        con.close()


if __name__ == '__main__':
    main()
