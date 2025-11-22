# Hospital Master Data Table Schema

## Overview
This document defines the schema for a comprehensive hospital master data table that tracks all hospital identifiers, demographics, and historical changes.

## Data Sources

### 1. CMS HCRIS (Hospital Cost Report Information System)
**Already in use - RPT files**
- Provider_Number (CCN) - 6-digit CMS Certification Number
- NPI (National Provider Identifier)
- Control_Type (Ownership: Government, Voluntary Non-Profit, Proprietary)
- Report_Status
- Fiscal_Year dates (FY_Begin, FY_End)
- Geographic_Code

### 2. CMS Provider of Services (POS) File
**To be integrated - Updates quarterly**
- Hospital name
- Address, City, State, Zip Code
- Certification dates (initial and current)
- Termination dates
- Accreditation information
- Provider category codes
- Bed counts
- Services provided

Source: [CMS POS File](https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-hospital-non-hospital-facilities)

### 3. NPPES NPI Registry (Optional enhancement)
**Future integration**
- NPI demographic information
- Practice addresses (mailing and physical)
- Taxonomy codes
- Provider enumeration dates

## Database Tables

### Table 1: `hospital_master`
**Primary reference table with current hospital information**

```sql
CREATE TABLE hospital_master (
    -- Primary Identifiers
    ccn VARCHAR(6) PRIMARY KEY,                 -- CMS Certification Number
    npi VARCHAR(10),                            -- National Provider Identifier

    -- Current Hospital Information
    hospital_name VARCHAR(255),                 -- Current legal name
    hospital_name_dba VARCHAR(255),             -- Doing Business As name

    -- Address Information
    street_address VARCHAR(255),
    city VARCHAR(100),
    state_code VARCHAR(2),
    zip_code VARCHAR(10),
    county_code VARCHAR(5),
    county_name VARCHAR(100),

    -- Contact Information
    phone_number VARCHAR(20),

    -- Hospital Classification
    hospital_type VARCHAR(50),                  -- Derived from CCN (Short Term, Critical Access, etc.)
    provider_type_code VARCHAR(10),             -- CMS provider type
    provider_category_code VARCHAR(10),         -- CMS provider category

    -- Ownership and Control
    ownership_type VARCHAR(50),                 -- Control_Type from HCRIS
    ownership_type_code VARCHAR(5),

    -- Hospital System/Group Affiliation
    hospital_system_id VARCHAR(20),             -- If part of a system
    hospital_system_name VARCHAR(255),          -- System/network name
    parent_ccn VARCHAR(6),                      -- Parent organization CCN if applicable

    -- Operational Status
    status VARCHAR(20),                         -- Active, Closed, Merged, etc.
    certification_date DATE,                    -- Initial Medicare certification
    termination_date DATE,                      -- If closed/terminated

    -- Capacity
    total_beds INTEGER,
    icu_beds INTEGER,

    -- Data Quality and Metadata
    data_source VARCHAR(50),                    -- Primary data source
    last_updated TIMESTAMP,                     -- Last update to this record
    data_quality_score INTEGER,                 -- 0-100 completeness score

    -- Audit Fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table 2: `hospital_identifiers_history`
**Tracks all changes to hospital identifiers (CCN, NPI, names)**

```sql
CREATE TABLE hospital_identifiers_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ccn VARCHAR(6) NOT NULL,                    -- References hospital_master

    -- Change Tracking
    change_type VARCHAR(50),                    -- NAME_CHANGE, NPI_CHANGE, CCN_MERGE, etc.
    change_date DATE,                           -- When change occurred
    fiscal_year INTEGER,                        -- Fiscal year of change

    -- Previous Values
    old_value VARCHAR(255),                     -- Previous identifier/name
    new_value VARCHAR(255),                     -- New identifier/name
    field_name VARCHAR(50),                     -- Which field changed

    -- Merger/Acquisition Tracking
    related_ccn VARCHAR(6),                     -- If merger, the other CCN involved
    merger_type VARCHAR(50),                    -- Acquired, Merged_Into, Split_From

    -- Documentation
    change_reason VARCHAR(500),                 -- Reason for change if known
    source_document VARCHAR(255),               -- Source of information

    -- Audit
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ccn) REFERENCES hospital_master(ccn)
);
```

### Table 3: `hospital_addresses_history`
**Tracks address changes (relocations, expansions)**

```sql
CREATE TABLE hospital_addresses_history (
    address_history_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    address_type VARCHAR(50),                   -- Physical, Mailing, Billing

    -- Audit
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ccn) REFERENCES hospital_master(ccn)
);
```

### Table 4: `hospital_system_membership`
**Tracks hospital system/network affiliations over time**

```sql
CREATE TABLE hospital_system_membership (
    membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ccn VARCHAR(6) NOT NULL,

    -- System Information
    hospital_system_id VARCHAR(20),
    hospital_system_name VARCHAR(255),
    system_type VARCHAR(50),                    -- Chain, Network, Alliance, etc.

    -- Membership Period
    membership_start_date DATE,
    membership_end_date DATE,
    is_current BOOLEAN DEFAULT FALSE,

    -- Additional Context
    ownership_percentage DECIMAL(5,2),          -- If partial ownership
    relationship_type VARCHAR(50),              -- Owned, Affiliated, Member

    -- Audit
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ccn) REFERENCES hospital_master(ccn)
);
```

### Table 5: `hospital_annual_snapshot`
**Annual snapshot from HCRIS data - links to existing analytics**

```sql
CREATE TABLE hospital_annual_snapshot (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ccn VARCHAR(6) NOT NULL,
    fiscal_year INTEGER NOT NULL,

    -- Identifiers at this point in time
    npi VARCHAR(10),
    hospital_name VARCHAR(255),                 -- Name used in that fiscal year

    -- From HCRIS RPT file
    control_type VARCHAR(50),
    report_status VARCHAR(20),
    fy_begin_date DATE,
    fy_end_date DATE,
    geographic_code VARCHAR(10),

    -- Operational Metrics (summary)
    total_beds INTEGER,
    total_discharges INTEGER,
    total_patient_days INTEGER,

    -- Financial Summary (from KPIs table)
    total_revenue DECIMAL(15,2),
    total_assets DECIMAL(15,2),
    operating_margin_pct DECIMAL(5,2),

    -- Status
    was_operational BOOLEAN DEFAULT TRUE,

    -- Link to detailed analytics
    kpi_record_id INTEGER,                      -- Links to hospital_kpis table

    -- Audit
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ccn) REFERENCES hospital_master(ccn),
    UNIQUE(ccn, fiscal_year)
);
```

## Indexes

```sql
-- hospital_master indexes
CREATE INDEX idx_hospital_master_npi ON hospital_master(npi);
CREATE INDEX idx_hospital_master_state ON hospital_master(state_code);
CREATE INDEX idx_hospital_master_type ON hospital_master(hospital_type);
CREATE INDEX idx_hospital_master_system ON hospital_master(hospital_system_id);
CREATE INDEX idx_hospital_master_status ON hospital_master(status);

