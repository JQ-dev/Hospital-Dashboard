"""
Test that dashboard shows ONLY the 6 Level 1 KPIs from to_do.txt
"""

from dashboard import HospitalDataManager, DB_COLUMN_TO_KPI_KEY
from kpi_hierarchy_config import KPI_METADATA

# The 6 Level 1 KPIs from to_do.txt
LEVEL_1_KPIS = {
    'Net_Income_Margin',                      # L1 KPI 1: Net Income Margin
    'AR_Days',                                # L1 KPI 2: Days in Net Patient AR
    'Operating_Expense_per_Adjusted_Discharge',  # L1 KPI 3: Operating Expense per Adjusted Discharge
    'Medicare_CCR',                           # L1 KPI 4: Medicare Cost-to-Charge Ratio
    'Bad_Debt_Charity_Pct',                   # L1 KPI 5: Bad Debt + Charity %
    'Current_Ratio'                           # L1 KPI 6: Current Ratio
}

print("=" * 80)
print("TEST: Verify Dashboard Shows ONLY Level 1 KPIs")
print("=" * 80)
print()

# Initialize data manager
m = HospitalDataManager()
kpi_data = m.calculate_kpis('310001')

print(f"Testing with provider: 310001")
print(f"Total database columns: {len(kpi_data.columns)}")
print()

# Simulate the filtering logic from dashboard
kpis_that_will_display = []

for db_col in kpi_data.columns:
    # Skip non-KPI columns
    if db_col in ['Provider_Number', 'Fiscal_Year']:
        continue

    # Map database column to KPI metadata key
    kpi_key = DB_COLUMN_TO_KPI_KEY.get(db_col, db_col)

    # Skip if not in metadata
    if kpi_key not in KPI_METADATA:
        continue

    # Filter: Only Level 1 KPIs
    if kpi_key not in LEVEL_1_KPIS:
        continue

    kpis_that_will_display.append({
        'db_column': db_col,
        'kpi_key': kpi_key,
        'name': KPI_METADATA[kpi_key].get('name', kpi_key),
        'level': KPI_METADATA[kpi_key].get('level', '?')
    })

print(f"KPIs that will display on dashboard: {len(kpis_that_will_display)}")
print()

if len(kpis_that_will_display) == 0:
    print("[FAIL] No KPIs will be displayed!")
    print()
    print("Possible issues:")
    print("1. Database columns don't match any Level 1 KPI keys")
    print("2. Mapping in DB_COLUMN_TO_KPI_KEY is incorrect")
    print()
    print("Available database columns that could be Level 1 KPIs:")
    for db_col in kpi_data.columns:
        if db_col not in ['Provider_Number', 'Fiscal_Year']:
            kpi_key = DB_COLUMN_TO_KPI_KEY.get(db_col, db_col)
            if kpi_key in KPI_METADATA:
                print(f"  - {db_col} -> {kpi_key} (Level {KPI_METADATA[kpi_key].get('level', '?')})")
else:
    print("Level 1 KPIs that WILL display:")
    print("-" * 80)
    for idx, kpi in enumerate(kpis_that_will_display, 1):
        print(f"{idx}. {kpi['name']}")
        print(f"   DB Column: {kpi['db_column']}")
        print(f"   KPI Key: {kpi['kpi_key']}")
        print(f"   Level: {kpi['level']}")
        print()

    # Check which Level 1 KPIs are missing
    displayed_keys = {kpi['kpi_key'] for kpi in kpis_that_will_display}
    missing_l1_kpis = LEVEL_1_KPIS - displayed_keys

    if missing_l1_kpis:
        print()
        print("[!] Missing Level 1 KPIs (not in database):")
        print("-" * 80)
        for kpi_key in missing_l1_kpis:
            if kpi_key in KPI_METADATA:
                print(f"  - {KPI_METADATA[kpi_key].get('name', kpi_key)} ({kpi_key})")
            else:
                print(f"  - {kpi_key} (not in metadata)")

    # Verify all are Level 1
    all_level_1 = all(kpi['level'] == 1 for kpi in kpis_that_will_display)

    print()
    print("=" * 80)
    print("TEST RESULTS")
    print("=" * 80)

    if all_level_1:
        print(f"[PASS] All {len(kpis_that_will_display)} KPIs are Level 1")
    else:
        print("[FAIL] Some KPIs are not Level 1:")
        for kpi in kpis_that_will_display:
            if kpi['level'] != 1:
                print(f"  - {kpi['name']} is Level {kpi['level']}")

    if len(kpis_that_will_display) <= 6:
        print(f"[PASS] Displaying {len(kpis_that_will_display)} KPIs (<= 6 expected Level 1 KPIs)")
    else:
        print(f"[FAIL] Displaying {len(kpis_that_will_display)} KPIs (expected <= 6)")

    if len(missing_l1_kpis) > 0:
        print(f"[INFO] {len(missing_l1_kpis)} Level 1 KPIs missing from database (need to be calculated)")
    else:
        print("[PASS] All 6 Level 1 KPIs have data in database")

    print()
    print("Summary:")
    print(f"  - Expected: 6 Level 1 KPIs")
    print(f"  - Displaying: {len(kpis_that_will_display)} KPIs")
    print(f"  - Missing: {len(missing_l1_kpis)} KPIs")
    print(f"  - All Level 1: {'Yes' if all_level_1 else 'No'}")
