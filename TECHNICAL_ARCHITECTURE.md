# Technical Architecture Documentation

## For LLM Context: Understanding the Database Approaches

This document explains the architecture of the Hospital Analytics Dashboard, specifically focusing on the two different database query approaches and how to improve the system.

---

## Executive Summary

The dashboard supports **two data access patterns**:

1. **Query-Based (Slow)**: On-demand calculation from raw parquet files or database tables
2. **Pre-Computed (Fast)**: Instant retrieval from pre-computed tables

The system automatically detects which approach to use and falls back gracefully.

---

## Architecture Overview

```
                    ┌─────────────────────────────┐
                    │   User Opens Dashboard      │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  HospitalDataManager Init   │
                    │  (dashboard.py:34-66)       │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Database File Exists?      │
                    └──┬──────────────────────┬───┘
                       │ YES                  │ NO
            ┌──────────▼──────────┐   ┌──────▼────────┐
            │ Can Open Database?  │   │ Use Parquet   │
            └──┬────────────┬─────┘   │ Files Direct  │
               │ YES        │ NO      └───────────────┘
               │            │
    ┌──────────▼──┐    ┌───▼──────────┐
    │Has KPI      │    │Use Raw Tables│
    │Tables?      │    │Only          │
    └──┬──────────┘    └──────────────┘
       │ YES
       │
    ┌──▼─────────────────────────────┐
    │ USE PRE-COMPUTED MODE (FAST!)  │
    │ - hospital_kpis table          │
    │ - hospital_benchmarks table    │
    │ - Indexed raw tables           │
    └────────────────────────────────┘
```

---

## 1. Query-Based Approach (Old/Fallback)

### How It Works

When pre-computed tables are NOT available, the system:
1. Reads raw parquet files directly
2. Performs aggregations at runtime
3. Calculates KPIs on-demand
4. Computes percentiles for benchmarks

### Code Location: `dashboard.py`

**Lines 147-304: `calculate_kpis()` method**
```python
def calculate_kpis(self, ccn, fiscal_years=None):
    # If we have pre-computed KPIs, use them (FAST!)
    if self.use_precomputed:
        # ... return pre-computed (lines 132-145)

    # OTHERWISE: Calculate from raw data (SLOW)
    con = duckdb.connect(':memory:')

    # Step 1: Aggregate balance sheet metrics
    balance_query = """
        SELECT Fiscal_Year,
            SUM(CASE WHEN Acc_level2 = 'Assets' AND Acc_level3 LIKE '%Current%'
                THEN Value ELSE 0 END) as Current_Assets,
            SUM(CASE WHEN Acc_level2 = 'Assets' THEN Value ELSE 0 END) as Total_Assets,
            ...
        FROM read_parquet(?, hive_partitioning=1)
        WHERE Provider_Number = ?
        GROUP BY Fiscal_Year
    """

    # Step 2: Aggregate revenue metrics
    # Step 3: Aggregate expense metrics
    # Step 4: Join all metrics
    # Step 5: Calculate 17 KPIs with formulas
```

**Lines 306-465: `get_benchmarks()` method**
```python
def get_benchmarks(self, ccn, fiscal_year, benchmark_level):
    # If we have pre-computed benchmarks, use them (FAST!)
    if self.use_precomputed:
        # ... return pre-computed (lines 316-369)

    # OTHERWISE: Calculate benchmarks (VERY SLOW)
    # Step 1: Get all hospitals in benchmark group
    # Step 2: Calculate KPIs for sample of hospitals
    # Step 3: Compute P25, Median, P75, Mean
```

### Performance Characteristics

| Operation | Time | Why Slow |
|-----------|------|----------|
| Load hospital KPIs | 5-15 sec | Scans 70M+ records, aggregates, calculates |
| Get benchmarks | 10-60 sec | Calculates KPIs for 100 hospitals, computes percentiles |
| Financial statements | 3-10 sec | Full table scans with filters |

### When It's Used

1. Database file doesn't exist
2. Database file is locked (being built)
3. Database exists but doesn't have `hospital_kpis` or `hospital_benchmarks` tables

---

## 2. Pre-Computed Approach (New/Optimized)

### How It Works

Pre-computation happens in `scripts/build_database.py`:

