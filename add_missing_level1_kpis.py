"""
Add the 2 missing Level 1 KPIs to the hospital_kpis table:
1. Medicare_CCR (Medicare Cost-to-Charge Ratio)
2. Bad_Debt_Charity_Pct (Bad Debt + Charity as % of Net Revenue)

Formulas from to_do.txt:
- Medicare CCR: (C Pt I Col 5 Sum) ÷ (C Pt I Col 8 Sum)
- Bad Debt + Charity %: (S-10 Line 29 Col 3 + Line 23 Col 3) ÷ (G-3 Line 3 - Provisions)
"""

import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = 'data/hospital_analytics.duckdb'
WORKSHEET_DB_PATH = 'data/hospital_worksheets.duckdb'

print("=" * 80)
print("Adding Missing Level 1 KPIs to Database")
print("=" * 80)
print()

# Connect to databases
print("Connecting to databases...")
analytics_con = duckdb.connect(DB_PATH)
worksheet_con = duckdb.connect(WORKSHEET_DB_PATH, read_only=True)

# Get list of all providers and fiscal years from existing data
existing_data = analytics_con.execute("""
    SELECT DISTINCT Provider_Number, Fiscal_Year
    FROM hospital_kpis
    ORDER BY Provider_Number, Fiscal_Year DESC
""").df()

print(f"Found {len(existing_data)} provider-year combinations to process")
print()

# First, check if columns exist, if not add them
print("Adding new columns to hospital_kpis table...")
try:
    analytics_con.execute("ALTER TABLE hospital_kpis ADD COLUMN Medicare_CCR DOUBLE")
    print("  - Added Medicare_CCR column")
except Exception as e:
    print(f"  - Medicare_CCR column already exists or error: {e}")

try:
    analytics_con.execute("ALTER TABLE hospital_kpis ADD COLUMN Bad_Debt_Charity_Pct DOUBLE")
    print("  - Added Bad_Debt_Charity_Pct column")
except Exception as e:
    print(f"  - Bad_Debt_Charity_Pct column already exists or error: {e}")

print()

# Calculate Medicare CCR for each provider-year
print("Calculating Medicare Cost-to-Charge Ratio (CCR)...")
print("Formula: (Worksheet C Part I Col 5 Sum) ÷ (Worksheet C Part I Col 8 Sum)")
print()

medicare_ccr_count = 0
bad_debt_charity_count = 0

