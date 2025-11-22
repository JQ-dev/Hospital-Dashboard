# Getting Started - Hospital Master Data

## Quick Start Guide

### Problem
Your HCRIS cost report data has CCN codes (Provider Numbers) but no hospital names, addresses, or other identifying information.

### Solution
Download the **CMS Hospital General Information** file which maps all CCN codes to hospital names, addresses, phone numbers, and more.

---

## Step-by-Step Instructions

### Step 1: Download Hospital Reference Data

**Option A: Manual Download (Most Reliable)**

1. **Open your browser** and visit:
   ```
   https://data.cms.gov/provider-data/dataset/xubh-q36u
   ```

2. **Click the "Export" button** in the top right

3. **Select "CSV"** format

4. **Save the file** as `hospital_general_information.csv`

5. **Move the file** to your project:
   ```bash
   mkdir -p data/cms_reference_data
   mv ~/Downloads/Hospital_General_Information*.csv data/cms_reference_data/hospital_general_information.csv
   ```

**Option B: Direct Download with curl**

```bash
# Create directory
mkdir -p data/cms_reference_data

# Download file
curl -L "https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0/download?format=csv" \
  -H "User-Agent: Mozilla/5.0" \
  -o data/cms_reference_data/hospital_general_information.csv
```

**Option C: Use the automated script**

```bash
python scripts/download_cms_reference_data.py --source hospital
```

---

### Step 2: Verify the Downloaded File

```bash
# Check file exists and size
ls -lh data/cms_reference_data/hospital_general_information.csv

# View first few lines
head data/cms_reference_data/hospital_general_information.csv

# Count hospitals
wc -l data/cms_reference_data/hospital_general_information.csv
```

**Expected:**
- File size: ~3-5 MB
- Number of hospitals: ~6,500+ (one per line plus header)
- Columns include: Facility ID, Facility Name, Address, City, State, ZIP Code, etc.

---

### Step 3: Build Hospital Master Data Tables

Now that you have the reference data, build the hospital master tables:

```bash
python etl/build_hospital_master.py
```

**What this does:**
1. Extracts all hospitals from your HCRIS parquet files
2. Creates hospital_master table with CCN, fiscal year data
3. Detects NPI and ownership changes
4. Creates historical tracking tables

**Output:**
- Tables in `hospital_analytics.duckdb`
- CSV exports in `data/hospital_master_exports/`

---

### Step 4: Enrich with CMS Reference Data

The build script will automatically look for and use the CMS reference file if you named it correctly. If not, you can run the integration manually:

```bash
# Update the integrate script to use the Hospital General Information file
python etl/integrate_hospital_general_info.py
```

Or modify `etl/build_hospital_master.py` to load the CSV and join it with your HCRIS data.

---

## What You Get

After completing these steps, you'll have:

### Database Tables

1. **hospital_master** - Complete hospital directory
   - CCN, NPI, hospital name
   - Street address, city, state, zip
   - Hospital type, ownership
   - Phone number
   - System/group affiliation
   - Status (Active/Closed)

2. **hospital_annual_snapshot** - Yearly HCRIS data
   - Links fiscal year to hospital identifiers
   - Tracks what name/NPI was used each year

3. **hospital_identifiers_history** - Change tracking
   - NPI changes
   - Name changes
   - Ownership changes

4. **hospital_addresses_history** - Address tracking
   - Relocations
   - Address corrections

5. **hospital_system_membership** - System affiliations
   - Hospital group memberships
   - Parent organizations

### CSV Exports

Files in `data/hospital_master_exports/`:
- `hospital_master.csv` - Full hospital directory
- `hospital_annual_snapshot.csv` - Yearly records
- `hospital_identifiers_history.csv` - Change log
- `ccn_hospital_mapping.csv` - Simple CCN to name/address lookup

---

## Field Mapping

### From CMS Hospital General Information:

| CMS File Column | Database Column | Description |
|-----------------|----------------|-------------|
| Facility ID | ccn | 6-digit Medicare certification number |
| Facility Name | hospital_name | Official hospital name |
| Address | street_address | Street address |
| City | city | City name |
| State | state_code | 2-letter state code |
| ZIP Code | zip_code | 5-digit ZIP code |
| County Name | county_name | County |
| Phone Number | phone_number | Main phone |
| Hospital Type | hospital_type | Type (Acute Care, Critical Access, etc.) |
| Hospital Ownership | ownership_type | Ownership (Govt, Non-Profit, Proprietary) |

### From Your HCRIS Data:

| HCRIS Field | Database Column | Description |
|-------------|----------------|-------------|
| Provider_Number | ccn | Same as Facility ID |
| NPI | npi | National Provider Identifier |
| Control_Type | ownership_type | Ownership from cost reports |
| Fiscal_Year | first_fiscal_year, last_fiscal_year | Reporting years |
| State_Code | state_code | From CCN first 2 digits |

---

## Using the Hospital Directory

### Query Examples