**Step 1: Build Raw Tables (Lines 52-120)**
```python
def build_raw_tables(con):
    # Load all parquet files into DuckDB tables
    con.execute("""
        CREATE TABLE balance_sheet AS
        SELECT * FROM read_parquet('../../poc_env/balance_sheet_long/**/*.parquet')
    """)

    # Create indexes for fast lookups
    con.execute("CREATE INDEX idx_bs_provider ON balance_sheet(Provider_Number)")
    con.execute("CREATE INDEX idx_bs_year ON balance_sheet(Fiscal_Year)")
```

**Step 2: Pre-Compute KPIs (Lines 122-276)**
```python
def build_kpi_table(con):
    # Single SQL query that:
    # 1. Joins balance_sheet, revenue, revenue_expenses
    # 2. Calculates ALL 17 KPIs for ALL hospital-year combinations
    # 3. Stores in hospital_kpis table

    con.execute("""
        CREATE TABLE hospital_kpis AS
        WITH
        balance_metrics AS (SELECT ... GROUP BY Provider_Number, Fiscal_Year),
        revenue_metrics AS (SELECT ... GROUP BY Provider_Number, Fiscal_Year),
        expense_metrics AS (SELECT ... GROUP BY Provider_Number, Fiscal_Year)

        SELECT
            Provider_Number, Fiscal_Year,
            -- 17 pre-calculated KPIs
            CASE WHEN Total_Revenue > 0
                THEN ((Total_Revenue - Total_Operating_Expenses) / Total_Revenue) * 100
                ELSE NULL END as Operating_Margin_Pct,
            ...
    """)

    # Result: 27,105 rows (one per hospital-year with all KPIs)
```

**Step 3: Pre-Compute Benchmarks (Lines 278-442)**
```python
def build_benchmark_tables(con):
    # For each benchmark level (National, State, Hospital Type, State+Type)
    # For each year (2019-2025)
    # For each KPI (17 KPIs)
    # Calculate: P25, Median, P75, Mean

    # Example for National benchmarks:
    stats = con.execute("""
        SELECT
            ? as KPI_Name,
            'National' as Benchmark_Level,
            ? as Fiscal_Year,
            COUNT(*) as Provider_Count,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY value_col) as P25,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY value_col) as Median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY value_col) as P75,
            AVG(value_col) as Mean
        FROM hospital_kpis
        WHERE Fiscal_Year = ? AND [KPI_column] IS NOT NULL
    """, [kpi_name, year, year])

    # Result: 28,268 benchmark rows
    # - National: 119 (7 years × 17 KPIs)
    # - State: 5,629
    # - Hospital_Type: 690
    # - State_Hospital_Type: 21,830
```

**Step 4: Optimize (Lines 444-457)**
```python
def analyze_database(con):
    # Run ANALYZE to update statistics
    # Enables query optimizer to use indexes effectively
    con.execute("ANALYZE hospital_kpis")
    con.execute("ANALYZE hospital_benchmarks")
```

### Dashboard Usage

**KPI Lookup (Lines 132-145 in dashboard.py)**
```python
def calculate_kpis(self, ccn, fiscal_years=None):
    if self.use_precomputed:
        con = self.get_connection()
        kpi_df = con.execute("""
            SELECT * FROM hospital_kpis
            WHERE Provider_Number = ?
            ORDER BY Fiscal_Year DESC
        """, [int(ccn)]).df()
        con.close()
        return kpi_df  # INSTANT - just an indexed lookup!
```

**Benchmark Lookup (Lines 316-369 in dashboard.py)**
```python
def get_benchmarks(self, ccn, fiscal_year, benchmark_level):
    if self.use_precomputed:
        benchmarks_df = con.execute("""
            SELECT KPI_Name, Provider_Count, P25, Median, P75, Mean
            FROM hospital_benchmarks
            WHERE Benchmark_Level = ? AND Fiscal_Year = ?
        """, [level, year]).df()
        # INSTANT - indexed lookup, no calculations!
```

### Performance Characteristics

| Operation | Time | Why Fast |
|-----------|------|----------|
| Load hospital KPIs | < 50ms | Single indexed SELECT |
| Get benchmarks | < 50ms | Single indexed SELECT |
| Financial statements | < 200ms | Indexed raw table queries |

**Speedup: 50-300x faster!**

---

## 3. Database Schema

### Pre-Computed Tables

