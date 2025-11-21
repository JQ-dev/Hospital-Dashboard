"""
Quick script to check which KPIs are available in the database
"""

from data.data_manager import HospitalDataManager
from config.mappings import DB_COLUMN_TO_KPI_KEY
from kpi_hierarchy_config import KPI_METADATA

# Initialize data manager
data_manager = HospitalDataManager()

# Test with a sample hospital (first one)
test_ccn = '310001'

print("="*70)
print("KPI Data Availability Check")
print("="*70)

# Get KPI data
kpi_data = data_manager.calculate_kpis(test_ccn)

if kpi_data.empty:
    print(f"\n[ERROR] No KPI data found for CCN {test_ccn}")
else:
    print(f"\n[OK] KPI data found for CCN {test_ccn}")
    print(f"Fiscal years: {list(kpi_data['Fiscal_Year'].unique())}")

    # List all columns except metadata columns
    kpi_columns = [col for col in kpi_data.columns if col not in ['Provider_Number', 'Fiscal_Year']]

    print(f"\n=== Available KPI Columns ({len(kpi_columns)}) ===")
    for col in sorted(kpi_columns):
        # Check if it has a mapping
        kpi_key = DB_COLUMN_TO_KPI_KEY.get(col, col)
        in_metadata = kpi_key in KPI_METADATA

        # Get sample value
        sample_val = kpi_data[col].iloc[0] if len(kpi_data) > 0 else None

        status = "[OK]" if in_metadata else "[MISSING METADATA]"
        print(f"  {status} {col:40s} -> {kpi_key:40s} | Value: {sample_val}")

# Define the 6 target Level 1 KPIs
LEVEL_1_KPIS = {
    'Net_Income_Margin',
    'AR_Days',
    'Operating_Expense_per_Adjusted_Discharge',
    'Medicare_CCR',
    'Bad_Debt_Charity_Pct',
    'Current_Ratio'
}

print(f"\n=== Level 1 KPIs Status ===")
for kpi_key in sorted(LEVEL_1_KPIS):
    # Find if any database column maps to this KPI
    db_col = None
    for col, mapped_key in DB_COLUMN_TO_KPI_KEY.items():
        if mapped_key == kpi_key:
            db_col = col
            break

    # Check if column exists in data
    if db_col and db_col in kpi_columns:
        status = "[OK] AVAILABLE"
        value = kpi_data[db_col].iloc[0] if len(kpi_data) > 0 else None
        print(f"  {status:20s} {kpi_key:45s} <- {db_col:30s} = {value}")
    elif db_col:
        status = "[MISSING] NO DATA"
        print(f"  {status:20s} {kpi_key:45s} <- {db_col:30s} (column not in data)")
    else:
        status = "[MISSING] NO MAPPING"
        print(f"  {status:20s} {kpi_key:45s} (no database column mapped)")

print("\n" + "="*70)
print("Summary")
print("="*70)

available_count = 0
for kpi_key in LEVEL_1_KPIS:
    db_col = None
    for col, mapped_key in DB_COLUMN_TO_KPI_KEY.items():
        if mapped_key == kpi_key:
            db_col = col
            break
    if db_col and db_col in kpi_columns:
        available_count += 1

print(f"Level 1 KPIs available: {available_count}/6")
print(f"Total KPI columns in data: {len(kpi_columns)}")

if available_count < 6:
    print(f"\n[ACTION NEEDED] {6 - available_count} KPI(s) missing!")
    print("Check the analysis above to see which KPIs need to be added.")
else:
    print("\n[OK] All 6 Level 1 KPIs are available!")
