# Data Structure Guide for Analysts

## Overview

This guide explains how CMS HCRIS hospital cost report data is stored in the DuckDB database and how to transform and adjust values for financial analysis.

**Database**: `data/hospital_worksheets.duckdb` (182.5 MB)
**Records**: 2.58 million across 25 worksheets
**Providers**: 229 hospitals (97 NJ, 132 NC)
**Time Period**: FY 2020-2024

---

## Core Concept: Long Format Storage

### How Traditional Financial Statements Look (Wide Format)

```
Balance Sheet - Hospital 310001 - FY 2024
┌─────────────────────────────────┬──────────┬──────────┐
│ Line Description                │ Beg Year │ End Year │
├─────────────────────────────────┼──────────┼──────────┤
│ Cash and Cash Equivalents       │ 5,000,000│ 6,200,000│
│ Accounts Receivable             │15,000,000│16,500,000│
│ Inventory                       │ 2,000,000│ 2,100,000│
│ Total Current Assets            │22,000,000│24,800,000│
└─────────────────────────────────┴──────────┴──────────┘
```

### How We Store It (Long Format)

```
┌──────────┬──────┬────────┬───────────────────────┬──────────────┬────────────┐
│ Provider │ Year │  Line  │   line_level1         │    Column    │   Value    │
├──────────┼──────┼────────┼───────────────────────┼──────────────┼────────────┤
│ 310001   │ 2024 │ 00100  │ Cash & Cash Equiv     │    00100     │  5,000,000 │
│ 310001   │ 2024 │ 00100  │ Cash & Cash Equiv     │    00200     │  6,200,000 │
│ 310001   │ 2024 │ 00200  │ Accounts Receivable   │    00100     │ 15,000,000 │
│ 310001   │ 2024 │ 00200  │ Accounts Receivable   │    00200     │ 16,500,000 │
│ 310001   │ 2024 │ 00300  │ Inventory             │    00100     │  2,000,000 │
│ 310001   │ 2024 │ 00300  │ Inventory             │    00200     │  2,100,000 │
└──────────┴──────┴────────┴───────────────────────┴──────────────┴────────────┘
```

**Why Long Format?**
- More flexible for filtering and aggregation
- Easier to add new worksheets without changing schema
- Standard format for all 25 worksheets
- Optimized for analytical queries (columnar storage)

---

## Database Schema

### Main Worksheet Tables (25 tables)

All worksheet tables follow this identical structure:

```sql
CREATE TABLE worksheet_g000000 (
    state_code        VARCHAR,      -- '31' (NJ) or '34' (NC)
    fiscal_year       INTEGER,      -- 2020, 2021, 2022, 2023, 2024
    Provider_Number   VARCHAR,      -- '310001' (Hospital CCN)
    FY_Begin_Date     DATE,         -- Fiscal year start
    FY_End_Date       DATE,         -- Fiscal year end
    Worksheet         VARCHAR,      -- 'G000000' (worksheet code)
    Line              VARCHAR,      -- '00100' (5-digit line number)
    "Column"          VARCHAR,      -- '00100' (5-digit column number)
    Report_Name       VARCHAR,      -- 'Balance Sheet'
    line_level1       VARCHAR,      -- 'ASSETS'
    line_level2       VARCHAR,      -- 'Current Assets'
    col_level1        VARCHAR,      -- 'Beginning Balance'
    col_level2        VARCHAR,      -- NULL or additional detail
    Value             DOUBLE        -- 1234567.89
);
```

### Key Points for Analysts

1. **Line and Column are STRINGS, not numbers**
   - Always use quotes: `WHERE Line = '00100'`
   - Always zero-padded to 5 digits: `'00100'`, not `'100'`

2. **Value column contains ALL numeric data**
   - Positive: Costs, expenses, assets, revenues
   - Negative: Credits, reductions, contra-accounts
   - Zero: May mean "not applicable" or truly zero

3. **Descriptions are in 4 columns**
   - `line_level1` + `line_level2` = Row description
   - `col_level1` + `col_level2` = Column description