**hospital_kpis** (27,105 rows)
```sql
CREATE TABLE hospital_kpis (
    Provider_Number INTEGER,
    Fiscal_Year INTEGER,

    -- Raw financial metrics
    Current_Assets DOUBLE,
    Fixed_Assets DOUBLE,
    Total_Assets DOUBLE,
    Current_Liabilities DOUBLE,
    Total_Liabilities DOUBLE,
    Fund_Balance DOUBLE,
    Cash_And_Securities DOUBLE,
    Accounts_Receivable DOUBLE,
    Inpatient_Revenue DOUBLE,
    Outpatient_Revenue DOUBLE,
    Total_Revenue DOUBLE,
    Total_Operating_Expenses DOUBLE,
    Net_Income DOUBLE,

    -- Calculated KPIs (17 metrics)
    Operating_Margin_Pct DOUBLE,
    Net_Margin_Pct DOUBLE,
    Total_Margin_Pct DOUBLE,
    Current_Ratio DOUBLE,
    Days_Cash_On_Hand DOUBLE,
    Working_Capital DOUBLE,
    Outpatient_Revenue_Pct DOUBLE,
    Inpatient_Revenue_Pct DOUBLE,
    Asset_Turnover_Ratio DOUBLE,
    Fixed_Asset_Turnover DOUBLE,
    AR_Days DOUBLE,
    Operating_Expense_Ratio DOUBLE,
    Debt_to_Equity_Ratio DOUBLE,
    Equity_Ratio_Pct DOUBLE,
    Debt_Ratio_Pct DOUBLE,
    Return_on_Assets_Pct DOUBLE,
    Return_on_Equity_Pct DOUBLE,
    Revenue_Growth_Pct DOUBLE
);

CREATE INDEX idx_kpis_provider ON hospital_kpis(Provider_Number);
CREATE INDEX idx_kpis_year ON hospital_kpis(Fiscal_Year);
CREATE INDEX idx_kpis_provider_year ON hospital_kpis(Provider_Number, Fiscal_Year);
```

**hospital_benchmarks** (28,268 rows)
```sql
CREATE TABLE hospital_benchmarks (
    KPI_Name VARCHAR,              -- e.g., 'Operating_Margin_Pct'
    Benchmark_Level VARCHAR,       -- 'National', 'State', 'Hospital_Type', 'State_Hospital_Type'
    State_Code VARCHAR,            -- e.g., '06' for California (NULL for National)
    Hospital_Type VARCHAR,         -- e.g., 'Short Term Acute Care' (NULL for National/State)
    Fiscal_Year INTEGER,           -- 2019-2025
    Provider_Count INTEGER,        -- Number of hospitals in benchmark group
    P25 DOUBLE,                    -- 25th percentile
    Median DOUBLE,                 -- 50th percentile
    P75 DOUBLE,                    -- 75th percentile
    Mean DOUBLE                    -- Average
);

CREATE INDEX idx_bench_level ON hospital_benchmarks(Benchmark_Level);
CREATE INDEX idx_bench_year ON hospital_benchmarks(Fiscal_Year);
CREATE INDEX idx_bench_kpi ON hospital_benchmarks(KPI_Name);
CREATE INDEX idx_bench_state ON hospital_benchmarks(State_Code);
CREATE INDEX idx_bench_type ON hospital_benchmarks(Hospital_Type);
```

**hospital_metadata** (6,021 rows)
```sql
CREATE TABLE hospital_metadata (
    Provider_Number INTEGER PRIMARY KEY,
    State_Code VARCHAR,
    Hospital_Type VARCHAR  -- Classified by CCN range
);

CREATE INDEX idx_meta_provider ON hospital_metadata(Provider_Number);
```

### Raw Data Tables

**balance_sheet** (834,794 rows)
```sql
-- Columns: Provider_Number, Fiscal_Year, State_Code, Acc_level1, Acc_level2,
--          Acc_level3, Line, Line_Name, Column_name, Acc_name, Value
-- Indexes: Provider_Number, Fiscal_Year, (Provider_Number, Fiscal_Year)
```

**revenue** (1,934,508 rows)
```sql
-- Columns: Provider_Number, Fiscal_Year, State_Code, Revenue_Line_Name,
--          Rev_Level, Rev_Account, Value
-- Indexes: Provider_Number, Fiscal_Year, (Provider_Number, Fiscal_Year)
```

