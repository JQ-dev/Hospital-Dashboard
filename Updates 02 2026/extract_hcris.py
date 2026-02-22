#!/usr/bin/env python3
"""
HCRIS Hospital Cost Report (Form 2552-10) SAS7BDAT Data Extractor

Reads prds_hosp10_yr*.sas7bdat files and exports them to CSV or Parquet.
Supports extracting individual years, year ranges, or all years at once.

Usage:
    python extract_hcris.py                          # Extract all years to CSV
    python extract_hcris.py --years 2024 2025        # Extract specific years
    python extract_hcris.py --year-range 2020 2025   # Extract a year range
    python extract_hcris.py --format parquet          # Export as Parquet
    python extract_hcris.py --combined                # Combine all years into one file
    python extract_hcris.py --info                    # Show file info without extracting
"""

import argparse
import os
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

# Suppress the SAS column count mismatch warning (known issue with these files)
warnings.filterwarnings("ignore", message="column count mismatch")

DEFAULT_INPUT_DIR = Path(__file__).parent / "hosp10-sas"
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "hosp10-extracted"

# Key identifier / metadata columns that appear at the start of each file
META_COLUMNS = [
    "rpt_rec_num", "prvdr_num", "fi_num", "rpt_stus_cd",
    "fi_creat_dt", "fy_bgn_dt", "fy_end_dt", "util_cd",
    "trnsmtl_num", "state", "st_cty_cd", "census",
    "region", "sub3", "proc_dt", "msa",
]


def discover_files(input_dir: Path) -> dict[int, Path]:
    """Find all prds_hosp10_yr*.sas7bdat files and return {year: path} mapping."""
    files = {}
    for p in sorted(input_dir.glob("prds_hosp10_yr*.sas7bdat")):
        year_str = p.stem.split("yr")[-1]
        try:
            files[int(year_str)] = p
        except ValueError:
            continue
    return files


def read_sas_file(path: Path) -> pd.DataFrame:
    """Read a single SAS7BDAT file into a DataFrame."""
    return pd.read_sas(str(path), format="sas7bdat", encoding="latin1")


def print_file_info(files: dict[int, Path]) -> None:
    """Print summary info for each discovered SAS file."""
    print(f"\n{'Year':<8}{'Rows':>8}{'Cols':>8}{'Size':>12}  Path")
    print("-" * 70)
    total_rows = 0
    for year, path in sorted(files.items()):
        size_mb = path.stat().st_size / (1024 * 1024)
        df = read_sas_file(path)
        total_rows += len(df)
        print(f"{year:<8}{len(df):>8,}{df.shape[1]:>8,}{size_mb:>10.1f} MB  {path.name}")
    print("-" * 70)
    print(f"{'Total':<8}{total_rows:>8,}")
    print()


def extract_year(path: Path, year: int, output_dir: Path, fmt: str) -> Path:
    """Extract a single year file to the chosen format. Returns the output path."""
    print(f"  Reading {path.name} ...", end=" ", flush=True)
    t0 = time.time()
    df = read_sas_file(path)
    df = pd.concat([pd.DataFrame({"year": year}, index=df.index), df], axis=1)
    elapsed_read = time.time() - t0
    print(f"({len(df):,} rows, {df.shape[1]:,} cols in {elapsed_read:.1f}s)")

    out_name = f"hosp10_yr{year}"
    if fmt == "parquet":
        out_path = output_dir / f"{out_name}.parquet"
        print(f"  Writing {out_path.name} ...", end=" ", flush=True)
        t0 = time.time()
        df.to_parquet(str(out_path), index=False, engine="pyarrow")
    else:
        out_path = output_dir / f"{out_name}.csv"
        print(f"  Writing {out_path.name} ...", end=" ", flush=True)
        t0 = time.time()
        df.to_csv(str(out_path), index=False)

    elapsed_write = time.time() - t0
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"({size_mb:.1f} MB in {elapsed_write:.1f}s)")
    return out_path


