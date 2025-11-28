# Hospital Master Data - Comprehensive Hospital Directory

## Overview

The Hospital Master Data system provides a comprehensive hospital directory with:

- **CCN Codes** (CMS Certification Numbers)
- **Hospital Names** (with historical name changes)
- **NPIs** (National Provider Identifiers) associated with each CCN
- **Complete Addresses** (street, city, state, zip code)
- **Hospital Groups/Systems** (if hospital belongs to a system)
- **Historical Tracking** of changes in names, codes, and identifiers
- **Annual Snapshots** from HCRIS fiscal year data
- **Data Quality Scoring** for completeness assessment

This enables your application to:
- Combine hospitals when they change names
- Track hospital mergers and acquisitions
- Link CCN codes to NPIs and addresses
- Identify hospitals that have closed or changed ownership

## Data Sources

### 1. CMS HCRIS (Hospital Cost Report Information System)
**Already integrated in your application**
- Provider Number (CCN)
- NPI
- Control Type (ownership)
- Fiscal year dates
- Report status
- 5 years of data (FY 2020-2024)

### 2. CMS Provider of Services (POS) File
**Requires download - see setup instructions below**
- Hospital names
- Full addresses
- Phone numbers
- Certification dates
- Bed counts
- Provider category codes
- Updated quarterly by CMS

**Download from:** [CMS POS File](https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-non-hospital-facilities)

### 3. Hospital Systems/Groups (Optional)
**Future enhancement**
- System affiliations typically from AHA Annual Survey (proprietary)
- Or can be manually curated for key systems

## Database Schema

### Core Tables

#### 1. `hospital_master`
Primary reference table with current hospital information
- CCN (primary key)
- NPI, hospital name
- Address, city, state, zip
- Hospital type, ownership
- System/group affiliation
- Operational status
- Data quality score

#### 2. `hospital_annual_snapshot`
Annual data from HCRIS for each hospital-year
- Links to fiscal year financial data
- Tracks identifiers used in each year
- Enables time-series analysis

#### 3. `hospital_identifiers_history`
Tracks all changes to identifiers
- NPI changes
- Name changes
- Ownership changes
- CCN mergers/consolidations

#### 4. `hospital_addresses_history`
Tracks address changes over time
- Relocations
- Address corrections
- Effective dates

#### 5. `hospital_system_membership`
Tracks hospital system affiliations
- Current membership
- Historical membership
- System name and type

See [hospital_master_data_schema.md](hospital_master_data_schema.md) for complete schema documentation.

## Setup Instructions

### Step 1: Build Hospital Master Tables from HCRIS Data

This extracts hospital information from your existing HCRIS parquet files and creates the hospital master data tables.

```bash
# Run from project root
python etl/build_hospital_master.py
```

**What this does:**
- Extracts all unique hospitals from HCRIS data (FY 2020-2024)
- Creates `hospital_master` table with ~6,000+ hospitals
- Creates `hospital_annual_snapshot` with yearly records
- Detects NPI and ownership changes
- Populates `hospital_identifiers_history`
- Calculates data quality scores
- Exports CSV files to `data/hospital_master_exports/`

**Note:** This only includes data from HCRIS. Hospital names and addresses will be NULL until you complete Step 2.

### Step 2: Integrate CMS Provider of Services (POS) Data

This enriches the hospital master table with names, addresses, and other demographic information.

#### Option A: Auto-download (Recommended)
```bash
python etl/integrate_pos_data.py --download
```

#### Option B: Manual download
1. Visit: https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-non-hospital-facilities
2. Click "Export" and download CSV
3. Save to `data/pos_files/`
4. Run:
```bash
python etl/integrate_pos_data.py --file data/pos_files/your_downloaded_file.csv
```

**What this does:**
- Downloads latest quarterly POS file from CMS
- Maps POS columns to hospital_master schema
- Updates existing hospitals with names and addresses
- Adds any new hospitals not in HCRIS data
- Recalculates data quality scores (will improve significantly)
- Exports updated `hospital_master_with_pos.csv`

### Step 3: Access Hospital Directory in Dashboard

After building the tables, access the Hospital Master Directory page in your dashboard:

**URL:** `http://localhost:8050/hospital-master`

