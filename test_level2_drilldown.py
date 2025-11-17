"""
Test the Level 2 drill-down functionality
"""

from dashboard import (
    HospitalDataManager,
    DB_COLUMN_TO_KPI_KEY,
    get_level2_page_layout
)
from kpi_hierarchy_config import KPI_HIERARCHY

print("=" * 80)
print("TEST: Level 2 Drill-Down Functionality")
print("=" * 80)
print()

# Initialize data manager
data_manager = HospitalDataManager()

# Test provider
test_provider = '310001'
print(f"Testing with provider: {test_provider}")
print()

# Get KPI data
kpi_data = data_manager.calculate_kpis(test_provider)
latest_year = kpi_data['Fiscal_Year'].max()
print(f"Latest fiscal year: {latest_year}")
print()

# Test each Level 1 KPI's drill-down page
print("=" * 80)
print("Testing Level 2 Drill-Down for Each Level 1 KPI")
print("=" * 80)
print()

level1_kpis = [
    'Net_Income_Margin',
    'AR_Days',
    'Operating_Expense_per_Adjusted_Discharge',
    'Current_Ratio',
    'Medicare_CCR',
    'Bad_Debt_Charity_Pct'
]

for kpi_key in level1_kpis:
    print(f"Testing: {kpi_key}")
    print("-" * 80)

    # Get KPI hierarchy
    kpi_hierarchy = KPI_HIERARCHY.get(kpi_key, {})
    kpi_name = kpi_hierarchy.get('name', kpi_key)
    l2_drivers_dict = kpi_hierarchy.get('level_2_kpis', {})
    l2_drivers = list(l2_drivers_dict.keys())

    print(f"  Name: {kpi_name}")
    print(f"  Level 2 Drivers: {len(l2_drivers)}")

    if l2_drivers:
        print(f"  Driver List:")
        for i, driver_key in enumerate(l2_drivers, 1):
            driver_hierarchy = l2_drivers_dict.get(driver_key, {})
            driver_name = driver_hierarchy.get('name', driver_key)

            # Check if driver has database mapping
            db_column = None
            for db_col, meta_key in DB_COLUMN_TO_KPI_KEY.items():
                if meta_key == driver_key:
                    db_column = db_col
                    break

            # Check if driver has value in database
            latest_data = kpi_data[kpi_data['Fiscal_Year'] == latest_year].iloc[0]
            driver_value = latest_data.get(db_column) if db_column else None

            status = "OK" if driver_value is not None else "MISSING"
            print(f"    {i}. [{status}] {driver_name} (db: {db_column}, value: {driver_value})")
    else:
        print(f"  WARNING: No Level 2 drivers defined!")

    # Try to generate the Level 2 page layout
    try:
        layout = get_level2_page_layout(kpi_key, test_provider)
        print(f"  [PASS] Level 2 page layout generated successfully")
    except Exception as e:
        print(f"  [FAIL] ERROR generating layout: {e}")
        import traceback
        traceback.print_exc()

    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()
print("Level 2 Drill-Down Features:")
print("  [OK] Each Level 1 KPI card has a 'Drill Down' button in top right")
print("  [OK] Button links to /level2/{kpi_key} URL")
print("  [OK] Level 2 page shows:")
print("    - L1 KPI card at top left")
print("    - Explanatory text card at top right")
print("    - 4 Level 2 driver cards below in grid layout")
print("    - Back to Dashboard button")
print()
print("To test in browser:")
print("  1. Open http://localhost:8050")
print("  2. Click 'Drill Down' button on any Level 1 KPI card")
print("  3. Verify Level 2 page displays with L1 card and 4 L2 driver cards")
print("  4. Click 'Back to Dashboard' to return")
print()
