# Data Verification Dashboard

Independent dashboard to verify data availability across hospitals, tables, and years.

## Features

### 1. **Hospital × Table Matrix**
- Select a database (Main Analytics or Worksheet)
- Select a table
- View color-coded data availability for each hospital
- Status indicators:
  - 🟢 **Green (Full)**: 100+ records
  - 🟡 **Yellow (Partial)**: 10-99 records
  - 🟠 **Orange (Minimal)**: 1-9 records
  - 🔴 **Red (None)**: 0 records

### 2. **Table × Year Matrix**
- Select a database and table
- View heatmap showing record counts by hospital and year
- Quickly identify missing years or incomplete data
- Interactive hover shows exact record counts

### 3. **Summary Statistics**
- Total hospitals count
- Number of tables in each database
- Complete list of available tables

## Running the Dashboard

### Start the Dashboard

```bash
# From the hospital_dashboard directory
python data_verification_dashboard.py
```

The dashboard will start on **port 8051**: http://localhost:8051

**Note**: This runs independently from the main dashboard (which runs on port 8050)

### Run Both Dashboards Simultaneously

Terminal 1 - Main Dashboard:
```bash
python dashboard.py
# Runs on http://localhost:8050
```

Terminal 2 - Verification Dashboard:
```bash
python data_verification_dashboard.py
# Runs on http://localhost:8051
```

## Database Connections

The dashboard connects to:
1. **Main Analytics Database**: `data/hospital_analytics.duckdb`
   - Pre-computed KPI tables
   - Financial statement tables
   - Benchmark tables

2. **Worksheet Database**: `data/hospital_worksheets.duckdb`
   - Raw HCRIS worksheet data
   - Used for Level 2 and Level 3 KPI calculations

## Usage Examples

### Example 1: Verify KPI Data Availability
1. Go to "Hospital × Table Matrix" tab
2. Select "Main Analytics DB"
3. Select table: `hospital_kpis`
4. View which hospitals have complete KPI data

### Example 2: Check Worksheet Coverage
1. Go to "Hospital × Table Matrix" tab
2. Select "Worksheet DB"
3. Select table: `worksheet_s300001` (Statistical Data)
4. Verify which hospitals have S-3 worksheet data

### Example 3: Identify Missing Years
1. Go to "Table × Year Matrix" tab
2. Select a table (e.g., `balance_sheet`)
3. View heatmap to identify hospitals with gaps in yearly data
4. Red cells = missing data for that year

## Interpreting the Results

### Hospital × Table Matrix

The table shows:
- **CCN**: Hospital provider number
- **First Year**: Earliest fiscal year with data
- **Last Year**: Most recent fiscal year with data
- **Years**: Number of years with data
- **Records in Table**: Number of records in selected table
- **Table Years**: Number of years with data in selected table
- **Status**: Color-coded availability status

### Table × Year Matrix

The heatmap shows:
- **Rows**: Hospital CCNs
- **Columns**: Fiscal years
- **Cell Color**: Record count (darker = more records)
- **Cell Text**: Exact record count

## Performance Notes

- **Hospital Limit**: Shows first 50 hospitals for performance
- **Full dataset**: Modify `hospitals_subset = hospitals_data[:50]` to show more
- **Large tables**: May take longer to load (e.g., worksheet tables with millions of records)

## Troubleshooting

### Database Not Found
If you see "Database not available":
1. Check that databases exist at:
   - `data/hospital_analytics.duckdb`
   - `data/hospital_worksheets.duckdb`
2. Run database build scripts if needed:
   ```bash
   python scripts/build_database.py
   python scripts/build_worksheet_database.py  # if exists
   ```

### Table Not Showing Data
If a table shows all red (no data):
1. Verify table has `Provider_Number` column
2. Check if table is empty: `SELECT COUNT(*) FROM table_name`
3. Verify CCN format (should be 6-digit string)

### Port Already in Use
If port 8051 is busy:
1. Change port in `data_verification_dashboard.py`:
   ```python
   app.run_server(debug=True, port=8052, host='0.0.0.0')
   ```
2. Or stop the process using port 8051

## Code Structure

```python
# Main components:
- get_database_connection()      # Connect to databases
- get_available_tables()         # List all tables
- get_hospitals_list()           # Get hospital metadata
- check_table_data_for_hospital() # Check data for specific hospital
- check_table_data_by_year()     # Get data by year

# Three main views:
- render_hospital_table_matrix()  # Hospital × Table view
- render_table_year_matrix()      # Table × Year heatmap
- render_summary_stats()          # Overall statistics
```

## Customization

### Change Hospital Limit
```python
# In render_hospital_table_matrix() and update_table_year_matrix()
hospitals_subset = hospitals_data[:100]  # Show first 100 instead of 50
```

### Adjust Status Thresholds
```python
# In check_table_data_for_hospital()
if record_count < 5:      # Change from 10
    status = 'minimal'
elif record_count < 50:   # Change from 100
    status = 'partial'
```

### Change Color Scheme
```python
COLORS = {
    'full': '#your_color',
    'partial': '#your_color',
    'minimal': '#your_color',
    'none': '#your_color'
}
```

## Use Cases

1. **Data Quality Assurance**
   - Verify all hospitals have required tables
   - Identify hospitals with incomplete data
   - Check for missing years

2. **ETL Validation**
   - Verify data loaded correctly after ETL pipeline
   - Check record counts match expectations
   - Identify failed or partial loads

3. **Database Monitoring**
   - Monitor data growth over time
   - Identify tables that need maintenance
   - Verify data consistency across databases

4. **Troubleshooting**
   - Debug why specific KPIs show "N/A"
   - Verify worksheet data exists for calculations
   - Check data availability before running analysis

## Next Steps

After verifying data availability:
1. If data is missing, check ETL logs
2. If data exists but KPIs show N/A, check calculation logic in `data_manager.py`
3. Use the main dashboard to view actual KPI values
4. Consult `COMPREHENSIVE_CODE_AND_KPI_DOCUMENTATION.md` for formula details

## Related Documentation

- [COMPREHENSIVE_CODE_AND_KPI_DOCUMENTATION.md](COMPREHENSIVE_CODE_AND_KPI_DOCUMENTATION.md) - Full system documentation
- [DATA_STRUCTURE_FOR_ANALYSTS.md](DATA_STRUCTURE_FOR_ANALYSTS.md) - Database structure guide
- [README.md](README.md) - Main dashboard documentation

---

**Version**: 1.0
**Last Updated**: 2025-11-24
**Port**: 8051
**Main Dashboard Port**: 8050