**Features:**
- Search by hospital name, city, CCN, or NPI
- Filter by state, hospital type, status
- View all hospital demographics in one table
- Export filtered results to CSV
- See data quality scores

## Usage Examples

### Query Hospital Master Data

```python
import duckdb
import pandas as pd

con = duckdb.connect('data/hospital_analytics.duckdb')

# Get all active hospitals in New Jersey
nj_hospitals = con.execute("""
    SELECT ccn, hospital_name, city, npi, total_beds
    FROM hospital_master
    WHERE state_code = '31' AND status = 'Active'
    ORDER BY city, hospital_name
""").df()

# Find a hospital by CCN
hospital = con.execute("""
    SELECT *
    FROM hospital_master
    WHERE ccn = '310001'
""").df()

# Get hospitals that changed ownership
ownership_changes = con.execute("""
    SELECT h.ccn, h.hospital_name, h.city, h.state_code,
           ih.old_value as old_ownership,
           ih.new_value as new_ownership,
           ih.change_date
    FROM hospital_master h
    JOIN hospital_identifiers_history ih ON h.ccn = ih.ccn
    WHERE ih.change_type = 'OWNERSHIP_CHANGE'
    ORDER BY ih.change_date DESC
""").df()

# Get hospitals with NPI changes
npi_changes = con.execute("""
    SELECT h.ccn, h.hospital_name,
           ih.fiscal_year,
           ih.old_value as old_npi,
           ih.new_value as new_npi
    FROM hospital_master h
    JOIN hospital_identifiers_history ih ON h.ccn = ih.ccn
    WHERE ih.change_type = 'NPI_CHANGE'
    ORDER BY h.ccn, ih.fiscal_year
""").df()

con.close()
```

### Combine Hospital Data When Names Change

```python
# Example: Hospital changed name in FY 2022
# Old name: "Memorial Hospital"
# New name: "Memorial Regional Medical Center"

# Get all fiscal year data for this hospital
con = duckdb.connect('data/hospital_analytics.duckdb')

hospital_timeline = con.execute("""
    SELECT
        s.fiscal_year,
        s.ccn,
        s.hospital_name,  -- Name used in that year
        s.npi,
        k.total_revenue,
        k.operating_margin_pct
    FROM hospital_annual_snapshot s
    LEFT JOIN hospital_kpis k ON s.ccn = k.Provider_Number AND s.fiscal_year = k.Fiscal_Year
    WHERE s.ccn = '310001'
    ORDER BY s.fiscal_year
""").df()

# This will show the hospital under both names across years
# but with the same CCN, allowing you to combine the data
```

### Find Hospital System Hospitals (Future)

Once hospital system data is integrated:

```python
# Get all hospitals in a system
system_hospitals = con.execute("""
    SELECT h.ccn, h.hospital_name, h.city, h.state_code, h.total_beds
    FROM hospital_master h
    WHERE h.hospital_system_name = 'Trinity Health'
    ORDER BY h.state_code, h.city
""").df()

# Get system membership history
membership_history = con.execute("""
    SELECT
        h.ccn,
        h.hospital_name,
        m.hospital_system_name,
        m.membership_start_date,
        m.membership_end_date,
        m.is_current
    FROM hospital_master h
    JOIN hospital_system_membership m ON h.ccn = m.ccn
    WHERE h.ccn = '310001'
    ORDER BY m.membership_start_date DESC
""").df()
```

## Data Quality

### Quality Score Calculation

Each hospital gets a data quality score (0-100) based on:

**Base Score (50 points):**
- CCN exists (always true)

**Additional Points:**
- Hospital name: +15 points
- NPI: +5 points
- Street address: +5 points
- City: +5 points
- State: +5 points
- Zip code: +5 points
- Phone number: +3 points
- Hospital type: +5 points
- Ownership type: +3 points
- Certification date: +2 points
- Bed count: +2 points

**Quality Categories:**
- Excellent: 80-100 (all key fields populated)
- Good: 60-79 (most fields populated)
- Fair: 40-59 (basic fields populated)
- Poor: <40 (minimal data)

### Improving Data Quality

**After HCRIS only (Step 1):**
- Average score: ~55-60
- Has CCN, NPI, state, type, ownership
- Missing names, addresses

