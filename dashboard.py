"""
Hospital KPI Scorecard - Interactive Dash Application

Features:
1. Interactive KPI cards with flip animation
2. Hospital and benchmark level selection
3. KPI ranking by importance (Impact × Ease of Change)
4. Trend visualizations (sparklines)
5. Benchmark comparison (National, State, Hospital Type, State+Type)
6. Color-coded performance indicators
7. Sortable and filterable KPI grid
8. Detailed table views with all data

Data Source: Parquet files (no database needed)
"""

import dash
from dash import dcc, html, Input, Output, State, callback, ALL, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.paths import (
    BALANCE_SHEET_OUTPUT,
    REVENUE_OUTPUT,
    REVENUE_EXPENSES_OUTPUT,
    COSTS_A000_OUTPUT,
    COSTS_B100_OUTPUT
)

# ============================================================================
# DATA ACCESS LAYER
# ============================================================================

class HospitalDataManager:
    """Manages data access for hospital KPIs and benchmarks from database"""

    def __init__(self, db_path='data/hospital_analytics.duckdb'):
        """Initialize with database connection"""
        self.db_path = db_path
        self.use_database = Path(db_path).exists()

        # Check if this is an optimized database (has pre-computed tables)
        if self.use_database:
            try:
                con = duckdb.connect(db_path, read_only=True)
                tables = con.execute("SHOW TABLES").df()['name'].tolist()
                self.use_precomputed = 'hospital_kpis' in tables and 'hospital_benchmarks' in tables
                con.close()

                if self.use_precomputed:
                    print(f"Using optimized database with pre-computed KPIs: {db_path}")
                else:
                    print(f"Using database: {db_path}")
            except Exception as e:
                print(f"Database file exists but cannot be opened (may be building): {e}")
                print("Falling back to parquet files")
                self.use_database = False
                self.use_precomputed = False
                self.balance_sheet_path = str(BALANCE_SHEET_OUTPUT / '**/*.parquet')
                self.revenue_path = str(REVENUE_OUTPUT / '**/*.parquet')
                self.revenue_expenses_path = str(REVENUE_EXPENSES_OUTPUT / '**/*.parquet')
        else:
            print(f"Database not found at {db_path}, falling back to parquet files")
            self.use_precomputed = False
            # Fallback to parquet paths (use centralized config)
            self.balance_sheet_path = str(BALANCE_SHEET_OUTPUT / '**/*.parquet')
            self.revenue_path = str(REVENUE_OUTPUT / '**/*.parquet')
            self.revenue_expenses_path = str(REVENUE_EXPENSES_OUTPUT / '**/*.parquet')

    def get_connection(self):
        """Get database connection"""
        if self.use_database:
            return duckdb.connect(self.db_path, read_only=True)
        else:
            return duckdb.connect(':memory:')

    def get_available_hospitals(self):
        """Get list of available hospitals with metadata"""
        try:
            con = self.get_connection()

            if self.use_database:
                hospitals = con.execute("""
                    SELECT DISTINCT
                        Provider_Number,
                        State_Code,
                        MAX(Fiscal_Year) as Latest_Year,
                        COUNT(DISTINCT Fiscal_Year) as Year_Count
                    FROM balance_sheet
                    WHERE Provider_Number IS NOT NULL
                    GROUP BY Provider_Number, State_Code
                    ORDER BY State_Code, Provider_Number
                """).df()
            else:
                hospitals = con.execute("""
                    SELECT DISTINCT
                        Provider_Number,
                        State_Code,
                        MAX(Fiscal_Year) as Latest_Year,
                        COUNT(DISTINCT Fiscal_Year) as Year_Count
                    FROM read_parquet(?, hive_partitioning=1)
                    WHERE Provider_Number IS NOT NULL
                    GROUP BY Provider_Number, State_Code
                    ORDER BY State_Code, Provider_Number
                """, [self.balance_sheet_path]).df()

            con.close()
            return hospitals
        except Exception as e:
            print(f"Error getting hospitals: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame(columns=['Provider_Number', 'State_Code', 'Latest_Year', 'Year_Count'])

    def classify_hospital_type(self, ccn):
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

    def calculate_kpis(self, ccn, fiscal_years=None):
        """
        Calculate all KPIs for a hospital across multiple years
        Returns DataFrame with KPI values and trends
        """
        # If we have pre-computed KPIs, use them (FAST!)
        if self.use_precomputed:
            con = self.get_connection()
            try:
                kpi_df = con.execute("""
                    SELECT * FROM hospital_kpis
                    WHERE Provider_Number = ?
                    ORDER BY Fiscal_Year DESC
                """, [int(ccn)]).df()
                con.close()
                return kpi_df
            except Exception as e:
                print(f"Error reading pre-computed KPIs: {e}")
                con.close()
                # Fall through to calculation below

        # Otherwise calculate from raw data
        con = duckdb.connect(':memory:') if not self.use_database else self.get_connection()

        # Get balance sheet data from parquet
        balance_query = """
            SELECT
                Fiscal_Year,
                SUM(CASE WHEN Acc_level2 = 'Assets' AND Acc_level3 LIKE '%Current%' THEN Value ELSE 0 END) as Current_Assets,
                SUM(CASE WHEN Acc_level2 = 'Assets' AND Acc_level3 LIKE '%Fixed%' THEN Value ELSE 0 END) as Fixed_Assets,
                SUM(CASE WHEN Acc_level2 = 'Assets' THEN Value ELSE 0 END) as Total_Assets,
                SUM(CASE WHEN Acc_level2 = 'Liabilities' AND Acc_level3 LIKE '%Current%' THEN Value ELSE 0 END) as Current_Liabilities,
                SUM(CASE WHEN Acc_level2 = 'Liabilities' THEN Value ELSE 0 END) as Total_Liabilities,
                SUM(CASE WHEN Acc_level1 = 'Fund Balances' OR Acc_level2 = 'Fund Balances' THEN Value ELSE 0 END) as Fund_Balance,
                SUM(CASE WHEN Line_Name LIKE '%Cash%' OR Line_Name LIKE '%Marketable%'
                    THEN Value ELSE 0 END) as Cash_And_Securities,
                SUM(CASE WHEN Line_Name LIKE '%receivable%' THEN Value ELSE 0 END) as Accounts_Receivable
            FROM read_parquet(?, hive_partitioning=1)
            WHERE Provider_Number = ?
            GROUP BY Fiscal_Year
            ORDER BY Fiscal_Year DESC
        """
        balance_df = con.execute(balance_query, [self.balance_sheet_path, int(ccn)]).df()

        # Get revenue data from parquet
        revenue_query = """
            SELECT
                Fiscal_Year,
                SUM(CASE WHEN REVENUE_CENTER = '%Inpatient%' THEN Value ELSE 0 END) as Inpatient_Revenue,
                SUM(CASE WHEN REVENUE_CENTER = '%Outpatient%' THEN Value ELSE 0 END) as Outpatient_Revenue,
                SUM(Value) as Total_Revenue
            FROM read_parquet(?, hive_partitioning=1)
            WHERE Provider_Number = ?
            GROUP BY Fiscal_Year
            ORDER BY Fiscal_Year DESC
        """
        revenue_df = con.execute(revenue_query, [self.revenue_path, int(ccn)]).df()

        # Get expense data from parquet
        expense_query = """
            SELECT
                Fiscal_Year,
                SUM(Value) as Total_Operating_Expenses
            FROM read_parquet(?, hive_partitioning=1)
            WHERE Provider_Number = ?
            GROUP BY Fiscal_Year
            ORDER BY Fiscal_Year DESC
        """
        expense_df = con.execute(expense_query, [self.revenue_expenses_path, int(ccn)]).df()

        con.close()

        # Merge all data
        kpi_df = balance_df.merge(revenue_df, on='Fiscal_Year', how='outer')
        kpi_df = kpi_df.merge(expense_df, on='Fiscal_Year', how='outer')

        # Sort by fiscal year in descending order (newest first)
        kpi_df = kpi_df.sort_values('Fiscal_Year', ascending=False).reset_index(drop=True)

        # Calculate KPIs
        kpi_df['Operating_Margin_Pct'] = np.where(
            kpi_df['Total_Revenue'] > 0,
            ((kpi_df['Total_Revenue'] - kpi_df['Total_Operating_Expenses']) / kpi_df['Total_Revenue']) * 100,
            None
        )

        kpi_df['Current_Ratio'] = np.where(
            kpi_df['Current_Liabilities'] > 0,
            kpi_df['Current_Assets'] / kpi_df['Current_Liabilities'],
            None
        )

        kpi_df['Days_Cash_On_Hand'] = np.where(
            kpi_df['Total_Operating_Expenses'] > 0,
            kpi_df['Cash_And_Securities'] / (kpi_df['Total_Operating_Expenses'] / 365),
            None
        )

        kpi_df['Outpatient_Revenue_Pct'] = np.where(
            kpi_df['Total_Revenue'] > 0,
            (kpi_df['Outpatient_Revenue'] / kpi_df['Total_Revenue']) * 100,
            None
        )

        kpi_df['Asset_Turnover_Ratio'] = np.where(
            kpi_df['Total_Assets'] > 0,
            kpi_df['Total_Revenue'] / kpi_df['Total_Assets'],
            None
        )

        kpi_df['Fixed_Asset_Turnover'] = np.where(
            kpi_df['Fixed_Assets'] > 0,
            kpi_df['Total_Revenue'] / kpi_df['Fixed_Assets'],
            None
        )

        kpi_df['AR_Days'] = np.where(
            kpi_df['Total_Revenue'] > 0,
            kpi_df['Accounts_Receivable'] / (kpi_df['Total_Revenue'] / 365),
            None
        )

        kpi_df['Debt_to_Equity_Ratio'] = np.where(
            kpi_df['Fund_Balance'] > 0,
            kpi_df['Total_Liabilities'] / kpi_df['Fund_Balance'],
            None
        )

        kpi_df['Equity_Ratio_Pct'] = np.where(
            kpi_df['Total_Assets'] > 0,
            (kpi_df['Fund_Balance'] / kpi_df['Total_Assets']) * 100,
            None
        )

        # Additional KPIs
        kpi_df['Net_Margin_Pct'] = kpi_df['Operating_Margin_Pct']

        kpi_df['Revenue_Growth_Pct'] = kpi_df['Total_Revenue'].pct_change(periods=-1) * 100

        kpi_df['Inpatient_Revenue_Pct'] = np.where(
            kpi_df['Total_Revenue'] > 0,
            (kpi_df['Inpatient_Revenue'] / kpi_df['Total_Revenue']) * 100,
            None
        )

        kpi_df['Operating_Expense_Ratio'] = np.where(
            kpi_df['Total_Revenue'] > 0,
            (kpi_df['Total_Operating_Expenses'] / kpi_df['Total_Revenue']) * 100,
            None
        )

        kpi_df['Working_Capital'] = (kpi_df['Current_Assets'] - kpi_df['Current_Liabilities']) / 1_000_000

        kpi_df['Debt_Ratio_Pct'] = np.where(
            kpi_df['Total_Assets'] > 0,
            (kpi_df['Total_Liabilities'] / kpi_df['Total_Assets']) * 100,
            None
        )

        kpi_df['Net_Income'] = kpi_df['Total_Revenue'] - kpi_df['Total_Operating_Expenses']
        kpi_df['Total_Margin_Pct'] = np.where(
            kpi_df['Total_Revenue'] > 0,
            (kpi_df['Net_Income'] / kpi_df['Total_Revenue']) * 100,
            None
        )

        kpi_df['Return_on_Assets_Pct'] = np.where(
            kpi_df['Total_Assets'] > 0,
            (kpi_df['Net_Income'] / kpi_df['Total_Assets']) * 100,
            None
        )

        kpi_df['Return_on_Equity_Pct'] = np.where(
            kpi_df['Fund_Balance'] > 0,
            (kpi_df['Net_Income'] / kpi_df['Fund_Balance']) * 100,
            None
        )

        return kpi_df

    def get_benchmarks(self, ccn, fiscal_year, benchmark_level='State_Hospital_Type'):
        """
        Get benchmark data for a hospital
        benchmark_level: 'National', 'State', 'Hospital_Type', 'State_Hospital_Type'
        """
        try:
            state_code = str(ccn)[:2]
            hospital_type = self.classify_hospital_type(ccn)

            # If we have pre-computed benchmarks, use them (FAST!)
            if self.use_precomputed:
                con = self.get_connection()
                try:
                    # Build filter for benchmark level using parameterized queries
                    if benchmark_level == 'National':
                        filter_sql = "Benchmark_Level = 'National'"
                        group_name = 'National'
                        params = [int(fiscal_year)]
                    elif benchmark_level == 'State':
                        filter_sql = "Benchmark_Level = 'State' AND State_Code = ?"
                        group_name = f'State {state_code}'
                        params = [state_code, int(fiscal_year)]
                    elif benchmark_level == 'Hospital_Type':
                        filter_sql = "Benchmark_Level = 'Hospital_Type' AND Hospital_Type = ?"
                        group_name = hospital_type
                        params = [hospital_type, int(fiscal_year)]
                    else:  # State_Hospital_Type
                        filter_sql = "Benchmark_Level = 'State_Hospital_Type' AND State_Code = ? AND Hospital_Type = ?"
                        group_name = f'{state_code} - {hospital_type}'
                        params = [state_code, hospital_type, int(fiscal_year)]

                    # Get benchmarks from pre-computed table
                    benchmarks_df = con.execute(f"""
                        SELECT
                            KPI_Name,
                            Provider_Count,
                            P25, Median, P75, Mean
                        FROM hospital_benchmarks
                        WHERE {filter_sql} AND Fiscal_Year = ?
                    """, params).df()

                    con.close()

                    if len(benchmarks_df) == 0:
                        return {'group_name': group_name, 'provider_count': 0, 'kpis': {}}

                    # Convert to expected format
                    kpis = {}
                    for _, row in benchmarks_df.iterrows():
                        kpis[row['KPI_Name']] = {
                            'P25': row['P25'],
                            'Median': row['Median'],
                            'P75': row['P75'],
                            'Mean': row['Mean']
                        }

                    provider_count = benchmarks_df['Provider_Count'].iloc[0] if len(benchmarks_df) > 0 else 0

                    return {
                        'group_name': group_name,
                        'provider_count': provider_count,
                        'kpis': kpis
                    }

                except Exception as e:
                    print(f"Error reading pre-computed benchmarks: {e}")
                    con.close()
                    # Fall through to calculation below

            # Otherwise calculate from raw data
            con = duckdb.connect(':memory:') if not self.use_database else self.get_connection()

            # Build filter based on benchmark level using parameterized queries
            if benchmark_level == 'National':
                filter_sql = "1=1"
                group_name = 'National'
                query_params = [self.balance_sheet_path, int(fiscal_year)]
            elif benchmark_level == 'State':
                filter_sql = "State_Code = ?"
                group_name = f'State {state_code}'
                query_params = [self.balance_sheet_path, int(fiscal_year), state_code]
            elif benchmark_level == 'Hospital_Type':
                # Need to get all hospitals of this type
                filter_sql = "1=1"  # Will filter in Python
                group_name = hospital_type
                query_params = [self.balance_sheet_path, int(fiscal_year)]
            else:  # State_Hospital_Type
                filter_sql = "State_Code = ?"
                group_name = f'{state_code} - {hospital_type}'
                query_params = [self.balance_sheet_path, int(fiscal_year), state_code]

            # Get all hospitals for this benchmark group
            hospitals_query = f"""
                SELECT DISTINCT Provider_Number, State_Code
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Fiscal_Year = ? AND {filter_sql}
            """
            hospitals_df = con.execute(hospitals_query, query_params).df()

            # Filter by hospital type if needed
            if benchmark_level in ['Hospital_Type', 'State_Hospital_Type']:
                hospitals_df['Hospital_Type'] = hospitals_df['Provider_Number'].apply(
                    lambda x: self.classify_hospital_type(str(int(x)).zfill(6))
                )
                hospitals_df = hospitals_df[hospitals_df['Hospital_Type'] == hospital_type]

            provider_count = len(hospitals_df)

            if provider_count == 0:
                return {'group_name': group_name, 'provider_count': 0, 'kpis': {}}

            # Calculate KPIs for all hospitals in benchmark group
            # This is computationally intensive, so we'll calculate just for this year
            kpi_values = {
                'Operating_Margin_Pct': [],
                'Current_Ratio': [],
                'Days_Cash_On_Hand': [],
                'Outpatient_Revenue_Pct': [],
                'Asset_Turnover_Ratio': [],
                'AR_Days': [],
                'Debt_to_Equity_Ratio': [],
                'Equity_Ratio_Pct': []
            }

            # Calculate KPIs for a sample of hospitals (to avoid long computation)
            sample_size = min(100, len(hospitals_df))
            for _, row in hospitals_df.head(sample_size).iterrows():
                hosp_ccn = str(int(row['Provider_Number'])).zfill(6)
                hosp_kpis = self.calculate_kpis(hosp_ccn)
                year_data = hosp_kpis[hosp_kpis['Fiscal_Year'] == fiscal_year]

                if not year_data.empty:
                    year_data = year_data.iloc[0]
                    for kpi_key in kpi_values.keys():
                        val = year_data.get(kpi_key)
                        if pd.notna(val):
                            kpi_values[kpi_key].append(val)

            con.close()

            # Calculate benchmarks (P25, Median, P75, Mean)
            kpis = {}
            for kpi_key, values in kpi_values.items():
                if len(values) > 0:
                    kpis[kpi_key] = {
                        'P25': np.percentile(values, 25),
                        'Median': np.percentile(values, 50),
                        'P75': np.percentile(values, 75),
                        'Mean': np.mean(values)
                    }
                else:
                    kpis[kpi_key] = {
                        'P25': None,
                        'Median': None,
                        'P75': None,
                        'Mean': None
                    }

            return {
                'group_name': group_name,
                'provider_count': provider_count,
                'kpis': kpis
            }

        except Exception as e:
            print(f"Error getting benchmarks: {e}")
            import traceback
            traceback.print_exc()
            return {
                'group_name': group_name if 'group_name' in locals() else 'Unknown',
                'provider_count': 0,
                'kpis': {}
            }


# ============================================================================
# VALUATION FUNCTIONS
# ============================================================================

def load_valuation_income_statement(ccn, fiscal_year):
    """Load income statement data for valuation analysis"""
    con = data_manager.get_connection()
    try:
        query = """
        SELECT
            Line_Name,
            Section,
            Subsection,
            Value
        FROM income_statement_long
        WHERE Provider_Number = ?
            AND Fiscal_Year = ?
        ORDER BY Line
        """
        df = con.execute(query, [int(ccn), int(fiscal_year)]).df()
        con.close()
        return df
    except Exception as e:
        print(f"Error loading income statement for valuation: {e}")
        con.close()
        return pd.DataFrame()

def load_valuation_expense_detail(ccn, fiscal_year):
    """Load detailed expense breakdown for valuation analysis"""
    con = data_manager.get_connection()
    try:
        query = """
        SELECT
            Expense_Category,
            Category_Description,
            Category_Type,
            Column_Description,
            SUM(Value) as Total_Expense
        FROM expense_detail
        WHERE Provider_Number = ?
            AND Fiscal_Year = ?
            AND Column_Description = 'Final_Adjusted'
        GROUP BY Expense_Category, Category_Description, Category_Type, Column_Description
        ORDER BY Total_Expense DESC
        """
        df = con.execute(query, [int(ccn), int(fiscal_year)]).df()
        con.close()
        return df
    except Exception as e:
        print(f"Error loading expense detail for valuation: {e}")
        con.close()
        return pd.DataFrame()


# ============================================================================
# KPI METADATA & RANKING
# ============================================================================

KPI_METADATA = {
    # PROFITABILITY (3 KPIs)
    'Operating_Margin_Pct': {
        'name': 'Operating Margin',
        'category': 'Profitability',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (3, 5),
        'impact_score': 10,
        'ease_of_change': 5,
        'description': 'Core operational profitability. Critical for financial sustainability.',
        'improvement_levers': ['Increase revenue', 'Reduce operating expenses', 'Optimize payer mix']
    },
    'Net_Margin_Pct': {
        'name': 'Net Margin',
        'category': 'Profitability',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (2, 4),
        'impact_score': 10,
        'ease_of_change': 4,
        'description': 'Overall profitability after all expenses.',
        'improvement_levers': ['Improve operating margin', 'Optimize capital structure', 'Reduce interest expense']
    },

    # LIQUIDITY (2 KPIs)
    'Current_Ratio': {
        'name': 'Current Ratio',
        'category': 'Liquidity',
        'unit': 'x',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (1.5, 2.0),
        'impact_score': 8,
        'ease_of_change': 6,
        'description': 'Short-term financial health. Ability to meet current obligations.',
        'improvement_levers': ['Improve collections', 'Manage payables', 'Reduce inventory']
    },
    'Days_Cash_On_Hand': {
        'name': 'Days Cash on Hand',
        'category': 'Liquidity',
        'unit': 'days',
        'format': '.0f',
        'higher_is_better': True,
        'target_range': (60, 150),
        'impact_score': 9,
        'ease_of_change': 4,
        'description': 'Financial cushion. Number of days hospital can operate without revenue.',
        'improvement_levers': ['Build reserves', 'Improve cash collections', 'Reduce cash outflows']
    },

    # REVENUE PERFORMANCE (3 KPIs)
    'Revenue_Growth_Pct': {
        'name': 'Revenue Growth',
        'category': 'Revenue Performance',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (3, 7),
        'impact_score': 8,
        'ease_of_change': 4,
        'description': 'Year-over-year revenue growth rate.',
        'improvement_levers': ['Increase volume', 'Improve payer mix', 'Add service lines']
    },
    'Outpatient_Revenue_Pct': {
        'name': 'Outpatient Revenue %',
        'category': 'Revenue Mix',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (40, 60),
        'impact_score': 7,
        'ease_of_change': 3,
        'description': 'Shift to outpatient care. Growing trend in healthcare delivery.',
        'improvement_levers': ['Expand outpatient services', 'Build ambulatory centers', 'Shift procedures']
    },
    'Inpatient_Revenue_Pct': {
        'name': 'Inpatient Revenue %',
        'category': 'Revenue Mix',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (40, 60),
        'impact_score': 6,
        'ease_of_change': 3,
        'description': 'Traditional inpatient revenue share. Declining trend in industry.',
        'improvement_levers': ['Optimize case mix', 'Improve ALOS', 'Focus on complex cases']
    },

    # COST MANAGEMENT (1 KPI)
    'Operating_Expense_Ratio': {
        'name': 'Operating Expense Ratio',
        'category': 'Cost Management',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (85, 95),
        'impact_score': 9,
        'ease_of_change': 5,
        'description': 'Operating expenses as % of revenue. Lower is better.',
        'improvement_levers': ['Reduce labor costs', 'Optimize supply chain', 'Improve efficiency']
    },

    # ASSET MANAGEMENT (4 KPIs)
    'Asset_Turnover_Ratio': {
        'name': 'Asset Turnover',
        'category': 'Efficiency',
        'unit': 'x',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (0.8, 1.2),
        'impact_score': 6,
        'ease_of_change': 5,
        'description': 'Asset utilization efficiency. Revenue generated per dollar of assets.',
        'improvement_levers': ['Increase utilization', 'Divest underperforming assets', 'Grow revenue']
    },
    'Fixed_Asset_Turnover': {
        'name': 'Fixed Asset Turnover',
        'category': 'Efficiency',
        'unit': 'x',
        'format': '.2f',
        'higher_is_better': True,
        'target_range': (1.0, 2.0),
        'impact_score': 5,
        'ease_of_change': 4,
        'description': 'Revenue generated per dollar of fixed assets (PP&E).',
        'improvement_levers': ['Increase bed utilization', 'Extend equipment hours', 'Grow revenue']
    },
    'AR_Days': {
        'name': 'AR Days',
        'category': 'Revenue Cycle',
        'unit': 'days',
        'format': '.0f',
        'higher_is_better': False,
        'target_range': (40, 50),
        'impact_score': 8,
        'ease_of_change': 7,
        'description': 'Revenue cycle efficiency. How quickly hospital collects payment.',
        'improvement_levers': ['Improve billing processes', 'Reduce denials', 'Accelerate collections']
    },
    'Working_Capital': {
        'name': 'Working Capital',
        'category': 'Liquidity',
        'unit': '$M',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (0, 100),
        'impact_score': 7,
        'ease_of_change': 5,
        'description': 'Current Assets - Current Liabilities. Operational buffer.',
        'improvement_levers': ['Improve collections', 'Manage inventory', 'Optimize payables']
    },

    # CAPITAL STRUCTURE (3 KPIs)
    'Debt_to_Equity_Ratio': {
        'name': 'Debt-to-Equity',
        'category': 'Leverage',
        'unit': 'x',
        'format': '.2f',
        'higher_is_better': False,
        'target_range': (0.8, 1.5),
        'impact_score': 7,
        'ease_of_change': 2,
        'description': 'Financial leverage. Balance between debt and equity financing.',
        'improvement_levers': ['Pay down debt', 'Build equity', 'Refinance high-cost debt']
    },
    'Equity_Ratio_Pct': {
        'name': 'Equity Ratio',
        'category': 'Capital Structure',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (30, 50),
        'impact_score': 6,
        'ease_of_change': 3,
        'description': 'Financial independence. Proportion of assets financed by equity.',
        'improvement_levers': ['Build reserves', 'Generate positive margins', 'Retain earnings']
    },
    'Debt_Ratio_Pct': {
        'name': 'Debt Ratio',
        'category': 'Leverage',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': False,
        'target_range': (40, 60),
        'impact_score': 6,
        'ease_of_change': 2,
        'description': 'Total debt as % of total assets.',
        'improvement_levers': ['Reduce debt', 'Increase assets', 'Improve profitability']
    },

    # ADDITIONAL FINANCIAL METRICS
    'Total_Margin_Pct': {
        'name': 'Total Margin',
        'category': 'Profitability',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (3, 6),
        'impact_score': 9,
        'ease_of_change': 4,
        'description': 'Net income including non-operating revenue as % of total revenue.',
        'improvement_levers': ['Improve operations', 'Optimize investments', 'Manage non-operating income']
    },
    'Return_on_Assets_Pct': {
        'name': 'Return on Assets (ROA)',
        'category': 'Profitability',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (2, 5),
        'impact_score': 7,
        'ease_of_change': 4,
        'description': 'Net income as % of total assets. Overall asset efficiency.',
        'improvement_levers': ['Improve margins', 'Optimize asset base', 'Increase revenue']
    },
    'Return_on_Equity_Pct': {
        'name': 'Return on Equity (ROE)',
        'category': 'Profitability',
        'unit': '%',
        'format': '.1f',
        'higher_is_better': True,
        'target_range': (5, 10),
        'impact_score': 7,
        'ease_of_change': 4,
        'description': 'Net income as % of equity. Return to stakeholders.',
        'improvement_levers': ['Improve profitability', 'Optimize capital structure', 'Grow efficiently']
    },
}

def calculate_importance_score(kpi_key):
    """Calculate BASE importance score = Impact × Ease of Change"""
    meta = KPI_METADATA.get(kpi_key, {})
    impact = meta.get('impact_score', 5)
    ease = meta.get('ease_of_change', 5)
    return impact * ease

def calculate_dynamic_priority(kpi_key, hospital_value, benchmark_median, higher_is_better=True):
    """
    Calculate DYNAMIC priority for this hospital based on:
    1. Base importance (impact × ease)
    2. Performance gap from benchmark
    3. Direction matters (worse performance = higher priority)

    Returns: priority score (0-1000)
    """
    base_importance = calculate_importance_score(kpi_key)

    if pd.isna(hospital_value) or pd.isna(benchmark_median) or benchmark_median == 0:
        return base_importance

    # Calculate gap percentage
    gap_pct = abs((hospital_value - benchmark_median) / benchmark_median) * 100

    # Determine if hospital is underperforming
    if higher_is_better:
        underperforming = hospital_value < benchmark_median
    else:
        underperforming = hospital_value > benchmark_median

    # Priority multiplier based on performance
    if underperforming:
        gap_multiplier = 1 + min(gap_pct / 100, 0.5)
    else:
        gap_multiplier = 0.5

    priority = base_importance * gap_multiplier
    return priority


# ============================================================================
# PROFESSIONAL TABLE STYLING HELPER
# ============================================================================

def get_professional_datatable_style():
    """
    Returns professional styling for DataTable components
    Inspired by financial presentation tables
    """
    return {
        'style_table': {
            'overflowX': 'auto',
            'borderRadius': '8px',
            'overflow': 'hidden',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'
        },
        'style_cell': {
            'textAlign': 'left',
            'padding': '12px 14px',
            'fontSize': '0.9rem',
            'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            'border': '1px solid #e8e8e8',
            'whiteSpace': 'normal',
            'height': 'auto',
            'minHeight': '44px'
        },
        'style_cell_conditional': [
            {
                'if': {'column_type': 'numeric'},
                'textAlign': 'right',
                'fontFamily': 'Monaco, Consolas, "Courier New", monospace',
                'fontWeight': '500'
            },
            {
                'if': {'column_id': 'Line'},
                'width': '80px',
                'textAlign': 'center',
                'fontWeight': '600',
                'color': '#5a6c7d'
            }
        ],
        'style_header': {
            'backgroundColor': '#34495e',
            'color': 'white',
            'fontWeight': '600',
            'fontSize': '0.95rem',
            'padding': '14px',
            'textAlign': 'center',
            'border': 'none',
            'textTransform': 'none'
        },
        'style_data': {
            'border': '1px solid #e8e8e8',
            'color': '#2c3e50'
        },
        'style_data_conditional': [
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'row_index': 'even'},
                'backgroundColor': 'white'
            },
            {
                'if': {'state': 'selected'},
                'backgroundColor': '#e8f4f8',
                'border': '1px solid #3498db'
            }
        ]
    }