4. **Column name "Column" must be quoted**
   - Correct: `SELECT "Column" FROM ...`
   - Wrong: `SELECT Column FROM ...` (will error)

---

## Understanding Line and Column Codes

### Line Numbering Pattern

Lines use a hierarchical numbering system:

```
00100 - Parent/Summary Line
  00101 - Detail line (child)
  00102 - Detail line (child)
  00103 - Detail line (child)
00200 - Parent/Summary Line
  00201 - Detail line (child)
  00202 - Detail line (child)
```

**Examples from Balance Sheet (G000000)**:

```
Line    Description
-----   -----------
00100   Total Current Assets (summary)
00101     Cash and Cash Equivalents (detail)
00102     Short-term Investments (detail)
00103     Accounts Receivable (detail)
00104     Inventory (detail)
00105     Prepaid Expenses (detail)
```

### Column Numbering Pattern

Columns represent different time periods or categories:

```
Column  Description (Balance Sheet)
------  ---------------------------
00100   Beginning of Year Balance
00200   End of Year Balance

Column  Description (Income Statement)
------  --------------------------------
00100   Current Year
00200   Prior Year
00300   Budget

Column  Description (Cost Allocation)
------  -------------------------------
00100   Department A receiving allocation
00200   Department B receiving allocation
00300   Department C receiving allocation
```

---

## How to Transform Data

### 1. Converting Long to Wide Format (Pivot)

**Problem**: You want a traditional financial statement layout

**Solution**: Pivot on Column

```sql
-- Balance Sheet in wide format
SELECT
    Line,
    line_level1 as Description,
    MAX(CASE WHEN "Column" = '00100' THEN Value ELSE NULL END) as Beginning_Balance,
    MAX(CASE WHEN "Column" = '00200' THEN Value ELSE NULL END) as Ending_Balance,
    (MAX(CASE WHEN "Column" = '00200' THEN Value ELSE 0 END) -
     MAX(CASE WHEN "Column" = '00100' THEN Value ELSE 0 END)) as Change
FROM worksheet_g000000
WHERE Provider_Number = '310001'
    AND fiscal_year = 2024
    AND state_code = '31'
GROUP BY Line, line_level1
ORDER BY Line;
```

**Result**:
```
Line    Description                Beginning_Balance  Ending_Balance    Change
-----   -------------------------  ----------------  ---------------  ----------
00100   Total Current Assets         22,000,000        24,800,000     2,800,000
00101   Cash & Cash Equiv             5,000,000         6,200,000     1,200,000
00102   Short-term Investments        3,000,000         3,500,000       500,000
...
```

### 2. Filtering to Summary Lines Only

**Problem**: Detail lines (00101, 00102) clutter your report; you only want summary lines (00100, 00200)

**Solution**: Filter where last 2 digits are '00'

```sql
-- Summary lines only
SELECT
    Line,
    line_level1,
    "Column",
    col_level1,
    Value
FROM worksheet_g000000
WHERE Provider_Number = '310001'
    AND fiscal_year = 2024
    AND RIGHT(Line, 2) = '00'        -- Only lines ending in 00
    AND RIGHT("Column", 2) = '00'    -- Only columns ending in 00
ORDER BY Line, "Column";
```

### 3. Calculating Totals from Detail Lines

**Problem**: You need to verify that detail lines sum to the total

**Solution**: Group by parent line

```sql
-- Verify Current Assets total
WITH detail_lines AS (
    SELECT
        SUBSTRING(Line, 1, 3) || '00' as Parent_Line,
        SUM(Value) as Calculated_Total
    FROM worksheet_g000000
    WHERE Provider_Number = '310001'
        AND fiscal_year = 2024
        AND "Column" = '00200'  -- End of year
        AND Line LIKE '001%'    -- Current assets section
        AND Line != '00100'     -- Exclude the total line itself
    GROUP BY SUBSTRING(Line, 1, 3) || '00'
),
reported_total AS (
    SELECT
        Line as Parent_Line,
        Value as Reported_Total
    FROM worksheet_g000000
    WHERE Provider_Number = '310001'
        AND fiscal_year = 2024
        AND "Column" = '00200'
        AND Line = '00100'
)
SELECT
    d.Parent_Line,
    d.Calculated_Total,
    r.Reported_Total,
    d.Calculated_Total - r.Reported_Total as Difference
FROM detail_lines d
LEFT JOIN reported_total r ON d.Parent_Line = r.Parent_Line;
```