**After POS integration (Step 2):**
- Average score: ~85-90
- Has names, addresses, phone, beds, certification dates
- Significantly improved

**Future enhancements:**
- Hospital system data: Additional +5 points
- Historical POS files: Better change tracking

## File Locations

### ETL Scripts
- `etl/build_hospital_master.py` - Build tables from HCRIS
- `etl/integrate_pos_data.py` - Integrate POS data

### Documentation
- `docs/hospital_master_data_schema.md` - Complete schema documentation
- `docs/HOSPITAL_MASTER_DATA_README.md` - This file

### UI Components
- `pages/hospital_master_page.py` - Hospital directory page

### Database
- `data/hospital_analytics.duckdb` - Main database file
  - Tables: hospital_master, hospital_annual_snapshot, hospital_identifiers_history, etc.

### Exports
- `data/hospital_master_exports/` - CSV exports
  - `hospital_master.csv` - After Step 1
  - `hospital_master_with_pos.csv` - After Step 2
  - `hospital_annual_snapshot.csv`
  - `hospital_identifiers_history.csv`

### Downloaded Data
- `data/pos_files/` - CMS POS files (created by Step 2)

## Maintenance

### Quarterly Updates

The CMS POS file is updated quarterly. To refresh with latest data:

```bash
# Download and integrate latest POS file
python etl/integrate_pos_data.py --download

# This will:
# - Download current quarter's POS file
# - Update hospital names/addresses if changed
# - Add any newly certified hospitals
# - Mark terminated hospitals
```

### Annual Updates

When new HCRIS fiscal year data is loaded:

```bash
# Rebuild annual snapshots
python etl/build_hospital_master.py

# This will:
# - Add new fiscal year snapshots
# - Detect new identifier changes
# - Update hospital status based on latest year
```

## Troubleshooting

### "No hospital_master table found"

**Solution:** Run Step 1 to build the tables:
```bash
python etl/build_hospital_master.py
```

### "Balance sheet parquet files not found"

**Cause:** HCRIS parquet files haven't been created yet

**Solution:** Run the ETL pipeline first to create parquet files from HCRIS source data:
```bash
# Check ETL documentation for your specific setup
python etl/create_all_worksheets.py  # or similar
```

### "POS file download failed"

**Solution:** Download manually:
1. Visit CMS data portal
2. Download CSV
3. Use `--file` option:
```bash
python etl/integrate_pos_data.py --file /path/to/downloaded/file.csv
```

### "Column mapping failed" for POS file

**Cause:** CMS changed column names in POS file

**Solution:**
1. Check the analysis output showing actual column names
2. Update column mapping logic in `etl/integrate_pos_data.py`
3. Look for the `map_pos_columns()` function
4. Add new column name variants

## Next Steps

### Recommended Enhancements

1. **Hospital System Data**
   - Source AHA Annual Survey data (requires license)
   - Or manually curate major systems
   - Populate `hospital_system_membership` table

2. **Historical POS Files**
   - Download quarterly POS files from data.cms.gov archive
   - Track name and address changes over time
   - Improve historical accuracy

3. **Merger Detection**
   - Analyze patterns in CCN terminations
   - Link related hospitals in mergers
   - Populate `related_ccn` in history table

4. **NPI Registry Integration**
   - Download NPPES NPI registry
   - Cross-reference NPIs
   - Add organization names from Type 2 NPIs

5. **Dashboard Enhancements**
   - Add hospital detail modal with full information
   - Show change history for selected hospital
   - Map view of hospitals by location
   - System/network visualization

## Questions?

See the complete schema documentation in `hospital_master_data_schema.md` for:
- Detailed table structures
- All column definitions
- Index strategies
- Foreign key relationships
- Data population phases

## Data Sources & Citations

- **CMS HCRIS:** Hospital Cost Report Information System
  - Source: https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/Cost-Reports

- **CMS Provider of Services:** Provider characteristics data
  - Source: https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-non-hospital-facilities
  - Updated: Quarterly

- **NPPES NPI Registry:** National Provider Identifier data (future)
  - Source: https://download.cms.gov/nppes/

All data is publicly available from CMS (Centers for Medicare & Medicaid Services).