# ============================================================================
# DASH APP
# ============================================================================

# Initialize app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True
)
app.config.suppress_callback_exceptions = True

# Initialize data manager
data_manager = HospitalDataManager()

# Get available hospitals dynamically
def get_hospital_options():
    """Get list of hospitals from parquet files for dropdown"""
    try:
        hospitals_df = data_manager.get_available_hospitals()
        print(f"Found {len(hospitals_df)} hospitals in parquet files")

        if hospitals_df.empty:
            print("No hospitals found, using default")
            return [{'label': '010001 - Default Hospital, State 01', 'value': '010001'}]

        options = []
        for _, row in hospitals_df.iterrows():
            provider_num = row['Provider_Number']
            ccn = str(int(provider_num)).zfill(6)
            state = str(int(row['State_Code'])).zfill(2)
            hosp_type = data_manager.classify_hospital_type(ccn)
            year_count = row.get('Year_Count', 'N/A')
            label = f"{ccn} - {hosp_type}, State {state} ({year_count} years)"
            options.append({'label': label, 'value': ccn})

        print(f"Loaded {len(options)} hospitals total")
        return options
    except Exception as e:
        print(f"Error loading hospitals: {e}")
        import traceback
        traceback.print_exc()
        return [{'label': '010001 - Default Hospital, State 01', 'value': '010001'}]

print("Loading hospitals from parquet files...")
hospital_options = get_hospital_options()
print(f"Hospital options ready: {len(hospital_options)} hospitals")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_percentile_rank(value, p25, median, p75):
    """Determine which quartile the value falls into"""
    if pd.isna(value) or p25 is None or median is None or p75 is None:
        return None, 'secondary'

    if value <= p25:
        return 'Bottom Quartile', 'danger'
    elif value <= median:
        return 'Below Median', 'warning'
    elif value <= p75:
        return 'Above Median', 'info'
    else:
        return 'Top Quartile', 'success'


def create_sparkline(values, fiscal_years):
    """Create a mini sparkline chart for trend"""
    if len(values) < 2:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(fiscal_years),
        y=list(values),
        mode='lines',
        line=dict(color='#2C3E50', width=2),
        fill='tozeroy',
        fillcolor='rgba(44, 62, 80, 0.1)'
    ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=50,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode=False
    )

    return fig


def calculate_trend(values):
    """Calculate trend direction and magnitude"""
    if len(values) < 2:
        return 'stable', 0

    recent = values[0]
    older = values[1]

    if pd.isna(recent) or pd.isna(older) or older == 0:
        return 'stable', 0

    change_pct = ((recent - older) / abs(older)) * 100

    if abs(change_pct) < 2:
        return 'stable', change_pct
    elif change_pct > 0:
        return 'up', change_pct
    else:
        return 'down', change_pct


# ============================================================================
# KPI CARD COMPONENT
# ============================================================================

