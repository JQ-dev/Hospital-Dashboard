"""
Deep dive into state benchmark data in the database
"""

import duckdb

DB_PATH = 'data/hospital_analytics.duckdb'

print("=" * 80)
print("DEEP DIVE: State Benchmark Database Investigation")
print("=" * 80)
print()

con = duckdb.connect(DB_PATH, read_only=True)

# 1. Check what benchmark levels exist
print("1. All Benchmark Levels in Database:")
print("-" * 80)
levels = con.execute("""
    SELECT DISTINCT Benchmark_Level, COUNT(*) as record_count
    FROM hospital_benchmarks
    GROUP BY Benchmark_Level
    ORDER BY Benchmark_Level
""").df()
print(levels)
print()

# 2. Check state benchmark structure
print("2. Sample State Benchmark Records:")
print("-" * 80)
state_samples = con.execute("""
    SELECT *
    FROM hospital_benchmarks
    WHERE Benchmark_Level = 'State'
    LIMIT 5
""").df()
print(state_samples)
print()

# 3. Check what state codes exist
print("3. State Codes in State Benchmarks:")
print("-" * 80)
state_codes = con.execute("""
    SELECT DISTINCT State_Code, COUNT(*) as kpi_count
    FROM hospital_benchmarks
    WHERE Benchmark_Level = 'State'
    GROUP BY State_Code
    ORDER BY State_Code
""").df()
print(state_codes)
print()

# 4. Check for state code 31 specifically
print("4. State Code 31 Benchmarks (if any):")
print("-" * 80)
state_31 = con.execute("""
    SELECT *
    FROM hospital_benchmarks
    WHERE Benchmark_Level = 'State' AND State_Code = 31
    LIMIT 5
""").df()
if len(state_31) > 0:
    print(state_31)
else:
    print("NO DATA FOUND for State Code 31")
print()

# 5. Check what fiscal years have state benchmarks
print("5. Fiscal Years with State Benchmarks:")
print("-" * 80)
fiscal_years = con.execute("""
    SELECT DISTINCT Fiscal_Year, COUNT(*) as record_count
    FROM hospital_benchmarks
    WHERE Benchmark_Level = 'State'
    GROUP BY Fiscal_Year
    ORDER BY Fiscal_Year DESC
""").df()
print(fiscal_years)
print()

# 6. Try the exact query from the code
print("6. Testing Exact Query from Code (State 31, Year 2024):")
print("-" * 80)
state_code = 31
fiscal_year = 2024
try:
    result = con.execute("""
        SELECT
            KPI_Name,
            Provider_Count,
            P25, Median, P75, Mean
        FROM hospital_benchmarks
        WHERE Benchmark_Level = 'State' AND State_Code = ? AND Fiscal_Year = ?
    """, [int(state_code), int(fiscal_year)]).df()

    print(f"Query Parameters: State_Code={state_code} (int), Fiscal_Year={fiscal_year} (int)")
    print(f"Results: {len(result)} rows")
    print()
    if len(result) > 0:
        print(result.head())
    else:
        print("QUERY RETURNED EMPTY RESULT!")
        print()
        print("Let's check what combinations DO exist:")
        all_combos = con.execute("""
            SELECT DISTINCT Benchmark_Level, State_Code, Fiscal_Year, COUNT(*) as count
            FROM hospital_benchmarks
            WHERE Benchmark_Level = 'State'
            GROUP BY Benchmark_Level, State_Code, Fiscal_Year
            ORDER BY Fiscal_Year DESC, State_Code
        """).df()
        print(all_combos)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

con.close()

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print("If State benchmarks exist in database but query returns empty,")
print("the issue is likely in the WHERE clause parameters or data types.")
print()
