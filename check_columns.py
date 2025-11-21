"""
Quick script to check available columns in kpi_data table
"""

from data.data_manager import HospitalDataManager

# Initialize data manager
data_manager = HospitalDataManager()

# Test with a sample hospital
test_ccn = '310001'
latest_year = 2021

print("=" * 70)
print("Checking kpi_data columns")
print("=" * 70)

# Get KPI data
kpi_data = data_manager.calculate_kpis(test_ccn)

if not kpi_data.empty:
    print(f"\nColumns in kpi_data for CCN {test_ccn}:")
    print("-" * 70)
    for col in sorted(kpi_data.columns):
        sample_val = kpi_data[col].iloc[0] if len(kpi_data) > 0 else None
        print(f"  {col:50s} = {sample_val}")

    print("\n" + "=" * 70)
    print("Looking for Current_Assets and Current_Liabilities:")
    print("=" * 70)

    if 'Current_Assets' in kpi_data.columns:
        print(f"  [OK] Current_Assets found: {kpi_data['Current_Assets'].iloc[0]}")
    else:
        print("  [MISSING] Current_Assets not in columns")

    if 'Current_Liabilities' in kpi_data.columns:
        print(f"  [OK] Current_Liabilities found: {kpi_data['Current_Liabilities'].iloc[0]}")
    else:
        print("  [MISSING] Current_Liabilities not in columns")

    # Try direct query
    print("\n" + "=" * 70)
    print("Trying direct query:")
    print("=" * 70)

    try:
        query = f"""
        SELECT *
        FROM kpi_data
        WHERE Provider_Number = '{test_ccn}'
        AND Fiscal_Year = {latest_year}
        LIMIT 1
        """
        result = data_manager.query(query)
        print(f"Query returned {len(result)} rows")
        if not result.empty:
            print(f"Columns: {list(result.columns)}")
            if 'Current_Assets' in result.columns:
                print(f"Current_Assets: {result['Current_Assets'].iloc[0]}")
            if 'Current_Liabilities' in result.columns:
                print(f"Current_Liabilities: {result['Current_Liabilities'].iloc[0]}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"[ERROR] No data found for CCN {test_ccn}")