def create_kpi_card(kpi_key, kpi_value, kpi_trend_values, fiscal_years,
                    benchmark_data, rank, importance_score):
    """
    Create an interactive KPI card

    Front: Shows KPI value, trend, benchmark comparison
    """
    meta = KPI_METADATA.get(kpi_key, {})
    kpi_name = meta.get('name', kpi_key)
    category = meta.get('category', 'General')
    unit = meta.get('unit', '')
    fmt = meta.get('format', '.1f')
    higher_is_better = meta.get('higher_is_better', True)

    # Get benchmark comparison
    benchmark_kpis = benchmark_data.get('kpis', {})
    kpi_benchmark = benchmark_kpis.get(kpi_key, {})
    p25 = kpi_benchmark.get('P25')
    median = kpi_benchmark.get('Median')
    p75 = kpi_benchmark.get('P75')
    mean = kpi_benchmark.get('Mean')

    # Calculate performance vs benchmark
    perf_label, perf_color = calculate_percentile_rank(kpi_value, p25, median, p75)

    # Calculate trend
    trend_direction, trend_pct = calculate_trend(kpi_trend_values)

    # Trend icon
    trend_icons = {
        'up': '↑',
        'down': '↓',
        'stable': '→'
    }
    trend_colors = {
        'up': 'success' if higher_is_better else 'danger',
        'down': 'danger' if higher_is_better else 'success',
        'stable': 'secondary'
    }

    # Create sparkline
    sparkline_fig = create_sparkline(kpi_trend_values, fiscal_years)

    # Card content
    card = dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H6(kpi_name, className="mb-0"),
                    html.Small(category, className="text-muted")
                ], width=8),
                dbc.Col([
                    dbc.Badge(f"#{rank}", color="primary", className="float-end")
                ], width=4)
            ])
        ]),
        dbc.CardBody([
            # Main KPI Value
            html.Div([
                html.H2(
                    f"{kpi_value:{fmt}}{unit}" if not pd.isna(kpi_value) else "N/A",
                    className="mb-2"
                ),
                dbc.Badge(
                    f"{trend_icons[trend_direction]} {abs(trend_pct):.1f}%",
                    color=trend_colors[trend_direction],
                    className="me-2"
                ),
            ]),

            # Sparkline
            html.Div([
                dcc.Graph(
                    figure=sparkline_fig,
                    config={'displayModeBar': False},
                    style={'height': '50px'}
                )
            ], className="mt-2 mb-3"),

            # Benchmark Comparison
            html.Div([
                html.Hr(),
                html.Small("Benchmark Comparison", className="text-muted d-block mb-2"),
                html.Div([
                    html.Strong(f"Mean: {format(mean, fmt)}{unit}" if mean else "Mean: N/A",
                               className="text-primary me-3"),
                    dbc.Badge(perf_label if perf_label else "N/A", color=perf_color, className="me-2")
                ], className="mb-2"),
                dbc.Progress([
                    dbc.Progress(value=25, color="danger", bar=True),
                    dbc.Progress(value=25, color="warning", bar=True),
                    dbc.Progress(value=25, color="info", bar=True),
                    dbc.Progress(value=25, color="success", bar=True),
                ], className="mb-2", style={'height': '8px'}),
                dbc.Row([
                    dbc.Col(html.Small(f"P25: {format(p25, fmt)}{unit}" if p25 else "N/A"), width=4),
                    dbc.Col(html.Small(f"Median: {format(median, fmt)}{unit}" if median else "N/A"), width=4),
                    dbc.Col(html.Small(f"P75: {format(p75, fmt)}{unit}" if p75 else "N/A"), width=4)
                ])
            ]),

            # Importance Score
            html.Hr(),
            html.Div([
                html.Small(f"Importance Score: {importance_score:.0f}/100", className="text-muted"),
                dbc.Progress(value=importance_score, max=100, className="mt-1",
                           color="primary", style={'height': '4px'})
            ]),

            # View Data Button
            html.Hr(),
            dbc.Button(
                [html.I(className="fas fa-table me-2"), "View Data"],
                id={'type': 'view-data-btn', 'index': kpi_key},
                color="outline-primary",
                size="sm",
                className="w-100"
            )
        ])
    ], className="shadow-sm mb-3", style={'height': '100%'})

    return card


# ============================================================================
# APP LAYOUT
# ============================================================================

# Helper function to format currency
def format_currency(value):
    """Format value in millions with 2 decimals (no currency symbols)"""
    if pd.isna(value) or value == 0:
        return "0.00"
    # Convert to millions with 2 decimal places
    value_in_millions = value / 1e6
    return f"{value_in_millions:.2f}"

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-hospital me-3"),
                "Hospital Financial Analytics Dashboard"
            ], className="mt-4 mb-2"),
            html.P(
                "Interactive performance dashboard with KPIs, benchmarks, and detailed financial statements",
                className="lead text-muted mb-4"
            )
        ])
    ]),

    # Hospital Selection (shared across tabs)
    dbc.Row([
        dbc.Col([
            html.Label("Hospital Selection"),
            dcc.Dropdown(
                id='hospital-dropdown',
                options=hospital_options,
                value=hospital_options[0]['value'] if hospital_options else '010001',
                clearable=False
            )
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H6("Hospital", className="text-muted mb-1"),
                        html.H5(id='header-hospital-name', className="mb-0")
                    ], className="d-inline-block me-4"),
                    html.Div([
                        html.H6("Type", className="text-muted mb-1"),
                        html.H5(id='header-hospital-type', className="mb-0")
                    ], className="d-inline-block")
                ], className="d-flex justify-content-around")
            ], className="shadow-sm")
        ], width=6)
    ], className="mb-4"),

    # Tabs
    dbc.Tabs(id="main-tabs", active_tab="tab-kpi", children=[
        # KPI Dashboard Tab
        dbc.Tab(label="KPI Dashboard", tab_id="tab-kpi", children=[
            html.Div([
                # Benchmark Level Control
                dbc.Row([
                    dbc.Col([
                        html.Label("Benchmark Level", className="mt-3"),
                        dcc.Dropdown(
                            id='benchmark-dropdown',
                            options=[
                                {'label': 'National - All Hospitals', 'value': 'National'},
                                {'label': 'State - Same State', 'value': 'State'},
                                {'label': 'Hospital Type - Same Type', 'value': 'Hospital_Type'},
                                {'label': 'State + Type - Most Specific', 'value': 'State_Hospital_Type'}
                            ],
                            value='State',
                            clearable=False
                        )
                    ], width=6)
                ], className="mb-4"),

                # Summary Stats
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Hospital", className="text-muted mb-1"),
                                html.H4(id='hospital-name', className="mb-0")
                            ])
                        ], className="shadow-sm")
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Type", className="text-muted mb-1"),
                                html.H4(id='hospital-type', className="mb-0")
                            ])
                        ], className="shadow-sm")
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Benchmark Group", className="text-muted mb-1"),
                                html.H4(id='benchmark-group', className="mb-0")
                            ])
                        ], className="shadow-sm")
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Peer Hospitals", className="text-muted mb-1"),
                                html.H4(id='peer-count', className="mb-0")
                            ])
                        ], className="shadow-sm")
                    ], width=3)
                ], className="mb-4"),

                # Sorting Controls
                dbc.Row([
                    dbc.Col([
                        html.Label("Sort KPIs by:", className="me-2"),
                        dbc.ButtonGroup([
                            dbc.Button("Priority (Dynamic)", id='sort-importance', color="primary", outline=False),
                            dbc.Button("Performance Gap", id='sort-performance', color="primary", outline=True),
                            dbc.Button("Trend Change", id='sort-trend', color="primary", outline=True),
                        ])
                    ], className="d-flex align-items-center")
                ], className="mb-3"),

                # KPI Cards Grid
                html.Div(id='kpi-cards-container'),
            ], className="mt-3")
        ]),

        # Financials Tab
        dbc.Tab(label="Financials", tab_id="tab-financials", children=[
            html.Div([
                html.H5("Multi-Year Financial Statements", className="mt-3 mb-3 text-primary"),
                html.P("All available fiscal years shown as columns (most recent on right)", className="text-muted mb-4"),

                # Financial Statements Sub-Tabs (lazy loading)
                dbc.Tabs(id="financial-subtabs", active_tab="subtab-balance-sheet", children=[
                    # Balance Sheet Sub-Tab
                    dbc.Tab(label="Balance Sheet", tab_id="subtab-balance-sheet", children=[
                        html.Div([
                            # Fund Type Filter
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Fund Type", className="fw-bold mb-2"),
                                    dcc.Dropdown(
                                        id='fund-type-dropdown',
                                        options=[
                                            {'label': 'General Fund', 'value': 'General Fund'},
                                            {'label': 'Specific Purpose Fund', 'value': 'Specific Purpose Fund'},
                                            {'label': 'Combined Total', 'value': 'Combined Total'},
                                            {'label': 'Medicaid Fund', 'value': 'Medicaid Fund'}
                                        ],
                                        value='General Fund',
                                        clearable=False
                                    )
                                ], width=4)
                            ], className="mt-3 mb-3"),
                            # Balance Sheet Content
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='balance-sheet-content')
                                ])
                            ])
                        ])
                    ]),

                    # Revenue Sub-Tab
                    dbc.Tab(label="Revenue Detail", tab_id="subtab-revenue", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='revenue-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Revenue & Expenses Sub-Tab
                    dbc.Tab(label="Revenue & Expenses", tab_id="subtab-revenue-expenses", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='revenue-expenses-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Cost Summary Sub-Tab (NEW - from B100)
                    dbc.Tab(label="Cost Summary", tab_id="subtab-cost-summary", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='cost-summary-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Detailed Costs Sub-Tab (Schedule A - Basic Table)
                    dbc.Tab(label="WORKSHEET A", tab_id="subtab-detailed-costs", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='detailed-costs-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='detailed-costs-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Worksheet B Sub-Tab (Schedule B-1 - Overhead Costs)
                    dbc.Tab(label="WORKSHEET B", tab_id="subtab-worksheet-b", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='worksheet-b-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='worksheet-b-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Worksheet G Sub-Tab (Balance Sheet)
                    dbc.Tab(label="WORKSHEET G", tab_id="subtab-worksheet-g", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='worksheet-g-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='worksheet-g-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Worksheet G-1 Sub-Tab (Fund Balance Changes)
                    dbc.Tab(label="WORKSHEET G-1", tab_id="subtab-worksheet-g1", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='worksheet-g1-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='worksheet-g1-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Worksheet G-2 Sub-Tab (Revenue)
                    dbc.Tab(label="WORKSHEET G-2", tab_id="subtab-worksheet-g2", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='worksheet-g2-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='worksheet-g2-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Worksheet G-3 Sub-Tab (Revenue & Expenses)
                    dbc.Tab(label="WORKSHEET G-3", tab_id="subtab-worksheet-g3", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='worksheet-g3-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='worksheet-g3-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Fund Balance Changes Sub-Tab
                    dbc.Tab(label="Fund Balance Changes", tab_id="subtab-fund-balance-changes", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='fund-balance-changes-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),
                ])
            ], className="mt-3")
        ]),

        # CMS Worksheets Tab
        dbc.Tab(label="CMS Worksheets", tab_id="tab-cms-worksheets", children=[
            html.Div([
                # Hospital and Year selection for CMS Worksheets
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Hospital (CMS Data):", className="fw-bold"),
                        dcc.Dropdown(
                            id='cms-hospital-dropdown',
                            placeholder="Select a hospital",
                            className="mb-3"
                        )
                    ], width=6),
                    dbc.Col([
                        html.Label("Select Fiscal Year:", className="fw-bold"),
                        dcc.Dropdown(
                            id='cms-year-dropdown',
                            placeholder="Select fiscal year",
                            className="mb-3"
                        )
                    ], width=3)
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        dbc.Tabs(id="cms-worksheet-tabs", active_tab="cms-tab-a000000", children=[
                            dbc.Tab(label="A000000 - General Service Cost Centers", tab_id="cms-tab-a000000"),
                            dbc.Tab(label="A6000A0 - Reclassifications", tab_id="cms-tab-a6000a0"),
                            dbc.Tab(label="A700001 - Reconciliation of Capital Costs Centers", tab_id="cms-tab-a700001"),
                            dbc.Tab(label="A700002 - Reconciliation of Capital Costs Centers", tab_id="cms-tab-a700002"),
                            dbc.Tab(label="A700003 - Reconciliation of Capital Costs Centers", tab_id="cms-tab-a700003"),
                            dbc.Tab(label="A800000 - Adjustments to Expenses", tab_id="cms-tab-a800000"),
                            dbc.Tab(label="A810000 - Costs Incurred - Related Organizations", tab_id="cms-tab-a810000"),
                            dbc.Tab(label="A820010 - Provider-Based Physicians Adjustments", tab_id="cms-tab-a820010"),
                            dbc.Tab(label="B000001 - Cost Allocation - General Service Costs", tab_id="cms-tab-b000001"),
                            dbc.Tab(label="B000002 - Cost Allocation - General Service Costs", tab_id="cms-tab-b000002"),
                            dbc.Tab(label="B100000 - Cost Allocation - General Service Costs", tab_id="cms-tab-b100000"),
                            dbc.Tab(label="C000001 - Cost Allocation - General Service Costs", tab_id="cms-tab-c000001"),
                            dbc.Tab(label="G000000 - Balance Sheet", tab_id="cms-tab-g000000"),
                            dbc.Tab(label="G100000 - Statement of Changes in Fund Balances", tab_id="cms-tab-g100000"),
                            dbc.Tab(label="G200000 - Statement of Patient Revenues", tab_id="cms-tab-g200000"),
                            dbc.Tab(label="G300000 - Statement of Revenues", tab_id="cms-tab-g300000"),
                            dbc.Tab(label="S000001 - Settlement Summary", tab_id="cms-tab-s000001"),
                            dbc.Tab(label="S100001 - Hospital Uncompensated & Indigent Care Data", tab_id="cms-tab-s100001"),
                            dbc.Tab(label="S200001 - Hospital & Healthcare Complex ID Data", tab_id="cms-tab-s200001"),
                            dbc.Tab(label="S300001 - Statistical Data", tab_id="cms-tab-s300001"),
                            dbc.Tab(label="S300002 - Statistical Data", tab_id="cms-tab-s300002"),
                            dbc.Tab(label="S300004 - Hospital Wage Related Costs", tab_id="cms-tab-s300004"),
                            dbc.Tab(label="S300005 - Hospital Wage Related Costs", tab_id="cms-tab-s300005"),
                            dbc.Tab(label="S410000 - Hospital Wage Related Costs", tab_id="cms-tab-s410000"),
                            dbc.Tab(label="S500000 - Hospital Renal Dialysis Department", tab_id="cms-tab-s500000"),
                        ]),
                        html.Div(id='cms-worksheet-content', className="mt-4")
                    ])
                ])
            ], className="mt-3")
        ]),

        # Valuation Analysis Tab
        dbc.Tab(label="Valuation Analysis", tab_id="tab-valuation", children=[
            html.Div([
                html.H5("Interactive Hospital Valuation Dashboard", className="mt-3 mb-3 text-primary"),
                html.P("Analyze how changes in revenue, expenses, and margins affect hospital valuation", className="text-muted mb-4"),

                # Hospital and Year Selection for Valuation
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Fiscal Year:", className="fw-bold"),
                        dcc.Dropdown(
                            id='valuation-year-dropdown',
                            placeholder="Select fiscal year",
                            className="mb-3"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Button('Load Valuation Data', id='valuation-load-button', n_clicks=0,
                                    className="btn btn-primary mt-4")
                    ], width=3)
                ], className="mb-4"),

                # Store components for valuation data
                dcc.Store(id='valuation-income-data'),
                dcc.Store(id='valuation-expense-data'),
                dcc.Store(id='valuation-baseline-metrics'),

                # Valuation content area
                html.Div(id='valuation-content')
            ], className="mt-3")
        ])
    ]),

    # Modal for data table
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id='modal-title')),
        dbc.ModalBody(id='modal-body', style={'overflowX': 'auto'}),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
        ),
    ], id="data-modal", size="xl", is_open=False, scrollable=True),

    # Footer
    html.Hr(className="my-5"),
    html.Footer([
        html.P(id='footer-datasource', className="text-center text-muted")
    ])

], fluid=True, className="py-4")


# ============================================================================
# CALLBACKS
# ============================================================================

