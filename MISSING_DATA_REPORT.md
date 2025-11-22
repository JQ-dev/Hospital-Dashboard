# Hospital Dashboard - Missing Data Report

**Generated:** 2025-11-22
**Analysis Scope:** Benchmark Table & Level 1 KPI Data Completeness

---

## Executive Summary

The hospital dashboard uses **6 Level 1 KPIs** for the main scorecard. Analysis shows that **3 out of 6 KPIs are missing** from both the `hospital_kpis` table and the `hospital_benchmarks` table, preventing them from being displayed in the dashboard.

### Missing KPIs Status

| KPI | Config Name | DB Column | Data Exists | Benchmarks Exist | Status |
|-----|-------------|-----------|-------------|------------------|--------|
| 1. Net Income Margin | `Net_Income_Margin` | `Net_Margin_Pct` | ✅ Yes (479 records) | ✅ Yes (75 benchmarks) | **COMPLETE** |
| 2. Days in AR | `AR_Days` | `AR_Days` | ✅ Yes (479 records) | ✅ Yes (75 benchmarks) | **COMPLETE** |
| 3. Operating Expense per Adjusted Discharge | `Operating_Expense_per_Adjusted_Discharge` | ❌ N/A | ❌ No | ❌ No | **MISSING** |
| 4. Medicare CCR | `Medicare_CCR` | ❌ N/A | ❌ No | ❌ No | **MISSING** |
| 5. Bad Debt + Charity % | `Bad_Debt_Charity_Pct` | ❌ N/A | ❌ No | ❌ No | **MISSING** |
| 6. Current Ratio | `Current_Ratio` | `Current_Ratio` | ✅ Yes (1,318 records) | ✅ Yes (119 benchmarks) | **COMPLETE** |

**Impact:** Only 3 out of 6 Level 1 KPI cards can currently display data in the dashboard.

---

## Detailed Analysis

### 1. Database Structure Overview

#### hospital_kpis Table
- **Total Rows:** 1,422 hospital-year records
- **Total Columns:** 33 KPI columns
- **Years Covered:** 2020-2024 (5 years)
- **Hospitals:** ~284 unique providers

#### hospital_benchmarks Table
- **Total Rows:** Varies by KPI (61-119 benchmark groups)
- **Benchmark Levels:** National, State, Hospital_Type, State_Hospital_Type (4 levels)
- **KPIs Benchmarked:** 17 KPIs currently have benchmark data
- **No NULL Issues:** All existing benchmarks have complete P25, Median, P75, Mean values

### 2. Data Completeness for Existing KPIs

| KPI in hospital_kpis | Total Records | Non-NULL | NULL | % Complete |
|---------------------|---------------|----------|------|------------|
| `Net_Margin_Pct` | 1,422 | 479 | 943 | 33.7% |
| `AR_Days` | 1,422 | 479 | 943 | 33.7% |
| `Current_Ratio` | 1,422 | 1,318 | 104 | 92.7% |
| `Days_Cash_On_Hand` | 1,422 | 479 | 943 | 33.7% |
| `Operating_Margin_Pct` | 1,422 | 479 | 943 | 33.7% |

**Note:** Lower completion rates (~33%) indicate data is only available for certain hospital types or years. Current Ratio has highest completeness at 92.7%.

### 3. Benchmark Coverage Analysis

Current benchmarks exist for these 17 KPIs:
- AR_Days ✅
- Asset_Turnover_Ratio ✅
- Current_Ratio ✅
- Days_Cash_On_Hand ✅
- Debt_Ratio_Pct ✅
- Debt_to_Equity_Ratio ✅
- Equity_Ratio_Pct ✅
- Inpatient_Revenue_Pct ✅
- Net_Margin_Pct ✅
- Operating_Expense_Ratio ✅
- Operating_Margin_Pct ✅
- Outpatient_Revenue_Pct ✅
- Return_on_Assets_Pct ✅
- Return_on_Equity_Pct ✅
- Revenue_Growth_Pct ✅ (1 NULL value in 2020 National)
- Total_Margin_Pct ✅
- Working_Capital ✅

---

## Missing KPIs - Root Cause Analysis

### Missing KPI #1: Operating_Expense_per_Adjusted_Discharge

