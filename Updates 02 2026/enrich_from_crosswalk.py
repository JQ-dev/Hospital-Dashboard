#!/usr/bin/env python3
"""
Enrich HCRIS column/line descriptions using the crosswalk from HCRIS-databuilder.

This script:
1. Reads the comprehensive crosswalk CSV (5,500+ field mappings from klocey/HCRIS-databuilder)
2. Reads the feature_labels CSV (2,771 human-readable labels)
3. Matches fields to our SAS columns and fills in missing descriptions
4. Propagates descriptions from Hospital variants to sub-provider variants
5. Updates FILL_LINE_DESCRIPTIONS.csv and FILL_COLUMN_HEADERS.csv
6. Produces an enriched column_mapping.csv

Usage:
    python enrich_from_crosswalk.py
    python enrich_from_crosswalk.py --dry-run   # Preview without writing
"""

import argparse
import csv
import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent
CROSSWALK_PATH = Path("/tmp/hcris_crosswalk.csv")
FEATURE_LABELS_PATH = Path("/tmp/hcris_feature_labels.csv")
COLUMN_MAPPING_PATH = BASE_DIR / "hosp10-extracted" / "column_mapping.csv"
FILL_LINES_PATH = BASE_DIR / "hosp10-extracted" / "FILL_LINE_DESCRIPTIONS.csv"
FILL_COLS_PATH = BASE_DIR / "hosp10-extracted" / "FILL_COLUMN_HEADERS.csv"


def load_crosswalk(path: Path) -> pd.DataFrame:
    """Load the HCRIS-databuilder crosswalk CSV."""
    df = pd.read_csv(str(path), encoding="utf-8-sig", keep_default_na=False)
    # Normalize column names
    df.columns = [c.strip() for c in df.columns]
    return df


def load_feature_labels(path: Path) -> dict:
    """Load feature labels and parse into a field_code -> label dict."""
    labels = {}
    if not path.exists():
        return labels
    with open(path, "r", encoding="utf-8-sig") as f:
        content = f.read().strip()
    # The file is a single row of comma-separated quoted strings
    # Each entry looks like: "CATEGORY, Description (field_code)"
    entries = []
    for match in re.finditer(r'"([^"]+)"', content):
        entries.append(match.group(1))

    for entry in entries:
        # Try to extract field code from parentheses
        m = re.search(r'\((\w+)\)$', entry.strip())
        if m:
            field_code = m.group(1)
            # Get the description part (everything before the field code)
            desc = entry[:entry.rfind("(")].strip().rstrip(",").strip()
            labels[field_code.upper()] = desc
    return labels


def build_crosswalk_lookup(crosswalk_df: pd.DataFrame) -> dict:
    """Build a lookup dict: field_name (uppercase) -> crosswalk row info."""
    lookup = {}
    for _, row in crosswalk_df.iterrows():
        field_name = str(row.get("10_FIELD_NAME", "")).strip().upper()
        if not field_name:
            continue
        desc = str(row.get("FIELD DESCRIPTION", "")).strip()
        if not desc:
            # Try alternate column name
            for col in crosswalk_df.columns:
                if "DESCRIPTION" in col.upper() and "FIELD" in col.upper():
                    desc = str(row.get(col, "")).strip()
                    if desc:
                        break

        lookup[field_name] = {
            "description": desc,
            "worksheet": str(row.get("WORKSHEET", "")).strip(),
            "category": str(row.get("CATEGORY", "")).strip(),
            "subcategory": str(row.get("SUBCATEGORY", "")).strip(),
            "data_type": str(row.get("DATA_TYPE", "")).strip(),
            "wksht_cd": str(row.get("WKSHT CD", "")).strip(),
            "line": str(row.get("LINE", "")).strip(),
            "column": str(row.get("COLUMN", "")).strip(),
        }
    return lookup


def build_line_descriptions(crosswalk_df: pd.DataFrame) -> dict:
    """Build lookup: (wksht_cd, line_num) -> description from crosswalk rows with descriptions."""
    line_descs = {}
    for _, row in crosswalk_df.iterrows():
        wk = str(row.get("WKSHT CD", "")).strip()
        ln = str(row.get("LINE", "")).strip()
        desc = ""
        for col in crosswalk_df.columns:
            if "DESCRIPTION" in col.upper() and "FIELD" in col.upper():
                desc = str(row.get(col, "")).strip()
                if desc:
                    break
        if wk and ln and desc:
            if (wk, ln) not in line_descs:
                line_descs[(wk, ln)] = desc
    return line_descs