@app.callback(
    [Output('hospital-name', 'children'),
     Output('hospital-type', 'children'),
     Output('benchmark-group', 'children'),
     Output('peer-count', 'children'),
     Output('kpi-cards-container', 'children')],
    [Input('hospital-dropdown', 'value'),
     Input('benchmark-dropdown', 'value'),
     Input('sort-importance', 'n_clicks'),
     Input('sort-performance', 'n_clicks'),
     Input('sort-trend', 'n_clicks')]
)
def update_dashboard(ccn, benchmark_level, sort_imp, sort_perf, sort_trend):
    """Main callback to update entire dashboard"""

    # Get hospital metadata
    hospital_type = data_manager.classify_hospital_type(ccn)
    state_code = str(ccn)[:2]

    # Get KPI data
    kpi_data = data_manager.calculate_kpis(ccn)

    if kpi_data.empty:
        return "N/A", "N/A", "N/A", "N/A", html.Div("No data available")

    latest_year = kpi_data['Fiscal_Year'].max()

    # Get benchmarks (NOTE: This calculates on the fly from parquet files - may be slow)
    print(f"Calculating benchmarks for {ccn} at {benchmark_level} level...")
    benchmark_data = data_manager.get_benchmarks(ccn, latest_year, benchmark_level)
    print(f"Benchmarks calculated: {benchmark_data['provider_count']} peers")

    # Create KPI cards
    kpi_cards = []
    kpi_rankings = []

    for kpi_key in KPI_METADATA.keys():
        if kpi_key not in kpi_data.columns:
            continue

        # Get KPI metadata
        kpi_meta = KPI_METADATA.get(kpi_key, {})
        higher_is_better = kpi_meta.get('higher_is_better', True)

        # Get KPI values across years
        kpi_values = kpi_data[kpi_key].values
        kpi_value = kpi_values[0] if len(kpi_values) > 0 else None

        # Get benchmark
        benchmark_kpis = benchmark_data.get('kpis', {})
        kpi_benchmark = benchmark_kpis.get(kpi_key, {})
        median = kpi_benchmark.get('Median')

        # Calculate DYNAMIC priority
        dynamic_priority = calculate_dynamic_priority(kpi_key, kpi_value, median, higher_is_better)

        # Calculate performance gap
        if kpi_value and median:
            if higher_is_better:
                perf_gap = median - kpi_value
            else:
                perf_gap = kpi_value - median
        else:
            perf_gap = 0

        # Calculate trend
        trend_direction, trend_pct = calculate_trend(kpi_values)

        kpi_rankings.append({
            'kpi_key': kpi_key,
            'dynamic_priority': dynamic_priority,
            'importance': calculate_importance_score(kpi_key),
            'perf_gap': abs(perf_gap),
            'trend_pct': abs(trend_pct),
            'kpi_value': kpi_value,
            'kpi_values': kpi_values
        })

    # Determine sort order
    ctx = dash.callback_context
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'sort-performance':
            kpi_rankings.sort(key=lambda x: x['perf_gap'], reverse=True)
        elif button_id == 'sort-trend':
            kpi_rankings.sort(key=lambda x: x['trend_pct'], reverse=True)
        else:
            kpi_rankings.sort(key=lambda x: x['dynamic_priority'], reverse=True)
    else:
        kpi_rankings.sort(key=lambda x: x['dynamic_priority'], reverse=True)

    # Create cards in sorted order
    for idx, ranking in enumerate(kpi_rankings):
        card = create_kpi_card(
            kpi_key=ranking['kpi_key'],
            kpi_value=ranking['kpi_value'],
            kpi_trend_values=ranking['kpi_values'],
            fiscal_years=kpi_data['Fiscal_Year'].values,
            benchmark_data=benchmark_data,
            rank=idx + 1,
            importance_score=ranking['dynamic_priority']
        )
        kpi_cards.append(dbc.Col(card, width=12, lg=6, xl=4))

    # Layout cards in grid
    cards_grid = dbc.Row(kpi_cards)

    return (
        f"CCN {ccn}",
        hospital_type,
        benchmark_data.get('group_name', 'N/A'),
        f"{benchmark_data.get('provider_count', 0):,}",
        cards_grid
    )


