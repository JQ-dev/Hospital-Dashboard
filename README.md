# Hospital Analytics Dashboard

A professional interactive dashboard for analyzing hospital financial performance using CMS HCRIS data.

## 🚀 New: Authentication & Cloud Deployment

**Deploy to free cloud services in 5 minutes!**

- ✅ **Secure Authentication** - Multi-user support (companies, employees, individuals)
- ✅ **Cloud Ready** - One-click deploy to Render, Railway, or Fly.io
- ✅ **100% Free Tier** - No credit card required
- ✅ **HTTPS Included** - Secure by default

**Quick Links:**
- 🔐 [Authentication Quick Start](AUTH_QUICKSTART.md) - Set up login in 3 minutes
- 🚀 [Deploy in 5 Minutes](DEPLOY_QUICKSTART.md) - Get your app live now
- 📖 [Full Deployment Guide](DEPLOYMENT_GUIDE.md) - All platforms covered
- 📚 [Authentication Guide](AUTHENTICATION_GUIDE.md) - Complete API reference

**Run with Authentication:**
```bash
pip install -r requirements.txt
python app_with_auth.py  # Or python app.py for production
```

Access at: `http://localhost:8050` → Create account → Start analyzing!

---

## Features

- **Interactive KPI Cards**: 17 key financial metrics with trend visualization
- **Benchmark Comparisons**: Compare against National, State, Hospital Type, or State+Type peers
- **Multi-Year Financial Statements**: Balance Sheet, Revenue, Revenue & Expenses, and Costs
- **Performance Tracking**: Monitor trends across multiple fiscal years
- **Fund Type Analysis**: Separate views for General Fund, Specific Purpose, Endowment, and Plant Funds
- **Pre-Computed Analytics**: Lightning-fast queries using optimized DuckDB database

## Project Structure

```
hospital_dashboard/
├── README.md                           # This file
├── QUICKSTART.md                       # Quick start guide
├── TECHNICAL_ARCHITECTURE.md           # Technical deep-dive for developers/LLMs
├── FOLDER_STRUCTURE.txt                # Detailed folder structure
├── dashboard.py                        # Main Dash application (~95 KB)
├── requirements.txt                    # Python dependencies
├── hospital_analytics.duckdb           # Optimized database (3.5 GB)
│
├── config/                            # Configuration Module
│   ├── __init__.py
│   ├── paths.py                       # Centralized path configuration
│   ├── mappings.py                    # DB column to KPI key mappings
│   ├── card_registry.py               # KPI card definitions (78 KPIs)
│   └── hierarchy_config.py            # KPI hierarchy tree structures
│
├── utils/                             # Utility Functions
│   ├── __init__.py
│   ├── logging_config.py              # Logging configuration
│   └── error_helpers.py               # Error handling utilities
│
├── etl/                               # ETL Scripts (Transform CMS data)
│   ├── create_duckdb_tables.py        # Step 1: Prepare source data tables
│   ├── create_balance_sheet.py        # Step 2: Transform balance sheet
│   ├── create_revenue.py              # Step 3: Transform revenue data
│   ├── create_revenue_expenses.py     # Step 4: Transform revenue & expenses
│   ├── create_costs_a000.py           # Step 5a: Transform costs - Schedule A
│   ├── create_costs_b100.py           # Step 5b: Transform costs - Schedule B-1
│   ├── create_fund_balance_changes.py # Step 6: Transform fund balance changes
│   └── logs/                          # ETL execution logs
│
├── scripts/                           # Utility Scripts
│   ├── build_database.py              # Build optimized database with pre-computed KPIs
│   └── add_state_filters.py           # Add state filtering to database
│
├── data/                              # Data Files
│   ├── source_data/                   # Raw CMS HCRIS Data (CSV)
│   │   ├── HOSP10FY2020/             # Fiscal Year 2020
│   │   ├── HOSP10FY2021/             # Fiscal Year 2021
│   │   ├── HOSP10FY2022/             # Fiscal Year 2022
│   │   ├── HOSP10FY2023/             # Fiscal Year 2023
│   │   └── HOSP10FY2024/             # Fiscal Year 2024
│   │
│   ├── Col_Names/                     # Column Mapping Files
│   │   ├── Names_A000.csv             # Schedule A mappings
│   │   ├── Names_B000.csv             # Schedule B mappings
│   │   ├── Names_B100.csv             # Schedule B-1 mappings
│   │   ├── Names_G000.csv             # Worksheet G mappings
│   │   ├── Names_G200.csv             # Worksheet G-2 mappings
│   │   └── Names_G300.csv             # Worksheet G-3 mappings
│   │
│   ├── other_data/                    # Reference Data
│   │   ├── ccn_state_codes.csv        # State code mappings
│   │   ├── ccn_grouped.csv            # Hospital type classifications
│   │   └── CMS_CCN_CODES_R29SOMA.pdf  # CMS provider number documentation
│   │
│   └── db_parquets/                   # Transformed Parquet Files (Generated)
│       ├── balance_sheet_long/
│       ├── revenue_long/
│       ├── revenue_expenses_long/
│       ├── costs_a000_long/
│       ├── costs_b100_long/
│       └── fund_balance_changes_long/
│
└── logs/                              # Application & ETL Logs
```