-- hospital_identifiers_history indexes
CREATE INDEX idx_identifiers_history_ccn ON hospital_identifiers_history(ccn);
CREATE INDEX idx_identifiers_history_type ON hospital_identifiers_history(change_type);
CREATE INDEX idx_identifiers_history_date ON hospital_identifiers_history(change_date);
CREATE INDEX idx_identifiers_history_related ON hospital_identifiers_history(related_ccn);

-- hospital_addresses_history indexes
CREATE INDEX idx_addresses_history_ccn ON hospital_addresses_history(ccn);
CREATE INDEX idx_addresses_history_current ON hospital_addresses_history(is_current);
CREATE INDEX idx_addresses_history_dates ON hospital_addresses_history(effective_date, end_date);

-- hospital_system_membership indexes
CREATE INDEX idx_system_membership_ccn ON hospital_system_membership(ccn);
CREATE INDEX idx_system_membership_system ON hospital_system_membership(hospital_system_id);
CREATE INDEX idx_system_membership_current ON hospital_system_membership(is_current);

-- hospital_annual_snapshot indexes
CREATE INDEX idx_annual_snapshot_ccn ON hospital_annual_snapshot(ccn);
CREATE INDEX idx_annual_snapshot_fy ON hospital_annual_snapshot(fiscal_year);
CREATE INDEX idx_annual_snapshot_ccn_fy ON hospital_annual_snapshot(ccn, fiscal_year);
```

## Key Features

### 1. Comprehensive Hospital Identity Tracking
- Primary CCN-based identification
- NPI tracking and historical changes
- Hospital name changes over time
- Multiple name types (legal name, DBA name)

### 2. Address and Location Management
- Current address in master table
- Historical addresses for tracking relocations
- Support for multiple address types (physical, mailing, billing)

### 3. Hospital System/Network Affiliation
- Current system membership
- Historical membership tracking
- Support for ownership percentages
- Different relationship types (owned, affiliated, member)

### 4. Change Detection and Tracking
- All identifier changes logged with dates
- Merger and acquisition tracking
- CCN consolidation/split tracking
- Source documentation for changes

### 5. Integration with Existing Analytics
- Annual snapshots link to hospital_kpis table
- Fiscal year alignment with HCRIS data
- Summary metrics for quick reference

## Data Population Strategy

### Phase 1: HCRIS Data (Immediate)
1. Extract all unique CCNs from existing parquet files
2. Populate hospital_annual_snapshot from HCRIS RPT files (FY 2020-2024)
3. Derive current hospital_master records from most recent fiscal year
4. Detect name changes by comparing across fiscal years
5. Classify hospital_type from CCN ranges

### Phase 2: CMS POS Integration (Next)
1. Download current CMS Provider of Services file
2. Match hospitals by CCN
3. Enrich hospital_master with:
   - Current official names
   - Complete addresses
   - Certification dates
   - Bed counts
   - Provider category codes
4. Populate hospital_addresses_history with POS data

### Phase 3: Historical POS Data (Optional)
1. Download historical quarterly POS files
2. Track name changes over time
3. Track address changes
4. Identify closed/merged hospitals
5. Populate hospital_identifiers_history

### Phase 4: System Affiliation (Future)
1. Research available system affiliation data sources
2. Integrate if public data available
3. Manual curation if needed for key systems
4. Populate hospital_system_membership table

## Data Quality Metrics

The `data_quality_score` field in hospital_master will be calculated as:

```
Score = (Number of populated required fields / Total required fields) * 100

