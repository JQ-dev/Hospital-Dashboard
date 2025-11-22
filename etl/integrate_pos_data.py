"""
Integrate CMS Provider of Services (POS) Data
==============================================

This script downloads and integrates CMS Provider of Services file data
to enrich hospital_master with:
- Hospital names (official legal names)
- Full addresses (street, city, state, zip)
- Phone numbers
- Certification and termination dates
- Bed counts
- Provider category codes

The POS file is updated quarterly by CMS and contains comprehensive
provider characteristics organized by CMS Certification Number (CCN).

Data Source:
https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-non-hospital-facilities

Usage:
    python etl/integrate_pos_data.py [--download] [--file POS_FILE.csv]

Options:
    --download          Download latest POS file from CMS
    --file FILE.csv     Use a specific POS file (already downloaded)

Without options, script will look for the most recent POS file in data/pos_files/
"""

import duckdb
import pandas as pd
import requests
from pathlib import Path
import sys
import logging
import argparse
from datetime import datetime
import zipfile
import io

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
POS_DIR = PROJECT_ROOT / 'data' / 'pos_files'
DB_PATH = PROJECT_ROOT / 'data' / 'hospital_analytics.duckdb'

# CMS Data.gov API endpoint for POS file
# Note: This may need to be updated as CMS changes their API
CMS_POS_API_URL = "https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0"
CMS_POS_DOWNLOAD_URL = "https://data.cms.gov/provider-data/sites/default/files/archive/Hospitals/2024/hospital_provider.csv"


def download_pos_file():
    """
    Download the latest CMS Provider of Services file

    Returns path to downloaded file
    """
    logger.info("Downloading CMS Provider of Services file...")

    POS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Try to download from CMS data portal
        logger.info(f"  Fetching from: {CMS_POS_DOWNLOAD_URL}")

        response = requests.get(CMS_POS_DOWNLOAD_URL, timeout=60)
        response.raise_for_status()

        # Save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        output_path = POS_DIR / f"pos_hospital_{timestamp}.csv"

        # Check if it's a ZIP file
        if response.headers.get('Content-Type') == 'application/zip':
            logger.info("  Received ZIP file, extracting...")
            z = zipfile.ZipFile(io.BytesIO(response.content))
            # Find CSV file in zip
            csv_files = [f for f in z.namelist() if f.endswith('.csv')]
            if csv_files:
                z.extract(csv_files[0], POS_DIR)
                extracted_path = POS_DIR / csv_files[0]
                extracted_path.rename(output_path)
                logger.info(f"  Extracted to: {output_path}")
            else:
                raise Exception("No CSV file found in ZIP archive")
        else:
            # Direct CSV file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"  Downloaded to: {output_path}")

        file_size = output_path.stat().st_size / (1024 * 1024)  # MB
        logger.info(f"  File size: {file_size:.1f} MB")

        return output_path

    except requests.RequestException as e:
        logger.error(f"  Failed to download POS file: {e}")
        logger.info("\n  Manual download instructions:")
        logger.info("  1. Visit: https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-non-hospital-facilities")
        logger.info("  2. Click 'Export' and download CSV")
        logger.info(f"  3. Save to: {POS_DIR}/")
        logger.info("  4. Run script with: --file <downloaded_file.csv>")
        raise


def find_latest_pos_file():
    """Find the most recent POS file in the POS directory"""

    if not POS_DIR.exists():
        return None

    csv_files = list(POS_DIR.glob("*.csv"))
    if not csv_files:
        return None

    # Return most recently modified file
    latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
    return latest_file


def analyze_pos_file(pos_file_path):
    """
    Analyze POS file structure and show sample data

    POS files can have varying column names across different releases
    """
    logger.info(f"\nAnalyzing POS file: {pos_file_path.name}")

    try:
        # Read first few rows to understand structure
        sample_df = pd.read_csv(pos_file_path, nrows=5, encoding='latin-1')

        logger.info(f"  Columns found: {len(sample_df.columns)}")
        logger.info("\n  Column names:")
        for i, col in enumerate(sample_df.columns, 1):
            logger.info(f"    {i:2d}. {col}")

        logger.info("\n  Sample data (first 2 rows):")
        logger.info(sample_df.head(2).to_string())

        # Count total rows
        total_rows = sum(1 for _ in open(pos_file_path, encoding='latin-1')) - 1  # Exclude header
        logger.info(f"\n  Total records: {total_rows:,}")

        return sample_df.columns.tolist()

    except Exception as e:
        logger.error(f"  Error analyzing POS file: {e}")
        raise