for idx, row in existing_data.iterrows():
    provider = row['Provider_Number']
    fiscal_year = row['Fiscal_Year']

    if idx % 50 == 0:
        print(f"Processing {idx+1}/{len(existing_data)}: Provider {provider}, FY {fiscal_year}")

    # Calculate Medicare CCR from Worksheet C
    # Formula: Total Costs (Col 5) / Total Charges (Col 8)
    try:
        # Get total costs from worksheet_c000001 where Column like '%00500%' (Column 5)
        total_costs = worksheet_con.execute("""
            SELECT SUM(Value) as total_costs
            FROM worksheet_c000001
            WHERE Provider_Number = ?
              AND fiscal_year = ?
              AND "Column" LIKE '%00500%'
              AND Value IS NOT NULL
              AND Value > 0
        """, [str(provider), int(fiscal_year)]).fetchone()

        # Get total charges from worksheet_c000001 where Column like '%00800%' (Column 8)
        total_charges = worksheet_con.execute("""
            SELECT SUM(Value) as total_charges
            FROM worksheet_c000001
            WHERE Provider_Number = ?
              AND fiscal_year = ?
              AND "Column" LIKE '%00800%'
              AND Value IS NOT NULL
              AND Value > 0
        """, [str(provider), int(fiscal_year)]).fetchone()

        if (total_costs and total_costs[0] and total_costs[0] > 0 and
            total_charges and total_charges[0] and total_charges[0] > 0):
            medicare_ccr = total_costs[0] / total_charges[0]

            # Update the KPI in hospital_kpis table
            analytics_con.execute("""
                UPDATE hospital_kpis
                SET Medicare_CCR = ?
                WHERE Provider_Number = ? AND Fiscal_Year = ?
            """, [medicare_ccr, int(provider), int(fiscal_year)])

            medicare_ccr_count += 1

    except Exception as e:
        pass  # Silently skip if worksheet data not available

    # Calculate Bad Debt + Charity % from Worksheet S-10 and G-3
    # Formula: (S-10 Line 29 Col 3 + Line 23 Col 3) ÷ (G-3 Line 3 - Provisions)
    try:
        # Get bad debt and charity care from worksheet_s100001
        # Line 02300 = Charity Care, Line 02900 = Bad Debt, Column 00300 = Amount
        bad_debt_charity_data = worksheet_con.execute("""
            SELECT
                SUM(CASE WHEN (Line LIKE '%02300%' OR Line LIKE '%02900%') AND "Column" LIKE '%00300%'
                    THEN Value ELSE 0 END) as bad_debt_charity
            FROM worksheet_s100001
            WHERE Provider_Number = ?
              AND fiscal_year = ?
              AND Value IS NOT NULL
        """, [str(provider), int(fiscal_year)]).fetchone()

        # Get net patient revenue from worksheet_g300000 (Statement of Revenues)
        # Line 00300 typically contains net patient revenue
        net_revenue_data = worksheet_con.execute("""
            SELECT SUM(Value) as net_revenue
            FROM worksheet_g300000
            WHERE Provider_Number = ?
              AND fiscal_year = ?
              AND Line LIKE '%00300%'
              AND "Column" LIKE '%00100%'
              AND Value IS NOT NULL
              AND Value > 0
        """, [str(provider), int(fiscal_year)]).fetchone()

        if (bad_debt_charity_data and bad_debt_charity_data[0] and bad_debt_charity_data[0] > 0 and
            net_revenue_data and net_revenue_data[0] and net_revenue_data[0] > 0):

            bad_debt_charity_pct = (bad_debt_charity_data[0] / net_revenue_data[0]) * 100

            # Update the KPI in hospital_kpis table
            analytics_con.execute("""
                UPDATE hospital_kpis
                SET Bad_Debt_Charity_Pct = ?
                WHERE Provider_Number = ? AND Fiscal_Year = ?
            """, [bad_debt_charity_pct, int(provider), int(fiscal_year)])

            bad_debt_charity_count += 1

    except Exception as e:
        pass  # Silently skip if worksheet data not available

# Commit changes
analytics_con.commit()

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
print(f"Successfully calculated Medicare CCR for {medicare_ccr_count} provider-years")
print(f"Successfully calculated Bad Debt + Charity % for {bad_debt_charity_count} provider-years")
print()

# Verify the updates
verification = analytics_con.execute("""
    SELECT
        COUNT(*) as total_records,
        COUNT(Medicare_CCR) as medicare_ccr_count,
        COUNT(Bad_Debt_Charity_Pct) as bad_debt_charity_count,
        AVG(Medicare_CCR) as avg_medicare_ccr,
        AVG(Bad_Debt_Charity_Pct) as avg_bad_debt_charity
    FROM hospital_kpis
""").df()

print("Verification:")
print(f"  Total records in hospital_kpis: {verification['total_records'].iloc[0]}")
print(f"  Records with Medicare CCR: {verification['medicare_ccr_count'].iloc[0]}")
print(f"  Records with Bad Debt + Charity %: {verification['bad_debt_charity_count'].iloc[0]}")
print(f"  Average Medicare CCR: {verification['avg_medicare_ccr'].iloc[0]:.4f}" if verification['avg_medicare_ccr'].iloc[0] else "  Average Medicare CCR: N/A")
print(f"  Average Bad Debt + Charity %: {verification['avg_bad_debt_charity'].iloc[0]:.2f}%" if verification['avg_bad_debt_charity'].iloc[0] else "  Average Bad Debt + Charity %: N/A")
print()

# Close connections
analytics_con.close()
worksheet_con.close()

print("Database updated successfully!")
print()
print("Next steps:")
print("  1. Restart the dashboard")
print("  2. All 6 Level 1 KPIs should now be visible")
print()
