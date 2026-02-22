#!/usr/bin/env python3
"""
Build a column name mapping from the HCRIS 2552-10 crosswalk Excel file.

Reads the 'RECORD LAYOUT' and 'NEW ROLLUPS' sheets and produces a CSV mapping
that maps each SAS column name to its human-readable description, worksheet,
line, and column.

For columns without descriptions in the crosswalk (~1,800), the script decodes
the column name pattern (e.g. E3_2_HOS_C1_3101) into a structured description
using worksheet names and CMS form line/column references.

Usage:
    python build_column_mapping.py
    python build_column_mapping.py --output column_mapping.csv
"""

import argparse
import re
import warnings
from pathlib import Path

import pandas as pd

DEFAULT_CROSSWALK = (
    Path(__file__).parent
    / "hosp10-sas"
    / "2552-10 SAS FILE RECORD LAYOUT AND CROSSWALK TO 96 - 2010.xlsx"
)
DEFAULT_SAS_FILE = (
    Path(__file__).parent / "hosp10-sas" / "prds_hosp10_yr2025.sas7bdat"
)
DEFAULT_OUTPUT = Path(__file__).parent / "hosp10-extracted" / "column_mapping.csv"

# Worksheet code -> human-readable name (from CMS Form 2552-10 + rollup sheet)
WORKSHEET_NAMES = {
    # S worksheets - Statistical data
    "S100000": "S-10: Uncompensated/Indigent Care",
    "S200001": "S-2, Part I: Hospital Identification",
    "S200002": "S-2, Part II: Hospital Characteristics",
    "S300001": "S-3, Part I: Utilization Data",
    "S300002": "S-3, Part II: Medicaid Ratio",
    "S300005": "S-3, Part V: Utilization Data",
    # A worksheets - Cost allocation
    "A000000": "A: Reclassification & Adjustment of Trial Balance",
    "A600000": "A-6: Reclassification",
    "A700001": "A-7, Part I: Capital Assets",
    "A700003": "A-7, Part III: Capital Assets",
    "A800000": "A-8: Adjustments to Expenses",
    # B worksheets - Cost allocation
    "B000001": "B, Part I: Cost Allocation - General",
    "B000002": "B, Part II: Cost Allocation",
    # C worksheets - Ancillary cost
    "C000001": "C, Part I: Ancillary & Outpatient Cost",
    # D worksheets - Apportionment
    "D00A181": "D, Part I: Apportionment - Hospital",
    "D00A182": "D, Part II: Apportionment - Hospital",
    "D00A183": "D, Part III: Apportionment - Hospital",
    "D00A184": "D, Part IV: Apportionment - Hospital",
    "D00A185": "D, Part V: Apportionment - Hospital",
    "D00B182": "D, Part II: Apportionment - IPF",
    "D00B184": "D, Part IV: Apportionment - IPF",
    "D00C182": "D, Part II: Apportionment - IRF",
    "D00C184": "D, Part IV: Apportionment - IRF",
    "D00E184": "D, Part IV: Apportionment - SNF",
    "D01D182": "D, Part II: Apportionment - Subprovider 1",
    "D01D184": "D, Part IV: Apportionment - Subprovider 1",
    "D02D182": "D, Part II: Apportionment - Subprovider 2",
    "D02D184": "D, Part IV: Apportionment - Subprovider 2",
    "D10A181": "D-1: Apportionment - Hospital (Old Age)",
    "D30A180": "D-3: Apportionment - Hospital",
    "D30B180": "D-3: Apportionment - IPF",
    "D30C180": "D-3: Apportionment - IRF",
    "D30E180": "D-3: Apportionment - SNF",
    "D31D180": "D-3: Apportionment - Subprovider 1",
    "D32D180": "D-3: Apportionment - Subprovider 2",
    "D4H0000": "D-4: Organ Acquisition - Heart",
    "D4I0000": "D-4: Organ Acquisition - Intestine",
    "D4K0000": "D-4: Organ Acquisition - Kidney",
    "D4L0000": "D-4: Organ Acquisition - Liver",
    "D4N0000": "D-4: Organ Acquisition - Pancreas",
    "D4P0000": "D-4: Organ Acquisition - Lung",
    "D4S0000": "D-4: Organ Acquisition - Islet",
    # E worksheets - Reimbursement settlement
    "E00A181": "E, Part A: Settlement - Hospital",
    "E00A18A": "E, Part A: Settlement - Hospital",
    "E00A18B": "E, Part B: Settlement - Hospital",
    "E00B18B": "E, Part B: Settlement - IPF",
    "E00C18B": "E, Part B: Settlement - IRF",
    "E00E18B": "E, Part B: Settlement - SNF",
    "E01D18B": "E, Part B: Settlement - Subprovider 1",
    "E02D18B": "E, Part B: Settlement - Subprovider 2",
    "E10A182": "E-1, Part II: Settlement",
    "E20F180": "E-2: Swing Bed SNF",
    "E30A181": "E-3, Part I: Settlement - Hospital",
    "E30A182": "E-3, Part II: Settlement - Hospital",
    "E30A183": "E-3, Part III: Settlement - Hospital",
    "E30A184": "E-3, Part IV: Settlement - Hospital",
    "E30A185": "E-3, Part V: Settlement - Hospital",
    "E30B181": "E-3, Part I: Settlement - IPF",
    "E30B182": "E-3, Part II: Settlement - IPF",
    "E30C181": "E-3, Part I: Settlement - IRF",
    "E30C183": "E-3, Part III: Settlement - IRF",
    "E30C184": "E-3, Part III: Settlement - IRF",
    "E30E181": "E-3, Part I: Settlement - SNF",
    "E30E186": "E-3, Part VI: Settlement - SNF",
    "E31D181": "E-3, Part I: Settlement - Subprovider 1",
    "E31D184": "E-3, Part IV: Settlement - Subprovider 1",
    "E32D181": "E-3, Part I: Settlement - Subprovider 2",
    "E32D184": "E-3, Part IV: Settlement - Subprovider 2",
    "E40A180": "E-4: DSH Payment Adjustment",
    # G worksheets - Balance sheet
    "G000000": "G: Balance Sheet",
    "G200000": "G-2: Statement of Changes in Fund Balance",
    "G300000": "G-3: Statement of Revenue & Expenses",
    # H worksheets - HHA
    "H310181": "H-3, Part I: HHA 1",
    "H320181": "H-3, Part I: HHA 2",
    "H330181": "H-3, Part I: HHA 3",
    "H340181": "H-3, Part I: HHA 4",
    "H350181": "H-3, Part I: HHA 5",
    "H410182": "H-4, Part II: HHA 1",
    "H420182": "H-4, Part II: HHA 2",
    "H430182": "H-4, Part II: HHA 3",
    "H440182": "H-4, Part II: HHA 4",
    "H450182": "H-4, Part II: HHA 5",
    # L worksheets
    "L00A181": "L, Part I: Hospital",
    "L00A182": "L, Part II: Hospital",
    "L00A183": "L, Part III: Hospital",
}

