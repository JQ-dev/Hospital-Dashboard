# HCRIS Data Pipeline Documentation

This document explains the full pipeline for extracting, mapping, and exploring
CMS Hospital Cost Report (Form 2552-10) data from the HCRIS SAS files.

---

## Overview

The pipeline has three stages:

```
  SAS7BDAT files                 Column Mapping CSV              Interactive Explorer
  (raw HCRIS data)     --->      (5,618 column names      --->   (Jupyter notebook:
   hosp10-sas/                    with descriptions)               pick hospital +
                                  hosp10-extracted/                 worksheet, view data)
```

| Script                    | Purpose                                     |
|---------------------------|---------------------------------------------|
| `extract_hcris.py`        | Read SAS files, export to CSV or Parquet    |
| `build_column_mapping.py` | Map coded column names to human descriptions|
| `explore_hcris.ipynb`     | Interactive browser for hospital worksheets |


---

## Source Data

CMS publishes HCRIS hospital cost reports as SAS7BDAT product files at:
https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/Cost-Reports

The files live in `hosp10-sas/`:

```
hosp10-sas/
  prds_hosp10_yr2010.sas7bdat   (2,325 hospitals, ~24 MB)
  prds_hosp10_yr2011.sas7bdat   (6,152 hospitals, ~60 MB)
  ...
  prds_hosp10_yr2025.sas7bdat   (75 hospitals,    ~2 MB)
  2552-10 SAS FILE RECORD LAYOUT AND CROSSWALK TO 96 - 2010.xlsx
```

Each file is a **wide-format table**: one row per hospital cost report, 5,618
columns. These "product" files are pre-joined from the four raw HCRIS tables
(RPT, ALPHA, NMRC, ROLLUP) into a single pivoted dataset.


---

## Stage 1: Extracting SAS Data (`extract_hcris.py`)

### What it does

Reads `prds_hosp10_yr*.sas7bdat` files and exports them to CSV or Parquet.

### Usage

```bash
# Show info about all files (row counts, sizes) without extracting
python extract_hcris.py --info

# Extract all years to CSV (default)
python extract_hcris.py

# Extract specific years
python extract_hcris.py --years 2024 2025

# Extract a range of years
python extract_hcris.py --year-range 2020 2025

# Export as Parquet (smaller files, faster reads)
python extract_hcris.py --format parquet

# Combine all selected years into one file
python extract_hcris.py --combined
```

### Output

Files go to `hosp10-extracted/` by default:

```
hosp10-extracted/
  hosp10_yr2025.csv         # one per year
  hosp10_yr2024.csv
  ...
```

Or with `--combined`:
```
hosp10-extracted/
  hosp10_combined_2010_2025.csv   # all years merged
```

Each output file adds a `year` column at the front.


---

## Stage 2: Building the Column Mapping (`build_column_mapping.py`)

### The Problem

The SAS columns have coded names like `S3_1_C3_8` or `D_4_HOS_C4_6250`.
These encode:
- **Worksheet** (e.g. S-3 = Utilization Data)
- **Part** (e.g. Part I)
- **Facility type** (e.g. HOS = Hospital)
- **Form column number** (e.g. C3 = Title XVIII Medicare Days)
- **Form line number** (e.g. 8 = Intensive Care Unit)

### How the Mapping Works

The script produces `hosp10-extracted/column_mapping.csv` with these fields:

| Field            | Example                                |
|------------------|----------------------------------------|
| `sas_column`     | `S3_1_C3_8`                            |
| `description`    | Intensive Care Unit                    |
| `data_type`      | ROLLUP                                 |
| `worksheet_code` | S300001                                |
| `worksheet_name` | S-3, Part I: Utilization Data          |
| `line_num`       | 00800                                  |
| `column_num`     | 00300                                  |
| `column_header`  | Inpatient Days (Title XVIII Medicare)  |

- **`description`** = the **row/line** label (what cost center or category)
- **`column_header`** = the **form column** label (what measure: days, charges, costs...)

### Three-Tier Fallback for `description`

The script tries three sources in order:

1. **Crosswalk Excel** -- The file `2552-10 SAS FILE RECORD LAYOUT AND
   CROSSWALK TO 96 - 2010.xlsx`, sheet "RECORD LAYOUT", has a `FIELD_DESCRIPTION`
   for ~3,680 columns. This is the primary source.

2. **Line description reuse** -- If a column has the same worksheet code + line
   number as another column that does have a description, it reuses that
   description. This fills ~46 more columns.

3. **Column name parsing** -- The function `parse_column_name()` decodes the
   SAS column name pattern `{Worksheet}_{Part}_{Facility}_C{Col}_{Line}` and
   builds a description like `"Hospital | Line 31.01 | Col 1"`. This fills
   ~1,830 more columns.

