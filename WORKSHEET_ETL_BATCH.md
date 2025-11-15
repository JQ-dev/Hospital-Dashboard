# Batch ETL Processing - All Worksheets

## Overview
Automated ETL processing for all 20 CMS HCRIS worksheets with multi-state Hive partitioning.

**Date**: 2025-11-08
**Author**: JQ-dev
**Script**: `etl/create_all_worksheets.py`

## Worksheets Being Processed

| # | Worksheet | Description |
|---|-----------|-------------|
| 1 | A000000 | General Service Cost Centers |
| 2 | A700001 | Statistical Data |
| 3 | A700002 | Statistical Data |
| 4 | A700003 | Statistical Data |
| 5 | A800000 | Inpatient Routine Service Cost Centers |
| 6 | A810000 | Ancillary Service Cost Centers |
| 7 | A820010 | Outpatient Service Cost Centers |
| 8 | B000001 | Balance Sheet |
| 9 | B000002 | Statement of Revenues and Expenses |
| 10 | B100000 | Cost Allocation - Stepdown |
| 11 | C000001 | Allocation Statistics |
| 12 | S000001 | Part A Settlement |
| 13 | S100001 | Part A Provider Statistical and Reimbursement |
| 14 | S200001 | Part A Bad Debts |
| 15 | S300001 | Part B Settlement |
| 16 | S300002 | Part B Statistical and Reimbursement |
| 17 | S300004 | Part B Bad Debts |
| 18 | S300005 | Part B ASC Cost and Payment |
| 19 | S410000 | Home Health Agency (HHA) |
| 20 | S500000 | Hospice |

## Configuration

**States**:
- 31 (New Jersey)
- 34 (North Carolina)

**Fiscal Years**: 2020, 2021, 2022, 2023, 2024

**Output Structure**:
```
data/worksheets/
├── a000000/
│   ├── state_code=31/
│   │   ├── fiscal_year=2020/data.parquet
│   │   ├── fiscal_year=2021/data.parquet
│   │   ├── fiscal_year=2022/data.parquet
│   │   ├── fiscal_year=2023/data.parquet
│   │   └── fiscal_year=2024/data.parquet
│   └── state_code=34/
│       └── ... (same structure)
├── a700001/
│   └── ... (same structure)
├── a700002/
│   └── ... (same structure)
└── ... (18 more worksheets)
```

## ETL Process

### Per Worksheet Steps:
1. Load line/column names from HCRIS_LINE_COL_NAMES.csv
2. For each state (31, 34):
   - For each fiscal year (2020-2024):
     - Load report metadata (filtered by state)
     - Load numeric data (filtered by worksheet and state)
     - Join numeric data with report metadata
     - Join with line/column names for descriptions
3. Combine all state/year data
4. Save to Hive-partitioned parquet files

### Performance Optimizations:
- DuckDB in-memory processing
- Batch processing by worksheet
- Efficient CSV reading with DuckDB
- Partition pruning enabled via Hive structure

## Expected Output

### File Count
- **Worksheets**: 20
- **States**: 2
- **Fiscal Years**: 5
- **Total Partition Files**: up to 200 (20 × 2 × 5)

**Note**: Some worksheets may not have data for all state/year combinations.

## Data Schema (All Worksheets)

All worksheets follow the same standardized schema:

| Column | Type | Partition | Description |
|--------|------|-----------|-------------|
| state_code | string | ✓ | State code (31, 34) |
| fiscal_year | int32 | ✓ | Fiscal year (2020-2024) |
| Provider_Number | string | | Hospital CCN |
| FY_Begin_Date | datetime | | Fiscal year begin date |
| FY_End_Date | datetime | | Fiscal year end date |
| Worksheet | string | | Worksheet code |
| Line | string | | Line number (5-digit, zero-padded) |
| Column | string | | Column number (5-digit, zero-padded) |
| Report_Name | string | | Report category |
| line_level1 | string | | Line description level 1 |
| line_level2 | string | | Line description level 2 |
| col_level1 | string | | Column description level 1 |
| col_level2 | string | | Column description level 2 |
| Value | float64 | | Numeric value |

