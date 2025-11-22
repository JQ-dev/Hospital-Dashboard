# State Code Matching Fix

## Issue Description

Single-digit state codes (e.g., '01', '02', '03') were not getting benchmark matches when querying the database. This affected hospitals with CCNs starting with '0' (like 014000, 033025, etc.).

## Root Cause Analysis

### Problem 1: CCN Normalization (FIXED)

**Issue**: When Provider_Number is stored as an integer in the database (e.g., 14000 instead of '014000'), the state code extraction was incorrect.

```python
# OLD CODE (BROKEN):
state_code = str(ccn)[:2]  # Gets '14' from '14000', not '01'

# NEW CODE (FIXED):
ccn_str = str(int(ccn)).zfill(6)  # Ensures '014000' format
state_code = ccn_str[:2]  # Gets '01' correctly
```

**Example**:
- CCN 14000 (stored as integer) → Should be '014000' (6-digit string)
- State code should be '01', not '14'

### Problem 2: Missing Benchmarks in Database (NEEDS DATABASE REBUILD)

**Issue**: The `hospital_benchmarks` table is missing data for certain state codes.

**Current State** (verified by test queries):
```
State codes in hospital_kpis:    1, 3, 14, 31 (328 hospitals total)
State codes in hospital_benchmarks:  14, 31 (only 2 states!)
```

**Missing benchmarks for**:
- State Code 1: 8 hospitals (no benchmarks)
- State Code 3: 17 hospitals (no benchmarks)

**Root cause**: When the database was built, the benchmark calculation likely had an issue with:
1. State code extraction from Provider_Number
2. Or filtering during benchmark aggregation

## Files Modified

### 1. data/data_manager.py

**Lines 1116-1119**: Fixed `get_benchmarks()` to normalize CCN before state code extraction
```python
# Ensure CCN is properly formatted as 6-digit string with leading zeros
ccn_str = str(int(ccn)).zfill(6)
state_code = ccn_str[:2]
hospital_type = self.classify_hospital_type(ccn_str)
```

**Lines 753-758**: Fixed `classify_hospital_type()` to normalize CCN input
```python
# Ensure CCN is properly formatted as 6-digit string
ccn_str = str(int(ccn)).zfill(6)
if len(ccn_str) != 6:
    return 'Unknown'

provider_num = int(ccn_str[2:])
```

### 2. callbacks/dashboard_callbacks.py

**Lines 52-57**: Fixed callback to normalize CCN before processing
```python
# Ensure CCN is properly formatted as 6-digit string with leading zeros
ccn_str = str(int(ccn)).zfill(6)

# Get hospital metadata
hospital_type = data_manager.classify_hospital_type(ccn_str)
state_code = ccn_str[:2]
```

### 3. pages/layouts.py

**Lines 505-506**: Fixed `get_level2_page_layout()` to normalize CCN
```python
# Ensure CCN is properly formatted as 6-digit string with leading zeros
ccn_str = str(int(ccn)).zfill(6)
```

**Lines 518, 524-527**: Use normalized CCN for all data manager calls
```python
kpi_data = data_manager.calculate_kpis(ccn_str)
...
all_benchmarks = {
    'state_hospital_type': data_manager.get_benchmarks(ccn_str, latest_year, 'State_Hospital_Type'),
    'state': data_manager.get_benchmarks(ccn_str, latest_year, 'State'),
    'hospital_type': data_manager.get_benchmarks(ccn_str, latest_year, 'Hospital_Type'),
    'national': data_manager.get_benchmarks(ccn_str, latest_year, 'National')
}
```

## Testing

### Test Results

Created `test_state_code_fix.py` to verify the fix. Results:

```
Testing CCN: 014000
======================================================================

1. Hospital Type Classification:
   Hospital Type: Psychiatric ✓

2. Hospital Type Classification (integer input 14000):
   Hospital Type: Psychiatric ✓

3. Get Benchmarks (State level):
   Benchmark Group: State 01 ✓
   Provider Count: 0 ⚠️  (NO BENCHMARKS IN DATABASE)
   KPIs Available: 0

4. Get Benchmarks (integer input 14000):
   Benchmark Group: State 01 ✓
   Provider Count: 0 ⚠️  (NO BENCHMARKS IN DATABASE)
   KPIs Available: 0

5. Get Benchmarks (State + Hospital Type level):
   Benchmark Group: 01 - Psychiatric ✓
   Provider Count: 0 ⚠️  (NO BENCHMARKS IN DATABASE)
   KPIs Available: 0

6. Manual State Code Extraction Test:
   Input CCN: 014000
   Normalized CCN: 014000 ✓
   Extracted State Code: 01 ✓
   State Code (as int): 1 ✓

7. Testing Provider from State 14: 140001
   Normalized CCN: 140001 ✓
   State Code: 14 ✓
   Benchmark Group: State 14 ✓
   Provider Count: 188 ✓  (BENCHMARKS EXIST)
```

### Summary

✅ **FIXED**: State code extraction from CCNs now works correctly
✅ **FIXED**: CCN normalization (zero-padding) working for all inputs
✅ **FIXED**: Hospital type classification handles both string and integer CCNs
✅ **FIXED**: Benchmark queries use correct state codes

⚠️ **REMAINING ISSUE**: Database is missing benchmarks for states 1 and 3

## Next Steps

### Option 1: Rebuild Database (Recommended)

The database build script needs to be updated to ensure all states get benchmarks calculated:

1. Update `scripts/build_database.py`:
   - Line 382-390: Ensure state code extraction from Provider_Number uses zero-padding
   - Verify hospital_metadata table has correct state codes
   - Re-run benchmark calculations for all states

2. Rebuild database:
```bash
cd "d:\HealthVista Analytics\hospital_dashboard"
python scripts/build_database.py
```

### Option 2: Manual Benchmark Generation

If rebuilding the entire database is not feasible, create benchmarks manually for missing states:

```sql
-- Calculate benchmarks for state 1
INSERT INTO hospital_benchmarks
SELECT
    KPI_Name,
    'State' as Benchmark_Level,
    1 as State_Code,
    NULL as Hospital_Type,
    Fiscal_Year,
    COUNT(*) as Provider_Count,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY value_col) as P25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY value_col) as Median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY value_col) as P75,
    AVG(value_col) as Mean
FROM hospital_kpis
WHERE Provider_Number >= 10000 AND Provider_Number < 20000
GROUP BY KPI_Name, Fiscal_Year;
```

## Impact

**Before Fix**:
- Hospitals with CCNs like 014000 would extract state code '14' instead of '01'
- No benchmarks would be found for these hospitals at State level
- Users would see "0 peers" in benchmark comparisons

**After Fix**:
- CCN normalization ensures state code '01' is extracted correctly
- Code correctly queries for state code 1 in the database
- Once database is rebuilt, benchmarks will appear for all states

## State Code Mapping Reference

| CCN Range | State Code (String) | State Code (Integer) | Example CCN |
|-----------|--------------------|--------------------|-------------|
| 010000-019999 | '01' | 1 | 014000 |
| 020000-029999 | '02' | 2 | 023456 |
| 030000-039999 | '03' | 3 | 033025 |
| 100000-109999 | '10' | 10 | 100123 |
| 140000-149999 | '14' | 14 | 140001 |
| 310000-319999 | '31' | 31 | 310001 |

---

**Date**: November 21, 2025
**Status**: ✅ Code Fix Complete | ⚠️ Database Rebuild Needed
**Files Modified**: 3 (data_manager.py, dashboard_callbacks.py, layouts.py)
**Test Script**: test_state_code_fix.py
