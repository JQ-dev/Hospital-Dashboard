"""
Fix Missing KPIs - Populate Missing Data and Generate Benchmarks

This script:
1. Extracts missing KPI data from HCRIS worksheets
2. Adds 3 new columns to hospital_kpis table
3. Populates the missing KPI values
4. Generates benchmarks for all 3 KPIs
5. Updates hospital_benchmarks table

Missing KPIs:
- Operating_Expense_per_Adjusted_Discharge (from S-3)
- Medicare_CCR (from S-10)
- Bad_Debt_Charity_Pct (from S-10 and G-3)
"""

import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


class MissingKPIFixer:
    """Fixes missing KPI data by extracting from worksheets and generating benchmarks"""

    def __init__(self,
                 analytics_db='data/hospital_analytics.duckdb',
                 worksheet_db='data/hospital_worksheets.duckdb'):
        """Initialize with database paths"""
        self.analytics_db = analytics_db
        self.worksheet_db = worksheet_db

        # Track statistics
        self.stats = {
            'adjusted_discharge_records': 0,
            'medicare_ccr_records': 0,
            'bad_debt_charity_records': 0,
            'benchmarks_created': 0,
            'errors': []
        }

    def log(self, message):
        """Print timestamped log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def classify_hospital_type(self, ccn):
        """Classify hospital type by CCN range"""
        if not ccn:
            return 'Unknown'

        ccn_str = str(int(ccn)).zfill(6)
        if len(ccn_str) != 6:
            return 'Unknown'

        provider_num = int(ccn_str[2:])

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

    def extract_adjusted_discharges(self):
        """Extract Adjusted Discharges from Worksheet S-3"""
        self.log("Extracting Adjusted Discharges from Worksheet S-3...")

        con = duckdb.connect(self.worksheet_db, read_only=True)

        # Get adjusted discharges (Line 1400, Column 1500)
        query = """
            SELECT
                Provider_Number,
                fiscal_year as Fiscal_Year,
                Value as Adjusted_Discharges
            FROM worksheet_s300001
            WHERE Line = '01400'
              AND "Column" = '01500'
              AND Value IS NOT NULL
              AND Value > 0
            ORDER BY Provider_Number, fiscal_year
        """

        df = con.execute(query).df()
        con.close()

        self.stats['adjusted_discharge_records'] = len(df)
        self.log(f"  Found {len(df)} adjusted discharge records")

        return df

    def extract_medicare_ccr(self):
        """Extract Medicare Cost-to-Charge Ratio from Worksheet S-10"""
        self.log("Extracting Medicare CCR from Worksheet S-10...")

        con = duckdb.connect(self.worksheet_db, read_only=True)

        # Medicare CCR is directly available on Line 100, Column 100
        query = """
            SELECT
                Provider_Number,
                fiscal_year as Fiscal_Year,
                Value as Medicare_CCR
            FROM worksheet_s100001
            WHERE Line = '00100'
              AND "Column" = '00100'
              AND Value IS NOT NULL
              AND Value > 0
              AND Value < 1.5  -- Sanity check: CCR should be less than 1.5 typically
            ORDER BY Provider_Number, fiscal_year
        """

        df = con.execute(query).df()
        con.close()

        self.stats['medicare_ccr_records'] = len(df)
        self.log(f"  Found {len(df)} Medicare CCR records")

        return df

    def extract_bad_debt_charity(self):
        """Extract Bad Debt and Charity Care from Worksheets S-10 and G-3"""
        self.log("Extracting Bad Debt and Charity Care from Worksheets S-10 and G-3...")

        con = duckdb.connect(self.worksheet_db, read_only=True)

        # Get charity care and bad debt from S-10
        charity_bad_debt_query = """
            SELECT
                Provider_Number,
                fiscal_year,
                SUM(CASE WHEN Line = '02000' AND "Column" = '00300' THEN Value ELSE 0 END) as Charity_Care,
                SUM(CASE WHEN Line = '02500' THEN Value ELSE 0 END) as Bad_Debt_Expense,
                SUM(CASE WHEN Line = '02600' AND "Column" = '00100' THEN Value ELSE 0 END) as Bad_Debt_Recoveries
            FROM worksheet_s100001
            WHERE Line IN ('02000', '02500', '02600')
            GROUP BY Provider_Number, fiscal_year
        """

        charity_debt_df = con.execute(charity_bad_debt_query).df()

        # Get net patient revenue from G-3
        # Look for lines that contain revenue data (Line 3 is typically net patient revenue)
        revenue_query = """
            SELECT
                Provider_Number,
                fiscal_year,
                SUM(Value) as Net_Patient_Revenue
            FROM worksheet_g300000
            WHERE Line = '00300'
              AND Value IS NOT NULL
              AND Value > 0
            GROUP BY Provider_Number, fiscal_year
        """

        revenue_df = con.execute(revenue_query).df()
        con.close()

        # Merge the two datasets
        merged = charity_debt_df.merge(
            revenue_df,
            on=['Provider_Number', 'fiscal_year'],
            how='inner'
        )

        # Calculate Bad Debt + Charity as % of Net Revenue
        merged['Bad_Debt_Charity_Pct'] = np.where(
            merged['Net_Patient_Revenue'] > 0,
            ((merged['Charity_Care'] + merged['Bad_Debt_Expense'] - merged['Bad_Debt_Recoveries']) /
             merged['Net_Patient_Revenue']) * 100,
            None
        )

        # Filter out invalid values
        merged = merged[
            (merged['Bad_Debt_Charity_Pct'].notna()) &
            (merged['Bad_Debt_Charity_Pct'] >= 0) &
            (merged['Bad_Debt_Charity_Pct'] <= 100)  # Sanity check
        ]

        result = merged[['Provider_Number', 'fiscal_year', 'Bad_Debt_Charity_Pct']].copy()
        result.columns = ['Provider_Number', 'Fiscal_Year', 'Bad_Debt_Charity_Pct']

        self.stats['bad_debt_charity_records'] = len(result)
        self.log(f"  Found {len(result)} Bad Debt + Charity records")

        return result

    def update_hospital_kpis_table(self):
        """Add new columns and populate hospital_kpis table"""
        self.log("=" * 80)
        self.log("STEP 1: Updating hospital_kpis table with missing KPIs")
        self.log("=" * 80)

        # Extract data from worksheets
        adjusted_discharge_df = self.extract_adjusted_discharges()
        medicare_ccr_df = self.extract_medicare_ccr()
        bad_debt_charity_df = self.extract_bad_debt_charity()

        # Connect to analytics database
        con = duckdb.connect(self.analytics_db)

        # Check if columns already exist
        existing_columns = con.execute("""
            SELECT column_name FROM (DESCRIBE hospital_kpis)
        """).df()['column_name'].tolist()

        # Add columns if they don't exist
        new_columns = {
            'Adjusted_Discharges': 'DOUBLE',
            'Operating_Expense_per_Adjusted_Discharge': 'DOUBLE',
            'Medicare_CCR': 'DOUBLE',
            'Bad_Debt_Charity_Pct': 'DOUBLE'
        }

        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                self.log(f"Adding column: {col_name}")
                con.execute(f"ALTER TABLE hospital_kpis ADD COLUMN {col_name} {col_type}")
            else:
                self.log(f"Column already exists: {col_name}")

        # Create temporary tables for updates
        self.log("Creating temporary tables for data updates...")

        con.execute("DROP TABLE IF EXISTS temp_adjusted_discharges")
        con.execute("CREATE TEMP TABLE temp_adjusted_discharges AS SELECT * FROM adjusted_discharge_df")

        con.execute("DROP TABLE IF EXISTS temp_medicare_ccr")
        con.execute("CREATE TEMP TABLE temp_medicare_ccr AS SELECT * FROM medicare_ccr_df")

        con.execute("DROP TABLE IF EXISTS temp_bad_debt_charity")
        con.execute("CREATE TEMP TABLE temp_bad_debt_charity AS SELECT * FROM bad_debt_charity_df")

        # Update Adjusted Discharges
        self.log("Updating Adjusted_Discharges...")
        con.execute("""
            UPDATE hospital_kpis
            SET Adjusted_Discharges = temp.Adjusted_Discharges
            FROM temp_adjusted_discharges temp
            WHERE hospital_kpis.Provider_Number = temp.Provider_Number
              AND hospital_kpis.Fiscal_Year = temp.Fiscal_Year
        """)

        # Calculate Operating_Expense_per_Adjusted_Discharge
        self.log("Calculating Operating_Expense_per_Adjusted_Discharge...")
        con.execute("""
            UPDATE hospital_kpis
            SET Operating_Expense_per_Adjusted_Discharge =
                CASE
                    WHEN Adjusted_Discharges > 0
                    THEN Total_Operating_Expenses / Adjusted_Discharges
                    ELSE NULL
                END
            WHERE Adjusted_Discharges IS NOT NULL
        """)

        # Update Medicare CCR
        self.log("Updating Medicare_CCR...")
        con.execute("""
            UPDATE hospital_kpis
            SET Medicare_CCR = temp.Medicare_CCR
            FROM temp_medicare_ccr temp
            WHERE hospital_kpis.Provider_Number = temp.Provider_Number
              AND hospital_kpis.Fiscal_Year = temp.Fiscal_Year
        """)

        # Update Bad Debt + Charity %
        self.log("Updating Bad_Debt_Charity_Pct...")
        con.execute("""
            UPDATE hospital_kpis
            SET Bad_Debt_Charity_Pct = temp.Bad_Debt_Charity_Pct
            FROM temp_bad_debt_charity temp
            WHERE hospital_kpis.Provider_Number = temp.Provider_Number
              AND hospital_kpis.Fiscal_Year = temp.Fiscal_Year
        """)

        # Verify updates
        verification = con.execute("""
            SELECT
                COUNT(*) as total_rows,
                SUM(CASE WHEN Adjusted_Discharges IS NOT NULL THEN 1 ELSE 0 END) as adj_discharge_count,
                SUM(CASE WHEN Operating_Expense_per_Adjusted_Discharge IS NOT NULL THEN 1 ELSE 0 END) as op_exp_per_discharge_count,
                SUM(CASE WHEN Medicare_CCR IS NOT NULL THEN 1 ELSE 0 END) as medicare_ccr_count,
                SUM(CASE WHEN Bad_Debt_Charity_Pct IS NOT NULL THEN 1 ELSE 0 END) as bad_debt_charity_count
            FROM hospital_kpis
        """).fetchone()

        self.log("Verification:")
        self.log(f"  Total rows in hospital_kpis: {verification[0]}")
        self.log(f"  Adjusted Discharges populated: {verification[1]}")
        self.log(f"  Operating Expense per Adj Discharge populated: {verification[2]}")
        self.log(f"  Medicare CCR populated: {verification[3]}")
        self.log(f"  Bad Debt + Charity % populated: {verification[4]}")

        con.close()

        self.log("[OK] hospital_kpis table updated successfully")

    def generate_benchmarks(self):
        """Generate benchmarks for the 3 new KPIs"""
        self.log("=" * 80)
        self.log("STEP 2: Generating benchmarks for missing KPIs")
        self.log("=" * 80)

        con = duckdb.connect(self.analytics_db)

        # Get all hospital data
        kpis_df = con.execute("""
            SELECT
                Provider_Number,
                Fiscal_Year,
                Operating_Expense_per_Adjusted_Discharge,
                Medicare_CCR,
                Bad_Debt_Charity_Pct
            FROM hospital_kpis
            WHERE Fiscal_Year IS NOT NULL
        """).df()

        # Extract state code from Provider_Number (first 2 digits)
        kpis_df['State_Code'] = kpis_df['Provider_Number'].apply(
            lambda x: int(str(int(x)).zfill(6)[:2])
        )

        # Add hospital type classification
        kpis_df['Hospital_Type'] = kpis_df['Provider_Number'].apply(
            lambda x: self.classify_hospital_type(str(int(x)).zfill(6))
        )

        # KPIs to benchmark
        kpi_columns = [
            'Operating_Expense_per_Adjusted_Discharge',
            'Medicare_CCR',
            'Bad_Debt_Charity_Pct'
        ]

        benchmark_rows = []

        # Benchmark levels
        fiscal_years = sorted(kpis_df['Fiscal_Year'].unique())

        for fiscal_year in fiscal_years:
            year_data = kpis_df[kpis_df['Fiscal_Year'] == fiscal_year]

            self.log(f"Generating benchmarks for year {fiscal_year}...")

            for kpi_name in kpi_columns:
                # Skip if no data for this KPI
                kpi_data = year_data[year_data[kpi_name].notna()][kpi_name]
                if len(kpi_data) == 0:
                    continue

                # 1. National benchmark
                benchmark_rows.append({
                    'KPI_Name': kpi_name,
                    'Benchmark_Level': 'National',
                    'State_Code': None,
                    'Hospital_Type': None,
                    'Fiscal_Year': fiscal_year,
                    'Provider_Count': len(kpi_data),
                    'P25': np.percentile(kpi_data, 25),
                    'Median': np.percentile(kpi_data, 50),
                    'P75': np.percentile(kpi_data, 75),
                    'Mean': np.mean(kpi_data)
                })

                # 2. State-level benchmarks
                for state_code in year_data['State_Code'].unique():
                    state_data = year_data[
                        (year_data['State_Code'] == state_code) &
                        (year_data[kpi_name].notna())
                    ][kpi_name]

                    if len(state_data) >= 3:  # Need at least 3 hospitals for meaningful benchmark
                        benchmark_rows.append({
                            'KPI_Name': kpi_name,
                            'Benchmark_Level': 'State',
                            'State_Code': int(state_code),
                            'Hospital_Type': None,
                            'Fiscal_Year': fiscal_year,
                            'Provider_Count': len(state_data),
                            'P25': np.percentile(state_data, 25),
                            'Median': np.percentile(state_data, 50),
                            'P75': np.percentile(state_data, 75),
                            'Mean': np.mean(state_data)
                        })

                # 3. Hospital Type benchmarks
                for hospital_type in year_data['Hospital_Type'].unique():
                    type_data = year_data[
                        (year_data['Hospital_Type'] == hospital_type) &
                        (year_data[kpi_name].notna())
                    ][kpi_name]

                    if len(type_data) >= 3:
                        benchmark_rows.append({
                            'KPI_Name': kpi_name,
                            'Benchmark_Level': 'Hospital_Type',
                            'State_Code': None,
                            'Hospital_Type': hospital_type,
                            'Fiscal_Year': fiscal_year,
                            'Provider_Count': len(type_data),
                            'P25': np.percentile(type_data, 25),
                            'Median': np.percentile(type_data, 50),
                            'P75': np.percentile(type_data, 75),
                            'Mean': np.mean(type_data)
                        })

                # 4. State + Hospital Type benchmarks
                for state_code in year_data['State_Code'].unique():
                    for hospital_type in year_data['Hospital_Type'].unique():
                        combined_data = year_data[
                            (year_data['State_Code'] == state_code) &
                            (year_data['Hospital_Type'] == hospital_type) &
                            (year_data[kpi_name].notna())
                        ][kpi_name]

                        if len(combined_data) >= 3:
                            benchmark_rows.append({
                                'KPI_Name': kpi_name,
                                'Benchmark_Level': 'State_Hospital_Type',
                                'State_Code': int(state_code),
                                'Hospital_Type': hospital_type,
                                'Fiscal_Year': fiscal_year,
                                'Provider_Count': len(combined_data),
                                'P25': np.percentile(combined_data, 25),
                                'Median': np.percentile(combined_data, 50),
                                'P75': np.percentile(combined_data, 75),
                                'Mean': np.mean(combined_data)
                            })

        self.stats['benchmarks_created'] = len(benchmark_rows)
        self.log(f"Generated {len(benchmark_rows)} benchmark records")

        # Insert benchmarks into database
        if len(benchmark_rows) > 0:
            benchmarks_df = pd.DataFrame(benchmark_rows)

            # Delete existing benchmarks for these KPIs
            self.log("Removing old benchmarks for these KPIs (if any)...")
            for kpi_name in kpi_columns:
                con.execute(f"""
                    DELETE FROM hospital_benchmarks
                    WHERE KPI_Name = '{kpi_name}'
                """)

            # Insert new benchmarks
            self.log("Inserting new benchmarks...")
            con.execute("""
                INSERT INTO hospital_benchmarks
                SELECT * FROM benchmarks_df
            """)

            self.log("[OK] Benchmarks generated and inserted successfully")

        con.close()

    def verify_fixes(self):
        """Verify that all fixes were applied correctly"""
        self.log("=" * 80)
        self.log("STEP 3: Verifying fixes")
        self.log("=" * 80)

        con = duckdb.connect(self.analytics_db, read_only=True)

        # Check KPI data
        kpi_check = con.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN Operating_Expense_per_Adjusted_Discharge IS NOT NULL THEN 1 ELSE 0 END) as op_exp_count,
                SUM(CASE WHEN Medicare_CCR IS NOT NULL THEN 1 ELSE 0 END) as medicare_ccr_count,
                SUM(CASE WHEN Bad_Debt_Charity_Pct IS NOT NULL THEN 1 ELSE 0 END) as bad_debt_count
            FROM hospital_kpis
        """).fetchone()

        # Check benchmarks
        benchmark_check = con.execute("""
            SELECT
                KPI_Name,
                COUNT(*) as benchmark_count,
                COUNT(DISTINCT Fiscal_Year) as years,
                COUNT(DISTINCT Benchmark_Level) as levels
            FROM hospital_benchmarks
            WHERE KPI_Name IN ('Operating_Expense_per_Adjusted_Discharge', 'Medicare_CCR', 'Bad_Debt_Charity_Pct')
            GROUP BY KPI_Name
            ORDER BY KPI_Name
        """).df()

        con.close()

        self.log("")
        self.log("Hospital KPIs Table:")
        self.log(f"  Total rows: {kpi_check[0]}")
        self.log(f"  Operating Expense per Adj Discharge: {kpi_check[1]} records ({kpi_check[1]/kpi_check[0]*100:.1f}%)")
        self.log(f"  Medicare CCR: {kpi_check[2]} records ({kpi_check[2]/kpi_check[0]*100:.1f}%)")
        self.log(f"  Bad Debt + Charity %: {kpi_check[3]} records ({kpi_check[3]/kpi_check[0]*100:.1f}%)")

        self.log("")
        self.log("Hospital Benchmarks Table:")
        for _, row in benchmark_check.iterrows():
            self.log(f"  {row['KPI_Name']}: {row['benchmark_count']} benchmarks across {row['years']} years and {row['levels']} levels")

    def run(self):
        """Execute the full fix process"""
        self.log("=" * 80)
        self.log("MISSING KPI FIX - Starting Process")
        self.log("=" * 80)
        self.log("")

        try:
            # Step 1: Update hospital_kpis table
            self.update_hospital_kpis_table()

            # Step 2: Generate benchmarks
            self.generate_benchmarks()

            # Step 3: Verify fixes
            self.verify_fixes()

            # Print summary
            self.log("")
            self.log("=" * 80)
            self.log("FIX COMPLETED SUCCESSFULLY")
            self.log("=" * 80)
            self.log("")
            self.log("Summary:")
            self.log(f"  Adjusted Discharge records extracted: {self.stats['adjusted_discharge_records']}")
            self.log(f"  Medicare CCR records extracted: {self.stats['medicare_ccr_records']}")
            self.log(f"  Bad Debt + Charity records extracted: {self.stats['bad_debt_charity_records']}")
            self.log(f"  Benchmarks created: {self.stats['benchmarks_created']}")

            if len(self.stats['errors']) > 0:
                self.log("")
                self.log("Errors encountered:")
                for error in self.stats['errors']:
                    self.log(f"  - {error}")
            else:
                self.log("")
                self.log("[OK] No errors encountered")

            self.log("")
            self.log("Next steps:")
            self.log("  1. Restart the dashboard: python dashboard.py")
            self.log("  2. Verify all 6 Level 1 KPI cards display data")
            self.log("  3. Check that benchmarks are populated for all cards")

        except Exception as e:
            self.log("")
            self.log(f"ERROR: {str(e)}")
            self.stats['errors'].append(str(e))
            import traceback
            traceback.print_exc()
            raise


if __name__ == '__main__':
    fixer = MissingKPIFixer()
    fixer.run()
