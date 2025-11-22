"""
Fix AR Days (Accounts Receivable Days) - Populate Missing Data

The hospital_kpis table has Accounts_Receivable = 0 for all records,
causing AR_Days to be 0 or NULL.

Root Cause:
- The original KPI build script used 'Line_Name' column which doesn't exist
- Should use 'Acc_name' or 'Account_Name' to filter for receivables

This script:
1. Extracts correct Accounts Receivable from balance_sheet table
2. Updates hospital_kpis with correct AR values
3. Recalculates AR_Days
4. Regenerates AR_Days benchmarks
"""

import duckdb
import pandas as pd
import numpy as np
from datetime import datetime


class ARDaysFixer:
    """Fixes Accounts Receivable and AR_Days data"""

    def __init__(self, analytics_db='data/hospital_analytics.duckdb'):
        """Initialize with database path"""
        self.analytics_db = analytics_db
        self.stats = {
            'ar_records_updated': 0,
            'ar_days_calculated': 0,
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

    def extract_accounts_receivable(self):
        """Extract Accounts Receivable from balance_sheet table"""
        self.log("Extracting Accounts Receivable from balance_sheet...")

        con = duckdb.connect(self.analytics_db, read_only=True)

        # Get net accounts receivable (gross AR minus allowances)
        # Note: balance_sheet has duplicate rows, so we use DISTINCT to deduplicate
        query = """
            WITH deduplicated AS (
                SELECT DISTINCT
                    Provider_Number,
                    Fiscal_Year,
                    Acc_name,
                    Value
                FROM balance_sheet
                WHERE Acc_name IN ('Accounts Receivable',
                                   'Allowances For Uncollectible Notes And Accounts Receivable')
            )
            SELECT
                Provider_Number,
                Fiscal_Year,
                SUM(CASE
                    WHEN Acc_name = 'Accounts Receivable' THEN Value
                    WHEN Acc_name LIKE '%Allowances%Receivable%' THEN Value
                    ELSE 0
                END) as Net_Accounts_Receivable
            FROM deduplicated
            GROUP BY Provider_Number, Fiscal_Year
            HAVING SUM(CASE WHEN Acc_name = 'Accounts Receivable' THEN Value ELSE 0 END) > 0
            ORDER BY Provider_Number, Fiscal_Year
        """

        df = con.execute(query).df()
        con.close()

        # Ensure AR is positive (allowances are negative, so the sum gives net AR)
        df['Net_Accounts_Receivable'] = df['Net_Accounts_Receivable'].clip(lower=0)

        self.stats['ar_records_updated'] = len(df)
        self.log(f"  Found {len(df)} Accounts Receivable records")

        return df

    def update_hospital_kpis(self):
        """Update Accounts Receivable and recalculate AR_Days in hospital_kpis table"""
        self.log("=" * 80)
        self.log("STEP 1: Updating Accounts Receivable in hospital_kpis")
        self.log("=" * 80)

        # Extract correct AR data
        ar_df = self.extract_accounts_receivable()

        # Connect to database
        con = duckdb.connect(self.analytics_db)

        # Create temp table
        self.log("Creating temporary table for AR data...")
        con.execute("DROP TABLE IF EXISTS temp_ar_data")
        con.execute("CREATE TEMP TABLE temp_ar_data AS SELECT * FROM ar_df")

        # Update Accounts_Receivable
        self.log("Updating Accounts_Receivable in hospital_kpis...")
        con.execute("""
            UPDATE hospital_kpis
            SET Accounts_Receivable = temp.Net_Accounts_Receivable
            FROM temp_ar_data temp
            WHERE hospital_kpis.Provider_Number = temp.Provider_Number
              AND hospital_kpis.Fiscal_Year = temp.Fiscal_Year
        """)

        # Recalculate AR_Days
        self.log("Recalculating AR_Days...")
        con.execute("""
            UPDATE hospital_kpis
            SET AR_Days =
                CASE
                    WHEN Total_Revenue > 0 AND Accounts_Receivable > 0
                    THEN Accounts_Receivable / (Total_Revenue / 365.0)
                    ELSE NULL
                END
            WHERE Accounts_Receivable IS NOT NULL
        """)

        # Verify updates
        verification = con.execute("""
            SELECT
                COUNT(*) as total_rows,
                SUM(CASE WHEN Accounts_Receivable > 0 THEN 1 ELSE 0 END) as ar_positive,
                SUM(CASE WHEN AR_Days > 0 THEN 1 ELSE 0 END) as ar_days_positive,
                AVG(CASE WHEN AR_Days > 0 THEN AR_Days ELSE NULL END) as avg_ar_days,
                MIN(CASE WHEN AR_Days > 0 THEN AR_Days ELSE NULL END) as min_ar_days,
                MAX(AR_Days) as max_ar_days
            FROM hospital_kpis
        """).fetchone()

        self.stats['ar_days_calculated'] = verification[2]

        self.log("Verification:")
        self.log(f"  Total rows in hospital_kpis: {verification[0]}")
        self.log(f"  Accounts Receivable > 0: {verification[1]} records")
        self.log(f"  AR_Days > 0: {verification[2]} records")
        self.log(f"  Average AR_Days: {verification[3]:.1f} days" if verification[3] else "  Average AR_Days: N/A")
        self.log(f"  Range: {verification[4]:.1f} - {verification[5]:.1f} days" if verification[4] else "  Range: N/A")

        con.close()

        self.log("[OK] Accounts Receivable and AR_Days updated successfully")

    def regenerate_benchmarks(self):
        """Regenerate AR_Days benchmarks with correct data"""
        self.log("=" * 80)
        self.log("STEP 2: Regenerating AR_Days benchmarks")
        self.log("=" * 80)

        con = duckdb.connect(self.analytics_db)

        # Get AR_Days data
        kpis_df = con.execute("""
            SELECT
                Provider_Number,
                Fiscal_Year,
                AR_Days
            FROM hospital_kpis
            WHERE Fiscal_Year IS NOT NULL
              AND AR_Days > 0
        """).df()

        # Extract state code from Provider_Number
        kpis_df['State_Code'] = kpis_df['Provider_Number'].apply(
            lambda x: int(str(int(x)).zfill(6)[:2])
        )

        # Add hospital type classification
        kpis_df['Hospital_Type'] = kpis_df['Provider_Number'].apply(
            lambda x: self.classify_hospital_type(str(int(x)).zfill(6))
        )

        benchmark_rows = []

        # Benchmark levels
        fiscal_years = sorted(kpis_df['Fiscal_Year'].unique())

        for fiscal_year in fiscal_years:
            year_data = kpis_df[kpis_df['Fiscal_Year'] == fiscal_year]

            self.log(f"Generating benchmarks for year {fiscal_year}...")

            kpi_data = year_data[year_data['AR_Days'].notna()]['AR_Days']

            if len(kpi_data) == 0:
                continue

            # 1. National benchmark
            benchmark_rows.append({
                'KPI_Name': 'AR_Days',
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
                    (year_data['AR_Days'].notna())
                ]['AR_Days']

                if len(state_data) >= 3:
                    benchmark_rows.append({
                        'KPI_Name': 'AR_Days',
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
                    (year_data['AR_Days'].notna())
                ]['AR_Days']

                if len(type_data) >= 3:
                    benchmark_rows.append({
                        'KPI_Name': 'AR_Days',
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
                        (year_data['AR_Days'].notna())
                    ]['AR_Days']

                    if len(combined_data) >= 3:
                        benchmark_rows.append({
                            'KPI_Name': 'AR_Days',
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

            # Delete existing AR_Days benchmarks
            self.log("Removing old AR_Days benchmarks...")
            con.execute("DELETE FROM hospital_benchmarks WHERE KPI_Name = 'AR_Days'")

            # Insert new benchmarks
            self.log("Inserting new AR_Days benchmarks...")
            con.execute("INSERT INTO hospital_benchmarks SELECT * FROM benchmarks_df")

            self.log("[OK] AR_Days benchmarks regenerated successfully")

        con.close()

    def verify_fixes(self):
        """Verify that all fixes were applied correctly"""
        self.log("=" * 80)
        self.log("STEP 3: Verifying fixes")
        self.log("=" * 80)

        con = duckdb.connect(self.analytics_db, read_only=True)

        # Check AR_Days data
        ar_check = con.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN Accounts_Receivable > 0 THEN 1 ELSE 0 END) as ar_positive,
                SUM(CASE WHEN AR_Days > 0 THEN 1 ELSE 0 END) as ar_days_positive,
                AVG(CASE WHEN AR_Days > 0 THEN AR_Days ELSE NULL END) as avg_ar_days
            FROM hospital_kpis
        """).fetchone()

        # Check benchmarks
        benchmark_check = con.execute("""
            SELECT
                COUNT(*) as benchmark_count,
                COUNT(DISTINCT Fiscal_Year) as years,
                COUNT(DISTINCT Benchmark_Level) as levels,
                AVG(Median) as avg_median
            FROM hospital_benchmarks
            WHERE KPI_Name = 'AR_Days'
        """).fetchone()

        # Sample data for verification
        sample = con.execute("""
            SELECT
                Fiscal_Year,
                Accounts_Receivable,
                Total_Revenue,
                AR_Days
            FROM hospital_kpis
            WHERE Provider_Number = 310001
              AND AR_Days > 0
            ORDER BY Fiscal_Year DESC
            LIMIT 3
        """).df()

        con.close()

        self.log("")
        self.log("Hospital KPIs Table:")
        self.log(f"  Total rows: {ar_check[0]}")
        self.log(f"  Accounts Receivable > 0: {ar_check[1]} records ({ar_check[1]/ar_check[0]*100:.1f}%)")
        self.log(f"  AR_Days > 0: {ar_check[2]} records ({ar_check[2]/ar_check[0]*100:.1f}%)")
        self.log(f"  Average AR_Days: {ar_check[3]:.1f} days" if ar_check[3] else "  Average AR_Days: N/A")

        self.log("")
        self.log("Hospital Benchmarks Table:")
        self.log(f"  AR_Days benchmarks: {benchmark_check[0]} records")
        self.log(f"  Years covered: {benchmark_check[1]}")
        self.log(f"  Benchmark levels: {benchmark_check[2]}")
        self.log(f"  Average median AR_Days: {benchmark_check[3]:.1f} days" if benchmark_check[3] else "  N/A")

        if len(sample) > 0:
            self.log("")
            self.log("Sample Data - Hospital CCN 310001:")
            self.log(sample.to_string(index=False))

    def run(self):
        """Execute the full fix process"""
        self.log("=" * 80)
        self.log("AR DAYS FIX - Starting Process")
        self.log("=" * 80)
        self.log("")

        try:
            # Step 1: Update AR and AR_Days
            self.update_hospital_kpis()

            # Step 2: Regenerate benchmarks
            self.regenerate_benchmarks()

            # Step 3: Verify fixes
            self.verify_fixes()

            # Print summary
            self.log("")
            self.log("=" * 80)
            self.log("FIX COMPLETED SUCCESSFULLY")
            self.log("=" * 80)
            self.log("")
            self.log("Summary:")
            self.log(f"  Accounts Receivable records updated: {self.stats['ar_records_updated']}")
            self.log(f"  AR_Days calculated: {self.stats['ar_days_calculated']}")
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
            self.log("  2. Verify AR_Days KPI card displays data")
            self.log("  3. Check that benchmarks show realistic values (typically 30-60 days)")

        except Exception as e:
            self.log("")
            self.log(f"ERROR: {str(e)}")
            self.stats['errors'].append(str(e))
            import traceback
            traceback.print_exc()
            raise


if __name__ == '__main__':
    fixer = ARDaysFixer()
    fixer.run()
