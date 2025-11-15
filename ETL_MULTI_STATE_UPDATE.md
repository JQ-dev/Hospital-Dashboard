# ETL Multi-State Update - Worksheet A000000

## Overview
Successfully updated the ETL pipeline to support multiple states with Hive-style partitioning by state_code and fiscal_year.

**Date**: 2025-11-08
**Author**: JQ-dev

## Key Changes

### 1. Multiple States Support
- **Previous**: Single state (State 31 - New Jersey)
- **Updated**: Multiple states (State 31 - New Jersey, State 34 - North Carolina)
- **Configurable**: Easy to add more states by updating `STATE_CODES` list

### 2. Hive-Style Partitioning
**Partition Structure**:
```
data/worksheets/a000000/
├── state_code=31/
│   ├── fiscal_year=2020/data.parquet
│   ├── fiscal_year=2021/data.parquet
│   ├── fiscal_year=2022/data.parquet
│   ├── fiscal_year=2023/data.parquet
│   └── fiscal_year=2024/data.parquet
└── state_code=34/
    ├── fiscal_year=2020/data.parquet
    ├── fiscal_year=2021/data.parquet
    ├── fiscal_year=2022/data.parquet
    ├── fiscal_year=2023/data.parquet
    └── fiscal_year=2024/data.parquet
```

### 3. Updated Data Schema

**Columns**:
| Column | Type | Description |
|--------|------|-------------|
| state_code | string | State code (partition column) |
| fiscal_year | int32 | Fiscal year (partition column) |
| Provider_Number | string | Hospital CCN |
| FY_Begin_Date | datetime | Fiscal year begin date |
| FY_End_Date | datetime | Fiscal year end date |
| Worksheet | string | Worksheet code (A000000) |
| Line | string | Line number (5-digit) |
| Column | string | Column number (5-digit) |
| Report_Name | string | Report category |
| line_level1 | string | Line description level 1 |
| line_level2 | string | Line description level 2 |
| col_level1 | string | Column description level 1 |
| col_level2 | string | Column description level 2 |
| Value | float64 | Numeric value |

**Note**: `state_code` and `fiscal_year` are **partition columns** and automatically added by Hive partitioning when querying.

## ETL Results

### Total Statistics
- **Total Records**: 287,895
- **Unique Providers**: 229
- **States**: 2 (New Jersey, North Carolina)
- **Fiscal Years**: 5 (2020-2024)
- **Execution Time**: ~28 seconds

### State 31 (New Jersey)
| Fiscal Year | Records | Providers |
|-------------|---------|-----------|
| 2020 | 25,734 | 95 |
| 2021 | 25,811 | 95 |
| 2022 | 25,659 | 95 |
| 2023 | 25,387 | 95 |
| 2024 | 21,328 | 74 |
| **Total** | **123,919** | **97** |

### State 34 (North Carolina)
| Fiscal Year | Records | Providers |
|-------------|---------|-----------|
| 2020 | 34,775 | 128 |
| 2021 | 35,572 | 128 |
| 2022 | 35,312 | 126 |
| 2023 | 34,769 | 128 |
| 2024 | 23,548 | 87 |
| **Total** | **163,976** | **132** |

## How to Query with Hive Partitioning

### Example 1: Query All Data
```python
import duckdb
con = duckdb.connect(':memory:')

df = con.execute('''
    SELECT *
    FROM read_parquet('data/worksheets/a000000/**/*.parquet', hive_partitioning=1)
    LIMIT 10
''').df()
```

### Example 2: Filter by State
```python
df = con.execute('''
    SELECT *
    FROM read_parquet('data/worksheets/a000000/**/*.parquet', hive_partitioning=1)
    WHERE state_code = '31'
''').df()
```

### Example 3: Filter by State and Year
```python
df = con.execute('''
    SELECT *
    FROM read_parquet('data/worksheets/a000000/**/*.parquet', hive_partitioning=1)
    WHERE state_code = '31' AND fiscal_year = 2024
''').df()
```

### Example 4: Aggregate by State and Year
```python
df = con.execute('''
    SELECT
        state_code,
        fiscal_year,
        COUNT(*) as record_count,
        COUNT(DISTINCT Provider_Number) as provider_count
    FROM read_parquet('data/worksheets/a000000/**/*.parquet', hive_partitioning=1)
    GROUP BY state_code, fiscal_year
    ORDER BY state_code, fiscal_year
''').df()
```