**revenue_expenses** (1,263,804 rows)
```sql
-- Columns: Provider_Number, Fiscal_Year, State_Code, RE_Line_Name, RE_Level,
--          RE_Report, RE_Account, Value
-- Indexes: Provider_Number, Fiscal_Year, (Provider_Number, Fiscal_Year)
```

**costs** (67,030,350 rows)
```sql
-- Columns: Provider_Number, Fiscal_Year, State_Code, Cost_Center,
--          Cost_Level1, Cost_Level2, Cost_Level3, Line, Value
-- Indexes: Provider_Number, Fiscal_Year, (Provider_Number, Fiscal_Year)
```

---

## 4. Code Flow: How the System Chooses

### Initialization (dashboard.py:34-66)

```python
class HospitalDataManager:
    def __init__(self, db_path='data/hospital_analytics.duckdb'):
        self.db_path = db_path
        self.use_database = Path(db_path).exists()

        if self.use_database:
            try:
                # Try to open database
                con = duckdb.connect(db_path, read_only=True)
                tables = con.execute("SHOW TABLES").df()['name'].tolist()

                # Check for pre-computed tables
                self.use_precomputed = 'hospital_kpis' in tables and \
                                      'hospital_benchmarks' in tables
                con.close()

                if self.use_precomputed:
                    print("Using optimized database with pre-computed KPIs")
                else:
                    print("Using database (raw tables only)")
            except Exception as e:
                # Database locked or corrupted - fall back to parquet
                print(f"Database cannot be opened: {e}")
                self.use_database = False
                self.use_precomputed = False
                # Set parquet paths
        else:
            # No database - use parquet files
            print("Database not found, falling back to parquet files")
            self.use_precomputed = False
            # Set parquet paths
```

### Decision Tree

```
Database file exists?
├─ NO → use_database=False, use_precomputed=False
│       USE: Parquet files
│
└─ YES → Can open database?
    ├─ NO → use_database=False, use_precomputed=False
    │        USE: Parquet files (fallback)
    │
    └─ YES → Has hospital_kpis AND hospital_benchmarks?
        ├─ NO → use_database=True, use_precomputed=False
        │        USE: Raw database tables (faster than parquet, but still slow)
        │
        └─ YES → use_database=True, use_precomputed=True
                 USE: Pre-computed tables (FAST!)
```

---

## 5. Areas for Improvement

### High Priority

#### 1. Add Incremental Updates
**Problem**: Full database rebuild takes 28 minutes
**Solution**: Add incremental update capability

```python
# New function in build_database.py
def update_database_incremental(con, new_fiscal_year):
    """Add data for new fiscal year without rebuilding everything"""

    # Step 1: Load only new year's data
    con.execute(f"""
        INSERT INTO balance_sheet
        SELECT * FROM read_parquet('../../poc_env/balance_sheet_long/Fiscal_Year={new_fiscal_year}/**/*.parquet')
    """)

    # Step 2: Update KPIs for affected hospitals
    con.execute(f"""
        INSERT INTO hospital_kpis
        SELECT ... (KPI calculation)
        FROM balance_sheet b
        JOIN revenue r ON ...
        WHERE b.Fiscal_Year = {new_fiscal_year}
    """)

    # Step 3: Recalculate benchmarks for new year only
    # Step 4: ANALYZE updated tables
```

**Impact**: Reduce update time from 28 minutes to ~2-3 minutes

#### 2. Add Data Validation
**Problem**: No validation that pre-computed data matches raw data
**Solution**: Add validation queries

```python
# New function in scripts/
def validate_database(con):
    """Verify pre-computed KPIs match raw data calculations"""

    # Test sample of hospitals
    test_hospitals = con.execute("""
        SELECT Provider_Number
        FROM hospital_kpis
        ORDER BY RANDOM()
        LIMIT 10
    """).df()

    for _, row in test_hospitals.iterrows():
        # Calculate KPIs from raw tables
        raw_kpis = calculate_kpis_from_raw(con, row['Provider_Number'])

        # Compare with pre-computed
        precomputed_kpis = con.execute("""
            SELECT * FROM hospital_kpis
            WHERE Provider_Number = ?
        """, [row['Provider_Number']]).df()

        # Check differences
        differences = compare_kpis(raw_kpis, precomputed_kpis)
        if differences:
            print(f"WARNING: Mismatch for {row['Provider_Number']}: {differences}")
```

