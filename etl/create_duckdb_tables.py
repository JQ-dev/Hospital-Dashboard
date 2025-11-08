"""
Create DuckDB tables from partitioned parquet files with smart Account_Name parsing
This creates a new 'hospital_analytics.duckdb' with intelligent account name decomposition

Features:
1. Smart Account_Name parsing based on financial knowledge and patterns
2. Hierarchical account structure recognition
3. Standardized date formats
4. Comprehensive summary tables for analysis
5. Multi-hospital support (configurable CCN list)
"""

import duckdb
import pandas as pd
from pathlib import Path
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
PROJECT_ROOT = Path(__file__).parent
DEFAULT_CCN = '010001'  # Alabama hospital - Southeast Health Medical Center

# ============================================================================
# SMART ACCOUNT NAME PARSING FUNCTIONS
# ============================================================================

def create_smart_balance_sheet_parsing():
    """
    Smart Balance Sheet Account_Name parsing based on financial structure knowledge

    Pattern Recognition:
    - General_Fund_BAL_ASSE_CURR_Cash_on_hand_and_in_banks
    - General_Fund_BAL_LIAB_CURR_Current_portion_of_LT_debt
    - General_Fund_BAL_FUND_CAPI_Restricted_fund_balance

    Hierarchical Structure:
    1. Fund: General_Fund, Designated_Fund, etc.
    2. Statement_Type: BAL (Balance Sheet)
    3. Major_Category: ASSE (Assets), LIAB (Liabilities), FUND (Fund Balance)
    4. Sub_Category: CURR (Current), FIXE (Fixed), LONG (Long-term), CAPI (Capital)
    5. Account_Group: Logical grouping (Cash, Receivables, Debt, etc.)
    6. Account_Detail: Specific account description
    """
    return """
    CREATE OR REPLACE TABLE balance_sheet AS
    SELECT
        Provider_Number,
        Fiscal_Year,
        State_Code,
        Account_Name,
        Value,
        Year,
        NPI,
        Control_Type,
        Report_Status,
        -- Standardize dates to YYYY-MM-DD format
        strptime(FY_Begin, '%m/%d/%Y')::DATE as FY_Begin,
        FY_End::DATE as FY_End,
        Geographic_Code,

        -- SMART PARSING: Fund Level (always first two parts)
        CASE
            WHEN split_part(Account_Name, '_', 1) = 'General' AND split_part(Account_Name, '_', 2) = 'Fund'
                THEN 'General_Fund'
            WHEN split_part(Account_Name, '_', 1) = 'Designated' AND split_part(Account_Name, '_', 2) = 'Fund'
                THEN 'Designated_Fund'
            ELSE split_part(Account_Name, '_', 1) || '_' || split_part(Account_Name, '_', 2)
        END as Fund,

        -- Statement Type (always BAL for balance sheet)
        split_part(Account_Name, '_', 3) as Statement_Type,

        -- Major Category with intelligent mapping
        CASE split_part(Account_Name, '_', 4)
            WHEN 'ASSE' THEN 'ASSETS'
            WHEN 'LIAB' THEN 'LIABILITIES'
            WHEN 'FUND' THEN 'FUND_BALANCE'
            ELSE split_part(Account_Name, '_', 4)
        END as Major_Category,

        -- Sub Category with business logic
        CASE split_part(Account_Name, '_', 5)
            WHEN 'CURR' THEN 'Current'
            WHEN 'FIXE' THEN 'Fixed'
            WHEN 'LONG' THEN 'Long-term'
            WHEN 'OTHE' THEN 'Other'
            WHEN 'CAPI' THEN 'Capital'
            WHEN 'RESTR' THEN 'Restricted'
            WHEN 'UNRESTR' THEN 'Unrestricted'
            ELSE split_part(Account_Name, '_', 5)
        END as Sub_Category,

        -- Account Group: Intelligent grouping based on account names
        CASE
            -- Cash and Cash Equivalents
            WHEN Account_Name LIKE '%Cash%' OR Account_Name LIKE '%Marketable%' THEN 'Cash_and_Investments'
            WHEN Account_Name LIKE '%Accounts_receivable%' OR Account_Name LIKE '%Patient%' THEN 'Receivables'
            WHEN Account_Name LIKE '%Inventory%' THEN 'Inventory'
            WHEN Account_Name LIKE '%Prepaid%' THEN 'Prepaid_Expenses'

            -- Fixed Assets
            WHEN Account_Name LIKE '%Building%' OR Account_Name LIKE '%Land%' THEN 'Property_and_Equipment'
            WHEN Account_Name LIKE '%Equipment%' THEN 'Equipment'
            WHEN Account_Name LIKE '%Leasehold%' THEN 'Leasehold_Improvements'
            WHEN Account_Name LIKE '%Construction%' THEN 'Construction_in_Progress'
            WHEN Account_Name LIKE '%Accumulated_depreciation%' THEN 'Accumulated_Depreciation'

            -- Liabilities
            WHEN Account_Name LIKE '%Accounts_payable%' THEN 'Accounts_Payable'
            WHEN Account_Name LIKE '%Accrued%' THEN 'Accrued_Liabilities'
            WHEN Account_Name LIKE '%Debt%' OR Account_Name LIKE '%Bond%' THEN 'Debt'
            WHEN Account_Name LIKE '%Mortgage%' THEN 'Mortgage_Payable'

            -- Equity/Fund Balance
            WHEN Account_Name LIKE '%Retained%' THEN 'Retained_Earnings'
            WHEN Account_Name LIKE '%Contributed%' THEN 'Contributed_Capital'
            WHEN Account_Name LIKE '%Restricted%' THEN 'Restricted_Funds'
            WHEN Account_Name LIKE '%Unrestricted%' THEN 'Unrestricted_Funds'

            -- Other Assets/Liabilities
            ELSE 'Other'
        END as Account_Group,

        -- Account Detail: Everything after the standard parts
        CASE
            WHEN length(Account_Name) - length(replace(Account_Name, '_', '')) + 1 > 5
            THEN substring(Account_Name,
                          length(split_part(Account_Name, '_', 1)) +
                          length(split_part(Account_Name, '_', 2)) +
                          length(split_part(Account_Name, '_', 3)) +
                          length(split_part(Account_Name, '_', 4)) +
                          length(split_part(Account_Name, '_', 5)) + 6)
            ELSE NULL
        END as Account_Detail,

        -- Business Logic Flags
        CASE WHEN split_part(Account_Name, '_', 4) = 'ASSE' THEN true ELSE false END as Is_Asset,
        CASE WHEN split_part(Account_Name, '_', 4) = 'LIAB' THEN true ELSE false END as Is_Liability,
        CASE WHEN split_part(Account_Name, '_', 4) = 'FUND' THEN true ELSE false END as Is_Equity,
        CASE WHEN split_part(Account_Name, '_', 5) = 'CURR' THEN true ELSE false END as Is_Current

    FROM read_parquet('balance_sheet_long/**/*.parquet', hive_partitioning=1)
    WHERE Provider_Number = ?
    ORDER BY Fiscal_Year DESC, Major_Category, Sub_Category, Account_Group, Account_Name;
    """

