"""
Debug the state benchmark calculation to see why it's broken
"""

from dashboard import HospitalDataManager

print("=" * 80)
print("DEBUG: State Benchmark Calculation")
print("=" * 80)
print()

# Initialize data manager
m = HospitalDataManager()

# Test with a provider
test_provider = '310001'
state_code = test_provider[:2]
print(f"Testing with provider: {test_provider}")
print(f"State code extracted: {state_code}")
print()

# Get KPI data
kpi_data = m.calculate_kpis(test_provider)
latest_year = kpi_data['Fiscal_Year'].max()
print(f"Latest fiscal year: {latest_year}")
print()

# Test each benchmark level separately
print("=" * 80)
print("Testing Each Benchmark Level")
print("=" * 80)
print()

# 1. National
print("1. NATIONAL Benchmark")
print("-" * 80)
try:
    national_bench = m.get_benchmarks(test_provider, latest_year, 'National')
    print(f"   Group Name: {national_bench['group_name']}")
    print(f"   Peer Count: {national_bench['provider_count']}")
    print(f"   KPIs Available: {len(national_bench.get('kpis', {}))}")
    if national_bench.get('kpis'):
        sample_kpi = list(national_bench['kpis'].keys())[0]
        print(f"   Sample KPI: {sample_kpi} = {national_bench['kpis'][sample_kpi]}")
except Exception as e:
    print(f"   ERROR: {e}")
print()

# 2. State
print("2. STATE Benchmark")
print("-" * 80)
try:
    state_bench = m.get_benchmarks(test_provider, latest_year, 'State')
    print(f"   Group Name: {state_bench['group_name']}")
    print(f"   Peer Count: {state_bench['provider_count']}")
    print(f"   KPIs Available: {len(state_bench.get('kpis', {}))}")
    if state_bench.get('kpis'):
        sample_kpi = list(state_bench['kpis'].keys())[0]
        print(f"   Sample KPI: {sample_kpi} = {state_bench['kpis'][sample_kpi]}")
    else:
        print(f"   WARNING: No KPIs found!")
        print(f"   Checking database for State benchmarks...")

        # Check if benchmarks exist in database
        import duckdb
        con = duckdb.connect('data/hospital_analytics.duckdb', read_only=True)
        result = con.execute("""
            SELECT COUNT(*) as count, Benchmark_Level, State_Code, Hospital_Type
            FROM hospital_benchmarks
            WHERE Fiscal_Year = ? AND Benchmark_Level = 'State'
            GROUP BY Benchmark_Level, State_Code, Hospital_Type
            LIMIT 10
        """, [int(latest_year)]).df()
        print(f"   Database check:")
        print(result)
        con.close()
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()
print()

# 3. Hospital Type
print("3. HOSPITAL TYPE Benchmark")
print("-" * 80)
try:
    type_bench = m.get_benchmarks(test_provider, latest_year, 'Hospital_Type')
    print(f"   Group Name: {type_bench['group_name']}")
    print(f"   Peer Count: {type_bench['provider_count']}")
    print(f"   KPIs Available: {len(type_bench.get('kpis', {}))}")
    if type_bench.get('kpis'):
        sample_kpi = list(type_bench['kpis'].keys())[0]
        print(f"   Sample KPI: {sample_kpi} = {type_bench['kpis'][sample_kpi]}")
except Exception as e:
    print(f"   ERROR: {e}")
print()

# 4. State & Hospital Type
print("4. STATE & HOSPITAL TYPE Benchmark")
print("-" * 80)
try:
    state_type_bench = m.get_benchmarks(test_provider, latest_year, 'State_Hospital_Type')
    print(f"   Group Name: {state_type_bench['group_name']}")
    print(f"   Peer Count: {state_type_bench['provider_count']}")
    print(f"   KPIs Available: {len(state_type_bench.get('kpis', {}))}")
    if state_type_bench.get('kpis'):
        sample_kpi = list(state_type_bench['kpis'].keys())[0]
        print(f"   Sample KPI: {sample_kpi} = {state_type_bench['kpis'][sample_kpi]}")
    else:
        print(f"   WARNING: No KPIs found!")
except Exception as e:
    print(f"   ERROR: {e}")
print()

# Check what's in the benchmark database
print("=" * 80)
print("Database Benchmark Levels Available")
print("=" * 80)
import duckdb
con = duckdb.connect('data/hospital_analytics.duckdb', read_only=True)
levels = con.execute("""
    SELECT DISTINCT Benchmark_Level, COUNT(*) as count
    FROM hospital_benchmarks
    WHERE Fiscal_Year = ?
    GROUP BY Benchmark_Level
""", [int(latest_year)]).df()
print(levels)
con.close()
print()