## Query Examples

### Query Single Worksheet
```python
import duckdb
con = duckdb.connect(':memory:')

# Query specific worksheet
df = con.execute('''
    SELECT *
    FROM read_parquet('data/worksheets/a700001/**/*.parquet', hive_partitioning=1)
    WHERE state_code = '31' AND fiscal_year = 2024
''').df()
```

### Query All Worksheets
```python
# Get summary across all worksheets
df = con.execute('''
    SELECT
        Worksheet,
        state_code,
        fiscal_year,
        COUNT(*) as record_count,
        COUNT(DISTINCT Provider_Number) as provider_count
    FROM read_parquet('data/worksheets/**/*.parquet', hive_partitioning=1)
    GROUP BY Worksheet, state_code, fiscal_year
    ORDER BY Worksheet, state_code, fiscal_year
''').df()
```

### Query Multiple Worksheets
```python
# Query balance sheet and income statement worksheets
df = con.execute('''
    SELECT *
    FROM read_parquet('data/worksheets/{b000001,b000002}/**/*.parquet', hive_partitioning=1)
    WHERE state_code = '34' AND fiscal_year IN (2023, 2024)
''').df()
```

### Join Across Worksheets
```python
# Join balance sheet with revenue data
df = con.execute('''
    SELECT
        b.Provider_Number,
        b.fiscal_year,
        b.Value as balance_sheet_value,
        r.Value as revenue_value
    FROM read_parquet('data/worksheets/b000001/**/*.parquet', hive_partitioning=1) b
    INNER JOIN read_parquet('data/worksheets/b000002/**/*.parquet', hive_partitioning=1) r
        ON b.Provider_Number = r.Provider_Number
        AND b.state_code = r.state_code
        AND b.fiscal_year = r.fiscal_year
        AND b.Line = r.Line
    WHERE b.state_code = '31'
''').df()
```

## Next Steps After ETL Completion

1. **Validate Data Quality**
   - Check record counts per worksheet
   - Verify all states and years are present
   - Validate line/column mappings

2. **Build DuckDB Database**
   - Create consolidated database from all parquet files
   - Add indexes on key columns
   - Pre-compute aggregations if needed

3. **Update Dashboard**
   - Point dashboard to new worksheet structure
   - Update queries to use Hive partitioning
   - Add worksheet selection dropdown

4. **Documentation**
   - Create data dictionary for each worksheet
   - Document common queries
   - Add troubleshooting guide

## Log Files

ETL execution logs saved to:
```
etl/logs/create_all_worksheets_YYYYMMDD_HHMMSS.log
```

## Benefits of Batch Processing

1. **Consistency**: All worksheets use same ETL logic
2. **Efficiency**: Single script processes all worksheets
3. **Maintainability**: One place to update ETL logic
4. **Scalability**: Easy to add more states or worksheets
5. **Standardization**: Uniform output structure

## Troubleshooting

### If a Worksheet Has No Data
- Check if worksheet code exists in HCRIS_LINE_COL_NAMES.csv
- Verify numeric data exists for that worksheet in source files
- Check if providers in selected states report that worksheet

### If ETL Fails
- Check log file for specific errors
- Verify source data files are present
- Ensure sufficient disk space for output
- Check memory availability (DuckDB uses RAM)

### Performance Issues
- Process fewer states/years at once
- Increase system memory
- Use SSD for faster I/O
- Consider processing worksheets individually

## Success Criteria

✓ All 20 worksheets processed without errors
✓ Hive-partitioned parquet files created
✓ Data queryable with hive_partitioning=1
✓ Record counts match expectations
✓ All states and fiscal years represented
✓ Line/column names properly joined

---

**Status**: Running
**Expected Duration**: 5-15 minutes depending on data volume
