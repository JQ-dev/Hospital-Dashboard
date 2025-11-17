"""
Complete test simulating exact dashboard behavior for all 4 benchmark levels
"""

from dashboard import HospitalDataManager, DB_COLUMN_TO_KPI_KEY
from kpi_hierarchy_config import KPI_METADATA

print("=" * 80)
print("COMPLETE TEST: All 4 Benchmark Levels - Exact Dashboard Simulation")
print("=" * 80)
print()

# Initialize data manager
m = HospitalDataManager()

# Test with provider 310001
test_provider = '310001'
print(f"Testing with provider: {test_provider}")
print()

# Get KPI data
kpi_data = m.calculate_kpis(test_provider)
latest_year = kpi_data['Fiscal_Year'].max()
print(f"Latest fiscal year: {latest_year}")
print()

# Calculate ALL 4 benchmark levels (EXACTLY as dashboard does)
print("Calculating all 4 benchmark levels (as dashboard callback does)...")
all_benchmarks = {
    'state_hospital_type': m.get_benchmarks(test_provider, latest_year, 'State_Hospital_Type'),
    'state': m.get_benchmarks(test_provider, latest_year, 'State'),
    'hospital_type': m.get_benchmarks(test_provider, latest_year, 'Hospital_Type'),
    'national': m.get_benchmarks(test_provider, latest_year, 'National')
}
print()

# Display in the order they appear on cards
print("=" * 80)
print("BENCHMARK LEVELS (in card display order):")
print("=" * 80)
print()

benchmark_order = [
    ('state_hospital_type', 'Hospital Type and State'),
    ('state', 'Hospitals in State'),
    ('hospital_type', 'Hospital Type'),
    ('national', 'Hospital Nationwide')
]

for key, label in benchmark_order:
    benchmark = all_benchmarks[key]
    group_name = benchmark.get('group_name', 'N/A')
    peer_count = benchmark.get('provider_count', 0)
    kpis = benchmark.get('kpis', {})

    print(f"{label}:")
    print(f"  Group: {group_name}")
    print(f"  Peers: {peer_count:,}")
    print(f"  KPIs Available: {len(kpis)}")

    if kpis:
        # Show a sample KPI
        sample_kpi_name = list(kpis.keys())[0]
        sample_kpi_data = kpis[sample_kpi_name]
        print(f"  Sample KPI ({sample_kpi_name}):")
        print(f"    P25: {sample_kpi_data.get('P25', 'N/A'):.2f}" if sample_kpi_data.get('P25') else "    P25: N/A")
        print(f"    Median: {sample_kpi_data.get('Median', 'N/A'):.2f}" if sample_kpi_data.get('Median') else "    Median: N/A")
        print(f"    P75: {sample_kpi_data.get('P75', 'N/A'):.2f}" if sample_kpi_data.get('P75') else "    P75: N/A")
        print()
    else:
        print("  [ERROR] No KPI data found!")
        print()

# Now test with actual Level 1 KPIs
print("=" * 80)
print("TESTING WITH ACTUAL LEVEL 1 KPIS")
print("=" * 80)
print()

LEVEL_1_KPIS = {
    'Net_Income_Margin',
    'AR_Days',
    'Operating_Expense_per_Adjusted_Discharge',
    'Medicare_CCR',
    'Bad_Debt_Charity_Pct',
    'Current_Ratio'
}

# Get first Level 1 KPI from database
test_kpi_key = None
test_db_column = None

for db_col in kpi_data.columns:
    if db_col in ['Provider_Number', 'Fiscal_Year']:
        continue

    kpi_key = DB_COLUMN_TO_KPI_KEY.get(db_col, db_col)

    if kpi_key in LEVEL_1_KPIS and kpi_key in KPI_METADATA:
        test_kpi_key = kpi_key
        test_db_column = db_col
        break

if test_kpi_key:
    print(f"Testing with KPI: {KPI_METADATA[test_kpi_key]['name']}")
    print(f"  Metadata Key: {test_kpi_key}")
    print(f"  DB Column: {test_db_column}")
    print()

    # Test benchmark lookup for this KPI across all 4 levels
    print("Benchmark Data for This KPI:")
    print("-" * 80)

    for key, label in benchmark_order:
        benchmark = all_benchmarks[key]
        kpis = benchmark.get('kpis', {})

        # Try to get benchmark using database column name (what actually works)
        kpi_bench = kpis.get(test_db_column, {})

        print(f"{label}:")
        if kpi_bench:
            print(f"  P25: {kpi_bench.get('P25', 'N/A'):.2f}" if kpi_bench.get('P25') else "  P25: N/A")
            print(f"  Median: {kpi_bench.get('Median', 'N/A'):.2f}" if kpi_bench.get('Median') else "  Median: N/A")
            print(f"  P75: {kpi_bench.get('P75', 'N/A'):.2f}" if kpi_bench.get('P75') else "  P75: N/A")
            print(f"  [SUCCESS] Data found!")
        else:
            print(f"  [ERROR] No benchmark data for this KPI!")
            print(f"  Available KPIs in this benchmark: {list(kpis.keys())[:3]}...")
        print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

all_working = all(
    all_benchmarks[key].get('provider_count', 0) > 0
    for key, _ in benchmark_order
)

if all_working:
    print("[SUCCESS] All 4 benchmark levels have data and peer counts!")
    print()
    print("If you're still seeing issues in the dashboard:")
    print("  1. Make sure you've refreshed the browser (Ctrl+F5)")
    print("  2. Check browser console for JavaScript errors")
    print("  3. Verify the dashboard is using the latest code")
else:
    print("[FAIL] Some benchmark levels are missing data")
    for key, label in benchmark_order:
        peer_count = all_benchmarks[key].get('provider_count', 0)
        status = "[OK]" if peer_count > 0 else "[FAIL]"
        print(f"  {status} {label}: {peer_count} peers")

print()