# Modal callbacks
@app.callback(
    [Output("data-modal", "is_open"),
     Output("modal-title", "children"),
     Output("modal-body", "children")],
    [Input({'type': 'view-data-btn', 'index': ALL}, 'n_clicks'),
     Input("close-modal", "n_clicks")],
    [State("data-modal", "is_open"),
     State('hospital-dropdown', 'value')],
    prevent_initial_call=True
)
def toggle_modal(view_clicks, close_clicks, _is_open, ccn):
    """Handle modal open/close and populate with KPI data table"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update

    trigger_id = ctx.triggered[0]['prop_id']

    # If no actual click happened (just a re-render), don't update
    if not trigger_id or trigger_id == '.':
        return dash.no_update, dash.no_update, dash.no_update

    # Close modal
    if 'close-modal' in trigger_id:
        return False, "", ""

    # Open modal with KPI data - only if a button was actually clicked
    if 'view-data-btn' in trigger_id:
        # Check if this was an actual click (not None and > 0)
        if view_clicks and any(clicks for clicks in view_clicks if clicks and clicks > 0):
            # Extract KPI key from button ID
            import json
            button_id = json.loads(trigger_id.split('.')[0])
            kpi_key = button_id['index']

            # Get KPI data
            kpi_data = data_manager.calculate_kpis(ccn)

            if kpi_data.empty:
                return True, "No Data", html.Div("No data available for this hospital", className="alert alert-warning")

            # Get KPI metadata
            kpi_meta = KPI_METADATA.get(kpi_key, {})

            # Create table with all years
            table_data = kpi_data[['Fiscal_Year', kpi_key]].copy()
            table_data = table_data.sort_values('Fiscal_Year', ascending=True)

            # Format values
            fmt = kpi_meta.get('format', '.2f')
            unit = kpi_meta.get('unit', '')

            table_data['Formatted_Value'] = table_data[kpi_key].apply(
                lambda x: f"{x:{fmt}}{unit}" if pd.notna(x) else "N/A"
            )

            # Create table
            display_df = table_data[['Fiscal_Year', 'Formatted_Value']].rename(
                columns={'Fiscal_Year': 'Year', 'Formatted_Value': kpi_meta.get('name', kpi_key)}
            )

            table = dbc.Table.from_dataframe(
                display_df,
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                className="table-sm"
            )

            # Create modal title
            title = f"{kpi_meta.get('name', kpi_key)} - Historical Data"

            # Create body
            body = html.Div([
                html.P([
                    html.Strong("Description: "),
                    kpi_meta.get('description', 'No description available')
                ], className="text-muted mb-2"),
                html.P([
                    html.Strong("Target Range: "),
                    f"{kpi_meta.get('target_range', (0, 0))[0]}-{kpi_meta.get('target_range', (0, 0))[1]}{unit}"
                ], className="text-muted mb-3"),
                table
            ])

            return True, title, body
        else:
            # Button rendered but not clicked - don't update
            return dash.no_update, dash.no_update, dash.no_update

    return dash.no_update, dash.no_update, dash.no_update


# ============================================================================
# FINANCIALS TAB CALLBACKS
# ============================================================================

# Update header hospital info (shared across tabs)
@app.callback(
    [Output('header-hospital-name', 'children'),
     Output('header-hospital-type', 'children')],
    [Input('hospital-dropdown', 'value')]
)
def update_header_info(ccn):
    """Update hospital info in header"""
    hospital_type = data_manager.classify_hospital_type(ccn)
    return f"CCN {ccn}", hospital_type


# Update footer to show data source
@app.callback(
    Output('footer-datasource', 'children'),
    [Input('hospital-dropdown', 'value')]  # Trigger on load
)
def update_footer(_):
    """Show data source in footer"""
    if data_manager.use_database:
        return f"Data Source: DuckDB Database ({data_manager.db_path}) | With Indexes for Fast Queries"
    else:
        return "Data Source: CMS HCRIS Parquet Files | No database (slower)"


# Helper functions for name cleaning and detection
def clean_re_line_name(name):
    """Remove Rev&Exp prefix from revenue & expenses line names"""
    if pd.isna(name):
        return ''
    name = str(name).strip()
    # Split on first space and take the rest
    parts = name.split(maxsplit=1)
    if len(parts) > 1:
        return parts[1].strip()
    return name

def clean_cost_line_name(name):
    """Remove Cost prefix from cost line names"""
    if pd.isna(name):
        return ''
    name = str(name).strip()
    # Cost lines may have prefixes like "Cost "
    if name.startswith('Cost '):
        return name[5:].strip()
    return name

def is_subtotal_line(name):
    """Detect if a line is a subtotal/total line"""
    if pd.isna(name):
        return False
    name = str(name).lower().strip()
    subtotal_keywords = ['total', 'subtotal', 'net ', 'gross', 'sum of']
    return any(keyword in name for keyword in subtotal_keywords)

# Helper function to create professional multi-year financial table
def create_multiyear_financial_table(df, title, statement_type):
    """Create a professionally formatted financial statement table with all years as columns"""
    if df is None or df.empty:
        return html.Div("No data available", className="alert alert-info")

    # Get unique years and sort (oldest to newest, so newest is on right)
    years = sorted(df['Fiscal_Year'].unique())

    # Pivot data to get years as columns
    # First, create a unique key for each line item and clean detail names
    # Include Line number for proper ordering

    # Handle unknown categories with sequential naming
    unknown_counters = {'major': 0, 'sub': 0}

    def get_category_name(value, level):
        """Get category name, handling blanks with sequential numbers"""
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
        else:
            unknown_counters[level] += 1
            return f"Other {unknown_counters[level]}"

    if statement_type == 'balance_sheet':
        # Use Acc_name for clean names (no prefixes)
        df['major'] = df['Acc_level2'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = df['Acc_level3'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['Acc_name'].fillna('Unknown item')
        df['is_subtotal'] = df['Acc_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    elif statement_type == 'revenue':
        # Revenue hierarchy: Revenue_Center -> Revenue_Group -> Revenue_Subgroup -> Revenue_Subgroup_Detail
        df['major'] = df['Revenue_Center'].apply(lambda x: get_category_name(x, 'major') if pd.notna(x) and str(x).strip() else '')
        df['sub'] = df['Revenue_Group'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['sub2'] = df['Revenue_Subgroup'].apply(lambda x: get_category_name(x, 'sub2') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['Revenue_Subgroup_Detail'].fillna('Unknown item')
        df['is_subtotal'] = df['Revenue_Subgroup_Detail'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['sub2'] + '|' + df['Line'].astype(str)

    elif statement_type == 'revenue_expenses':
        # Revenue & Expenses: Sort by Line, indent by RE_Level (1 or 2)
        df['clean_name'] = df['RE_Line_Name'].apply(clean_re_line_name)
        df['level'] = df['RE_Level'].fillna(1).astype(int)  # Level 1 or 2
        df['detail'] = df['clean_name'].replace('', 'Unknown item')
        df['is_subtotal'] = df['clean_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        # Use line_num directly for sorting, level for grouping
        df['line_key'] = df['Line'].astype(str)

    elif statement_type == 'costs':
        # Clean Cost_Center_Name
        df['clean_name'] = df['Cost_Center_Name'].apply(clean_cost_line_name)
        df['major'] = df['Cost_Class'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = df['Cost_Allocation_Type'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['clean_name'].replace('', 'Unknown item')
        df['is_subtotal'] = df['clean_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    elif statement_type == 'cost-summary':
        # Cost Summary from B100 (lines 3000-20200, column 2600)
        df['major'] = df['Account_group'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = ''  # No subcategories for cost summary
        df['detail'] = df['Account_name'].fillna('Unknown item')
        df['is_subtotal'] = df['Account_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['Line'].astype(str)

    elif statement_type == 'fund_balance_changes':
        # Fund Balance Changes (similar structure to balance sheet)
        df['major'] = df['Acc_level1'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = df['Acc_level2'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['Acc_name'].fillna('Unknown item')
        df['is_subtotal'] = df['Acc_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    elif statement_type == 'detailed-costs':
        # Detailed Costs (Schedule A + B combined, unpivoted by cost component)
        # Structure: Account_name (cost center) → Cost_Component (subgroup) → Value
        df['major'] = df['Account_name'].fillna('Unknown Cost Center')
        df['sub'] = df['Cost_Component'].fillna('Unknown Component')
        df['detail'] = ''  # No detail level for unpivoted structure
        df['is_subtotal'] = df['Account_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    else:
        return html.Div("Unknown statement type", className="alert alert-warning")

    # Pivot: one row per line_key, columns for each year
    # Include line_num and is_subtotal in index for sorting
    # Dynamically build index columns based on statement type
    index_cols = ['line_key']

    if 'major' in df.columns:
        # For balance_sheet, revenue, costs (hierarchical structure)
        index_cols.extend(['major', 'sub'])
        if 'sub2' in df.columns:
            index_cols.append('sub2')
        if 'sub3' in df.columns:
            index_cols.append('sub3')
    elif 'level' in df.columns:
        # For revenue_expenses (flat structure with level)
        index_cols.append('level')

    index_cols.extend(['detail', 'line_num', 'is_subtotal'])

    pivot_df = df.pivot_table(
        index=index_cols,
        columns='Fiscal_Year',
        values='Value',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Group data by major categories (with support for up to 4 levels)
    # Skip grouping for revenue_expenses (it uses flat structure)
    grouped_data = {}

    if statement_type != 'revenue_expenses':
        for _, row in pivot_df.iterrows():
            major = row['major']
            sub = row['sub']
            sub2 = row.get('sub2', '')
            sub3 = row.get('sub3', '')
            detail = row['detail']
            line_num = row['line_num']
            is_subtotal = row['is_subtotal']

            # Get values for each year
            year_values = {year: row.get(year, 0) for year in years}

            # Build nested structure: major -> sub -> sub2 -> sub3 -> items
            if major not in grouped_data:
                grouped_data[major] = {}

            sub_key = sub if sub else '_items'
            if sub_key not in grouped_data[major]:
                grouped_data[major][sub_key] = {}

            # For revenue with 4 levels, use sub2 as next level
            if sub2:
                sub2_key = sub2 if sub2 else '_items'
                if sub2_key not in grouped_data[major][sub_key]:
                    grouped_data[major][sub_key][sub2_key] = {}

                if sub3:
                    sub3_key = sub3 if sub3 else '_items'
                    if sub3_key not in grouped_data[major][sub_key][sub2_key]:
                        grouped_data[major][sub_key][sub2_key][sub3_key] = []

                    grouped_data[major][sub_key][sub2_key][sub3_key].append({
                        'detail': detail,
                        'line_num': line_num,
                        'is_subtotal': is_subtotal,
                        'year_values': year_values
                    })
                else:
                    # 3 levels only
                    if '_items' not in grouped_data[major][sub_key][sub2_key]:
                        grouped_data[major][sub_key][sub2_key]['_items'] = []
                    grouped_data[major][sub_key][sub2_key]['_items'].append({
                        'detail': detail,
                        'line_num': line_num,
                        'is_subtotal': is_subtotal,
                        'year_values': year_values
                    })
            else:
                # 2 levels only (original logic)
                if '_items' not in grouped_data[major][sub_key]:
                    grouped_data[major][sub_key]['_items'] = []
                grouped_data[major][sub_key]['_items'].append({
                    'detail': detail,
                    'line_num': line_num,
                    'is_subtotal': is_subtotal,
                    'year_values': year_values
                })

    # Build table rows
    table_rows = []

    # Helper function to calculate totals recursively
    def calc_totals_recursive(data, years):
        totals = {year: 0 for year in years}
        if isinstance(data, list):
            # Base case: list of items
            for item in data:
                if not item.get('is_subtotal', False):
                    for year in years:
                        totals[year] += item['year_values'].get(year, 0)
        elif isinstance(data, dict):
            # Recursive case: dict of sub-categories
            for value in data.values():
                sub_totals = calc_totals_recursive(value, years)
                for year in years:
                    totals[year] += sub_totals[year]
        return totals

    # Helper function to get minimum line number from nested structure
    def get_min_line_num(data):
        """Recursively find the minimum line number in a nested structure"""
        if isinstance(data, list):
            # Base case: list of items
            return min([item['line_num'] for item in data], default=999999)
        elif isinstance(data, dict):
            # Recursive case: dict of sub-categories
            min_nums = []
            for key, value in data.items():
                if key != '_items':
                    min_nums.append(get_min_line_num(value))
                else:
                    # _items is a list
                    min_nums.append(get_min_line_num(value))
            return min(min_nums, default=999999) if min_nums else 999999
        return 999999

    # Use statement-specific rendering
    if statement_type == 'revenue_expenses':
        # Revenue & Expenses: Simple rendering sorted by line, indented by level (1 or 2)
        sorted_items = sorted(pivot_df.to_dict('records'), key=lambda x: x['line_num'])

        for item in sorted_items:
            level = item.get('level', 1)
            detail = item['detail']
            is_subtotal = item.get('is_subtotal', False)

            # Determine indentation based on level
            if level == 1:
                padding_class = "ps-2"
                row_class = "table-secondary"
                use_bold = True
            else:  # level == 2
                padding_class = "ps-4"
                row_class = ""
                use_bold = is_subtotal

            # Create row
            if use_bold or is_subtotal:
                row_cells = [html.Td(html.Strong(detail), className=padding_class)]
            else:
                row_cells = [html.Td(detail, className=padding_class)]

            for year in years:
                value = item.get(year, 0)
                if use_bold or is_subtotal:
                    row_cells.append(html.Td(html.Strong(format_currency(value)), className="text-end"))
                else:
                    row_cells.append(html.Td(format_currency(value), className="text-end"))

            if is_subtotal:
                table_rows.append(html.Tr(row_cells, className="table-info"))
            elif row_class:
                table_rows.append(html.Tr(row_cells, className=row_class))
            else:
                table_rows.append(html.Tr(row_cells))

    elif statement_type == 'revenue':
        # Revenue-specific rendering: 3 levels (Revenue_Center -> Revenue_Group -> Revenue_Subgroup -> Detail)
        for major, subcats in sorted(grouped_data.items()):
            # Level 1: Revenue_Center (major) - ps-2
            major_totals = calc_totals_recursive(subcats, years)
            major_row_cells = [html.Td(html.Strong(major), className="text-uppercase ps-2")]
            for year in years:
                major_row_cells.append(
                    html.Td(html.Strong(format_currency(major_totals[year])), className="text-end")
                )
            table_rows.append(html.Tr(major_row_cells, className="table-primary"))

            # Level 2: Revenue_Group (sub) - ps-3 - sort by minimum line number
            for sub, sub_data in sorted(subcats.items(), key=lambda x: get_min_line_num(x[1])):
                if sub and sub != '_items':
                    sub_totals = calc_totals_recursive(sub_data, years)
                    sub_row_cells = [html.Td(html.Strong(sub), className="ps-3")]
                    for year in years:
                        sub_row_cells.append(
                            html.Td(html.Strong(format_currency(sub_totals[year])), className="text-end")
                        )
                    table_rows.append(html.Tr(sub_row_cells, className="table-secondary"))

                    # Level 3: Revenue_Subgroup (sub2) - ps-4 - sort by minimum line number
                    if isinstance(sub_data, dict):
                        for sub2, items_data in sorted(sub_data.items(), key=lambda x: get_min_line_num(x[1]) if x[0] != '_items' else 0):
                            if sub2 and sub2 != '_items':
                                sub2_totals = calc_totals_recursive(items_data, years)
                                sub2_row_cells = [html.Td(sub2, className="ps-4 fw-bold")]
                                for year in years:
                                    sub2_row_cells.append(
                                        html.Td(format_currency(sub2_totals[year]), className="text-end")
                                    )
                                table_rows.append(html.Tr(sub2_row_cells, style={'background-color': '#f8f9fa'}))

                            # Detail items: Revenue_Subgroup_Detail - ps-5
                            items_list = items_data.get('_items', []) if isinstance(items_data, dict) else items_data
                            if isinstance(items_list, list):
                                sorted_items = sorted(items_list, key=lambda x: x['line_num'])
                                for item in sorted_items:
                                    is_subtotal = item.get('is_subtotal', False)
                                    if is_subtotal:
                                        detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-5 fw-bold")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                                    else:
                                        detail_row_cells = [html.Td(item['detail'], className="ps-5")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells))
    else:
        # Generic rendering for other statement types (balance_sheet, revenue_expenses, costs)

        # Sort major categories - use line numbers for costs, custom order for balance sheet
        if statement_type == 'balance_sheet' or statement_type == 'fund_balance_changes':
            # For balance sheet: Assets first, then Liabilities, then Fund Balances
            def sort_major(item):
                major = item[0]
                if major == 'Assets':
                    return '0'
                elif major == 'Liabilities':
                    return '1'
                elif 'Fund' in major or 'Equity' in major or 'Balance' in major:
                    return '2'
                else:
                    return '3_' + major  # Other categories at end
            sorted_majors = sorted(grouped_data.items(), key=sort_major)
        else:
            # For costs and other statements: sort by minimum line number
            sorted_majors = sorted(grouped_data.items(), key=lambda x: get_min_line_num(x[1]))

        for major, subcats in sorted_majors:
            # Calculate major category totals for each year
            major_totals = calc_totals_recursive(subcats, years)

            # Major category header row
            major_row_cells = [html.Td(html.Strong(major), className="text-uppercase ps-2")]
            for year in years:
                major_row_cells.append(
                    html.Td(html.Strong(format_currency(major_totals[year])), className="text-end")
                )
            table_rows.append(html.Tr(major_row_cells, className="table-primary"))

            # Process subcategories (level 2) - sort by minimum line number
            for subcat, sub_data in sorted(subcats.items(), key=lambda x: get_min_line_num(x[1])):
                if subcat and subcat != '_items':
                    # Subcategory header row (Level 2)
                    subcat_totals = calc_totals_recursive(sub_data, years)
                    subcat_row_cells = [html.Td(f"  {subcat}", className="fw-bold ps-3")]
                    for year in years:
                        subcat_row_cells.append(
                            html.Td(format_currency(subcat_totals[year]), className="text-end fw-bold")
                        )
                    table_rows.append(html.Tr(subcat_row_cells, className="table-secondary"))

                # Check if sub_data contains another level or items
                if isinstance(sub_data, dict):
                    for sub2_key, sub2_data in sorted(sub_data.items(), key=lambda x: get_min_line_num(x[1]) if x[0] != '_items' else 0):
                        if sub2_key and sub2_key != '_items':
                            # Level 3 header (sub2)
                            sub2_totals = calc_totals_recursive(sub2_data, years)
                            sub2_row_cells = [html.Td(f"    {sub2_key}", className="fw-bold ps-4")]
                            for year in years:
                                sub2_row_cells.append(
                                    html.Td(format_currency(sub2_totals[year]), className="text-end")
                                )
                            table_rows.append(html.Tr(sub2_row_cells, style={'background-color': '#f8f9fa'}))

                        # Check if sub2_data contains another level or items
                        if isinstance(sub2_data, dict):
                            for sub3_key, sub3_data in sorted(sub2_data.items(), key=lambda x: get_min_line_num(x[1]) if x[0] != '_items' else 0):
                                if sub3_key and sub3_key != '_items':
                                    # Level 4 header (sub3)
                                    sub3_totals = calc_totals_recursive(sub3_data, years)
                                    sub3_row_cells = [html.Td(f"      {sub3_key}", className="ps-5")]
                                    for year in years:
                                        sub3_row_cells.append(
                                            html.Td(format_currency(sub3_totals[year]), className="text-end")
                                        )
                                    table_rows.append(html.Tr(sub3_row_cells, style={'background-color': '#fafafa'}))

                                # Render items at level 5 (detail items under level 4 header)
                                items_list = sub3_data if isinstance(sub3_data, list) else sub3_data.get('_items', [])
                                sorted_items = sorted(items_list, key=lambda x: x['line_num'])
                                for item in sorted_items:
                                    is_subtotal = item.get('is_subtotal', False)
                                    if is_subtotal:
                                        # Subtotals at level 5 (indented under level 4)
                                        detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-6 fw-bold")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                                    else:
                                        # Regular detail items at level 5
                                        detail_row_cells = [html.Td(item['detail'], className="ps-6")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells))
                        elif isinstance(sub2_data, list):
                            # Items directly at level 4 (under level 3 header)
                            sorted_items = sorted(sub2_data, key=lambda x: x['line_num'])
                            for item in sorted_items:
                                is_subtotal = item.get('is_subtotal', False)
                                if is_subtotal:
                                    # Subtotals at level 4
                                    detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-5 fw-bold")]
                                    for year in years:
                                        detail_row_cells.append(
                                            html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                        )
                                    table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                                else:
                                    # Regular detail items at level 4
                                    detail_row_cells = [html.Td(item['detail'], className="ps-5")]
                                    for year in years:
                                        detail_row_cells.append(
                                            html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                        )
                                    table_rows.append(html.Tr(detail_row_cells))
                elif isinstance(sub_data, list):
                    # Items directly at level 3 (under level 2 header, original 2-level structure)
                    sorted_items = sorted(sub_data, key=lambda x: x['line_num'])
                    for item in sorted_items:
                        is_subtotal = item.get('is_subtotal', False)
                        if is_subtotal:
                            # Subtotals at level 3
                            detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-4 fw-bold")]
                            for year in years:
                                detail_row_cells.append(
                                    html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                )
                            table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                        else:
                            # Regular detail items at level 3
                            detail_row_cells = [html.Td(item['detail'], className="ps-4")]
                            for year in years:
                                detail_row_cells.append(
                                    html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                )
                            table_rows.append(html.Tr(detail_row_cells))

    # Create table header with years
    header_cells = [html.Th("Account", className="text-start", style={'min-width': '300px'})]
    for year in years:
        header_cells.append(html.Th(str(int(year)), className="text-end", style={'min-width': '120px'}))

    # Create table
    table = dbc.Table([
        html.Thead(html.Tr(header_cells), className="table-dark"),
        html.Tbody(table_rows)
    ], bordered=True, hover=True, responsive=True, className="table-sm", style={'font-size': '0.9rem'})

    return html.Div([
        html.H5(title, className="mb-3"),
        html.P([
            html.Strong("Note: "),
            f"All amounts in millions (USD). Showing {len(years)} fiscal years: {min(years)} - {max(years)}"
        ], className="text-muted mb-3", style={'fontSize': '0.95rem'}),
        html.Div(table, style={'overflowX': 'auto'})
    ])


# Load Balance Sheet data
@app.callback(
    Output('balance-sheet-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('fund-type-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_balance_sheet(ccn, fund_type, active_subtab):
    """Load and display balance sheet for all years, filtered by fund type"""
    # Only load if this tab is active
    if active_subtab != 'subtab-balance-sheet':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    if not fund_type:
        fund_type = 'General Fund'

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Query database table directly (FAST with indexes)
            # Use CASE statement to create Column_name from Column if it doesn't exist
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Acc_level1, Acc_level2, Acc_level3, Line, 
                    CASE
                        WHEN "Column" = '00100' THEN 'General Fund'
                        WHEN "Column" = '00200' THEN 'Specific Purpose Fund'
                        WHEN "Column" = '00300' THEN 'Endowment Fund'
                        WHEN "Column" = '00400' THEN 'Plant Fund'
                        ELSE "Column"
                    END as Column_name,
                    Acc_name,
                    Value
                FROM balance_sheet
                WHERE Provider_Number = ?
                  AND CASE
                        WHEN "Column" = '00100' THEN 'General Fund'
                        WHEN "Column" = '00200' THEN 'Specific Purpose Fund'
                        WHEN "Column" = '00300' THEN 'Endowment Fund'
                        WHEN "Column" = '00400' THEN 'Plant Fund'
                        ELSE "Column"
                      END = ?
                ORDER BY Fiscal_Year, Line
            """, [int(ccn), fund_type]).df()
        else:
            # Fallback to parquet (has Column_name field)
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Acc_level1, Acc_level2, Acc_level3, Line, Column_name, Acc_name,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ? AND Column_name = ?
                ORDER BY Fiscal_Year, Line
            """, [data_manager.balance_sheet_path, int(ccn), fund_type]).df()

        con.close()

        if df.empty:
            return html.Div(f"No balance sheet data available for this hospital in {fund_type}", className="alert alert-warning")

        return create_multiyear_financial_table(df, f"Balance Sheet - {fund_type}", 'balance_sheet')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading balance sheet: {str(e)}", className="alert alert-danger")


# Load Revenue data
@app.callback(
    Output('revenue-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_revenue(ccn, active_subtab):
    """Load and display revenue detail for all years"""
    # Only load if this tab is active
    if active_subtab != 'subtab-revenue':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Query database table directly (FAST with indexes)
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, Revenue_Group, Revenue_Subgroup, Revenue_Subgroup_Detail, Revenue_Center,
                    Value
                FROM revenue
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, Line 
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, Revenue_Group, Revenue_Subgroup, Revenue_Subgroup_Detail, Revenue_Center,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, Line 
            """, [data_manager.revenue_path, int(ccn)]).df()

        con.close()

        if df.empty:
            return html.Div("No revenue data available for this hospital", className="alert alert-warning")

        return create_multiyear_financial_table(df, "Revenue Detail", 'revenue')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading revenue: {str(e)}", className="alert alert-danger")


# Load Revenue & Expenses data
@app.callback(
    Output('revenue-expenses-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_revenue_expenses(ccn, active_subtab):
    """Load and display revenue & expenses statement for all years"""
    # Only load if this tab is active
    if active_subtab != 'subtab-revenue-expenses':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Query database table directly (FAST with indexes)
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, RE_Report, RE_Account, RE_Line_Name,
                    COALESCE(RE_Level, 999) as RE_Level,
                    Value
                FROM revenue_expenses
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, RE_Level, RE_Report, Line
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, RE_Report, RE_Account, RE_Line_Name,
                    COALESCE(RE_Level, 999) as RE_Level,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, RE_Level, RE_Report, Line
            """, [data_manager.revenue_expenses_path, int(ccn)]).df()

        con.close()

        if df.empty:
            return html.Div("No revenue & expenses data available for this hospital", className="alert alert-warning")

        return create_multiyear_financial_table(df, "Revenue & Expenses Statement", 'revenue_expenses')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading revenue & expenses: {str(e)}", className="alert alert-danger")


# Load Cost Summary data (from B100, lines 3000-20200, column 2600)
@app.callback(
    Output('cost-summary-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_cost_summary(ccn, active_subtab):
    """Load and display cost summary from B100 worksheet"""
    # Only load if this tab is active (important for performance!)
    if active_subtab != 'subtab-cost-summary':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Query database table directly (FAST with indexes)
            # Filter: Lines 3000-20200, Column 2600 (Total)
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    CAST(Line AS INTEGER) as Line,
                    Account_group,
                    Account_name,
                    Value
                FROM costs_b100
                WHERE Provider_Number = ?
                  AND CAST(Line AS INTEGER) >= 3000
                  AND CAST(Line AS INTEGER) <= 20200
                  AND "Column" = '02600'
                ORDER BY Fiscal_Year, CAST(Line AS INTEGER)
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet
            costs_b100_path = str(COSTS_B100_OUTPUT / '**/*.parquet')
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    CAST(Line AS INTEGER) as Line,
                    Account_group,
                    Account_name,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                  AND CAST(Line AS INTEGER) >= 3000
                  AND CAST(Line AS INTEGER) <= 20200
                  AND "Column" = '02600'
                ORDER BY Fiscal_Year, CAST(Line AS INTEGER)
            """, [costs_b100_path, int(ccn)]).df()

        con.close()

        if df.empty:
            return html.Div([
                html.H5("Cost Summary Data Unavailable", className="alert-heading"),
                html.P([
                    "Cost Summary data is currently unavailable due to a known data quality issue with the B100 worksheet. ",
                    "The summary lines (3000-20200) in the CMS HCRIS data lack provider identifiers."
                ]),
                html.P([
                    "Please use the ",
                    html.Strong("Costs Detail"),
                    " tab instead for comprehensive cost center analysis."
                ]),
                html.P([
                    html.Em("Note: This will be fixed in a future ETL update.")
                ], className="mb-0")
            ], className="alert alert-warning")

        return create_multiyear_financial_table(df, "Cost Summary", 'cost-summary')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading cost summary: {str(e)}", className="alert alert-danger")


# Populate year dropdown for Detailed Costs
@app.callback(
    Output('detailed-costs-year-dropdown', 'options'),
    Output('detailed-costs-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_detailed_costs_years(ccn, active_subtab):
    """Populate available years for detailed costs when hospital is selected"""
    if active_subtab != 'subtab-detailed-costs' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM costs_a000
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            costs_a000_path = str(COSTS_A000_OUTPUT / '**/*.parquet')
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [costs_a000_path, int(ccn)]).df()
        con.close()

        if years_df.empty:
            return [], None

        years = years_df['Fiscal_Year'].tolist()
        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])  # Most recent year
        return options, default_value
    except:
        return [], None


