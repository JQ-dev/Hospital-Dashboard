"""
Download CMS Hospital Reference Data
=====================================

This script downloads the actual CMS data files that contain:
- CCN codes (CMS Certification Numbers / Facility IDs)
- Hospital names
- Addresses, city, state, zip codes
- NPIs (where available)
- Phone numbers, hospital types, ownership

Data Sources:
1. CMS Hospital General Information (primary source - updated monthly)
2. CMS Provider of Services file (quarterly updates)
3. NPPES NPI Registry (for NPI data)

Usage:
    python scripts/download_cms_reference_data.py [--source all|hospital|pos|npi]
"""

import requests
import pandas as pd
from pathlib import Path
import sys
import logging
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
DATA_DIR = PROJECT_ROOT / 'data' / 'cms_reference_data'

# CMS Data Sources
SOURCES = {
    'hospital_general_info': {
        'name': 'Hospital General Information',
        'url': 'https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0/download?format=csv',
        'filename': 'hospital_general_information.csv',
        'description': 'All Medicare-registered hospitals with CCN, names, addresses, phone, ratings',
        'update_frequency': 'Monthly'
    },
    'pos_hospital': {
        'name': 'Provider of Services - Hospitals',
        'url': 'https://www.cms.gov/files/zip/pos-hospital-provider-dec-2024.zip',
        'filename': 'pos_hospital_current.zip',
        'description': 'Detailed provider characteristics by CCN - quarterly updates',
        'update_frequency': 'Quarterly',
        'note': 'URL may need updating for current quarter'
    }
}