### Example 5: Query Specific Line/Column
```python
df = con.execute('''
    SELECT *
    FROM read_parquet('data/worksheets/a000000/**/*.parquet', hive_partitioning=1)
    WHERE state_code = '34'
        AND fiscal_year = 2024
        AND Line = '00100'
        AND "Column" = '00700'
''').df()
```

**Important**: Use double quotes around `"Column"` in SQL queries since it's a reserved word.

## Benefits of Hive Partitioning

1. **Efficient Filtering**: Query optimizer only reads relevant partition files
2. **Automatic Metadata**: Partition columns added automatically during query
3. **Scalable**: Easy to add more states/years without changing schema
4. **Standard Format**: Compatible with Spark, Presto, Athena, and other tools
5. **Performance**: Partition pruning reduces I/O significantly

### Performance Example
```python
# Without partitioning: Reads ALL 10 files
SELECT * FROM data WHERE state_code = '31'

# With Hive partitioning: Reads ONLY 5 files (state_code=31/*)
SELECT * FROM read_parquet('.../**/*.parquet', hive_partitioning=1)
WHERE state_code = '31'
```

## Configuration

To add more states, simply update the configuration in `create_worksheet_a000000.py`:

```python
# Configuration
STATE_CODES = ['31', '34', '05']  # Add state code
STATE_NAMES = {
    '31': 'New Jersey',
    '34': 'North Carolina',
    '05': 'California'  # Add state name
}
```

## File Locations

**ETL Script**: `etl/create_worksheet_a000000.py`
**Output Data**: `data/worksheets/a000000/`
**Log Files**: `etl/logs/create_worksheet_a000000_*.log`

## Tested Scenarios

✅ Query all data across all states and years
✅ Filter by single state
✅ Filter by state and year
✅ Aggregate counts by partition columns
✅ Query specific Line/Column combinations
✅ Partition column metadata automatically added
✅ File structure follows Hive conventions

## Next Steps

1. **Apply to Other Worksheets**: Use same pattern for G000000, G200000, G300000, B000000, B100000
2. **Build DuckDB Database**: Once all worksheets are ready, create consolidated database
3. **Update Dashboard**: Read from new Hive-partitioned parquet files
4. **Add More States**: Expand to all US states for production

## Migration Notes

### Old Structure (Single State, Single Partition)
```
data/worksheets/a000000/
├── fiscal_year=2020/worksheet_a000000_fy2020.parquet
├── fiscal_year=2021/worksheet_a000000_fy2021.parquet
└── ...
```

### New Structure (Multi-State, Dual Partition)
```
data/worksheets/a000000/
├── state_code=31/fiscal_year=2020/data.parquet
├── state_code=31/fiscal_year=2021/data.parquet
├── state_code=34/fiscal_year=2020/data.parquet
└── ...
```

### Query Differences
```python
# Old: No state_code column
SELECT * FROM old_data WHERE fiscal_year = 2024

# New: state_code available as partition column
SELECT * FROM new_data
WHERE state_code = '31' AND fiscal_year = 2024
```

## Validation Results

```
Testing Hive Partitioning Query
================================================================================

1. Query all data (LIMIT 5):
 state_code  fiscal_year Provider_Number  Line Column       Value
         31         2020          310001 00100  00200  24573240.0
         31         2020          310001 00100  00300  24573240.0
         31         2020          310001 00100  00400  35120323.0
         31         2020          310001 00100  00500  59693563.0
         31         2020          310001 00100  00600 -24433418.0

2. Query State 31, FY 2024 (LIMIT 5):
 state_code  fiscal_year Provider_Number  Line Column       Value
         31         2024          310001 00100  00200  42731590.0
         31         2024          310001 00100  00300  42731590.0
         31         2024          310001 00100  00400  35381813.0
         31         2024          310001 00100  00500  78113403.0
         31         2024          310001 00100  00600 -43812184.0

3. Record counts by State and Fiscal Year:
 state_code  fiscal_year  record_count  provider_count
         31         2020         25734              95
         31         2021         25811              95
         31         2022         25659              95
         31         2023         25387              95
         31         2024         21328              74
         34         2020         34775             128
         34         2021         35572             128
         34         2022         35312             126
         34         2023         34769             128
         34         2024         23548              87
```

## Success Criteria

✅ **Multi-state support**: 2 states processed successfully
✅ **Hive partitioning**: Dual partition (state_code/fiscal_year)
✅ **287,895 records** processed
✅ **229 providers** across both states
✅ **Query performance**: Partition pruning works correctly
✅ **Data integrity**: All counts match expected values
✅ **Standardized schema**: Compatible with other BI tools

---

**Status**: ✅ Complete and Tested
**Ready for**: Production use and template for other worksheets
