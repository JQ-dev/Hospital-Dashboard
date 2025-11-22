"""Test state code matching issue"""
import duckdb

# Test CCN from state 01
ccn = '014000'
state_code = str(ccn)[:2]

print(f'CCN: {ccn}')
print(f'State code (string): {state_code}')
print(f'State code (int): {int(state_code)}')
print('\nTest queries:')

con = duckdb.connect('data/hospital_analytics.duckdb', read_only=True)

# Check if benchmarks exist for state code 1
result = con.execute("""
    SELECT COUNT(*) as cnt
    FROM hospital_benchmarks
    WHERE State_Code = ?
      AND Benchmark_Level = 'State'
""", [int(state_code)]).fetchone()
print(f'\nBenchmarks found for State_Code = {int(state_code)}: {result[0]}')

# Check all distinct state codes in benchmarks
result2 = con.execute("""
    SELECT DISTINCT State_Code, COUNT(*) as cnt
    FROM hospital_benchmarks
    WHERE Benchmark_Level = 'State'
    GROUP BY State_Code
    ORDER BY State_Code
    LIMIT 10
""").df()
print(f'\nAll state codes in benchmarks (first 10):')
print(result2)

# Check if there are any hospitals from state code 1
result3 = con.execute("""
    SELECT COUNT(DISTINCT Provider_Number) as cnt
    FROM hospital_kpis
    WHERE Provider_Number >= 10000 AND Provider_Number < 20000
""").fetchone()
print(f'\nHospitals with Provider_Number starting with 01 (10000-19999): {result3[0]}')

# Check what state codes are actually in hospital_kpis
result4 = con.execute("""
    SELECT
        CAST(Provider_Number / 10000 AS INTEGER) as State_Code,
        COUNT(DISTINCT Provider_Number) as Hospital_Count
    FROM hospital_kpis
    GROUP BY CAST(Provider_Number / 10000 AS INTEGER)
    ORDER BY State_Code
    LIMIT 10
""").df()
print(f'\nState codes in hospital_kpis (extracted from Provider_Number):')
print(result4)

con.close()
