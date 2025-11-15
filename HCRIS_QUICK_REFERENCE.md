# HCRIS Quick Reference Guide
## Essential Formulas and Worksheet Mappings

**Last Updated:** 2025-11-13

---

## Key Worksheet Codes

| Code | Worksheet Name | Primary Use |
|------|----------------|-------------|
| **G000000** | Balance Sheet | Assets, Liabilities, Equity |
| **G100000** | Changes in Fund Balances | Equity reconciliation |
| **G200000** | Patient Revenues & Operating Expenses | Revenue/expense detail |
| **G300000** | Statement of Revenues & Expenses | **INCOME STATEMENT** ⭐ |
| **A000000** | Trial Balance | Expense detail by cost center |
| **A700000** | Capital Assets Analysis | Depreciation |
| **S300000** | Statistical Data | Patient days, discharges |

---

## Essential Valuation Formulas

### Net Patient Revenue
```
Worksheet G-3, Line 00300, Column 00100

= Total Patient Revenue (Line 00100)
  - Allowances & Discounts (Line 00200)
```

### Operating Income
```
Worksheet G-3, Line 00500, Column 00100

= Net Patient Revenue (Line 00300)
  - Total Operating Expenses (Line 00400)
```

### Net Income
```
Worksheet G-3, Line 02900, Column 00100

= Operating Income (Line 00500)
  + Total Other Income (Line 02500)
  - Other Expenses (Line 02800)
```

### EBITDA
```
CALCULATED FROM MULTIPLE WORKSHEETS:

= Net Income (G-3, Line 02900)
  + Interest Expense (A, Line 11300, Column 00300)
  + Depreciation (A-7, Columns 00900-01400, Line 20000)
  + Amortization (if applicable)
  + Income Tax (if investor-owned)
```

### Free Cash Flow
```
CALCULATED:

= Operating Cash Flow
  - Capital Expenditures
```

---

## Key Balance Sheet Line Items (Worksheet G)

### Assets

| Line | Column | Item | Formula |
|------|--------|------|---------|
| 00100 | 00500 | Cash | Direct |
| 00200 | 00500 | Temporary Investments | Direct |
| 00400 | 00500 | Accounts Receivable (Gross) | Direct |
| 00600 | 00500 | Allowance for Doubtful Accounts | Direct (negative) |
| 01100 | 00500 | **Total Current Assets** | Sum Lines 1-10 |
| 01500 | 00500 | Buildings (Gross) | Direct |
| 01600 | 00500 | Buildings Accum. Depreciation | Direct (negative) |
| 02300 | 00500 | Equipment (Gross) | Direct |
| 02400 | 00500 | Equipment Accum. Depreciation | Direct (negative) |
| 03000 | 00500 | **Total PP&E (Net)** | Sum Lines 12-29 |
| 03600 | 00500 | **TOTAL ASSETS** | Sum Lines 11+30+35 |

### Liabilities & Equity

| Line | Column | Item | Formula |
|------|--------|------|---------|
| 03700 | 00500 | Accounts Payable | Direct |
| 04000 | 00500 | Short-Term Debt | Direct |
| 04500 | 00500 | **Total Current Liabilities** | Sum Lines 37-44 |
| 04600 | 00500 | Mortgage Payable | Direct |
| 04700 | 00500 | Long-Term Debt | Direct |
| 05000 | 00500 | **Total Long-Term Liabilities** | Sum Lines 46-49 |
| 05100 | 00500 | **TOTAL LIABILITIES** | Lines 45+50 |
| 05200 | 00500 | General Fund Balance | Direct |
| 05900 | 00500 | **Total Fund Balances (Equity)** | Sum Lines 52-58 |
| 06000 | 00500 | Total Liabilities + Equity | Lines 51+59 |

**Validation:** Line 06000 must equal Line 03600 (Assets = Liabilities + Equity)

---

## Key Income Statement Line Items (Worksheet G-3)

| Line | Column | Item | Formula |
|------|--------|------|---------|
| 00100 | 00100 | Total Patient Revenue (Gross) | From G-2, Part I, Line 28 |
| 00200 | 00100 | Allowances & Discounts | Direct |
| **00300** | **00100** | **Net Patient Revenue** ⭐ | Line 1 - Line 2 |
| 00400 | 00100 | Total Operating Expenses | From G-2, Part II, Line 43 |
| **00500** | **00100** | **Operating Income** ⭐ | Line 3 - Line 4 |
| 00600 | 00100 | Investment Income | Direct |
| 02100 | 00100 | EHR Incentive Payments | Direct |
| 02200 | 00100 | COVID-19 Relief Funds | Direct |
| 02450 | 00100 | COVID-19 PHE Funding | Direct |
| 02500 | 00100 | Total Other Income | Sum Lines 6-24.60 |
| 02800 | 00100 | Other Expenses | Direct |
| **02900** | **00100** | **Net Income** ⭐ | Line 5 + Line 25 - Line 28 |