### 4. Handling NULL and Missing Descriptions

**Problem**: Some lines have NULL in `line_level1` or `col_level1`

**Solution**: Use COALESCE to provide defaults

```sql
-- Safe description handling
SELECT
    Line,
    COALESCE(line_level1, '') || ' ' || COALESCE(line_level2, '') as Full_Description,
    "Column",
    COALESCE(col_level1, 'No Description') as Column_Description,
    Value
FROM worksheet_g000000
WHERE Provider_Number = '310001'
    AND fiscal_year = 2024
ORDER BY Line, "Column";
```

### 5. Multi-Year Comparisons

**Problem**: You want to compare the same line item across multiple years

**Solution**: Pivot on fiscal_year

```sql
-- 5-Year trend for Total Operating Revenue
SELECT
    Line,
    line_level1 as Description,
    MAX(CASE WHEN fiscal_year = 2020 THEN Value END) as FY2020,
    MAX(CASE WHEN fiscal_year = 2021 THEN Value END) as FY2021,
    MAX(CASE WHEN fiscal_year = 2022 THEN Value END) as FY2022,
    MAX(CASE WHEN fiscal_year = 2023 THEN Value END) as FY2023,
    MAX(CASE WHEN fiscal_year = 2024 THEN Value END) as FY2024,
    -- Calculate compound annual growth rate
    POWER(
        MAX(CASE WHEN fiscal_year = 2024 THEN Value END) /
        MAX(CASE WHEN fiscal_year = 2020 THEN Value END),
        1.0/4
    ) - 1 as CAGR_4yr
FROM worksheet_g300000
WHERE Provider_Number = '310001'
    AND state_code = '31'
    AND Line = '00100'  -- Total Operating Revenue line
GROUP BY Line, line_level1;
```

### 6. Joining Multiple Worksheets

**Problem**: You need data from Balance Sheet AND Income Statement

**Solution**: Join on Provider_Number, fiscal_year, state_code

```sql
-- Calculate Return on Assets (ROA)
WITH income AS (
    SELECT
        Provider_Number,
        fiscal_year,
        state_code,
        SUM(CASE WHEN line_level1 LIKE '%Net Income%' THEN Value ELSE 0 END) as net_income
    FROM worksheet_g300000
    GROUP BY Provider_Number, fiscal_year, state_code
),
assets AS (
    SELECT
        Provider_Number,
        fiscal_year,
        state_code,
        SUM(CASE WHEN Line LIKE '00%' AND "Column" = '00200' THEN Value ELSE 0 END) as total_assets
    FROM worksheet_g000000
    GROUP BY Provider_Number, fiscal_year, state_code
)
SELECT
    i.Provider_Number,
    i.fiscal_year,
    i.net_income,
    a.total_assets,
    (i.net_income / a.total_assets) * 100 as ROA_pct
FROM income i
INNER JOIN assets a
    ON i.Provider_Number = a.Provider_Number
    AND i.fiscal_year = a.fiscal_year
    AND i.state_code = a.state_code
WHERE i.Provider_Number = '310001'
ORDER BY i.fiscal_year;
```

---

## Common Adjustments and Calculations

### 1. Handling Negative Values

**Revenue Adjustments** (G200000):
- Gross Revenue: Positive values
- Contractual Allowances: **Negative values** (reduce gross revenue)
- Bad Debt: **Negative values**
- Net Revenue = Gross + Contractual + Bad Debt

