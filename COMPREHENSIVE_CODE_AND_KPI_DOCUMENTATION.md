# Comprehensive Hospital Dashboard Documentation
## Code Structure, Functionalities, and KPI Reference

**Version**: 1.0
**Last Updated**: 2025-11-22
**Purpose**: Complete technical documentation of the Hospital Dashboard application including all code structures, KPIs with formulas, and data source locations.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Application Architecture](#application-architecture)
3. [Code Structure and Components](#code-structure-and-components)
4. [Complete KPI Reference with Formulas](#complete-kpi-reference-with-formulas)
5. [Data Sources and Origins](#data-sources-and-origins)
6. [Data Flow Architecture](#data-flow-architecture)
7. [Database Schema](#database-schema)
8. [Component Details](#component-details)
9. [ETL Pipeline](#etl-pipeline)
10. [Authentication System](#authentication-system)

---

## Executive Summary

The Hospital Dashboard is a Python-based web application built with Dash/Plotly that provides interactive financial analytics for hospitals using CMS HCRIS (Hospital Cost Report Information System) data. The application features:

- **78 KPIs** organized in a 3-level hierarchy (6 Level 1, 24 Level 2, 48 Level 3)
- **4 benchmark levels** (National, State, Hospital Type, State+Hospital Type)
- **Multi-year analysis** (2020-2024)
- **6,000+ hospitals** tracked
- **Pre-computed analytics** using DuckDB for sub-100ms query performance
- **Secure authentication** with multi-user support

---

## Application Architecture

### Technology Stack

```
Frontend:
├── Dash (web framework)
├── Plotly (visualizations)
├── Dash Bootstrap Components (UI components)
└── HTML/CSS (layout)

Backend:
├── Python 3.8+ (application logic)
├── DuckDB (analytical database)
├── Pandas (data manipulation)
└── NumPy (numerical operations)

Data Storage:
├── DuckDB (~3.5 GB optimized database)
├── Parquet files (transformed data)
└── CSV files (source CMS data)

Authentication:
└── Custom auth system with SQLite backend
```

### Application Modes

1. **Production Mode** (`app.py`): Full authentication enabled
2. **Development Mode** (`dashboard.py`): No authentication for testing
3. **Authenticated Mode** (`app_with_auth.py`): Base authenticated application

---

## Code Structure and Components

### Directory Structure

```
Hospital-Dashboard/
│
├── Core Application Files
│   ├── app.py                          # Production entry point with auth
│   ├── app_with_auth.py                # Authenticated application
│   ├── dashboard.py                    # Main dashboard (4,291 lines)
│   ├── valuation_dashboard.py         # Valuation analysis module
│   ├── dashboard_worksheets.py         # Worksheet viewer
│   └── dashboard_worksheets_v2.py      # Enhanced worksheet viewer
│
├── Configuration
│   ├── kpi_hierarchy_config.py         # 78 KPI definitions (1,111 lines)
│   ├── config/
│   │   ├── __init__.py
│   │   └── paths.py                    # Path configuration
│   └── requirements.txt                # Dependencies
│
├── Components (UI Elements)
│   ├── components/
│   │   ├── kpi_cards.py                # KPI card components (863 lines)
│   │   └── __init__.py
│
├── Callbacks (Interactivity)
│   ├── callbacks/
│   │   ├── dashboard_callbacks.py      # Main dashboard callbacks
│   │   ├── valuation_callbacks.py      # Valuation callbacks
│   │   ├── cms_worksheets_callbacks.py # CMS worksheet callbacks
│   │   ├── balance_worksheets_callbacks.py
│   │   ├── cost_worksheets_callbacks.py
│   │   ├── financial_statements_callbacks.py
│   │   └── __init__.py
│
├── Utilities
│   ├── utils/
│   │   ├── kpi_helpers.py              # KPI calculations (182 lines)
│   │   ├── financial_tables.py         # Financial table utilities
│   │   ├── error_helpers.py            # Error handling
│   │   └── logging_config.py           # Logging setup
│
├── Data Loaders
│   ├── data_loaders/
│   │   ├── valuation.py                # Valuation data loaders
│   │   └── __init__.py
│
├── ETL Pipeline
│   ├── etl/
│   │   ├── create_duckdb_tables.py     # Step 1: Source tables
│   │   ├── create_balance_sheet.py     # Step 2: Balance sheet
│   │   ├── create_revenue.py           # Step 3: Revenue
│   │   ├── create_revenue_expenses.py  # Step 4: Rev & expenses
│   │   ├── create_costs_a000.py        # Step 5a: Cost schedule A
│   │   ├── create_costs_b100.py        # Step 5b: Cost schedule B-1
│   │   ├── create_income_statement.py  # Income statement
│   │   ├── create_expense_detail.py    # Expense details
│   │   ├── create_fund_balance_changes.py
│   │   ├── create_worksheet_a000000.py
│   │   ├── create_all_worksheets.py
│   │   └── process_a6000a0.py
│
├── Scripts
│   ├── scripts/
│   │   ├── build_database.py           # Build optimized DB
│   │   ├── load_valuation_data.py      # Load valuation data
│   │   └── add_state_filters.py        # Add state filtering
│
├── Authentication
│   ├── auth_manager.py                 # Auth business logic (14,660 lines)
│   ├── auth_models.py                  # Data models (14,265 lines)
│   ├── auth_components.py              # UI components (22,430 lines)
│
├── Data Storage
│   ├── hospital_analytics.duckdb       # Main database (~3.5 GB)
│   ├── data/
│   │   ├── source_data/                # CMS HCRIS CSV files
│   │   ├── db_parquets/                # Transformed parquet files
│   │   ├── Col_Names/                  # Column mapping files
│   │   └── other_data/                 # Reference data
│
└── Documentation
    ├── README.md                       # User guide
    ├── KPI_HIERARCHY_DOCUMENTATION.md  # KPI hierarchy docs
    ├── DATA_STRUCTURE_FOR_ANALYSTS.md  # Data structure guide
    ├── APP_STRUCTURE.md                # Application structure
    ├── AUTHENTICATION_GUIDE.md         # Auth system guide
    ├── DEPLOYMENT_GUIDE.md             # Deployment instructions
    └── COMPREHENSIVE_CODE_AND_KPI_DOCUMENTATION.md  # This file
```

### Key Modules

#### 1. Main Dashboard (`dashboard.py`)

**Purpose**: Core application logic and data management

**Key Classes**:
- `HospitalDataManager`: Manages database connections and queries
  - `get_connection()`: Create read-only DuckDB connection
  - `get_hospital_list()`: Retrieve hospital metadata
  - `calculate_kpis(ccn, fiscal_year)`: Calculate KPIs for hospital
  - `get_benchmark_data()`: Retrieve benchmark statistics
  - `load_financial_data()`: Load financial statements

**Key Functions**:
- `create_dashboard_layout()`: Generate main UI layout
- `create_kpi_section()`: Create KPI card grid
- `format_number()`: Number formatting utilities

#### 2. KPI Configuration (`kpi_hierarchy_config.py`)

**Purpose**: Define all 78 KPIs with metadata

**Data Structures**:
- `KPI_HIERARCHY`: Nested dictionary with 3-level structure
- `KPI_METADATA`: Flat dictionary for easy access

**Helper Functions**:
- `get_level_1_kpis()`: Return Level 1 KPIs
- `get_level_2_kpis(level_1_key)`: Return Level 2 drivers
- `get_level_3_kpis(level_1_key, level_2_key)`: Return Level 3 sub-drivers
- `get_kpi_lineage(kpi_key)`: Get KPI hierarchy path
- `flatten_kpi_hierarchy()`: Convert nested to flat structure

#### 3. KPI Cards (`components/kpi_cards.py`)

**Purpose**: Create interactive KPI visualization components

**Key Functions**:
- `create_kpi_card()`: Basic KPI card with trend and benchmark
- `create_enhanced_level1_kpi_card()`: Enhanced card with 4 benchmark levels
- `create_hierarchical_kpi_card()`: Expandable card with L2/L3 drivers
- `create_historical_quartile_table()`: Color-coded historical values

#### 4. KPI Helpers (`utils/kpi_helpers.py`)

**Purpose**: KPI calculation and analysis utilities

**Key Functions**:
- `calculate_importance_score(kpi_key)`: Base importance (impact × ease)
- `calculate_dynamic_priority()`: Priority based on performance gap
- `calculate_percentile_rank()`: Determine quartile position
- `calculate_trend()`: YoY trend direction and magnitude
- `create_sparkline()`: Generate mini trend chart

---

## Complete KPI Reference with Formulas

### KPI Hierarchy Overview

**Total KPIs**: 78
**Level 1**: 6 strategic KPIs
**Level 2**: 24 driver KPIs (4 per Level 1)
**Level 3**: 48 sub-driver KPIs (2 per Level 2)

---

## LEVEL 1 KPIs (Strategic Metrics)

### L1-1: Net Income Margin

**Category**: Profitability
**Unit**: %
**Format**: .1f (e.g., "3.5%")
**Higher is Better**: Yes
**Target Range**: 2-4%
**Impact Score**: 10/10
**Ease of Change**: 4/10

**Description**: Overall profitability reflecting financial health and sustainability.

**Formula**:
```
Net Income Margin = (Net Income) ÷ (Total Revenue) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G-3, Line 29 (Net Income)
Denominator: Worksheet G-3, Line 3 (Total Operating Revenue)
```

**Database Calculation**:
```sql
SELECT
    Provider_Number,
    Fiscal_Year,
    (Net_Income / NULLIF(Total_Revenue, 0)) * 100 as Net_Income_Margin
FROM hospital_kpis
WHERE Provider_Number = ? AND Fiscal_Year = ?
```

**Improvement Levers**:
- Improve operating margin
- Manage non-operating income
- Control expenses

---

### L1-2: Days in Net Patient Accounts Receivable (AR Days)

**Category**: Revenue Cycle
**Unit**: days
**Format**: .0f (e.g., "45 days")
**Higher is Better**: No
**Target Range**: 40-50 days
**Impact Score**: 9/10
**Ease of Change**: 7/10

**Description**: Cash cycle efficiency measuring how quickly the hospital collects revenue.

**Formula**:
```
AR Days = (Net Patient AR) ÷ (Net Patient Revenue ÷ 365)
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G (Balance Sheet), Current Assets - Net Patient AR
Denominator: Worksheet G-3, Line 3 (Total Operating Revenue) ÷ 365
```

**Database Calculation**:
```sql
SELECT
    Provider_Number,
    Fiscal_Year,
    Net_Patient_AR / NULLIF((Total_Revenue / 365.0), 0) as AR_Days
FROM hospital_kpis
WHERE Provider_Number = ? AND Fiscal_Year = ?
```

**Improvement Levers**:
- Improve billing processes
- Reduce denials
- Accelerate collections

---

### L1-3: Operating Expense per Adjusted Discharge

**Category**: Cost Management
**Unit**: $
**Format**: ,.0f (e.g., "$10,500")
**Higher is Better**: No
**Target Range**: $8,000-$12,000
**Impact Score**: 9/10
**Ease of Change**: 6/10

**Description**: Cost control efficiency gauging per-unit cost management.

**Formula**:
```
Operating Expense per Adjusted Discharge =
    (Total Operating Expenses) ÷ (Adjusted Discharges)

Where Adjusted Discharges =
    (Inpatient Discharges × Case Mix Index) + (Outpatient Visits × 0.35)
```

**HCRIS Data Source**:
```
Numerator: Worksheet G-3, Line 25 (Total Operating Expenses)
Denominator Components:
  - Worksheet S-3, Part I, Line 1, Column 1: Inpatient Discharges
  - Worksheet S-3, Part I, Line 1, Column 15: Case Mix Index (CMI)
  - Worksheet S-3, Part I, Line 15, Column 1: Outpatient Visits
```

**Database Calculation**:
```sql
SELECT
    Provider_Number,
    Fiscal_Year,
    Total_Operating_Expenses / NULLIF(
        (Inpatient_Discharges * Case_Mix_Index) +
        (Outpatient_Visits * 0.35),
        0
    ) as Operating_Expense_per_Adjusted_Discharge
FROM hospital_kpis
WHERE Provider_Number = ? AND Fiscal_Year = ?
```

**Improvement Levers**:
- Reduce labor costs
- Optimize supply costs
- Improve operational efficiency

---

### L1-4: Medicare Cost-to-Charge Ratio (CCR)

**Category**: Efficiency
**Unit**: ratio
**Format**: .3f (e.g., "0.325")
**Higher is Better**: No
**Target Range**: 0.2-0.4
**Impact Score**: 7/10
**Ease of Change**: 5/10

**Description**: Cost efficiency proxy. Lower CCR indicates better charge optimization.

**Formula**:
```
Medicare CCR = (Total Costs) ÷ (Total Charges)
```

**HCRIS Data Source**:
```
Numerator:   Worksheet C, Part I, Column 5 (Sum of all cost centers)
Denominator: Worksheet C, Part I, Column 8 (Sum of all charges)
```

**Database Calculation**:
```sql
SELECT
    Provider_Number,
    Fiscal_Year,
    Total_Costs / NULLIF(Total_Charges, 0) as Medicare_CCR
FROM hospital_kpis
WHERE Provider_Number = ? AND Fiscal_Year = ?
```

**Improvement Levers**:
- Optimize charge master
- Control costs
- Improve operational efficiency

---

### L1-5: Bad Debt + Charity as % of Net Revenue

**Category**: Revenue Cycle
**Unit**: %
**Format**: .1f (e.g., "5.5%")
**Higher is Better**: No
**Target Range**: 3-8%
**Impact Score**: 8/10
**Ease of Change**: 5/10

**Description**: Uncompensated care burden measuring charity care and bad debt as % of revenue.

**Formula**:
```
Bad Debt + Charity % =
    (Bad Debt + Charity Care) ÷ (Net Revenue - Provisions) × 100
```

**HCRIS Data Source**:
```
Numerator Components:
  - Worksheet S-10, Line 29, Column 3: Bad Debt
  - Worksheet S-10, Line 23, Column 3: Charity Care
Denominator:
  - Worksheet G-3, Line 3: Total Operating Revenue
  - Less: Provisions for bad debt
```

**Database Calculation**:
```sql
SELECT
    Provider_Number,
    Fiscal_Year,
    ((Bad_Debt + Charity_Care) / NULLIF(Net_Revenue - Provisions, 0)) * 100
        as Bad_Debt_Charity_Pct
FROM hospital_kpis
WHERE Provider_Number = ? AND Fiscal_Year = ?
```

**Improvement Levers**:
- Improve financial screening
- Reduce bad debt
- Optimize charity care policies

---

### L1-6: Current Ratio (Unrestricted)

**Category**: Liquidity
**Unit**: ratio
**Format**: .2f (e.g., "2.15")
**Higher is Better**: Yes
**Target Range**: 1.5-2.5
**Impact Score**: 9/10
**Ease of Change**: 5/10

**Description**: Short-term liquidity measuring ability to meet current obligations with current assets.

**Formula**:
```
Current Ratio = (Current Assets - Unrestricted) ÷ (Current Liabilities)
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G (Balance Sheet), Lines 1-12, Column 3 (Unrestricted)
             Sum of:
             - Line 1: Cash and cash equivalents
             - Line 2: Short-term investments
             - Line 3: Assets whose use is limited
             - Line 4: Patient accounts receivable (net)
             - Line 5: Other receivables (net)
             - Line 6: Inventory
             - Line 7: Prepaid expenses
             - Lines 8-12: Other current assets
Denominator: Worksheet G, Lines 46-58, Column 3 (Current Liabilities)
```

**Database Calculation**:
```sql
SELECT
    Provider_Number,
    Fiscal_Year,
    Current_Assets / NULLIF(Current_Liabilities, 0) as Current_Ratio
FROM hospital_kpis
WHERE Provider_Number = ? AND Fiscal_Year = ?
```

**Improvement Levers**:
- Build cash reserves
- Improve collections
- Manage payables strategically

---

## LEVEL 2 KPIs (Driver Metrics)

### Net Income Margin Drivers

#### L2-1-1: Operating Expense Ratio

**Parent**: Net Income Margin
**Unit**: %
**Format**: .1f
**Higher is Better**: No
**Target Range**: 85-95%
**Impact Score**: 9/10
**Ease of Change**: 5/10

**Formula**:
```
Operating Expense Ratio = (Total Operating Expenses) ÷ (Total Revenue) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G-3, Line 25 (Total Operating Expenses)
Denominator: Worksheet G-3, Line 3 (Total Operating Revenue)
```

**Why It Affects Parent**: Higher expenses directly erode net income

---

#### L2-1-2: Non-Operating Income %

**Parent**: Net Income Margin
**Unit**: %
**Format**: .1f
**Higher is Better**: Yes
**Target Range**: 2-5%
**Impact Score**: 7/10
**Ease of Change**: 3/10

**Formula**:
```
Non-Operating Income % =
    (Non-Operating Income) ÷ (Total Revenue + Non-Operating Income) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G-3, Line 28 (Non-Operating Income)
Denominator: Worksheet G-3, Line 3 + Line 28
```

**Why It Affects Parent**: Boosts net income beyond core operations

---

#### L2-1-3: Payer Mix - Medicare %

**Parent**: Net Income Margin
**Unit**: %
**Format**: .1f
**Higher is Better**: No
**Target Range**: 30-50%
**Impact Score**: 8/10
**Ease of Change**: 3/10

**Formula**:
```
Payer Mix - Medicare % = (Medicare Patient Days) ÷ (Total Patient Days) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet S-3, Part I, Line 14, Column 2 (Medicare Days)
Denominator: Worksheet S-3, Part I, Line 14, Column 8 (Total Days)
```

**Why It Affects Parent**: Affects revenue stability and profit margins

---

#### L2-1-4: Capital Cost % of Expenses

**Parent**: Net Income Margin
**Unit**: %
**Format**: .1f
**Higher is Better**: No
**Target Range**: 5-10%
**Impact Score**: 6/10
**Ease of Change**: 2/10

**Formula**:
```
Capital Cost % = (Capital Costs) ÷ (Total Operating Expenses) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet A, Lines 1-3, Column 7 (Sum of capital-related costs)
Denominator: Worksheet G-3, Line 25 (Total Operating Expenses)
```

**Why It Affects Parent**: High capital costs eat into margins if not managed

---

### AR Days Drivers

#### L2-2-1: Denial Rate

**Parent**: AR Days
**Unit**: %
**Format**: .1f
**Higher is Better**: No
**Target Range**: 5-10%
**Impact Score**: 8/10
**Ease of Change**: 6/10

**Formula**:
```
Denial Rate = (Total Denials) ÷ (Total Claims) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet E, Part A, Line 25 (Total Denials)
Denominator: Worksheet E, Part A, Line 1 (Total Claims)
```

**Why It Affects Parent**: Denials delay collections and increase AR days

---

#### L2-2-2: Payer Mix - Commercial %

**Parent**: AR Days
**Unit**: %
**Format**: .1f
**Higher is Better**: Yes
**Target Range**: 30-50%
**Impact Score**: 7/10
**Ease of Change**: 4/10

**Formula**:
```
Commercial % = (Commercial Patient Days) ÷ (Total Patient Days) × 100

Where Commercial Days = Total Days - (Medicare + Medicaid + Other Government)
```

**HCRIS Data Source**:
```
Numerator:   Worksheet S-3, Part I, Line 14, Column 7 - (Columns 1-6 Sum)
Denominator: Worksheet S-3, Part I, Line 14, Column 8 (Total Days)
```

**Why It Affects Parent**: Slower commercial payers increase AR days

---

#### L2-2-3: Billing Efficiency Ratio

**Parent**: AR Days
**Unit**: ratio
**Format**: .2f
**Higher is Better**: Yes
**Target Range**: 0.8-1.2
**Impact Score**: 7/10
**Ease of Change**: 6/10

**Formula**:
```
Billing Efficiency = (Total Revenue) ÷ (Adjusted Discharges)
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G-3, Line 3 (Total Operating Revenue)
Denominator: Worksheet S-3, Part I, Line 14, Column 15 (Adjusted Discharges)
```

**Why It Affects Parent**: Inefficient billing prolongs AR collection

---

#### L2-2-4: Collection Rate

**Parent**: AR Days
**Unit**: %
**Format**: .1f
**Higher is Better**: Yes
**Target Range**: 90-98%
**Impact Score**: 9/10
**Ease of Change**: 6/10

**Formula**:
```
Collection Rate = (Cash Increase) ÷ (Net Revenue) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G-1 (Cash flow statement):
             Cash + Investments increase
Denominator: Worksheet G-3, Line 3 (Total Operating Revenue)
```

**Why It Affects Parent**: Poor collections inflate AR days

---

### Operating Expense per Adjusted Discharge Drivers

#### L2-3-1: Labor Cost per Discharge

**Parent**: Operating Expense per Adjusted Discharge
**Unit**: $
**Format**: ,.0f
**Higher is Better**: No
**Target Range**: $4,000-$7,000
**Impact Score**: 9/10
**Ease of Change**: 5/10

**Formula**:
```
Labor Cost per Discharge = (Total Labor Costs) ÷ (Adjusted Discharges)
```

**HCRIS Data Source**:
```
Numerator:   Worksheet S-3, Part II, Line 1, Column 1 (Total Salaries)
Denominator: Worksheet S-3, Part I, Line 1, Column 1 (Adjusted Discharges)
```

**Why It Affects Parent**: Labor is 50-60% of total operating expenses

---

#### L2-3-2: Supply Cost per Discharge

**Parent**: Operating Expense per Adjusted Discharge
**Unit**: $
**Format**: ,.0f
**Higher is Better**: No
**Target Range**: $1,500-$3,000
**Impact Score**: 8/10
**Ease of Change**: 6/10

**Formula**:
```
Supply Cost per Discharge = (Total Supply Costs) ÷ (Adjusted Discharges)
```

**HCRIS Data Source**:
```
Numerator:   Worksheet A, Line 71, Column 7 (Medical Supplies)
Denominator: Worksheet S-3, Part I, Line 1, Column 1 (Adjusted Discharges)
```

**Why It Affects Parent**: Supplies drive variable costs per patient

---

#### L2-3-3: Overhead Allocation Ratio

**Parent**: Operating Expense per Adjusted Discharge
**Unit**: %
**Format**: .1f
**Higher is Better**: No
**Target Range**: 15-25%
**Impact Score**: 7/10
**Ease of Change**: 4/10

**Formula**:
```
Overhead Allocation Ratio = (Overhead Costs) ÷ (Total Operating Expenses) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet B, Part I, Column 26 (General Services - Sum)
Denominator: Worksheet G-3, Line 25 (Total Operating Expenses)
```

**Why It Affects Parent**: Overhead inflates per-unit costs

---

#### L2-3-4: Case Mix Index

**Parent**: Operating Expense per Adjusted Discharge
**Unit**: index
**Format**: .2f
**Higher is Better**: Yes
**Target Range**: 1.2-1.6
**Impact Score**: 8/10
**Ease of Change**: 3/10

**Formula**:
```
Case Mix Index = Average DRG Weight
```

**HCRIS Data Source**:
```
Worksheet S-3, Part I, Line 1, Column 15 (Case Mix Index)
```

**Why It Affects Parent**: Higher acuity raises expenses per discharge

---

### Medicare CCR Drivers

#### L2-4-1: Ancillary Cost Ratio

**Parent**: Medicare CCR
**Unit**: ratio
**Format**: .3f
**Higher is Better**: No
**Target Range**: 0.15-0.35
**Impact Score**: 7/10
**Ease of Change**: 5/10

**Formula**:
```
Ancillary Cost Ratio = (Ancillary Costs) ÷ (Total Costs)
```

**HCRIS Data Source**:
```
Numerator:   Worksheet C, Part I, Lines 50-76, Column 5 (Ancillary cost centers)
Denominator: Worksheet C, Part I, Column 5 Total (All cost centers)
```

**Why It Affects Parent**: Ancillary services drive CCR variability

---

#### L2-4-2: Charge Inflation Rate

**Parent**: Medicare CCR
**Unit**: %
**Format**: .1f
**Higher is Better**: Yes
**Target Range**: 2-5%
**Impact Score**: 6/10
**Ease of Change**: 6/10

**Formula**:
```
Charge Inflation Rate =
    ((Current Year Charges - Prior Year Charges) ÷ Prior Year Charges) × 100
```

**HCRIS Data Source**:
```
Year-over-Year change in:
Worksheet C, Part I, Column 8 Sum (Total Charges)
```

**Why It Affects Parent**: Rising charges lower CCR if costs lag behind

---

#### L2-4-3: Adjustment Impact on Costs

**Parent**: Medicare CCR
**Unit**: %
**Format**: .1f
**Higher is Better**: No
**Target Range**: 1-5%
**Impact Score**: 6/10
**Ease of Change**: 4/10

**Formula**:
```
Adjustment Impact = (Total Adjustments) ÷ (Total Costs) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet A-8, Column 2 (Sum of all adjustments)
Denominator: Worksheet C, Part I, Column 5 Sum (Total Costs)
```

**Why It Affects Parent**: Adjustments reduce allowable costs, raising CCR

---

#### L2-4-4: Utilization Mix

**Parent**: Medicare CCR
**Unit**: ratio
**Format**: .2f
**Higher is Better**: Yes
**Target Range**: 0.4-0.6
**Impact Score**: 7/10
**Ease of Change**: 4/10

**Formula**:
```
Utilization Mix =
    (Outpatient Visits) ÷ (Total Adjusted Encounters)

Where Total Adjusted Encounters =
    Inpatient Discharges + (Outpatient Visits adjusted)
```

**HCRIS Data Source**:
```
Numerator:   Worksheet S-3, Part I, Line 15, Column 1 (OP Visits)
Denominator: Worksheet S-3, Part I:
             Line 1, Column 1 + Line 15, Column 1 (adjusted)
```

**Why It Affects Parent**: Shift to outpatient affects aggregate CCR

---

### Bad Debt + Charity % Drivers

#### L2-5-1: Charity Care Charge Ratio

**Parent**: Bad Debt + Charity %
**Unit**: %
**Format**: .1f
**Higher is Better**: No
**Target Range**: 2-6%
**Impact Score**: 7/10
**Ease of Change**: 5/10

**Formula**:
```
Charity Care Charge Ratio = (Charity Care Charges) ÷ (Total Charges) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet S-10, Line 20, Column 3 (Charity Care Charges)
Denominator: Worksheet C, Part I, Column 8 Sum (Total Charges)
```

**Why It Affects Parent**: High charity care increases uncompensated care %

---

#### L2-5-2: Bad Debt Recovery Rate

**Parent**: Bad Debt + Charity %
**Unit**: %
**Format**: .1f
**Higher is Better**: Yes
**Target Range**: 10-30%
**Impact Score**: 7/10
**Ease of Change**: 6/10

**Formula**:
```
Bad Debt Recovery Rate = (Bad Debt Recovered) ÷ (Total Bad Debt) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet S-10, Line 26 (Bad Debt Recovered)
Denominator: Worksheet S-10, Line 25 (Total Bad Debt)
```

**Why It Affects Parent**: Low recoveries inflate bad debt percentage

---

#### L2-5-3: Uninsured Patient %

**Parent**: Bad Debt + Charity %
**Unit**: %
**Format**: .1f
**Higher is Better**: No
**Target Range**: 5-15%
**Impact Score**: 8/10
**Ease of Change**: 4/10

**Formula**:
```
Uninsured Patient % = (Uninsured Encounters) ÷ (Total Encounters) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet S-10, Line 20, Column 1 + Line 31 (Uninsured)
Denominator: Worksheet S-3, Part I, Line 14, Column 8 (Total Patient Days)
```

**Why It Affects Parent**: Uninsured patients drive charity care and bad debt

---

#### L2-5-4: Medicaid Shortfall %

**Parent**: Bad Debt + Charity %
**Unit**: %
**Format**: .1f
**Higher is Better**: No
**Target Range**: 0-5%
**Impact Score**: 7/10
**Ease of Change**: 3/10

**Formula**:
```
Medicaid Shortfall % =
    ((Medicaid Cost - Medicaid Payment) ÷ Total Revenue) × 100
```

**HCRIS Data Source**:
```
Numerator Components:
  - Worksheet S-10, Line 18 (Medicaid Cost)
  - Worksheet S-10, Line 19 (Medicaid Payment)
Denominator: Worksheet G-3, Line 3 (Total Revenue)
```

**Why It Affects Parent**: Payment shortfalls add to uncompensated care load

---

### Current Ratio Drivers

#### L2-6-1: Cash + Equivalents % of Assets

**Parent**: Current Ratio
**Unit**: %
**Format**: .1f
**Higher is Better**: Yes
**Target Range**: 10-30%
**Impact Score**: 8/10
**Ease of Change**: 5/10

**Formula**:
```
Cash % of Assets = (Cash + Marketable Securities) ÷ (Total Assets) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G, Balance Sheet:
             Line 1 + Line 2 (Cash + Short-term investments), Column 3
Denominator: Worksheet G, Line 59, Column 3 (Total Assets)
```

**Why It Affects Parent**: Boosts current assets for better liquidity

---

#### L2-6-2: Current Liabilities Ratio

**Parent**: Current Ratio
**Unit**: %
**Format**: .1f
**Higher is Better**: No
**Target Range**: 20-40%
**Impact Score**: 7/10
**Ease of Change**: 5/10

**Formula**:
```
Current Liabilities Ratio = (Current Liabilities) ÷ (Total Liabilities) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G, Lines 46-58, Column 3 Sum (Current Liabilities)
Denominator: Worksheet G, Line 75, Column 3 (Total Liabilities)
```

**Why It Affects Parent**: High current liabilities strain liquidity ratio

---

#### L2-6-3: Inventory Turnover

**Parent**: Current Ratio
**Unit**: ratio
**Format**: .1f
**Higher is Better**: Yes
**Target Range**: 20-40
**Impact Score**: 6/10
**Ease of Change**: 6/10

**Formula**:
```
Inventory Turnover = (Supply Expense) ÷ (Average Inventory)
```

**HCRIS Data Source**:
```
Numerator:   Worksheet A, Line 71, Column 2 (Supplies Expense)
Denominator: Worksheet G, Inventory (Average of beginning and ending)
```

**Why It Affects Parent**: Low turnover ties up current assets

---

#### L2-6-4: Fund Balance % Change

**Parent**: Current Ratio
**Unit**: %
**Format**: .1f
**Higher is Better**: Yes
**Target Range**: 2-8%
**Impact Score**: 7/10
**Ease of Change**: 4/10

**Formula**:
```
Fund Balance % Change =
    (Change in Fund Balance) ÷ (Beginning Fund Balance) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G-1, Line 21, Column 3 (Change in Fund Balance)
Denominator: Worksheet G, Line 70, Column 3 Beginning (Fund Balance)
```

**Why It Affects Parent**: Positive changes build reserves and strengthen liquidity

---

## LEVEL 3 KPIs (Sub-Driver Metrics)

_Due to length constraints, here are selected Level 3 KPIs. All 48 are fully defined in `kpi_hierarchy_config.py`._

### Operating Expense Ratio Sub-Drivers

#### L3-1-1-1: FTE per Bed

**Parent**: Operating Expense Ratio
**Unit**: ratio
**Format**: .2f
**Higher is Better**: No

**Formula**:
```
FTE per Bed = (Total FTEs) ÷ (Total Beds)
```

**HCRIS Data Source**:
```
Numerator:   Worksheet S-3, Part I, Line 14, Column 6 (Total FTEs)
Denominator: Worksheet S-3, Part I, Line 7, Column 1 (Total Beds)
```

---

#### L3-1-1-2: Salary % of Total Expenses

**Parent**: Operating Expense Ratio
**Unit**: %
**Format**: .1f
**Higher is Better**: No

**Formula**:
```
Salary % = (Total Salaries) ÷ (Total Operating Expenses) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet S-3, Part II, Line 1, Column 1 (Total Salaries)
Denominator: Worksheet G-3, Line 25 (Total Operating Expenses)
```

---

### Non-Operating Income % Sub-Drivers

#### L3-1-2-1: Investment Income Share

**Parent**: Non-Operating Income %
**Unit**: %
**Format**: .1f
**Higher is Better**: Yes

**Formula**:
```
Investment Income Share = (Investment Income) ÷ (Non-Operating Income) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G-1, Line 5, Column 3 (Investment Income)
Denominator: Worksheet G-3, Line 28 (Total Non-Operating Income)
```

---

#### L3-1-2-2: Donation/Grant %

**Parent**: Non-Operating Income %
**Unit**: %
**Format**: .1f
**Higher is Better**: Yes

**Formula**:
```
Donation/Grant % = (Donations + Grants) ÷ (Non-Operating Income) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G-1, Line 6, Column 3 (Donations and Grants)
Denominator: Worksheet G-3, Line 28 (Total Non-Operating Income)
```

---

### Capital Cost % of Expenses Sub-Drivers

#### L3-1-4-1: Depreciation % of Capital

**Parent**: Capital Cost % of Expenses
**Unit**: %
**Format**: .1f
**Higher is Better**: No

**Formula**:
```
Depreciation % = (Depreciation) ÷ (Total Capital Costs) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet A-7, Part I, Column 9 (Depreciation)
Denominator: Worksheet A-7, Part I, Column 1 (Total Capital Costs)
```

---

#### L3-1-4-2: Interest Expense Ratio

**Parent**: Capital Cost % of Expenses
**Unit**: %
**Format**: .1f
**Higher is Better**: No

**Formula**:
```
Interest Expense Ratio = (Interest Expense) ÷ (Total Capital Costs) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet A, Line 116, Column 2 (Interest Expense)
Denominator: Worksheet A, Lines 1-3, Column 7 Sum (Capital Costs)
```

---

### Current Liabilities Ratio Sub-Drivers

#### L3-6-2-1: Accounts Payable %

**Parent**: Current Liabilities Ratio
**Unit**: %
**Format**: .1f
**Higher is Better**: No

**Formula**:
```
Accounts Payable % = (Accounts Payable) ÷ (Current Liabilities) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G, Line 47, Column 3 (Accounts Payable)
Denominator: Worksheet G, Lines 46-58 Sum (Current Liabilities)
```

---

#### L3-6-2-2: Short-Term Debt %

**Parent**: Current Liabilities Ratio
**Unit**: %
**Format**: .1f
**Higher is Better**: No

**Formula**:
```
Short-Term Debt % = (Short-Term Debt) ÷ (Current Liabilities) × 100
```

**HCRIS Data Source**:
```
Numerator:   Worksheet G, Line 46, Column 3 (Short-term debt)
Denominator: Worksheet G, Lines 46-58 Sum (Current Liabilities)
```

---

## Data Sources and Origins

### CMS HCRIS Worksheets

The application uses data from the following CMS Form 2552-10 worksheets:

#### Worksheet A - Reclassification and Adjustment of Trial Balance
- **Lines 1-200**: Expense reclassifications
- **Column 7**: Final adjusted expenses
- **Usage**: Operating expenses, supply costs, depreciation, interest

#### Worksheet A-7 - Depreciation
- **Part I**: Depreciation calculations
- **Column 9**: Depreciation expense
- **Column 1**: Depreciable assets

#### Worksheet A-8 - Adjustments to Expenses
- **Column 2**: Cost adjustments
- **Usage**: Non-allowable cost adjustments affecting CCR

#### Worksheet B - Cost Allocation - General Service Costs
- **Part I**: Cost center allocations
- **Column 26**: General services allocations
- **Usage**: Overhead cost allocation

#### Worksheet C - Cost Allocation - Statistical Basis
- **Part I**: Cost-to-charge ratios
- **Column 5**: Costs by cost center
- **Column 6**: Inpatient charges
- **Column 7**: Outpatient charges
- **Column 8**: Total charges
- **Lines 50-76**: Ancillary services

#### Worksheet D - Computation of Reimbursable Costs
- **Part V**: Revenue by payer
- **Column 2**: Medicare outpatient revenue
- **Usage**: Payer mix analysis

#### Worksheet E - Computation of Medicare Reimbursement
- **Part A**: Claims and denials
- **Line 1**: Total claims
- **Line 4**: Medicare claims
- **Line 25**: Total denials
- **Line 64**: Medicare bad debt

#### Worksheet G - Balance Sheet
- **Lines 1-12**: Current assets (Column 3 for unrestricted)
  - Line 1: Cash and cash equivalents
  - Line 2: Short-term investments
  - Line 4: Patient accounts receivable
  - Line 6: Inventory
- **Lines 46-58**: Current liabilities
  - Line 46: Short-term debt
  - Line 47: Accounts payable
- **Line 59**: Total assets
- **Line 70**: Fund balance (beginning)
- **Line 73**: Retained earnings
- **Line 75**: Total liabilities
- **Column 100**: Beginning of year
- **Column 200**: End of year
- **Column 3**: Unrestricted funds

#### Worksheet G-1 - Statement of Changes in Fund Balance
- **Line 1, Column 3**: Cash from operations
- **Line 3, Column 3**: Depreciation (non-cash)
- **Line 5, Column 3**: Investment income
- **Line 6, Column 3**: Donations and grants
- **Line 21, Column 3**: Change in fund balance

#### Worksheet G-2 - Statement of Patient Revenue
- **Part I**: Revenue details
- **Column 3**: Total revenue amounts

#### Worksheet G-3 - Statement of Revenues and Expenses
- **Line 2**: Gross patient revenue
- **Line 3**: Net patient revenue (Total Operating Revenue)
- **Line 25**: Total operating expenses
- **Line 28**: Non-operating income
- **Line 29**: Net income

#### Worksheet S-3 - Hospital Statistical Data
- **Part I - Utilization**:
  - Line 1, Column 1: Total discharges
  - Line 1, Column 15: Case Mix Index (CMI)
  - Line 7, Column 1: Total beds
  - Line 8, Column 2: Medicare inpatient days
  - Line 8, Column 8: Total inpatient days
  - Line 14, Column 2: Medicare patient days
  - Line 14, Column 5+6: Medicaid patient days
  - Line 14, Column 7: Other payer days
  - Line 14, Column 8: Total patient days
  - Line 14, Column 15: Adjusted discharges
  - Line 15, Column 1: Outpatient visits
- **Part II - Staffing**:
  - Line 1, Column 1: Total salaries
  - Line 1, Column 2: Total hours
  - Line 10, Column 2: Overtime hours
- **Part III**:
  - Line 14, Column 6: Total FTEs
- **Part V**:
  - Line 11, Column 1: Contract labor costs

#### Worksheet S-10 - Uncompensated Care and Bad Debt
- **Line 18**: Medicaid cost
- **Line 19**: Medicaid payment
- **Line 20, Column 1**: Non-covered charity care
- **Line 20, Column 2**: Insured charity care
- **Line 20, Column 3**: Total charity care charges
- **Line 23, Column 3**: Charity care costs
- **Line 25**: Total bad debt
- **Line 26**: Bad debt recovered
- **Line 29, Column 3**: Total bad debt expense
- **Line 31**: Uninsured self-pay

---

## Data Flow Architecture

### Overall Data Flow

```
┌──────────────────────────────────────────────────────────┐
│ 1. CMS HCRIS Source Data (CSV Files)                     │
│    - 5 fiscal years (2020-2024)                          │
│    - 25+ worksheets per hospital                         │
│    - Raw format from CMS                                 │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│ 2. ETL Pipeline (etl/ directory)                         │
│    - create_duckdb_tables.py: Load CSVs → DuckDB        │
│    - create_*.py scripts: Transform to long format      │
│    - Output: Parquet files in data/db_parquets/         │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│ 3. Database Build (scripts/build_database.py)           │
│    - Read all parquet files                              │
│    - Calculate all 78 KPIs for all hospitals/years      │
│    - Compute 4-level benchmarks (National/State/Type)   │
│    - Create indexes on Provider_Number, Fiscal_Year     │
│    - Output: hospital_analytics.duckdb (~3.5 GB)        │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│ 4. Application Runtime (dashboard.py)                    │
│    - Read-only connection to hospital_analytics.duckdb  │
│    - Sub-100ms queries using indexes                    │
│    - Generate visualizations with Plotly                │
│    - Serve via Dash web framework                       │
└──────────────────────────────────────────────────────────┘
```

### Detailed ETL Process

```
Source CSV Files (data/source_data/HOSP10FY20XX/)
├── HOSP10FY2020_NMRC.CSV    (Numeric data)
├── HOSP10FY2020_ALPHA.CSV   (Alpha data)
├── HOSP10FY2020_RPT.CSV     (Report metadata)
└── HOSP10FY2020_ROLLUP.CSV  (Rollup data)
                 │
                 ▼
         [create_duckdb_tables.py]
         Creates source tables:
         - nmrc_source (numeric data by worksheet/line/column)
         - alpha_source (text data)
         - rpt_source (report periods)
                 │
                 ▼
         [Transformation Scripts]
         ├── create_balance_sheet.py → balance_sheet_long/
         ├── create_revenue.py → revenue_long/
         ├── create_revenue_expenses.py → revenue_expenses_long/
         ├── create_costs_a000.py → costs_a000_long/
         ├── create_costs_b100.py → costs_b100_long/
         ├── create_income_statement.py → income_statement_long/
         ├── create_expense_detail.py → expense_detail/
         └── create_fund_balance_changes.py → fund_balance_changes_long/
                 │
                 ▼
         Parquet Files (data/db_parquets/)
         - Partitioned by fiscal year
         - Long format (Provider, Year, Line, Column, Value)
         - Columnar storage for fast analytics
                 │
                 ▼
         [build_database.py]
         Aggregates and computes:
         1. hospital_kpis table (all 78 KPIs calculated)
         2. hospital_benchmarks (4 levels: National/State/Type/State+Type)
         3. hospital_metadata (CCN, state, type, bed count)
         4. Indexed financial statement tables
                 │
                 ▼
         hospital_analytics.duckdb
         - 27,000+ hospital-year records
         - Pre-computed KPIs
         - Pre-computed benchmarks
         - Optimized for <100ms queries
```

### Query Execution Flow

```
User selects hospital in dashboard
         │
         ▼
Dashboard calls HospitalDataManager.calculate_kpis(ccn, fiscal_year)
         │
         ▼
Execute indexed query:
SELECT * FROM hospital_kpis
WHERE Provider_Number = ? AND Fiscal_Year = ?
         │
         ▼
Returns row with all 78 KPI values (pre-computed)
         │
         ▼
Dashboard calls HospitalDataManager.get_benchmark_data(state, type)
         │
         ▼
Execute benchmark queries (4 queries in parallel):
1. National benchmarks
2. State benchmarks
3. Hospital type benchmarks
4. State + hospital type benchmarks
         │
         ▼
Returns P25, Median, P75, Mean for each KPI at each level
         │
         ▼
Create KPI cards with:
- Current value
- 5-year trend
- Benchmark comparison (quartile position)
- Sparkline visualization
         │
         ▼
Render in browser (<100ms total query time)
```

---

## Database Schema

### Main Tables

#### 1. hospital_kpis

**Purpose**: Pre-computed KPI values for all hospitals and years

**Schema**:
```sql
CREATE TABLE hospital_kpis (
    Provider_Number VARCHAR,
    Fiscal_Year INTEGER,
    State_Code VARCHAR,
    Hospital_Type VARCHAR,

    -- Level 1 KPIs (6)
    Net_Income_Margin DOUBLE,
    AR_Days DOUBLE,
    Operating_Expense_per_Adjusted_Discharge DOUBLE,
    Medicare_CCR DOUBLE,
    Bad_Debt_Charity_Pct DOUBLE,
    Current_Ratio DOUBLE,

    -- Level 2 KPIs (24) - example subset
    Operating_Expense_Ratio DOUBLE,
    Non_Operating_Income_Pct DOUBLE,
    Payer_Mix_Medicare_Pct DOUBLE,
    Capital_Cost_Pct_of_Expenses DOUBLE,
    Denial_Rate DOUBLE,
    Payer_Mix_Commercial_Pct DOUBLE,
    Billing_Efficiency_Ratio DOUBLE,
    Collection_Rate DOUBLE,
    -- ... (20 more Level 2 KPIs)

    -- Level 3 KPIs (48) - example subset
    FTE_per_Bed DOUBLE,
    Salary_Pct_of_Expenses DOUBLE,
    Investment_Income_Share DOUBLE,
    Donation_Grant_Pct DOUBLE,
    -- ... (44 more Level 3 KPIs)

    -- Base calculation components
    Total_Revenue DOUBLE,
    Net_Income DOUBLE,
    Total_Operating_Expenses DOUBLE,
    Current_Assets DOUBLE,
    Current_Liabilities DOUBLE,
    Net_Patient_AR DOUBLE,
    -- ... (additional base values)

    PRIMARY KEY (Provider_Number, Fiscal_Year)
);

CREATE INDEX idx_hospital_kpis_provider ON hospital_kpis(Provider_Number);
CREATE INDEX idx_hospital_kpis_year ON hospital_kpis(Fiscal_Year);
CREATE INDEX idx_hospital_kpis_state ON hospital_kpis(State_Code);
CREATE INDEX idx_hospital_kpis_type ON hospital_kpis(Hospital_Type);
```

**Record Count**: ~27,000 (6,000+ hospitals × 5 years - some missing)

---

#### 2. hospital_benchmarks

**Purpose**: Pre-computed benchmark statistics at 4 levels

**Schema**:
```sql
CREATE TABLE hospital_benchmarks (
    Benchmark_Level VARCHAR,  -- 'National', 'State', 'Hospital_Type', 'State_Hospital_Type'
    State_Code VARCHAR,       -- NULL for National and Hospital_Type levels
    Hospital_Type VARCHAR,    -- NULL for National and State levels
    Fiscal_Year INTEGER,
    KPI_Name VARCHAR,

    -- Benchmark statistics
    P25 DOUBLE,              -- 25th percentile
    Median DOUBLE,           -- 50th percentile (median)
    P75 DOUBLE,              -- 75th percentile
    Mean DOUBLE,             -- Arithmetic mean
    Count INTEGER,           -- Number of hospitals in benchmark
    Std_Dev DOUBLE,          -- Standard deviation

    PRIMARY KEY (Benchmark_Level, State_Code, Hospital_Type, Fiscal_Year, KPI_Name)
);
```

**Benchmark Levels**:
1. **National**: All hospitals nationwide
2. **State**: All hospitals in a specific state
3. **Hospital_Type**: All hospitals of a specific type (Short Term, CAH, etc.)
4. **State_Hospital_Type**: Hospitals of specific type within specific state (most specific)

---

#### 3. hospital_metadata

**Purpose**: Hospital classification and reference data

**Schema**:
```sql
CREATE TABLE hospital_metadata (
    Provider_Number VARCHAR PRIMARY KEY,
    Hospital_Name VARCHAR,
    State_Code VARCHAR,
    State_Name VARCHAR,
    Hospital_Type VARCHAR,
    Urban_Rural VARCHAR,
    Bed_Count INTEGER,
    Teaching_Status VARCHAR,
    DSH_Percentage DOUBLE,
    First_Fiscal_Year INTEGER,
    Last_Fiscal_Year INTEGER
);
```

---

#### 4. Financial Statement Tables

All financial tables follow similar long-format structure:

##### balance_sheet_long
```sql
CREATE TABLE balance_sheet_long (
    Provider_Number VARCHAR,
    Fiscal_Year INTEGER,
    Line VARCHAR,
    "Column" VARCHAR,
    line_level1 VARCHAR,
    line_level2 VARCHAR,
    col_level1 VARCHAR,
    Value DOUBLE,

    PRIMARY KEY (Provider_Number, Fiscal_Year, Line, "Column")
);

CREATE INDEX idx_balance_provider_year ON balance_sheet_long(Provider_Number, Fiscal_Year);
```

##### revenue_long
```sql
CREATE TABLE revenue_long (
    Provider_Number VARCHAR,
    Fiscal_Year INTEGER,
    Line VARCHAR,
    "Column" VARCHAR,
    line_level1 VARCHAR,
    Value DOUBLE,

    PRIMARY KEY (Provider_Number, Fiscal_Year, Line, "Column")
);
```

##### revenue_expenses_long
```sql
CREATE TABLE revenue_expenses_long (
    Provider_Number VARCHAR,
    Fiscal_Year INTEGER,
    Line VARCHAR,
    "Column" VARCHAR,
    line_level1 VARCHAR,
    Value DOUBLE,

    PRIMARY KEY (Provider_Number, Fiscal_Year, Line, "Column")
);
```

##### costs_a000_long
```sql
CREATE TABLE costs_a000_long (
    Provider_Number VARCHAR,
    Fiscal_Year INTEGER,
    Line VARCHAR,
    "Column" VARCHAR,
    line_level1 VARCHAR,
    line_level2 VARCHAR,
    Value DOUBLE,

    PRIMARY KEY (Provider_Number, Fiscal_Year, Line, "Column")
);
```

##### costs_b100_long
```sql
CREATE TABLE costs_b100_long (
    Provider_Number VARCHAR,
    Fiscal_Year INTEGER,
    Line VARCHAR,
    "Column" VARCHAR,
    line_level1 VARCHAR,
    Value DOUBLE,

    PRIMARY KEY (Provider_Number, Fiscal_Year, Line, "Column")
);
```

##### income_statement_long
```sql
CREATE TABLE income_statement_long (
    Provider_Number VARCHAR,
    Fiscal_Year INTEGER,
    Line VARCHAR,
    Section VARCHAR,
    Subsection VARCHAR,
    Line_Name VARCHAR,
    Value DOUBLE,

    PRIMARY KEY (Provider_Number, Fiscal_Year, Line)
);
```

##### expense_detail
```sql
CREATE TABLE expense_detail (
    Provider_Number VARCHAR,
    Fiscal_Year INTEGER,
    Expense_Category VARCHAR,
    Category_Description VARCHAR,
    Category_Type VARCHAR,
    Column_Description VARCHAR,
    Value DOUBLE
);
```

---

## Component Details

### HospitalDataManager Class

**Location**: `dashboard.py`

**Purpose**: Central data access layer managing all database operations

**Key Methods**:

```python
class HospitalDataManager:
    """Manages hospital data and KPI calculations"""

    def __init__(self, db_path='hospital_analytics.duckdb'):
        """Initialize with database path"""

    def get_connection(self):
        """Create read-only DuckDB connection"""

    def get_hospital_list(self):
        """
        Retrieve list of all hospitals with metadata
        Returns: DataFrame with Provider_Number, Hospital_Name, State, Type
        """

    def calculate_kpis(self, ccn, fiscal_year=None):
        """
        Get pre-computed KPIs for hospital
        Args:
            ccn: Provider number (string)
            fiscal_year: Specific year or None for all years
        Returns: DataFrame with all 78 KPIs
        """

    def get_benchmark_data(self, state_code, hospital_type, fiscal_year):
        """
        Retrieve 4-level benchmark statistics
        Args:
            state_code: Two-digit state code
            hospital_type: Hospital classification
            fiscal_year: Year for benchmarks
        Returns: Dict with 4 benchmark levels
        """

    def load_financial_data(self, table_name, ccn, fiscal_year=None):
        """
        Load financial statement data
        Args:
            table_name: 'balance_sheet_long', 'revenue_long', etc.
            ccn: Provider number
            fiscal_year: Specific year or None for all
        Returns: DataFrame in long format
        """

    def pivot_to_wide_format(self, df, value_col='Value'):
        """
        Convert long format to wide format for display
        Args:
            df: Long format DataFrame
            value_col: Column containing values
        Returns: Wide format DataFrame (years as columns)
        """
```

---

### KPI Card Components

**Location**: `components/kpi_cards.py`

#### create_enhanced_level1_kpi_card()

**Purpose**: Create enhanced Level 1 KPI card with all features

**Parameters**:
```python
def create_enhanced_level1_kpi_card(
    kpi_key,                # KPI identifier (e.g., 'Net_Income_Margin')
    kpi_value,              # Current value
    kpi_trend_values,       # List of 5 historical values
    fiscal_years,           # List of 5 years
    all_benchmarks,         # Dict with 4 benchmark levels
    rank,                   # KPI priority rank (1-6)
    l2_kpis=None,          # Level 2 KPI values (optional)
    l3_kpis=None,          # Level 3 KPI values (optional)
    ccn=None,              # Provider number
    fiscal_year=None,      # Current fiscal year
    db_column=None,        # DB column name
    data_manager=None,     # Data manager instance
    kpi_data_df=None       # KPI data DataFrame
):
```

**Returns**: Dash Bootstrap Card component with:
- KPI name and description
- Current value with year-over-year trend
- 5-year historical values (color-coded by quartile)
- Benchmark comparison table (4 levels)
- Quartile position for last 2 years
- Drill-down button to Level 2 drivers

---

#### create_historical_quartile_table()

**Purpose**: Create color-coded historical values table

**Color Coding**:
- **Green** (Top Quartile): Best performance
- **Light Blue** (Above Median): Good performance
- **Yellow** (Below Median): Needs improvement
- **Red** (Bottom Quartile): Urgent attention needed

**Logic adjusts for "higher_is_better" direction**

---

### KPI Calculation Helpers

**Location**: `utils/kpi_helpers.py`

#### calculate_percentile_rank()

```python
def calculate_percentile_rank(value, p25, median, p75):
    """
    Determine which quartile the value falls into

    Args:
        value: Hospital's KPI value
        p25: 25th percentile benchmark
        median: 50th percentile benchmark
        p75: 75th percentile benchmark

    Returns:
        (label, color) tuple:
        - ('Bottom Quartile', 'danger') if value <= p25
        - ('Below Median', 'warning') if p25 < value <= median
        - ('Above Median', 'info') if median < value <= p75
        - ('Top Quartile', 'success') if value > p75
    """
```

#### calculate_trend()

```python
def calculate_trend(values):
    """
    Calculate year-over-year trend

    Args:
        values: List of historical values (most recent first)

    Returns:
        (direction, pct_change) tuple:
        - direction: 'up', 'down', or 'stable'
        - pct_change: Percentage change from previous year

    Stable threshold: ±2%
    """
```

#### calculate_dynamic_priority()

```python
def calculate_dynamic_priority(kpi_key, hospital_value, benchmark_median, higher_is_better):
    """
    Calculate dynamic priority score based on performance gap

    Formula:
        base_importance = impact_score × ease_of_change
        gap_pct = |hospital_value - benchmark| / benchmark
        gap_multiplier = 1 + min(gap_pct/100, 0.5) if underperforming else 0.5
        priority = base_importance × gap_multiplier

    Returns: Priority score (0-1000)
    """
```

---

## ETL Pipeline

### Pipeline Overview

The ETL (Extract, Transform, Load) pipeline transforms raw CMS HCRIS CSV files into optimized analytical structures.

### Step-by-Step Process

#### Step 1: Create Source Tables

**Script**: `etl/create_duckdb_tables.py`

**Purpose**: Load raw CMS CSV files into DuckDB tables

**Input**:
```
data/source_data/HOSP10FY20XX/
├── HOSP10FY20XX_NMRC.CSV    (~500 MB each)
├── HOSP10FY20XX_ALPHA.CSV
├── HOSP10FY20XX_RPT.CSV
└── HOSP10FY20XX_ROLLUP.CSV
```

**Output Tables**:
- `nmrc_source`: All numeric data (worksheet, line, column, value)
- `alpha_source`: All text data
- `rpt_source`: Report periods and metadata

**Execution**:
```bash
cd etl
python create_duckdb_tables.py
```

---

#### Step 2: Transform Balance Sheet

**Script**: `etl/create_balance_sheet.py`

**Purpose**: Extract and transform Worksheet G (Balance Sheet)

**Transformation Logic**:
```sql
-- Extract specific lines for balance sheet
SELECT
    Provider_Number,
    Fiscal_Year,
    Line,
    "Column",
    line_level1,
    line_level2,
    col_level1,
    Value
FROM nmrc_source
WHERE Worksheet = 'G000000'
    AND Line IN ('00100', '00101', '00102', ...) -- Asset and liability lines
ORDER BY Provider_Number, Fiscal_Year, Line, "Column"
```

**Output**: `data/db_parquets/balance_sheet_long/` (partitioned by fiscal_year)

---

#### Step 3: Transform Revenue

**Script**: `etl/create_revenue.py`

**Purpose**: Extract Worksheet G-2 (Revenue Detail)

**Output**: `data/db_parquets/revenue_long/`

---

#### Step 4: Transform Revenue & Expenses

**Script**: `etl/create_revenue_expenses.py`

**Purpose**: Extract Worksheet G-3 (Income Statement)

**Key Lines**:
- Line 2: Gross patient revenue
- Line 3: Net patient revenue
- Line 25: Total operating expenses
- Line 28: Non-operating income
- Line 29: Net income

**Output**: `data/db_parquets/revenue_expenses_long/`

---

#### Step 5a: Transform Costs - Schedule A

**Script**: `etl/create_costs_a000.py`

**Purpose**: Extract Worksheet A (Expense Reclassification)

**Key Columns**:
- Column 7: Final adjusted expenses by cost center

**Output**: `data/db_parquets/costs_a000_long/`

---

#### Step 5b: Transform Costs - Schedule B-1

**Script**: `etl/create_costs_b100.py`

**Purpose**: Extract Worksheet B-1 (Cost Allocation)

**Output**: `data/db_parquets/costs_b100_long/`

---

#### Step 6: Build Optimized Database

**Script**: `scripts/build_database.py`

**Purpose**: Create pre-computed analytical database

**Process**:

1. **Load all parquet files**
   ```python
   balance_df = pd.read_parquet('data/db_parquets/balance_sheet_long/')
   revenue_df = pd.read_parquet('data/db_parquets/revenue_long/')
   # ... etc
   ```

2. **Calculate all 78 KPIs** for each hospital-year combination
   ```python
   for provider in providers:
       for year in years:
           kpis = calculate_all_kpis(provider, year)
           # Result: One row with 78 KPI columns
   ```

3. **Compute benchmarks** at 4 levels
   ```python
   # National benchmarks
   national_benchmarks = kpis_df.groupby('Fiscal_Year').agg({
       'Net_Income_Margin': ['quantile(0.25)', 'median', 'quantile(0.75)', 'mean'],
       # ... for all 78 KPIs
   })

   # State benchmarks
   state_benchmarks = kpis_df.groupby(['State_Code', 'Fiscal_Year']).agg(...)

   # Hospital type benchmarks
   type_benchmarks = kpis_df.groupby(['Hospital_Type', 'Fiscal_Year']).agg(...)

   # State + Type benchmarks (most specific)
   state_type_benchmarks = kpis_df.groupby(['State_Code', 'Hospital_Type', 'Fiscal_Year']).agg(...)
   ```

4. **Create indexes** for fast queries
   ```sql
   CREATE INDEX idx_kpis_provider ON hospital_kpis(Provider_Number);
   CREATE INDEX idx_kpis_year ON hospital_kpis(Fiscal_Year);
   CREATE INDEX idx_kpis_state ON hospital_kpis(State_Code);
   CREATE INDEX idx_kpis_type ON hospital_kpis(Hospital_Type);
   ```

5. **Write to DuckDB**
   ```python
   con = duckdb.connect('hospital_analytics.duckdb')
   con.execute("CREATE TABLE hospital_kpis AS SELECT * FROM kpis_df")
   con.execute("CREATE TABLE hospital_benchmarks AS SELECT * FROM benchmarks_df")
   # ... etc
   ```

**Output**: `hospital_analytics.duckdb` (~3.5 GB)

**Execution Time**: 20-40 minutes (one-time setup)

**Execution**:
```bash
cd scripts
python build_database.py
```

---

## Authentication System

**Location**: `auth_manager.py`, `auth_models.py`, `auth_components.py`

### Account Types

1. **Company**: Organizations with multiple employees
2. **Employee**: Users belonging to a company
3. **Individual**: Independent users

### Authentication Flow

```
User visits app → Login page
    │
    ├─ Has account? → Login
    │   ├─ Validate credentials
    │   ├─ Create session
    │   └─ Redirect to dashboard
    │
    └─ No account? → Register
        ├─ Choose account type
        ├─ Create account
        ├─ Create session
        └─ Redirect to dashboard
```

### Session Management

- **Storage**: SQLite database (`data/auth.db`)
- **Session Duration**: 24 hours
- **Cleanup**: Automatic on startup
- **Security**: Password hashing with bcrypt

### Deployment

The authentication system enables:
- Multi-tenant deployment
- Usage tracking
- Access control
- Cloud deployment (Render, Railway, Fly.io)

---

## Performance Characteristics

### Query Performance

**Without Pre-Computed Database**:
- KPI calculation: 5-30 seconds per hospital
- Benchmark calculation: 10-60 seconds
- Financial statements: 2-5 seconds

**With Pre-Computed Database**:
- KPI retrieval: 10-50 ms
- Benchmark retrieval: 20-100 ms (4 queries)
- Financial statements: 50-200 ms
- **Total page load**: < 500 ms

### Performance Optimization Strategies

1. **Pre-Computation**: All KPIs calculated once during DB build
2. **Columnar Storage**: DuckDB's columnar format optimizes analytics
3. **Indexing**: B-tree indexes on Provider_Number and Fiscal_Year
4. **Partitioning**: Parquet files partitioned by fiscal year
5. **Read-Only Connections**: Allows concurrent user access
6. **Caching**: Benchmark data cached in memory

---

## Deployment Architecture

### Local Development

```bash
# Clone repository
git clone <repo-url>
cd Hospital-Dashboard

# Install dependencies
pip install -r requirements.txt

# Run without authentication
python dashboard.py

# Run with authentication
python app.py
```

### Cloud Deployment

**Supported Platforms**:
- Render (recommended for free tier)
- Railway
- Fly.io
- Heroku

**Deployment Files**:
- `Procfile`: Process definition
- `runtime.txt`: Python version
- `render.yaml`: Render configuration
- `requirements.txt`: Dependencies

**Environment Variables**:
```bash
PORT=8050                    # Application port
HOST=0.0.0.0                # Listen on all interfaces
DEBUG=False                 # Production mode
DATABASE_PATH=hospital_analytics.duckdb
```

---

## Summary

This Hospital Dashboard application provides comprehensive financial analytics for 6,000+ hospitals using:

- **78 KPIs** organized in 3-level hierarchy
- **CMS HCRIS data** from 25+ worksheets spanning 5 years
- **4-level benchmarking** (National/State/Type/State+Type)
- **Sub-100ms queries** using pre-computed DuckDB database
- **Interactive visualizations** with Dash and Plotly
- **Secure authentication** for multi-user deployment

All KPIs are traceable to specific HCRIS worksheet lines, with formulas clearly documented and data sources precisely identified. The pre-computation strategy delivers 50-300x performance improvement over on-demand calculation, enabling real-time interactive analysis.

---

**For Questions or Support**:
- Review this documentation
- Check `kpi_hierarchy_config.py` for KPI definitions
- Review `dashboard.py` for implementation details
- Consult CMS HCRIS documentation for worksheet references

**Version**: 1.0
**Last Updated**: 2025-11-22
**Total KPIs Documented**: 78 (6 Level 1 + 24 Level 2 + 48 Level 3)
