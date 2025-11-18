# Hospital Dashboard - Application Structure

**Last Updated:** 2025-11-18

This document provides a complete overview of the application structure, showing which files are active, their roles, and which files can be safely removed.

---

## Table of Contents

1. [Production Application Files](#production-application-files)
2. [Landing Page](#landing-page)
3. [Authentication System](#authentication-system)
4. [Core Dashboard Module](#core-dashboard-module)
5. [Configuration & Utilities](#configuration--utilities)
6. [ETL Pipeline](#etl-pipeline)
7. [Database Scripts](#database-scripts)
8. [Alternative Dashboards](#alternative-dashboards)
9. [Test Files](#test-files)
10. [Debug & Development Scripts](#debug--development-scripts)
11. [Documentation Files](#documentation-files)
12. [Files That Can Be Removed](#files-that-can-be-removed)

---

## Production Application Files

### **app.py** (2.1 KB)
**Status:** ACTIVE - Production Entry Point
**Role:** Production wrapper for online deployment
**Used By:** Render, Railway, Fly.io, etc.
**Dependencies:** Imports from `app_with_auth.py`
**URLs:**
- Landing page: `http://HOST:PORT/`
- Dashboard: `http://HOST:PORT/app`

```python
# Key Features:
- Handles environment variables (PORT, HOST, DEBUG)
- Production configuration
- Imports app from app_with_auth.py
```

### **app_with_auth.py** (31 KB)
**Status:** ACTIVE - Main Application with Authentication
**Role:** Authenticated dashboard application (online deployment)
**Used By:** `app.py` (production)
**Dependencies:**
- `dashboard.py` (HospitalDataManager)
- `auth_manager.py` (AuthenticationManager)
- `auth_components.py` (UI components)

```python
# Key Features:
- User authentication (login/register/logout)
- Multi-user support (Company, Employee, Individual)
- Session management
- Dual routing (/ = landing, /app = dashboard)
- Uses HospitalDataManager from dashboard.py
```

### **dashboard.py** (251 KB)
**Status:** ACTIVE - Core Dashboard Module
**Role:** Main dashboard application (local deployment) + Data manager
**Used By:**
- Direct execution for local development
- Imported by `app_with_auth.py` for HospitalDataManager class
**Dependencies:**
- `config/paths.py`
- `kpi_hierarchy_config.py`

```python
# Key Features:
- HospitalDataManager class (database/parquet access)
- Full dashboard UI with KPI cards
- Level 2 KPI drill-down
- Financial statements (Balance Sheet, Revenue, Costs)
- Benchmark comparisons
- Dual routing (/ = landing, /app = dashboard)
```

**Important:** This file serves dual purposes:
1. Standalone local dashboard (run directly)
2. Data manager module (imported by app_with_auth.py)

---

## Landing Page

### **index.html** (12 KB)
**Status:** ACTIVE - Marketing Landing Page
**Role:** Professional landing page served at root URL
**Served By:** Flask routes in `dashboard.py` and `app_with_auth.py`
**URL:** `http://localhost:8050/` or production domain root

```html
<!-- Key Features: -->
- Hero section with value proposition
- Feature showcase
- Pricing tiers
- Testimonials
- All CTAs link to /app
```

### **styles.css** (11 KB)
**Status:** ACTIVE - Landing Page Styles
**Role:** CSS styling for landing page
**Used By:** `index.html`

```css
/* Key Features: */
- Professional design (no emojis)
- Responsive layout (mobile, tablet, desktop)
- Modern color scheme with primary blue theme
- Smooth animations and hover effects
```

---

## Authentication System

### **auth_manager.py** (15 KB)
**Status:** ACTIVE - Authentication Logic
**Role:** User authentication and session management
**Used By:** `app_with_auth.py`
**Dependencies:** `auth_models.py`

```python
# Key Features:
- Password hashing (bcrypt)
- Session management
- User registration/login/logout
- Company/Employee/Individual account types
- SQLite database (users.db)
```

### **auth_models.py** (14 KB)
**Status:** ACTIVE - Database Models
**Role:** SQLAlchemy models for users and sessions
**Used By:** `auth_manager.py`

```python
# Database Tables:
- users: User accounts
- companies: Organization accounts
- sessions: Active user sessions
```

### **auth_components.py** (22 KB)
**Status:** ACTIVE - UI Components
**Role:** Dash UI components for login/register
**Used By:** `app_with_auth.py`

```python
# UI Components:
- Login form
- Registration forms (Company, Employee, Individual)
- User menu (profile, logout)
```

---

## Core Dashboard Module

### **kpi_hierarchy_config.py** (55 KB)
**Status:** ACTIVE - KPI Configuration
**Role:** Defines KPI hierarchy (L1, L2, L3) and mappings
**Used By:** `dashboard.py`

```python
# Key Features:
- 6 Level 1 KPIs
- 78 total KPIs across 3 levels
- Formula definitions
- Category mappings
- Importance rankings
```

---

## Configuration & Utilities

### **config/paths.py**
**Status:** ACTIVE - Path Configuration
**Role:** Centralized path configuration for parquet files
**Used By:** `dashboard.py`, ETL scripts

```python
# Defines paths for:
- Balance sheet parquet files
- Revenue parquet files
- Costs parquet files
- Revenue & expenses parquet files
```

### **config/__init__.py**
**Status:** ACTIVE - Module Init
**Role:** Makes config a Python package

### **utils/logging_config.py**
**Status:** ACTIVE - Logging Setup
**Role:** Centralized logging configuration
**Used By:** ETL scripts

### **utils/error_helpers.py**
**Status:** ACTIVE - Error Handling
**Role:** Error handling utilities
**Used By:** ETL scripts

### **utils/__init__.py**
**Status:** ACTIVE - Module Init
**Role:** Makes utils a Python package

---

## ETL Pipeline

All ETL scripts transform raw CMS HCRIS data into parquet files for the dashboard.

### **etl/create_duckdb_tables.py**
**Status:** ACTIVE - ETL Step 1
**Role:** Create DuckDB tables from CSV files

### **etl/create_balance_sheet.py**
**Status:** ACTIVE - ETL Step 2
**Role:** Transform balance sheet data

### **etl/create_revenue.py**
**Status:** ACTIVE - ETL Step 3
**Role:** Transform revenue data

### **etl/create_revenue_expenses.py**
**Status:** ACTIVE - ETL Step 4
**Role:** Transform revenue & expenses data

### **etl/create_costs_a000.py**
**Status:** ACTIVE - ETL Step 5a
**Role:** Transform costs from Schedule A

### **etl/create_costs_b100.py**
**Status:** ACTIVE - ETL Step 5b
**Role:** Transform costs from Schedule B-1

### **etl/create_fund_balance_changes.py**
**Status:** ACTIVE - ETL Step 6
**Role:** Transform fund balance changes

### **etl/create_all_worksheets.py**
**Status:** ACTIVE - Worksheet ETL
**Role:** Create detailed worksheet tables

### **etl/create_worksheet_a000000.py**
**Status:** ACTIVE - Worksheet A ETL
**Role:** Process Worksheet A (Balance Sheet)

### **etl/process_a6000a0.py**
**Status:** ACTIVE - Worksheet Processing
**Role:** Process Worksheet A-6

### **etl/create_income_statement.py**
**Status:** ACTIVE - Income Statement ETL
**Role:** Create income statement data

### **etl/create_expense_detail.py**
**Status:** ACTIVE - Expense Detail ETL
**Role:** Create detailed expense breakdowns

---

## Database Scripts

### **scripts/build_database.py**
**Status:** ACTIVE - Database Builder
**Role:** Build optimized database with pre-computed KPIs
**Output:** `hospital_analytics.duckdb` (3.5 GB)

```python
# Creates:
- hospital_kpis table (27K+ records)
- hospital_benchmarks table (pre-computed percentiles)
- hospital_metadata table
- Indexed financial statement tables
```

### **scripts/build_worksheets_database.py**
**Status:** ACTIVE - Worksheet Database Builder
**Role:** Build detailed worksheet database
**Output:** `hospital_worksheets.duckdb`

### **scripts/add_state_filters.py**
**Status:** ACTIVE - Database Enhancement
**Role:** Add state filtering to database

### **scripts/load_valuation_data.py**
**Status:** ACTIVE - Valuation Data Loader
**Role:** Load valuation-specific data for valuation dashboard

---

## Alternative Dashboards

These are separate dashboard applications that can run independently.

### **valuation_dashboard.py** (29 KB)
**Status:** STANDALONE - Separate Dashboard
**Role:** Interactive hospital valuation dashboard
**Can Be Run:** `python valuation_dashboard.py`

```python
# Features:
- Valuation analysis
- Revenue/expense impact modeling
- Waterfall charts
- Independent from main dashboard
```

### **dashboard_worksheets.py** (12 KB)
**Status:** STANDALONE - Worksheet Dashboard
**Role:** Display raw HCRIS worksheet data
**Can Be Run:** `python dashboard_worksheets.py`

```python
# Features:
- Worksheet-level data display
- Year-by-year columns
- Line/column navigation
```

### **dashboard_worksheets_v2.py** (13 KB)
**Status:** STANDALONE - Simplified Worksheet Dashboard
**Role:** Simplified version of worksheet dashboard
**Can Be Run:** `python dashboard_worksheets_v2.py`

---

## Test Files

All files starting with `test_*.py` are test/validation scripts.

### **Test Files (13 files)**
**Status:** DEVELOPMENT ONLY - Not needed in production
**Role:** Testing and validation during development

1. **test_all_benchmarks_complete.py** (5.0 KB) - Verify benchmark completeness
2. **test_benchmark_order.py** (4.2 KB) - Test benchmark ordering
3. **test_dash.py** (1.3 KB) - Basic Dash test
4. **test_dashboard_data.py** (3.6 KB) - Data validation
5. **test_enhanced_cards.py** (5.6 KB) - KPI card testing
6. **test_kpi_mapping.py** (716 bytes) - KPI mapping validation
7. **test_level1_filter.py** (4.5 KB) - Level 1 filter testing
8. **test_level2_drilldown.py** (3.3 KB) - Drill-down testing
9. **test_level2_kpis.py** (8.3 KB) - Level 2 KPI testing
10. **test_phase3_ui.py** (8.1 KB) - Phase 3 UI testing
11. **test_phase4_hierarchy.py** (12 KB) - Hierarchy testing
12. **test_state_benchmark.py** (4.2 KB) - State benchmark testing
13. **test_worksheet_connection.py** (8.7 KB) - Worksheet connection testing

**Total Size:** ~67 KB

---

## Debug & Development Scripts

### **debug_local.py** (2.5 KB)
**Status:** DEVELOPMENT ONLY
**Role:** Simulate production environment locally
**Use Case:** Test deployment configuration locally

### **debug_state_benchmarks.py** (3.3 KB)
**Status:** DEVELOPMENT ONLY
**Role:** Debug state benchmark calculations

### **explore_worksheet_tables.py** (1.6 KB)
**Status:** DEVELOPMENT ONLY
**Role:** Explore worksheet database schema

### **add_missing_level1_kpis.py** (7.2 KB)
**Status:** ONE-TIME SCRIPT - Already executed
**Role:** Add 2 missing L1 KPIs (Medicare CCR, Bad Debt %)
**Note:** This was a database migration script, already run

### **extract_pdf_text.py** (317 bytes)
**Status:** UTILITY SCRIPT
**Role:** Extract text from PDF files
**Note:** Minimal utility, likely for documentation extraction

---

## Documentation Files

### **Active Documentation** (Keep These)

1. **README.md** - Main project documentation
2. **QUICKSTART.md** - Quick start guide
3. **TECHNICAL_ARCHITECTURE.md** - Technical deep-dive
4. **AUTHENTICATION_GUIDE.md** - Authentication documentation
5. **AUTH_QUICKSTART.md** - Quick auth setup
6. **DEPLOYMENT_GUIDE.md** - Full deployment guide
7. **DEPLOY_QUICKSTART.md** - Quick deployment guide
8. **KPI_HIERARCHY_DOCUMENTATION.md** - KPI documentation

### **Phase Documentation** (Historical - Can Archive)

9. **PHASE_1_COMPLETE.md** - Phase 1 completion notes
10. **PHASE_2_COMPLETE.md** - Phase 2 completion notes
11. **PHASE_3_COMPLETE.md** - Phase 3 completion notes
12. **PHASE_4_COMPLETE.md** - Phase 4 completion notes

### **Specialized Guides** (Keep if Using Features)

13. **DASHBOARD_WORKSHEETS_GUIDE.md** - Worksheet dashboard guide
14. **VALUATION_DASHBOARD_GUIDE.md** - Valuation dashboard guide
15. **WORKSHEET_ETL_BATCH.md** - Worksheet ETL documentation
16. **HCRIS_VALUATION_METHODOLOGY.md** - Valuation methodology
17. **HCRIS_QUICK_REFERENCE.md** - HCRIS reference
18. **DATA_STRUCTURE_FOR_ANALYSTS.md** - Data structure guide
19. **KPI_IMPLEMENTATION_GAP_ANALYSIS.md** - Gap analysis

### **Development Guides** (Development Only)

20. **LOCAL_DEBUG_GUIDE.md** - Local debugging
21. **QUICK_START_DEBUG.md** - Debug quick start
22. **DATABASE_BUILD_COMPLETE.md** - Database build notes
23. **DASHBOARD_INTEGRATION.md** - Integration notes
24. **ETL_REDESIGN_SUMMARY.md** - ETL redesign notes
25. **ETL_MULTI_STATE_UPDATE.md** - Multi-state update notes
26. **CLEANUP_GUIDE.md** - Cleanup instructions
27. **MASTER_GUIDE.md** - Master guide (possibly outdated)

### **Other Files**

28. **FOLDER_STRUCTURE.txt** - Folder structure
29. **Provider Reimbursement Manual.txt** - CMS manual reference
30. **to_do.txt** - TODO list

---

## Dependency Files

### **requirements.txt**
**Status:** ACTIVE - Main Dependencies
**Role:** Python dependencies for the application

### **requirements_auth.txt**
**Status:** ACTIVE - Auth Dependencies
**Role:** Additional dependencies for authentication
**Note:** Should be merged into requirements.txt

### **runtime.txt**
**Status:** ACTIVE - Python Version
**Role:** Specifies Python version for deployment platforms

---

## Files That Can Be Removed

### Safely Removable (54.6 KB total)

#### Test Files (67 KB)
All `test_*.py` files can be removed from production:
- test_all_benchmarks_complete.py
- test_benchmark_order.py
- test_dash.py
- test_dashboard_data.py
- test_enhanced_cards.py
- test_kpi_mapping.py
- test_level1_filter.py
- test_level2_drilldown.py
- test_level2_kpis.py
- test_phase3_ui.py
- test_phase4_hierarchy.py
- test_state_benchmark.py
- test_worksheet_connection.py

#### Debug/Development Scripts (13.6 KB)
- **debug_local.py** - Only needed for local development
- **debug_state_benchmarks.py** - Debugging tool
- **explore_worksheet_tables.py** - Development exploration

#### One-Time Scripts (7.5 KB)
- **add_missing_level1_kpis.py** - Already executed, no longer needed
- **extract_pdf_text.py** - Minimal utility

#### Documentation (Can Archive)
- **PHASE_1_COMPLETE.md** - Historical
- **PHASE_2_COMPLETE.md** - Historical
- **PHASE_3_COMPLETE.md** - Historical
- **PHASE_4_COMPLETE.md** - Historical
- **MASTER_GUIDE.md** - Possibly outdated
- **to_do.txt** - Task list (move to issues/project board)

### Total Removable: ~88 KB of Python files + Historical docs

---

## Application Flow

### Local Deployment (Development)
```
User visits http://localhost:8050
    ↓
Flask serves index.html (landing page)
    ↓
User clicks CTA → /app
    ↓
dashboard.py runs Dash application
    ↓
HospitalDataManager loads data
    ↓
User interacts with KPI dashboard
```

### Online Deployment (Production)
```
User visits https://your-domain.com
    ↓
Flask serves index.html (landing page)
    ↓
User clicks CTA → /app
    ↓
app_with_auth.py shows login/register
    ↓
User authenticates
    ↓
app_with_auth imports HospitalDataManager from dashboard.py
    ↓
User interacts with KPI dashboard
```

### Deployment Command Flow
```
Production:
  python app.py
      ↓
  Imports from app_with_auth.py
      ↓
  Imports HospitalDataManager from dashboard.py

Local:
  python dashboard.py
      ↓
  Runs standalone without authentication
```

---

## File Size Summary

### Production Files (Core Application)
- **app.py:** 2.1 KB
- **app_with_auth.py:** 31 KB
- **dashboard.py:** 251 KB
- **kpi_hierarchy_config.py:** 55 KB
- **auth_manager.py:** 15 KB
- **auth_models.py:** 14 KB
- **auth_components.py:** 22 KB
- **index.html:** 12 KB
- **styles.css:** 11 KB

**Total Core:** ~413 KB

### ETL & Scripts (Required for Data Processing)
- **ETL Scripts:** ~14 files
- **Database Scripts:** ~4 files

### Alternative Dashboards (Optional)
- **valuation_dashboard.py:** 29 KB
- **dashboard_worksheets.py:** 12 KB
- **dashboard_worksheets_v2.py:** 13 KB

**Total Alternative:** ~54 KB

### Removable Files
- **Test files:** ~67 KB
- **Debug scripts:** ~13.6 KB
- **One-time scripts:** ~7.5 KB

**Total Removable:** ~88 KB

---

## Recommendations

### For Production Deployment

**Keep:**
1. All files in "Production Application Files"
2. All files in "Authentication System"
3. All files in "Landing Page"
4. kpi_hierarchy_config.py
5. config/ and utils/ directories
6. README.md, deployment guides, authentication guides

**Remove:**
1. All test_*.py files (67 KB)
2. All debug_*.py files (13.6 KB)
3. add_missing_level1_kpis.py (7.2 KB)
4. extract_pdf_text.py (317 bytes)
5. Historical phase documentation

**Optional (Keep if using features):**
1. valuation_dashboard.py (if using valuation features)
2. dashboard_worksheets.py / dashboard_worksheets_v2.py (if using worksheet view)
3. ETL scripts (if running data updates)
4. scripts/ directory (if rebuilding database)

### For Development

**Keep Everything** - Tests and debug scripts are useful during development

---

## Cleanup Commands

To remove test and debug files from production:

```bash
# Remove test files
rm test_*.py

# Remove debug files
rm debug_*.py explore_worksheet_tables.py

# Remove one-time scripts
rm add_missing_level1_kpis.py extract_pdf_text.py

# Archive historical docs
mkdir archive
mv PHASE_*.md archive/
mv MASTER_GUIDE.md archive/
mv to_do.txt archive/
```

**WARNING:** Only run these commands on production deployments, not in development!

---

## Summary

### Active Application Structure:
```
Hospital-Dashboard/
├── app.py                          # Production entry point
├── app_with_auth.py                # Authenticated dashboard (online)
├── dashboard.py                    # Main dashboard module (local + data manager)
├── index.html                      # Landing page
├── styles.css                      # Landing page styles
│
├── Authentication/
│   ├── auth_manager.py             # Auth logic
│   ├── auth_models.py              # Database models
│   └── auth_components.py          # UI components
│
├── Configuration/
│   ├── kpi_hierarchy_config.py     # KPI definitions
│   ├── config/paths.py             # Path configuration
│   └── utils/                      # Utilities (logging, errors)
│
├── ETL/
│   └── etl/*.py                    # Data transformation scripts
│
├── Scripts/
│   └── scripts/*.py                # Database builders
│
├── Alternative Dashboards/
│   ├── valuation_dashboard.py      # Valuation analysis
│   └── dashboard_worksheets*.py    # Worksheet viewer
│
└── Documentation/
    ├── README.md                   # Main docs
    ├── *_GUIDE.md                  # Various guides
    └── archive/                    # Historical docs (can move)
```

---

**End of Document**