# Load Detailed Costs data (Schedule A - Basic Table)
@app.callback(
    Output('detailed-costs-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('detailed-costs-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_detailed_costs(ccn, selected_year, active_subtab):
    """Load and display detailed costs from Schedule A for selected year"""
    # Only load if this tab is active (important for performance!)
    if active_subtab != 'subtab-detailed-costs':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    if not selected_year:
        return html.Div("Please select a fiscal year", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Simple query: get A000 data for the selected year and pivot columns based on Cost_type
            df = con.execute("""
                SELECT
                    --Line,
                    Account_group,
                    Account_name,
                    MAX(CASE WHEN "Column" = '00100' THEN Value ELSE 0 END) as Salaries,
                    MAX(CASE WHEN "Column" = '00200' THEN Value ELSE 0 END) as Other,

                    MAX(CASE WHEN "Column" = '00600' THEN Value ELSE 0 END) as Adjustments

                FROM costs_a000
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Account_name is not null
                GROUP BY Line, Account_group, Account_name
                ORDER BY CAST(Line AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet
            costs_a000_path = str(COSTS_A000_OUTPUT / '**/*.parquet')
            df = con.execute("""
                SELECT
                    Line,
                    Account_group,
                    Account_name,
                    MAX(CASE WHEN "Column" = '00100' THEN Value ELSE 0 END) as Salaries,
                    MAX(CASE WHEN "Column" = '00200' THEN Value ELSE 0 END) as Other,
                    MAX(CASE WHEN "Column" = '00600' THEN Value ELSE 0 END) as Adjustments
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                GROUP BY Line, Account_group, Account_name
                ORDER BY CAST(Line AS INTEGER)
            """, [costs_a000_path, int(ccn), int(selected_year)]).df()

        con.close()

        if df.empty:
            return html.Div(f"No detailed costs data available for fiscal year {selected_year}", className="alert alert-warning")

        # Create a simple table
        from dash import dash_table

        # Format table
        table = dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[
                {'name': 'Line', 'id': 'Line'},
                {'name': 'Account Group', 'id': 'Account_group'},
                {'name': 'Account Name', 'id': 'Account_name'},
                {'name': 'Salaries', 'id': 'Salaries', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
                {'name': 'Other', 'id': 'Other', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
                {'name': 'Adjustments', 'id': 'Adjustments', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
            ],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'fontSize': '13px'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'borderBottom': '2px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        )

        return html.Div([
            html.H5(f"Worksheet A - Cost Report (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading detailed costs: {str(e)}", className="alert alert-danger")


# Populate year dropdown for Worksheet B
@app.callback(
    Output('worksheet-b-year-dropdown', 'options'),
    Output('worksheet-b-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_worksheet_b_years(ccn, active_subtab):
    """Populate available years for worksheet B when hospital is selected"""
    if active_subtab != 'subtab-worksheet-b' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM costs_b100
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            costs_b100_path = str(COSTS_B100_OUTPUT / '**/*.parquet')
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [costs_b100_path, int(ccn)]).df()
        con.close()

        if years_df.empty:
            return [], None

        years = years_df['Fiscal_Year'].tolist()
        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])  # Most recent year
        return options, default_value
    except Exception as e:
        return [], None


# Load Worksheet B data
@app.callback(
    Output('worksheet-b-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('worksheet-b-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_worksheet_b(ccn, selected_year, active_subtab):
    """Load and display worksheet B (Schedule B-1 - Overhead Costs) for selected year"""
    # Only load if this tab is active (important for performance!)
    if active_subtab != 'subtab-worksheet-b':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    if not selected_year:
        return html.Div("Please select a fiscal year", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Get all overhead centers with their column values for sorting
            df = con.execute("""
                SELECT
                    Line,
                    Account_group,
                    Account_name,
                    "Column",
                    Overhead_center,
                    Value
                FROM costs_b100
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Account_name IS NOT NULL
                    AND Overhead_center IS NOT NULL
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet
            costs_b100_path = str(COSTS_B100_OUTPUT / '**/*.parquet')
            df = con.execute("""
                SELECT
                    Line,
                    Account_group,
                    Account_name,
                    "Column",
                    Overhead_center,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Account_name IS NOT NULL
                    AND Overhead_center IS NOT NULL
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [costs_b100_path, int(ccn), int(selected_year)]).df()

        con.close()

        if df.empty:
            return html.Div(f"No worksheet B data available for fiscal year {selected_year}", className="alert alert-warning")

        # Create mapping of Overhead_center to Column for sorting
        column_mapping = df[['Overhead_center', 'Column']].drop_duplicates()
        column_mapping['Column_Int'] = column_mapping['Column'].astype(int)
        column_mapping = column_mapping.sort_values('Column_Int')
        overhead_order = column_mapping['Overhead_center'].tolist()

        # Pivot the dataframe to have overhead centers as columns
        pivot_df = df.pivot_table(
            index=['Line', 'Account_group', 'Account_name'],
            columns='Overhead_center',
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Reorder columns based on Column value
        base_cols = ['Line', 'Account_group', 'Account_name']
        ordered_overhead_cols = [col for col in overhead_order if col in pivot_df.columns]
        pivot_df = pivot_df[base_cols + ordered_overhead_cols]

        # Create a simple table
        from dash import dash_table

        # Build column definitions dynamically based on overhead centers present
        columns = [
            {'name': 'Line', 'id': 'Line'},
            {'name': 'Account Group', 'id': 'Account_group'},
            {'name': 'Account Name', 'id': 'Account_name'},
        ]

        # Add columns for each overhead center (already sorted by Column value)
        for col in pivot_df.columns[3:]:  # Skip Line, Account_group, Account_name
            columns.append({
                'name': col,
                'id': col,
                'type': 'numeric',
                'format': {'specifier': '$,.0f'}
            })

        # Format table
        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'fontSize': '13px',
                'minWidth': '120px'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'borderBottom': '2px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        )

        return html.Div([
            html.H5(f"Worksheet B - Overhead Costs (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet B: {str(e)}", className="alert alert-danger")


# Populate year dropdown for Worksheet G
@app.callback(
    Output('worksheet-g-year-dropdown', 'options'),
    Output('worksheet-g-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_worksheet_g_years(ccn, active_subtab):
    """Populate available years for worksheet G when hospital is selected"""
    if active_subtab != 'subtab-worksheet-g' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM balance_sheet
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            balance_sheet_path = str(BALANCE_SHEET_OUTPUT / '**/*.parquet')
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [balance_sheet_path, int(ccn)]).df()
        con.close()

        if years_df.empty:
            return [], None

        years = years_df['Fiscal_Year'].tolist()
        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])  # Most recent year
        return options, default_value
    except Exception as e:
        return [], None


# Load Worksheet G data
@app.callback(
    Output('worksheet-g-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('worksheet-g-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_worksheet_g(ccn, selected_year, active_subtab):
    """Load and display worksheet G (Balance Sheet) for selected year"""
    # Only load if this tab is active (important for performance!)
    if active_subtab != 'subtab-worksheet-g':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    if not selected_year:
        return html.Div("Please select a fiscal year", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Get balance sheet data with Line and Column for sorting
            df = con.execute("""
                SELECT
                    Line,
                    "Column",
                    Acc_level2,
                    Acc_level3,
                    Acc_name,
                    Column_name,
                    Value
                FROM balance_sheet
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Acc_name IS NOT NULL
                    AND Column_name IS NOT NULL
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet
            balance_sheet_path = str(BALANCE_SHEET_OUTPUT / '**/*.parquet')
            df = con.execute("""
                SELECT
                    Line,
                    "Column",
                    Acc_level2,
                    Acc_level3,
                    Acc_name,
                    Column_name,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Acc_name IS NOT NULL
                    AND Column_name IS NOT NULL
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [balance_sheet_path, int(ccn), int(selected_year)]).df()

        con.close()

        if df.empty:
            return html.Div(f"No worksheet G data available for fiscal year {selected_year}", className="alert alert-warning")

        # Create mapping of Column_name to Column for sorting
        column_mapping = df[['Column_name', 'Column']].drop_duplicates()
        column_mapping['Column_Int'] = column_mapping['Column'].astype(int)
        column_mapping = column_mapping.sort_values('Column_Int')
        column_order = column_mapping['Column_name'].tolist()

        # Pivot the dataframe to have Column_name as columns
        pivot_df = df.pivot_table(
            index=['Line', 'Acc_level2', 'Acc_level3', 'Acc_name'],
            columns='Column_name',
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Reorder columns based on Column value
        base_cols = ['Line', 'Acc_level2', 'Acc_level3', 'Acc_name']
        ordered_column_cols = [col for col in column_order if col in pivot_df.columns]
        pivot_df = pivot_df[base_cols + ordered_column_cols]

        # Create a simple table
        from dash import dash_table

        # Build column definitions dynamically
        columns = [
            {'name': 'Line', 'id': 'Line'},
            {'name': 'Level 2', 'id': 'Acc_level2'},
            {'name': 'Level 3', 'id': 'Acc_level3'},
            {'name': 'Account Name', 'id': 'Acc_name'},
        ]

        # Add columns for each column name (already sorted by Column value)
        for col in pivot_df.columns[4:]:  # Skip Line, Acc_level2, Acc_level3, Acc_name
            columns.append({
                'name': col,
                'id': col,
                'type': 'numeric',
                'format': {'specifier': '$,.0f'}
            })

        # Format table
        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'fontSize': '13px',
                'minWidth': '120px'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'borderBottom': '2px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        )

        return html.Div([
            html.H5(f"Worksheet G - Balance Sheet (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet G: {str(e)}", className="alert alert-danger")


# ============================================================================
# WORKSHEET G-1 CALLBACKS (FUND BALANCE CHANGES)
# ============================================================================

# Populate year dropdown for Worksheet G-1
@app.callback(
    Output('worksheet-g1-year-dropdown', 'options'),
    Output('worksheet-g1-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_worksheet_g1_years(ccn, active_subtab):
    """Populate available years for worksheet G-1 when hospital is selected"""
    if active_subtab != 'subtab-worksheet-g1' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM fund_balance_changes
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet files
            fund_balance_parquet = Path('data/db_parquets/fund_balance_changes_long')
            df_list = []
            for partition_dir in fund_balance_parquet.glob('Fiscal_Year=*'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return [], None

            years_df = pd.concat(df_list, ignore_index=True)[['Fiscal_Year']].drop_duplicates()
            years_df = years_df.sort_values('Fiscal_Year', ascending=False)

        years = years_df['Fiscal_Year'].tolist()
        if not years:
            return [], None

        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])

        return options, default_value
    except Exception as e:
        print(f"Error populating worksheet G-1 years: {e}")
        import traceback
        traceback.print_exc()
        return [], None


# Load Worksheet G-1 data
@app.callback(
    Output('worksheet-g1-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('worksheet-g1-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_worksheet_g1(ccn, selected_year, active_subtab):
    """Load and display worksheet G-1 (Fund Balance Changes) for selected year"""
    if active_subtab != 'subtab-worksheet-g1':
        return html.Div()

    if not ccn or not selected_year:
        return html.Div("Please select a hospital and fiscal year.", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Get fund balance changes data with Line and Column for sorting
            df = con.execute("""
                SELECT
                    Line,
                    "Column",
                    Acc_level2,
                    Acc_level3,
                    Acc_name,
                    Value
                FROM fund_balance_changes
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Acc_name IS NOT NULL
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet files
            fund_balance_parquet = Path('data/db_parquets/fund_balance_changes_long')
            df_list = []
            for partition_dir in fund_balance_parquet.glob(f'Fiscal_Year={selected_year}'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return html.Div("No data available for this hospital and year.", className="alert alert-warning")

            df = pd.concat(df_list, ignore_index=True)
            df = df[df['Acc_name'].notna()]
            df['Line_Int'] = df['Line'].astype(int)
            df['Column_Int'] = df['Column'].astype(int)
            df = df.sort_values(['Line_Int', 'Column_Int'])

        if df.empty:
            return html.Div("No data available for this hospital and year.", className="alert alert-warning")

        # Create mapping of Column to Column for sorting (use Column code as display name)
        column_mapping = df[['Column']].drop_duplicates()
        column_mapping['Column_Int'] = column_mapping['Column'].astype(int)
        column_mapping = column_mapping.sort_values('Column_Int')
        column_order = column_mapping['Column'].tolist()

        # Pivot the dataframe to have Column as columns
        pivot_df = df.pivot_table(
            index=['Line', 'Acc_level2', 'Acc_level3', 'Acc_name'],
            columns='Column',
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Reorder columns based on Column value
        base_cols = ['Line', 'Acc_level2', 'Acc_level3', 'Acc_name']
        ordered_column_cols = [col for col in column_order if col in pivot_df.columns]
        pivot_df = pivot_df[base_cols + ordered_column_cols]

        # Create DataTable with dynamic columns
        columns = [
            {'name': 'Line', 'id': 'Line'},
            {'name': 'Level 2', 'id': 'Acc_level2'},
            {'name': 'Level 3', 'id': 'Acc_level3'},
            {'name': 'Account Name', 'id': 'Acc_name'},
        ]

        # Add value columns with currency formatting
        for col in pivot_df.columns[4:]:
            columns.append({
                'name': col,
                'id': col,
                'type': 'numeric',
                'format': {'specifier': '$,.0f'}
            })

        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'fontSize': '13px',
                'minWidth': '120px'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'borderBottom': '2px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        )

        return html.Div([
            html.H5(f"Worksheet G-1 - Fund Balance Changes (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet G-1: {str(e)}", className="alert alert-danger")


# ============================================================================
# WORKSHEET G-2 CALLBACKS (REVENUE)
# ============================================================================

# Populate year dropdown for Worksheet G-2
@app.callback(
    Output('worksheet-g2-year-dropdown', 'options'),
    Output('worksheet-g2-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_worksheet_g2_years(ccn, active_subtab):
    """Populate available years for worksheet G-2 when hospital is selected"""
    if active_subtab != 'subtab-worksheet-g2' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM revenue
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet files
            revenue_parquet = Path('data/db_parquets/revenue_long')
            df_list = []
            for partition_dir in revenue_parquet.glob('Fiscal_Year=*'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return [], None

            years_df = pd.concat(df_list, ignore_index=True)[['Fiscal_Year']].drop_duplicates()
            years_df = years_df.sort_values('Fiscal_Year', ascending=False)

        years = years_df['Fiscal_Year'].tolist()
        if not years:
            return [], None

        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])

        return options, default_value
    except Exception as e:
        print(f"Error populating worksheet G-2 years: {e}")
        import traceback
        traceback.print_exc()
        return [], None


# Load Worksheet G-2 data
@app.callback(
    Output('worksheet-g2-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('worksheet-g2-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_worksheet_g2(ccn, selected_year, active_subtab):
    """Load and display worksheet G-2 (Revenue) for selected year"""
    if active_subtab != 'subtab-worksheet-g2':
        return html.Div()

    if not ccn or not selected_year:
        return html.Div("Please select a hospital and fiscal year.", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Get revenue data with Line and Column for sorting
            # Note: Fill nulls with 'Unknown' to avoid filtering out data
            df = con.execute("""
                SELECT
                    Line,
                    "Column",
                    COALESCE(Revenue_Group, 'Unknown') as Revenue_Group,
                    COALESCE(Revenue_Subgroup, 'Unknown') as Revenue_Subgroup,
                    COALESCE(Revenue_Subgroup_Detail, 'Unknown') as Revenue_Subgroup_Detail,
                    COALESCE(Revenue_Center, 'Unknown') as Revenue_Center,
                    Value
                FROM revenue
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet files
            revenue_parquet = Path('data/db_parquets/revenue_long')
            df_list = []
            for partition_dir in revenue_parquet.glob(f'Fiscal_Year={selected_year}'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return html.Div("No data available for this hospital and year.", className="alert alert-warning")

            df = pd.concat(df_list, ignore_index=True)
            # Fill nulls with 'Unknown' instead of filtering them out
            df['Revenue_Group'] = df['Revenue_Group'].fillna('Unknown')
            df['Revenue_Subgroup'] = df['Revenue_Subgroup'].fillna('Unknown')
            df['Revenue_Subgroup_Detail'] = df['Revenue_Subgroup_Detail'].fillna('Unknown')
            df['Revenue_Center'] = df['Revenue_Center'].fillna('Unknown')
            df['Line_Int'] = df['Line'].astype(int)
            df['Column_Int'] = df['Column'].astype(int)
            df = df.sort_values(['Line_Int', 'Column_Int'])

        if df.empty:
            return html.Div("No data available for this hospital and year.", className="alert alert-warning")

        # Create mapping of Revenue_Center to Column for sorting
        column_mapping = df[['Revenue_Center', 'Column']].drop_duplicates()
        column_mapping['Column_Int'] = column_mapping['Column'].astype(int)
        column_mapping = column_mapping.sort_values('Column_Int')
        column_order = column_mapping['Revenue_Center'].tolist()

        # Pivot the dataframe to have Revenue_Center as columns
        pivot_df = df.pivot_table(
            index=['Line', 'Revenue_Group', 'Revenue_Subgroup', 'Revenue_Subgroup_Detail'],
            columns='Revenue_Center',
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Reorder columns based on Column value
        base_cols = ['Line', 'Revenue_Group', 'Revenue_Subgroup', 'Revenue_Subgroup_Detail']
        ordered_column_cols = [col for col in column_order if col in pivot_df.columns]
        pivot_df = pivot_df[base_cols + ordered_column_cols]

        # Create DataTable with dynamic columns
        columns = [
            {'name': 'Line', 'id': 'Line'},
            {'name': 'Revenue Group', 'id': 'Revenue_Group'},
            {'name': 'Revenue Subgroup', 'id': 'Revenue_Subgroup'},
            {'name': 'Revenue Detail', 'id': 'Revenue_Subgroup_Detail'},
        ]

        # Add value columns with currency formatting
        for col in pivot_df.columns[4:]:
            columns.append({
                'name': col,
                'id': col,
                'type': 'numeric',
                'format': {'specifier': '$,.0f'}
            })

        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'fontSize': '13px',
                'minWidth': '120px'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'borderBottom': '2px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        )

        return html.Div([
            html.H5(f"Worksheet G-2 - Revenue (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet G-2: {str(e)}", className="alert alert-danger")


# ============================================================================
# WORKSHEET G-3 CALLBACKS (REVENUE & EXPENSES)
# ============================================================================

# Populate year dropdown for Worksheet G-3
@app.callback(
    Output('worksheet-g3-year-dropdown', 'options'),
    Output('worksheet-g3-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_worksheet_g3_years(ccn, active_subtab):
    """Populate available years for worksheet G-3 when hospital is selected"""
    if active_subtab != 'subtab-worksheet-g3' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM revenue_expenses
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet files
            revenue_expenses_parquet = Path('data/db_parquets/revenue_expenses_long')
            df_list = []
            for partition_dir in revenue_expenses_parquet.glob('Fiscal_Year=*'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return [], None

            years_df = pd.concat(df_list, ignore_index=True)[['Fiscal_Year']].drop_duplicates()
            years_df = years_df.sort_values('Fiscal_Year', ascending=False)

        years = years_df['Fiscal_Year'].tolist()
        if not years:
            return [], None

        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])

        return options, default_value
    except Exception as e:
        print(f"Error populating worksheet G-3 years: {e}")
        import traceback
        traceback.print_exc()
        return [], None


# Load Worksheet G-3 data
@app.callback(
    Output('worksheet-g3-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('worksheet-g3-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_worksheet_g3(ccn, selected_year, active_subtab):
    """Load and display worksheet G-3 (Revenue & Expenses) for selected year"""
    if active_subtab != 'subtab-worksheet-g3':
        return html.Div()

    if not ccn or not selected_year:
        return html.Div("Please select a hospital and fiscal year.", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Get revenue & expenses data with Line and Column for sorting
            # Use Account_Name and Column (RE_Column_Name is all NULL in the data)
            df = con.execute("""
                SELECT
                    Line,
                    "Column",
                    COALESCE(Account_Name, 'Unknown') as Account_Name,
                    Value
                FROM revenue_expenses
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet files
            revenue_expenses_parquet = Path('data/db_parquets/revenue_expenses_long')
            df_list = []
            for partition_dir in revenue_expenses_parquet.glob(f'Fiscal_Year={selected_year}'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return html.Div("No data available for this hospital and year.", className="alert alert-warning")

            df = pd.concat(df_list, ignore_index=True)
            df['Account_Name'] = df['Account_Name'].fillna('Unknown')
            df['Line_Int'] = df['Line'].astype(int)
            df['Column_Int'] = df['Column'].astype(int)
            df = df.sort_values(['Line_Int', 'Column_Int'])

        if df.empty:
            return html.Div("No data available for this hospital and year.", className="alert alert-warning")

        # Create mapping of Column codes for sorting (use Column as display name)
        column_mapping = df[['Column']].drop_duplicates()
        column_mapping['Column_Int'] = column_mapping['Column'].astype(int)
        column_mapping = column_mapping.sort_values('Column_Int')
        column_order = column_mapping['Column'].tolist()

        # Pivot the dataframe to have Column as columns
        pivot_df = df.pivot_table(
            index=['Line', 'Account_Name'],
            columns='Column',
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Reorder columns based on Column value
        base_cols = ['Line', 'Account_Name']
        ordered_column_cols = [col for col in column_order if col in pivot_df.columns]
        pivot_df = pivot_df[base_cols + ordered_column_cols]

        # Create DataTable with dynamic columns
        columns = [
            {'name': 'Line', 'id': 'Line'},
            {'name': 'Account', 'id': 'Account_Name'},
        ]

        # Add value columns with currency formatting
        for col in pivot_df.columns[2:]:
            columns.append({
                'name': col,
                'id': col,
                'type': 'numeric',
                'format': {'specifier': '$,.0f'}
            })

        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '8px',
                'fontSize': '13px',
                'minWidth': '120px'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'borderBottom': '2px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        )

        return html.Div([
            html.H5(f"Worksheet G-3 - Revenue & Expenses (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet G-3: {str(e)}", className="alert alert-danger")


# Load Fund Balance Changes data
@app.callback(
    Output('fund-balance-changes-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_fund_balance_changes(ccn, active_subtab):
    """Load and display fund balance changes for all years"""
    # Only load if this tab is active
    if active_subtab != 'subtab-fund-balance-changes':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Query database table directly (FAST with indexes)
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, Acc_level1, Acc_level2, Acc_level3, Acc_name,
                    Value
                FROM fund_balance_changes
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, Line
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, Acc_level1, Acc_level2, Acc_level3, Acc_name,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, Line
            """, [data_manager.balance_sheet_path, int(ccn)]).df()

        con.close()

        if df.empty:
            return html.Div("No fund balance changes data available for this hospital", className="alert alert-warning")

        # The data structure is similar to balance sheet, so we can use the same formatter
        # Just need to ensure it has the expected column structure
        return create_multiyear_financial_table(df, "Statement of Changes in Fund Balances", 'fund_balance_changes')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading fund balance changes: {str(e)}", className="alert alert-danger")


# ============================================================================
# CMS WORKSHEETS CALLBACKS
# ============================================================================

@app.callback(
    [Output('cms-hospital-dropdown', 'options'),
     Output('cms-hospital-dropdown', 'value')],
    Input('main-tabs', 'active_tab')
)
def populate_cms_hospital_dropdown(active_tab):
    """Populate hospital dropdown for CMS Worksheets tab"""
    if active_tab != 'tab-cms-worksheets':
        return [], None

    try:
        worksheets_db_path = Path(__file__).parent / 'data' / 'hospital_worksheets.duckdb'
        con = duckdb.connect(str(worksheets_db_path), read_only=True)

        providers = con.execute("""
            SELECT DISTINCT Provider_Number, state_code
            FROM provider_list
            ORDER BY state_code, Provider_Number
        """).df()

        con.close()

        options = [
            {
                'label': f"{row['Provider_Number']} ({row['state_code']})",
                'value': row['Provider_Number']
            }
            for _, row in providers.iterrows()
        ]

        # Set first hospital as default
        default_value = options[0]['value'] if options else None

        return options, default_value
    except Exception as e:
        print(f"Error loading CMS hospitals: {e}")
        return [], None


@app.callback(
    [Output('cms-year-dropdown', 'options'),
     Output('cms-year-dropdown', 'value')],
    Input('cms-hospital-dropdown', 'value')
)
def populate_cms_year_dropdown(provider_number):
    """Populate year dropdown based on selected hospital"""
    if not provider_number:
        return [], None

    try:
        worksheets_db_path = Path(__file__).parent / 'data' / 'hospital_worksheets.duckdb'
        con = duckdb.connect(str(worksheets_db_path), read_only=True)

        years = con.execute("""
            SELECT DISTINCT fiscal_year
            FROM all_worksheets
            WHERE Provider_Number = ?
            ORDER BY fiscal_year DESC
        """, [provider_number]).df()

        con.close()

        options = [{'label': str(year), 'value': year} for year in years['fiscal_year']]

        # Set most recent year as default
        default_value = options[0]['value'] if options else None

        return options, default_value
    except Exception as e:
        print(f"Error loading years: {e}")
        return [], None


@app.callback(
    Output('cms-worksheet-content', 'children'),
    [Input('cms-worksheet-tabs', 'active_tab'),
     Input('cms-hospital-dropdown', 'value'),
     Input('cms-year-dropdown', 'value')]
)
def update_cms_worksheet_content(active_tab, ccn, selected_year):
    """Update content based on selected CMS worksheet tab"""

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    if not selected_year:
        return html.Div("Please select a fiscal year", className="alert alert-info")

    # Extract worksheet code from tab ID
    worksheet_code = active_tab.replace('cms-tab-', '').upper()

    # Worksheet names mapping
    WORKSHEET_NAMES = {
        'A000000': 'General Service Cost Centers',
        'A6000A0': 'Reclassifications',
        'A700001': 'Reconciliation of Capital Costs Centers',
        'A700002': 'Reconciliation of Capital Costs Centers',
        'A700003': 'Reconciliation of Capital Costs Centers',
        'A800000': 'Adjustments to Expenses',
        'A810000': 'Costs Incurred - Related Organizations',
        'A820010': 'Provider-Based Physicians Adjustments',
        'B000001': 'Cost Allocation - General Service Costs',
        'B000002': 'Cost Allocation - General Service Costs',
        'B100000': 'Cost Allocation - General Service Costs',
        'C000001': 'Cost Allocation - General Service Costs',
        'G000000': 'Balance Sheet',
        'G100000': 'Statement of Changes in Fund Balances',
        'G200000': 'Statement of Patient Revenues',
        'G300000': 'Statement of Revenues',
        'S000001': 'Settlement Summary',
        'S100001': 'Hospital Uncompensated & Indigent Care Data',
        'S200001': 'Hospital & Healthcare Complex ID Data',
        'S300001': 'Statistical Data',
        'S300002': 'Statistical Data',
        'S300004': 'Hospital Wage Related Costs',
        'S300005': 'Hospital Wage Related Costs',
        'S410000': 'Hospital Wage Related Costs',
        'S500000': 'Hospital Renal Dialysis Department',
    }

    worksheet_name = WORKSHEET_NAMES.get(worksheet_code, worksheet_code)

    try:
        # Connect to the worksheets database
        worksheets_db_path = Path(__file__).parent / 'data' / 'hospital_worksheets.duckdb'
        con = duckdb.connect(str(worksheets_db_path), read_only=True)

        # Query worksheet data
        # Sanitize worksheet_code to prevent SQL injection (only allow alphanumeric characters)
        if not worksheet_code.replace('_', '').isalnum():
            con.close()
            return html.Div(f"Invalid worksheet code", className="alert alert-danger")

        table_name = f'worksheet_{worksheet_code.lower()}'

        df = con.execute(f"""
            SELECT
                Line,
                "Column",
                line_level1,
                line_level2,
                col_level1,
                col_level2,
                Value
            FROM {table_name}
            WHERE Provider_Number = ?
                AND fiscal_year = ?
            ORDER BY Line, "Column"
        """, [ccn, int(selected_year)]).df()

        con.close()

        if df.empty:
            return html.Div(
                f"No data available for {worksheet_name} in fiscal year {selected_year}",
                className="alert alert-warning"
            )

        # Roll-up logic: Keep only rows/columns ending in "00", sum the detail lines
        df['Line_Parent'] = df['Line'].str[:3] + '00'
        df['Column_Parent'] = df['Column'].str[:3] + '00'

        # Group by parent Line and Column, sum the values
        rollup_df = df.groupby(['Line_Parent', 'Column_Parent'], as_index=False).agg({
            'Value': 'sum',
            'line_level1': 'first',
            'line_level2': 'first',
            'col_level1': 'first',
            'col_level2': 'first'
        })

        # Rename back to Line and Column
        rollup_df = rollup_df.rename(columns={'Line_Parent': 'Line', 'Column_Parent': 'Column'})
        df = rollup_df

        # Convert to string and fill NaN values with empty strings for display
        df['line_level1'] = df['line_level1'].astype(str).replace('nan', '').replace('<NA>', '')
        df['line_level2'] = df['line_level2'].astype(str).replace('nan', '').replace('<NA>', '')
        df['col_level1'] = df['col_level1'].astype(str).replace('nan', '').replace('<NA>', '')
        df['col_level2'] = df['col_level2'].astype(str).replace('nan', '').replace('<NA>', '')

        # Filter out rows where ALL line and column levels are empty
        df = df[
            (df['line_level1'] != '') | (df['line_level2'] != '') |
            (df['col_level1'] != '') | (df['col_level2'] != '')
        ]

        # Create row labels (Line + descriptions)
        df['Row_Label'] = df.apply(
            lambda x: f"{x['Line']} | {x['line_level1']} {x['line_level2']}".strip(),
            axis=1
        )

        # Create column labels (Column + descriptions)
        df['Col_Label'] = df.apply(
            lambda x: f"{x['Column']} | {x['col_level1']} {x['col_level2']}".strip() if x['col_level1'] or x['col_level2'] else x['Column'],
            axis=1
        )

        # Get unique columns in order
        col_order = df[['Column', 'Col_Label']].drop_duplicates().sort_values('Column')

        # Pivot the data
        pivot_df = df.pivot_table(
            index=['Line', 'Row_Label'],
            columns='Col_Label',
            values='Value',
            aggfunc='first'
        ).reset_index()

        # Reorder columns based on original Column order
        ordered_cols = ['Line', 'Row_Label'] + [col for col in col_order['Col_Label'] if col in pivot_df.columns]
        pivot_df = pivot_df[ordered_cols]

        # Create DataTable columns
        columns = [
            {'name': 'Line', 'id': 'Line', 'type': 'text'},
            {'name': 'Description', 'id': 'Row_Label', 'type': 'text'}
        ]

        # Add value columns
        for col in pivot_df.columns:
            if col not in ['Line', 'Row_Label']:
                columns.append({
                    'name': col,
                    'id': col,
                    'type': 'numeric',
                    'format': {'specifier': ',.2f'}
                })

        # Create table with professional styling
        pro_style = get_professional_datatable_style()

        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table=pro_style['style_table'],
            style_cell=pro_style['style_cell'],
            style_cell_conditional=[
                {
                    'if': {'column_id': 'Line'},
                    'width': '90px',
                    'textAlign': 'center',
                    'fontWeight': '600',
                    'color': '#5a6c7d',
                    'backgroundColor': '#f0f3f5'
                },
                {
                    'if': {'column_id': 'Row_Label'},
                    'minWidth': '280px',
                    'maxWidth': '450px',
                    'fontWeight': '500',
                    'paddingLeft': '16px'
                },
                {
                    'if': {'column_type': 'numeric'},
                    'textAlign': 'right',
                    'minWidth': '130px',
                    'fontFamily': 'Monaco, Consolas, "Courier New", monospace',
                    'fontWeight': '500',
                    'paddingRight': '16px'
                }
            ],
            style_header=pro_style['style_header'],
            style_data=pro_style['style_data'],
            style_data_conditional=pro_style['style_data_conditional'],
            page_size=100,
            filter_action='native',
            sort_action='native',
            export_format='xlsx',
            export_headers='display'
        )

        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H5(f"{worksheet_name} - Fiscal Year {selected_year}", className="mb-3"),
                    html.P([
                        html.Strong("Total rows: "), f"{len(pivot_df):,} | ",
                        html.Strong("Total columns: "), f"{len(pivot_df.columns)-2:,}"
                    ], className="text-muted mb-3"),
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    table
                ])
            ])
        ])

    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet: {str(e)}", className="alert alert-danger")


# ============================================================================
# VALUATION TAB CALLBACKS
# ============================================================================

@app.callback(
    Output('valuation-year-dropdown', 'options'),
    Input('hospital-dropdown', 'value')
)
def populate_valuation_years(ccn):
    """Populate year dropdown for valuation tab based on selected hospital"""
    if not ccn:
        return []

    con = data_manager.get_connection()
    try:
        query = """
        SELECT DISTINCT Fiscal_Year
        FROM income_statement_long
        WHERE Provider_Number = ?
        ORDER BY Fiscal_Year DESC
        """
        df = con.execute(query, [int(ccn)]).df()
        con.close()

        if df.empty:
            return []

        years = df['Fiscal_Year'].tolist()
        return [{'label': str(year), 'value': year} for year in years]
    except:
        con.close()
        return []


@app.callback(
    [Output('valuation-income-data', 'data'),
     Output('valuation-expense-data', 'data'),
     Output('valuation-baseline-metrics', 'data'),
     Output('valuation-content', 'children')],
    [Input('valuation-load-button', 'n_clicks')],
    [State('hospital-dropdown', 'value'),
     State('valuation-year-dropdown', 'value')]
)
def load_valuation_data(n_clicks, ccn, fiscal_year):
    """Load and display valuation data"""
    if n_clicks == 0 or not ccn or not fiscal_year:
        return None, None, None, html.Div([
            html.P("Please select a fiscal year and click 'Load Valuation Data'.",
                   className="text-center text-muted mt-4")
        ])

    # Load data
    income_df = load_valuation_income_statement(ccn, fiscal_year)
    expense_df = load_valuation_expense_detail(ccn, fiscal_year)

    if income_df.empty:
        return None, None, None, html.Div([
            html.P("No income statement data found for the selected hospital and year.",
                   className="text-center text-danger mt-4")
        ])

    # Calculate baseline metrics
    baseline = {}
    for _, row in income_df.iterrows():
        if row['Line_Name'] == 'Net_Patient_Revenue':
            baseline['net_revenue'] = row['Value']
        elif row['Line_Name'] == 'Operating_Income':
            baseline['operating_income'] = row['Value']
        elif row['Line_Name'] == 'Net_Income':
            baseline['net_income'] = row['Value']
        elif row['Line_Name'] == 'Total_Operating_Expenses':
            baseline['operating_expenses'] = row['Value']
        elif row['Line_Name'] == 'Total_Other_Income':
            baseline['other_income'] = row['Value']
        elif row['Line_Name'] == 'Total_Other_Expenses':
            baseline['other_expenses'] = row['Value']

    # Calculate baseline EBITDA (simplified - using Operating Income as proxy)
    baseline['ebitda'] = baseline.get('operating_income', 0)
    baseline['operating_margin'] = (baseline.get('operating_income', 0) /
                                     baseline.get('net_revenue', 1) * 100) if baseline.get('net_revenue', 0) != 0 else 0
    baseline['ebitda_margin'] = (baseline.get('ebitda', 0) /
                                  baseline.get('net_revenue', 1) * 100) if baseline.get('net_revenue', 0) != 0 else 0

    # Create dashboard layout
    valuation_layout = html.Div([
        # Row 1: Key Metrics Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Net Patient Revenue", className="text-muted mb-2"),
                        html.H4(f"${baseline.get('net_revenue', 0):,.0f}", className="text-primary mb-0")
                    ])
                ], className="shadow-sm")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Operating Income", className="text-muted mb-2"),
                        html.H4(f"${baseline.get('operating_income', 0):,.0f}", className="text-success mb-0"),
                        html.Small(f"{baseline['operating_margin']:.1f}% margin", className="text-muted")
                    ])
                ], className="shadow-sm")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("EBITDA (Est.)", className="text-muted mb-2"),
                        html.H4(f"${baseline.get('ebitda', 0):,.0f}", className="text-info mb-0"),
                        html.Small(f"{baseline['ebitda_margin']:.1f}% margin", className="text-muted")
                    ])
                ], className="shadow-sm")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Valuation (8x EBITDA)", className="text-muted mb-2"),
                        html.H4(f"${baseline.get('ebitda', 0) * 8:,.0f}", className="text-warning mb-0"),
                        html.Small("Estimated Value", className="text-muted")
                    ])
                ], className="shadow-sm")
            ], width=3)
        ], className="mb-4"),

        # Row 2: Sensitivity Analysis Controls
        dbc.Card([
            dbc.CardBody([
                html.H5("Valuation Sensitivity Analysis", className="mb-3"),
                html.P("Adjust the sliders below to see how changes affect valuation:", className="text-muted mb-4"),

                # Revenue Change
                html.Div([
                    html.Label("Revenue Change (%)", className="fw-bold"),
                    dcc.Slider(
                        id='revenue-slider',
                        min=-20, max=20, step=1, value=0,
                        marks={i: f"{i:+d}%" for i in range(-20, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], className="mb-4"),

                # Operating Margin Change
                html.Div([
                    html.Label("Operating Margin Change (percentage points)", className="fw-bold"),
                    dcc.Slider(
                        id='margin-slider',
                        min=-10, max=10, step=0.5, value=0,
                        marks={i: f"{i:+.0f}pp" for i in range(-10, 11, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], className="mb-4"),

                # Expense Change
                html.Div([
                    html.Label("Operating Expense Change (%)", className="fw-bold"),
                    dcc.Slider(
                        id='expense-slider',
                        min=-20, max=20, step=1, value=0,
                        marks={i: f"{i:+d}%" for i in range(-20, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], className="mb-4"),

                # Valuation Multiple
                html.Div([
                    html.Label("EBITDA Valuation Multiple", className="fw-bold"),
                    dcc.Slider(
                        id='multiple-slider',
                        min=4, max=14, step=0.5, value=8,
                        marks={i: f"{i}x" for i in range(4, 15, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], className="mb-3"),
            ])
        ], className="shadow-sm mb-4"),

        # Row 3: Adjusted Metrics Display
        html.Div(id='valuation-adjusted-metrics', className="mb-4"),

        # Row 4: Visualizations
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='valuation-waterfall'),
            ], width=6),
            dbc.Col([
                dcc.Graph(id='valuation-sensitivity'),
            ], width=6)
        ], className="mb-4"),

        # Row 5: Expense Breakdown
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='valuation-expense-breakdown'),
            ], width=6),
            dbc.Col([
                dcc.Graph(id='valuation-expense-type'),
            ], width=6)
        ])
    ])

    return (income_df.to_dict('records'),
            expense_df.to_dict('records') if not expense_df.empty else [],
            baseline,
            valuation_layout)


@app.callback(
    [Output('valuation-adjusted-metrics', 'children'),
     Output('valuation-waterfall', 'figure'),
     Output('valuation-sensitivity', 'figure'),
     Output('valuation-expense-breakdown', 'figure'),
     Output('valuation-expense-type', 'figure')],
    [Input('revenue-slider', 'value'),
     Input('margin-slider', 'value'),
     Input('expense-slider', 'value'),
     Input('multiple-slider', 'value')],
    [State('valuation-baseline-metrics', 'data'),
     State('valuation-income-data', 'data'),
     State('valuation-expense-data', 'data')]
)
def update_valuation_analysis(revenue_change, margin_change, expense_change, multiple,
                                baseline, income_data, expense_data):
    """Update valuation analysis based on slider inputs"""
    if not baseline:
        return html.Div(), {}, {}, {}, {}

    # Calculate adjusted metrics
    base_revenue = baseline.get('net_revenue', 0)
    base_expenses = baseline.get('operating_expenses', 0)
    base_operating_income = baseline.get('operating_income', 0)

    # Apply changes
    adj_revenue = base_revenue * (1 + revenue_change / 100)
    adj_expenses = base_expenses * (1 + expense_change / 100)
    adj_operating_income = adj_revenue - adj_expenses

    # Apply margin change (as percentage point change)
    if margin_change != 0:
        target_margin = (base_operating_income / base_revenue * 100) + margin_change
        adj_operating_income = adj_revenue * (target_margin / 100)
        adj_expenses = adj_revenue - adj_operating_income

    adj_ebitda = adj_operating_income
    adj_valuation = adj_ebitda * multiple

    # Calculate changes
    revenue_change_amt = adj_revenue - base_revenue
    expense_change_amt = adj_expenses - base_expenses
    operating_income_change = adj_operating_income - base_operating_income
    ebitda_change = adj_ebitda - baseline.get('ebitda', 0)
    valuation_change = adj_valuation - (baseline.get('ebitda', 0) * 8)

    # Adjusted metrics table with professional styling
    adjusted_metrics_layout = dbc.Card([
        dbc.CardBody([
            html.H5("Adjusted Valuation Metrics",
                   style={'color': '#2c3e50', 'fontWeight': '600', 'marginBottom': '20px', 'fontSize': '1.3rem'}),
            html.Div([
                dbc.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Metric", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                            html.Th("Original", className="text-end", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                            html.Th("Adjusted", className="text-end", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                            html.Th("Change ($)", className="text-end", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                            html.Th("Change (%)", className="text-end", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'})
                        ])
                    ]),
                    html.Tbody([
                        # Revenue Row
                        html.Tr([
                            html.Td("Net Patient Revenue", style={'padding': '12px', 'fontWeight': '500', 'color': '#2c3e50'}),
                            html.Td(f"${base_revenue:,.0f}", className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(f"${adj_revenue:,.0f}", className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(f"${revenue_change_amt:+,.0f}", className="text-end",
                                   style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if revenue_change_amt >= 0 else '#e74c3c', 'fontWeight': '600'}),
                            html.Td(f"{revenue_change:+.1f}%", className="text-end",
                                   style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if revenue_change >= 0 else '#e74c3c', 'fontWeight': '600'})
                        ], style={'backgroundColor': 'white'}),
                        # Expenses Row
                        html.Tr([
                            html.Td("Operating Expenses", style={'padding': '12px', 'fontWeight': '500', 'color': '#2c3e50'}),
                            html.Td(f"${base_expenses:,.0f}", className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(f"${adj_expenses:,.0f}", className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(f"${expense_change_amt:+,.0f}", className="text-end",
                                   style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#e74c3c' if expense_change_amt >= 0 else '#27ae60', 'fontWeight': '600'}),
                            html.Td(f"{(expense_change_amt/base_expenses*100) if base_expenses != 0 else 0:+.1f}%", className="text-end",
                                   style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#e74c3c' if expense_change_amt >= 0 else '#27ae60', 'fontWeight': '600'})
                        ], style={'backgroundColor': '#f8f9fa'}),
                        # Operating Income Row (Highlighted)
                        html.Tr([
                            html.Td(html.Strong("Operating Income"), style={'padding': '12px', 'color': '#2c3e50', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"${base_operating_income:,.0f}"), className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(html.Strong(f"${adj_operating_income:,.0f}"), className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(html.Strong(f"${operating_income_change:+,.0f}"),
                                   className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if operating_income_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"{(operating_income_change/base_operating_income*100) if base_operating_income != 0 else 0:+.1f}%"),
                                   className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if operating_income_change >= 0 else '#e74c3c', 'fontWeight': '700'})
                        ], style={'backgroundColor': '#e8f4f8', 'borderTop': '2px solid #3498db', 'borderBottom': '2px solid #3498db'}),
                        # EBITDA Row (Highlighted)
                        html.Tr([
                            html.Td(html.Strong("EBITDA (Est.)"), style={'padding': '12px', 'color': '#2c3e50', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"${baseline.get('ebitda', 0):,.0f}"), className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(html.Strong(f"${adj_ebitda:,.0f}"), className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(html.Strong(f"${ebitda_change:+,.0f}"),
                                   className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if ebitda_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"{(ebitda_change/baseline.get('ebitda', 1)*100):+.1f}%"),
                                   className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if ebitda_change >= 0 else '#e74c3c', 'fontWeight': '700'})
                        ], style={'backgroundColor': '#f8f9fa'}),
                        # Valuation Row (Most Important - Gold Highlight)
                        html.Tr([
                            html.Td(html.Strong(f"Enterprise Valuation ({multiple}x EBITDA)"), style={'padding': '14px', 'color': '#2c3e50', 'fontWeight': '700', 'fontSize': '1.05rem'}),
                            html.Td(html.Strong(f"${baseline.get('ebitda', 0) * 8:,.0f}"), className="text-end",
                                   style={'padding': '14px', 'fontFamily': 'monospace', 'fontSize': '1.05rem', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"${adj_valuation:,.0f}"), className="text-end",
                                   style={'padding': '14px', 'fontFamily': 'monospace', 'fontSize': '1.05rem', 'color': '#f39c12', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"${valuation_change:+,.0f}"),
                                   className="text-end", style={'padding': '14px', 'fontFamily': 'monospace', 'fontSize': '1.05rem', 'color': '#27ae60' if valuation_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"{(valuation_change/(baseline.get('ebitda', 1) * 8)*100):+.1f}%"),
                                   className="text-end", style={'padding': '14px', 'fontFamily': 'monospace', 'fontSize': '1.05rem', 'color': '#27ae60' if valuation_change >= 0 else '#e74c3c', 'fontWeight': '700'})
                        ], style={'backgroundColor': '#fff9e6', 'borderTop': '3px solid #f39c12', 'borderBottom': '3px solid #f39c12'})
                    ])
                ], className="mb-0",
                   style={'border': '1px solid #dee2e6', 'borderRadius': '8px', 'overflow': 'hidden', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'})
            ])
        ], style={'padding': '24px'})
    ], className="shadow-sm", style={'borderRadius': '10px', 'border': 'none'})

    # Create waterfall chart
    waterfall_fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["relative", "relative", "total"],
        x=["Net Revenue", "Operating Expenses", "Operating Income"],
        textposition="outside",
        text=[f"${adj_revenue:,.0f}", f"-${adj_expenses:,.0f}", f"${adj_operating_income:,.0f}"],
        y=[adj_revenue, -adj_expenses, None],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))

    waterfall_fig.update_layout(
        title="Adjusted Income Statement Flow",
        showlegend=False,
        height=400
    )

    # Create valuation sensitivity chart
    scenarios = ['Base Case', 'Current Scenario']
    valuations = [baseline.get('ebitda', 0) * 8, adj_valuation]
    colors = ['#3498db', '#27ae60' if valuation_change >= 0 else '#e74c3c']

    valuation_fig = go.Figure(data=[
        go.Bar(x=scenarios, y=valuations, marker_color=colors, text=valuations,
               texttemplate='$%{text:,.0f}', textposition='outside')
    ])

    valuation_fig.update_layout(
        title=f"Valuation Comparison (Change: ${valuation_change:+,.0f})",
        yaxis_title="Valuation ($)",
        height=400,
        showlegend=False
    )

    # Create expense breakdown charts
    expense_cat_fig = {}
    expense_type_fig = {}

    if expense_data:
        expense_df = pd.DataFrame(expense_data)

        # Expense by category
        expense_cat_fig = px.bar(
            expense_df.nlargest(10, 'Total_Expense'),
            x='Total_Expense',
            y='Expense_Category',
            orientation='h',
            title="Top 10 Expense Categories",
            labels={'Total_Expense': 'Total Expense ($)', 'Expense_Category': 'Category'},
            color='Total_Expense',
            color_continuous_scale='Reds'
        )
        expense_cat_fig.update_layout(height=400, showlegend=False)

        # Expense by type
        expense_type_summary = expense_df.groupby('Category_Type')['Total_Expense'].sum().reset_index()
        expense_type_fig = px.pie(
            expense_type_summary,
            values='Total_Expense',
            names='Category_Type',
            title="Expense Distribution by Type"
        )
        expense_type_fig.update_layout(height=400)

    return adjusted_metrics_layout, waterfall_fig, valuation_fig, expense_cat_fig, expense_type_fig


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("STARTING HOSPITAL KPI SCORECARD DASHBOARD")
    print("="*80)

    # Show correct data source
    if data_manager.use_precomputed:
        print(f"Data source: Optimized Database with Pre-Computed KPIs")
    elif data_manager.use_database:
        print(f"Data source: Database (raw tables only)")
    else:
        print(f"Data source: Parquet files (no database)")

    print(f"Available hospitals: {len(hospital_options)}")
    print(f"Dashboard running at: http://localhost:8050")
    print("="*80 + "\n")
    app.run(debug=True, port=8050)