def build_column_descriptions(crosswalk_df: pd.DataFrame) -> dict:
    """Build lookup: (wksht_cd, col_num) -> set of descriptions."""
    col_descs = {}
    for _, row in crosswalk_df.iterrows():
        wk = str(row.get("WKSHT CD", "")).strip()
        cn = str(row.get("COLUMN", "")).strip()
        cat = str(row.get("CATEGORY", "")).strip()
        subcat = str(row.get("SUBCATEGORY", "")).strip()
        if wk and cn and cat:
            key = (wk, cn)
            if key not in col_descs:
                col_descs[key] = cat
                if subcat:
                    col_descs[key] = f"{cat} - {subcat}"
    return col_descs


# Mapping of base worksheet codes to their sub-provider variants
# Sub-provider worksheets share the same line structure as the Hospital version
WORKSHEET_FAMILIES = {
    # D, Part II
    "D00A182": [
        "D00B182", "D00C182", "D00E182", "D01D182", "D02D182",
    ] + [f"D{i:02d}D182" for i in range(3, 55)],
    # D, Part IV
    "D00A184": [
        "D00B184", "D00C184", "D00E184", "D01D184", "D02D184",
    ] + [f"D{i:02d}D184" for i in range(3, 55)],
    # D-1
    "D10A181": ["D10B181", "D10C181", "D10E181", "D11D181", "D12D181"],
    # D-3
    "D30A180": [
        "D30B180", "D30C180", "D30E180", "D31D180", "D32D180",
    ] + [f"D{i:02d}D180" for i in range(33, 87)],
    # E, Part B
    "E00A18B": ["E00B18B", "E00C18B", "E00E18B", "E01D18B", "E02D18B"],
    # E-3, Part I
    "E30A181": ["E30B181", "E30C181", "E30E181", "E31D181", "E32D181"],
    # E-3, Part II
    "E30A182": ["E30B182"],
    # E-3, Part III
    "E30A183": ["E30C183", "E30C184"],
    # E-3, Part IV
    "E30A184": [f"E3{i:01d}D184" for i in range(1, 10)] + ["E30A185"],
}


def propagate_descriptions(line_descs: dict) -> dict:
    """Copy descriptions from base worksheet to sub-provider variants."""
    propagated = dict(line_descs)
    for base_code, variant_codes in WORKSHEET_FAMILIES.items():
        # Find all line descriptions for the base worksheet
        base_lines = {
            ln: desc
            for (wk, ln), desc in line_descs.items()
            if wk == base_code
        }
        if not base_lines:
            continue
        for variant_code in variant_codes:
            for ln, desc in base_lines.items():
                key = (variant_code, ln)
                if key not in propagated:
                    propagated[key] = desc
    return propagated


def enrich_column_mapping(
    mapping_df: pd.DataFrame,
    crosswalk_lookup: dict,
    feature_labels: dict,
    line_descs: dict,
) -> pd.DataFrame:
    """Enrich the column_mapping DataFrame with crosswalk data."""
    enriched = mapping_df.copy()

    filled_from_crosswalk = 0
    filled_from_labels = 0
    filled_from_propagation = 0

    for idx, row in enriched.iterrows():
        sas_col = str(row["sas_column"]).strip()
        current_desc = str(row.get("description", "")).strip()

        # Skip if already has a good description (not just "Line X | Col Y")
        has_real_desc = current_desc and not re.match(
            r'^(Hospital|IPF|IRF|SNF|Subprovider|HHA|Swing Bed)?\s*\|?\s*Line\s+\d',
            current_desc,
        )

        if has_real_desc:
            # Still try to add category/subcategory from crosswalk
            key = sas_col.upper()
            if key in crosswalk_lookup:
                xw = crosswalk_lookup[key]
                if xw["category"] and not row.get("category"):
                    enriched.at[idx, "category"] = xw["category"]
                if xw["subcategory"] and not row.get("subcategory"):
                    enriched.at[idx, "subcategory"] = xw["subcategory"]
            continue

        # Try 1: Direct crosswalk match by field name
        key = sas_col.upper()
        if key in crosswalk_lookup:
            xw = crosswalk_lookup[key]
            if xw["description"]:
                enriched.at[idx, "description"] = xw["description"]
                enriched.at[idx, "category"] = xw["category"]
                enriched.at[idx, "subcategory"] = xw.get("subcategory", "")
                filled_from_crosswalk += 1
                continue

        # Try 2: Feature labels match
        if key in feature_labels:
            enriched.at[idx, "description"] = feature_labels[key]
            filled_from_labels += 1
            continue

        # Try 3: Line description propagation (for sub-provider worksheets)
        wksht_code = str(row.get("worksheet_code", "")).strip()
        line_num = str(row.get("line_num", "")).strip()
        if wksht_code and line_num:
            desc = line_descs.get((wksht_code, line_num))
            if desc:
                enriched.at[idx, "description"] = desc
                filled_from_propagation += 1
                continue

    # Add category/subcategory columns if they don't exist
    if "category" not in enriched.columns:
        enriched["category"] = ""
    if "subcategory" not in enriched.columns:
        enriched["subcategory"] = ""

    print(f"\n  Enrichment results:")
    print(f"    Filled from crosswalk direct match: {filled_from_crosswalk}")
    print(f"    Filled from feature labels:         {filled_from_labels}")
    print(f"    Filled from line propagation:        {filled_from_propagation}")
    print(f"    Total newly filled:                  {filled_from_crosswalk + filled_from_labels + filled_from_propagation}")

    return enriched