**Impact**: Catch data quality issues early

#### 3. Cache Hospital List
**Problem**: Dashboard loads 6,021 hospitals from parquet on every restart (takes 5-10 seconds)
**Solution**: Store hospital list in database

```python
# In build_database.py, add:
def build_hospital_list(con):
    con.execute("""
        CREATE TABLE hospital_list AS
        SELECT DISTINCT
            b.Provider_Number,
            b.State_Code,
            m.Hospital_Type,
            COUNT(DISTINCT b.Fiscal_Year) as Year_Count,
            MIN(b.Fiscal_Year) as First_Year,
            MAX(b.Fiscal_Year) as Latest_Year
        FROM balance_sheet b
        JOIN hospital_metadata m ON b.Provider_Number = m.Provider_Number
        GROUP BY b.Provider_Number, b.State_Code, m.Hospital_Type
        ORDER BY b.State_Code, b.Provider_Number
    """)

    con.execute("CREATE INDEX idx_hosp_list_provider ON hospital_list(Provider_Number)")
```

```python
# In dashboard.py, update get_available_hospitals():
def get_available_hospitals(self):
    if self.use_database:
        con = self.get_connection()
        hospitals_df = con.execute("""
            SELECT Provider_Number, State_Code, Hospital_Type, Year_Count, Latest_Year
            FROM hospital_list
        """).df()
        con.close()
        return hospitals_df
    else:
        # Fallback to parquet scan
```

**Impact**: Dashboard startup from 10 seconds to < 1 second

#### 4. Add Missing KPIs
**Current**: 17 KPIs tracked
**Potential**: CMS HCRIS has 100+ financial metrics

```python
# Examples of additional KPIs to add:
additional_kpis = {
    'Labor_Cost_Pct': 'Labor costs as % of operating expenses',
    'Supply_Cost_Pct': 'Supply costs as % of operating expenses',
    'Bad_Debt_Pct': 'Bad debt as % of revenue',
    'Charity_Care_Pct': 'Charity care as % of revenue',
    'Medicare_Pct': 'Medicare revenue as % of total revenue',
    'Medicaid_Pct': 'Medicaid revenue as % of total revenue',
    'Length_of_Stay_Days': 'Average length of stay',
    'Occupancy_Rate_Pct': 'Bed occupancy rate',
    'Cost_Per_Discharge': 'Average cost per discharge',
    'Revenue_Per_Bed': 'Annual revenue per bed'
}
```

**Impact**: More comprehensive financial analysis

### Medium Priority

#### 5. Add Trend Analysis Table
**Problem**: Revenue growth calculated in window function (slow for multi-year trends)
**Solution**: Pre-compute all year-over-year changes

```python
def build_trend_table(con):
    con.execute("""
        CREATE TABLE hospital_trends AS
        SELECT
            Provider_Number,
            Fiscal_Year,
            -- Year-over-year changes for all metrics
            Revenue_YoY_Change_Pct,
            Revenue_YoY_Change_Dollars,
            Operating_Margin_YoY_Change,
            -- 3-year CAGR
            Revenue_3yr_CAGR,
            -- 5-year CAGR
            Revenue_5yr_CAGR
        FROM ...
    """)
```

**Impact**: Faster trend visualizations

#### 6. Add Financial Ratios Table
**Problem**: Financial statements still query raw tables
**Solution**: Pre-aggregate by major categories

```python
def build_financial_summary_table(con):
    con.execute("""
        CREATE TABLE financial_summary AS
        SELECT
            Provider_Number,
            Fiscal_Year,
            Fund_Type,
            Category,
            Subcategory,
            Line_Count,
            Total_Value,
            Pct_of_Category
        FROM balance_sheet
        GROUP BY Provider_Number, Fiscal_Year, Fund_Type, Category, Subcategory
    """)
```

**Impact**: Financial statements load 5-10x faster

#### 7. Add Data Quality Metrics
**Problem**: No visibility into data completeness
**Solution**: Track data quality by hospital

```python
def build_data_quality_table(con):
    con.execute("""
        CREATE TABLE data_quality AS
        SELECT
            Provider_Number,
            Fiscal_Year,
            Balance_Sheet_Lines,
            Revenue_Lines,
            Cost_Lines,
            Missing_KPIs,
            Data_Completeness_Pct,
            Last_Updated_Date
        FROM ...
    """)
```

