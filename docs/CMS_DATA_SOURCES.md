# CMS Hospital Data Sources - Quick Reference

## Available Public Data Files with CCN, Names, and Addresses

### 1. ⭐ Hospital General Information (RECOMMENDED - Primary Source)

**Best for:** Complete hospital directory with CCN, names, addresses

**What it contains:**
- Facility ID (CCN) - 6-digit Medicare certification number
- Facility Name - Official hospital name
- Address, City, State, ZIP Code
- County Name
- Phone Number
- Hospital Type (Acute Care, Critical Access, etc.)
- Hospital Ownership (Government, Voluntary Non-Profit, Proprietary)
- Emergency Services (Yes/No)
- Hospital overall rating (1-5 stars)
- Meets EHR meaningful use criteria

**Update Frequency:** Monthly

**Format:** CSV (direct download)

**Download Methods:**

**Option A: Direct API Download (Recommended)**
```bash
# Direct CSV download link
curl -o hospital_general_information.csv \
  "https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0/download?format=csv"
```

**Option B: Automated Script**
```bash
python scripts/download_cms_reference_data.py --source hospital
```

**Option C: Manual Download**
1. Visit: https://data.cms.gov/provider-data/dataset/xubh-q36u
2. Click "Export" button
3. Select "CSV" format
4. Save file

**File Size:** ~3-5 MB (approximately 6,500+ hospitals)

**Key Fields:**
```
Facility ID                -> Use as CCN
Facility Name              -> Hospital name
Address                    -> Street address
City                       -> City
State                      -> State code (2 letters)
ZIP Code                   -> 5-digit zip
County Name                -> County
Phone Number               -> Main phone
Hospital Type              -> Type classification
Hospital Ownership         -> Ownership type
Hospital overall rating    -> CMS rating (1-5 stars)
```

