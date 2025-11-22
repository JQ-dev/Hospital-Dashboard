# Dashboard Display Issues - Root Cause Analysis & Fix

**Date:** 2025-11-22
**Issue:** KPIs with complete data not showing in dashboard

---

## Executive Summary

**3 out of 6 Level 1 KPIs are NOT displaying correctly** in the dashboard despite having complete data and benchmarks:

1. ✅ Net Income Margin - **Working correctly** (56.97% vs 60.10% median)
2. ❌ AR Days - **Displaying but WRONG VALUES** (1.2 days - should be ~50 days)
3. ❌ Operating Expense per Adj Discharge - **Displaying WRONG KPI** (showing Operating Margin % instead)
4. ✅ Medicare CCR - **Working correctly** (0.22 vs 0.17 median)
5. ✅ Bad Debt + Charity % - **Working correctly** (8.87% vs 12.25% median)
6. ✅ Current Ratio - **Working correctly** (5.71 vs 1.82 median)

---

## Root Cause #1: AR Days - Data Quality Issue

### Problem
AR_Days shows **1-2 days** average, but hospital accounts receivable typically takes **30-60 days** to collect.

### Root Cause Chain

1. **Original Database Build Error** ([data_manager.py:818](d:\HealthVista Analytics\hospital_dashboard\data\data_manager.py#L818))
   ```python
   # WRONG - Line_Name doesn't exist in balance_sheet table
   SUM(CASE WHEN Line_Name LIKE '%receivable%' THEN Value ELSE 0 END) as Accounts_Receivable

   # Should be:
   SUM(CASE WHEN Acc_name LIKE '%receivable%' THEN Value ELSE 0 END) as Accounts_Receivable
   ```

2. **Result:** All hospitals have `Accounts_Receivable = 0` in hospital_kpis table

3. **Calculation:** `AR_Days = 0 / (Revenue/365) = 0`

### Additional Data Quality Issue

**Duplicate Rows in balance_sheet Table:**
- Every balance sheet entry appears **3 times** (exact duplicates)
- Example: Hospital 310001, 2024, Accounts Receivable = $428,952,507 × 3 = $1,286,857,521
- Must use `SELECT DISTINCT` to deduplicate

### What We Fixed

Created [fix_ar_days.py](d:\HealthVista Analytics\hospital_dashboard\fix_ar_days.py):
- ✅ Extracts Accounts Receivable using correct column name (`Acc_name`)
- ✅ Deduplicates balance_sheet data
- ✅ Calculates Net AR (Gross AR - Allowances)
- ✅ Recalculates AR_Days
- ✅ Regenerates benchmarks

### Current Status After Fix

**Hospital 310001, 2024:**
- Gross AR: $428,952,507
- Allowances: -$77,502,463
- **Net AR: $351,450,044**
- Total Revenue: $106.6 billion
- **AR_Days = 1.2 days** ← Still seems wrong!

### Why AR_Days is Still Too Low

**Potential Issues:**
1. **Revenue Scale Issue:** Revenue might be in wrong units (billions vs millions)
2. **AR Calculation:** Should we use Gross AR instead of Net AR?
3. **Data Source Problem:** HCRIS balance sheet extraction may have issues
4. **Formula Issue:** AR Days formula might need adjustment for how HCRIS reports data

**Manual Calculation Check:**
```
Net AR: $351,450,044
Daily Revenue: $106,600,000,000 / 365 = $292,054,795
AR Days: $351,450,044 / $292,054,795 = 1.20 days

This math is correct, but the values themselves seem off.
Revenue of $106 BILLION for a single hospital is suspiciously high.
```

### Recommended Next Steps for AR_Days

1. **Verify Revenue Units:** Check if `Total_Revenue` in hospital_kpis is inflated
2. **Check Source Data:** Review balance_sheet and revenue parquet file extraction
3. **Cross-reference:** Compare against CMS public data for hospital 310001
4. **Alternative Formula:** Research if HCRIS AR Days uses different calculation method

---

## Root Cause #2: Operating Expense per Adjusted Discharge - Wrong Column Mapped

### Problem
Dashboard shows **43%** but benchmarks show **$792,526**. These are incompatible units!

### Root Cause

**Incorrect Column Mapping** in [config/mappings.py:13](d:\HealthVista Analytics\hospital_dashboard\config\mappings.py#L13):

```python
DB_COLUMN_TO_KPI_KEY = {
    # WRONG MAPPING:
    'Operating_Expense_Ratio': 'Operating_Expense_per_Adjusted_Discharge',

    # This maps the WRONG database column!
    # Operating_Expense_Ratio is a PERCENTAGE (Operating Margin %)
    # Operating_Expense_per_Adjusted_Discharge is a DOLLAR AMOUNT ($ per discharge)
}
```

### What's Happening

1. Dashboard expects KPI key: `Operating_Expense_per_Adjusted_Discharge`
2. Mapping says: Use database column `Operating_Expense_Ratio`
3. **But `Operating_Expense_Ratio` is the WRONG KPI!**
   - `Operating_Expense_Ratio` = Operating expenses as % of revenue = **43%**
   - `Operating_Expense_per_Adjusted_Discharge` = Total expenses / discharges = **$1,106,703**

### The Correct Columns

**In hospital_kpis table we have BOTH:**

| Column Name | Description | Hospital 310001 Value | Correct? |
|-------------|-------------|---------------------|----------|
| `Operating_Expense_Ratio` | Operating expenses as % of revenue | 43.03% | ✅ Different KPI |
| `Operating_Expense_per_Adjusted_Discharge` | Total expenses per adjusted discharge | $1,106,703 | ✅ This is the Level 1 KPI we want |

### The Fix

**Update [config/mappings.py:13](d:\HealthVista Analytics\hospital_dashboard\config\mappings.py#L13):**

```python
# BEFORE (WRONG):
'Operating_Expense_Ratio': 'Operating_Expense_per_Adjusted_Discharge',

# AFTER (CORRECT):
'Operating_Expense_per_Adjusted_Discharge': 'Operating_Expense_per_Adjusted_Discharge',
```

**Also update benchmarks in database:** The benchmarks are stored by `KPI_Name`, which should match the database column name:

```sql
-- Current benchmarks use column name
SELECT * FROM hospital_benchmarks WHERE KPI_Name = 'Operating_Expense_per_Adjusted_Discharge';

-- This is correct! The fix is just in the mapping.
```

---

## Summary of All Issues

| KPI | Database Column | Has Data? | Has Benchmarks? | Dashboard Status | Issue |
|-----|----------------|-----------|-----------------|------------------|-------|
| Net Income Margin | `Net_Margin_Pct` | ✅ 532 records | ✅ 75 benchmarks | ✅ **Working** | None |
| AR Days | `AR_Days` | ⚠️ 471 records (all ~1-2 days) | ✅ 63 benchmarks | ❌ **Wrong values** | Data quality - AR = 0 in original build |
| Operating Expense per Adj Discharge | `Operating_Expense_per_Adjusted_Discharge` | ✅ 435 records | ✅ 48 benchmarks | ❌ **Showing wrong KPI** | Wrong column mapped (maps to Operating_Expense_Ratio instead) |
| Medicare CCR | `Medicare_CCR` | ✅ 121 records | ✅ 8 benchmarks | ✅ **Working** | None |
| Bad Debt + Charity % | `Bad_Debt_Charity_Pct` | ✅ 107 records | ✅ 8 benchmarks | ✅ **Working** | None |
| Current Ratio | `Current_Ratio` | ✅ 1,318 records | ✅ 119 benchmarks | ✅ **Working** | None |

---

## Files That Need Fixing

### 1. Fix Column Mapping (CRITICAL - Dashboard Won't Show Correct KPI)

**File:** [config/mappings.py](d:\HealthVista Analytics\hospital_dashboard\config\mappings.py)

**Line 13 - Change from:**
```python
'Operating_Expense_Ratio': 'Operating_Expense_per_Adjusted_Discharge',
```

**To:**
```python
'Operating_Expense_per_Adjusted_Discharge': 'Operating_Expense_per_Adjusted_Discharge',
```

**And optionally add (for clarity):**
```python
'Operating_Expense_Ratio': 'Operating_Expense_Ratio',  # This is Operating Margin %, not Level 1 KPI
```

### 2. Fix AR Days Data (Data Quality Issue)

**Option A: Rebuild hospital_kpis table from scratch**
- Fix [data_manager.py:818](d:\HealthVista Analytics\hospital_dashboard\data\data_manager.py#L818) to use `Acc_name` instead of `Line_Name`
- Rebuild entire hospital_analytics.duckdb database
- This fixes AR Days AND ensures all other KPIs use correct source

**Option B: Use fix script (Quick fix for AR Days only)**
- Run [fix_ar_days.py](d:\HealthVista Analytics\hospital_dashboard\fix_ar_days.py)
- Updates only Accounts_Receivable and AR_Days columns
- Leaves other columns as-is

**Recommended:** Option A (rebuild database) to ensure data quality across all KPIs

### 3. Investigate Revenue/AR Data Quality (Follow-up)

Need to understand why AR_Days values are so low (1-2 days):
1. Check source HCRIS parquet files for revenue data
2. Verify balance sheet extraction didn't corrupt values
3. Cross-reference with CMS public reporting for validation
4. Consider if formula needs adjustment for HCRIS reporting structure

---

## Testing Checklist

After applying fixes, verify:

### Operating Expense per Adj Discharge
- [ ] Dashboard shows dollar amounts (e.g., "$1,106,703") not percentages (e.g., "43%")
- [ ] Benchmark median is ~$750K-$850K (not 40-60%)
- [ ] Card title says "Operating Expense per Adjusted Discharge"
- [ ] Values are realistic for hospital cost per discharge

### AR Days (After Data Fix)
- [ ] Dashboard shows realistic values (30-60 days typical)
- [ ] Benchmark median is in similar range
- [ ] Not showing 0-2 days for most hospitals
- [ ] Calculation display shows correct AR and Revenue values

### All 6 KPIs
- [ ] All 6 Level 1 KPI cards display data (no "Data Not Available")
- [ ] Benchmarks populate for all cards
- [ ] Trend arrows show where applicable
- [ ] Performance indicators (quartile badges) display correctly

---

## Quick Fix Steps

### Immediate (5 minutes)
1. Edit [config/mappings.py](d:\HealthVista Analytics\hospital_dashboard\config\mappings.py) line 13
2. Restart dashboard
3. Operating Expense per Adj Discharge should now show correct values

### Short-term (15 minutes)
1. Run `python fix_ar_days.py`
2. Restart dashboard
3. AR Days will show values (still may be low due to data quality)

### Long-term (1-2 hours)
1. Fix [data_manager.py:818](d:\HealthVista Analytics\hospital_dashboard\data\data_manager.py#L818)
2. Rebuild hospital_analytics.duckdb database
3. Investigate revenue data quality issues
4. Validate against CMS public data

---

## Files Created

1. [MISSING_DATA_REPORT.md](d:\HealthVista Analytics\hospital_dashboard\MISSING_DATA_REPORT.md) - Analysis of missing KPIs
2. [FIX_SUMMARY.md](d:\HealthVista Analytics\hospital_dashboard\FIX_SUMMARY.md) - Summary of missing KPI fixes
3. [fix_missing_kpis.py](d:\HealthVista Analytics\hospital_dashboard\fix_missing_kpis.py) - Script to populate 3 missing KPIs
4. [fix_ar_days.py](d:\HealthVista Analytics\hospital_dashboard\fix_ar_days.py) - Script to fix AR Days data
5. [DASHBOARD_FIX_REPORT.md](d:\HealthVista Analytics\hospital_dashboard\DASHBOARD_FIX_REPORT.md) - This file

---

## Contact

For questions about these fixes:
- Column mapping fix: See [config/mappings.py](d:\HealthVista Analytics\hospital_dashboard\config\mappings.py)
- AR Days data quality: See [fix_ar_days.py](d:\HealthVista Analytics\hospital_dashboard\fix_ar_days.py)
- Missing KPIs fix: See [fix_missing_kpis.py](d:\HealthVista Analytics\hospital_dashboard\fix_missing_kpis.py)
- Data manager issues: See [data/data_manager.py](d:\HealthVista Analytics\hospital_dashboard\data\data_manager.py)

---

*Analysis completed 2025-11-22*