def map_pos_columns(columns):
    """
    Map POS file columns to our schema

    CMS sometimes changes column names, so we handle multiple possible names
    """
    column_map = {}

    # Provider Number (CCN) - various possible names
    ccn_candidates = ['PRVDR_NUM', 'Provider Number', 'PROVIDER_NUMBER', 'CCN']
    for col in columns:
        if col in ccn_candidates or 'PROVIDER' in col.upper() and 'NUM' in col.upper():
            column_map['ccn'] = col
            break

    # Hospital Name - various possible names
    name_candidates = ['PROVIDER_NAME', 'Provider Name', 'FAC_NAME', 'HOSP_NAME']
    for col in columns:
        if col in name_candidates or 'NAME' in col.upper() and 'PROVIDER' in col.upper():
            column_map['hospital_name'] = col
            break

    # Address
    address_candidates = ['STREET_ADDR', 'Street Address', 'ADDRESS', 'ADDR_LINE']
    for col in columns:
        if col in address_candidates or 'STREET' in col.upper() or (
            'ADDR' in col.upper() and 'LINE' not in col.upper() and 'PO' not in col.upper()
        ):
            column_map['street_address'] = col
            break

    # City
    city_candidates = ['CITY', 'City', 'CITY_NAME']
    for col in columns:
        if col in city_candidates or col.upper() == 'CITY':
            column_map['city'] = col
            break

    # State
    state_candidates = ['STATE', 'State', 'STATE_CD', 'STATE_CODE']
    for col in columns:
        if col in state_candidates or 'STATE' in col.upper():
            column_map['state_code'] = col
            break

    # ZIP Code
    zip_candidates = ['ZIP', 'Zip Code', 'ZIP_CODE', 'ZIP_CD']
    for col in columns:
        if col in zip_candidates or 'ZIP' in col.upper():
            column_map['zip_code'] = col
            break

    # County
    county_candidates = ['COUNTY_NAME', 'County', 'CNTY_NAME']
    for col in columns:
        if col in county_candidates or 'COUNTY' in col.upper():
            column_map['county_name'] = col
            break

    # Phone
    phone_candidates = ['PHONE', 'Phone Number', 'PHNE_NUM', 'TELEPHONE']
    for col in columns:
        if col in phone_candidates or 'PHONE' in col.upper() or 'TELE' in col.upper():
            column_map['phone_number'] = col
            break

    # Certification Date
    cert_candidates = ['CERTIFICATION_DATE', 'CERT_DATE', 'PARTICIPATION_DATE']
    for col in columns:
        if col in cert_candidates or ('CERT' in col.upper() and 'DATE' in col.upper()):
            column_map['certification_date'] = col
            break

    # Termination Date
    term_candidates = ['TERMINATION_DATE', 'TERM_DATE', 'TERMNTN_EXPRTN_DT']
    for col in columns:
        if col in term_candidates or ('TERM' in col.upper() and 'DATE' in col.upper()):
            column_map['termination_date'] = col
            break

    # Bed Count
    bed_candidates = ['BED_COUNT', 'Beds', 'TOTAL_BEDS', 'NO_OF_BEDS']
    for col in columns:
        if col in bed_candidates or ('BED' in col.upper() and ('COUNT' in col.upper() or 'TOTAL' in col.upper())):
            column_map['total_beds'] = col
            break

    # Provider Type
    type_candidates = ['PROVIDER_TYPE', 'PRVDR_TYPE_CD', 'TYPE_CODE']
    for col in columns:
        if col in type_candidates or ('PROVIDER' in col.upper() and 'TYPE' in col.upper()):
            column_map['provider_type_code'] = col
            break

    # Provider Category
    cat_candidates = ['PROVIDER_CATEGORY', 'PRVDR_CTGRY_CD', 'CATEGORY_CODE']
    for col in columns:
        if col in cat_candidates or ('PROVIDER' in col.upper() and 'CATEG' in col.upper()):
            column_map['provider_category_code'] = col
            break

    logger.info("\n  Column mapping:")
    for our_field, pos_column in column_map.items():
        logger.info(f"    {our_field:25s} <- {pos_column}")

    missing_fields = []
    for field in ['ccn', 'hospital_name', 'city', 'state_code']:
        if field not in column_map:
            missing_fields.append(field)

    if missing_fields:
        logger.warning(f"\n  WARNING: Required fields not mapped: {missing_fields}")
        logger.warning("  Manual column mapping may be needed")

    return column_map


