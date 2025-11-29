# Data Verification Dashboard - Quick Start Guide

## 🚀 Quick Start

### Start the Dashboard
```bash
# Option 1: Using batch file (Windows)
run_verification.bat

# Option 2: Direct Python command
python data_verification_dashboard.py
```

**Access at**: http://localhost:8051

---

## 📊 Dashboard Views

### 1. Hospital × Table Matrix
**Purpose**: Check which hospitals have data in a specific table

**How to Use**:
1. Select database type (Main Analytics or Worksheet)
2. Pick a table from dropdown
3. View color-coded results:
   - 🟢 Green = Full data (100+ records)
   - 🟡 Yellow = Partial (10-99 records)
   - 🟠 Orange = Minimal (1-9 records)
   - 🔴 Red = No data (0 records)

**Example Use Case**:
*"Check if CCN 310001 has data in the hospital_kpis table"*

![Hospital Table Matrix View]
```
CCN      | First Year | Last Year | Years | Records | Status
---------|------------|-----------|-------|---------|--------
310001   | 2020       | 2024      | 5     | 342     | full (green)
310002   | 2020       | 2024      | 5     | 0       | none (red)
310003   | 2021       | 2024      | 4     | 156     | full (green)
```

---

### 2. Table × Year Matrix
**Purpose**: Visualize data coverage across years for multiple hospitals

**How to Use**:
1. Select database and table
2. View heatmap showing record counts by year
3. Identify missing years (lighter colors or zeros)

**Example Use Case**:
*"Which hospitals are missing 2022 data in the balance_sheet table?"*

![Table Year Heatmap]
```
         | 2020 | 2021 | 2022 | 2023 | 2024
---------|------|------|------|------|------
310001   | 342  | 356  |  0   | 378  | 401  ← Missing 2022!
310002   | 289  | 301  | 315  | 328  | 342
310003   | 156  | 168  | 172  | 185  | 199
```

---

### 3. Summary Statistics
**Purpose**: High-level overview of data availability

**Shows**:
- Total hospitals in database
- Number of tables in Main DB
- Number of tables in Worksheet DB
- Complete list of available tables

---

## 🎯 Common Verification Tasks

### Task 1: Verify KPI Data for a Hospital
```
1. Go to "Hospital × Table Matrix"
2. Select "Main Analytics DB"
3. Select table: "hospital_kpis"
4. Find your hospital CCN in the table
5. Check Status column (should be green/yellow)
```

### Task 2: Check Worksheet Coverage
```
1. Go to "Hospital × Table Matrix"
2. Select "Worksheet DB"
3. Select table: "worksheet_g300000" (Income Statement)
4. Verify hospitals have data (green status)
```

### Task 3: Find Missing Years
```
1. Go to "Table × Year Matrix"
2. Select table with temporal data
3. Look for:
   - Light colored cells = few records
   - Zero values = missing data
   - Gaps in the timeline
```

### Task 4: Validate ETL Pipeline
```
After running ETL:
1. Go to "Summary Statistics"
2. Check table counts match expectations
3. Go to "Hospital × Table Matrix"
4. Verify new data loaded (green status)
5. Check record counts increased
```

---

## 🔍 Interpreting Results

### Status Colors Explained

| Color | Status | Records | Meaning |
|-------|--------|---------|---------|
| 🟢 Green | Full | 100+ | Complete dataset, ready for analysis |
| 🟡 Yellow | Partial | 10-99 | Some data available, may be incomplete |
| 🟠 Orange | Minimal | 1-9 | Very limited data, likely unusable |
| 🔴 Red | None | 0 | No data available |

### When to Be Concerned

**🚨 Red Flags**:
- Hospital has Red status in `hospital_kpis` → KPIs won't calculate
- All hospitals show Red for a table → ETL may have failed
- Missing consecutive years → Data pipeline interrupted

**⚠️ Yellow Flags**:
- Yellow/Orange in worksheet tables → Level 2/3 KPIs may fail
- Decreasing record counts over time → Data quality issue
- Partial data for recent years → ETL incomplete

