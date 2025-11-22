"""Test peer count logic"""
import duckdb

con = duckdb.connect('data/hospital_analytics.duckdb', read_only=True)

print('Provider counts by benchmark level for Current_Ratio (2021):')
print('=' * 80)

result = con.execute("""
    SELECT
        Benchmark_Level,
        State_Code,
        Hospital_Type,
        Provider_Count
    FROM hospital_benchmarks
    WHERE Fiscal_Year = 2021
      AND KPI_Name = 'Current_Ratio'
    ORDER BY Benchmark_Level, State_Code, Hospital_Type
""").df()

print(result)

print('\n\nExpected hierarchy:')
print('=' * 80)
print('National >= Hospital_Type >= State >= State_Hospital_Type')
print('\nNational should have ALL hospitals')
print('Hospital_Type should have subset (one type)')
print('State should have subset (one state)')
print('State_Hospital_Type should have smallest subset (one state AND one type)')

# Check actual counts
print('\n\nActual counts from database:')
print('=' * 80)
for level in ['National', 'Hospital_Type', 'State', 'State_Hospital_Type']:
    counts = result[result['Benchmark_Level'] == level]['Provider_Count'].tolist()
    if counts:
        print(f'{level:25s}: min={min(counts):3d}, max={max(counts):3d}, avg={sum(counts)/len(counts):.1f}')

con.close()