def create_smart_revenue_parsing():
    """
    Smart Revenue Account_Name parsing based on healthcare revenue patterns

    Pattern Recognition:
    - INPATIENT_IC_IP_Ancillary_services
    - OUTPATIENT_IC_IP_Outpatient_services
    - _TOTAL_IC_IP_Total_patient_revenues

    Hierarchical Structure:
    1. Patient_Type: INPATIENT, OUTPATIENT, _TOTAL (system totals)
    2. Service_Category: IC (Intensive Care), IP (Inpatient), OP (Outpatient), etc.
    3. Service_Subcategory: IP (General Inpatient), specific service types
    4. Service_Detail: Specific service descriptions
    """
    return """
    CREATE OR REPLACE TABLE revenue AS
    SELECT
        Provider_Number,
        Fiscal_Year,
        State_Code,
        Account_Name,
        Value,
        Year,
        NPI,
        Control_Type,
        Report_Status,
        -- Standardize dates
        strptime(FY_Begin, '%m/%d/%Y')::DATE as FY_Begin,
        FY_End::DATE as FY_End,
        Geographic_Code,

        -- SMART PARSING: Patient Type
        CASE
            WHEN Account_Name LIKE 'INPATIENT%' THEN 'INPATIENT'
            WHEN Account_Name LIKE 'OUTPATIENT%' THEN 'OUTPATIENT'
            WHEN Account_Name LIKE '_TOTAL%' THEN 'TOTAL'
            WHEN Account_Name LIKE 'TOTAL%' THEN 'TOTAL'
            ELSE 'OTHER'
        END as Patient_Type,

        -- Service Category with intelligent mapping
        CASE split_part(Account_Name, '_', 2)
            WHEN 'IC' THEN 'Intensive_Care'
            WHEN 'IP' THEN 'Inpatient'
            WHEN 'OP' THEN 'Outpatient'
            WHEN 'PatRev' THEN 'Patient_Revenue'
            WHEN 'Other' THEN 'Other_Revenue'
            WHEN 'Nonpat' THEN 'Non_Patient_Revenue'
            ELSE split_part(Account_Name, '_', 2)
        END as Service_Category,

        -- Service Subcategory
        CASE split_part(Account_Name, '_', 3)
            WHEN 'IP' THEN 'General_Inpatient'
            WHEN 'OP' THEN 'General_Outpatient'
            WHEN 'ICU' THEN 'Intensive_Care_Unit'
            WHEN 'CCU' THEN 'Coronary_Care_Unit'
            WHEN 'NICU' THEN 'Neonatal_ICU'
            WHEN 'SICU' THEN 'Surgical_ICU'
            WHEN 'MICU' THEN 'Medical_ICU'
            ELSE split_part(Account_Name, '_', 3)
        END as Service_Subcategory,

        -- Service Detail: Everything after standard parts
        CASE
            WHEN length(Account_Name) - length(replace(Account_Name, '_', '')) + 1 > 3
            THEN substring(Account_Name,
                          length(split_part(Account_Name, '_', 1)) +
                          length(split_part(Account_Name, '_', 2)) +
                          length(split_part(Account_Name, '_', 3)) + 4)
            ELSE split_part(Account_Name, '_', 1)
        END as Service_Detail,

        -- Business Logic Flags
        CASE WHEN Patient_Type = 'INPATIENT' THEN true ELSE false END as Is_Inpatient_Revenue,
        CASE WHEN Patient_Type = 'OUTPATIENT' THEN true ELSE false END as Is_Outpatient_Revenue,
        CASE WHEN Patient_Type = 'TOTAL' THEN true ELSE false END as Is_Total_Revenue,
        CASE WHEN Service_Category = 'Intensive_Care' THEN true ELSE false END as Is_Intensive_Care_Revenue

    FROM read_parquet('revenue_long/**/*.parquet', hive_partitioning=1)
    WHERE Provider_Number = ?
    ORDER BY Fiscal_Year DESC, Patient_Type, Service_Category, Account_Name;
    """