**Impact**: Better transparency for users

### Low Priority

#### 8. Add Compression
**Current**: Database is 3.51 GB
**Potential**: DuckDB supports ZSTD compression

```python
# In build_database.py main():
con.execute("PRAGMA enable_object_cache")
con.execute("PRAGMA enable_http_metadata_cache")
con.execute("PRAGMA max_memory='8GB'")
con.execute("PRAGMA threads=4")

# After creating tables:
con.execute("OPTIMIZE")  # Compact and compress
```

**Impact**: Reduce database size to ~2 GB

#### 9. Add Query Logging
**Problem**: No visibility into slow queries
**Solution**: Add query performance logging

```python
# In HospitalDataManager:
import time
import logging

def execute_with_logging(self, query, params=None):
    start = time.time()
    con = self.get_connection()
    result = con.execute(query, params).df() if params else con.execute(query).df()
    duration = time.time() - start

    if duration > 1.0:  # Log slow queries
        logging.warning(f"Slow query ({duration:.2f}s): {query[:100]}...")

    con.close()
    return result
```

**Impact**: Identify performance bottlenecks

---

## 6. Testing Strategy

### Unit Tests
```python
# tests/test_database.py
def test_kpi_calculation():
    """Verify KPI formulas are correct"""
    # Test case: Known hospital with verified financials
    kpis = data_manager.calculate_kpis('010001')

    assert abs(kpis['Operating_Margin_Pct'].iloc[0] - 3.5) < 0.01
    assert abs(kpis['Current_Ratio'].iloc[0] - 1.8) < 0.01

def test_benchmark_calculation():
    """Verify benchmarks are calculated correctly"""
    benchmarks = data_manager.get_benchmarks('060001', 2024, 'National')

    assert benchmarks['provider_count'] > 1000
    assert benchmarks['kpis']['Operating_Margin_Pct']['P25'] < \
           benchmarks['kpis']['Operating_Margin_Pct']['Median'] < \
           benchmarks['kpis']['Operating_Margin_Pct']['P75']

def test_fallback_behavior():
    """Verify system falls back gracefully"""
    # Simulate missing database
    manager = HospitalDataManager(db_path='nonexistent.duckdb')
    assert not manager.use_database
    assert not manager.use_precomputed
```

### Integration Tests
```python
# tests/test_dashboard.py
def test_dashboard_load_time():
    """Verify dashboard loads within acceptable time"""
    start = time.time()
    # Select hospital and load KPIs
    duration = time.time() - start
    assert duration < 0.5  # Should be < 500ms with pre-computed

def test_financial_statements():
    """Verify financial statements load correctly"""
    balance_sheet = load_balance_sheet('010001', 'General Fund')
    assert not balance_sheet.empty
    assert 'Assets' in balance_sheet['Acc_level1'].values
```

### Performance Tests
```python
# tests/test_performance.py
def test_query_performance():
    """Benchmark query times"""
    times = []
    for hospital in sample_hospitals:
        start = time.time()
        data_manager.calculate_kpis(hospital)
        times.append(time.time() - start)

    avg_time = sum(times) / len(times)
    assert avg_time < 0.1  # Average should be < 100ms
```

---

## 7. Deployment Checklist

### Initial Setup
- [ ] Run ETL pipeline (`etl/create_*.py`)
- [ ] Build optimized database (`scripts/build_database.py`)
- [ ] Verify database size (~3.5 GB)
- [ ] Test dashboard startup (< 15 seconds)
- [ ] Test hospital selection (< 100ms)

### Adding New Fiscal Year
- [ ] Run ETL for new year
- [ ] Run incremental database update (once implemented)
- [ ] Verify new year appears in dashboard
- [ ] Test KPIs for new year

### Performance Monitoring
- [ ] Check query times in logs
- [ ] Monitor database file size
- [ ] Verify index usage (`EXPLAIN QUERY PLAN`)
- [ ] Check memory usage during queries

---

## 8. Common Issues & Solutions

### Issue: Dashboard says "Falling back to parquet files"
**Cause**: Database doesn't exist or can't be opened
**Solution**:
1. Check if `data/hospital_analytics.duckdb` exists
2. Rebuild database: `python scripts/build_database.py data/hospital_analytics.duckdb`

