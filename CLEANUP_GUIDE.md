# Hospital Dashboard - File Cleanup Guide

## 📋 Unnecessary Files to Remove

This document identifies files that can be safely removed to clean up the project.

---

## 🗑️ Files to Delete

### Test Files (Safe to Delete)
```bash
# Remove these test files after verifying functionality
test_dash.py
test_dashboard_data.py
extract_pdf_text.py
```

**Reason:** These are development/testing files not needed for production.

---

### Duplicate/Old Documentation (Consolidate or Remove)

#### Process Documentation (ETL-specific, can archive)
```
ETL_MULTI_STATE_UPDATE.md          # Archived - ETL process complete
ETL_REDESIGN_SUMMARY.md            # Archived - ETL redesign complete
WORKSHEET_ETL_BATCH.md             # Archived - batch process complete
DATABASE_BUILD_COMPLETE.md         # Archived - database build docs
```

**Action:** Move to `docs/archive/` folder or delete if not needed.

#### Reference Documents (Low priority for core app)
```
Provider Reimbursement Manual.txt  # Large reference file - can store elsewhere
FOLDER_STRUCTURE.txt               # Outdated - replaced by master guide
```

**Action:** Archive or delete.

#### Development Notes
```
to_do.txt                          # Task list - now completed
```

**Action:** Delete or archive.

---

### Redundant Requirements File
```
requirements_auth.txt              # Merged into requirements.txt
```

**Action:** Delete - all dependencies now in `requirements.txt`

---

## 📁 Files to Organize

### Move to `docs/` Folder

Create a `docs/` folder and organize documentation:

```bash
mkdir -p docs/user-guides
mkdir -p docs/technical
mkdir -p docs/archive
mkdir -p docs/reference

# User-facing guides
mv QUICKSTART.md docs/user-guides/
mv AUTH_QUICKSTART.md docs/user-guides/
mv DEPLOY_QUICKSTART.md docs/user-guides/

# Technical documentation
mv TECHNICAL_ARCHITECTURE.md docs/technical/
mv KPI_HIERARCHY_DOCUMENTATION.md docs/technical/
mv AUTHENTICATION_GUIDE.md docs/technical/
mv DEPLOYMENT_GUIDE.md docs/technical/

# Dashboard-specific guides
mv DASHBOARD_WORKSHEETS_GUIDE.md docs/user-guides/
mv VALUATION_DASHBOARD_GUIDE.md docs/user-guides/

# Reference materials
mv HCRIS_QUICK_REFERENCE.md docs/reference/
mv HCRIS_VALUATION_METHODOLOGY.md docs/reference/
mv DATA_STRUCTURE_FOR_ANALYSTS.md docs/reference/

# Archive old docs
mv ETL_MULTI_STATE_UPDATE.md docs/archive/
mv ETL_REDESIGN_SUMMARY.md docs/archive/
mv WORKSHEET_ETL_BATCH.md docs/archive/
mv DATABASE_BUILD_COMPLETE.md docs/archive/
mv FOLDER_STRUCTURE.txt docs/archive/
```

---

## 🧹 Cleanup Commands

### Quick Cleanup (Safe - Removes Only Test Files)
```bash
cd /home/user/Hospital-Dashboard

# Remove test files
rm -f test_dash.py
rm -f test_dashboard_data.py
rm -f extract_pdf_text.py

# Remove merged requirements
rm -f requirements_auth.txt

# Remove completed task list
rm -f to_do.txt
```

### Full Cleanup with Organization
```bash
cd /home/user/Hospital-Dashboard

# Create documentation structure
mkdir -p docs/{user-guides,technical,archive,reference}

# Move documentation files
mv QUICKSTART.md AUTH_QUICKSTART.md DEPLOY_QUICKSTART.md docs/user-guides/
mv DASHBOARD_WORKSHEETS_GUIDE.md VALUATION_DASHBOARD_GUIDE.md docs/user-guides/

mv TECHNICAL_ARCHITECTURE.md KPI_HIERARCHY_DOCUMENTATION.md docs/technical/
mv AUTHENTICATION_GUIDE.md DEPLOYMENT_GUIDE.md docs/technical/

mv HCRIS_QUICK_REFERENCE.md HCRIS_VALUATION_METHODOLOGY.md docs/reference/
mv DATA_STRUCTURE_FOR_ANALYSTS.md docs/reference/

mv ETL_MULTI_STATE_UPDATE.md ETL_REDESIGN_SUMMARY.md docs/archive/
mv WORKSHEET_ETL_BATCH.md DATABASE_BUILD_COMPLETE.md docs/archive/
mv FOLDER_STRUCTURE.txt docs/archive/

# Remove unnecessary files
rm -f test_dash.py test_dashboard_data.py extract_pdf_text.py
rm -f requirements_auth.txt to_do.txt
rm -f "Provider Reimbursement Manual.txt"  # Large file - archive elsewhere

# Update README.md to reflect new structure
```

---

## 📊 File Count Summary

### Before Cleanup:
- **Total Files**: ~60 files
- **Documentation**: 19 MD files in root
- **Test Files**: 3 files
- **Redundant**: 2 files