## Prerequisites

- Python 3.8+
- 8GB+ RAM (for database build)
- CMS HCRIS data in parquet format (from poc_env)

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Required Python packages:
   - dash
   - dash-bootstrap-components
   - plotly
   - duckdb
   - pandas
   - numpy

## Setup Instructions

### Step 1: Prepare Source Data (If Not Already Done)

If you don't have the transformed parquet files, run the ETL pipeline:

```bash
cd etl

# Step 1: Create source DuckDB tables from CMS HCRIS files
python create_duckdb_tables.py

# Step 2: Transform Balance Sheet
python create_balance_sheet.py

# Step 3: Transform Revenue
python create_revenue.py

# Step 4: Transform Revenue & Expenses
python create_revenue_expenses.py

# Step 5a: Transform Costs - Schedule A
python create_costs_a000.py

# Step 5b: Transform Costs - Schedule B-1
python create_costs_b100.py

# Step 6: Transform Fund Balance Changes
python create_fund_balance_changes.py
```

This will create parquet files in `data/db_parquets/`:
- `balance_sheet_long/`
- `revenue_long/`
- `revenue_expenses_long/`
- `costs_a000_long/`
- `costs_b100_long/`
- `fund_balance_changes_long/`

### Step 2: Build Optimized Database

Build the pre-computed database for fast queries (takes 20-40 minutes):

```bash
cd scripts
python build_database.py
```

This creates `hospital_analytics.duckdb` (~3.5 GB) with:
- Pre-computed KPIs for all hospital-year combinations
- Pre-computed benchmarks (P25, Median, P75, Mean) for all levels
- Optimized indexes for instant queries

**Database Schema:**
- `hospital_kpis` - 27K+ records with 17 KPIs per hospital/year
- `hospital_benchmarks` - Pre-computed percentiles for 4 benchmark levels
- `hospital_metadata` - Hospital classifications and state codes
- `balance_sheet` - Multi-year balance sheet data with indexes
- `revenue` - Revenue data with indexes
- `revenue_expenses` - Revenue & expenses data with indexes
- `costs_a000` - Schedule A costs with indexes
- `costs_b100` - Schedule B-1 costs with indexes
- `fund_balance_changes` - Fund balance changes with indexes

### Step 3: Run Dashboard

```bash
python dashboard.py
```

The dashboard will be available at: **http://localhost:8050**

## Usage

### Dashboard Interface

#### KPI Dashboard Tab
1. **Select Hospital**: Choose from 6,000+ hospitals in dropdown
2. **Select Fiscal Year**: View data for specific year
3. **Select Benchmark Level**: Compare against National, State, Hospital Type, or State+Type
4. **View KPI Cards**: Click cards to flip and see details
5. **View Data Tables**: Click "View Data" buttons to see multi-year trends
6. **Reorder Cards**: Click "Reorder Cards by Importance" to prioritize KPIs

#### Financials Tab
1. **Balance Sheet**: View by fund type (General, Specific Purpose, Endowment, Plant)
2. **Revenue Detail**: Inpatient and outpatient revenue breakdown
3. **Revenue & Expenses**: Operating performance with major categories
4. **Costs**: Detailed cost center analysis

All financial statements show **all fiscal years as columns** with the most recent year on the right.

## Performance

- **Without Pre-Computed Database**: 5-30 seconds per hospital selection
- **With Pre-Computed Database**: < 100ms per hospital selection

The optimized database provides **50-300x faster queries** by pre-computing:
- All KPI calculations
- All benchmark percentiles
- All index lookups

## Data Flow

```
CMS HCRIS Data (CSV)
    ↓
data/source_data/HOSP10FY20XX/
    ↓
create_duckdb_tables.py (prepare source tables)
    ↓
ETL scripts (create_*.py) - Transform to long format
    ↓
data/db_parquets/*_long/ (Parquet files)
    ↓
build_database.py (pre-compute KPIs and benchmarks)
    ↓
hospital_analytics.duckdb (optimized database)
    ↓
dashboard.py (interactive visualization)
```

