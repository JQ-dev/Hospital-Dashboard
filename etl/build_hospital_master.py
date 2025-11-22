"""
Build Hospital Master Data Tables
==================================

This script creates comprehensive hospital master data tables with:
1. hospital_master - Current hospital information
2. hospital_identifiers_history - Track name/NPI/CCN changes
3. hospital_addresses_history - Track address changes
4. hospital_system_membership - Track system affiliations
5. hospital_annual_snapshot - Annual data from HCRIS

Data Sources (Phase 1 - HCRIS Only):
- Existing parquet files in data/db_parquets/
- Derives hospital information from fiscal year data
- Detects changes by comparing across years

Future Phases:
- Phase 2: Integrate CMS Provider of Services (POS) file
- Phase 3: Historical POS data for complete change tracking
- Phase 4: Hospital system affiliation data

Usage:
    python etl/build_hospital_master.py
"""

import duckdb
import pandas as pd
from pathlib import Path
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'db_parquets'
DB_PATH = PROJECT_ROOT / 'data' / 'hospital_analytics.duckdb'


def classify_hospital_type(ccn):
    """
    Classify hospital type based on CCN range

    CCN Format: XXYYYY where XX = state, YYYY = provider number
    Provider number ranges indicate hospital type
    """
    try:
        provider_num = int(str(ccn)[2:])  # Last 4 digits

        if 1 <= provider_num <= 899:
            return 'Short Term Acute Care'
        elif 1300 <= provider_num <= 1399:
            return 'Critical Access'
        elif 2000 <= provider_num <= 2299:
            return 'Long Term'
        elif 3025 <= provider_num <= 3099:
            return 'Rehabilitation'
        elif 3300 <= provider_num <= 3399:
            return "Children's"
        elif 4000 <= provider_num <= 4499:
            return 'Psychiatric'
        else:
            return 'Other'
    except:
        return 'Unknown'


