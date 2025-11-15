# Hospital Analytics Dashboard - Worksheet Version

## Overview

New dashboard implementation that displays CMS HCRIS worksheet data directly from the DuckDB database with a clean, worksheet-focused interface.

**File**: `dashboard_worksheets.py`
**Database**: `data/hospital_worksheets.duckdb`
**URL**: http://localhost:8050

**Date**: 2025-11-08
**Author**: JQ-dev

## Key Features

### ✅ Simplified Design
- **20 worksheet tabs** (one per CMS HCRIS worksheet)
- **Year-by-year views** (select fiscal year per worksheet)
- **Pivot table display** with proper row/column structure
- **Direct database queries** (no ETL on-the-fly)
- **Fast performance** (indexed database queries)

### ✅ Data Display Format

**Rows**:
- Line number + line_level1 + line_level2
- Ordered by Line number (ascending)

**Columns**:
- Column number + col_level1 + col_level2
- Ordered by Column number (ascending)

**Values**:
- Numeric data from worksheet
- Formatted with thousands separator

## Available Worksheets

| Tab | Worksheet | Description |
|-----|-----------|-------------|
| 1 | A000000 | General Service Cost Centers |
| 2 | A700001 | Statistical Data 1 |
| 3 | A700002 | Statistical Data 2 |
| 4 | A700003 | Statistical Data 3 |
| 5 | A800000 | Inpatient Routine Cost Centers |
| 6 | A810000 | Ancillary Service Cost Centers |
| 7 | A820010 | Outpatient Service Cost Centers |
| 8 | B000001 | Balance Sheet |
| 9 | B000002 | Statement of Revenues and Expenses |
| 10 | B100000 | Cost Allocation - Stepdown |
| 11 | C000001 | Allocation Statistics |
| 12 | S000001 | Part A Settlement |
| 13 | S100001 | Part A Provider Statistical/Reimbursement |
| 14 | S200001 | Part A Bad Debts |
| 15 | S300001 | Part B Settlement |
| 16 | S300002 | Part B Statistical/Reimbursement |
| 17 | S300004 | Part B Bad Debts |
| 18 | S300005 | Part B ASC Cost and Payment |
| 19 | S410000 | Home Health Agency (HHA) |
| 20 | S500000 | Hospice |

## How to Use

### 1. Start the Dashboard

```bash
cd "d:\HealthVista Analytics\hospital_dashboard"
python dashboard_worksheets.py
```

Dashboard will be available at: **http://localhost:8050**

### 2. Select a Hospital

- Use the dropdown to select a hospital
- Format: `Provider_Number (State_Code)`
- Example: `310001 (31)` for a New Jersey hospital

### 3. View Hospital Info

After selection, you'll see:
- Provider Number
- State Code
- Fiscal year range
- Number of fiscal years available

### 4. Navigate Worksheets

- Click on any worksheet tab
- Select a fiscal year from the dropdown
- View the pivot table with:
  - Rows: Line descriptions
  - Columns: Column descriptions
  - Values: Numeric data

### 5. Interact with Data

- **Filter**: Use the filter boxes in column headers
- **Sort**: Click column headers to sort
- **Navigate**: Use pagination for large datasets
- **Search**: Type in filter boxes to find specific rows

## Data Structure

### Row Format
```
Line - line_level1 line_level2
```

Example:
```
00100 - GENERAL SERVICE COST CENTERS Capital Related Costs-Buildings and Fixtures
```

### Column Format
```
Column - col_level1 col_level2
```

Example:
```
00100 - SALARIES
00200 - OTHER
00700 - FOR ALLOCATION (col. 5 ± col. 6)
```

### Value Format
- Numbers formatted with thousands separator
- Right-aligned for easy reading
- Scientific notation for very large/small numbers

## Technical Details

### Database Connection
- **Read-only mode**: Safe for multiple users
- **Connection pooling**: Efficient resource usage
- **Automatic cleanup**: Connections closed after queries

### Query Performance
- **Indexed queries**: Fast lookups by Provider_Number, fiscal_year
- **Filtered data**: Only requested worksheet and year loaded
- **Pivot in memory**: Client-side pivot for flexibility

### Data Tables
- **Dash DataTable**: Interactive tables with filtering, sorting
- **Pagination**: 50 rows per page (configurable)
- **Responsive**: Horizontal scroll for wide tables
- **Native filtering**: Type to filter any column

## Differences from Original Dashboard

### Removed Features
- ❌ KPI dashboard (focus on raw data)
- ❌ Benchmark comparisons
- ❌ Multi-year summary tables
- ❌ Pre-computed aggregations
- ❌ Fund balance changes tab
- ❌ Complex filtering options