**Get all hospitals in a state:**
```python
import duckdb
con = duckdb.connect('data/hospital_analytics.duckdb')

nj_hospitals = con.execute("""
    SELECT ccn, hospital_name, city, street_address, phone_number
    FROM hospital_master
    WHERE state_code = '31'  -- New Jersey
      AND status = 'Active'
    ORDER BY city, hospital_name
""").df()
```

**Find a specific hospital:**
```python
hospital = con.execute("""
    SELECT *
    FROM hospital_master
    WHERE ccn = '310001'
       OR hospital_name LIKE '%Memorial%'
""").df()
```

**Track hospital name changes:**
```python
changes = con.execute("""
    SELECT
        h.ccn,
        s.fiscal_year,
        s.hospital_name,
        h.hospital_name as current_name
    FROM hospital_annual_snapshot s
    JOIN hospital_master h ON s.ccn = h.ccn
    WHERE s.ccn = '310001'
    ORDER BY s.fiscal_year
""").df()
```

---

## Dashboard Access

Once built, access the Hospital Directory at:

```
http://localhost:8050/hospital-master
```

**Features:**
- Search by name, city, CCN, NPI
- Filter by state, type, status
- Export filtered results to CSV
- View data quality scores
- See hospital counts and statistics

---

## Troubleshooting

### Issue: "Download failed" or 403 error

**Solution:** Use the manual download method via your web browser:
1. Visit https://data.cms.gov/provider-data/dataset/xubh-q36u
2. Click Export → CSV
3. Save file and move to `data/cms_reference_data/`

### Issue: "No parquet files found"

**Solution:** Run the HCRIS ETL pipeline first:
```bash
# Create parquet files from HCRIS source data
python etl/create_all_worksheets.py
# Or whichever ETL script you use for initial data loading
```

### Issue: "CCN not found in reference data"

**Causes:**
1. Hospital not Medicare-certified
2. Hospital closed before CMS data snapshot
3. CCN formatting issue (needs leading zeros)

**Check:**
```python
# Ensure CCN is 6 digits with leading zeros
ccn = str(provider_num).zfill(6)
```

### Issue: "Hospital name is NULL"

**Cause:** CMS reference file not loaded or didn't match on CCN

**Solution:**
1. Verify file downloaded correctly
2. Check CCN formatting in both files
3. Run integration script again

---

## Data Updates

### Monthly: CMS Reference Data
The Hospital General Information file is updated monthly.

**To refresh:**
1. Download new file from CMS
2. Replace `hospital_general_information.csv`
3. Re-run integration script

### Annual: HCRIS Data
When new fiscal year data is available:

```bash
# Add new HCRIS data via your ETL pipeline
python etl/create_all_worksheets.py

# Rebuild hospital master tables
python etl/build_hospital_master.py
```

---

## Next Steps

### 1. Add Hospital System/Group Data

Hospital system affiliations aren't in the free CMS data. Options:

**Option A: AHA Annual Survey (Requires License)**
- Comprehensive system membership data
- Requires purchasing AHA database license

**Option B: Manual Curation**
- Identify major systems in your market
- Manually populate `hospital_system_membership` table
- Use web research to find affiliations

**Option C: Parse Hospital Names**
- Many hospitals include system name in official name
- "XYZ Hospital - Trinity Health"
- Can extract programmatically

### 2. Add Historical Name Tracking

Download quarterly POS files over time to track:
- Name changes with exact dates
- Mergers and acquisitions
- Address changes
- Ownership changes

### 3. Integrate NPI Registry (Advanced)

For Type 2 (organizational) NPIs:

```bash
# Download NPPES data (7GB!)
curl -o npi_data.zip https://download.cms.gov/nppes/NPPES_Data_Dissemination_January_2025.zip

# Extract and parse
# Match hospitals by name and address
# Add NPI where missing
```

---

## Summary

✅ **Download CMS Hospital General Information file** (the easy way is manual download from website)

✅ **Save to** `data/cms_reference_data/hospital_general_information.csv`

✅ **Run** `python etl/build_hospital_master.py`

✅ **Access dashboard** at `/hospital-master`

✅ **Now you have** complete hospital directory with CCN → Name → Address → Phone mapping!

---

## Support Resources

**Documentation:**
- `docs/CMS_DATA_SOURCES.md` - Detailed data source information
- `docs/HOSPITAL_MASTER_DATA_README.md` - Complete system documentation
- `docs/hospital_master_data_schema.md` - Database schema reference

**Scripts:**
- `scripts/download_cms_reference_data.py` - Automated download
- `etl/build_hospital_master.py` - Build master tables
- `pages/hospital_master_page.py` - Dashboard UI

**CMS Resources:**
- [Hospital Data Portal](https://data.cms.gov/provider-data/topics/hospitals)
- [Provider of Services](https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/Provider-of-Services)
- [CCN Lookup Tool](https://www.qualityreportingcenter.com/en/inpatient-quality-reporting-programs/CCNLookup/)