def extract_combined(paths: dict[int, Path], output_dir: Path, fmt: str) -> Path:
    """Extract and combine multiple years into a single file."""
    frames = []
    for year, path in sorted(paths.items()):
        print(f"  Reading {path.name} ...", end=" ", flush=True)
        t0 = time.time()
        df = read_sas_file(path)
        df = pd.concat([pd.DataFrame({"year": year}, index=df.index), df], axis=1)
        frames.append(df)
        elapsed = time.time() - t0
        print(f"({len(df):,} rows in {elapsed:.1f}s)")

    print("  Concatenating all years ...", end=" ", flush=True)
    t0 = time.time()
    combined = pd.concat(frames, ignore_index=True)
    print(f"({len(combined):,} total rows in {time.time() - t0:.1f}s)")

    years_label = f"{min(paths)}_{max(paths)}"
    out_name = f"hosp10_combined_{years_label}"
    if fmt == "parquet":
        out_path = output_dir / f"{out_name}.parquet"
        print(f"  Writing {out_path.name} ...", end=" ", flush=True)
        t0 = time.time()
        combined.to_parquet(str(out_path), index=False, engine="pyarrow")
    else:
        out_path = output_dir / f"{out_name}.csv"
        print(f"  Writing {out_path.name} ...", end=" ", flush=True)
        t0 = time.time()
        combined.to_csv(str(out_path), index=False)

    elapsed = time.time() - t0
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"({size_mb:.1f} MB in {elapsed:.1f}s)")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Extract HCRIS Hospital Cost Report SAS7BDAT files to CSV or Parquet."
    )
    parser.add_argument(
        "--input-dir", type=Path, default=DEFAULT_INPUT_DIR,
        help="Directory containing prds_hosp10_yr*.sas7bdat files",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help="Directory for extracted output files",
    )
    parser.add_argument(
        "--years", type=int, nargs="+",
        help="Specific years to extract (e.g. --years 2024 2025)",
    )
    parser.add_argument(
        "--year-range", type=int, nargs=2, metavar=("START", "END"),
        help="Range of years to extract (inclusive, e.g. --year-range 2020 2025)",
    )
    parser.add_argument(
        "--format", choices=["csv", "parquet"], default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--combined", action="store_true",
        help="Combine all selected years into a single output file",
    )
    parser.add_argument(
        "--info", action="store_true",
        help="Show file info (row counts, sizes) without extracting",
    )
    parser.add_argument(
        "--columns", nargs="+",
        help="Only extract these columns (plus meta columns are always included)",
    )
    parser.add_argument(
        "--meta-only", action="store_true",
        help="Only extract the 16 metadata/identifier columns",
    )

    args = parser.parse_args()

    # Validate input dir
    if not args.input_dir.is_dir():
        print(f"Error: Input directory not found: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    # Discover files
    all_files = discover_files(args.input_dir)
    if not all_files:
        print(f"Error: No prds_hosp10_yr*.sas7bdat files found in {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(all_files)} SAS files: years {min(all_files)}-{max(all_files)}")

    # Info mode
    if args.info:
        print_file_info(all_files)
        return

    # Determine which years to process
    if args.years:
        selected_years = sorted(args.years)
    elif args.year_range:
        start, end = args.year_range
        selected_years = [y for y in sorted(all_files) if start <= y <= end]
    else:
        selected_years = sorted(all_files.keys())

    # Validate selected years
    missing = [y for y in selected_years if y not in all_files]
    if missing:
        print(f"Warning: No files found for years: {missing}", file=sys.stderr)
    selected = {y: all_files[y] for y in selected_years if y in all_files}
    if not selected:
        print("Error: No valid files to process.", file=sys.stderr)
        sys.exit(1)

    # Check parquet dependency
    if args.format == "parquet":
        try:
            import pyarrow  # noqa: F401
        except ImportError:
            print("Error: pyarrow is required for Parquet output. Install with: pip install pyarrow", file=sys.stderr)
            sys.exit(1)

    # Create output dir
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting {len(selected)} year(s) to {args.format.upper()} -> {args.output_dir}/")
    print()

    t_start = time.time()

    if args.combined:
        out = extract_combined(selected, args.output_dir, args.format)
        output_paths = [out]
    else:
        output_paths = []
        for year, path in sorted(selected.items()):
            out = extract_year(path, year, args.output_dir, args.format)
            output_paths.append(out)
            print()

    total_time = time.time() - t_start
    total_size = sum(p.stat().st_size for p in output_paths) / (1024 * 1024)

    print(f"Done! {len(output_paths)} file(s), {total_size:.1f} MB total in {total_time:.1f}s")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
