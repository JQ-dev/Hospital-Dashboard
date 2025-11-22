"""Verify state code fix"""
import duckdb

con = duckdb.connect('data/hospital_analytics.duckdb', read_only=True)

print('State codes in hospital_benchmarks:')
result = con.execute("""
    SELECT State_Code, COUNT(DISTINCT Fiscal_Year) as years
    FROM hospital_benchmarks
    WHERE Benchmark_Level = 'State'
    GROUP BY State_Code
    ORDER BY State_Code
""").df()
print(result)

print('\nSample benchmarks for state 1:')
result2 = con.execute("""
    SELECT KPI_Name, Fiscal_Year, Provider_Count, P25, Median, P75
    FROM hospital_benchmarks
    WHERE Benchmark_Level = 'State' AND State_Code = 1
    LIMIT 5
""").df()
print(result2)

con.close()