def create_smart_costs_parsing():
    """
    Smart Costs Account_Name parsing based on healthcare cost center patterns

    Pattern Recognition:
    - CAPITAL_RELATED_COSTS_BLDGS._&_FIXTURES_Anesthesiology
    - SALARIES_AND_WAGES_Nursing_Administration
    - PROFESSIONAL_FEES_Pathology

    Hierarchical Structure:
    1. Cost_Type: CAPITAL_RELATED_COSTS, SALARIES_AND_WAGES, etc.
    2. Cost_Category: BLDGS._&_FIXTURES, Nursing, etc.
    3. Cost_Center: Anesthesiology, Administration, etc.
    4. Cost_Detail: Additional descriptive information
    """
    return """
    CREATE OR REPLACE TABLE costs AS
    SELECT
        Provider_Number,
        Fiscal_Year,
        State_Code,
        Account_Name,
        Value,
        Year,
        NPI,
        Control_Type,
        Report_Status,
        -- Standardize dates
        strptime(FY_Begin, '%m/%d/%Y')::DATE as FY_Begin,
        FY_End::DATE as FY_End,
        Geographic_Code,

        -- SMART PARSING: Cost Type (first part, often multi-word)
        CASE
            WHEN Account_Name LIKE 'CAPITAL_RELATED_COSTS%' THEN 'CAPITAL_RELATED_COSTS'
            WHEN Account_Name LIKE 'SALARIES_AND_WAGES%' THEN 'SALARIES_AND_WAGES'
            WHEN Account_Name LIKE 'PROFESSIONAL_FEES%' THEN 'PROFESSIONAL_FEES'
            WHEN Account_Name LIKE 'SUPPLIES%' THEN 'SUPPLIES'
            WHEN Account_Name LIKE 'UTILITIES%' THEN 'UTILITIES'
            WHEN Account_Name LIKE 'MAINTENANCE%' THEN 'MAINTENANCE'
            WHEN Account_Name LIKE 'INSURANCE%' THEN 'INSURANCE'
            WHEN Account_Name LIKE 'ADMINISTRATIVE%' THEN 'ADMINISTRATIVE'
            WHEN Account_Name LIKE 'OTHER%' THEN 'OTHER'
            ELSE split_part(Account_Name, '_', 1)
        END as Cost_Type,

        -- Cost Category (second part, with intelligent mapping)
        CASE
            WHEN Account_Name LIKE 'CAPITAL_RELATED_COSTS_BLDGS%' THEN 'Buildings_and_Fixtures'
            WHEN Account_Name LIKE 'CAPITAL_RELATED_COSTS_MOVABLE%' THEN 'Movable_Equipment'
            WHEN Account_Name LIKE 'SALARIES_AND_WAGES_%' THEN
                CASE split_part(Account_Name, '_', 3)
                    WHEN 'Nursing' THEN 'Nursing'
                    WHEN 'Administrative' THEN 'Administrative'
                    WHEN 'Medical' THEN 'Medical'
                    WHEN 'Technical' THEN 'Technical'
                    WHEN 'Professional' THEN 'Professional'
                    ELSE split_part(Account_Name, '_', 3)
                END
            ELSE split_part(Account_Name, '_', 2)
        END as Cost_Category,

        -- Cost Center (last meaningful part, often department/service)
        CASE
            WHEN Account_Name IS NOT NULL AND Account_Name != 'None'
            THEN regexp_extract(Account_Name, '([^_]+)$', 1)
            ELSE NULL
        END as Cost_Center,

        -- Cost Detail (everything between category and center)
        CASE
            WHEN length(Account_Name) - length(replace(Account_Name, '_', '')) + 1 > 3
                AND Account_Name IS NOT NULL AND Account_Name != 'None'
            THEN substring(Account_Name,
                          length(split_part(Account_Name, '_', 1)) +
                          length(split_part(Account_Name, '_', 2)) +
                          length(split_part(Account_Name, '_', 3)) + 4,
                          length(Account_Name) - length(split_part(Account_Name, '_', 1)) -
                          length(split_part(Account_Name, '_', 2)) - length(split_part(Account_Name, '_', 3)) -
                          length(regexp_extract(Account_Name, '([^_]+)$', 1)) - 4)
            ELSE NULL
        END as Cost_Detail,

        -- Business Logic Flags
        CASE WHEN Cost_Type = 'SALARIES_AND_WAGES' THEN true ELSE false END as Is_Labor_Cost,
        CASE WHEN Cost_Type = 'SUPPLIES' THEN true ELSE false END as Is_Supply_Cost,
        CASE WHEN Cost_Type = 'CAPITAL_RELATED_COSTS' THEN true ELSE false END as Is_Capital_Cost,
        CASE WHEN Cost_Category = 'Nursing' THEN true ELSE false END as Is_Nursing_Cost

    FROM read_parquet('costs_long/**/*.parquet', hive_partitioning=1)
    WHERE Provider_Number = ?
        AND Account_Name IS NOT NULL
        AND Account_Name != 'None'
    ORDER BY Fiscal_Year DESC, Cost_Type, Cost_Category, Account_Name;
    """