# Provider/facility type abbreviations in column names
FACILITY_TYPES = {
    "HOS": "Hospital",
    "IPF": "Inpatient Psychiatric Facility",
    "IRF": "Inpatient Rehabilitation Facility",
    "SNF": "Skilled Nursing Facility",
    "SUB1": "Subprovider 1",
    "SUB2": "Subprovider 2",
    "SWSNF": "Swing Bed SNF",
    "HHA1": "Home Health Agency 1",
    "HHA2": "Home Health Agency 2",
    "HHA3": "Home Health Agency 3",
    "HHA4": "Home Health Agency 4",
    "HHA5": "Home Health Agency 5",
}

# CMS Form 2552-10 column headers per worksheet.
# Key = worksheet prefix (matched against the SAS column name prefix).
# Value = {form_col_num: header_label}.
# Column numbers use the raw form (e.g. "00200" -> "C2").
FORM_COLUMN_HEADERS = {
    # S-2, Part I: Hospital Identification
    "S200001": {
        "00100": "General Information",
        "00200": "Provider Number / Address",
        "00300": "MSA / Payment System",
        "00400": "Hospital Type / Provider Type",
        "00500": "Component",
        "00600": "Component Number",
        "00700": "Provider Number (Swing Bed)",
    },
    # S-3, Part I: Utilization Data (Inpatient)
    "S300001": {
        "00200": "Inpatient Days (Title V & XVIII)",
        "00300": "Inpatient Days (Title XVIII Medicare)",
        "00400": "Discharges (Title XVIII Medicare)",
        "00500": "Inpatient Days (Title XIX Medicaid)",
        "00600": "Total Inpatient Days",
        "00700": "% Medicare Days / Total Days",
        "00800": "Total Discharges",
        "00900": "Inpatient Days (Title XVIII + XIX)",
        "01000": "Discharges (Title XIX Medicaid)",
        "01100": "Total Days (All Patients)",
        "01200": "Total Patient Days",
        "01300": "Average Length of Stay",
        "01400": "Beds Available",
        "01500": "Bed Days Available",
    },
    # S-3, Part II: Medicaid Ratio / Outpatient
    "S300002": {
        "00100": "Visits/Procedures",
        "00200": "Medicare Charges",
        "00300": "Total Charges",
        "00400": "Cost Center Code",
        "00500": "Medicare Visits",
        "00600": "Total Visits",
    },
    # S-10: Uncompensated / Indigent Care
    "S100000": {
        "00100": "Amount",
        "00200": "Amount (Secondary)",
    },
    # A: Reclassification & Adjustment of Trial Balance
    "A000000": {
        "00100": "Salaries",
        "00200": "Other Costs",
        "00600": "Reclassified Net Expenses",
    },
    # A-7, Part I: Capital Assets
    "A700001": {
        "00300": "Cost of Assets (Historical)",
        "00700": "Accumulated Depreciation",
    },
    # A-8: Adjustments to Expenses
    "A800000": {
        "00200": "Reclassification",
    },
    # B, Part I: Cost Allocation - General Service
    "B000001": {
        "00000": "Statistical Basis / Cost Center",
        "01900": "Cap Rel Costs - Bldg & Fixtures",
        "02000": "Cap Rel Costs - Movable Equipment",
        "02100": "Inpatient Routine Services",
        "02200": "Ancillary Services",
        "02300": "Outpatient Services",
        "02400": "Other Reimbursable",
        "02500": "Non-Reimbursable",
        "02600": "Stat Basis / Total",
    },
    # B, Part II: Cost Allocation
    "B000002": {
        "02100": "Inpatient Routine Services",
        "02200": "Ancillary Services",
        "02300": "Outpatient Services",
    },
    # C, Part I: Ancillary & Outpatient Cost
    "C000001": {
        "00200": "Total Charges (All Patients)",
        "00500": "Medicare Charges (Title XVIII PPS)",
        "00600": "Medicare Charges (Title XVIII Other)",
        "00700": "Total Medicare Charges (Title XVIII)",
    },
    # D, Part I-V: Apportionment
    "D00A181": {
        "00400": "Title XVIII Days",
        "00600": "Title XVIII Discharges",
        "00700": "Total Days",
    },
    "D00A182": {
        "00100": "Cost / Charge Ratio",
        "00200": "Charges",
        "00300": "Cost",
        "00400": "Payment",
        "00500": "Settlement Amount",
    },
    "D00A184": {
        "00100": "Cost / Charge Ratio",
        "00200": "Program Charges",
        "00300": "Program Cost",
        "00400": "Title XVIII PPS Payment",
        "00500": "Reasonable Cost Payment",
        "01000": "Tentative Settlement",
        "01100": "Net Settlement Amount",
        "01200": "Amount Due To/From Provider",
        "01300": "Amount Due To/From Program",
    },
    # D-1: Apportionment Hospital (Old Age)
    "D10A181": {
        "00100": "Cost per Diem",
    },
    # D-3: Apportionment
    "D30A180": {
        "00100": "Total Charges",
        "00200": "Medicare Charges",
        "00300": "Cost / Charge Ratio",
    },
    # E, Part A: Settlement - Hospital
    "E00A18A": {
        "00100": "Amount",
    },
    "E00A181": {
        "00100": "Amount",
    },
    # E, Part B: Settlement
    "E00A18B": {
        "00100": "Amount",
    },
    # E-3: Settlement (multiple parts)
    "E30A181": {
        "00100": "Amount",
    },
    # E-4: DSH Payment Adjustment
    "E40A180": {
        "00100": "Amount / Factor",
        "00200": "Secondary Amount",
        "00300": "Computed Value",
    },
    # G: Balance Sheet
    "G000000": {
        "00100": "Current Period End",
        "00200": "Prior Period End",
    },
    # G-2: Statement of Changes in Fund Balance
    "G200000": {
        "00100": "General Fund",
        "00200": "Specific Purpose Fund",
        "00300": "Plant Fund",
        "00400": "Endowment Fund",
    },
    # G-3: Statement of Revenue & Expenses
    "G300000": {
        "00000": "Description",
        "00100": "Amount",
    },
    # L worksheets
    "L00A181": {
        "00100": "Amount",
    },
}

