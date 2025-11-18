"""
Debug why state benchmarks show 0 peers - check KPI name mismatches
"""

import duckdb
from dashboard import DB_COLUMN_TO_KPI_KEY

DB_PATH = 'data/hospital_analytics.duckdb'

print("=" * 80)
print("DEBUG: State Benchmark KPI Name Mismatch")
print("=" * 80)
print()

con = duckdb.connect(DB_PATH, read_only=True)

# 1. Get KPI names from state benchmarks
print("1. KPI Names in State Benchmarks (Fiscal Year 2024):")
print("-" * 80)
state_kpis = con.execute("""
    SELECT DISTINCT KPI_Name
    FROM hospital_benchmarks
    WHERE Benchmark_Level = 'State' AND Fiscal_Year = 2024
    ORDER BY KPI_Name
""").df()
print(f"Found {len(state_kpis)} KPIs in state benchmarks:")
for kpi in state_kpis['KPI_Name']:
    print(f"  - {kpi}")
print()

# 2. Get Level 1 KPIs from dashboard mapping
print("2. Level 1 KPI Database Column Names (from DB_COLUMN_TO_KPI_KEY):")
print("-" * 80)
level1_db_columns = [
    'Net_Margin_Pct',
    'AR_Days',
    'Operating_Expense_Ratio',
    'Current_Ratio',
    'Medicare_CCR',
    'Bad_Debt_Charity_Pct'
]
print(f"Expected Level 1 database columns:")
for col in level1_db_columns:
    meta_key = DB_COLUMN_TO_KPI_KEY.get(col, 'NOT FOUND')
    print(f"  - {col} -> {meta_key}")
print()

# 3. Check which Level 1 KPIs are MISSING from state benchmarks
print("3. Matching Check:")
print("-" * 80)
state_kpi_set = set(state_kpis['KPI_Name'].values)
for db_col in level1_db_columns:
    if db_col in state_kpi_set:
        print(f"  [OK] {db_col} - FOUND in state benchmarks")
    else:
        print(f"  [MISSING] {db_col} - NOT in state benchmarks")

        # Check if similar name exists
        similar = [k for k in state_kpi_set if db_col.lower() in k.lower() or k.lower() in db_col.lower()]
        if similar:
            print(f"            Similar names found: {similar}")
print()

# 4. Get sample state benchmark data to see structure
print("4. Sample State Benchmark Record:")
print("-" * 80)
sample = con.execute("""
    SELECT
        Benchmark_Level,
        State_Code,
        Fiscal_Year,
        KPI_Name,
        Provider_Count,
        P25, Median, P75
    FROM hospital_benchmarks
    WHERE Benchmark_Level = 'State' AND Fiscal_Year = 2024
    LIMIT 3
""").df()
print(sample)
print()

# 5. Check if the issue is KPI-specific
print("5. Checking Provider_Count for each State KPI:")
print("-" * 80)
counts = con.execute("""
    SELECT
        KPI_Name,
        Provider_Count
    FROM hospital_benchmarks
    WHERE Benchmark_Level = 'State' AND State_Code = 31 AND Fiscal_Year = 2024
    ORDER BY KPI_Name
""").df()
print(counts)
print()

con.close()

print("=" * 80)
print("DIAGNOSIS")
print("=" * 80)
print()
print("The '0 peers' issue occurs when:")
print("  1. The KPI name in the dashboard (db_column) doesn't match the KPI_Name in hospital_benchmarks")
print("  2. The benchmark data exists but kpi_bench.get('kpis', {}).get(bench_lookup_key, {}) returns empty")
print()
print("Check the 'Matching Check' section above to see which Level 1 KPIs are missing.")
print()