4. **Special patterns** -- For columns that don't match the standard pattern
   (e.g. `G_C1THRU4_56`, `util_cd`), hardcoded dictionaries provide the
   description.

### Column Header Source (`column_header`)

Column headers come from the `FORM_COLUMN_HEADERS` dictionary in the script.
This is a manual mapping of CMS Form 2552-10 column headers per worksheet.
For example, Worksheet S-3 Part I has:

| Form Column | column_num | Column Header                          |
|-------------|------------|----------------------------------------|
| C2          | 00200      | Inpatient Days (Title V & XVIII)       |
| C3          | 00300      | Inpatient Days (Title XVIII Medicare)  |
| C4          | 00400      | Discharges (Title XVIII Medicare)      |
| C5          | 00500      | Inpatient Days (Title XIX Medicaid)    |
| C6          | 00600      | Total Inpatient Days                   |
| C7          | 00700      | % Medicare Days / Total Days           |
| C8          | 00800      | Total Discharges                       |

### Usage

```bash
python build_column_mapping.py
```

Output: `hosp10-extracted/column_mapping.csv` (5,618 rows).

### Key Data Structures in the Script

| Dict / Constant         | Purpose                                              |
|-------------------------|------------------------------------------------------|
| `WORKSHEET_NAMES`       | Maps worksheet codes to human names (90+ entries)    |
| `FACILITY_TYPES`        | Maps abbreviations: HOS, IPF, IRF, SNF, HHA1-5, etc |
| `FORM_COLUMN_HEADERS`   | Maps worksheet + column number to form column header |
| `KNOWN_META_COLUMNS`    | Descriptions for `util_cd`, `proc_dt`, `msa`, etc   |


---

## Stage 3: Interactive Explorer (`explore_hcris.ipynb`)

### What it does

A Jupyter notebook with ipywidgets for browsing hospital data:

1. **Select Year** -- Dropdown + "Load Year" button. Reads the SAS file.
2. **Filter/Select Hospital** -- Text filter narrows the dropdown list.
   Hospitals shown as `"010008 - CRENSHAW COMMUNITY HOSPITAL (AL)"`.
3. **Select Worksheet** -- Dropdown listing all 101 worksheets with column counts.
4. **View Data** -- Button displays a table with:

| Description              | Column Header                        | Value   |
|--------------------------|--------------------------------------|---------|
| Intensive Care Unit      | Inpatient Days (Title XVIII Medicare) | 420.0   |
| Intensive Care Unit      | Total Discharges                     | 112.0   |
| Coronary Care Unit       | Inpatient Days (Title XVIII Medicare) | 180.0   |

### Usage

1. Open `explore_hcris.ipynb` in VS Code or JupyterLab
2. Run Cell 1 (setup) then Cell 2 (widgets)
3. Select year, hospital, worksheet
4. Click "View Data"


---

## How to Add Missing Column Names and Line Descriptions

When you see generic descriptions like `"Hospital | Line 12 | Col 1"` or empty
`column_header` values, you can add the real CMS form labels. Here's how.

### Adding Line (Row) Descriptions

