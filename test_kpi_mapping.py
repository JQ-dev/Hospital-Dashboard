"""Test KPI mapping between database columns and metadata"""
from dashboard import HospitalDataManager, DB_COLUMN_TO_KPI_KEY
from kpi_hierarchy_config import KPI_METADATA

m = HospitalDataManager()
kpi_data = m.calculate_kpis('310001')

mapped_kpis = []
for col in kpi_data.columns:
    if col in ['Provider_Number', 'Fiscal_Year']:
        continue
    kpi_key = DB_COLUMN_TO_KPI_KEY.get(col, col)
    if kpi_key in KPI_METADATA:
        mapped_kpis.append((col, kpi_key, KPI_METADATA[kpi_key].get('name', '')))

print(f"\n{len(mapped_kpis)} KPIs will be displayed\n")
print("Mapped KPIs:")
print("-" * 100)
for db_col, meta_key, name in mapped_kpis:
    print(f"  DB: {db_col:30} -> META: {meta_key:35} | {name}")
