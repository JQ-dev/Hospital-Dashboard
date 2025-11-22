#!/usr/bin/env python3
"""
Test script to debug KPI callback
"""

from data.data_manager import HospitalDataManager
from config.mappings import DB_COLUMN_TO_KPI_KEY

# Initialize data manager
data_manager = HospitalDataManager()

print("Data Manager Status:")
print(f"  - Using database: {data_manager.use_database}")
print(f"  - Using precomputed KPIs: {data_manager.use_precomputed}")
print(f"  - Using worksheets: {data_manager.use_worksheets}")

# Test KPI data loading
ccn = 310001
kpi_data = data_manager.calculate_kpis(ccn)

print(f"\nKPI Data for CCN {ccn}:")
print(f"  - DataFrame shape: {kpi_data.shape}")
print(f"  - Columns: {list(kpi_data.columns)}")
if not kpi_data.empty:
    print(f"  - Fiscal years: {sorted(kpi_data['Fiscal_Year'].unique())}")
    print(f"  - Sample data (first row): {kpi_data.iloc[0].to_dict() if len(kpi_data) > 0 else 'No rows'}")

# Test the mapping logic from callback
LEVEL_1_KPIS = {
    'Net_Income_Margin',
    'AR_Days',
    'Operating_Expense_per_Adjusted_Discharge',
    'Medicare_CCR',
    'Bad_Debt_Charity_Pct',
    'Current_Ratio'
}

# Create a reverse mapping to find database columns for each KPI key
kpi_key_to_db_col = {}
for db_col in kpi_data.columns:
    if db_col not in ['Provider_Number', 'Fiscal_Year']:
        kpi_key = DB_COLUMN_TO_KPI_KEY.get(db_col, db_col)
        kpi_key_to_db_col[kpi_key] = db_col

print(f"\nKPI Key to DB Column Mapping:")
for k, v in kpi_key_to_db_col.items():
    print(f"  {k} -> {v}")

print(f"\nTesting KPI value extraction:")
for kpi_key in LEVEL_1_KPIS:
    db_col = kpi_key_to_db_col.get(kpi_key)
    if db_col and db_col in kpi_data.columns:
        kpi_values = kpi_data[db_col].values
        kpi_value = kpi_values[0] if len(kpi_values) > 0 else None
        print(f"  {kpi_key}: Found column '{db_col}', value = {kpi_value}")
    else:
        print(f"  {kpi_key}: No column found (looked for '{kpi_key}' -> '{db_col}'), value = None")