# Also map by worksheet prefix for worksheets sharing the same column structure
# (D Part II IPF/IRF/SNF/SUB all share D Part II Hospital structure)
_D2_COLS = FORM_COLUMN_HEADERS.get("D00A182", {})
for code in ["D00B182", "D00C182", "D01D182", "D02D182"]:
    FORM_COLUMN_HEADERS.setdefault(code, _D2_COLS)

_D4_COLS = FORM_COLUMN_HEADERS.get("D00A184", {})
for code in ["D00B184", "D00C184", "D00E184", "D01D184", "D02D184"]:
    FORM_COLUMN_HEADERS.setdefault(code, _D4_COLS)

_D3_COLS = FORM_COLUMN_HEADERS.get("D30A180", {})
for code in ["D30B180", "D30C180", "D30E180", "D31D180", "D32D180"]:
    FORM_COLUMN_HEADERS.setdefault(code, _D3_COLS)

_D1_COLS = FORM_COLUMN_HEADERS.get("D00A181", {})
for code in ["D00B181", "D00C181"]:
    FORM_COLUMN_HEADERS.setdefault(code, _D1_COLS)

_EB_COLS = FORM_COLUMN_HEADERS.get("E00A18B", {})
for code in ["E00B18B", "E00C18B", "E00E18B", "E01D18B", "E02D18B"]:
    FORM_COLUMN_HEADERS.setdefault(code, _EB_COLS)