Required fields:
- ccn (always present)
- hospital_name
- city
- state_code
- hospital_type
- ownership_type
- status

Optional fields that improve score:
- npi
- street_address
- zip_code
- phone_number
- hospital_system_name
- total_beds
```

## Handling Special Cases

### Mergers and Acquisitions
When Hospital A (CCN A) merges into Hospital B (CCN B):
1. Hospital A master record: status = 'Merged_Into', termination_date set
2. Hospital B master record: updated with merged entity info if applicable
3. History record created: change_type = 'CCN_MERGE', related_ccn = CCN B
4. Annual snapshots preserve pre-merger data for both CCNs

### Name Changes
1. Update hospital_master.hospital_name to new name
2. Create history record with old_value = old name, new_value = new name
3. Annual snapshots show name used in that specific fiscal year

### NPI Changes
1. Update hospital_master.npi to new NPI
2. Create history record tracking old NPI to new NPI
3. Preserve old NPI associations in annual snapshots

### CCN Changes (Rare)
1. Create new hospital_master record with new CCN
2. Old CCN record: status = 'CCN_Changed', link to new CCN
3. History record documents the CCN change
4. Preserve historical analytics under old CCN

## Implementation Notes

1. **DuckDB Implementation**: All tables will be created in the main hospital_analytics.duckdb database
2. **Parquet Export**: Master tables can be exported to parquet for efficient querying
3. **Update Frequency**:
   - hospital_annual_snapshot: Updated when new fiscal year HCRIS data available
   - hospital_master: Updated quarterly when new POS data available
   - Historical tables: Updated as changes detected
4. **Performance**: Indexes on frequently queried fields (CCN, NPI, state, type, fiscal_year)
5. **Data Validation**: Referential integrity enforced via foreign keys
