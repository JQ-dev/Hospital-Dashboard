# Quick Start Guide

Get the Hospital Analytics Dashboard running in 3 simple steps!

## Prerequisites Check

Before starting, verify you have:
- [x] Python 3.8 or higher installed
- [x] 8GB+ RAM
- [x] Transformed parquet data in `../poc_env/` folders

## Step 1: Install Dependencies (2 minutes)

```bash
cd hospital_dashboard
pip install -r requirements.txt
```

## Step 2: Build Optimized Database (20-40 minutes)

This is a one-time setup that pre-computes all KPIs and benchmarks:

```bash
cd scripts
python build_database.py ../data/hospital_analytics.duckdb
```

**What's happening:**
- Loading 71M+ financial records from parquet files
- Computing 27K+ pre-computed KPI records
- Generating benchmarks for 4 levels across 7 years
- Creating indexes for instant queries

**Expected output:**
```
================================================================================
DATABASE BUILD COMPLETE
================================================================================

TABLE SUMMARY:
  hospital_kpis: 27,105 records
  hospital_benchmarks: 8,XXX records
  balance_sheet: 834,794 records
  revenue: 1,934,508 records
  revenue_expenses: 1,263,804 records
  costs: 67,030,350 records

HOSPITAL COVERAGE:
  Hospitals: 6,224
  Years: 7 (2019-2025)

DATABASE FILE:
  Path: ../data/hospital_analytics.duckdb
  Size: 2.XX GB
================================================================================
```

## Step 3: Launch Dashboard (< 1 minute)

```bash
cd ..
python dashboard.py
```

**Expected output:**
```
Using optimized database with pre-computed KPIs: data/hospital_analytics.duckdb
Loading hospitals from parquet files...
Found 6021 hospitals in parquet files
Loaded 6021 hospitals total
Hospital options ready: 6021 hospitals

================================================================================
STARTING HOSPITAL KPI SCORECARD DASHBOARD
================================================================================
Data source: Optimized Database with Pre-Computed KPIs
Available hospitals: 6021
Dashboard running at: http://localhost:8050
================================================================================

Dash is running on http://127.0.0.1:8050/
```

## Step 4: Open in Browser

Navigate to: **http://localhost:8050**

You should see:
- Hospital dropdown with 6,000+ hospitals
- Two tabs: "KPI Dashboard" and "Financials"
- 17 interactive KPI cards
- Fast loading times (< 100ms per hospital)

## Troubleshooting

### Issue: "Database not found, falling back to parquet files"

**Problem**: The optimized database hasn't been built yet.

**Solution**: Run Step 2 above to build the database.

### Issue: "No module named 'dash'"

**Problem**: Dependencies not installed.

**Solution**: Run `pip install -r requirements.txt`

### Issue: Dashboard loads slowly (5-30 seconds per hospital)

**Problem**: Running without optimized database.

**Solution**: The dashboard works without the database but will be much slower. Build the database for optimal performance.

### Issue: "Error loading balance sheet: No files found"

**Problem**: Parquet files not in expected location.

**Solution**: Verify that `../poc_env/balance_sheet_long/` exists and contains data. You may need to run the ETL scripts first.

## Next Steps

Once the dashboard is running:

1. **Explore KPIs**
   - Select different hospitals
   - Change benchmark levels (National, State, Hospital Type)
   - Click KPI cards to see details
   - View data tables with multi-year trends

2. **Analyze Financials**
   - Switch to "Financials" tab
   - Review Balance Sheet by fund type
   - Examine Revenue details
   - Analyze Costs breakdown

3. **Clean Up (Optional)**
   - Review `FILES_TO_DELETE.md` for cleanup recommendations
   - Archive old development files
   - Free up ~4-5 GB disk space

## Performance Metrics

With optimized database:
- **Hospital selection**: < 100ms
- **KPI calculation**: 0ms (pre-computed)
- **Benchmark lookup**: < 50ms (indexed)
- **Financial statements**: < 200ms

Without database (parquet fallback):
- **Hospital selection**: 5-30 seconds
- **KPI calculation**: 5-15 seconds
- **Benchmark lookup**: 10-60 seconds
- **Financial statements**: 3-10 seconds

**Speedup: 50-300x faster with database!**

## Support

For detailed documentation, see:
- `README.md` - Full documentation
- `FILES_TO_DELETE.md` - Cleanup guide
- Script comments - Technical details