---

## Depreciation Extraction (Worksheet A-7)

**Location:** Worksheet A700000, Line 20000 (Total), Columns by Asset Type

| Column | Asset Type |
|--------|------------|
| 00900 | Land Improvements Depreciation |
| 01000 | Buildings Depreciation |
| 01100 | Leasehold Improvements Depreciation |
| 01200 | Fixed Equipment Depreciation |
| 01300 | Major Movable Equipment Depreciation |
| 01400 | Minor Equipment Depreciation |

**Total Depreciation = Sum of Columns 00900-01400, Line 20000**

---

## Interest Expense Extraction (Worksheet A)

**Location:** Worksheet A000000, Line 11300, Column 00300 (Total)

**Note:** This is interest expense BEFORE reclassification to capital-related costs.

---

## Key Financial Ratios

### Profitability Ratios

| Ratio | Formula | Benchmark |
|-------|---------|-----------|
| **Operating Margin** | (Operating Income / Net Patient Revenue) × 100% | Healthy: >5% |
| **Net Margin** | (Net Income / Net Patient Revenue) × 100% | Healthy: >3% |
| **EBITDA Margin** | (EBITDA / Net Patient Revenue) × 100% | Strong: >12% |
| **Return on Assets (ROA)** | (Net Income / Total Assets) × 100% | Good: >5% |
| **Return on Equity (ROE)** | (Net Income / Total Equity) × 100% | Good: >10% |

### Liquidity Ratios

| Ratio | Formula | Benchmark |
|-------|---------|-----------|
| **Current Ratio** | Current Assets / Current Liabilities | Healthy: >2.0 |
| **Quick Ratio** | (Cash + Investments + AR Net) / Current Liabilities | Healthy: >1.5 |
| **Days Cash on Hand** | Cash / (Operating Expenses / 365) | Strong: >100 days |

### Leverage Ratios

| Ratio | Formula | Benchmark |
|-------|---------|-----------|
| **Debt-to-Equity** | Total Liabilities / Total Equity | Conservative: <1.0 |
| **Debt-to-Assets** | Total Liabilities / Total Assets | Conservative: <0.5 |
| **Debt Service Coverage** | EBITDA / Interest Expense | Healthy: >3.0 |

### Efficiency Ratios

| Ratio | Formula | Benchmark |
|-------|---------|-----------|
| **Asset Turnover** | Net Patient Revenue / Total Assets | Varies by size |
| **Days in Receivables** | 365 / (NPR / AR Net) | Good: <60 days |
| **Receivables Turnover** | Net Patient Revenue / AR Net | Higher is better |

---

## SQL Query Templates

### Extract Balance Sheet
```sql
SELECT
    rpt.Provider_Number,
    YEAR(rpt.FY_End) AS Fiscal_Year,
    nmrc.Line,
    nmrc.Column,
    nmrc.Value
FROM nmrc_data AS nmrc
JOIN rpt_data AS rpt ON nmrc.Report_Record_Number = rpt.Report_Record_Number
WHERE nmrc.Worksheet = 'G000000'
    AND nmrc.Column = '00500'  -- Total column
    AND rpt.Report_Status IN ('A', 'F')
ORDER BY rpt.Provider_Number, rpt.FY_End, nmrc.Line;
```

### Extract Income Statement
```sql
SELECT
    rpt.Provider_Number,
    YEAR(rpt.FY_End) AS Fiscal_Year,
    nmrc.Line,
    nmrc.Value,
    CASE nmrc.Line
        WHEN '00300' THEN 'Net_Patient_Revenue'
        WHEN '00500' THEN 'Operating_Income'
        WHEN '02900' THEN 'Net_Income'
    END AS Metric_Name
FROM nmrc_data AS nmrc
JOIN rpt_data AS rpt ON nmrc.Report_Record_Number = rpt.Report_Record_Number
WHERE nmrc.Worksheet = 'G300000'
    AND nmrc.Column = '00100'
    AND nmrc.Line IN ('00300', '00500', '02900')
    AND rpt.Report_Status IN ('A', 'F')
ORDER BY rpt.Provider_Number, rpt.FY_End;
```