**Data Source:** [CMS Hospital General Information Dataset](https://data.cms.gov/provider-data/dataset/xubh-q36u)

---

### 2. Provider of Services (POS) File

**Best for:** Detailed provider characteristics, certification dates, more comprehensive data

**What it contains:**
- Provider Number (CCN)
- Provider Name
- Address, City, State, ZIP
- Certification Date
- Termination Date (if applicable)
- Provider Type Code
- Provider Category Code
- Bed Count
- Accreditation information
- Ownership details
- Many additional administrative fields

**Update Frequency:** Quarterly

**Format:** ZIP file containing TXT and/or CSV files

**Download Methods:**

**Option A: Official CMS Page**
1. Visit: https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/Provider-of-Services
2. Look for "Current Files" section
3. Download "HOSPITAL_Provider" file (ZIP format)
4. Extract the files

**Option B: Data.CMS.gov Portal**
1. Visit: https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-non-hospital-facilities
2. Click "Export" or download link
3. May require navigating through the interface

**File Size:** Larger than Hospital General Info (~20-50 MB compressed)

**Note:** POS file has more fields but can be harder to work with. Hospital General Information is usually sufficient for most needs.

**Data Sources:**
- [CMS POS Current Files](https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/Provider-of-Services)
- [Data.CMS.gov POS Portal](https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-non-hospital-facilities)

---

### 3. NPPES NPI Registry (For NPI Data)

**Best for:** NPI to organization name mapping, practice locations

**What it contains:**
- NPI (National Provider Identifier)
- Entity Type (Individual vs Organization)
- Provider Organization Name
- Provider First Name, Last Name (for individuals)
- Mailing Address and Practice Location Address
- Taxonomy Code (specialty)
- Enumeration Date

**Update Frequency:** Monthly (full file), Weekly (updates only)

**Format:** CSV (very large file, ~7 GB uncompressed)

**Download:**
1. Visit: https://download.cms.gov/nppes/NPI_Files.html
2. Download "NPPES Data Dissemination" full replacement file or weekly updates
3. File is very large (several GB)

**Important Note about NPI-CCN Linking:**
- CMS stopped providing CCN in the NPPES file in 2018
- Historical NPI-CCN crosswalk available from NBER (2017 data): https://www.nber.org/research/data/national-provider-identifier-npi-medicare-ccn-crosswalk
- For current NPI-CCN linking, you'll need to match by hospital name/address

**Data Source:** [NPPES NPI Files](https://download.cms.gov/nppes/NPI_Files.html)

---

## Quick Comparison

| Feature | Hospital General Info | POS File | NPPES NPI |
|---------|----------------------|----------|-----------|
| Has CCN | ✅ Yes (Facility ID) | ✅ Yes (Provider Number) | ❌ No (since 2018) |
| Has Hospital Name | ✅ Yes | ✅ Yes | ✅ Yes (Org Name) |
| Has Address | ✅ Yes | ✅ Yes | ✅ Yes |
| Has NPI | ❌ No | Sometimes | ✅ Yes (primary ID) |
| File Size | Small (~5 MB) | Medium (~50 MB) | Very Large (~7 GB) |
| Update Frequency | Monthly | Quarterly | Monthly |
| Ease of Use | ⭐⭐⭐⭐⭐ Easy | ⭐⭐⭐ Moderate | ⭐⭐ Complex |
| **Recommended** | **✅ PRIMARY** | ✅ Optional | ⚠️ Advanced |

---

## Recommended Workflow

### For Your Hospital Dashboard Application:

**Step 1: Download Hospital General Information (PRIMARY)**
```bash
# Use the automated script
python scripts/download_cms_reference_data.py --source hospital

# Or download directly
curl -o data/cms_reference_data/hospital_general_information.csv \
  "https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0/download?format=csv"
```

**Step 2: Use the CCN Mapping**
The script creates `ccn_hospital_mapping.csv` with clean CCN to name/address mappings.

**Step 3: Build Hospital Master Tables**
```bash
python etl/build_hospital_master.py
```

This will automatically use the CMS reference data if available.

**Step 4 (Optional): Download POS for Additional Details**
If you need certification dates, bed counts, or more detailed provider information:
```bash
python scripts/download_cms_reference_data.py --source pos
```

---

## Data Coverage

### What CCNs are Included?

- **Hospital General Information**: All Medicare-certified hospitals (~6,500+)
- **Your HCRIS Data**: All hospitals that submit cost reports (~6,200+)
- **Overlap**: ~95%+ of HCRIS hospitals are in the Hospital General Information file

### Why Some Hospitals May Not Match:

1. **New hospitals**: May be in CMS reference but haven't submitted cost reports yet
2. **Closed hospitals**: May be in HCRIS historical data but not current CMS reference
3. **Non-Medicare hospitals**: Won't be in CMS files at all
4. **Data timing**: CMS reference updated monthly, HCRIS data is annual

---

## Field Mapping - Hospital General Information to Your Schema

| CMS Field | Your Schema Field | Notes |
|-----------|-------------------|-------|
| Facility ID | `ccn` | Primary identifier (6 digits) |
| Facility Name | `hospital_name` | Official hospital name |
| Address | `street_address` | Street address |
| City | `city` | City name |
| State | `state_code` | 2-letter state code |
| ZIP Code | `zip_code` | 5-digit ZIP |
| County Name | `county_name` | County name |
| Phone Number | `phone_number` | Main phone |
| Hospital Type | `hospital_type` | Type classification |
| Hospital Ownership | `ownership_type` | Ownership category |

---

## Troubleshooting

### "Download failed" or "403 Forbidden"

**Solution:** Use manual download method:
1. Visit the data.cms.gov link in your browser
2. Use the Export button on the website
3. Save CSV file to `data/cms_reference_data/`

### "CCN format mismatch"

CMS uses "Facility ID" which may have leading zeros stripped in Excel.
- **Always** pad to 6 digits: `str(ccn).zfill(6)`
- Example: `1234` → `001234`

### "Can't find my hospital"

1. Check if hospital is Medicare-certified (required for CMS data)
2. Verify CCN is correct (check on cms.gov or qualityreportingcenter.com)
3. Hospital may have closed or merged - check POS file for termination dates

---

## Additional Resources

### Official Documentation:
- [CMS Provider Data Catalog](https://data.cms.gov/provider-data/topics/hospitals)
- [Provider of Services Files Documentation](https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/Provider-of-Services)
- [NPPES NPI Documentation](https://download.cms.gov/nppes/NPI_Files.html)

### Lookup Tools:
- [CCN Lookup Tool](https://www.qualityreportingcenter.com/en/inpatient-quality-reporting-programs/CCNLookup/)
- [NPI Registry Search](https://npiregistry.cms.hhs.gov/)

### Research Data:
- [NBER Healthcare Data](https://www.nber.org/research/data?page=1&perPage=50&topic=76)
- [ResDAC CMS Variables](https://resdac.org/search-variables)

---

## Summary

✅ **Use Hospital General Information as your primary source** - it's current, complete, and easy to use.

✅ **Run the download script** to automatically fetch and prepare the data:
```bash
python scripts/download_cms_reference_data.py
```

✅ **This gives you everything you need:**
- CCN codes
- Hospital names
- Full addresses
- Phone numbers
- Hospital types and ownership
- Updated monthly by CMS

The script will verify coverage against your HCRIS data and create a clean mapping file ready to use!