### After Cleanup:
- **Root Directory**: Core app files only (~12 files)
- **docs/ Folder**: Organized documentation (19 files)
- **Removed**: 5 files (tests, redundant)
- **Much Cleaner!** ✨

---

## 🎯 Recommended Project Structure (After Cleanup)

```
Hospital-Dashboard/
├── README.md                        # Main README with links to docs/
├── app.py                          # Production entry point
├── app_with_auth.py                # Authenticated app
├── dashboard.py                    # Main KPI dashboard
├── dashboard_worksheets.py         # Worksheet viewer v1
├── dashboard_worksheets_v2.py      # Worksheet viewer v2
├── valuation_dashboard.py          # Valuation dashboard
├── kpi_hierarchy_config.py         # KPI hierarchy
├── auth_models.py                  # Authentication models
├── auth_manager.py                 # Authentication manager
├── auth_components.py              # Authentication UI
├── Procfile                        # Deployment config
├── render.yaml                     # Render config
├── runtime.txt                     # Python version
├── requirements.txt                # Dependencies
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore
│
├── config/                         # Configuration
│   ├── __init__.py
│   └── paths.py
│
├── utils/                          # Utilities
│   ├── __init__.py
│   ├── logging_config.py
│   └── error_helpers.py
│
├── etl/                            # ETL Scripts
│   ├── create_duckdb_tables.py
│   ├── create_balance_sheet.py
│   ├── create_revenue.py
│   ├── create_revenue_expenses.py
│   ├── create_costs_a000.py
│   ├── create_costs_b100.py
│   ├── create_fund_balance_changes.py
│   ├── create_all_worksheets.py
│   ├── create_income_statement.py
│   ├── create_expense_detail.py
│   ├── create_worksheet_a000000.py
│   └── process_a6000a0.py
│
├── scripts/                        # Utility Scripts
│   ├── build_database.py
│   ├── build_worksheets_database.py
│   ├── add_state_filters.py
│   └── load_valuation_data.py
│
└── docs/                           # Documentation (NEW!)
    ├── user-guides/               # End-user guides
    │   ├── QUICKSTART.md
    │   ├── AUTH_QUICKSTART.md
    │   ├── DEPLOY_QUICKSTART.md
    │   ├── DASHBOARD_WORKSHEETS_GUIDE.md
    │   └── VALUATION_DASHBOARD_GUIDE.md
    │
    ├── technical/                 # Technical documentation
    │   ├── TECHNICAL_ARCHITECTURE.md
    │   ├── KPI_HIERARCHY_DOCUMENTATION.md
    │   ├── AUTHENTICATION_GUIDE.md
    │   └── DEPLOYMENT_GUIDE.md
    │
    ├── reference/                 # Reference materials
    │   ├── HCRIS_QUICK_REFERENCE.md
    │   ├── HCRIS_VALUATION_METHODOLOGY.md
    │   └── DATA_STRUCTURE_FOR_ANALYSTS.md
    │
    └── archive/                   # Archived documentation
        ├── ETL_MULTI_STATE_UPDATE.md
        ├── ETL_REDESIGN_SUMMARY.md
        ├── WORKSHEET_ETL_BATCH.md
        ├── DATABASE_BUILD_COMPLETE.md
        └── FOLDER_STRUCTURE.txt
```

---

## ⚠️ Files to Keep

### Core Application (DO NOT DELETE)
```
✅ app.py
✅ app_with_auth.py
✅ dashboard.py
✅ dashboard_worksheets.py
✅ dashboard_worksheets_v2.py
✅ valuation_dashboard.py
✅ kpi_hierarchy_config.py
✅ auth_models.py
✅ auth_manager.py
✅ auth_components.py
```

### Deployment (DO NOT DELETE)
```
✅ Procfile
✅ render.yaml
✅ runtime.txt
✅ requirements.txt
✅ .env.example
✅ .gitignore
```

### Must-Keep Documentation
```
✅ README.md (main entry point)
```

---

## 🔄 After Cleanup - Update Links

After moving files to `docs/`, update links in `README.md`:

```markdown
**Quick Links:**
- 🔐 [Authentication Quick Start](docs/user-guides/AUTH_QUICKSTART.md)
- 🚀 [Deploy in 5 Minutes](docs/user-guides/DEPLOY_QUICKSTART.md)
- 📖 [Full Deployment Guide](docs/technical/DEPLOYMENT_GUIDE.md)
- 📚 [Authentication Guide](docs/technical/AUTHENTICATION_GUIDE.md)
```

---

## 📝 Summary

### Immediate Actions:
1. **Delete**: Test files, redundant requirements, task list (5 files)
2. **Organize**: Move 19 documentation files to `docs/` folder
3. **Archive**: Move 5 process docs to `docs/archive/`
4. **Update**: README.md links to new locations

### Benefits:
- ✅ Cleaner root directory
- ✅ Organized documentation
- ✅ Easier to navigate
- ✅ Professional structure
- ✅ Easier maintenance

### Estimated Time:
- **Quick cleanup**: 2 minutes
- **Full organization**: 10 minutes

---

**Last Updated**: 2025-11-16
**Files to Remove**: 5-6
**Files to Organize**: 19
**Result**: Clean, professional project structure