def integrate_pos_data(pos_file_path, column_map):
    """
    Integrate POS data into hospital_master table

    Updates existing records with POS data
    """
    logger.info("\nIntegrating POS data into hospital_master...")

    con = duckdb.connect(str(DB_PATH))

    try:
        # Load POS file
        logger.info(f"  Loading POS file: {pos_file_path}")
        pos_df = pd.read_csv(pos_file_path, encoding='latin-1', low_memory=False)
        logger.info(f"  Loaded {len(pos_df):,} POS records")

        # Filter to only hospitals (if provider type column available)
        if 'provider_type_code' in column_map:
            original_count = len(pos_df)
            # Keep only hospitals (type codes vary, but typically start with 0 for hospitals)
            pos_df = pos_df[pos_df[column_map['provider_type_code']].astype(str).str.startswith('0', na=False)]
            logger.info(f"  Filtered to {len(pos_df):,} hospital records ({original_count - len(pos_df):,} non-hospital records excluded)")

        # Create a temporary table with POS data
        logger.info("  Creating temporary POS table...")

        # Build column selection for DuckDB
        select_cols = []
        for our_field, pos_column in column_map.items():
            select_cols.append(f'"{pos_column}" as {our_field}')

        # Register pandas DataFrame
        con.register('pos_staging', pos_df)

        # Update hospital_master with POS data
        logger.info("  Updating hospital_master records...")

        updates = []
        for our_field, pos_column in column_map.items():
            if our_field != 'ccn':  # Don't update the primary key
                updates.append(f"{our_field} = pos.{our_field}")

        update_sql = f"""
            UPDATE hospital_master
            SET
                {', '.join(updates)},
                data_source = CASE
                    WHEN hospital_master.data_source = 'HCRIS' THEN 'HCRIS+POS'
                    ELSE 'POS'
                END,
                last_updated = CURRENT_TIMESTAMP
            FROM (
                SELECT {', '.join(select_cols)}
                FROM pos_staging
            ) pos
            WHERE hospital_master.ccn = pos.ccn
        """

        con.execute(update_sql)

        # Get update statistics
        updated_count = con.execute("""
            SELECT COUNT(*)
            FROM hospital_master
            WHERE data_source LIKE '%POS%'
        """).fetchone()[0]

        logger.info(f"  Updated {updated_count:,} hospital records with POS data")

        # Insert any new hospitals from POS that aren't in hospital_master
        logger.info("  Checking for new hospitals in POS file...")

        # First, ensure classify_hospital_type function is available
        from build_hospital_master import classify_hospital_type
        con.create_function("classify_hospital_type", classify_hospital_type)

        insert_sql = f"""
            INSERT INTO hospital_master (
                ccn,
                {', '.join([f for f in column_map.keys() if f != 'ccn'])},
                hospital_type,
                status,
                data_source,
                last_updated,
                created_at,
                updated_at
            )
            SELECT
                pos.ccn,
                {', '.join([f'pos.{f}' for f in column_map.keys() if f != 'ccn'])},
                classify_hospital_type(pos.ccn) as hospital_type,
                CASE
                    WHEN pos.termination_date IS NULL THEN 'Active'
                    ELSE 'Terminated'
                END as status,
                'POS' as data_source,
                CURRENT_TIMESTAMP as last_updated,
                CURRENT_TIMESTAMP as created_at,
                CURRENT_TIMESTAMP as updated_at
            FROM (
                SELECT {', '.join(select_cols)}
                FROM pos_staging
            ) pos
            WHERE NOT EXISTS (
                SELECT 1 FROM hospital_master
                WHERE hospital_master.ccn = pos.ccn
            )
        """

        con.execute(insert_sql)

        # Get insert statistics
        total_hospitals = con.execute("SELECT COUNT(*) FROM hospital_master").fetchone()[0]
        logger.info(f"  Total hospitals in master: {total_hospitals:,}")

        # Recalculate data quality scores
        logger.info("  Recalculating data quality scores...")
        con.execute("""
            UPDATE hospital_master
            SET data_quality_score = (
                50 +  -- base score for having a record
                CASE WHEN npi IS NOT NULL THEN 5 ELSE 0 END +
                CASE WHEN hospital_name IS NOT NULL THEN 15 ELSE 0 END +
                CASE WHEN street_address IS NOT NULL THEN 5 ELSE 0 END +
                CASE WHEN city IS NOT NULL THEN 5 ELSE 0 END +
                CASE WHEN state_code IS NOT NULL THEN 5 ELSE 0 END +
                CASE WHEN zip_code IS NOT NULL THEN 5 ELSE 0 END +
                CASE WHEN phone_number IS NOT NULL THEN 3 ELSE 0 END +
                CASE WHEN hospital_type IS NOT NULL AND hospital_type != 'Unknown' THEN 5 ELSE 0 END +
                CASE WHEN ownership_type IS NOT NULL THEN 3 ELSE 0 END +
                CASE WHEN certification_date IS NOT NULL THEN 2 ELSE 0 END +
                CASE WHEN total_beds IS NOT NULL THEN 2 ELSE 0 END
            )
        """)

        # Show quality improvement
        avg_quality = con.execute("SELECT ROUND(AVG(data_quality_score), 1) FROM hospital_master").fetchone()[0]
        logger.info(f"  New average data quality score: {avg_quality}/100")

        # Show sample of enriched data
        logger.info("\n  Sample enriched hospital records:")
        sample = con.execute("""
            SELECT
                ccn,
                hospital_name,
                city,
                state_code,
                total_beds,
                data_quality_score
            FROM hospital_master
            WHERE data_source LIKE '%POS%'
            ORDER BY data_quality_score DESC
            LIMIT 5
        """).df()
        logger.info(sample.to_string(index=False))

        # Export updated master
        logger.info("\n  Exporting updated hospital_master...")
        export_dir = PROJECT_ROOT / 'data' / 'hospital_master_exports'
        export_dir.mkdir(parents=True, exist_ok=True)

        master_df = con.execute("SELECT * FROM hospital_master ORDER BY ccn").df()
        master_path = export_dir / 'hospital_master_with_pos.csv'
        master_df.to_csv(master_path, index=False)
        logger.info(f"  Exported to: {master_path}")

        logger.info("\n  [SUCCESS] POS data integration complete!")

    except Exception as e:
        logger.error(f"  Error integrating POS data: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        con.close()


def main():
    """Main execution function"""

    parser = argparse.ArgumentParser(
        description='Integrate CMS Provider of Services data into hospital master table'
    )
    parser.add_argument('--download', action='store_true',
                        help='Download latest POS file from CMS')
    parser.add_argument('--file', type=str,
                        help='Path to specific POS CSV file to use')

    args = parser.parse_args()

    logger.info("="*80)
    logger.info("CMS PROVIDER OF SERVICES (POS) DATA INTEGRATION")
    logger.info("="*80)
    logger.info(f"Database: {DB_PATH}\n")

    # Determine which POS file to use
    pos_file = None

    if args.file:
        # User specified a file
        pos_file = Path(args.file)
        if not pos_file.exists():
            logger.error(f"File not found: {pos_file}")
            sys.exit(1)
        logger.info(f"Using specified file: {pos_file}")

    elif args.download:
        # Download latest file
        try:
            pos_file = download_pos_file()
        except Exception as e:
            logger.error("Download failed. Please download manually and use --file option.")
            sys.exit(1)

    else:
        # Look for most recent file in POS directory
        pos_file = find_latest_pos_file()
        if pos_file:
            logger.info(f"Found POS file: {pos_file}")
        else:
            logger.warning("No POS file found in data/pos_files/")
            logger.info("\nOptions:")
            logger.info("1. Download automatically: python etl/integrate_pos_data.py --download")
            logger.info("2. Use existing file: python etl/integrate_pos_data.py --file <path>")
            sys.exit(1)

    # Analyze POS file structure
    columns = analyze_pos_file(pos_file)

    # Map POS columns to our schema
    column_map = map_pos_columns(columns)

    # Check if we have minimum required fields
    if 'ccn' not in column_map:
        logger.error("\nERROR: Could not identify CCN/Provider Number column in POS file")
        logger.error("Please check the POS file format or update column mapping logic")
        sys.exit(1)

    # Integrate the data
    integrate_pos_data(pos_file, column_map)

    logger.info("\n" + "="*80)
    logger.info("[SUCCESS] POS data integration completed successfully!")
    logger.info("="*80)
    logger.info("\nNext steps:")
    logger.info("1. Review enriched data: data/hospital_master_exports/hospital_master_with_pos.csv")
    logger.info("2. Create dashboard UI to display hospital data table")
    logger.info("3. Add hospital group/system affiliation data if available")


if __name__ == "__main__":
    main()