### New Features
- ✅ All 20 worksheets in one place
- ✅ Direct database access
- ✅ Consistent pivot table format
- ✅ Year-by-year selection
- ✅ Simplified navigation
- ✅ Native table filtering/sorting

## Example Use Cases

### 1. View Balance Sheet
1. Select hospital
2. Click "B000001 - Balance Sheet" tab
3. Select fiscal year
4. View assets, liabilities, equity

### 2. Compare Revenues Year-over-Year
1. Select hospital
2. Click "B000002 - Statement of Revenues and Expenses"
3. Select year 2024, note values
4. Switch to year 2023, compare

### 3. Analyze Cost Centers
1. Select hospital
2. Click "A000000 - General Service Cost Centers"
3. Filter by specific line descriptions
4. Review cost allocations

### 4. Review Settlement Data
1. Select hospital
2. Click "S300001 - Part B Settlement"
3. Select fiscal year
4. Analyze Medicare reimbursements

## Customization

### Change Page Size

In `dashboard_worksheets.py`, find:
```python
page_size=50,
```

Change to desired number (e.g., `100`, `200`)

### Modify Number Format

In `dashboard_worksheets.py`, find:
```python
'format': {'specifier': ',.0f'}
```

Options:
- `',.0f'` - Integer with thousands separator
- `',.2f'` - Two decimal places
- `'$,.2f'` - Currency format
- `'.2%'` - Percentage

### Add More States

Update `STATE_CODES` in ETL scripts:
```python
STATE_CODES = ['31', '34', '05']  # Add California
```

Re-run ETL and rebuild database.

## Performance Optimization

### For Large Datasets
1. Increase pagination size
2. Use filtering to reduce rows
3. Consider pre-aggregating common queries
4. Add more indexes if needed

### For Many Users
1. Deploy with Gunicorn or uWSGI
2. Enable database connection pooling
3. Use caching for static queries
4. Consider read replicas for database

## Troubleshooting

### Dashboard Won't Start
- Check if port 8050 is available
- Verify database file exists
- Check Python dependencies installed

### No Data Showing
- Verify hospital selection
- Check fiscal year selection
- Ensure database has data for that provider/year
- Check browser console for JavaScript errors

### Slow Performance
- Check database indexes
- Reduce number of rows displayed
- Enable filtering before loading
- Check network connection if remote

### Column Headers Too Wide
- Table scrolls horizontally automatically
- Zoom out browser if needed
- Filter to reduce columns shown

## File Structure

```
d:\HealthVista Analytics\hospital_dashboard\
├── dashboard_worksheets.py        # New worksheet-based dashboard
├── dashboard.py                   # Original KPI dashboard
├── data/
│   └── hospital_worksheets.duckdb # Database (172.3 MB)
└── Documentation/
    └── DASHBOARD_WORKSHEETS_GUIDE.md  # This file
```

## Next Steps

### Potential Enhancements
1. Add export to Excel functionality
2. Add multi-year comparison view
3. Add calculated columns (ratios, percentages)
4. Add data visualization (charts, graphs)
5. Add search across all worksheets
6. Add provider comparison mode
7. Add favorites/bookmarks feature
8. Add custom report builder

### Integration Options
1. Connect to Jupyter notebooks for analysis
2. Export API for external tools
3. Automated report generation
4. Email alerts for data updates
5. Integration with BI tools (Tableau, Power BI)

## Support

### Documentation
- [DATABASE_BUILD_COMPLETE.md](DATABASE_BUILD_COMPLETE.md) - Database reference
- [ETL_MULTI_STATE_UPDATE.md](ETL_MULTI_STATE_UPDATE.md) - ETL process
- [WORKSHEET_ETL_BATCH.md](WORKSHEET_ETL_BATCH.md) - Worksheet details

### Database Queries
For custom queries outside dashboard, use:

```python
import duckdb
import pandas as pd

con = duckdb.connect('data/hospital_worksheets.duckdb', read_only=True)

# Your custom query here
df = con.execute('''
    SELECT *
    FROM worksheet_b000001
    WHERE Provider_Number = '310001'
''').df()

con.close()
```

## Version History

### v1.0 (2025-11-08)
- Initial release
- 20 worksheets supported
- 2 states (NJ, NC)
- 5 fiscal years (2020-2024)
- 2.47 million records
- 229 providers

---

**Status**: ✅ Production Ready
**Dashboard URL**: http://localhost:8050
**Database**: 172.3 MB, 20 tables, 80 indexes
**Performance**: < 1 second query time per worksheet
