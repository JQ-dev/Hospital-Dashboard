"""
Quick test to verify dashboard data loading works
"""

import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent / "hospital_analytics.duckdb"

print(f"Testing database connection to: {DB_PATH}")
print(f"Database exists: {DB_PATH.exists()}")
print()

# Test connection
conn = duckdb.connect(str(DB_PATH), read_only=True)

# Test 1: List tables
print("=" * 60)
print("TEST 1: List Tables")
print("=" * 60)
tables = conn.execute("SHOW TABLES").fetchall()
print(f"Tables found: {tables}")
print()

# Test 2: Count records
print("=" * 60)
print("TEST 2: Record Counts")
print("=" * 60)
income_count = conn.execute("SELECT COUNT(*) FROM income_statement_long").fetchone()[0]
expense_count = conn.execute("SELECT COUNT(*) FROM expense_detail").fetchone()[0]
print(f"Income statement records: {income_count:,}")
print(f"Expense detail records: {expense_count:,}")
print()

# Test 3: Load hospital list (dashboard query)
print("=" * 60)
print("TEST 3: Hospital List Query (Dashboard)")
print("=" * 60)
query = """
SELECT DISTINCT
    Provider_Number,
    MAX(Fiscal_Year) as latest_year
FROM income_statement_long
GROUP BY Provider_Number
ORDER BY Provider_Number
LIMIT 10
"""
df = conn.execute(query).df()
print(f"Hospitals found: {len(df)}")
print(df)
print()

# Test 4: Load years for first hospital
print("=" * 60)
print("TEST 4: Year Dropdown Query")
print("=" * 60)
if not df.empty:
    first_provider = df.iloc[0]['Provider_Number']
    print(f"Testing with Provider: {first_provider}")
    query = f"""
    SELECT DISTINCT Fiscal_Year
    FROM income_statement_long
    WHERE Provider_Number = '{first_provider}'
    ORDER BY Fiscal_Year DESC
    """
    years_df = conn.execute(query).df()
    print(f"Years found: {years_df['Fiscal_Year'].tolist()}")
    print()

    # Test 5: Load income statement for first provider
    print("=" * 60)
    print("TEST 5: Income Statement Query")
    print("=" * 60)
    fiscal_year = years_df.iloc[0]['Fiscal_Year']
    print(f"Testing with Provider: {first_provider}, Year: {fiscal_year}")
    query = f"""
    SELECT
        Line_Name,
        Section,
        Subsection,
        Value
    FROM income_statement_long
    WHERE Provider_Number = '{first_provider}'
        AND Fiscal_Year = {fiscal_year}
    ORDER BY Line
    """
    income_df = conn.execute(query).df()
    print(f"Income statement lines: {len(income_df)}")
    print("\nKey metrics:")
    for _, row in income_df.iterrows():
        if row['Line_Name'] in ['Net_Patient_Revenue', 'Operating_Income', 'Net_Income']:
            print(f"  {row['Line_Name']}: ${row['Value']:,.0f}")
    print()

    # Test 6: Load expense detail
    print("=" * 60)
    print("TEST 6: Expense Detail Query")
    print("=" * 60)
    query = f"""
    SELECT
        Expense_Category,
        Category_Description,
        Category_Type,
        SUM(Value) as Total_Expense
    FROM expense_detail
    WHERE Provider_Number = '{first_provider}'
        AND Fiscal_Year = {fiscal_year}
        AND Column_Description = 'Final_Adjusted'
    GROUP BY Expense_Category, Category_Description, Category_Type
    ORDER BY Total_Expense DESC
    LIMIT 10
    """
    expense_df = conn.execute(query).df()
    print(f"Expense categories: {len(expense_df)}")
    print("\nTop 5 expense categories:")
    print(expense_df.head())

conn.close()

print()
print("=" * 60)
print("ALL TESTS PASSED! Dashboard should work now.")
print("=" * 60)
print()
print("To start the dashboard, run:")
print("  python valuation_dashboard.py")
print()
print("Then open your browser to: http://127.0.0.1:8051")