```sql
-- Calculate Net Patient Revenue
SELECT
    Provider_Number,
    fiscal_year,
    SUM(CASE WHEN line_level1 LIKE '%Gross%' THEN Value ELSE 0 END) as gross_revenue,
    SUM(CASE WHEN line_level1 LIKE '%Contractual%' THEN Value ELSE 0 END) as contractual_allowances,  -- Negative
    SUM(CASE WHEN line_level1 LIKE '%Bad Debt%' THEN Value ELSE 0 END) as bad_debt,  -- Negative
    SUM(Value) as net_revenue
FROM worksheet_g200000
WHERE Provider_Number = '310001'
    AND fiscal_year = 2024
GROUP BY Provider_Number, fiscal_year;
```

### 2. Per-Unit Calculations

**Problem**: You need cost per admission, revenue per day, etc.

**Solution**: Join financial data with utilization statistics

```sql
-- Cost per Admission
WITH costs AS (
    SELECT
        Provider_Number,
        fiscal_year,
        SUM(CASE WHEN line_level1 LIKE '%Total%Expense%' THEN Value ELSE 0 END) as total_cost
    FROM worksheet_g300000
    GROUP BY Provider_Number, fiscal_year
),
volume AS (
    SELECT
        Provider_Number,
        fiscal_year,
        SUM(CASE WHEN line_level1 LIKE '%Admissions%' THEN Value ELSE 0 END) as total_admissions
    FROM worksheet_s300001
    GROUP BY Provider_Number, fiscal_year
)
SELECT
    c.Provider_Number,
    c.fiscal_year,
    c.total_cost,
    v.total_admissions,
    c.total_cost / NULLIF(v.total_admissions, 0) as cost_per_admission
FROM costs c
INNER JOIN volume v
    ON c.Provider_Number = v.Provider_Number
    AND c.fiscal_year = v.fiscal_year
WHERE c.Provider_Number = '310001'
ORDER BY c.fiscal_year;
```

### 3. Percentage Calculations

**Common-Size Analysis**:

```sql
-- Income Statement as % of Revenue
WITH revenue AS (
    SELECT
        Provider_Number,
        fiscal_year,
        SUM(CASE WHEN line_level1 LIKE '%Operating Revenue%' AND Line = '00100' THEN Value ELSE 0 END) as total_revenue
    FROM worksheet_g300000
    GROUP BY Provider_Number, fiscal_year
)
SELECT
    i.Line,
    i.line_level1 as Expense_Category,
    i.Value as Dollar_Amount,
    (i.Value / r.total_revenue) * 100 as Percent_of_Revenue
FROM worksheet_g300000 i
INNER JOIN revenue r
    ON i.Provider_Number = r.Provider_Number
    AND i.fiscal_year = r.fiscal_year
WHERE i.Provider_Number = '310001'
    AND i.fiscal_year = 2024
    AND i.line_level1 LIKE '%Expense%'
ORDER BY ABS(i.Value) DESC;
```

### 4. Year-over-Year Growth

```sql
-- Revenue Growth Rate
WITH current_year AS (
    SELECT
        Provider_Number,
        Value as current_revenue
    FROM worksheet_g300000
    WHERE Provider_Number = '310001'
        AND fiscal_year = 2024
        AND Line = '00100'  -- Total Operating Revenue
),
prior_year AS (
    SELECT
        Provider_Number,
        Value as prior_revenue
    FROM worksheet_g300000
    WHERE Provider_Number = '310001'
        AND fiscal_year = 2023
        AND Line = '00100'
)
SELECT
    c.Provider_Number,
    c.current_revenue,
    p.prior_revenue,
    c.current_revenue - p.prior_revenue as dollar_change,
    ((c.current_revenue - p.prior_revenue) / p.prior_revenue) * 100 as pct_change
FROM current_year c
INNER JOIN prior_year p ON c.Provider_Number = p.Provider_Number;
```

---

## Working with Different Worksheet Types

### Financial Statements (G-Series)