def download_file(url, output_path, description="file"):
    """Download a file with progress indication"""

    logger.info(f"Downloading {description}...")
    logger.info(f"  URL: {url}")

    try:
        response = requests.get(url, timeout=300, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(output_path, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = (downloaded / total_size) * 100
                        logger.info(f"  Progress: {percent:.1f}% ({downloaded / 1024 / 1024:.1f} MB)")

        file_size = output_path.stat().st_size / (1024 * 1024)  # MB
        logger.info(f"  ✓ Downloaded: {output_path.name} ({file_size:.1f} MB)")
        return output_path

    except requests.RequestException as e:
        logger.error(f"  ✗ Download failed: {e}")
        return None


def download_hospital_general_info():
    """
    Download CMS Hospital General Information file

    This is the PRIMARY source for hospital names and addresses.
    Contains: Facility ID (CCN), Name, Address, City, State, ZIP, Phone, Type, Ownership
    """

    source = SOURCES['hospital_general_info']
    output_path = DATA_DIR / source['filename']

    logger.info("="*80)
    logger.info(f"SOURCE 1: {source['name']}")
    logger.info("="*80)
    logger.info(f"Description: {source['description']}")
    logger.info(f"Update Frequency: {source['update_frequency']}")
    logger.info("")

    result = download_file(source['url'], output_path, source['name'])

    if result:
        # Analyze the file
        logger.info("\nAnalyzing downloaded file...")
        try:
            df = pd.read_csv(output_path, nrows=5)

            logger.info(f"  Total columns: {len(df.columns)}")
            logger.info("\n  Column names:")
            for i, col in enumerate(df.columns, 1):
                logger.info(f"    {i:2d}. {col}")

            logger.info("\n  Sample record:")
            if len(df) > 0:
                sample = df.iloc[0]
                key_fields = ['Facility ID', 'Facility Name', 'Address', 'City', 'State', 'ZIP Code',
                             'Phone Number', 'Hospital Type', 'Hospital Ownership']
                for field in key_fields:
                    if field in sample:
                        logger.info(f"    {field:20s}: {sample[field]}")

            # Count total records
            total_records = sum(1 for _ in open(output_path, encoding='utf-8')) - 1
            logger.info(f"\n  Total hospitals: {total_records:,}")

        except Exception as e:
            logger.error(f"  Error analyzing file: {e}")

        return output_path
    else:
        logger.warning("\nManual download instructions:")
        logger.warning("1. Visit: https://data.cms.gov/provider-data/dataset/xubh-q36u")
        logger.warning("2. Click 'Export' button")
        logger.warning("3. Select 'CSV' format")
        logger.warning(f"4. Save to: {DATA_DIR}/")

        return None


def download_pos_hospital():
    """
    Download CMS Provider of Services file (if available)

    Note: The POS file URL changes quarterly. This function attempts
    to download, but may need manual download.
    """

    source = SOURCES['pos_hospital']
    output_path = DATA_DIR / source['filename']

    logger.info("\n" + "="*80)
    logger.info(f"SOURCE 2: {source['name']}")
    logger.info("="*80)
    logger.info(f"Description: {source['description']}")
    logger.info(f"Update Frequency: {source['update_frequency']}")
    logger.info(f"Note: {source['note']}")
    logger.info("")

    result = download_file(source['url'], output_path, source['name'])

    if not result:
        logger.warning("\nPOS file download may require manual steps:")
        logger.warning("1. Visit: https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/Provider-of-Services")
        logger.warning("2. Look for 'Current Files' section")
        logger.warning("3. Download the 'HOSPITAL_Provider' file")
        logger.warning(f"4. Save to: {DATA_DIR}/")
        logger.warning("\nAlternatively:")
        logger.warning("Visit: https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-non-hospital-facilities")

        return None

    # Try to extract if it's a ZIP file
    if result and result.suffix == '.zip':
        logger.info("\nExtracting ZIP file...")
        try:
            with zipfile.ZipFile(result, 'r') as zip_ref:
                # List contents
                logger.info("  ZIP contents:")
                for name in zip_ref.namelist():
                    logger.info(f"    - {name}")

                # Extract all
                zip_ref.extractall(DATA_DIR)
                logger.info(f"  ✓ Extracted to: {DATA_DIR}/")

        except Exception as e:
            logger.error(f"  Error extracting ZIP: {e}")

    return result


def create_ccn_mapping_file():
    """
    Create a simple CCN to hospital name mapping from downloaded files

    This creates an easy-to-use reference file
    """

    logger.info("\n" + "="*80)
    logger.info("CREATING CCN MAPPING FILE")
    logger.info("="*80)

    hospital_info_path = DATA_DIR / 'hospital_general_information.csv'

    if not hospital_info_path.exists():
        logger.error("Hospital General Information file not found. Download it first.")
        return None

    logger.info("Reading Hospital General Information file...")

    try:
        df = pd.read_csv(hospital_info_path)

        # Create simplified mapping
        mapping_columns = {
            'Facility ID': 'CCN',
            'Facility Name': 'Hospital_Name',
            'Address': 'Street_Address',
            'City': 'City',
            'State': 'State',
            'ZIP Code': 'Zip_Code',
            'County Name': 'County',
            'Phone Number': 'Phone',
            'Hospital Type': 'Hospital_Type',
            'Hospital Ownership': 'Ownership'
        }

        # Select and rename columns
        available_cols = [col for col in mapping_columns.keys() if col in df.columns]
        mapping_df = df[available_cols].copy()
        mapping_df.rename(columns=mapping_columns, inplace=True)

        # Clean CCN format (ensure 6 digits)
        if 'CCN' in mapping_df.columns:
            mapping_df['CCN'] = mapping_df['CCN'].astype(str).str.zfill(6)

        # Save
        output_path = DATA_DIR / 'ccn_hospital_mapping.csv'
        mapping_df.to_csv(output_path, index=False)

        logger.info(f"✓ Created CCN mapping file: {output_path}")
        logger.info(f"  Total hospitals: {len(mapping_df):,}")

        # Show sample
        logger.info("\n  Sample records:")
        logger.info(mapping_df.head(5).to_string(index=False))

        # Show statistics
        logger.info("\n  Statistics:")
        logger.info(f"    Unique CCNs: {mapping_df['CCN'].nunique():,}")
        if 'State' in mapping_df.columns:
            logger.info(f"    States represented: {mapping_df['State'].nunique()}")
        if 'Hospital_Type' in mapping_df.columns:
            logger.info(f"\n  Hospital types:")
            type_counts = mapping_df['Hospital_Type'].value_counts()
            for htype, count in type_counts.items():
                logger.info(f"      {htype}: {count:,}")

        return output_path

    except Exception as e:
        logger.error(f"Error creating mapping file: {e}")
        import traceback
        traceback.print_exc()
        return None


def verify_ccn_coverage(mapping_file):
    """
    Check what percentage of HCRIS CCNs are in the CMS reference data

    This helps verify data completeness
    """

    logger.info("\n" + "="*80)
    logger.info("VERIFYING CCN COVERAGE")
    logger.info("="*80)

    # Check if HCRIS data exists
    hcris_data_dir = PROJECT_ROOT / 'data' / 'db_parquets' / 'balance_sheet_long'

    if not hcris_data_dir.exists():
        logger.warning("HCRIS parquet files not found. Skipping coverage verification.")
        logger.warning("Run ETL pipeline first to create parquet files.")
        return

    logger.info("Loading HCRIS CCNs from parquet files...")

    try:
        import duckdb

        con = duckdb.connect(':memory:')

        hcris_ccns = con.execute(f"""
            SELECT DISTINCT Provider_Number as CCN
            FROM read_parquet('{hcris_data_dir}/**/*.parquet', hive_partitioning=1)
            ORDER BY CCN
        """).df()

        logger.info(f"  HCRIS hospitals: {len(hcris_ccns):,}")

        # Load CMS reference data
        logger.info("Loading CMS reference CCNs...")
        cms_ccns = pd.read_csv(mapping_file)

        logger.info(f"  CMS reference hospitals: {len(cms_ccns):,}")

        # Find matches
        hcris_set = set(hcris_ccns['CCN'].astype(str).str.zfill(6))
        cms_set = set(cms_ccns['CCN'].astype(str).str.zfill(6))

        matched = hcris_set & cms_set
        hcris_only = hcris_set - cms_set
        cms_only = cms_set - hcris_set

        logger.info("\n  Coverage Analysis:")
        logger.info(f"    Hospitals in both HCRIS and CMS: {len(matched):,} ({len(matched)/len(hcris_set)*100:.1f}%)")
        logger.info(f"    Hospitals in HCRIS only: {len(hcris_only):,} ({len(hcris_only)/len(hcris_set)*100:.1f}%)")
        logger.info(f"    Hospitals in CMS only: {len(cms_only):,}")

        if hcris_only:
            logger.info("\n  Sample HCRIS hospitals not in CMS reference:")
            for ccn in list(hcris_only)[:10]:
                logger.info(f"      {ccn}")

        con.close()

    except Exception as e:
        logger.error(f"Error verifying coverage: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main execution"""

    import argparse

    parser = argparse.ArgumentParser(description='Download CMS hospital reference data')
    parser.add_argument('--source', choices=['all', 'hospital', 'pos'], default='all',
                       help='Which source to download (default: all)')

    args = parser.parse_args()

    logger.info("="*80)
    logger.info("CMS HOSPITAL REFERENCE DATA DOWNLOADER")
    logger.info("="*80)
    logger.info(f"Output directory: {DATA_DIR}\n")

    # Create data directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    start_time = datetime.now()

    # Download sources
    if args.source in ['all', 'hospital']:
        download_hospital_general_info()

    if args.source in ['all', 'pos']:
        download_pos_hospital()

    # Create mapping file
    logger.info("\n")
    mapping_file = create_ccn_mapping_file()

    # Verify coverage
    if mapping_file:
        verify_ccn_coverage(mapping_file)

    elapsed = datetime.now() - start_time

    logger.info("\n" + "="*80)
    logger.info("DOWNLOAD COMPLETE")
    logger.info("="*80)
    logger.info(f"Time elapsed: {elapsed}")
    logger.info(f"\nFiles saved to: {DATA_DIR}")
    logger.info("\nNext steps:")
    logger.info("1. Review downloaded files in data/cms_reference_data/")
    logger.info("2. Use ccn_hospital_mapping.csv for CCN lookups")
    logger.info("3. Run: python etl/build_hospital_master.py")
    logger.info("4. The build script will automatically use these reference files")


if __name__ == "__main__":
    main()