**Status:** ❌ MISSING - Column does not exist in hospital_kpis table

**Root Cause:**
- The KPI calculation requires **Adjusted Discharges** data
- Adjusted Discharges data exists in `worksheet_s300001` (Worksheet S-3, Part I)
- The `hospital_kpis` table has `Total_Operating_Expenses` but was never joined with discharge data
- This KPI was never calculated during database build process

**Formula:**
```
Operating_Expense_per_Adjusted_Discharge = Total_Operating_Expenses / Adjusted_Discharges
```

**Data Sources:**
1. **Numerator:** `Total_Operating_Expenses` - Already exists in `hospital_kpis` table
2. **Denominator:** `Adjusted_Discharges` - Available in `worksheet_s300001`
   - Location: Line `01400`, Column `01500`
   - Field: `Value` column
   - Coverage: 70,584 rows, 229 hospitals, years 2020-2024

**Sample Data Available:**
```
Provider_Number | Fiscal_Year | Line  | Column | Value (Adjusted Discharges)
310001         | 2024        | 01400 | 01500  | 41,455
310001         | 2023        | 01400 | 01500  | 41,703
310001         | 2022        | 01400 | 01500  | 41,187
```

---

### Missing KPI #2: Medicare_CCR

**Status:** ❌ MISSING - Column does not exist in hospital_kpis table

**Root Cause:**
- Medicare Cost-to-Charge Ratio (CCR) is a specialized Medicare reporting metric
- Data exists in `worksheet_s100001` (Worksheet S-10)
- This worksheet was not integrated into the `hospital_kpis` table during build
- Worksheet S-10 contains both Medicare costs and charges needed for the ratio

**Formula:**
```
Medicare_CCR = Medicare_Allowable_Costs / Medicare_Covered_Charges
```

**Data Sources:**
- **Source:** `worksheet_s100001` (Worksheet S-10)
- **Coverage:** 6,714 rows, 168 hospitals, years 2023-2024
- **Key Lines:**
  - Line `00100`, Column `00100`: Medicare CCR ratio (direct value: 0.2178, 0.2432, etc.)
  - Line `00200`, Column `00100`: Medicare Covered Charges
  - Line `03000`, Column `00100`: Medicare Allowable Costs
  - Line `03100`, Column `00100`: Total costs (alternative)

**Sample Data Available:**
```
Provider_Number | Fiscal_Year | Line  | Column | Value
310001         | 2024        | 00100 | 00100  | 0.2178 (CCR Ratio)
310001         | 2024        | 00200 | 00100  | 213,103,700 (Charges)
310001         | 2024        | 03000 | 00100  | 101,350,600 (Costs)
```

**Note:** Line `00100` already contains the pre-calculated Medicare CCR ratio, making extraction straightforward.

---

### Missing KPI #3: Bad_Debt_Charity_Pct

**Status:** ❌ MISSING - Column does not exist in hospital_kpis table

**Root Cause:**
- Bad Debt and Charity Care are important indicators of financial health and community benefit
- Data exists in `worksheet_s100001` (Worksheet S-10) for both components
- Net Patient Revenue exists in `worksheet_g300000` (Worksheet G-3)
- These worksheets were not joined during the database build process

**Formula:**
```
Bad_Debt_Charity_Pct = (Bad_Debt_Expense + Charity_Care_Charges) / Net_Patient_Revenue × 100
```

**Data Sources:**

1. **Bad Debt & Charity Care:** `worksheet_s100001` (S-10)
   - Line `02000`, Column `00300`: Total Charity Care Charges
   - Line `02000`, Column `00100`: Charity Care - Uninsured
   - Line `02000`, Column `00200`: Charity Care - Insured
   - Line `02500`: Bad Debt Expense
   - Line `02600`: Bad Debt Recoveries
   - Coverage: 6,714 rows, 168 hospitals, years 2023-2024

2. **Net Patient Revenue:** `worksheet_g300000` (G-3)
   - Filter: `line_level1 = 'NET PATIENT REVENUE'`
   - Coverage: 15,178 rows, 229 hospitals, years 2020-2024