Line descriptions tell you what each row means on the form (e.g. "Intensive
Care Unit", "Coronary Care Unit", "Adults & Pediatrics").

**Option A: The crosswalk already has it, but it wasn't matched**

Check the crosswalk Excel file, sheet "RECORD LAYOUT". Search for the
worksheet code and line number. If you find a description there, the matching
logic may need adjustment (case sensitivity, extra spaces, etc).

**Option B: Add the description to the crosswalk lookup**

The crosswalk is the primary source. If CMS publishes an updated crosswalk
Excel file, replace the file in `hosp10-sas/` and re-run:

```bash
python build_column_mapping.py
```

**Option C: The line is not in the crosswalk**

For lines that CMS added after the crosswalk was published, the description
falls back to pattern parsing (`"Line 12 | Col 1"`). To add a real
description, you have two choices:

1. **Add to the crosswalk Excel** -- Open the Excel file, go to sheet
   "RECORD LAYOUT", and add a row with `DATA_TYPE`, `LABEL` (the SAS column
   name), `FIELD_DESCRIPTION`, `WKSHT_CD`, `LINE_NUM`, and `CLMN_NUM`.

2. **Add a hardcoded override in the script** -- In `build_column_mapping.py`,
   add entries to the `KNOWN_META_COLUMNS` dictionary at the top of the file:

   ```python
   KNOWN_META_COLUMNS = {
       "util_cd": "Utilization Code (F=Full, L=Low Medicare)",
       ...
       # Add your new column here:
       "E5_C1_1": "Some Description From CMS Form",
   }
   ```

   Then re-run `python build_column_mapping.py`.

### Adding Column Headers

Column headers tell you what each form column measures (e.g. "Title XVIII
Days", "Total Charges", "Cost/Charge Ratio").

These are defined in the `FORM_COLUMN_HEADERS` dictionary in
`build_column_mapping.py`. To add headers for a worksheet:

**Step 1: Find the worksheet code**

Look at the `column_mapping.csv` for the worksheet you're interested in. The
`worksheet_code` column has the code (e.g. `S300001`, `G300000`).

**Step 2: Find the column numbers**

Look at the `column_num` values for that worksheet. They're 5-digit strings
like `00100`, `00200`, `00300`.

**Step 3: Look up the CMS form**

The CMS 2552-10 form instructions document what each column means. You can
find this at https://www.cms.gov/Regulations-and-Guidance/Guidance/Transmittals/
or by searching for "CMS 2552-10 form instructions".

**Step 4: Add to the dictionary**

In `build_column_mapping.py`, add an entry to `FORM_COLUMN_HEADERS`:

```python
FORM_COLUMN_HEADERS = {
    ...
    # Add your worksheet here:
    "S500000": {                          # worksheet code
        "00100": "Number of Stations",    # column_num -> header
        "00200": "Total Patients",
        "00300": "Medicare Patients",
    },
    ...
}
```

**Step 5: Handle shared column structures**

If multiple worksheets use the same column layout (e.g. D Part II for Hospital,
IPF, IRF all have the same columns), add the inheritance at the bottom of the
`FORM_COLUMN_HEADERS` section:

```python
_MY_COLS = FORM_COLUMN_HEADERS.get("D00A182", {})
for code in ["D00B182", "D00C182"]:
    FORM_COLUMN_HEADERS.setdefault(code, _MY_COLS)
```

**Step 6: Regenerate**

```bash
python build_column_mapping.py
```

The new headers will appear in `column_mapping.csv` and in the notebook.

### Adding New Worksheet Names

If a worksheet code appears in the mapping but has no human-readable name
(shows the raw code like `S420000` instead of a name), add it to the
`WORKSHEET_NAMES` dictionary in `build_column_mapping.py`:

```python
WORKSHEET_NAMES = {
    ...
    "S420000": "S-4: HHA 2 Cost Report Data",
    ...
}
```


---

## Column Naming Convention Reference

The SAS column names encode the form location:

```
  E3_2_HOS_C1_3101
  |  | |   |  |
  |  | |   |  +-- Line number (31.01 on the form)
  |  | |   +----- Form column number (Column 1)
  |  | +--------- Facility type (HOS = Hospital)
  |  +----------- Part number (Part II)
  +-------------- Worksheet (E-3 = Settlement)
```

### Facility Type Abbreviations

| Code  | Meaning                            |
|-------|------------------------------------|
| HOS   | Hospital                           |
| IPF   | Inpatient Psychiatric Facility     |
| IRF   | Inpatient Rehabilitation Facility  |
| SNF   | Skilled Nursing Facility           |
| SUB1  | Subprovider 1                      |
| SUB2  | Subprovider 2                      |
| SWSNF | Swing Bed SNF                      |
| HHA1  | Home Health Agency 1               |
| HHA2  | Home Health Agency 2               |
| HHA3  | Home Health Agency 3               |
| HHA4  | Home Health Agency 4               |
| HHA5  | Home Health Agency 5               |

### Line Number Format

Line numbers on the CMS form use a subscript notation:
- `00800` = Line 8
- `03101` = Line 31, subscript 01 (displayed as 31.01)
- `20000` = Line 200 (total line)

### Metadata Columns (Always Present)

| Column        | Description                              |
|---------------|------------------------------------------|
| `rpt_rec_num` | Unique report record number (primary key)|
| `prvdr_num`   | 6-digit CMS provider number              |
| `fi_num`      | Fiscal intermediary number               |
| `rpt_stus_cd` | Report status (1=As Submitted, etc.)     |
| `fi_creat_dt` | FI/MAC create date                       |
| `fy_bgn_dt`   | Fiscal year begin date                   |
| `fy_end_dt`   | Fiscal year end date                     |
| `util_cd`     | Utilization code (F=Full, L=Low Medicare)|
| `trnsmtl_num` | Transmittal number                       |
| `state`       | SSA state code (numeric)                 |
| `st_cty_cd`   | SSA state + county code                  |
| `census`      | Census division code                     |
| `region`      | CMS region code                          |
| `sub3`        | Subprovider III indicator                |
| `proc_dt`     | Processing date                          |
| `msa`         | Metropolitan statistical area code       |


---

## Quick Reference

| Task                              | Command                            |
|-----------------------------------|------------------------------------|
| See what data is available        | `python extract_hcris.py --info`   |
| Extract year 2024 to CSV          | `python extract_hcris.py --years 2024` |
| Extract all years to Parquet      | `python extract_hcris.py --format parquet` |
| Regenerate column mapping         | `python build_column_mapping.py`   |
| Browse data interactively         | Open `explore_hcris.ipynb`         |