**G000000 - Balance Sheet**:
```sql
-- Structure: Lines = Balance sheet items, Columns = Time periods

-- Get all assets at end of year
SELECT Line, line_level1, line_level2, Value
FROM worksheet_g000000
WHERE Provider_Number = '310001'
    AND fiscal_year = 2024
    AND "Column" = '00200'  -- End of year
    AND Line LIKE '0%'      -- Assets section
ORDER BY Line;
```

**G300000 - Income Statement**:
```sql
-- Structure: Lines = Revenue/Expense items, Columns = Usually just one (current year)

-- Calculate operating margin
SELECT
    SUM(CASE WHEN line_level1 LIKE '%Operating Revenue%' THEN Value ELSE 0 END) as op_revenue,
    SUM(CASE WHEN line_level1 LIKE '%Operating Expense%' THEN Value ELSE 0 END) as op_expense,
    (op_revenue - op_expense) / op_revenue * 100 as operating_margin_pct
FROM worksheet_g300000
WHERE Provider_Number = '310001' AND fiscal_year = 2024;
```

**G200000 - Patient Revenue**:
```sql
-- Structure: Lines = Service types, Columns = Payer types

-- Payer mix analysis
SELECT
    "Column" as Payer_Code,
    col_level1 as Payer_Name,
    SUM(Value) as Total_Revenue,
    SUM(Value) * 100.0 / SUM(SUM(Value)) OVER () as Pct_of_Total
FROM worksheet_g200000
WHERE Provider_Number = '310001'
    AND fiscal_year = 2024
GROUP BY "Column", col_level1
ORDER BY Total_Revenue DESC;
```

### Cost Allocation (B-Series)

**Structure**: Lines = Cost centers being allocated FROM, Columns = Departments receiving allocation

```sql
-- Total overhead allocated to Emergency Department
SELECT
    SUM(Value) as total_overhead_allocated
FROM worksheet_b100000
WHERE Provider_Number = '310001'
    AND fiscal_year = 2024
    AND "Column" = '00500'  -- Emergency Department column
    AND col_level1 LIKE '%Emergency%';
```

### Statistical Data (S-Series)

**S300001 - Utilization**:
```sql
-- Calculate occupancy rate
WITH bed_data AS (
    SELECT
        SUM(CASE WHEN line_level1 LIKE '%Patient Days%' THEN Value ELSE 0 END) as patient_days,
        SUM(CASE WHEN line_level1 LIKE '%Available Beds%' THEN Value ELSE 0 END) as available_beds
    FROM worksheet_s300001
    WHERE Provider_Number = '310001' AND fiscal_year = 2024
)
SELECT
    patient_days,
    available_beds,
    patient_days / (available_beds * 365) * 100 as occupancy_rate_pct
FROM bed_data;
```

---

## Data Quality Checks

### 1. Check for Missing Data

```sql
-- Providers with incomplete years
SELECT
    Provider_Number,
    COUNT(DISTINCT fiscal_year) as years_with_data,
    MIN(fiscal_year) as first_year,
    MAX(fiscal_year) as last_year
FROM worksheet_g000000
GROUP BY Provider_Number
HAVING COUNT(DISTINCT fiscal_year) < 5  -- Less than 5 years
ORDER BY Provider_Number;
```

### 2. Identify Outliers

```sql
-- Find providers with unusual operating margins
WITH margins AS (
    SELECT
        Provider_Number,
        fiscal_year,
        SUM(CASE WHEN line_level1 LIKE '%Operating Revenue%' THEN Value ELSE 0 END) as revenue,
        SUM(CASE WHEN line_level1 LIKE '%Operating Expense%' THEN Value ELSE 0 END) as expense,
        (revenue - expense) / revenue * 100 as margin_pct
    FROM worksheet_g300000
    WHERE fiscal_year = 2024
    GROUP BY Provider_Number, fiscal_year
)
SELECT
    Provider_Number,
    margin_pct,
    AVG(margin_pct) OVER () as avg_margin,
    STDDEV(margin_pct) OVER () as stddev_margin
FROM margins
WHERE ABS(margin_pct - AVG(margin_pct) OVER ()) > 2 * STDDEV(margin_pct) OVER ()  -- More than 2 std devs
ORDER BY margin_pct;
```