### Extract EBITDA Components
```sql
-- Net Income
SELECT Provider_Number, Fiscal_Year, Value AS Net_Income
FROM nmrc_data nmrc
JOIN rpt_data rpt ON nmrc.Report_Record_Number = rpt.Report_Record_Number
WHERE Worksheet = 'G300000' AND Line = '02900' AND Column = '00100'

UNION ALL

-- Interest Expense
SELECT Provider_Number, Fiscal_Year, Value AS Interest_Expense
FROM nmrc_data nmrc
JOIN rpt_data rpt ON nmrc.Report_Record_Number = rpt.Report_Record_Number
WHERE Worksheet = 'A000000' AND Line = '11300' AND Column = '00300'

UNION ALL

-- Depreciation
SELECT Provider_Number, Fiscal_Year, SUM(Value) AS Depreciation_Expense
FROM nmrc_data nmrc
JOIN rpt_data rpt ON nmrc.Report_Record_Number = rpt.Report_Record_Number
WHERE Worksheet = 'A700000'
    AND Line = '20000'
    AND Column IN ('00900', '01000', '01100', '01200', '01300', '01400')
GROUP BY Provider_Number, Fiscal_Year;
```

---

## Valuation Multiple Ranges (Hospital M&A)

### EBITDA Multiples
- **Large Academic Medical Centers:** 10-14x EBITDA
- **Regional Hospitals (>200 beds):** 7-10x EBITDA
- **Community Hospitals (50-200 beds):** 5-8x EBITDA
- **Small Rural Hospitals (<50 beds):** 3-6x EBITDA
- **Distressed Hospitals (negative EBITDA):** Asset-based valuation

### Revenue Multiples (if EBITDA negative)
- **Stable Revenue, Turnaround Potential:** 0.3-0.7x Revenue
- **Declining Revenue:** 0.1-0.3x Revenue

---

## Data Quality Flags

### Critical Validations

1. **Balance Sheet Balance:**
   - `Total_Assets = Total_Liabilities + Total_Equity`
   - Tolerance: ±$1.00

2. **Net Income Reconciliation:**
   - `Net Income = Operating Income + Other Income - Other Expenses`
   - Tolerance: ±$1.00

3. **Ratio Reasonableness:**
   - Operating Margin: -50% to +50%
   - Current Ratio: 0.1 to 10.0
   - Debt-to-Equity: 0.0 to 20.0

4. **Completeness:**
   - All key metrics present (NPR, Operating Income, Net Income)
   - No NULL values for required fields

---

## Common Line Number Patterns

### Worksheet A (Trial Balance)
- **Lines 1-3:** Capital costs (buildings, equipment)
- **Lines 4-23:** General service costs (A&G, dietary, housekeeping, etc.)
- **Lines 30-46:** Inpatient routine services
- **Lines 50-78:** Ancillary services (radiology, lab, OR, pharmacy, PT, etc.)
- **Lines 88-93:** Outpatient services
- **Line 200:** TOTAL (all cost centers)

### Worksheet G (Balance Sheet)
- **Lines 1-11:** Current assets
- **Lines 12-30:** Property, plant & equipment
- **Lines 31-35:** Other assets
- **Lines 37-45:** Current liabilities
- **Lines 46-50:** Long-term liabilities
- **Lines 52-59:** Fund balances (equity)

### Worksheet G-3 (Income Statement)
- **Line 1:** Total patient revenue (gross)
- **Line 2:** Allowances and discounts
- **Line 3:** Net patient revenue ⭐
- **Line 4:** Total operating expenses
- **Line 5:** Operating income ⭐
- **Lines 6-25:** Other income (non-operating)
- **Lines 27-28:** Other expenses
- **Line 29:** Net income ⭐

---

## Column Structure Reference

### Worksheet G (Balance Sheet) Columns
- **Column 1 (00100):** General Fund
- **Column 2 (00200):** Specific Purpose Fund
- **Column 3 (00300):** Endowment Fund
- **Column 4 (00400):** Plant Fund
- **Column 5 (00500):** **TOTAL** (sum of columns 1-4) ⭐ PRIMARY

### Worksheet A (Trial Balance) Columns
- **Column 1 (00100):** Salaries
- **Column 2 (00200):** Other than Salaries
- **Column 3 (00300):** Total (Column 1 + Column 2)
- **Column 4 (00400):** Reclassifications
- **Column 5 (00500):** Adjusted (Column 3 + Column 4)
- **Column 6 (00600):** Adjustments
- **Column 7 (00700):** **Final** ⭐ PRIMARY

### Worksheet A-7 (Capital Analysis) Columns
- **Columns 1-8:** Asset tracking (beginning balance, additions, retirements, transfers, ending balance)
- **Column 9 (00900):** Depreciation - Land improvements
- **Column 10 (01000):** Depreciation - Buildings
- **Column 11 (01100):** Depreciation - Leasehold improvements
- **Column 12 (01200):** Depreciation - Fixed equipment
- **Column 13 (01300):** Depreciation - Major movable equipment
- **Column 14 (01400):** Depreciation - Minor equipment

---

## Python/Pandas Code Snippets

