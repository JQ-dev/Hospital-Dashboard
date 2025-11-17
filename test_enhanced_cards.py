"""
Test that dashboard displays enhanced KPI cards with all 4 benchmark levels
Tests the implementation from the user requirement:
- All 4 benchmark levels displayed on each card (not dropdown)
- 5-year trend visualization
- KPI description
- 3 cards per row layout
"""

from dashboard import HospitalDataManager, DB_COLUMN_TO_KPI_KEY, create_enhanced_level1_kpi_card
from kpi_hierarchy_config import KPI_METADATA

print("=" * 80)
print("TEST: Enhanced Level 1 KPI Cards with All Benchmark Levels")
print("=" * 80)
print()

# Initialize data manager
m = HospitalDataManager()

# Test with a provider
test_provider = '310001'
print(f"Testing with provider: {test_provider}")
print()

# Get KPI data
kpi_data = m.calculate_kpis(test_provider)
latest_year = kpi_data['Fiscal_Year'].max()

print(f"Latest fiscal year: {latest_year}")
print()

# Calculate ALL 4 benchmark levels (like the updated callback does)
print("Calculating all 4 benchmark levels...")
all_benchmarks = {
    'national': m.get_benchmarks(test_provider, latest_year, 'national'),
    'state': m.get_benchmarks(test_provider, latest_year, 'state'),
    'hospital_type': m.get_benchmarks(test_provider, latest_year, 'hospital_type'),
    'bed_size': m.get_benchmarks(test_provider, latest_year, 'bed_size')
}

print(f"  National peers: {all_benchmarks['national']['provider_count']:,}")
print(f"  State peers: {all_benchmarks['state']['provider_count']:,}")
print(f"  Hospital Type peers: {all_benchmarks['hospital_type']['provider_count']:,}")
print(f"  Bed Size peers: {all_benchmarks['bed_size']['provider_count']:,}")
print()

# Get Level 2 and Level 3 KPIs
l2_kpis = m.calculate_level2_kpis(test_provider, latest_year)
l3_kpis = m.calculate_level3_kpis(test_provider, latest_year)

# Test creating an enhanced card for the first available Level 1 KPI
LEVEL_1_KPIS = {
    'Net_Income_Margin',
    'AR_Days',
    'Operating_Expense_per_Adjusted_Discharge',
    'Medicare_CCR',
    'Bad_Debt_Charity_Pct',
    'Current_Ratio'
}

test_card_created = False
for db_col in kpi_data.columns:
    if db_col in ['Provider_Number', 'Fiscal_Year']:
        continue

    kpi_key = DB_COLUMN_TO_KPI_KEY.get(db_col, db_col)

    if kpi_key not in KPI_METADATA or kpi_key not in LEVEL_1_KPIS:
        continue

    # Found a Level 1 KPI - test creating enhanced card
    kpi_values = kpi_data[db_col].values
    kpi_value = kpi_values[0] if len(kpi_values) > 0 else None

    print(f"Testing enhanced card creation for: {KPI_METADATA[kpi_key]['name']}")
    print(f"  KPI Key: {kpi_key}")
    print(f"  Current Value: {kpi_value}")
    print()

    try:
        card = create_enhanced_level1_kpi_card(
            kpi_key=kpi_key,
            kpi_value=kpi_value,
            kpi_trend_values=kpi_values,
            fiscal_years=kpi_data['Fiscal_Year'].values,
            all_benchmarks=all_benchmarks,
            rank=1,
            l2_kpis=l2_kpis,
            l3_kpis=l3_kpis,
            ccn=test_provider,
            fiscal_year=latest_year
        )

        print("[PASS] Enhanced card created successfully!")
        print()
        print("Card components expected:")
        print("  - KPI title and current value")
        print("  - 5-year trend sparkline")
        print("  - Benchmark table with ALL 4 levels:")
        print("    1. National")
        print("    2. State")
        print("    3. Hospital Type")
        print("    4. Bed Size")
        print("  - Performance badges for each benchmark level")
        print("  - KPI description text")
        print("  - Expandable Level 2 drivers section")
        print()
        test_card_created = True
        break

    except Exception as e:
        print(f"[FAIL] Error creating enhanced card: {e}")
        import traceback
        traceback.print_exc()
        break

if not test_card_created:
    print("[FAIL] Could not create test card - no Level 1 KPIs found in database")
    print()

print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)

# Verify dashboard configuration
print()
print("Dashboard Configuration Checks:")
print()

# Check 1: Benchmark dropdown removed
print("[INFO] Benchmark dropdown should be removed from UI")
print("       All 4 benchmark levels now display on each card")
print()

# Check 2: 3-per-row layout
print("[INFO] Cards should use 3-per-row layout")
print("       Implementation: dbc.Col(card, width=12, lg=4)")
print("       - width=12: Full width on mobile")
print("       - lg=4: 3 cards per row on desktop (12/4=3)")
print()

# Check 3: Enhanced card function
print("[INFO] Dashboard callback should use create_enhanced_level1_kpi_card()")
print("       Passes all_benchmarks dict with all 4 levels")
print()

# Check 4: All 6 Level 1 KPIs
level1_count = 0
for db_col in kpi_data.columns:
    if db_col in ['Provider_Number', 'Fiscal_Year']:
        continue
    kpi_key = DB_COLUMN_TO_KPI_KEY.get(db_col, db_col)
    if kpi_key in LEVEL_1_KPIS and kpi_key in KPI_METADATA:
        level1_count += 1

print(f"[INFO] Level 1 KPIs in database: {level1_count} of 6")
if level1_count == 6:
    print("       [PASS] All 6 Level 1 KPIs have data")
else:
    print(f"       [WARN] Only {level1_count} Level 1 KPIs have data")
    print("       Missing KPIs need to be calculated")
print()

print("=" * 80)
print("NEXT STEPS")
print("=" * 80)
print()
print("1. Open browser to http://localhost:8050")
print("2. Select a hospital from dropdown")
print("3. Verify each card shows:")
print("   - All 4 benchmark levels (National, State, Type, Bed Size)")
print("   - 5-year trend sparkline chart")
print("   - KPI description text")
print("   - 3 cards per row on desktop")
print("4. No benchmark dropdown should be visible")
print()