### 3. Verify Data Completeness

```sql
-- Check if all expected worksheets exist for a provider
SELECT
    w.worksheet_code,
    CASE WHEN d.Worksheet IS NOT NULL THEN 'Present' ELSE 'Missing' END as status
FROM (
    VALUES
        ('G000000'), ('G100000'), ('G200000'), ('G300000'),
        ('B000001'), ('B000002'), ('B100000'),
        ('S300001'), ('S300002')
) AS w(worksheet_code)
LEFT JOIN (
    SELECT DISTINCT Worksheet
    FROM all_worksheets
    WHERE Provider_Number = '310001' AND fiscal_year = 2024
) AS d ON w.worksheet_code = d.Worksheet
ORDER BY w.worksheet_code;
```

---

## Performance Tips for Analysts

### 1. Always Filter on Indexed Columns First

```sql
-- ✅ GOOD: Filters on indexed columns
SELECT *
FROM worksheet_g000000
WHERE state_code = '31'          -- Indexed
    AND fiscal_year = 2024        -- Indexed
    AND Provider_Number = '310001' -- Indexed
    AND Line = '00100';

-- ❌ BAD: No filters on indexed columns
SELECT *
FROM worksheet_g000000
WHERE line_level1 LIKE '%Cash%';  -- Not indexed, slow full scan
```

### 2. Use Specific Tables Instead of Views

```sql
-- ✅ GOOD: Query specific table
SELECT * FROM worksheet_g000000 WHERE ...

-- ❌ BAD: Query view (scans all 25 tables)
SELECT * FROM all_worksheets WHERE Worksheet = 'G000000' AND ...
```

### 3. Select Only Needed Columns

```sql
-- ✅ GOOD: Only necessary columns
SELECT Line, line_level1, Value
FROM worksheet_g000000
WHERE ...

-- ❌ BAD: All columns (slower)
SELECT *
FROM worksheet_g000000
WHERE ...
```

### 4. Use CTEs for Readability

```sql
-- ✅ GOOD: Clear, maintainable
WITH revenue AS (
    SELECT Provider_Number, fiscal_year, SUM(Value) as total_revenue
    FROM worksheet_g300000
    WHERE line_level1 LIKE '%Revenue%'
    GROUP BY Provider_Number, fiscal_year
),
expenses AS (
    SELECT Provider_Number, fiscal_year, SUM(Value) as total_expense
    FROM worksheet_g300000
    WHERE line_level1 LIKE '%Expense%'
    GROUP BY Provider_Number, fiscal_year
)
SELECT
    r.Provider_Number,
    r.fiscal_year,
    r.total_revenue,
    e.total_expense,
    r.total_revenue - e.total_expense as net_income
FROM revenue r
INNER JOIN expenses e USING (Provider_Number, fiscal_year);
```

---

## Python Integration

### Connect and Query

```python
import duckdb
import pandas as pd

# Connect to database
con = duckdb.connect('data/hospital_worksheets.duckdb', read_only=True)

# Execute query and return DataFrame
df = con.execute("""
    SELECT
        Provider_Number,
        fiscal_year,
        Line,
        line_level1,
        Value
    FROM worksheet_g000000
    WHERE Provider_Number = '310001'
        AND fiscal_year = 2024
    ORDER BY Line
""").df()

# Now work with pandas DataFrame
print(df.head())
print(df.describe())

# Close connection
con.close()
```

### Pivot in Python

```python
# Query long format
df_long = con.execute("""
    SELECT
        Line,
        line_level1 as Description,
        "Column",
        col_level1 as Column_Name,
        Value
    FROM worksheet_g000000
    WHERE Provider_Number = '310001'
        AND fiscal_year = 2024
""").df()

# Pivot to wide format
df_wide = df_long.pivot(
    index=['Line', 'Description'],
    columns='Column_Name',
    values='Value'
).reset_index()

print(df_wide)
```