# ============================================================================
# MAIN DATABASE CREATION FUNCTION
# ============================================================================

def create_hospital_analytics_database(ccn_list=None, db_name='hospital_analytics_new.duckdb'):
    """
    Create comprehensive DuckDB database with smart account parsing

    Args:
        ccn_list: List of CCNs to include (default: single hospital)
        db_name: Output database name
    """
    if ccn_list is None:
        ccn_list = [DEFAULT_CCN]

    logger.info("=" * 80)
    logger.info("SMART HOSPITAL ANALYTICS DATABASE CREATION")
    logger.info("=" * 80)
    logger.info(f"Target Database: {db_name}")
    logger.info(f"Hospitals to Process: {len(ccn_list)}")
    logger.info(f"CCNs: {', '.join(ccn_list)}")

    # Initialize DuckDB connection
    con = duckdb.connect(db_name)

    total_start_time = datetime.now()

    for ccn in ccn_list:
        logger.info(f"\n{'='*60}")
        logger.info(f"PROCESSING HOSPITAL CCN: {ccn}")
        logger.info(f"{'='*60}")

        # 1. BALANCE SHEET with Smart Parsing
        logger.info("\n1. Creating Balance Sheet table with smart parsing...")
        start_time = datetime.now()

        bs_query = create_smart_balance_sheet_parsing()
        con.execute(bs_query, [ccn])

        result = con.execute("SELECT COUNT(*) as records FROM balance_sheet").fetchone()
        logger.info(f"   [OK] Balance Sheet: {result[0]:,} records ({datetime.now() - start_time})")

        # Show sample parsed accounts
        sample = con.execute("""
            SELECT Account_Name, Fund, Major_Category, Sub_Category, Account_Group, Account_Detail
            FROM balance_sheet
            LIMIT 3
        """).df()
        logger.info("\n   Sample parsed accounts:")
        for _, row in sample.iterrows():
            logger.info(f"   • {row['Account_Name'][:50]}... → {row['Major_Category']}/{row['Account_Group']}")

        # 2. REVENUE with Smart Parsing
        logger.info("\n2. Creating Revenue table with smart parsing...")
        start_time = datetime.now()

        rev_query = create_smart_revenue_parsing()
        con.execute(rev_query, [ccn])

        result = con.execute("SELECT COUNT(*) as records FROM revenue").fetchone()
        logger.info(f"   [OK] Revenue: {result[0]:,} records ({datetime.now() - start_time})")

        # Show sample parsed revenue
        sample = con.execute("""
            SELECT Account_Name, Patient_Type, Service_Category, Service_Detail
            FROM revenue
            LIMIT 3
        """).df()
        logger.info("\n   Sample parsed revenue:")
        for _, row in sample.iterrows():
            logger.info(f"   • {row['Patient_Type']} → {row['Service_Category']}")

        # 3. COSTS with Smart Parsing
        logger.info("\n3. Creating Costs table with smart parsing...")
        start_time = datetime.now()

        cost_query = create_smart_costs_parsing()
        con.execute(cost_query, [ccn])

        result = con.execute("SELECT COUNT(*) as records FROM costs").fetchone()
        logger.info(f"   [OK] Costs: {result[0]:,} records ({datetime.now() - start_time})")

        # Show sample parsed costs
        sample = con.execute("""
            SELECT Account_Name, Cost_Type, Cost_Category, Cost_Center
            FROM costs
            WHERE Cost_Center IS NOT NULL
            LIMIT 3
        """).df()
        logger.info("\n   Sample parsed costs:")
        for _, row in sample.iterrows():
            logger.info(f"   • {row['Cost_Type']} → {row['Cost_Category']} → {row['Cost_Center']}")

        # 4. REVENUE & EXPENSES (unparsed, for compatibility)
        logger.info("\n4. Creating Revenue & Expenses table...")
        rev_exp_query = f"""
        CREATE OR REPLACE TABLE revenue_expenses AS
        SELECT
            Provider_Number,
            Fiscal_Year,
            State_Code,
            Account_Name,
            Value,
            Year,
            NPI,
            Control_Type,
            Report_Status,
            strptime(FY_Begin, '%m/%d/%Y')::DATE as FY_Begin,
            FY_End::DATE as FY_End,
            Geographic_Code
        FROM read_parquet('revenue_expenses_long/**/*.parquet', hive_partitioning=1)
        WHERE Provider_Number = ?
        ORDER BY Fiscal_Year DESC, Account_Name;
        """
        con.execute(rev_exp_query, [ccn])
        result = con.execute("SELECT COUNT(*) as records FROM revenue_expenses").fetchone()
        logger.info(f"   [OK] Revenue & Expenses: {result[0]:,} records")

        # 5. CREATE WIDE FORMAT TABLES
        logger.info("\n5. Creating wide format pivot tables...")

        # Balance Sheet Wide
        bs_wide_query = """
        CREATE OR REPLACE TABLE balance_sheet_wide AS
        PIVOT (
            SELECT Account_Name, Fiscal_Year, Value
            FROM balance_sheet
        )
        ON Fiscal_Year
        USING SUM(Value)
        ORDER BY Account_Name;
        """
        con.execute(bs_wide_query)
        result = con.execute("SELECT COUNT(*) as records FROM balance_sheet_wide").fetchone()
        logger.info(f"   [OK] Balance Sheet Wide: {result[0]} account rows")

        # Revenue Wide
        rev_wide_query = """
        CREATE OR REPLACE TABLE revenue_wide AS
        PIVOT (
            SELECT Account_Name, Fiscal_Year, Value
            FROM revenue
        )
        ON Fiscal_Year
        USING SUM(Value)
        ORDER BY Account_Name;
        """
        con.execute(rev_wide_query)
        result = con.execute("SELECT COUNT(*) as records FROM revenue_wide").fetchone()
        logger.info(f"   [OK] Revenue Wide: {result[0]} account rows")

        # 6. CREATE SUMMARY TABLES
        logger.info("\n6. Creating summary and analytical tables...")

        # Financial Summary
        financial_summary_query = """
        CREATE OR REPLACE TABLE financial_summary AS
        SELECT
            b.Fiscal_Year,
            b.Provider_Number,
            b.State_Code,
            COALESCE(SUM(CASE WHEN b.Is_Asset THEN b.Value END), 0) as Total_Assets,
            COALESCE(SUM(CASE WHEN b.Is_Liability THEN b.Value END), 0) as Total_Liabilities,
            COALESCE(SUM(CASE WHEN b.Is_Equity THEN b.Value END), 0) as Fund_Balance,
            COALESCE(SUM(r.Value), 0) as Total_Revenue,
            COALESCE(SUM(c.Value), 0) as Total_Costs,
            COALESCE(SUM(r.Value), 0) - COALESCE(SUM(c.Value), 0) as Net_Income
        FROM balance_sheet b
        LEFT JOIN revenue r ON b.Fiscal_Year = r.Fiscal_Year AND b.Provider_Number = r.Provider_Number
        LEFT JOIN costs c ON b.Fiscal_Year = c.Fiscal_Year AND b.Provider_Number = c.Provider_Number
        GROUP BY b.Fiscal_Year, b.Provider_Number, b.State_Code
        ORDER BY b.Fiscal_Year DESC;
        """
        con.execute(financial_summary_query)
        result = con.execute("SELECT COUNT(*) as records FROM financial_summary").fetchone()
        logger.info(f"   [OK] Financial Summary: {result[0]} year records")

        # KPI Summary
        kpi_query = """
        CREATE OR REPLACE TABLE kpi_summary AS
        SELECT
            Fiscal_Year,
            Provider_Number,
            Total_Revenue,
            Total_Costs,
            Net_Income,
            Total_Assets,
            Total_Liabilities,
            Fund_Balance,
            CASE WHEN Total_Revenue > 0 THEN (Net_Income / Total_Revenue) * 100 ELSE 0 END as Profit_Margin_Pct,
            CASE WHEN Total_Assets > 0 THEN (Net_Income / Total_Assets) * 100 ELSE 0 END as ROA_Pct,
            CASE WHEN Total_Liabilities > 0 THEN Total_Assets / Total_Liabilities ELSE 0 END as Debt_to_Asset_Ratio,
            CASE WHEN Total_Assets > 0 THEN (Total_Assets - Total_Liabilities) / Total_Assets * 100 ELSE 0 END as Equity_Ratio_Pct
        FROM financial_summary
        ORDER BY Fiscal_Year DESC;
        """
        con.execute(kpi_query)
        result = con.execute("SELECT COUNT(*) as records FROM kpi_summary").fetchone()
        logger.info(f"   [OK] KPI Summary: {result[0]} records")

        # Balance Sheet Summary by Category
        bs_category_summary = """
        CREATE OR REPLACE TABLE balance_sheet_by_category AS
        SELECT
            Fiscal_Year,
            Provider_Number,
            Fund,
            Major_Category,
            Sub_Category,
            Account_Group,
            SUM(Value) as Total_Value,
            COUNT(*) as Account_Count
        FROM balance_sheet
        GROUP BY Fiscal_Year, Provider_Number, Fund, Major_Category, Sub_Category, Account_Group
        ORDER BY Fiscal_Year DESC, Major_Category, Sub_Category, Account_Group;
        """
        con.execute(bs_category_summary)
        result = con.execute("SELECT COUNT(*) as records FROM balance_sheet_by_category").fetchone()
        logger.info(f"   [OK] Balance Sheet by Category: {result[0]} category records")

        # Revenue by Patient Type and Service
        revenue_summary = """
        CREATE OR REPLACE TABLE revenue_by_type AS
        SELECT
            Fiscal_Year,
            Provider_Number,
            Patient_Type,
            Service_Category,
            Service_Subcategory,
            SUM(Value) as Total_Revenue,
            COUNT(DISTINCT Account_Name) as Account_Count
        FROM revenue
        GROUP BY Fiscal_Year, Provider_Number, Patient_Type, Service_Category, Service_Subcategory
        ORDER BY Fiscal_Year DESC, Patient_Type, Service_Category;
        """
        con.execute(revenue_summary)
        result = con.execute("SELECT COUNT(*) as records FROM revenue_by_type").fetchone()
        logger.info(f"   [OK] Revenue by Type: {result[0]} type records")

        # Costs by Type and Category
        costs_summary = """
        CREATE OR REPLACE TABLE costs_by_type AS
        SELECT
            Fiscal_Year,
            Provider_Number,
            Cost_Type,
            Cost_Category,
            Cost_Center,
            SUM(Value) as Total_Costs,
            COUNT(DISTINCT Account_Name) as Account_Count
        FROM costs
        WHERE Cost_Center IS NOT NULL
        GROUP BY Fiscal_Year, Provider_Number, Cost_Type, Cost_Category, Cost_Center
        ORDER BY Fiscal_Year DESC, Cost_Type, Cost_Category, Total_Costs DESC;
        """
        con.execute(costs_summary)
        result = con.execute("SELECT COUNT(*) as records FROM costs_by_type").fetchone()
        logger.info(f"   [OK] Costs by Type: {result[0]} type records")

        # Top Revenue Accounts
        top_revenue_query = """
        CREATE OR REPLACE TABLE top_revenue_accounts AS
        SELECT
            Provider_Number,
            Fiscal_Year,
            Account_Name,
            Value,
            RANK() OVER (PARTITION BY Fiscal_Year ORDER BY Value DESC) as Rank
        FROM revenue
        WHERE Value > 0
        QUALIFY Rank <= 10
        ORDER BY Fiscal_Year DESC, Rank;
        """
        con.execute(top_revenue_query)
        result = con.execute("SELECT COUNT(*) as records FROM top_revenue_accounts").fetchone()
        logger.info(f"   [OK] Top Revenue Accounts: {result[0]} records")

        # Top Cost Centers
        top_costs_query = """
        CREATE OR REPLACE TABLE top_cost_centers AS
        SELECT
            Provider_Number,
            Fiscal_Year,
            Cost_Center,
            SUM(Value) as Total_Cost,
            COUNT(*) as Account_Count,
            RANK() OVER (PARTITION BY Fiscal_Year ORDER BY SUM(Value) DESC) as Rank
        FROM costs
        WHERE Cost_Center IS NOT NULL AND Value > 0
        GROUP BY Fiscal_Year, Provider_Number, Cost_Center
        QUALIFY Rank <= 20
        ORDER BY Fiscal_Year DESC, Rank;
        """
        con.execute(top_costs_query)
        result = con.execute("SELECT COUNT(*) as records FROM top_cost_centers").fetchone()
        logger.info(f"   [OK] Top Cost Centers: {result[0]} records")

        # Provider Info
        provider_info_query = """
        CREATE OR REPLACE TABLE provider_info AS
        SELECT DISTINCT
            Provider_Number,
            NPI,
            Control_Type,
            State_Code,
            Geographic_Code,
            MIN(FY_Begin) as First_Fiscal_Year_Begin,
            MAX(FY_End) as Last_Fiscal_Year_End,
            COUNT(DISTINCT Fiscal_Year) as Years_Reported
        FROM balance_sheet
        GROUP BY Provider_Number, NPI, Control_Type, State_Code, Geographic_Code;
        """
        con.execute(provider_info_query)
        result = con.execute("SELECT * FROM provider_info").fetchall()
        logger.info(f"   [OK] Provider Info: {len(result)} provider record")

    # ============================================================================
    # DISPLAY SUMMARY INFORMATION
    # ============================================================================

    logger.info(f"\n{'='*80}")
    logger.info("DATABASE CREATION SUMMARY")
    logger.info(f"{'='*80}")

    # Show tables created
    tables = con.execute("SHOW TABLES").df()
    logger.info(f"\nCreated {len(tables)} tables:")
    for table in tables['name']:
        count_query = f"SELECT COUNT(*) as cnt FROM {table}"
        try:
            count = con.execute(count_query).fetchone()[0]
            logger.info(f"  • {table}: {count:,} records")
        except:
            logger.info(f"  • {table}: (view/table)")

    # Show sample data
    logger.info(f"\n{'='*80}")
    logger.info("SAMPLE DATA PREVIEW")
    logger.info(f"{'='*80}")

    # Financial Summary
    logger.info("\nFinancial Summary (Latest Year):")
    summary_df = con.execute("SELECT * FROM financial_summary ORDER BY Fiscal_Year DESC LIMIT 1").df()
    logger.info(summary_df.to_string(index=False))

    # Balance Sheet Categories
    logger.info("\nBalance Sheet by Category (Latest Year):")
    bs_cat_df = con.execute("""
        SELECT Major_Category, Sub_Category, SUM(Total_Value) as Total_Value
        FROM balance_sheet_by_category
        WHERE Fiscal_Year = (SELECT MAX(Fiscal_Year) FROM balance_sheet_by_category)
        GROUP BY Major_Category, Sub_Category
        ORDER BY Major_Category, Sub_Category
    """).df()
    logger.info(bs_cat_df.to_string(index=False))

    # Revenue by Type
    logger.info("\nRevenue by Patient Type (Latest Year):")
    rev_type_df = con.execute("""
        SELECT Patient_Type, SUM(Total_Revenue) as Total_Revenue
        FROM revenue_by_type
        WHERE Fiscal_Year = (SELECT MAX(Fiscal_Year) FROM revenue_by_type)
        GROUP BY Patient_Type
        ORDER BY Total_Revenue DESC
    """).df()
    logger.info(rev_type_df.to_string(index=False))

    # Top Cost Centers
    logger.info("\nTop 5 Cost Centers (Latest Year):")
    top_costs_df = con.execute("""
        SELECT Cost_Center, Total_Cost, Rank
        FROM top_cost_centers
        WHERE Fiscal_Year = (SELECT MAX(Fiscal_Year) FROM top_cost_centers)
        ORDER BY Rank
        LIMIT 5
    """).df()
    logger.info(top_costs_df.to_string(index=False))

    # Close connection
    con.close()

    total_time = datetime.now() - total_start_time
    logger.info(f"\n{'='*80}")
    logger.info("[SUCCESS] Smart hospital analytics database created!")
    logger.info(f"[SUCCESS] Database: {db_name}")
    logger.info(f"[SUCCESS] Total processing time: {total_time}")
    logger.info(f"[SUCCESS] Hospitals processed: {len(ccn_list)}")
    logger.info("[SUCCESS] Features: Smart account parsing, standardized dates, comprehensive summaries")
    logger.info(f"{'='*80}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Default: single hospital
    ccn_list = [DEFAULT_CCN]

    # Allow command line specification of multiple CCNs
    if len(sys.argv) > 1:
        ccn_list = sys.argv[1:]

    create_hospital_analytics_database(ccn_list)