### Issue: Dashboard slow even with database
**Cause**: Database exists but doesn't have pre-computed tables
**Solution**: Check database was built with new script (not old build_fast_database.py)

### Issue: KPIs don't match expectations
**Cause**: KPI formula error or data quality issue
**Solution**:
1. Verify raw data: `SELECT * FROM balance_sheet WHERE Provider_Number = ? LIMIT 10`
2. Check KPI calculation: Compare with manual calculation
3. Run validation script (once implemented)

### Issue: Benchmarks returning NULL
**Cause**: Not enough hospitals in benchmark group
**Solution**: Check Provider_Count in hospital_benchmarks table

### Issue: Database build fails
**Cause**: Insufficient memory or disk space
**Solution**:
1. Increase memory: Change `SET memory_limit='8GB'` to higher value
2. Free disk space (needs ~4 GB)
3. Check parquet files exist in `../../poc_env/`

---

## 9. Quick Reference: Key Files

| File | Purpose | Lines of Interest |
|------|---------|-------------------|
| `dashboard.py` | Main app | 34-66 (init), 126-304 (KPIs), 306-465 (benchmarks) |
| `scripts/build_database.py` | Database builder | 52-120 (raw), 122-276 (KPIs), 278-442 (benchmarks) |
| `etl/create_balance_sheet.py` | Balance sheet ETL | Transforms raw HCRIS to long format |
| `etl/create_revenue.py` | Revenue ETL | Transforms revenue data |
| `etl/create_revenue_expenses.py` | R&E ETL | Transforms operating expenses |
| `etl/create_costs.py` | Costs ETL | Transforms cost center data |

---

## 10. LLM Instructions for Future Improvements

### To Add a New KPI:

1. **Update `scripts/build_database.py`** (build_kpi_table function ~line 220):
   ```python
   # Add your KPI calculation
   CASE WHEN [denominator] > 0
       THEN [numerator] / [denominator] * 100
       ELSE NULL
   END as New_KPI_Name,
   ```

2. **Update `dashboard.py`** (KPI_METADATA dictionary ~line 465):
   ```python
   'New_KPI_Name': {
       'name': 'Display Name',
       'category': 'Profitability',  # or Liquidity, Efficiency, Leverage, Returns
       'unit': '%',
       'format': '.1f',
       'higher_is_better': True,
       'target_range': (min, max),
       'impact_score': 1-10,
       'ease_of_change': 1-10,
       'description': 'What this KPI measures',
       'improvement_levers': ['Action 1', 'Action 2']
   }
   ```

3. **Rebuild database**

### To Add a New Benchmark Level:

1. **Update `scripts/build_database.py`** (build_benchmark_tables function ~line 410):
   ```python
   # Add new benchmark level (e.g., "Region")
   for region in regions:
       for year in years:
           for kpi in kpi_columns:
               stats = con.execute("""
                   SELECT ... FROM hospital_kpis k
                   JOIN hospital_metadata m ON ...
                   WHERE m.Region = ? AND k.Fiscal_Year = ?
               """, [region, year])
   ```

2. **Update `dashboard.py`** (benchmark dropdown ~line 990)

3. **Rebuild database**

### To Optimize a Slow Query:

1. **Add EXPLAIN to see query plan**:
   ```python
   con.execute("EXPLAIN QUERY PLAN SELECT ...").df()
   ```

2. **Check if indexes are used** (look for "INDEX SCAN" not "SEQ SCAN")

3. **Add index if needed**:
   ```python
   con.execute("CREATE INDEX idx_name ON table(column)")
   ```

4. **Re-run ANALYZE**:
   ```python
   con.execute("ANALYZE table")
   ```

---

## Summary

This system uses a **two-tier architecture**:
- **Tier 1 (Fast)**: Pre-computed KPIs and benchmarks in indexed database tables
- **Tier 2 (Fallback)**: On-demand calculation from parquet files

The pre-computation happens once during database build and provides **50-300x speedup** for dashboard queries.

Future improvements should focus on:
1. Incremental updates (reduce rebuild time)
2. Additional KPIs (expand analytics)
3. Data validation (ensure accuracy)
4. Caching optimizations (faster startup)

The code is designed to gracefully degrade from fast → medium → slow depending on what's available.
