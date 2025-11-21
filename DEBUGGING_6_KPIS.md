# Debugging: Why Only 4 KPIs Show Instead of 6

## Issue
Dashboard only shows 4 KPI cards instead of the expected 6.

## Investigation

### Expected 6 Level 1 KPIs
```python
LEVEL_1_KPIS = {
    'Net_Income_Margin',                      # L1 KPI 1
    'AR_Days',                                # L1 KPI 2
    'Operating_Expense_per_Adjusted_Discharge',  # L1 KPI 3
    'Medicare_CCR',                           # L1 KPI 4
    'Bad_Debt_Charity_Pct',                   # L1 KPI 5
    'Current_Ratio'                           # L1 KPI 6
}
```

### Database Column Mappings (config/mappings.py)
```python
DB_COLUMN_TO_KPI_KEY = {
    'Net_Margin_Pct': 'Net_Income_Margin',
    'AR_Days': 'AR_Days',
    'Operating_Expense_Ratio': 'Operating_Expense_per_Adjusted_Discharge',
    'Current_Ratio': 'Current_Ratio',
    'Medicare_CCR': 'Medicare_CCR',
    'Bad_Debt_Charity_Pct': 'Bad_Debt_Charity_Pct',
}
```

## Root Cause Analysis

The issue is likely one of these:

### 1. Missing Database Columns
The KPI data from `calculate_kpis()` might not include all 6 columns. Possible reasons:
- `Medicare_CCR` column doesn't exist in the database
- `Bad_Debt_Charity_Pct` column doesn't exist in the database
- Columns exist but have NULL values for all hospitals

### 2. Missing KPI Metadata
The KPI keys might not be defined in `KPI_METADATA` in `kpi_hierarchy_config.py`

### 3. Data Quality Issues
The columns exist but:
- All values are NULL
- Data type mismatch
- Column names don't match exactly

## Debug Output Added

I've added debug logging to `callbacks/dashboard_callbacks.py` that will print:

```python
=== DEBUG: KPI Data Analysis ===
Available columns: ['Net_Margin_Pct', 'AR_Days', 'Current_Ratio', 'Operating_Expense_Ratio']
Target Level 1 KPIs: {'Net_Income_Margin', 'AR_Days', ...}

Column Mapping Results:
  'Net_Margin_Pct' -> 'Net_Income_Margin' | In LEVEL_1: True | In KPI_METADATA: True
    ✓ Including in dashboard
  'AR_Days' -> 'AR_Days' | In LEVEL_1: True | In KPI_METADATA: True
    ✓ Including in dashboard
  ...
```

## How to Diagnose

### Step 1: Run the Dashboard
```bash
cd "d:\HealthVista Analytics\hospital_dashboard"
python dashboard.py
```

### Step 2: Open in Browser
Visit http://127.0.0.1:8050

### Step 3: Select a Hospital
Choose any hospital from the dropdown

### Step 4: Check Console Output
The debug output will show:
- Which columns are available in the data
- How they map to KPI keys
- Which ones are included/excluded and why

## Likely Solutions

### Solution 1: Add Missing Columns to Database
If `Medicare_CCR` or `Bad_Debt_Charity_Pct` columns don't exist:

```python
# In data/data_manager.py, update calculate_kpis() to include:
Medicare_CCR = (Medicare_Costs / Medicare_Charges) * 100
Bad_Debt_Charity_Pct = ((Bad_Debt + Charity_Care) / Total_Revenue) * 100
```

### Solution 2: Add Missing KPI Metadata
If KPIs are missing from `KPI_METADATA`:

```python
# In kpi_hierarchy_config.py, add:
'Medicare_CCR': {
    'name': 'Medicare Cost-to-Charge Ratio',
    'description': 'Ratio of Medicare costs to charges',
    'format': '.2f',
    'unit': '%',
    'higher_is_better': False,
    'target_range': (0, 100),
    'impact_score': 7,
    'ease_of_change': 4
},
'Bad_Debt_Charity_Pct': {
    'name': 'Bad Debt + Charity %',
    'description': 'Percentage of bad debt and charity care',
    'format': '.2f',
    'unit': '%',
    'higher_is_better': False,
    'target_range': (0, 10),
    'impact_score': 8,
    'ease_of_change': 5
}
```

### Solution 3: Update Column Names
If columns exist with different names:

```python
# In config/mappings.py, add mappings:
DB_COLUMN_TO_KPI_KEY = {
    # ... existing mappings ...
    'Medicare_Cost_to_Charge_Ratio': 'Medicare_CCR',
    'Bad_Debt_and_Charity_Pct': 'Bad_Debt_Charity_Pct',
}
```

## Next Steps

1. **Run the dashboard** and check the debug output
2. **Identify which KPIs are missing** from the data
3. **Choose the appropriate solution** based on what's missing:
   - Missing columns → Add to data_manager.py
   - Missing metadata → Add to kpi_hierarchy_config.py
   - Wrong column names → Update mappings.py

## Testing

After implementing the fix:

1. Restart the dashboard
2. Select a hospital
3. Verify 6 KPI cards appear
4. Remove debug output from dashboard_callbacks.py (optional)

## Clean Up

Once the issue is resolved, you can remove the debug print statements from:
- `callbacks/dashboard_callbacks.py` (lines 107-132)

Or keep them for future debugging!

---

**Created**: November 21, 2025
**Status**: Investigation in progress