def update_fill_line_descriptions(
    fill_path: Path,
    line_descs: dict,
    crosswalk_lookup: dict,
) -> int:
    """Update FILL_LINE_DESCRIPTIONS.csv with descriptions from crosswalk."""
    if not fill_path.exists():
        print(f"  {fill_path.name} not found, skipping")
        return 0

    df = pd.read_csv(str(fill_path), keep_default_na=False)
    filled = 0

    for idx, row in df.iterrows():
        current_desc = str(row.get("line_description", "")).strip()
        if current_desc:
            continue  # Already has a description

        sas_col = str(row.get("example_sas_column", "")).strip()

        # Try crosswalk direct match
        key = sas_col.upper()
        if key in crosswalk_lookup:
            xw = crosswalk_lookup[key]
            if xw["description"]:
                df.at[idx, "line_description"] = xw["description"]
                filled += 1
                continue

        # Try worksheet/line lookup
        ws_name = str(row.get("worksheet_name", "")).strip()
        line_num = str(row.get("line_num", "")).strip()
        # Try all worksheet codes for this line
        for (wk, ln), desc in line_descs.items():
            if ln == line_num and desc:
                df.at[idx, "line_description"] = desc
                filled += 1
                break

    df.to_csv(str(fill_path), index=False)
    return filled


def update_fill_column_headers(
    fill_path: Path,
    col_descs: dict,
) -> int:
    """Update FILL_COLUMN_HEADERS.csv with descriptions from crosswalk."""
    if not fill_path.exists():
        print(f"  {fill_path.name} not found, skipping")
        return 0

    df = pd.read_csv(str(fill_path), keep_default_na=False)
    filled = 0

    for idx, row in df.iterrows():
        current_hdr = str(row.get("column_header", "")).strip()
        if current_hdr:
            continue

        wk_code = str(row.get("worksheet_code", "")).strip()
        col_num = str(row.get("column_num", "")).strip()

        key = (wk_code, col_num)
        if key in col_descs:
            df.at[idx, "column_header"] = col_descs[key]
            filled += 1

    df.to_csv(str(fill_path), index=False)
    return filled


