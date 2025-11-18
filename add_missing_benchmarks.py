"""
Add benchmarks for Medicare_CCR and Bad_Debt_Charity_Pct

These two KPIs were added after the initial benchmark computation,
so we need to generate benchmarks for them.
"""

import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = 'data/hospital_analytics.duckdb'

print("=" * 80)
print("Adding Benchmarks for Missing KPIs")
print("=" * 80)
print()

def classify_hospital_type(ccn):
    """Classify hospital type by CCN range"""
    if not ccn or len(str(ccn)) != 6:
        return 'Unknown'

    provider_num = int(str(ccn)[2:])

    if 1 <= provider_num <= 899:
        return 'Short Term Acute Care'
    elif 3300 <= provider_num <= 3399:
        return "Children's"
    elif 1300 <= provider_num <= 1399:
        return 'Critical Access'
    elif 2000 <= provider_num <= 2299:
        return 'Long Term'
    elif 4000 <= provider_num <= 4499:
        return 'Psychiatric'
    elif 3025 <= provider_num <= 3099:
        return 'Rehabilitation'
    else:
        return 'Other'

con = duckdb.connect(DB_PATH)

# The two missing KPIs
missing_kpis = ['Medicare_CCR', 'Bad_Debt_Charity_Pct']

print(f"Adding benchmarks for: {', '.join(missing_kpis)}")
print()

# Check if hospital_metadata table exists
metadata_exists = con.execute("""
    SELECT COUNT(*) FROM information_schema.tables
    WHERE table_name = 'hospital_metadata'
""").fetchone()[0] > 0

if not metadata_exists:
    print("Creating hospital_metadata table...")
    # Get state codes from balance sheet
    state_codes = con.execute("""
        SELECT DISTINCT Provider_Number, State_Code
        FROM balance_sheet
    """).df()

    # Add hospital type classification
    print("Classifying hospital types...")
    state_codes['Hospital_Type'] = state_codes['Provider_Number'].apply(
        lambda x: classify_hospital_type(str(int(x)).zfill(6))
    )

    # Create hospital metadata table
    con.register('hospital_metadata_temp', state_codes)
    con.execute("""
        CREATE TABLE hospital_metadata AS
        SELECT * FROM hospital_metadata_temp
    """)
    con.execute("CREATE INDEX idx_meta_provider ON hospital_metadata(Provider_Number)")
    print(f"Hospital metadata: {len(state_codes):,} hospitals classified")
    print()

# Get available years and states
years = con.execute("SELECT DISTINCT Fiscal_Year FROM hospital_kpis ORDER BY Fiscal_Year").df()['Fiscal_Year'].tolist()
states = con.execute("SELECT DISTINCT State_Code FROM hospital_metadata WHERE State_Code IS NOT NULL").df()['State_Code'].tolist()
hosp_types = con.execute("SELECT DISTINCT Hospital_Type FROM hospital_metadata WHERE Hospital_Type IS NOT NULL").df()['Hospital_Type'].tolist()

print(f"Found: {len(years)} years, {len(states)} states, {len(hosp_types)} hospital types")
print()

benchmark_dfs = []
total_benchmarks = 0