### Extract Net Patient Revenue
```python
import pandas as pd

# Filter to Worksheet G-3, Line 300 (Net Patient Revenue)
net_revenue = nmrc_df[
    (nmrc_df['Worksheet'] == 'G300000') &
    (nmrc_df['Line'] == '00300') &
    (nmrc_df['Column'] == '00100')
].copy()

# Merge with provider info
net_revenue = net_revenue.merge(
    rpt_df[['Report_Record_Number', 'Provider_Number', 'FY_End']],
    on='Report_Record_Number'
)

# Create fiscal year
net_revenue['Fiscal_Year'] = pd.to_datetime(net_revenue['FY_End']).dt.year

# Select relevant columns
net_revenue = net_revenue[['Provider_Number', 'Fiscal_Year', 'Value']].rename(
    columns={'Value': 'Net_Patient_Revenue'}
)
```

### Calculate EBITDA
```python
# Extract components
net_income = get_value('G300000', '02900', '00100')  # Net Income
interest = get_value('A000000', '11300', '00300')    # Interest
depreciation = get_depreciation_total('A700000')     # Depreciation

# Calculate EBITDA
ebitda = net_income.merge(interest, on=['Provider_Number', 'Fiscal_Year'], how='left')
ebitda = ebitda.merge(depreciation, on=['Provider_Number', 'Fiscal_Year'], how='left')

ebitda['EBITDA'] = (
    ebitda['Net_Income'].fillna(0) +
    ebitda['Interest_Expense'].fillna(0) +
    ebitda['Depreciation_Expense'].fillna(0)
)
```

### Pivot Balance Sheet to Wide Format
```python
# Extract balance sheet data
bs_raw = nmrc_df[
    (nmrc_df['Worksheet'] == 'G000000') &
    (nmrc_df['Column'] == '00500')  # Total column
].copy()

# Merge with metadata
bs_raw = bs_raw.merge(
    rpt_df[['Report_Record_Number', 'Provider_Number', 'FY_End']],
    on='Report_Record_Number'
)

# Merge with line names
bs_raw = bs_raw.merge(
    names_df[['Worksheet', 'Line', 'Line_Name']],
    on=['Worksheet', 'Line'],
    how='left'
)

# Pivot to wide format
bs_wide = bs_raw.pivot_table(
    index=['Provider_Number', 'FY_End'],
    columns='Line',
    values='Value',
    aggfunc='sum'
).reset_index()

# Rename columns to meaningful names
bs_wide = bs_wide.rename(columns={
    '00100': 'Cash',
    '01100': 'Total_Current_Assets',
    '03000': 'Total_PPE_Net',
    '03600': 'Total_Assets',
    '04500': 'Total_Current_Liabilities',
    '05100': 'Total_Liabilities',
    '05900': 'Total_Equity'
})
```

---

## State Benchmarking Example

```sql
-- Compare hospital to state peers
WITH state_stats AS (
    SELECT
        State_Code,
        Fiscal_Year,
        AVG(EBITDA_Margin) AS Avg_EBITDA_Margin,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EBITDA_Margin) AS P25_EBITDA_Margin,
        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY EBITDA_Margin) AS Median_EBITDA_Margin,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EBITDA_Margin) AS P75_EBITDA_Margin
    FROM hospital_valuation_metrics
    WHERE EBITDA_Margin IS NOT NULL
    GROUP BY State_Code, Fiscal_Year
)

SELECT
    hvm.Provider_Number,
    hvm.Provider_Name,
    hvm.Fiscal_Year,
    hvm.EBITDA_Margin AS Hospital_EBITDA_Margin,
    ss.Avg_EBITDA_Margin AS State_Avg,
    ss.Median_EBITDA_Margin AS State_Median,
    (hvm.EBITDA_Margin - ss.Avg_EBITDA_Margin) AS Difference_From_State_Avg,
    CASE
        WHEN hvm.EBITDA_Margin >= ss.P75_EBITDA_Margin THEN 'Top Quartile'
        WHEN hvm.EBITDA_Margin >= ss.Median_EBITDA_Margin THEN 'Above Median'
        WHEN hvm.EBITDA_Margin >= ss.P25_EBITDA_Margin THEN 'Below Median'
        ELSE 'Bottom Quartile'
    END AS Performance_Tier
FROM hospital_valuation_metrics AS hvm
JOIN state_stats AS ss
    ON hvm.State_Code = ss.State_Code
    AND hvm.Fiscal_Year = ss.Fiscal_Year
ORDER BY hvm.State_Code, hvm.EBITDA_Margin DESC;
```

---

**Quick Reference Prepared By:** Claude Code
**For Use With:** HCRIS Form CMS-2552-10
**Last Updated:** 2025-11-13