_E3_COLS = FORM_COLUMN_HEADERS.get("E30A181", {})
for code in ["E30A182", "E30A183", "E30A184", "E30A185",
             "E30B181", "E30B182", "E30C181", "E30C183", "E30C184",
             "E30E181", "E30E186", "E31D181", "E31D184", "E32D181", "E32D184"]:
    FORM_COLUMN_HEADERS.setdefault(code, _E3_COLS)


# Known metadata columns not in the crosswalk
KNOWN_META_COLUMNS = {
    "util_cd": "Utilization Code (F=Full, L=Low Medicare)",
    "trnsmtl_num": "Transmittal Number",
    "proc_dt": "Processing Date",
    "msa": "Metropolitan Statistical Area Code",
    "_NAME_": "SAS Internal Row Identifier",
}


def parse_column_name(col_name: str) -> dict:
    """Parse a SAS column name like E3_2_HOS_C1_3101 into components."""
    # Pattern: {Worksheet}_{Part}_{Facility}_C{ColNum}_{LineNum}
    # or:      {Worksheet}_C{ColNum}_{LineNum}
    # or:      {Worksheet}_{Part}_C{ColNum}_{LineNum}

    # Try with facility type
    for fac_key in sorted(FACILITY_TYPES.keys(), key=len, reverse=True):
        pattern = rf'^(.+?)_{fac_key}_C(\d+)_(.+)$'
        m = re.match(pattern, col_name, re.IGNORECASE)
        if m:
            worksheet_part = m.group(1)
            form_col = m.group(2)
            line = m.group(3)
            return {
                "worksheet_part": worksheet_part,
                "facility": FACILITY_TYPES.get(fac_key, fac_key),
                "form_column": int(form_col),
                "form_line": line,
            }

    # Try without facility type: {WS}_{Part}_C{Col}_{Line} or {WS}_C{Col}_{Line}
    m = re.match(r'^(.+?)_C(\d+)_(.+)$', col_name)
    if m:
        worksheet_part = m.group(1)
        form_col = m.group(2)
        line = m.group(3)
        return {
            "worksheet_part": worksheet_part,
            "facility": "",
            "form_column": int(form_col),
            "form_line": line,
        }

    return None


def format_line_number(line_str: str) -> str:
    """Format a line number like '3101' as '31.01' when it has subscripts."""
    if len(line_str) > 2 and line_str[-2:] not in ("00",):
        major = line_str[:-2].lstrip("0") or "0"
        minor = line_str[-2:]
        if minor != "00":
            return f"{major}.{minor}"
    return line_str.lstrip("0") or "0"


def build_description(col_name: str, worksheet_name: str, parsed: dict) -> str:
    """Build a human-readable description for an undescribed column."""
    parts = []

    if parsed.get("facility"):
        parts.append(parsed["facility"])

    line_fmt = format_line_number(parsed["form_line"])
    parts.append(f"Line {line_fmt}")
    parts.append(f"Col {parsed['form_column']}")

    return " | ".join(parts)


def get_column_header(wksht_code: str, col_num: str) -> str:
    """Look up the form column header for a given worksheet code and column number."""
    headers = FORM_COLUMN_HEADERS.get(wksht_code, {})
    return headers.get(col_num, "")