def generate_enrichment_report(
    mapping_df: pd.DataFrame, enriched_df: pd.DataFrame
) -> str:
    """Generate a summary report of enrichments made."""
    lines = []
    lines.append("=" * 70)
    lines.append("HCRIS Data Enrichment Report")
    lines.append("=" * 70)

    # Before
    orig_has_desc = (mapping_df["description"].str.strip() != "").sum()
    orig_total = len(mapping_df)
    lines.append(f"\nBefore enrichment:")
    lines.append(f"  Total columns: {orig_total}")
    lines.append(f"  With descriptions: {orig_has_desc} ({100*orig_has_desc/orig_total:.1f}%)")
    lines.append(f"  Missing descriptions: {orig_total - orig_has_desc}")

    # After
    new_has_desc = (enriched_df["description"].str.strip() != "").sum()
    new_total = len(enriched_df)
    # Count real descriptions (not just "Line X | Col Y" patterns)
    real_desc_mask = enriched_df["description"].str.strip().apply(
        lambda d: bool(d) and not bool(re.match(
            r'^(Hospital|IPF|IRF|SNF|Subprovider|HHA|Swing Bed)?\s*\|?\s*Line\s+\d',
            d,
        ))
    )
    real_descs = real_desc_mask.sum()

    lines.append(f"\nAfter enrichment:")
    lines.append(f"  Total columns: {new_total}")
    lines.append(f"  With any description: {new_has_desc} ({100*new_has_desc/new_total:.1f}%)")
    lines.append(f"  With real descriptions: {real_descs} ({100*real_descs/new_total:.1f}%)")
    lines.append(f"  Still missing: {new_total - new_has_desc}")

    # Improvement
    improvement = new_has_desc - orig_has_desc
    lines.append(f"\n  Descriptions added: +{improvement}")

    # Per-worksheet summary
    lines.append(f"\n--- Descriptions by worksheet ---")
    ws_groups = enriched_df.groupby("worksheet_name")
    ws_summary = []
    for ws_name, group in ws_groups:
        if not ws_name:
            continue
        total = len(group)
        has_desc = (group["description"].str.strip() != "").sum()
        ws_summary.append((ws_name, total, has_desc))
    ws_summary.sort(key=lambda x: x[1], reverse=True)

    for ws_name, total, has_desc in ws_summary[:30]:
        pct = 100 * has_desc / total if total else 0
        bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
        lines.append(f"  {ws_name:<50} {has_desc:>4}/{total:<4} [{bar}] {pct:.0f}%")

    # Still missing (sample)
    still_missing = enriched_df[enriched_df["description"].str.strip() == ""]
    if not still_missing.empty:
        lines.append(f"\n--- Sample of still-missing columns ({len(still_missing)} total) ---")
        for _, row in still_missing.head(20).iterrows():
            lines.append(f"  {row['sas_column']:<35} ws={row.get('worksheet_name','')}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Enrich HCRIS data with crosswalk descriptions")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    args = parser.parse_args()

    print("Loading crosswalk data...")
    if not CROSSWALK_PATH.exists():
        print(f"ERROR: Crosswalk file not found at {CROSSWALK_PATH}")
        print("Please download it from https://github.com/klocey/HCRIS-databuilder/")
        print("Expected file: crosswalk/2552-10 SAS FILE RECORD LAYOUT AND CROSSWALK TO 96 - 2021.csv")
        return

    crosswalk_df = load_crosswalk(CROSSWALK_PATH)
    print(f"  Loaded {len(crosswalk_df)} crosswalk entries")

    crosswalk_lookup = build_crosswalk_lookup(crosswalk_df)
    print(f"  Built lookup with {len(crosswalk_lookup)} field mappings")

    feature_labels = load_feature_labels(FEATURE_LABELS_PATH)
    print(f"  Loaded {len(feature_labels)} feature labels")

    line_descs = build_line_descriptions(crosswalk_df)
    print(f"  Built {len(line_descs)} line descriptions")

    # Propagate to sub-provider variants
    line_descs = propagate_descriptions(line_descs)
    print(f"  After propagation: {len(line_descs)} line descriptions")

    col_descs = build_column_descriptions(crosswalk_df)
    print(f"  Built {len(col_descs)} column descriptions")

    # Load current column mapping
    print(f"\nLoading current column mapping...")
    if not COLUMN_MAPPING_PATH.exists():
        print(f"  ERROR: {COLUMN_MAPPING_PATH} not found. Run build_column_mapping.py first.")
        return

    mapping_df = pd.read_csv(str(COLUMN_MAPPING_PATH), keep_default_na=False)
    print(f"  Loaded {len(mapping_df)} columns")

    # Enrich
    print(f"\nEnriching column mapping...")
    enriched_df = enrich_column_mapping(mapping_df, crosswalk_lookup, feature_labels, line_descs)

    # Generate report
    report = generate_enrichment_report(mapping_df, enriched_df)
    print(f"\n{report}")

    if args.dry_run:
        print("\n[DRY RUN] No files written.")
        return

    # Save enriched mapping
    output_path = COLUMN_MAPPING_PATH
    enriched_df.to_csv(str(output_path), index=False)
    print(f"\nSaved enriched mapping to: {output_path}")

    # Update FILL_LINE_DESCRIPTIONS
    print(f"\nUpdating FILL_LINE_DESCRIPTIONS.csv...")
    n_lines = update_fill_line_descriptions(FILL_LINES_PATH, line_descs, crosswalk_lookup)
    print(f"  Filled {n_lines} line descriptions")

    # Update FILL_COLUMN_HEADERS
    print(f"\nUpdating FILL_COLUMN_HEADERS.csv...")
    n_cols = update_fill_column_headers(FILL_COLS_PATH, col_descs)
    print(f"  Filled {n_cols} column headers")

    # Save report
    report_path = BASE_DIR / "hosp10-extracted" / "ENRICHMENT_REPORT.txt"
    with open(str(report_path), "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")

    # Also copy crosswalk to project for future reference
    crosswalk_dest = BASE_DIR / "hosp10-extracted" / "hcris_crosswalk_reference.csv"
    crosswalk_df.to_csv(str(crosswalk_dest), index=False)
    print(f"Crosswalk reference saved to: {crosswalk_dest}")

    print("\nDone!")


if __name__ == "__main__":
    main()