---

## Common SQL Patterns

### 1. Get Latest Year Data

```sql
-- Automatically get most recent year for each provider
WITH latest_year AS (
    SELECT Provider_Number, MAX(fiscal_year) as max_year
    FROM worksheet_g000000
    GROUP BY Provider_Number
)
SELECT w.*
FROM worksheet_g000000 w
INNER JOIN latest_year ly
    ON w.Provider_Number = ly.Provider_Number
    AND w.fiscal_year = ly.max_year
WHERE w.Provider_Number = '310001';
```

### 2. Running Totals

```sql
-- Cumulative revenue over time
SELECT
    fiscal_year,
    Value as annual_revenue,
    SUM(Value) OVER (
        ORDER BY fiscal_year
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) as cumulative_revenue
FROM worksheet_g300000
WHERE Provider_Number = '310001'
    AND Line = '00100'  -- Total Operating Revenue
ORDER BY fiscal_year;
```

### 3. Ranking and Percentiles

```sql
-- Rank hospitals by operating margin
WITH margins AS (
    SELECT
        Provider_Number,
        state_code,
        fiscal_year,
        SUM(CASE WHEN line_level1 LIKE '%Operating Revenue%' THEN Value ELSE 0 END) as revenue,
        SUM(CASE WHEN line_level1 LIKE '%Operating Expense%' THEN Value ELSE 0 END) as expense
    FROM worksheet_g300000
    WHERE fiscal_year = 2024
    GROUP BY Provider_Number, state_code, fiscal_year
)
SELECT
    Provider_Number,
    (revenue - expense) / revenue * 100 as operating_margin_pct,
    RANK() OVER (ORDER BY (revenue - expense) / revenue DESC) as margin_rank,
    NTILE(4) OVER (ORDER BY (revenue - expense) / revenue) as quartile
FROM margins
ORDER BY margin_rank;
```

---

## Quick Reference: Line Number Patterns

| Pattern | Meaning | Example |
|---------|---------|---------|
| `Line LIKE '00%'` | Section 0 (often Assets) | 00100, 00200, 00300 |
| `Line LIKE '10%'` | Section 1 (often Liabilities) | 10100, 10200 |
| `Line LIKE '20%'` | Section 2 (often Equity) | 20100, 20200 |
| `Line LIKE '%00'` | Summary/Total lines | 00100, 01500, 10200 |
| `Line LIKE '001__'` | Detail under 00100 | 00101, 00102, 00103 |
| `RIGHT(Line, 2) = '00'` | Lines ending in 00 | 00100, 05600, 10000 |
| `SUBSTRING(Line, 1, 3)` | First 3 digits (parent) | '001' from '00101' |

---

## Summary: Key Takeaways for Analysts

1. **All data is stored in long format** - one row per Line/Column/Value combination
2. **Line and Column are STRINGS** - always use quotes and 5-digit zero-padding
3. **Column name must be quoted** - `"Column"` not `Column`
4. **Filter on indexed columns** - state_code, fiscal_year, Provider_Number for speed
5. **Use specific tables** - worksheet_g000000 faster than all_worksheets view
6. **Pivot when needed** - use CASE/MAX or Python pandas for wide format
7. **Handle NULLs** - use COALESCE for descriptions
8. **Lines ending in 00** - summary lines; others are detail
9. **Negative values are meaningful** - contractual allowances, reductions
10. **Join on Provider + Year + State** - when combining worksheets

---

## Getting Help

**Check worksheet content**:
```sql
SELECT * FROM worksheet_g000000 WHERE Provider_Number = '310001' LIMIT 10;
```

**List all providers**:
```sql
SELECT * FROM provider_list ORDER BY Provider_Number;
```

**Check data availability**:
```sql
SELECT * FROM worksheet_summary ORDER BY Worksheet, fiscal_year;
```

**View all tables**:
```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'main';
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-09
**For Questions**: Refer to DATABASE_BUILD_COMPLETE.md for detailed worksheet descriptions