## Troubleshooting

### Dashboard Running Slowly
- Make sure you've built the optimized database: `python scripts/build_database.py`
- Check that the dashboard finds the database (should print "Using optimized database with pre-computed KPIs")
- Verify `hospital_analytics.duckdb` exists in the root directory

### Database Build Fails
- Ensure you have 8GB+ RAM available
- Verify parquet files exist in `data/db_parquets/balance_sheet_long/` etc.
- Check disk space (database needs ~4GB total)
- Review logs in `logs/` directory for specific errors

### Missing Data
- Verify ETL scripts have run successfully (check logs in `etl/logs/`)
- Check that all parquet directories exist in `data/db_parquets/` and contain files
- Ensure mapping CSV files are present in `data/Col_Names/`
- Verify source data exists in `data/source_data/HOSP10FY20XX/`

## KPI Hierarchy (78 KPIs across 3 Levels)

The dashboard uses a modular 3-level KPI hierarchy for drill-down analysis:

### Level 1: Strategic KPIs (6 total)
Top-level financial health indicators:
- **Net Income Margin** - Overall profitability
- **Days in AR** - Cash cycle efficiency
- **Operating Expense per Adjusted Discharge** - Cost control
- **Medicare Cost-to-Charge Ratio** - Pricing efficiency
- **Bad Debt + Charity %** - Uncompensated care burden
- **Current Ratio** - Short-term liquidity

### Level 2: Driver KPIs (24 total)
Each Level 1 KPI has 4 driver KPIs explaining performance:
- Operating Expense Ratio, Non-Operating Income %, Payer Mix, Capital Costs
- Denial Rate, Commercial Payer %, Billing Efficiency, Collection Rate
- Labor Cost, Supply Cost, Overhead Allocation, Case Mix Index
- And more...

### Level 3: Sub-Driver KPIs (48 total)
Detailed metrics for root cause analysis:
- FTE per Bed, Salary % of Expenses, Investment Income Share
- Medicare Denial %, Contract Labor %, Drug Cost %
- And more...

### Configuration Files
KPI definitions are modular and extensible:
- `config/card_registry.py` - All 78 KPI cards with metadata, tags, and scoring
- `config/hierarchy_config.py` - Tree structures (default, cost-focused, revenue-focused)

## Benchmark Levels

- **National**: Compare against all US hospitals
- **State**: Compare against hospitals in same state
- **Hospital Type**: Compare against same type (Short Term Acute Care, Critical Access, etc.)
- **State + Hospital Type**: Compare against same state AND same type

## Technical Details

### Database Optimization
- Columnar storage with DuckDB
- B-tree indexes on Provider_Number and Fiscal_Year
- Read-only connections for concurrent users
- Pre-computed aggregations eliminate runtime calculations

### Data Sources
- CMS HCRIS (Hospital Cost Report Information System)
- 5 fiscal years of data (2020-2024)
- 6,224+ hospitals tracked
- Multiple worksheets: Balance Sheet (G000, G200, G300), Revenue (A000), Revenue & Expenses (G000), Costs (A000, B100), Fund Changes (B000)

### Technologies
- **Backend**: Python 3.8+, DuckDB
- **Frontend**: Dash, Plotly, Dash Bootstrap Components
- **Data Processing**: Pandas, NumPy
- **Storage**: Parquet files in `data/db_parquets/` (long format with fiscal year partitioning)

## License

This project uses publicly available CMS HCRIS data.

## Support

For issues or questions, please check:
1. This README - User guide and setup instructions
2. **TECHNICAL_ARCHITECTURE.md** - Deep technical documentation for developers and LLMs
3. The comments in the Python scripts
4. The CMS HCRIS documentation

### For Developers & Future LLMs

See **[TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md)** for:
- Detailed explanation of query-based vs pre-computed approaches
- Database schema and indexing strategy
- Code flow and decision trees
- Performance optimization techniques
- Areas for improvement with specific implementation guidance
- Testing strategies and deployment checklists

## Version History

- **v1.1** - Modular KPI configuration with 78 KPIs across 3 levels
  - New `config/card_registry.py` with all KPI definitions
  - New `config/hierarchy_config.py` with flexible tree structures
  - Support for alternative hierarchies (cost-focused, revenue-focused)
  - Tags and impact scores for KPI prioritization
- **v1.0** - Initial release with pre-computed database optimization
