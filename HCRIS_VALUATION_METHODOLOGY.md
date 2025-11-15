# HCRIS Hospital Valuation Methodology
## Complete Step-by-Step Guide to Building Final Financial Tables

**Document Version:** 1.0
**Last Updated:** 2025-11-13
**Source:** Provider Reimbursement Manual (CMS Pub. 15-1, Form CMS-2552-10)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [HCRIS Worksheet Overview](#hcris-worksheet-overview)
3. [Data Flow Architecture](#data-flow-architecture)
4. [Core Financial Statements](#core-financial-statements)
5. [Step-by-Step Implementation Guide](#step-by-step-implementation-guide)
6. [Key Metrics for Hospital Valuation](#key-metrics-for-hospital-valuation)
7. [SQL Implementation Examples](#sql-implementation-examples)
8. [Data Validation Checkpoints](#data-validation-checkpoints)
9. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)

---

## Executive Summary

This document provides a comprehensive methodology for transforming raw HCRIS (Healthcare Cost Report Information System) data into final financial statements suitable for hospital valuation. HCRIS Form CMS-2552-10 contains detailed cost reporting data submitted annually by Medicare-participating hospitals.

### Key Objectives:
- Extract Balance Sheet data from Worksheet G
- Calculate Net Patient Revenue from Worksheet G-3
- Derive Operating Income/EBITDA for valuation
- Build comprehensive financial statement tables
- Enable multi-year trend analysis and benchmarking

### Required HCRIS Worksheets:
- **Worksheet G:** Balance Sheet (Assets, Liabilities, Fund Balances)
- **Worksheet G-1:** Statement of Changes in Fund Balances
- **Worksheet G-2:** Patient Revenues and Operating Expenses
- **Worksheet G-3:** Statement of Revenues and Expenses (Income Statement)
- **Worksheet A:** Trial Balance of Expenses (for EBITDA calculation)
- **Worksheet A-7:** Capital Assets Analysis (for depreciation)
- **Worksheet S-3:** Statistical Data (for operational metrics)

---

## HCRIS Worksheet Overview

### Worksheet Hierarchy and Purpose

```
┌─────────────────────────────────────────────────────────────┐
│                    HCRIS COST REPORT                         │
│                   Form CMS-2552-10                           │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   WORKSHEET A         WORKSHEET B         WORKSHEET S
   Trial Balance      Cost Allocation      Statistical Data
   (Lines 1-200)      (Step-Down)          (Utilization)
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                      WORKSHEET G-2
              Patient Revenues & Operating Expenses
                            │
                            ▼
                      WORKSHEET G-3
              Statement of Revenues & Expenses
             (INCOME STATEMENT - Primary Source)
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
          WORKSHEET G-1            WORKSHEET G
    Changes in Fund Balance      Balance Sheet
                                 (Primary Source)
```

### Worksheet Details

| Worksheet | Name | Purpose | Key Metrics |
|-----------|------|---------|-------------|
| **G** | Balance Sheet | Assets, Liabilities, Equity | Total Assets, Liabilities, Net Worth |
| **G-1** | Changes in Fund Balances | Equity reconciliation | Beginning/Ending Equity, Net Income |
| **G-2** | Patient Revenues & Operating Expenses | Revenue/expense compilation | Total Patient Revenue, Operating Expenses |
| **G-3** | Statement of Revenues & Expenses | Income Statement | Net Patient Revenue, Operating Income, Net Income |
| **A** | Trial Balance | Expense detail by cost center | Total Expenses, Salary vs. Non-Salary |
| **A-7** | Capital Assets Analysis | Depreciation and capital costs | Depreciation Expense, Asset Values |
| **S-3** | Statistical Data | Utilization statistics | Patient Days, Discharges, FTEs |

---

## Data Flow Architecture

### Primary Data Sources

HCRIS data is distributed in three CSV files per fiscal year:

1. **alpha.csv** - Text descriptions (Line/Column labels)
2. **nmrc.csv** - Numeric values (financial data)
3. **rpt.csv** - Report metadata (Provider ID, dates, status)

### Worksheet Identification

Worksheets are identified by a 7-character code:
- **G000000** = Worksheet G (Balance Sheet)
- **G100000** = Worksheet G-1 (Changes in Fund Balances)
- **G200000** = Worksheet G-2 (Patient Revenues & Operating Expenses)
- **G300000** = Worksheet G-3 (Statement of Revenues & Expenses)
- **A000000** = Worksheet A (Trial Balance)
- **A700000** = Worksheet A-7 (Capital Assets)
- **S300000** = Worksheet S-3 (Statistical Data)

### Line and Column Structure

Each worksheet has:
- **Lines (rows):** Specific account or line item (5-digit code, e.g., "00100")
- **Columns:** Different classifications or time periods (5-digit code, e.g., "00100")

Example: Worksheet G, Line 1, Column 1 = "Cash on hand and in banks - General Fund"

---

## Core Financial Statements

### 1. Balance Sheet (Worksheet G)

**Purpose:** Snapshot of hospital's financial position at fiscal year end

#### Assets (Lines 1-36)

**Current Assets (Lines 1-11):**
```
Line 1:  Cash on hand and in banks
Line 2:  Temporary investments
Line 3:  Notes receivable
Line 4:  Accounts receivable
Line 5:  Other receivables
Line 6:  Less: Allowance for uncollectible accounts (negative)
Line 7:  Inventory
Line 8:  Prepaid expenses
Line 9:  Other current assets
Line 10: Due from other funds
Line 11: TOTAL CURRENT ASSETS
```

**Property, Plant & Equipment (Lines 12-30):**
```
Line 12: Land
Lines 13-14: Land improvements (gross, accumulated depreciation)
Lines 15-16: Buildings (gross, accumulated depreciation)
Lines 17-18: Leasehold improvements (gross, accumulated depreciation)
Lines 19-20: Fixed equipment (gross, accumulated depreciation)
Lines 21-22: Automobiles and trucks (gross, accumulated depreciation)
Lines 23-24: Major movable equipment (gross, accumulated depreciation)
Lines 25-26: Minor equipment - depreciable (gross, accumulated depreciation)
Lines 27-28: HIT designated assets (gross, accumulated depreciation)
Line 29: Minor equipment - nondepreciable
Line 30: TOTAL PROPERTY, PLANT & EQUIPMENT (NET)
```

**Other Assets (Lines 31-35):**
```
Line 31: Investments
Line 32: Deposits on leases
Line 33: Due from owners/officers
Line 34: Other assets (goodwill, intangibles)
Line 35: TOTAL OTHER ASSETS
```

**Line 36: TOTAL ASSETS**

#### Liabilities (Lines 37-51)

**Current Liabilities (Lines 37-45):**
```
Line 37: Accounts payable
Line 38: Salaries, wages, and fees payable
Line 39: Payroll taxes payable
Line 40: Notes and loans payable (short-term)
Line 41: Deferred income
Line 42: Accelerated payments (including Medicare advance payments)
Line 43: Due to other funds
Line 44: Other current liabilities
Line 45: TOTAL CURRENT LIABILITIES
```

**Long-Term Liabilities (Lines 46-50):**
```
Line 46: Mortgage payable
Line 47: Notes payable
Line 48: Unsecured loans
Line 49: Other long-term liabilities
Line 50: TOTAL LONG-TERM LIABILITIES
```

**Line 51: TOTAL LIABILITIES**

#### Fund Balances / Equity (Lines 52-59)

```
Line 52: General fund balance
Line 53: Specific purpose fund
Line 54: Endowment fund balance - restricted
Line 55: Endowment fund balance - unrestricted
Line 56: Endowment fund balance - governing body created
Line 57: Plant fund balance - invested in plant
Line 58: Plant fund balance - reserves
Line 59: TOTAL FUND BALANCES (EQUITY)

Line 60: TOTAL LIABILITIES AND FUND BALANCES (must equal Line 36)
```

**Columns for Worksheet G:**
- **Column 1:** General Fund
- **Column 2:** Specific Purpose Fund
- **Column 3:** Endowment Fund
- **Column 4:** Plant Fund
- **Column 5:** Total (sum of columns 1-4)

---

### 2. Statement of Revenues and Expenses (Worksheet G-3)

**Purpose:** Hospital's income statement - PRIMARY SOURCE for valuation metrics

#### Complete Line Structure:

```
REVENUES:
─────────────────────────────────────────────────────────────
Line 1:  Total Patient Revenue (gross charges)
           [from Worksheet G-2, Part I, Line 28]

Line 2:  Less: Allowances and Discounts
           - Bad debts
           - Contractual adjustments (Medicare, Medicaid, managed care)
           - Charity care
           - Teaching allowances
           - Administrative and courtesy allowances
           - Policy discounts
           - Implicit price concessions

Line 3:  NET PATIENT REVENUES ⭐ KEY METRIC
           [Line 1 - Line 2]

OPERATING EXPENSES:
─────────────────────────────────────────────────────────────
Line 4:  Less: Total Operating Expenses
           [from Worksheet G-2, Part II, Line 43]

Line 5:  NET INCOME FROM SERVICE TO PATIENTS ⭐ KEY METRIC
           (Operating Income)
           [Line 3 - Line 4]

OTHER INCOME (Non-Operating):
─────────────────────────────────────────────────────────────
Line 6:  Income from investments
Line 7:  Purchase discounts
Line 8:  Income from rentals
Line 9:  Income from sale of scrap and salvage
Line 10: Proceeds from sale of capital assets
Line 11: Income from sale of cafeteria meals to visitors
Line 12: Income from sale of medical and pharmacy supplies
Line 13: Income from vending machines
Line 14: Income from gift, flower, and coffee shops
Line 15: Contributions, donations, and bequests
Line 16: Income from educational programs
Line 17: Research grants
Line 18: Income from miscellaneous sources
Line 19: Income from related organizations
Line 20: Transfers from restricted funds
Line 21: EHR incentive payments
Line 22: COVID-19 relief funds
Line 23: Other funding
Line 24: Other (specify)
Line 24.50: COVID-19 PHE funding
Lines 24.51-24.60: Other COVID-19 related funding

Line 25: Total Other Income
           [Sum of Lines 6-24.60]

Line 26: TOTAL INCOME
           [Line 5 + Line 25]

OTHER EXPENSES (Non-Operating):
─────────────────────────────────────────────────────────────
Line 27: Other expenses (specify)
Line 28: Total Other Expenses

NET INCOME:
─────────────────────────────────────────────────────────────
Line 29: NET INCOME (OR LOSS) FOR THE PERIOD ⭐ KEY METRIC
           [Line 26 - Line 28]
           [Transfers to Worksheet G-1, Line 2]
```

---

### 3. Patient Revenues and Operating Expenses (Worksheet G-2)

**Purpose:** Detailed breakdown of revenue sources and expense compilation

#### Part I - Patient Revenues (Lines 1-28)

```
INPATIENT ROUTINE CARE:
Line 1:  General inpatient routine care - hospital
Line 2:  General inpatient routine care - subprovider I
Line 3:  General inpatient routine care - subprovider II
Line 4:  General inpatient routine care - swing bed
Line 5:  General inpatient routine care - SNF
Line 6:  General inpatient routine care - NF
Line 7-10: Other long-term care inpatient routine

INTENSIVE CARE:
Line 11: Intensive care unit (ICU)
Line 12: Coronary care unit (CCU)
Line 13: Burn intensive care unit
Line 14: Surgical intensive care unit
Line 15: Other special care units
Line 16: Observation beds

Line 17: TOTAL INPATIENT ROUTINE CARE SERVICES

OTHER PATIENT SERVICES:
Line 18: Ancillary services (inpatient and outpatient)
Line 19: Outpatient services
Line 20: Rural health clinic (RHC)
Line 21: Federally qualified health center (FQHC)
Line 22: Home health agency (HHA)
Line 23: Ambulance services
Line 24: Outpatient rehabilitation providers
Line 25: Ambulatory surgical center (ASC)
Line 26: Hospice
Line 27: Other

Line 28: TOTAL PATIENT REVENUES ⭐
           [Transfers to Worksheet G-3, Line 1]
```

#### Part II - Operating Expenses (Lines 29-43)

```
Line 29: Operating expenses
           [from Worksheet A, Line 200, Column 3]

ADDITIONS (Lines 30-35):
Line 30: Depreciation - buildings and fixtures
Line 31: Depreciation - movable equipment
Line 32: Interest expense
Line 33: Insurance
Line 34: Taxes (other than payroll and income taxes)
Line 35: Other additions

Line 36: Total Additions

DEDUCTIONS (Lines 37-42):
Line 37: Expense incurred in prior periods
Line 38: Income from sale of scrap, salvage, and excess materials
Line 39: Proceeds from sale of capital assets
Line 40: Purchase discounts
Line 41: Recovery of bad debts
Line 42: Other deductions

Line 42: Total Deductions

Line 43: TOTAL OPERATING EXPENSES ⭐
           [Line 29 + Line 36 - Line 42]
           [Transfers to Worksheet G-3, Line 4]
```

---

### 4. Trial Balance (Worksheet A) - For EBITDA Calculation

**Purpose:** Detailed expense breakdown by cost center

#### Key Lines for Valuation:

```
CAPITAL-RELATED COSTS:
Line 1:   Capital-related costs - Building and fixtures
Line 2:   Capital-related costs - Movable equipment
Line 113: Interest expense (before reclassification)

GENERAL SERVICE COSTS:
Line 4:   Employee benefits
Line 5:   Administrative and general
Line 6:   Maintenance and repairs
Line 7:   Operation of plant
Line 8:   Laundry and linen
Line 9:   Housekeeping
Line 10:  Dietary
Line 11:  Cafeteria

REVENUE-PRODUCING DEPARTMENTS:
Lines 30-46:  Inpatient routine service costs
Lines 50-78:  Ancillary service costs
Lines 88-93:  Outpatient service costs

Line 200: TOTAL COSTS (Column 3 = total expenses)
```

**Column Structure:**
- **Column 1:** Salaries and wages
- **Column 2:** Other than salaries
- **Column 3:** Total (Column 1 + Column 2)
- **Column 7:** Final adjusted costs (after reclassifications and adjustments)

---

### 5. Capital Assets Analysis (Worksheet A-7) - For Depreciation

**Purpose:** Track depreciation expense for EBITDA calculation

#### Part I - Changes in Capital Asset Balances (Lines by asset type):

```
Asset Categories:
Line 1:  Land improvements
Line 2:  Buildings
Line 3:  Leasehold improvements
Line 4:  Fixed equipment
Line 5:  Major movable equipment
Line 6:  Minor equipment
Line 7:  HIT designated assets
```

#### Part III - Capital Cost Allocation (by column):

```
Column 9:  Depreciation - Land improvements
Column 10: Depreciation - Buildings
Column 11: Depreciation - Leasehold improvements
Column 12: Depreciation - Fixed equipment
Column 13: Depreciation - Major movable equipment
Column 14: Depreciation - Minor equipment

TOTAL DEPRECIATION = Sum of Columns 9-14, Line 200
```

---

## Step-by-Step Implementation Guide

### Phase 1: Data Extraction and Preparation

#### Step 1.1: Extract Balance Sheet Data (Worksheet G000000)

**SQL/Python Pseudocode:**

```sql
-- Extract Balance Sheet data
SELECT
    rpt.Provider_Number,
    rpt.FY_End,
    YEAR(rpt.FY_End) AS Fiscal_Year,
    nmrc.Line,
    nmrc.Column,
    names.Line_Name,
    names.Column_Name,
    nmrc.Value
FROM nmrc_data AS nmrc
JOIN rpt_data AS rpt
    ON nmrc.Report_Record_Number = rpt.Report_Record_Number
LEFT JOIN worksheet_names AS names
    ON nmrc.Worksheet = names.Worksheet
    AND nmrc.Line = names.Line
    AND nmrc.Column = names.Column
WHERE nmrc.Worksheet = 'G000000'
    AND rpt.Report_Status IN ('A', 'F')  -- Final or As-Submitted reports only
ORDER BY rpt.Provider_Number, rpt.FY_End, nmrc.Line, nmrc.Column;
```

#### Step 1.2: Extract Income Statement Data (Worksheet G300000)

```sql
-- Extract Income Statement data
SELECT
    rpt.Provider_Number,
    rpt.FY_End,
    YEAR(rpt.FY_End) AS Fiscal_Year,
    nmrc.Line,
    names.Line_Name,
    nmrc.Value
FROM nmrc_data AS nmrc
JOIN rpt_data AS rpt
    ON nmrc.Report_Record_Number = rpt.Report_Record_Number
LEFT JOIN worksheet_names AS names
    ON nmrc.Worksheet = names.Worksheet
    AND nmrc.Line = names.Line
WHERE nmrc.Worksheet = 'G300000'
    AND nmrc.Column = '00100'  -- Column 1 (General Fund - primary column)
    AND rpt.Report_Status IN ('A', 'F')
ORDER BY rpt.Provider_Number, rpt.FY_End, nmrc.Line;
```

#### Step 1.3: Extract Expense Detail (Worksheet A000000)

```sql
-- Extract expense data for EBITDA calculation
SELECT
    rpt.Provider_Number,
    rpt.FY_End,
    nmrc.Line,
    names.Line_Name,
    nmrc.Column,
    nmrc.Value
FROM nmrc_data AS nmrc
JOIN rpt_data AS rpt
    ON nmrc.Report_Record_Number = rpt.Report_Record_Number
LEFT JOIN worksheet_names AS names
    ON nmrc.Worksheet = names.Worksheet
    AND nmrc.Line = names.Line
WHERE nmrc.Worksheet = 'A000000'
    AND nmrc.Line IN ('00100', '00200', '11300', '20000')  -- Key lines for EBITDA
    AND nmrc.Column IN ('00100', '00200', '00300')  -- Salaries, Other, Total
    AND rpt.Report_Status IN ('A', 'F')
ORDER BY rpt.Provider_Number, rpt.FY_End, nmrc.Line;
```

#### Step 1.4: Extract Depreciation (Worksheet A700000)

```sql
-- Extract depreciation data
SELECT
    rpt.Provider_Number,
    rpt.FY_End,
    nmrc.Line,
    nmrc.Column,
    names.Column_Name AS Asset_Type,
    SUM(nmrc.Value) AS Depreciation_Value
FROM nmrc_data AS nmrc
JOIN rpt_data AS rpt
    ON nmrc.Report_Record_Number = rpt.Report_Record_Number
LEFT JOIN worksheet_names AS names
    ON nmrc.Worksheet = names.Worksheet
    AND nmrc.Column = names.Column
WHERE nmrc.Worksheet = 'A700000'
    AND nmrc.Column IN ('00900', '01000', '01100', '01200', '01300', '01400')  -- Depreciation columns
    AND nmrc.Line = '20000'  -- Total line
    AND rpt.Report_Status IN ('A', 'F')
GROUP BY rpt.Provider_Number, rpt.FY_End, nmrc.Line, nmrc.Column, names.Column_Name
ORDER BY rpt.Provider_Number, rpt.FY_End;
```

---

### Phase 2: Build Core Financial Tables

#### Step 2.1: Create Balance Sheet Table

**Target Schema:**

```sql
CREATE TABLE balance_sheet (
    Provider_Number VARCHAR(10),
    Provider_Name VARCHAR(255),
    Fiscal_Year INT,
    FY_Begin DATE,
    FY_End DATE,
    State_Code VARCHAR(2),

    -- Current Assets
    Cash DECIMAL(15,2),
    Temporary_Investments DECIMAL(15,2),
    Accounts_Receivable_Gross DECIMAL(15,2),
    Allowance_Doubtful_Accounts DECIMAL(15,2),
    Accounts_Receivable_Net DECIMAL(15,2),
    Inventory DECIMAL(15,2),
    Prepaid_Expenses DECIMAL(15,2),
    Total_Current_Assets DECIMAL(15,2),

    -- PP&E
    Land DECIMAL(15,2),
    Buildings_Gross DECIMAL(15,2),
    Buildings_Accumulated_Depreciation DECIMAL(15,2),
    Buildings_Net DECIMAL(15,2),
    Equipment_Gross DECIMAL(15,2),
    Equipment_Accumulated_Depreciation DECIMAL(15,2),
    Equipment_Net DECIMAL(15,2),
    Total_PPE_Net DECIMAL(15,2),

    -- Other Assets
    Investments DECIMAL(15,2),
    Other_Assets DECIMAL(15,2),
    Total_Other_Assets DECIMAL(15,2),

    -- TOTAL ASSETS
    Total_Assets DECIMAL(15,2),

    -- Current Liabilities
    Accounts_Payable DECIMAL(15,2),
    Salaries_Payable DECIMAL(15,2),
    Short_Term_Debt DECIMAL(15,2),
    Other_Current_Liabilities DECIMAL(15,2),
    Total_Current_Liabilities DECIMAL(15,2),

    -- Long-Term Liabilities
    Mortgage_Payable DECIMAL(15,2),
    Long_Term_Debt DECIMAL(15,2),
    Other_Long_Term_Liabilities DECIMAL(15,2),
    Total_Long_Term_Liabilities DECIMAL(15,2),

    -- TOTAL LIABILITIES
    Total_Liabilities DECIMAL(15,2),

    -- Fund Balances / Equity
    General_Fund_Balance DECIMAL(15,2),
    Other_Fund_Balances DECIMAL(15,2),
    Total_Fund_Balances DECIMAL(15,2),

    -- Validation
    Total_Liabilities_And_Equity DECIMAL(15,2),
    Balance_Check DECIMAL(15,2),  -- Should be zero (Assets - Liab - Equity)

    PRIMARY KEY (Provider_Number, Fiscal_Year)
);
```

**Population Query:**

```sql
INSERT INTO balance_sheet
SELECT
    Provider_Number,
    Provider_Name,
    Fiscal_Year,
    FY_Begin,
    FY_End,
    SUBSTRING(Provider_Number, 1, 2) AS State_Code,

    -- Current Assets (Column 5 = Total across all funds)
    MAX(CASE WHEN Line = '00100' AND Column = '00500' THEN Value END) AS Cash,
    MAX(CASE WHEN Line = '00200' AND Column = '00500' THEN Value END) AS Temporary_Investments,
    MAX(CASE WHEN Line = '00400' AND Column = '00500' THEN Value END) AS Accounts_Receivable_Gross,
    MAX(CASE WHEN Line = '00600' AND Column = '00500' THEN Value END) AS Allowance_Doubtful_Accounts,
    (MAX(CASE WHEN Line = '00400' AND Column = '00500' THEN Value END) +
     MAX(CASE WHEN Line = '00600' AND Column = '00500' THEN Value END)) AS Accounts_Receivable_Net,
    MAX(CASE WHEN Line = '00700' AND Column = '00500' THEN Value END) AS Inventory,
    MAX(CASE WHEN Line = '00800' AND Column = '00500' THEN Value END) AS Prepaid_Expenses,
    MAX(CASE WHEN Line = '01100' AND Column = '00500' THEN Value END) AS Total_Current_Assets,

    -- PP&E
    MAX(CASE WHEN Line = '01200' AND Column = '00500' THEN Value END) AS Land,
    MAX(CASE WHEN Line = '01500' AND Column = '00500' THEN Value END) AS Buildings_Gross,
    MAX(CASE WHEN Line = '01600' AND Column = '00500' THEN Value END) AS Buildings_Accumulated_Depreciation,
    (MAX(CASE WHEN Line = '01500' AND Column = '00500' THEN Value END) -
     ABS(MAX(CASE WHEN Line = '01600' AND Column = '00500' THEN Value END))) AS Buildings_Net,
    (MAX(CASE WHEN Line = '02300' AND Column = '00500' THEN Value END) +
     MAX(CASE WHEN Line = '02100' AND Column = '00500' THEN Value END)) AS Equipment_Gross,
    (MAX(CASE WHEN Line = '02400' AND Column = '00500' THEN Value END) +
     MAX(CASE WHEN Line = '02200' AND Column = '00500' THEN Value END)) AS Equipment_Accumulated_Depreciation,
    ((MAX(CASE WHEN Line = '02300' AND Column = '00500' THEN Value END) +
      MAX(CASE WHEN Line = '02100' AND Column = '00500' THEN Value END)) -
     ABS(MAX(CASE WHEN Line = '02400' AND Column = '00500' THEN Value END) +
         MAX(CASE WHEN Line = '02200' AND Column = '00500' THEN Value END))) AS Equipment_Net,
    MAX(CASE WHEN Line = '03000' AND Column = '00500' THEN Value END) AS Total_PPE_Net,

    -- Other Assets
    MAX(CASE WHEN Line = '03100' AND Column = '00500' THEN Value END) AS Investments,
    MAX(CASE WHEN Line = '03400' AND Column = '00500' THEN Value END) AS Other_Assets,
    MAX(CASE WHEN Line = '03500' AND Column = '00500' THEN Value END) AS Total_Other_Assets,

    -- TOTAL ASSETS
    MAX(CASE WHEN Line = '03600' AND Column = '00500' THEN Value END) AS Total_Assets,

    -- Current Liabilities
    MAX(CASE WHEN Line = '03700' AND Column = '00500' THEN Value END) AS Accounts_Payable,
    MAX(CASE WHEN Line = '03800' AND Column = '00500' THEN Value END) AS Salaries_Payable,
    MAX(CASE WHEN Line = '04000' AND Column = '00500' THEN Value END) AS Short_Term_Debt,
    MAX(CASE WHEN Line = '04400' AND Column = '00500' THEN Value END) AS Other_Current_Liabilities,
    MAX(CASE WHEN Line = '04500' AND Column = '00500' THEN Value END) AS Total_Current_Liabilities,

    -- Long-Term Liabilities
    MAX(CASE WHEN Line = '04600' AND Column = '00500' THEN Value END) AS Mortgage_Payable,
    MAX(CASE WHEN Line = '04700' AND Column = '00500' THEN Value END) AS Long_Term_Debt,
    MAX(CASE WHEN Line = '04900' AND Column = '00500' THEN Value END) AS Other_Long_Term_Liabilities,
    MAX(CASE WHEN Line = '05000' AND Column = '00500' THEN Value END) AS Total_Long_Term_Liabilities,

    -- TOTAL LIABILITIES
    MAX(CASE WHEN Line = '05100' AND Column = '00500' THEN Value END) AS Total_Liabilities,

    -- Fund Balances
    MAX(CASE WHEN Line = '05200' AND Column = '00500' THEN Value END) AS General_Fund_Balance,
    (MAX(CASE WHEN Line = '05300' AND Column = '00500' THEN Value END) +
     MAX(CASE WHEN Line = '05700' AND Column = '00500' THEN Value END)) AS Other_Fund_Balances,
    MAX(CASE WHEN Line = '05900' AND Column = '00500' THEN Value END) AS Total_Fund_Balances,

    -- Validation
    MAX(CASE WHEN Line = '06000' AND Column = '00500' THEN Value END) AS Total_Liabilities_And_Equity,
    (MAX(CASE WHEN Line = '03600' AND Column = '00500' THEN Value END) -
     MAX(CASE WHEN Line = '05100' AND Column = '00500' THEN Value END) -
     MAX(CASE WHEN Line = '05900' AND Column = '00500' THEN Value END)) AS Balance_Check

FROM balance_sheet_raw  -- Your extracted data from Step 1.1
GROUP BY Provider_Number, Provider_Name, Fiscal_Year, FY_Begin, FY_End;
```

---

#### Step 2.2: Create Income Statement Table

**Target Schema:**

```sql
CREATE TABLE income_statement (
    Provider_Number VARCHAR(10),
    Provider_Name VARCHAR(255),
    Fiscal_Year INT,
    FY_Begin DATE,
    FY_End DATE,
    State_Code VARCHAR(2),

    -- Revenue
    Total_Patient_Revenue_Gross DECIMAL(15,2),
    Contractual_Adjustments DECIMAL(15,2),
    Bad_Debts DECIMAL(15,2),
    Charity_Care DECIMAL(15,2),
    Other_Deductions DECIMAL(15,2),
    Total_Deductions_From_Revenue DECIMAL(15,2),
    Net_Patient_Revenue DECIMAL(15,2),  -- KEY METRIC

    -- Operating Expenses
    Total_Operating_Expenses DECIMAL(15,2),

    -- Operating Income
    Operating_Income DECIMAL(15,2),  -- KEY METRIC

    -- Other Income (Non-Operating)
    Investment_Income DECIMAL(15,2),
    Donations_And_Grants DECIMAL(15,2),
    COVID_Relief_Funds DECIMAL(15,2),
    EHR_Incentive_Payments DECIMAL(15,2),
    Other_Nonoperating_Income DECIMAL(15,2),
    Total_Other_Income DECIMAL(15,2),

    -- Other Expenses (Non-Operating)
    Other_Expenses DECIMAL(15,2),

    -- Net Income
    Net_Income DECIMAL(15,2),  -- KEY METRIC

    -- Calculated Metrics (from Worksheet A and A-7)
    Depreciation_Expense DECIMAL(15,2),
    Interest_Expense DECIMAL(15,2),
    EBITDA DECIMAL(15,2),  -- KEY METRIC

    -- Ratios
    Operating_Margin_Percent DECIMAL(10,4),
    Net_Margin_Percent DECIMAL(10,4),
    EBITDA_Margin_Percent DECIMAL(10,4),

    PRIMARY KEY (Provider_Number, Fiscal_Year)
);
```

**Population Query:**

```sql
INSERT INTO income_statement
SELECT
    g3.Provider_Number,
    g3.Provider_Name,
    g3.Fiscal_Year,
    g3.FY_Begin,
    g3.FY_End,
    SUBSTRING(g3.Provider_Number, 1, 2) AS State_Code,

    -- Revenue (from Worksheet G-3, Column 1)
    MAX(CASE WHEN g3.Line = '00100' THEN g3.Value END) AS Total_Patient_Revenue_Gross,
    MAX(CASE WHEN g3.Line = '00200' THEN g3.Value END) AS Total_Deductions_From_Revenue,
    MAX(CASE WHEN g3.Line = '00200' THEN g3.Value END) * 0.70 AS Contractual_Adjustments,  -- Estimate
    MAX(CASE WHEN g3.Line = '00200' THEN g3.Value END) * 0.15 AS Bad_Debts,  -- Estimate
    MAX(CASE WHEN g3.Line = '00200' THEN g3.Value END) * 0.10 AS Charity_Care,  -- Estimate
    MAX(CASE WHEN g3.Line = '00200' THEN g3.Value END) * 0.05 AS Other_Deductions,  -- Estimate
    MAX(CASE WHEN g3.Line = '00200' THEN g3.Value END) AS Total_Deductions_From_Revenue,
    MAX(CASE WHEN g3.Line = '00300' THEN g3.Value END) AS Net_Patient_Revenue,  -- ⭐ KEY

    -- Operating Expenses
    MAX(CASE WHEN g3.Line = '00400' THEN g3.Value END) AS Total_Operating_Expenses,

    -- Operating Income
    MAX(CASE WHEN g3.Line = '00500' THEN g3.Value END) AS Operating_Income,  -- ⭐ KEY

    -- Other Income
    MAX(CASE WHEN g3.Line = '00600' THEN g3.Value END) AS Investment_Income,
    (MAX(CASE WHEN g3.Line = '01500' THEN g3.Value END) +
     MAX(CASE WHEN g3.Line = '01700' THEN g3.Value END)) AS Donations_And_Grants,
    (MAX(CASE WHEN g3.Line = '02200' THEN g3.Value END) +
     MAX(CASE WHEN g3.Line = '02450' THEN g3.Value END)) AS COVID_Relief_Funds,
    MAX(CASE WHEN g3.Line = '02100' THEN g3.Value END) AS EHR_Incentive_Payments,
    MAX(CASE WHEN g3.Line = '01800' THEN g3.Value END) AS Other_Nonoperating_Income,
    MAX(CASE WHEN g3.Line = '02500' THEN g3.Value END) AS Total_Other_Income,

    -- Other Expenses
    MAX(CASE WHEN g3.Line = '02800' THEN g3.Value END) AS Other_Expenses,

    -- Net Income
    MAX(CASE WHEN g3.Line = '02900' THEN g3.Value END) AS Net_Income,  -- ⭐ KEY

    -- Add Depreciation from Worksheet A-7
    COALESCE(depr.Total_Depreciation, 0) AS Depreciation_Expense,

    -- Add Interest from Worksheet A
    COALESCE(intr.Interest_Expense, 0) AS Interest_Expense,

    -- Calculate EBITDA
    (MAX(CASE WHEN g3.Line = '02900' THEN g3.Value END) +
     COALESCE(depr.Total_Depreciation, 0) +
     COALESCE(intr.Interest_Expense, 0)) AS EBITDA,  -- ⭐ KEY

    -- Calculate Ratios
    (MAX(CASE WHEN g3.Line = '00500' THEN g3.Value END) /
     NULLIF(MAX(CASE WHEN g3.Line = '00300' THEN g3.Value END), 0) * 100) AS Operating_Margin_Percent,

    (MAX(CASE WHEN g3.Line = '02900' THEN g3.Value END) /
     NULLIF(MAX(CASE WHEN g3.Line = '00300' THEN g3.Value END), 0) * 100) AS Net_Margin_Percent,

    ((MAX(CASE WHEN g3.Line = '02900' THEN g3.Value END) +
      COALESCE(depr.Total_Depreciation, 0) +
      COALESCE(intr.Interest_Expense, 0)) /
     NULLIF(MAX(CASE WHEN g3.Line = '00300' THEN g3.Value END), 0) * 100) AS EBITDA_Margin_Percent

FROM worksheet_g3_raw AS g3
LEFT JOIN (
    -- Subquery to get total depreciation from Worksheet A-7
    SELECT
        Provider_Number,
        Fiscal_Year,
        SUM(Value) AS Total_Depreciation
    FROM worksheet_a7_raw
    WHERE Line = '20000'  -- Total line
        AND Column IN ('00900', '01000', '01100', '01200', '01300', '01400')
    GROUP BY Provider_Number, Fiscal_Year
) AS depr
    ON g3.Provider_Number = depr.Provider_Number
    AND g3.Fiscal_Year = depr.Fiscal_Year
LEFT JOIN (
    -- Subquery to get interest expense from Worksheet A
    SELECT
        Provider_Number,
        Fiscal_Year,
        Value AS Interest_Expense
    FROM worksheet_a_raw
    WHERE Line = '11300'  -- Interest expense line
        AND Column = '00300'  -- Total column
) AS intr
    ON g3.Provider_Number = intr.Provider_Number
    AND g3.Fiscal_Year = intr.Fiscal_Year

GROUP BY g3.Provider_Number, g3.Provider_Name, g3.Fiscal_Year, g3.FY_Begin, g3.FY_End,
         depr.Total_Depreciation, intr.Interest_Expense;
```

---

#### Step 2.3: Create Cash Flow Statement (Derived)

**Target Schema:**

```sql
CREATE TABLE cash_flow_statement (
    Provider_Number VARCHAR(10),
    Provider_Name VARCHAR(255),
    Fiscal_Year INT,
    FY_Begin DATE,
    FY_End DATE,
    State_Code VARCHAR(2),

    -- Operating Activities
    Net_Income DECIMAL(15,2),
    Depreciation_And_Amortization DECIMAL(15,2),
    Change_In_Accounts_Receivable DECIMAL(15,2),
    Change_In_Inventory DECIMAL(15,2),
    Change_In_Prepaid_Expenses DECIMAL(15,2),
    Change_In_Accounts_Payable DECIMAL(15,2),
    Change_In_Accrued_Liabilities DECIMAL(15,2),
    Change_In_Other_Working_Capital DECIMAL(15,2),
    Cash_Flow_From_Operations DECIMAL(15,2),  -- KEY METRIC

    -- Investing Activities
    Capital_Expenditures DECIMAL(15,2),
    Proceeds_From_Asset_Sales DECIMAL(15,2),
    Change_In_Investments DECIMAL(15,2),
    Cash_Flow_From_Investing DECIMAL(15,2),

    -- Financing Activities
    Change_In_Long_Term_Debt DECIMAL(15,2),
    Change_In_Short_Term_Debt DECIMAL(15,2),
    Cash_Flow_From_Financing DECIMAL(15,2),

    -- Net Change
    Net_Change_In_Cash DECIMAL(15,2),

    -- Free Cash Flow
    Free_Cash_Flow DECIMAL(15,2),  -- KEY METRIC (Operating CF - CapEx)

    PRIMARY KEY (Provider_Number, Fiscal_Year)
);
```

**Population Query:**

```sql
INSERT INTO cash_flow_statement
SELECT
    curr.Provider_Number,
    curr.Provider_Name,
    curr.Fiscal_Year,
    curr.FY_Begin,
    curr.FY_End,
    curr.State_Code,

    -- Operating Activities
    is_curr.Net_Income,
    is_curr.Depreciation_Expense AS Depreciation_And_Amortization,

    -- Changes in Working Capital (current year - prior year)
    (curr.Accounts_Receivable_Net - COALESCE(prior.Accounts_Receivable_Net, 0)) * -1 AS Change_In_Accounts_Receivable,
    (curr.Inventory - COALESCE(prior.Inventory, 0)) * -1 AS Change_In_Inventory,
    (curr.Prepaid_Expenses - COALESCE(prior.Prepaid_Expenses, 0)) * -1 AS Change_In_Prepaid_Expenses,
    (curr.Accounts_Payable - COALESCE(prior.Accounts_Payable, 0)) AS Change_In_Accounts_Payable,
    (curr.Salaries_Payable - COALESCE(prior.Salaries_Payable, 0)) AS Change_In_Accrued_Liabilities,
    ((curr.Other_Current_Liabilities - COALESCE(prior.Other_Current_Liabilities, 0)) -
     (curr.Other_Assets - COALESCE(prior.Other_Assets, 0))) AS Change_In_Other_Working_Capital,

    -- Cash Flow from Operations
    (is_curr.Net_Income +
     is_curr.Depreciation_Expense +
     (curr.Accounts_Receivable_Net - COALESCE(prior.Accounts_Receivable_Net, 0)) * -1 +
     (curr.Inventory - COALESCE(prior.Inventory, 0)) * -1 +
     (curr.Prepaid_Expenses - COALESCE(prior.Prepaid_Expenses, 0)) * -1 +
     (curr.Accounts_Payable - COALESCE(prior.Accounts_Payable, 0)) +
     (curr.Salaries_Payable - COALESCE(prior.Salaries_Payable, 0))) AS Cash_Flow_From_Operations,

    -- Investing Activities
    (curr.Total_PPE_Net - COALESCE(prior.Total_PPE_Net, 0) + is_curr.Depreciation_Expense) * -1 AS Capital_Expenditures,
    0 AS Proceeds_From_Asset_Sales,  -- Would need to extract from G-3, Line 10
    (curr.Investments - COALESCE(prior.Investments, 0)) * -1 AS Change_In_Investments,
    ((curr.Total_PPE_Net - COALESCE(prior.Total_PPE_Net, 0) + is_curr.Depreciation_Expense) * -1 +
     (curr.Investments - COALESCE(prior.Investments, 0)) * -1) AS Cash_Flow_From_Investing,

    -- Financing Activities
    (curr.Long_Term_Debt - COALESCE(prior.Long_Term_Debt, 0)) AS Change_In_Long_Term_Debt,
    (curr.Short_Term_Debt - COALESCE(prior.Short_Term_Debt, 0)) AS Change_In_Short_Term_Debt,
    ((curr.Long_Term_Debt - COALESCE(prior.Long_Term_Debt, 0)) +
     (curr.Short_Term_Debt - COALESCE(prior.Short_Term_Debt, 0))) AS Cash_Flow_From_Financing,

    -- Net Change in Cash
    (curr.Cash - COALESCE(prior.Cash, 0)) AS Net_Change_In_Cash,

    -- Free Cash Flow (Operating CF - CapEx)
    ((is_curr.Net_Income +
      is_curr.Depreciation_Expense +
      (curr.Accounts_Receivable_Net - COALESCE(prior.Accounts_Receivable_Net, 0)) * -1 +
      (curr.Inventory - COALESCE(prior.Inventory, 0)) * -1 +
      (curr.Prepaid_Expenses - COALESCE(prior.Prepaid_Expenses, 0)) * -1 +
      (curr.Accounts_Payable - COALESCE(prior.Accounts_Payable, 0)) +
      (curr.Salaries_Payable - COALESCE(prior.Salaries_Payable, 0))) -
     (curr.Total_PPE_Net - COALESCE(prior.Total_PPE_Net, 0) + is_curr.Depreciation_Expense)) AS Free_Cash_Flow

FROM balance_sheet AS curr
LEFT JOIN balance_sheet AS prior
    ON curr.Provider_Number = prior.Provider_Number
    AND curr.Fiscal_Year = prior.Fiscal_Year + 1
LEFT JOIN income_statement AS is_curr
    ON curr.Provider_Number = is_curr.Provider_Number
    AND curr.Fiscal_Year = is_curr.Fiscal_Year;
```

---

### Phase 3: Calculate Valuation Metrics

#### Step 3.1: Create Comprehensive Valuation Metrics Table

**Target Schema:**

```sql
CREATE TABLE hospital_valuation_metrics (
    Provider_Number VARCHAR(10),
    Provider_Name VARCHAR(255),
    Fiscal_Year INT,
    State_Code VARCHAR(2),

    -- Income Statement Metrics
    Net_Patient_Revenue DECIMAL(15,2),
    Operating_Income DECIMAL(15,2),
    Net_Income DECIMAL(15,2),
    EBITDA DECIMAL(15,2),

    -- Balance Sheet Metrics
    Total_Assets DECIMAL(15,2),
    Total_Liabilities DECIMAL(15,2),
    Total_Equity DECIMAL(15,2),
    Net_Working_Capital DECIMAL(15,2),

    -- Cash Flow Metrics
    Operating_Cash_Flow DECIMAL(15,2),
    Free_Cash_Flow DECIMAL(15,2),

    -- Profitability Ratios (%)
    Operating_Margin DECIMAL(10,4),
    Net_Margin DECIMAL(10,4),
    EBITDA_Margin DECIMAL(10,4),
    Return_On_Assets DECIMAL(10,4),
    Return_On_Equity DECIMAL(10,4),

    -- Liquidity Ratios
    Current_Ratio DECIMAL(10,4),
    Quick_Ratio DECIMAL(10,4),
    Days_Cash_On_Hand DECIMAL(10,2),

    -- Leverage Ratios
    Debt_To_Equity DECIMAL(10,4),
    Debt_To_Assets DECIMAL(10,4),
    Debt_Service_Coverage_Ratio DECIMAL(10,4),

    -- Efficiency Ratios
    Asset_Turnover DECIMAL(10,4),
    Receivables_Turnover DECIMAL(10,4),
    Days_In_Receivables DECIMAL(10,2),

    -- Growth Rates (YoY %)
    Revenue_Growth_Rate DECIMAL(10,4),
    EBITDA_Growth_Rate DECIMAL(10,4),
    Asset_Growth_Rate DECIMAL(10,4),

    PRIMARY KEY (Provider_Number, Fiscal_Year)
);
```

**Population Query:**

```sql
INSERT INTO hospital_valuation_metrics
SELECT
    curr.Provider_Number,
    curr.Provider_Name,
    curr.Fiscal_Year,
    curr.State_Code,

    -- Income Statement Metrics
    is_curr.Net_Patient_Revenue,
    is_curr.Operating_Income,
    is_curr.Net_Income,
    is_curr.EBITDA,

    -- Balance Sheet Metrics
    bs_curr.Total_Assets,
    bs_curr.Total_Liabilities,
    bs_curr.Total_Fund_Balances AS Total_Equity,
    (bs_curr.Total_Current_Assets - bs_curr.Total_Current_Liabilities) AS Net_Working_Capital,

    -- Cash Flow Metrics
    cf_curr.Cash_Flow_From_Operations AS Operating_Cash_Flow,
    cf_curr.Free_Cash_Flow,

    -- Profitability Ratios (%)
    is_curr.Operating_Margin_Percent AS Operating_Margin,
    is_curr.Net_Margin_Percent AS Net_Margin,
    is_curr.EBITDA_Margin_Percent AS EBITDA_Margin,
    (is_curr.Net_Income / NULLIF(bs_curr.Total_Assets, 0) * 100) AS Return_On_Assets,
    (is_curr.Net_Income / NULLIF(bs_curr.Total_Fund_Balances, 0) * 100) AS Return_On_Equity,

    -- Liquidity Ratios
    (bs_curr.Total_Current_Assets / NULLIF(bs_curr.Total_Current_Liabilities, 0)) AS Current_Ratio,
    ((bs_curr.Cash + bs_curr.Temporary_Investments + bs_curr.Accounts_Receivable_Net) /
     NULLIF(bs_curr.Total_Current_Liabilities, 0)) AS Quick_Ratio,
    (bs_curr.Cash / NULLIF((is_curr.Total_Operating_Expenses / 365), 0)) AS Days_Cash_On_Hand,

    -- Leverage Ratios
    (bs_curr.Total_Liabilities / NULLIF(bs_curr.Total_Fund_Balances, 0)) AS Debt_To_Equity,
    (bs_curr.Total_Liabilities / NULLIF(bs_curr.Total_Assets, 0)) AS Debt_To_Assets,
    (is_curr.EBITDA / NULLIF(is_curr.Interest_Expense, 0)) AS Debt_Service_Coverage_Ratio,

    -- Efficiency Ratios
    (is_curr.Net_Patient_Revenue / NULLIF(bs_curr.Total_Assets, 0)) AS Asset_Turnover,
    (is_curr.Net_Patient_Revenue / NULLIF(bs_curr.Accounts_Receivable_Net, 0)) AS Receivables_Turnover,
    (365 / NULLIF((is_curr.Net_Patient_Revenue / NULLIF(bs_curr.Accounts_Receivable_Net, 0)), 0)) AS Days_In_Receivables,

    -- Growth Rates (YoY %)
    ((is_curr.Net_Patient_Revenue - COALESCE(is_prior.Net_Patient_Revenue, 0)) /
     NULLIF(COALESCE(is_prior.Net_Patient_Revenue, 0), 0) * 100) AS Revenue_Growth_Rate,
    ((is_curr.EBITDA - COALESCE(is_prior.EBITDA, 0)) /
     NULLIF(COALESCE(is_prior.EBITDA, 0), 0) * 100) AS EBITDA_Growth_Rate,
    ((bs_curr.Total_Assets - COALESCE(bs_prior.Total_Assets, 0)) /
     NULLIF(COALESCE(bs_prior.Total_Assets, 0), 0) * 100) AS Asset_Growth_Rate

FROM income_statement AS is_curr
JOIN balance_sheet AS bs_curr
    ON is_curr.Provider_Number = bs_curr.Provider_Number
    AND is_curr.Fiscal_Year = bs_curr.Fiscal_Year
LEFT JOIN income_statement AS is_prior
    ON is_curr.Provider_Number = is_prior.Provider_Number
    AND is_curr.Fiscal_Year = is_prior.Fiscal_Year + 1
LEFT JOIN balance_sheet AS bs_prior
    ON bs_curr.Provider_Number = bs_prior.Provider_Number
    AND bs_curr.Fiscal_Year = bs_prior.Fiscal_Year + 1
LEFT JOIN cash_flow_statement AS cf_curr
    ON is_curr.Provider_Number = cf_curr.Provider_Number
    AND is_curr.Fiscal_Year = cf_curr.Fiscal_Year
JOIN (SELECT DISTINCT Provider_Number, Provider_Name, Fiscal_Year, State_Code FROM income_statement) AS curr
    ON is_curr.Provider_Number = curr.Provider_Number
    AND is_curr.Fiscal_Year = curr.Fiscal_Year;
```

---

## Key Metrics for Hospital Valuation

### Primary Valuation Metrics

#### 1. **Net Patient Revenue (NPR)**
```
Source: Worksheet G-3, Line 3
Formula: Total Patient Revenue - Allowances & Discounts
Use: Primary revenue metric for valuation multiples
```

#### 2. **EBITDA**
```
Source: Calculated from Worksheets G-3, A, A-7
Formula: Net Income + Interest + Depreciation + Amortization + Tax
Use: Core profitability metric; basis for most hospital valuations
Typical Multiple: 6-12x EBITDA for hospital acquisitions
```

#### 3. **Operating Income**
```
Source: Worksheet G-3, Line 5
Formula: Net Patient Revenue - Operating Expenses
Use: Measure of core operational performance
```

#### 4. **Free Cash Flow (FCF)**
```
Source: Calculated from Balance Sheet and Income Statement
Formula: Operating Cash Flow - Capital Expenditures
Use: Measure of cash available for debt service, expansion, or distribution
```

### Financial Health Indicators

#### 5. **Operating Margin**
```
Formula: (Operating Income / Net Patient Revenue) × 100%
Benchmark:
  - Healthy: >5%
  - Marginal: 1-5%
  - Distressed: <1%
```

#### 6. **EBITDA Margin**
```
Formula: (EBITDA / Net Patient Revenue) × 100%
Benchmark:
  - Strong: >12%
  - Average: 7-12%
  - Weak: <7%
```

#### 7. **Days Cash on Hand**
```
Formula: Cash / (Operating Expenses / 365)
Benchmark:
  - Strong: >100 days
  - Adequate: 50-100 days
  - Weak: <50 days
```

#### 8. **Current Ratio**
```
Formula: Current Assets / Current Liabilities
Benchmark:
  - Healthy: >2.0
  - Adequate: 1.5-2.0
  - Weak: <1.5
```

#### 9. **Debt-to-Equity Ratio**
```
Formula: Total Liabilities / Total Equity
Benchmark:
  - Conservative: <1.0
  - Moderate: 1.0-2.0
  - Aggressive: >2.0
```

#### 10. **Return on Assets (ROA)**
```
Formula: (Net Income / Total Assets) × 100%
Benchmark:
  - Excellent: >5%
  - Good: 2-5%
  - Poor: <2%
```

---

## SQL Implementation Examples

### Example 1: Multi-Year Trend Analysis

```sql
-- Create a comprehensive trend view
CREATE VIEW hospital_trends AS
SELECT
    hvm.Provider_Number,
    hvm.Provider_Name,
    hvm.Fiscal_Year,
    hvm.State_Code,

    -- Current Year Metrics
    hvm.Net_Patient_Revenue,
    hvm.EBITDA,
    hvm.Operating_Margin,
    hvm.EBITDA_Margin,
    hvm.Current_Ratio,

    -- 3-Year Averages
    AVG(hvm.Net_Patient_Revenue) OVER (
        PARTITION BY hvm.Provider_Number
        ORDER BY hvm.Fiscal_Year
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS NPR_3Yr_Avg,

    AVG(hvm.EBITDA) OVER (
        PARTITION BY hvm.Provider_Number
        ORDER BY hvm.Fiscal_Year
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS EBITDA_3Yr_Avg,

    AVG(hvm.Operating_Margin) OVER (
        PARTITION BY hvm.Provider_Number
        ORDER BY hvm.Fiscal_Year
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS Operating_Margin_3Yr_Avg,

    -- Growth Metrics
    hvm.Revenue_Growth_Rate,
    hvm.EBITDA_Growth_Rate,

    -- Ranking within State
    RANK() OVER (
        PARTITION BY hvm.State_Code, hvm.Fiscal_Year
        ORDER BY hvm.EBITDA_Margin DESC
    ) AS EBITDA_Margin_Rank_In_State

FROM hospital_valuation_metrics AS hvm
ORDER BY hvm.Provider_Number, hvm.Fiscal_Year;
```

### Example 2: Peer Benchmarking

```sql
-- Compare hospital to state and national peers
SELECT
    curr.Provider_Number,
    curr.Provider_Name,
    curr.Fiscal_Year,
    curr.State_Code,

    -- Hospital Metrics
    curr.Net_Patient_Revenue,
    curr.EBITDA,
    curr.Operating_Margin,
    curr.EBITDA_Margin,
    curr.Current_Ratio,

    -- State Benchmarks
    AVG(state.EBITDA_Margin) AS State_Avg_EBITDA_Margin,
    STDDEV(state.EBITDA_Margin) AS State_StdDev_EBITDA_Margin,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY state.EBITDA_Margin) AS State_Median_EBITDA_Margin,

    -- National Benchmarks
    AVG(natl.EBITDA_Margin) AS National_Avg_EBITDA_Margin,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY natl.EBITDA_Margin) AS National_Median_EBITDA_Margin,

    -- Percentile Ranking
    PERCENT_RANK() OVER (
        PARTITION BY curr.State_Code, curr.Fiscal_Year
        ORDER BY curr.EBITDA_Margin
    ) * 100 AS State_Percentile,

    PERCENT_RANK() OVER (
        PARTITION BY curr.Fiscal_Year
        ORDER BY curr.EBITDA_Margin
    ) * 100 AS National_Percentile

FROM hospital_valuation_metrics AS curr
LEFT JOIN hospital_valuation_metrics AS state
    ON curr.State_Code = state.State_Code
    AND curr.Fiscal_Year = state.Fiscal_Year
LEFT JOIN hospital_valuation_metrics AS natl
    ON curr.Fiscal_Year = natl.Fiscal_Year

WHERE curr.Fiscal_Year = 2023  -- Example: Latest year
GROUP BY
    curr.Provider_Number, curr.Provider_Name, curr.Fiscal_Year, curr.State_Code,
    curr.Net_Patient_Revenue, curr.EBITDA, curr.Operating_Margin,
    curr.EBITDA_Margin, curr.Current_Ratio
ORDER BY curr.State_Code, curr.EBITDA_Margin DESC;
```

### Example 3: Valuation Screening

```sql
-- Identify hospitals meeting specific valuation criteria
SELECT
    hvm.Provider_Number,
    hvm.Provider_Name,
    hvm.State_Code,
    hvm.Fiscal_Year,

    -- Financial Metrics
    hvm.Net_Patient_Revenue / 1000000 AS NPR_Millions,
    hvm.EBITDA / 1000000 AS EBITDA_Millions,
    hvm.EBITDA_Margin,
    hvm.Operating_Margin,
    hvm.Current_Ratio,
    hvm.Debt_To_Equity,
    hvm.Days_Cash_On_Hand,

    -- Valuation Estimate (8x EBITDA multiple)
    (hvm.EBITDA * 8) / 1000000 AS Estimated_Value_8x_Millions,

    -- Quality Score (composite)
    (CASE WHEN hvm.EBITDA_Margin > 12 THEN 2
          WHEN hvm.EBITDA_Margin > 7 THEN 1
          ELSE 0 END +
     CASE WHEN hvm.Current_Ratio > 2.0 THEN 2
          WHEN hvm.Current_Ratio > 1.5 THEN 1
          ELSE 0 END +
     CASE WHEN hvm.Days_Cash_On_Hand > 100 THEN 2
          WHEN hvm.Days_Cash_On_Hand > 50 THEN 1
          ELSE 0 END +
     CASE WHEN hvm.Debt_To_Equity < 1.0 THEN 2
          WHEN hvm.Debt_To_Equity < 2.0 THEN 1
          ELSE 0 END) AS Financial_Quality_Score  -- Max: 8

FROM hospital_valuation_metrics AS hvm

WHERE hvm.Fiscal_Year = 2023  -- Latest year
    AND hvm.Net_Patient_Revenue > 50000000  -- Minimum $50M revenue
    AND hvm.EBITDA > 0  -- Profitable
    AND hvm.EBITDA_Margin > 5  -- Minimum 5% EBITDA margin
    AND hvm.Current_Ratio > 1.0  -- Adequate liquidity

ORDER BY (hvm.EBITDA * 8) DESC;  -- Sort by estimated value
```

---

## Data Validation Checkpoints

### Validation Checkpoint 1: Balance Sheet Balancing

```sql
-- Check that Assets = Liabilities + Equity
SELECT
    Provider_Number,
    Provider_Name,
    Fiscal_Year,
    Total_Assets,
    Total_Liabilities,
    Total_Fund_Balances,
    Total_Liabilities_And_Equity,
    Balance_Check,
    CASE
        WHEN ABS(Balance_Check) < 1.00 THEN 'PASS'
        WHEN ABS(Balance_Check) < 100.00 THEN 'WARNING'
        ELSE 'FAIL'
    END AS Validation_Status
FROM balance_sheet
WHERE ABS(Balance_Check) > 0.01  -- Flag any imbalance > $0.01
ORDER BY ABS(Balance_Check) DESC;
```

### Validation Checkpoint 2: Income Statement Reconciliation

```sql
-- Verify Net Income calculation
SELECT
    Provider_Number,
    Provider_Name,
    Fiscal_Year,
    Net_Patient_Revenue,
    Total_Operating_Expenses,
    Operating_Income,
    Total_Other_Income,
    Other_Expenses,
    Net_Income,

    -- Recalculate to verify
    (Net_Patient_Revenue - Total_Operating_Expenses + Total_Other_Income - Other_Expenses) AS Calculated_Net_Income,
    (Net_Income - (Net_Patient_Revenue - Total_Operating_Expenses + Total_Other_Income - Other_Expenses)) AS Variance,

    CASE
        WHEN ABS(Net_Income - (Net_Patient_Revenue - Total_Operating_Expenses + Total_Other_Income - Other_Expenses)) < 1.00 THEN 'PASS'
        ELSE 'FAIL'
    END AS Validation_Status

FROM income_statement
WHERE ABS(Net_Income - (Net_Patient_Revenue - Total_Operating_Expenses + Total_Other_Income - Other_Expenses)) > 0.01
ORDER BY ABS(Variance) DESC;
```

### Validation Checkpoint 3: Cash Flow Reconciliation

```sql
-- Verify cash change reconciles to calculated cash flows
SELECT
    cfs.Provider_Number,
    cfs.Provider_Name,
    cfs.Fiscal_Year,
    cfs.Net_Change_In_Cash AS Calculated_Cash_Change,

    -- Verify from Balance Sheet
    (bs_curr.Cash - bs_prior.Cash) AS Actual_Cash_Change,

    -- Calculate variance
    (cfs.Net_Change_In_Cash - (bs_curr.Cash - bs_prior.Cash)) AS Variance,

    CASE
        WHEN ABS(cfs.Net_Change_In_Cash - (bs_curr.Cash - bs_prior.Cash)) < 100.00 THEN 'PASS'
        WHEN ABS(cfs.Net_Change_In_Cash - (bs_curr.Cash - bs_prior.Cash)) < 1000.00 THEN 'WARNING'
        ELSE 'FAIL'
    END AS Validation_Status

FROM cash_flow_statement AS cfs
JOIN balance_sheet AS bs_curr
    ON cfs.Provider_Number = bs_curr.Provider_Number
    AND cfs.Fiscal_Year = bs_curr.Fiscal_Year
LEFT JOIN balance_sheet AS bs_prior
    ON cfs.Provider_Number = bs_prior.Provider_Number
    AND cfs.Fiscal_Year = bs_prior.Fiscal_Year + 1

WHERE ABS(cfs.Net_Change_In_Cash - (bs_curr.Cash - COALESCE(bs_prior.Cash, 0))) > 100
ORDER BY ABS(Variance) DESC;
```

### Validation Checkpoint 4: Ratio Reasonableness

```sql
-- Identify outlier ratios that may indicate data quality issues
SELECT
    Provider_Number,
    Provider_Name,
    Fiscal_Year,
    State_Code,

    -- Flag unreasonable values
    Operating_Margin,
    CASE
        WHEN Operating_Margin < -50 OR Operating_Margin > 50 THEN 'OUT_OF_RANGE'
        ELSE 'OK'
    END AS Operating_Margin_Flag,

    EBITDA_Margin,
    CASE
        WHEN EBITDA_Margin < -50 OR EBITDA_Margin > 50 THEN 'OUT_OF_RANGE'
        ELSE 'OK'
    END AS EBITDA_Margin_Flag,

    Current_Ratio,
    CASE
        WHEN Current_Ratio < 0 OR Current_Ratio > 10 THEN 'OUT_OF_RANGE'
        ELSE 'OK'
    END AS Current_Ratio_Flag,

    Debt_To_Equity,
    CASE
        WHEN Debt_To_Equity < 0 OR Debt_To_Equity > 20 THEN 'OUT_OF_RANGE'
        ELSE 'OK'
    END AS Debt_To_Equity_Flag

FROM hospital_valuation_metrics

WHERE Operating_Margin < -50 OR Operating_Margin > 50
   OR EBITDA_Margin < -50 OR EBITDA_Margin > 50
   OR Current_Ratio < 0 OR Current_Ratio > 10
   OR Debt_To_Equity < 0 OR Debt_To_Equity > 20

ORDER BY Provider_Number, Fiscal_Year;
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Multiple Reports per Provider/Year

**Problem:** Hospitals may file amended reports, resulting in duplicate records.

**Solution:** Always filter by `Report_Status` and keep most recent:
```sql
-- Keep only final or as-submitted reports
WHERE Report_Status IN ('A', 'F')

-- Or keep most recent by Process_Date
WHERE Report_Record_Number IN (
    SELECT Report_Record_Number
    FROM (
        SELECT Report_Record_Number,
               ROW_NUMBER() OVER (
                   PARTITION BY Provider_Number, YEAR(FY_End)
                   ORDER BY Report_Status DESC, Process_Date DESC
               ) AS rn
        FROM rpt_data
    ) sub
    WHERE rn = 1
)
```

### Pitfall 2: Negative Values for Accumulated Depreciation

**Problem:** Accumulated depreciation is stored as positive but represents a contra-asset.

**Solution:** Apply negation when calculating net PP&E:
```sql
-- Buildings Net = Buildings Gross - ABS(Accumulated Depreciation)
Buildings_Net = Buildings_Gross - ABS(Buildings_Accumulated_Depreciation)
```

### Pitfall 3: Missing Line/Column Descriptions

**Problem:** Not all Line/Column combinations have descriptions in the names file.

**Solution:** Use LEFT JOIN and handle nulls:
```sql
LEFT JOIN worksheet_names AS names
    ON nmrc.Worksheet = names.Worksheet
    AND nmrc.Line = names.Line
    AND nmrc.Column = names.Column

-- Filter out unmatched records if necessary
WHERE names.Line_Name IS NOT NULL
```

### Pitfall 4: Fiscal Year vs. Calendar Year

**Problem:** Hospitals may have fiscal years that don't align with calendar years.

**Solution:** Always use `FY_End` to determine fiscal year:
```sql
-- Extract fiscal year from FY_End date
Fiscal_Year = YEAR(FY_End)

-- For fiscal years ending before June 30, you may need special handling
CASE
    WHEN MONTH(FY_End) < 7 THEN YEAR(FY_End)
    ELSE YEAR(FY_End) + 1
END AS Fiscal_Year
```

### Pitfall 5: COVID-19 Impact on Metrics

**Problem:** 2020-2021 data may be distorted by COVID relief funds and PPE expenses.

**Solution:** Separate COVID-related items:
```sql
-- Extract COVID relief separately
COVID_Relief_Funds = Line 02200 + Line 02450

-- Create adjusted EBITDA excluding COVID relief
Adjusted_EBITDA = EBITDA - COVID_Relief_Funds

-- Flag COVID-era years in analysis
CASE
    WHEN Fiscal_Year IN (2020, 2021) THEN 'COVID_ERA'
    ELSE 'NORMAL'
END AS Period_Flag
```

### Pitfall 6: Zero or Null Values in Denominators

**Problem:** Division by zero errors when calculating ratios.

**Solution:** Use NULLIF or COALESCE:
```sql
-- Safe ratio calculation
Operating_Margin = Operating_Income / NULLIF(Net_Patient_Revenue, 0) * 100

-- Or return NULL if denominator is zero
Operating_Margin = CASE
    WHEN Net_Patient_Revenue = 0 OR Net_Patient_Revenue IS NULL THEN NULL
    ELSE Operating_Income / Net_Patient_Revenue * 100
END
```

### Pitfall 7: Mixing Different Report Versions

**Problem:** CMS has updated cost report forms over time (2552-96 vs. 2552-10).

**Solution:** Filter to specific form version and date ranges:
```sql
-- Only use CMS-2552-10 (effective May 2010+)
WHERE FY_Begin >= '2010-05-01'

-- Check form version in rpt metadata if available
AND Form_Version = '2552-10'
```

---

## Conclusion

This methodology provides a comprehensive framework for extracting and calculating hospital financial metrics from HCRIS data. The key steps are:

1. **Extract** raw data from Worksheets G, G-3, A, A-7
2. **Transform** into structured financial statements (Balance Sheet, Income Statement, Cash Flow)
3. **Calculate** key valuation metrics (EBITDA, margins, ratios)
4. **Validate** data quality at each step
5. **Analyze** trends and benchmarks

The resulting tables provide a complete foundation for hospital valuation analysis, M&A screening, and financial benchmarking.

---

**Document Prepared By:** Claude Code
**Based On:** CMS Provider Reimbursement Manual, Part 2, Chapter 40
**Form:** CMS-2552-10 (Hospital and Hospital Health Care Complex Cost Report)
**Last Updated:** 2025-11-13