**✅ Green Lights**:
- Green status across all critical tables
- Consistent record counts across years
- All worksheets populated

---

## 📋 Verification Checklist

### Pre-Analysis Verification
- [ ] Main database exists at `data/hospital_analytics.duckdb`
- [ ] Worksheet database exists at `data/hospital_worksheets.duckdb`
- [ ] Target hospital has data in `hospital_kpis` (green)
- [ ] Target hospital has data in `balance_sheet` (green)
- [ ] All required fiscal years present

### Post-ETL Verification
- [ ] Record counts increased in source tables
- [ ] New fiscal year data appears in year matrix
- [ ] No new Red statuses appeared
- [ ] Benchmark tables updated

### KPI Troubleshooting
If KPI shows "N/A":
- [ ] Check hospital has data in `hospital_kpis` table
- [ ] Verify worksheet tables have data (for L2/L3 KPIs)
- [ ] Check fiscal year exists in time series
- [ ] Review calculation logic in `data_manager.py`

---

## 🛠️ Configuration

### Show More Hospitals
Default limit is 50 hospitals. To show more:

Edit `data_verification_dashboard.py`:
```python
# Line ~334 and ~488
hospitals_subset = hospitals_data[:100]  # Change from 50 to 100
```

### Change Status Thresholds
Edit `data_verification_dashboard.py`:
```python
# In check_table_data_for_hospital() function
if record_count < 5:      # Minimal threshold (default: 10)
    status = 'minimal'
elif record_count < 50:   # Partial threshold (default: 100)
    status = 'partial'
else:
    status = 'full'
```

### Use Different Port
```python
# Last line of data_verification_dashboard.py
app.run_server(debug=True, port=8052, host='0.0.0.0')  # Change from 8051
```

---

## 🐛 Troubleshooting

### Problem: "Database not available"
**Solution**: Check database files exist:
```bash
ls data/hospital_analytics.duckdb
ls data/hospital_worksheets.duckdb
```

### Problem: Port 8051 already in use
**Solution**: Kill the process or change port:
```bash
# Windows
netstat -ano | findstr :8051
taskkill /PID <process_id> /F

# Or change port in code (see Configuration section)
```

### Problem: No data showing for any table
**Solution**: Verify database connection:
```python
import duckdb
con = duckdb.connect('data/hospital_analytics.duckdb', read_only=True)
print(con.execute("SHOW TABLES").df())
con.close()
```

### Problem: Dashboard slow to load
**Solution**: Reduce hospital limit (see Configuration)

---

## 📚 Related Resources

- **[DATA_VERIFICATION_README.md](DATA_VERIFICATION_README.md)** - Full technical documentation
- **[COMPREHENSIVE_CODE_AND_KPI_DOCUMENTATION.md](COMPREHENSIVE_CODE_AND_KPI_DOCUMENTATION.md)** - KPI formulas and code
- **[DATA_STRUCTURE_FOR_ANALYSTS.md](DATA_STRUCTURE_FOR_ANALYSTS.md)** - Database schema

---

## 💡 Pro Tips

1. **Start with Summary** → Get overview before diving into details
2. **Use Filters** → Both tables support native filtering and sorting
3. **Check Year Gaps** → Use heatmap to quickly spot missing years
4. **Bookmark Common Checks** → Save URLs with selected tables
5. **Run in Parallel** → Keep both dashboards open (ports 8050 and 8051)

---

## 📞 Support

**Issue**: KPI shows "N/A" in main dashboard
**Steps**:
1. Open verification dashboard (port 8051)
2. Check if hospital has data in required tables
3. Review [COMPREHENSIVE_CODE_AND_KPI_DOCUMENTATION.md](COMPREHENSIVE_CODE_AND_KPI_DOCUMENTATION.md) for formula
4. Verify worksheet tables if Level 2/3 KPI

**Still stuck?** Check:
- ETL pipeline logs
- Database build scripts output
- KPI calculation code in `data/data_manager.py`

---

**Version**: 1.0
**Dashboard Port**: 8051
**Main Dashboard Port**: 8050
**Last Updated**: 2025-11-24