def create_schema(con):
    """Create the hospital master data schema"""

    logger.info("Creating hospital master data schema...")

    # Table 1: hospital_master
    logger.info("  Creating hospital_master table...")
    con.execute("""
        CREATE TABLE IF NOT EXISTS hospital_master (
            -- Primary Identifiers
            ccn VARCHAR(6) PRIMARY KEY,
            npi VARCHAR(10),

            -- Current Hospital Information
            hospital_name VARCHAR(255),
            hospital_name_dba VARCHAR(255),

            -- Address Information (to be populated from POS file)
            street_address VARCHAR(255),
            city VARCHAR(100),
            state_code VARCHAR(2),
            zip_code VARCHAR(10),
            county_code VARCHAR(5),
            county_name VARCHAR(100),

            -- Contact Information
            phone_number VARCHAR(20),

            -- Hospital Classification
            hospital_type VARCHAR(50),
            provider_type_code VARCHAR(10),
            provider_category_code VARCHAR(10),

            -- Ownership and Control
            ownership_type VARCHAR(50),
            ownership_type_code VARCHAR(5),

            -- Hospital System/Group Affiliation
            hospital_system_id VARCHAR(20),
            hospital_system_name VARCHAR(255),
            parent_ccn VARCHAR(6),

            -- Operational Status
            status VARCHAR(20),
            certification_date DATE,
            termination_date DATE,

            -- Capacity
            total_beds INTEGER,
            icu_beds INTEGER,

            -- HCRIS Reporting Info
            first_fiscal_year INTEGER,
            last_fiscal_year INTEGER,
            total_years_reported INTEGER,
            last_report_status VARCHAR(20),
            geographic_code VARCHAR(10),

            -- Data Quality and Metadata
            data_source VARCHAR(50),
            last_updated TIMESTAMP,
            data_quality_score INTEGER,

            -- Audit Fields
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 2: hospital_identifiers_history
    logger.info("  Creating hospital_identifiers_history table...")
    con.execute("""
        CREATE TABLE IF NOT EXISTS hospital_identifiers_history (
            history_id INTEGER PRIMARY KEY,
            ccn VARCHAR(6) NOT NULL,

            -- Change Tracking
            change_type VARCHAR(50),
            change_date DATE,
            fiscal_year INTEGER,

            -- Previous Values
            old_value VARCHAR(255),
            new_value VARCHAR(255),
            field_name VARCHAR(50),

            -- Merger/Acquisition Tracking
            related_ccn VARCHAR(6),
            merger_type VARCHAR(50),

            -- Documentation
            change_reason VARCHAR(500),
            source_document VARCHAR(255),

            -- Audit
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 3: hospital_addresses_history
    logger.info("  Creating hospital_addresses_history table...")
    con.execute("""
        CREATE TABLE IF NOT EXISTS hospital_addresses_history (
            address_history_id INTEGER PRIMARY KEY,
            ccn VARCHAR(6) NOT NULL,

            -- Address Information
            street_address VARCHAR(255),
            city VARCHAR(100),
            state_code VARCHAR(2),
            zip_code VARCHAR(10),
            county_code VARCHAR(5),

            -- Validity Period
            effective_date DATE,
            end_date DATE,
            is_current BOOLEAN DEFAULT FALSE,

            -- Address Type
            address_type VARCHAR(50),

            -- Audit
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 4: hospital_system_membership
    logger.info("  Creating hospital_system_membership table...")
    con.execute("""
        CREATE TABLE IF NOT EXISTS hospital_system_membership (
            membership_id INTEGER PRIMARY KEY,
            ccn VARCHAR(6) NOT NULL,

            -- System Information
            hospital_system_id VARCHAR(20),
            hospital_system_name VARCHAR(255),
            system_type VARCHAR(50),

            -- Membership Period
            membership_start_date DATE,
            membership_end_date DATE,
            is_current BOOLEAN DEFAULT FALSE,

            -- Additional Context
            ownership_percentage DECIMAL(5,2),
            relationship_type VARCHAR(50),

            -- Audit
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 5: hospital_annual_snapshot
    logger.info("  Creating hospital_annual_snapshot table...")
    con.execute("""
        CREATE TABLE IF NOT EXISTS hospital_annual_snapshot (
            snapshot_id INTEGER PRIMARY KEY,
            ccn VARCHAR(6) NOT NULL,
            fiscal_year INTEGER NOT NULL,

            -- Identifiers at this point in time
            npi VARCHAR(10),
            hospital_name VARCHAR(255),

            -- From HCRIS RPT file
            control_type VARCHAR(50),
            report_status VARCHAR(20),
            fy_begin_date DATE,
            fy_end_date DATE,
            geographic_code VARCHAR(10),

            -- Operational Metrics (summary - to be added)
            total_beds INTEGER,
            total_discharges INTEGER,
            total_patient_days INTEGER,

            -- Financial Summary (from KPIs if available)
            total_revenue DECIMAL(15,2),
            total_assets DECIMAL(15,2),
            operating_margin_pct DECIMAL(5,2),

            -- Status
            was_operational BOOLEAN DEFAULT TRUE,

            -- Audit
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(ccn, fiscal_year)
        )
    """)

    # Create indexes
    logger.info("  Creating indexes...")

    # hospital_master indexes
    con.execute("CREATE INDEX IF NOT EXISTS idx_hospital_master_npi ON hospital_master(npi)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_hospital_master_state ON hospital_master(state_code)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_hospital_master_type ON hospital_master(hospital_type)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_hospital_master_status ON hospital_master(status)")

    # hospital_identifiers_history indexes
    con.execute("CREATE INDEX IF NOT EXISTS idx_identifiers_history_ccn ON hospital_identifiers_history(ccn)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_identifiers_history_type ON hospital_identifiers_history(change_type)")

    # hospital_annual_snapshot indexes
    con.execute("CREATE INDEX IF NOT EXISTS idx_annual_snapshot_ccn ON hospital_annual_snapshot(ccn)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_annual_snapshot_fy ON hospital_annual_snapshot(fiscal_year)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_annual_snapshot_ccn_fy ON hospital_annual_snapshot(ccn, fiscal_year)")

    logger.info("  Schema creation complete!")


def populate_annual_snapshots(con):
    """
    Populate hospital_annual_snapshot from existing parquet files

    Extract all hospital identifiers and metadata from balance sheet parquet files
    """
    logger.info("\nPopulating hospital_annual_snapshot from parquet files...")

    balance_sheet_path = DATA_DIR / 'balance_sheet_long'

    if not balance_sheet_path.exists():
        logger.warning(f"  Balance sheet parquet files not found at {balance_sheet_path}")
        logger.warning("  Skipping annual snapshots - run ETL pipeline first to create parquet files")
        return

    # Extract unique hospital-year combinations from balance sheet data
    con.execute(f"""
        INSERT OR REPLACE INTO hospital_annual_snapshot (
            snapshot_id,
            ccn,
            fiscal_year,
            npi,
            control_type,
            report_status,
            fy_begin_date,
            fy_end_date,
            geographic_code,
            was_operational,
            recorded_at
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY Provider_Number, Fiscal_Year) as snapshot_id,
            Provider_Number as ccn,
            Fiscal_Year as fiscal_year,
            NPI as npi,
            Control_Type as control_type,
            Report_Status as report_status,
            FY_Begin as fy_begin_date,
            FY_End as fy_end_date,
            Geographic_Code as geographic_code,
            TRUE as was_operational,
            CURRENT_TIMESTAMP as recorded_at
        FROM (
            SELECT DISTINCT
                Provider_Number,
                Fiscal_Year,
                NPI,
                Control_Type,
                Report_Status,
                MIN(FY_Begin) as FY_Begin,
                MAX(FY_End) as FY_End,
                Geographic_Code
            FROM read_parquet('{balance_sheet_path}/**/*.parquet', hive_partitioning=1)
            GROUP BY Provider_Number, Fiscal_Year, NPI, Control_Type, Report_Status, Geographic_Code
        ) snapshots
        ORDER BY Provider_Number, Fiscal_Year
    """)

    count = con.execute("SELECT COUNT(*) FROM hospital_annual_snapshot").fetchone()[0]
    logger.info(f"  Created {count:,} annual snapshot records")

    # Show sample
    sample = con.execute("""
        SELECT ccn, fiscal_year, npi, control_type
        FROM hospital_annual_snapshot
        ORDER BY ccn, fiscal_year
        LIMIT 5
    """).df()
    logger.info("\n  Sample records:")
    logger.info(sample.to_string(index=False))


def populate_hospital_master(con):
    """
    Populate hospital_master from annual snapshots

    Takes the most recent fiscal year data for each hospital
    """
    logger.info("\nPopulating hospital_master from annual snapshots...")

    con.execute("""
        INSERT OR REPLACE INTO hospital_master (
            ccn,
            npi,
            state_code,
            hospital_type,
            ownership_type,
            status,
            first_fiscal_year,
            last_fiscal_year,
            total_years_reported,
            last_report_status,
            geographic_code,
            data_source,
            last_updated,
            created_at,
            updated_at
        )
        SELECT
            ccn,
            npi,
            SUBSTRING(ccn, 1, 2) as state_code,
            hospital_type,
            ownership_type,
            CASE
                WHEN last_fiscal_year >= 2023 THEN 'Active'
                WHEN last_fiscal_year >= 2021 THEN 'Possibly Closed'
                ELSE 'Likely Closed'
            END as status,
            first_fiscal_year,
            last_fiscal_year,
            total_years_reported,
            last_report_status,
            geographic_code,
            'HCRIS' as data_source,
            CURRENT_TIMESTAMP as last_updated,
            CURRENT_TIMESTAMP as created_at,
            CURRENT_TIMESTAMP as updated_at
        FROM (
            SELECT
                ccn,
                -- Use most recent NPI
                LAST_VALUE(npi) OVER (
                    PARTITION BY ccn
                    ORDER BY fiscal_year
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) as npi,
                -- Use most recent control type
                LAST_VALUE(control_type) OVER (
                    PARTITION BY ccn
                    ORDER BY fiscal_year
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) as ownership_type,
                -- Use most recent report status
                LAST_VALUE(report_status) OVER (
                    PARTITION BY ccn
                    ORDER BY fiscal_year
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) as last_report_status,
                -- Use most recent geographic code
                LAST_VALUE(geographic_code) OVER (
                    PARTITION BY ccn
                    ORDER BY fiscal_year
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) as geographic_code,
                MIN(fiscal_year) OVER (PARTITION BY ccn) as first_fiscal_year,
                MAX(fiscal_year) OVER (PARTITION BY ccn) as last_fiscal_year,
                COUNT(*) OVER (PARTITION BY ccn) as total_years_reported
            FROM hospital_annual_snapshot
        ) hospital_summary
        CROSS JOIN LATERAL (
            SELECT classify_hospital_type(hospital_summary.ccn) as hospital_type
        ) classification
        GROUP BY ccn
        ORDER BY ccn
    """, {"classify_hospital_type": classify_hospital_type})

    count = con.execute("SELECT COUNT(*) FROM hospital_master").fetchone()[0]
    logger.info(f"  Created {count:,} hospital master records")

    # Show summary by status
    status_summary = con.execute("""
        SELECT
            status,
            COUNT(*) as hospital_count
        FROM hospital_master
        GROUP BY status
        ORDER BY hospital_count DESC
    """).df()
    logger.info("\n  Hospitals by status:")
    logger.info(status_summary.to_string(index=False))

    # Show summary by type
    type_summary = con.execute("""
        SELECT
            hospital_type,
            COUNT(*) as hospital_count
        FROM hospital_master
        GROUP BY hospital_type
        ORDER BY hospital_count DESC
    """).df()
    logger.info("\n  Hospitals by type:")
    logger.info(type_summary.to_string(index=False))


def detect_identifier_changes(con):
    """
    Detect NPI and name changes by comparing annual snapshots

    Populates hospital_identifiers_history with detected changes
    """
    logger.info("\nDetecting identifier changes...")

    # Detect NPI changes
    logger.info("  Detecting NPI changes...")
    con.execute("""
        INSERT INTO hospital_identifiers_history (
            history_id,
            ccn,
            change_type,
            change_date,
            fiscal_year,
            old_value,
            new_value,
            field_name,
            change_reason,
            source_document,
            recorded_at
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY ccn, fiscal_year) as history_id,
            ccn,
            'NPI_CHANGE' as change_type,
            fy_end_date as change_date,
            fiscal_year,
            old_npi as old_value,
            new_npi as new_value,
            'npi' as field_name,
            'Detected from fiscal year comparison' as change_reason,
            'HCRIS Annual Snapshots' as source_document,
            CURRENT_TIMESTAMP as recorded_at
        FROM (
            SELECT
                ccn,
                fiscal_year,
                npi as new_npi,
                fy_end_date,
                LAG(npi) OVER (PARTITION BY ccn ORDER BY fiscal_year) as old_npi
            FROM hospital_annual_snapshot
            WHERE npi IS NOT NULL
        ) npi_changes
        WHERE old_npi IS NOT NULL
          AND old_npi != new_npi
        ORDER BY ccn, fiscal_year
    """)

    npi_changes = con.execute("SELECT COUNT(*) FROM hospital_identifiers_history WHERE change_type = 'NPI_CHANGE'").fetchone()[0]
    logger.info(f"  Found {npi_changes} NPI changes")

    # Detect control type changes (ownership changes)
    logger.info("  Detecting ownership/control type changes...")
    con.execute("""
        INSERT INTO hospital_identifiers_history (
            history_id,
            ccn,
            change_type,
            change_date,
            fiscal_year,
            old_value,
            new_value,
            field_name,
            change_reason,
            source_document,
            recorded_at
        )
        SELECT
            ROW_NUMBER() OVER (ORDER BY ccn, fiscal_year) + (SELECT COALESCE(MAX(history_id), 0) FROM hospital_identifiers_history) as history_id,
            ccn,
            'OWNERSHIP_CHANGE' as change_type,
            fy_end_date as change_date,
            fiscal_year,
            old_control_type as old_value,
            new_control_type as new_value,
            'control_type' as field_name,
            'Detected from fiscal year comparison' as change_reason,
            'HCRIS Annual Snapshots' as source_document,
            CURRENT_TIMESTAMP as recorded_at
        FROM (
            SELECT
                ccn,
                fiscal_year,
                control_type as new_control_type,
                fy_end_date,
                LAG(control_type) OVER (PARTITION BY ccn ORDER BY fiscal_year) as old_control_type
            FROM hospital_annual_snapshot
            WHERE control_type IS NOT NULL
        ) control_changes
        WHERE old_control_type IS NOT NULL
          AND old_control_type != new_control_type
        ORDER BY ccn, fiscal_year
    """)

    ownership_changes = con.execute("SELECT COUNT(*) FROM hospital_identifiers_history WHERE change_type = 'OWNERSHIP_CHANGE'").fetchone()[0]
    logger.info(f"  Found {ownership_changes} ownership/control type changes")

    total_changes = con.execute("SELECT COUNT(*) FROM hospital_identifiers_history").fetchone()[0]
    logger.info(f"\n  Total identifier changes detected: {total_changes}")

    if total_changes > 0:
        # Show sample changes
        sample = con.execute("""
            SELECT ccn, change_type, fiscal_year, old_value, new_value
            FROM hospital_identifiers_history
            ORDER BY change_date DESC
            LIMIT 10
        """).df()
        logger.info("\n  Sample identifier changes:")
        logger.info(sample.to_string(index=False))


def calculate_data_quality_scores(con):
    """
    Calculate data quality scores for hospital_master records

    Score based on completeness of key fields
    """
    logger.info("\nCalculating data quality scores...")

    con.execute("""
        UPDATE hospital_master
        SET data_quality_score = (
            -- Required fields (always present)
            100 +  -- ccn

            -- Optional fields that improve quality
            CASE WHEN npi IS NOT NULL THEN 15 ELSE 0 END +
            CASE WHEN hospital_name IS NOT NULL THEN 15 ELSE 0 END +
            CASE WHEN state_code IS NOT NULL THEN 10 ELSE 0 END +
            CASE WHEN hospital_type IS NOT NULL AND hospital_type != 'Unknown' THEN 10 ELSE 0 END +
            CASE WHEN ownership_type IS NOT NULL THEN 10 ELSE 0 END +
            CASE WHEN street_address IS NOT NULL THEN 10 ELSE 0 END +
            CASE WHEN city IS NOT NULL THEN 10 ELSE 0 END +
            CASE WHEN zip_code IS NOT NULL THEN 10 ELSE 0 END +
            CASE WHEN total_beds IS NOT NULL THEN 5 ELSE 0 END +
            CASE WHEN hospital_system_name IS NOT NULL THEN 5 ELSE 0 END
        ) / 2  -- Divide by 2 to get score out of 100
    """)

    # Show quality score distribution
    quality_dist = con.execute("""
        SELECT
            CASE
                WHEN data_quality_score >= 80 THEN 'Excellent (80-100)'
                WHEN data_quality_score >= 60 THEN 'Good (60-79)'
                WHEN data_quality_score >= 40 THEN 'Fair (40-59)'
                ELSE 'Poor (<40)'
            END as quality_category,
            COUNT(*) as hospital_count,
            ROUND(AVG(data_quality_score), 1) as avg_score
        FROM hospital_master
        GROUP BY quality_category
        ORDER BY avg_score DESC
    """).df()

    logger.info("\n  Data quality distribution:")
    logger.info(quality_dist.to_string(index=False))

    avg_score = con.execute("SELECT ROUND(AVG(data_quality_score), 1) FROM hospital_master").fetchone()[0]
    logger.info(f"\n  Overall average quality score: {avg_score}/100")


def create_summary_views(con):
    """Create useful views for querying hospital master data"""

    logger.info("\nCreating summary views...")

    # View: Active hospitals with complete info
    con.execute("""
        CREATE OR REPLACE VIEW hospital_master_active AS
        SELECT *
        FROM hospital_master
        WHERE status = 'Active'
        ORDER BY state_code, ccn
    """)

    # View: Hospital changes summary
    con.execute("""
        CREATE OR REPLACE VIEW hospital_changes_summary AS
        SELECT
            h.ccn,
            h.hospital_name,
            h.state_code,
            h.hospital_type,
            COUNT(DISTINCT ih.history_id) as total_changes,
            COUNT(DISTINCT CASE WHEN ih.change_type = 'NPI_CHANGE' THEN ih.history_id END) as npi_changes,
            COUNT(DISTINCT CASE WHEN ih.change_type = 'OWNERSHIP_CHANGE' THEN ih.history_id END) as ownership_changes,
            MIN(ih.change_date) as first_change_date,
            MAX(ih.change_date) as last_change_date
        FROM hospital_master h
        LEFT JOIN hospital_identifiers_history ih ON h.ccn = ih.ccn
        GROUP BY h.ccn, h.hospital_name, h.state_code, h.hospital_type
        HAVING total_changes > 0
        ORDER BY total_changes DESC
    """)

    # View: Hospitals with complete time series data
    con.execute("""
        CREATE OR REPLACE VIEW hospital_complete_timeseries AS
        SELECT
            h.ccn,
            h.hospital_name,
            h.state_code,
            h.hospital_type,
            h.first_fiscal_year,
            h.last_fiscal_year,
            h.total_years_reported,
            CASE
                WHEN h.total_years_reported = (h.last_fiscal_year - h.first_fiscal_year + 1) THEN 'Complete'
                ELSE 'Gaps'
            END as timeseries_completeness
        FROM hospital_master h
        WHERE h.status = 'Active'
        ORDER BY h.total_years_reported DESC
    """)

    logger.info("  Created 3 summary views")


def export_to_csv(con):
    """Export hospital master tables to CSV for easy review"""

    logger.info("\nExporting tables to CSV...")

    export_dir = PROJECT_ROOT / 'data' / 'hospital_master_exports'
    export_dir.mkdir(parents=True, exist_ok=True)

    # Export hospital_master
    master_df = con.execute("SELECT * FROM hospital_master ORDER BY ccn").df()
    master_path = export_dir / 'hospital_master.csv'
    master_df.to_csv(master_path, index=False)
    logger.info(f"  Exported hospital_master to {master_path}")

    # Export hospital_annual_snapshot
    snapshot_df = con.execute("SELECT * FROM hospital_annual_snapshot ORDER BY ccn, fiscal_year").df()
    snapshot_path = export_dir / 'hospital_annual_snapshot.csv'
    snapshot_df.to_csv(snapshot_path, index=False)
    logger.info(f"  Exported hospital_annual_snapshot to {snapshot_path}")

    # Export hospital_identifiers_history
    history_df = con.execute("SELECT * FROM hospital_identifiers_history ORDER BY ccn, change_date").df()
    if len(history_df) > 0:
        history_path = export_dir / 'hospital_identifiers_history.csv'
        history_df.to_csv(history_path, index=False)
        logger.info(f"  Exported hospital_identifiers_history to {history_path}")

    # Export active hospitals view
    active_df = con.execute("SELECT * FROM hospital_master_active").df()
    active_path = export_dir / 'hospital_master_active.csv'
    active_df.to_csv(active_path, index=False)
    logger.info(f"  Exported hospital_master_active to {active_path}")

    logger.info(f"\n  All exports saved to {export_dir}")


def main():
    """Main execution function"""

    logger.info("="*80)
    logger.info("HOSPITAL MASTER DATA TABLE BUILDER")
    logger.info("="*80)
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Data Source: {DATA_DIR}")
    logger.info("")

    start_time = datetime.now()

    # Check if database exists
    if not DB_PATH.exists():
        logger.warning(f"Database not found at {DB_PATH}")
        logger.warning("Creating new database...")
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    con = duckdb.connect(str(DB_PATH))

    # Register classify_hospital_type function
    con.create_function("classify_hospital_type", classify_hospital_type)

    try:
        # Step 1: Create schema
        create_schema(con)

        # Step 2: Populate annual snapshots from parquet files
        populate_annual_snapshots(con)

        # Step 3: Create hospital_master from snapshots
        populate_hospital_master(con)

        # Step 4: Detect identifier changes
        detect_identifier_changes(con)

        # Step 5: Calculate data quality scores
        calculate_data_quality_scores(con)

        # Step 6: Create summary views
        create_summary_views(con)

        # Step 7: Export to CSV
        export_to_csv(con)

        # Final summary
        logger.info("\n" + "="*80)
        logger.info("SUMMARY")
        logger.info("="*80)

        summary = con.execute("""
            SELECT
                (SELECT COUNT(*) FROM hospital_master) as total_hospitals,
                (SELECT COUNT(*) FROM hospital_master WHERE status = 'Active') as active_hospitals,
                (SELECT COUNT(DISTINCT ccn) FROM hospital_annual_snapshot) as hospitals_with_data,
                (SELECT COUNT(*) FROM hospital_annual_snapshot) as total_snapshots,
                (SELECT COUNT(*) FROM hospital_identifiers_history) as total_changes,
                (SELECT ROUND(AVG(data_quality_score), 1) FROM hospital_master) as avg_quality_score
        """).fetchone()

        logger.info(f"Total Hospitals: {summary[0]:,}")
        logger.info(f"Active Hospitals: {summary[1]:,}")
        logger.info(f"Hospitals with Data: {summary[2]:,}")
        logger.info(f"Annual Snapshots: {summary[3]:,}")
        logger.info(f"Identifier Changes Detected: {summary[4]:,}")
        logger.info(f"Average Data Quality Score: {summary[5]}/100")

        elapsed = datetime.now() - start_time
        logger.info(f"\nTotal processing time: {elapsed}")
        logger.info("="*80)
        logger.info("[SUCCESS] Hospital master data tables created successfully!")
        logger.info("="*80)

        logger.info("\nNext steps:")
        logger.info("1. Review exported CSV files in data/hospital_master_exports/")
        logger.info("2. Download CMS Provider of Services file to add hospital names and addresses")
        logger.info("3. Run: python etl/integrate_pos_data.py (to be created)")

    except Exception as e:
        logger.error(f"Error building hospital master data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        con.close()


if __name__ == "__main__":
    main()