def build_mapping(crosswalk_path: Path, sas_path: Path) -> pd.DataFrame:
    """Build the column mapping DataFrame."""
    # Read crosswalk sheets
    layout = pd.read_excel(
        str(crosswalk_path), sheet_name="RECORD LAYOUT", keep_default_na=False
    )
    rollup = pd.read_excel(
        str(crosswalk_path), sheet_name="NEW ROLLUPS", keep_default_na=False
    )

    # Build worksheet name lookup from rollup sheet
    for _, r in rollup.iterrows():
        wk = str(r["Wksht Cd"]).strip()
        ws = str(r["Worksheet"]).strip()
        if wk and ws and wk not in WORKSHEET_NAMES:
            WORKSHEET_NAMES[wk] = ws

    # Filter to data rows with labels
    valid_types = {"ID", "NUMERIC", "ALPHANUMERIC", "ROLLUP"}
    data_rows = layout[
        layout["DATA_TYPE"].isin(valid_types) & (layout["LABEL"].str.strip() != "")
    ].copy()
    data_rows["LABEL"] = data_rows["LABEL"].str.strip()
    data_rows["FIELD_DESCRIPTION "] = data_rows["FIELD_DESCRIPTION "].str.strip()

    # Build lookup: lowercase label -> row
    crosswalk_lookup = {}
    for _, row in data_rows.iterrows():
        key = row["LABEL"].lower()
        crosswalk_lookup[key] = row

    # Build line description lookup from described rows:
    # (worksheet_code, line_num) -> description
    line_desc_lookup = {}
    for _, row in data_rows.iterrows():
        desc = row["FIELD_DESCRIPTION "]
        wk = str(row["WKSHT_CD"]).strip()
        ln = str(row["LINE_NUM"]).strip()
        if desc and wk and ln and (wk, ln) not in line_desc_lookup:
            line_desc_lookup[(wk, ln)] = desc

    # Load user-provided fill-in files if they exist
    fill_lines_path = Path(__file__).parent / "hosp10-extracted" / "FILL_LINE_DESCRIPTIONS.csv"
    fill_cols_path = Path(__file__).parent / "hosp10-extracted" / "FILL_COLUMN_HEADERS.csv"

    user_line_overrides = {}  # (worksheet_name, line_num) -> description
    if fill_lines_path.exists():
        fill_lines = pd.read_csv(str(fill_lines_path), keep_default_na=False)
        for _, r in fill_lines.iterrows():
            desc = str(r.get("line_description", "")).strip()
            if desc:
                user_line_overrides[(r["worksheet_name"], str(r["line_num"]).strip())] = desc
        if user_line_overrides:
            print(f"  Loaded {len(user_line_overrides)} line descriptions from FILL_LINE_DESCRIPTIONS.csv")

    user_col_overrides = {}  # (worksheet_code, column_num) -> header
    if fill_cols_path.exists():
        fill_cols = pd.read_csv(str(fill_cols_path), keep_default_na=False)
        for _, r in fill_cols.iterrows():
            hdr = str(r.get("column_header", "")).strip()
            if hdr:
                user_col_overrides[(str(r["worksheet_code"]).strip(), str(r["column_num"]).strip())] = hdr
        if user_col_overrides:
            print(f"  Loaded {len(user_col_overrides)} column headers from FILL_COLUMN_HEADERS.csv")

    # Read actual SAS columns
    warnings.filterwarnings("ignore", message="column count mismatch")
    sas_df = pd.read_sas(str(sas_path), format="sas7bdat", encoding="latin1")
    sas_columns = list(sas_df.columns)

    # Build the mapping for every SAS column
    rows = []
    for col in sas_columns:
        key = col.lower().strip()

        if key in crosswalk_lookup:
            r = crosswalk_lookup[key]
            wksht_code = str(r["WKSHT_CD"]).strip()
            orig_desc = r["FIELD_DESCRIPTION "]
            line_num = str(r["LINE_NUM"]).strip() if r["LINE_NUM"] else ""
            col_num = str(r["CLMN_NUM"]).strip() if r["CLMN_NUM"] else ""
            data_type = r["DATA_TYPE"]
            ws_name = WORKSHEET_NAMES.get(wksht_code, wksht_code)

            # If no description, try line_desc_lookup or parse
            if not orig_desc:
                orig_desc = line_desc_lookup.get((wksht_code, line_num), "")

            if not orig_desc:
                parsed = parse_column_name(col)
                if parsed:
                    orig_desc = build_description(col, ws_name, parsed)

            # Handle special patterns that parse_column_name can't decode
            if not orig_desc:
                g_match = re.match(r'^G_C1THRU4_(\d+)$', col)
                if g_match:
                    orig_desc = f"Balance Sheet Cols 1-4, Line {g_match.group(1)}"
                elif col in KNOWN_META_COLUMNS:
                    orig_desc = KNOWN_META_COLUMNS[col]

            rows.append({
                "sas_column": col,
                "description": orig_desc,
                "data_type": data_type,
                "worksheet_code": wksht_code,
                "worksheet_name": ws_name,
                "line_num": line_num,
                "column_num": col_num,
                "column_header": get_column_header(wksht_code, col_num),
            })
        else:
            # Column not in crosswalk at all - try to parse from name
            parsed = parse_column_name(col)

            # Handle known special patterns
            desc, ws_name, data_type = "", "", ""
            g_match = re.match(r'^G_C1THRU4_(\d+)$', col)
            if g_match:
                line = g_match.group(1)
                desc = f"Balance Sheet Cols 1-4, Line {line}"
                ws_name = "G: Balance Sheet"
                data_type = "ROLLUP"
            elif col in KNOWN_META_COLUMNS:
                desc = KNOWN_META_COLUMNS[col]
                data_type = "ID"

            if parsed:
                if not desc:
                    desc = build_description(col, ws_name, parsed)
                rows.append({
                    "sas_column": col,
                    "description": desc,
                    "data_type": data_type or "UNKNOWN",
                    "worksheet_code": "",
                    "worksheet_name": ws_name,
                    "line_num": parsed["form_line"],
                    "column_num": str(parsed["form_column"]),
                    "column_header": "",
                })
            else:
                rows.append({
                    "sas_column": col,
                    "description": desc,
                    "data_type": data_type,
                    "worksheet_code": "",
                    "worksheet_name": ws_name,
                    "line_num": "",
                    "column_num": "",
                    "column_header": "",
                })

    # Apply user-provided overrides from fill-in CSV files
    for row_dict in rows:
        ws_name = row_dict.get("worksheet_name", "")
        ws_code = row_dict.get("worksheet_code", "")
        ln = str(row_dict.get("line_num", "")).strip()
        cn = str(row_dict.get("column_num", "")).strip()

        # Override line description if user provided one
        override_desc = user_line_overrides.get((ws_name, ln))
        if override_desc:
            row_dict["description"] = override_desc

        # Override column header if user provided one
        override_hdr = user_col_overrides.get((ws_code, cn))
        if override_hdr and not row_dict.get("column_header"):
            row_dict["column_header"] = override_hdr

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Build HCRIS column name mapping from the 2552-10 crosswalk."
    )
    parser.add_argument(
        "--crosswalk", type=Path, default=DEFAULT_CROSSWALK,
        help="Path to the crosswalk Excel file",
    )
    parser.add_argument(
        "--sas-file", type=Path, default=DEFAULT_SAS_FILE,
        help="Path to a SAS7BDAT file to get actual column order",
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help="Output CSV path for the mapping",
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Reading crosswalk: {args.crosswalk.name}")
    print(f"Reading SAS columns from: {args.sas_file.name}")

    mapping = build_mapping(args.crosswalk, args.sas_file)

    has_desc = (mapping["description"].str.strip() != "").sum()
    total = len(mapping)
    print(f"\nMapping: {has_desc}/{total} columns have descriptions ({100*has_desc/total:.1f}%)")
    still_empty = total - has_desc
    if still_empty:
        empty = mapping[mapping["description"].str.strip() == ""]
        print(f"Still without description: {still_empty}")
        print("  Columns:", empty["sas_column"].tolist()[:20])

    mapping.to_csv(str(args.output), index=False)
    print(f"\nSaved to: {args.output}")

    # Print summary by worksheet
    print("\n--- Columns per worksheet ---")
    ws_counts = mapping.groupby("worksheet_name").size().sort_values(ascending=False)
    for ws, count in ws_counts.head(25).items():
        if ws:
            print(f"  {count:>5}  {ws}")

    # Print a sample of described columns
    print("\n--- Sample mappings ---")
    sample = mapping[mapping["description"].str.strip() != ""].iloc[::250]
    for _, r in sample.iterrows():
        desc = r["description"][:55].ljust(55)
        ws = r["worksheet_name"][:40] if r["worksheet_name"] else ""
        print(f"  {r['sas_column']:<30} {desc} [{ws}]")


if __name__ == "__main__":
    main()