**Sample Data Available:**
```
# From S-10 (Bad Debt & Charity)
Provider_Number | Fiscal_Year | Line  | Column | Value
310001         | 2024        | 02000 | 00300  | 346,782,368 (Total Charity)
310001         | 2024        | 02000 | 00100  | 342,087,036 (Uninsured Charity)
310001         | 2024        | 02000 | 00200  | 4,695,332   (Insured Charity)
310001         | 2024        | 02600 | 00100  | 111,111,162 (Bad Debt Recoveries)

# From G-3 (Net Patient Revenue) - would need to sum where line_level1 = 'NET PATIENT REVENUE'
```

---

## Recommendations

### Immediate Action Items

1. **Add Missing Columns to hospital_kpis Table**
   - Create 3 new columns: `Operating_Expense_per_Adjusted_Discharge`, `Medicare_CCR`, `Bad_Debt_Charity_Pct`
   - Populate with calculations from worksheet data
   - Backfill for all available years (2020-2024)

2. **Generate Benchmarks for Missing KPIs**
   - Calculate P25, Median, P75, Mean for each KPI
   - Generate benchmarks at all 4 levels (National, State, Hospital_Type, State_Hospital_Type)
   - Add ~240 new benchmark rows (3 KPIs × 4 levels × 5 years × 4 variations)

3. **Update Dashboard Configuration**
   - Verify `kpi_hierarchy_config.py` has correct mapping for all 6 Level 1 KPIs
   - Update `config/mappings.py` to include new KPI column mappings
   - Test KPI card display with new data

### Data Quality Notes

1. **Adjusted Discharges:** High coverage (229 hospitals, 5 years) - Good data quality expected
2. **Medicare CCR:** Lower coverage (168 hospitals, 2 years) - Newer reporting requirement
3. **Bad Debt & Charity:** Same coverage as Medicare CCR (168 hospitals, 2 years)

**Coverage Gap:** Worksheets S-10 data only goes back to 2023, while other KPIs have 2020-2024 data. This is a CMS reporting change and cannot be backfilled.

---

## Implementation Plan

See `fix_missing_kpis.py` for automated data extraction and population script.

### Script Capabilities:
1. Extract Adjusted Discharges from Worksheet S-3
2. Extract Medicare CCR from Worksheet S-10
3. Extract Bad Debt and Charity Care from Worksheets S-10 and G-3
4. Calculate all 3 missing KPIs
5. Update hospital_kpis table with new columns
6. Generate benchmarks for all 3 KPIs
7. Update hospital_benchmarks table

### Expected Results After Fix:
- **hospital_kpis:** 3 new columns populated for ~479 hospital-years (Operating Expense) and ~336 hospital-years (Medicare CCR, Bad Debt)
- **hospital_benchmarks:** ~240 new benchmark rows across all levels and years
- **Dashboard:** All 6 Level 1 KPI cards functional

---

## Appendix: Worksheet References

### CMS HCRIS Worksheets Used

| Worksheet | Table Name | Description | Coverage |
|-----------|------------|-------------|----------|
| S-3 Part I | `worksheet_s300001` | Hospital Statistics - Patient Days, Discharges, Case Mix | 70,584 rows, 229 hospitals, 2020-2024 |
| S-10 | `worksheet_s100001` | Computation of Medicare CCR, Bad Debt, Charity Care | 6,714 rows, 168 hospitals, 2023-2024 |
| G-3 | `worksheet_g300000` | Statement of Revenues and Expenses | 15,178 rows, 229 hospitals, 2020-2024 |

### Key Line and Column References

**Adjusted Discharges (S-3):**
- Line `01400`, Column `01500`: Total Adjusted Patient Days / ALOS = Adjusted Discharges

**Medicare CCR (S-10):**
- Line `00100`, Column `00100`: Calculated Medicare Cost-to-Charge Ratio

**Bad Debt & Charity (S-10):**
- Line `02000`, Column `00300`: Total Charity Care Charges
- Line `02500`: Bad Debt Expense
- Line `02600`: Bad Debt Recoveries

**Net Patient Revenue (G-3):**
- Filter by `line_level1 = 'NET PATIENT REVENUE'` and sum all line items

---

## Contact

For questions about this analysis or the fix implementation, see:
- Analysis notebook: `KPI_Card_Data_Extraction.ipynb`
- Data manager: `data/data_manager.py`
- Fix script: `fix_missing_kpis.py` (to be created)