for kpi in missing_kpis:
    print(f"Computing benchmarks for {kpi}...")

    # NATIONAL BENCHMARKS
    print(f"  - National benchmarks...")
    for year in years:
        stats = con.execute(f"""
            SELECT
                '{kpi}' as KPI_Name,
                'National' as Benchmark_Level,
                NULL as State_Code,
                NULL as Hospital_Type,
                {year} as Fiscal_Year,
                COUNT(*) as Provider_Count,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {kpi}) as P25,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY {kpi}) as Median,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {kpi}) as P75,
                AVG({kpi}) as Mean
            FROM hospital_kpis
            WHERE Fiscal_Year = {year} AND {kpi} IS NOT NULL
        """).df()
        if len(stats) > 0 and stats['Provider_Count'].iloc[0] > 0:
            benchmark_dfs.append(stats)
            total_benchmarks += 1

    # STATE BENCHMARKS
    print(f"  - State benchmarks...")
    for state in states:
        for year in years:
            stats = con.execute(f"""
                SELECT
                    '{kpi}' as KPI_Name,
                    'State' as Benchmark_Level,
                    '{state}' as State_Code,
                    NULL as Hospital_Type,
                    {year} as Fiscal_Year,
                    COUNT(*) as Provider_Count,
                    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY k.{kpi}) as P25,
                    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY k.{kpi}) as Median,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY k.{kpi}) as P75,
                    AVG(k.{kpi}) as Mean
                FROM hospital_kpis k
                JOIN hospital_metadata m ON k.Provider_Number = m.Provider_Number
                WHERE k.Fiscal_Year = {year} AND m.State_Code = '{state}' AND k.{kpi} IS NOT NULL
            """).df()
            if len(stats) > 0 and stats['Provider_Count'].iloc[0] > 0:
                benchmark_dfs.append(stats)
                total_benchmarks += 1

    # HOSPITAL TYPE BENCHMARKS
    print(f"  - Hospital type benchmarks...")
    for hosp_type in hosp_types:
        for year in years:
            # Escape single quotes in hospital type name
            hosp_type_escaped = hosp_type.replace("'", "''")
            stats = con.execute(f"""
                SELECT
                    '{kpi}' as KPI_Name,
                    'Hospital_Type' as Benchmark_Level,
                    NULL as State_Code,
                    '{hosp_type_escaped}' as Hospital_Type,
                    {year} as Fiscal_Year,
                    COUNT(*) as Provider_Count,
                    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY k.{kpi}) as P25,
                    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY k.{kpi}) as Median,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY k.{kpi}) as P75,
                    AVG(k.{kpi}) as Mean
                FROM hospital_kpis k
                JOIN hospital_metadata m ON k.Provider_Number = m.Provider_Number
                WHERE k.Fiscal_Year = {year} AND m.Hospital_Type = '{hosp_type_escaped}' AND k.{kpi} IS NOT NULL
            """).df()
            if len(stats) > 0 and stats['Provider_Count'].iloc[0] > 0:
                benchmark_dfs.append(stats)
                total_benchmarks += 1

    # STATE + HOSPITAL TYPE BENCHMARKS
    print(f"  - State + hospital type benchmarks...")
    for state in states:
        for hosp_type in hosp_types:
            for year in years:
                # Escape single quotes in hospital type name
                hosp_type_escaped = hosp_type.replace("'", "''")
                stats = con.execute(f"""
                    SELECT
                        '{kpi}' as KPI_Name,
                        'State_Hospital_Type' as Benchmark_Level,
                        '{state}' as State_Code,
                        '{hosp_type_escaped}' as Hospital_Type,
                        {year} as Fiscal_Year,
                        COUNT(*) as Provider_Count,
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY k.{kpi}) as P25,
                        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY k.{kpi}) as Median,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY k.{kpi}) as P75,
                        AVG(k.{kpi}) as Mean
                    FROM hospital_kpis k
                    JOIN hospital_metadata m ON k.Provider_Number = m.Provider_Number
                    WHERE k.Fiscal_Year = {year}
                        AND m.State_Code = '{state}'
                        AND m.Hospital_Type = '{hosp_type_escaped}'
                        AND k.{kpi} IS NOT NULL
                """).df()
                if len(stats) > 0 and stats['Provider_Count'].iloc[0] > 0:
                    benchmark_dfs.append(stats)
                    total_benchmarks += 1

    print(f"  Completed {kpi}")
    print()

# Combine all benchmarks
print(f"Combining {total_benchmarks} benchmark records...")
all_benchmarks = pd.concat(benchmark_dfs, ignore_index=True)

# Convert State_Code to INTEGER
print("Converting State_Code to INTEGER...")
all_benchmarks['State_Code'] = all_benchmarks['State_Code'].apply(
    lambda x: int(x) if pd.notna(x) else None
)

# Insert into hospital_benchmarks table
print("Inserting into hospital_benchmarks table...")
con.register('new_benchmarks', all_benchmarks)
con.execute("""
    INSERT INTO hospital_benchmarks
    SELECT * FROM new_benchmarks
""")

con.commit()
con.close()

print()
print("=" * 80)
print("COMPLETE!")
print("=" * 80)
print(f"Added {total_benchmarks} benchmark records for {len(missing_kpis)} KPIs")
print()
print("Verification:")
for kpi in missing_kpis:
    con2 = duckdb.connect(DB_PATH, read_only=True)
    count = con2.execute(f"""
        SELECT COUNT(*) FROM hospital_benchmarks WHERE KPI_Name = '{kpi}'
    """).fetchone()[0]
    print(f"  {kpi}: {count} benchmarks")
    con2.close()

print()
print("Next step: Restart the dashboard to see the new benchmarks!")
print()
