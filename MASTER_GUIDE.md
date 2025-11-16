# Hospital KPI Dashboard - Master Guide

**The Complete Reference for Understanding and Using the Hospital Analytics Platform**

---

## 📚 Table of Contents

1. [Project Overview](#project-overview)
2. [Quick Start Paths](#quick-start-paths)
3. [Architecture Overview](#architecture-overview)
4. [Feature Catalog](#feature-catalog)
5. [Documentation Map](#documentation-map)
6. [Development Workflow](#development-workflow)
7. [Deployment Options](#deployment-options)
8. [Data Pipeline](#data-pipeline)
9. [Security & Authentication](#security--authentication)
10. [Troubleshooting](#troubleshooting)
11. [Roadmap](#roadmap)

---

## 🎯 Project Overview

### What is This?

The **Hospital KPI Dashboard** is a comprehensive, production-ready web application for analyzing hospital financial performance using CMS HCRIS (Hospital Cost Report Information System) data.

### Key Capabilities

✅ **78-KPI Hierarchical Analytics** - Three-level drill-down from strategic to granular metrics
✅ **Multi-User Authentication** - Supports companies, employees, and individual users
✅ **Cloud Deployment Ready** - One-click deploy to free hosting services
✅ **Real-Time Benchmarking** - Compare against national, state, and hospital type peers
✅ **Interactive Dashboards** - Multiple specialized views (KPIs, worksheets, valuation)
✅ **Secure** - bcrypt password hashing, session management, audit logging

### Technology Stack

- **Frontend**: Dash (Plotly), Bootstrap, Font Awesome
- **Backend**: Python, Flask, Gunicorn
- **Database**: DuckDB (SQLite for auth)
- **Authentication**: bcrypt, session-based
- **Deployment**: Render, Railway, Fly.io (all free tiers available)

---

## 🚀 Quick Start Paths

Choose your path based on what you want to do:

### Path 1: Deploy & Use (Fastest - 5 minutes)
```
1. Read: DEPLOY_QUICKSTART.md
2. Visit: render.com
3. Connect GitHub → Deploy
4. Done! Create account and use
```

### Path 2: Run Locally (10 minutes)
```
1. Read: AUTH_QUICKSTART.md
2. pip install -r requirements.txt
3. python app_with_auth.py
4. http://localhost:8050
```

### Path 3: Understand Architecture (30 minutes)
```
1. Read: TECHNICAL_ARCHITECTURE.md
2. Read: KPI_HIERARCHY_DOCUMENTATION.md
3. Read: AUTHENTICATION_GUIDE.md
4. Explore code
```

### Path 4: Build Database from Scratch (2-3 hours)
```
1. Read: QUICKSTART.md
2. Run ETL pipeline (etl/*.py)
3. Build database (scripts/build_database.py)
4. Launch dashboard
```

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────┐
│           USER INTERFACE LAYER                   │
├─────────────────────────────────────────────────┤
│  - Login/Registration (auth_components.py)      │
│  - KPI Dashboard (dashboard.py)                 │
│  - Worksheet Viewer (dashboard_worksheets.py)   │
│  - Valuation Dashboard (valuation_dashboard.py) │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│        APPLICATION LAYER                         │
├─────────────────────────────────────────────────┤
│  - Auth Manager (auth_manager.py)               │
│  - KPI Config (kpi_hierarchy_config.py)         │
│  - Data Manager (HospitalDataManager)           │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│          DATA LAYER                              │
├─────────────────────────────────────────────────┤
│  - Auth Database (SQLite - auth.db)             │
│  - Analytics Database (DuckDB - *.duckdb)       │
│  - Parquet Files (db_parquets/)                 │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│          ETL PIPELINE                            │
├─────────────────────────────────────────────────┤
│  - Source Data → DuckDB (create_duckdb_tables)  │
│  - Transformations (create_*.py scripts)        │
│  - Pre-computation (build_database.py)          │
└─────────────────────────────────────────────────┘
```

### File Organization

```
Hospital-Dashboard/
├── 🚀 ENTRY POINTS
│   ├── app.py                      # Production (cloud)
│   ├── app_with_auth.py            # Local with auth
│   └── dashboard.py                # Core KPI dashboard
│
├── 🔐 AUTHENTICATION
│   ├── auth_models.py              # Database schema
│   ├── auth_manager.py             # Auth logic
│   └── auth_components.py          # UI components
│
├── 📊 DASHBOARDS
│   ├── dashboard.py                # Main KPI (78 KPIs)
│   ├── dashboard_worksheets.py     # Worksheet viewer v1
│   ├── dashboard_worksheets_v2.py  # Worksheet viewer v2
│   └── valuation_dashboard.py      # Valuation analysis
│
├── ⚙️ CONFIGURATION
│   ├── kpi_hierarchy_config.py     # 78-KPI hierarchy
│   ├── config/paths.py             # Path config
│   └── utils/                      # Logging, errors
│
├── 🔄 ETL PIPELINE
│   └── etl/                        # 12 transformation scripts
│
├── 🛠️ UTILITIES
│   └── scripts/                    # Database builders
│
└── 📚 DOCUMENTATION
    ├── README.md                   # Main entry
    ├── MASTER_GUIDE.md            # This file
    └── 18 other guides             # See Documentation Map
```

---

## 🎨 Feature Catalog

### 1. KPI Dashboard (dashboard.py)

**Purpose**: Main analytics dashboard with 78 hierarchical KPIs

**Features**:
- ✅ Three-level KPI hierarchy (6 L1 → 24 L2 → 48 L3)
- ✅ Interactive flip cards
- ✅ Trend sparklines
- ✅ Benchmark comparisons (4 levels)
- ✅ Hospital selector
- ✅ Multi-year analysis

**Access**: Main page after login

**Documentation**: KPI_HIERARCHY_DOCUMENTATION.md

**Key File**: `dashboard.py` (main app)

---

### 2. Authentication System

**Purpose**: Secure multi-user access control

**Features**:
- ✅ Three account types (company, employee, individual)
- ✅ bcrypt password hashing
- ✅ Session management (24-hour expiration)
- ✅ Email validation
- ✅ Audit logging
- ✅ Role-based access

**Access**: Login page (`/`)

**Documentation**:
- AUTH_QUICKSTART.md (quick start)
- AUTHENTICATION_GUIDE.md (complete guide)

**Key Files**:
- `auth_models.py` - Database schema (6 tables)
- `auth_manager.py` - Auth logic
- `auth_components.py` - UI components

---

### 3. Worksheet Viewer

**Purpose**: Explore raw HCRIS worksheets

**Features**:
- ✅ All worksheets (A, B, C, D, E, G, S, etc.)
- ✅ Multi-year comparison
- ✅ Export to Excel
- ✅ Search and filter
- ✅ Line-by-line details

**Access**: Separate app (`dashboard_worksheets_v2.py`)

**Documentation**: DASHBOARD_WORKSHEETS_GUIDE.md

**Key Files**:
- `dashboard_worksheets.py` (v1)
- `dashboard_worksheets_v2.py` (v2 - recommended)

---

### 4. Valuation Dashboard

**Purpose**: Hospital valuation analysis

**Features**:
- ✅ Income statement analysis
- ✅ Expense detail breakdown
- ✅ EBITDA calculations
- ✅ Valuation multiples
- ✅ Trend analysis

**Access**: Separate app (`valuation_dashboard.py`)

**Documentation**: VALUATION_DASHBOARD_GUIDE.md

**Key File**: `valuation_dashboard.py`

---

### 5. Cloud Deployment

**Purpose**: Deploy to free hosting services

**Features**:
- ✅ One-click deployment
- ✅ Auto HTTPS
- ✅ Environment variables
- ✅ Auto-deploy on git push
- ✅ Multiple platform options

**Platforms**:
- Render (recommended - 750 hrs/mo free)
- Railway ($5 credit/mo)
- Fly.io (generous free tier)

**Documentation**:
- DEPLOY_QUICKSTART.md (5-minute guide)
- DEPLOYMENT_GUIDE.md (complete guide)

**Key Files**:
- `app.py` (production entry)
- `Procfile` (deployment config)
- `render.yaml` (Render config)
- `runtime.txt` (Python version)

---

## 📖 Documentation Map

### 🎯 Start Here (Essential)

| Document | Purpose | Time | Audience |
|----------|---------|------|----------|
| **README.md** | Project overview | 5 min | Everyone |
| **MASTER_GUIDE.md** | Complete reference (this file) | 20 min | Everyone |
| **QUICKSTART.md** | Get started locally | 10 min | Developers |

### 🔐 Authentication & Security

| Document | Purpose | Time | Audience |
|----------|---------|------|----------|
| **AUTH_QUICKSTART.md** | Set up login in 3 min | 3 min | All users |
| **AUTHENTICATION_GUIDE.md** | Complete auth reference | 30 min | Developers |

### 🚀 Deployment

| Document | Purpose | Time | Audience |
|----------|---------|------|----------|
| **DEPLOY_QUICKSTART.md** | Deploy in 5 minutes | 5 min | All users |
| **DEPLOYMENT_GUIDE.md** | All platforms + troubleshooting | 20 min | DevOps |

### 📊 Features & Usage

| Document | Purpose | Time | Audience |
|----------|---------|------|----------|
| **KPI_HIERARCHY_DOCUMENTATION.md** | 78-KPI structure | 15 min | Analysts |
| **DASHBOARD_WORKSHEETS_GUIDE.md** | Worksheet viewer guide | 10 min | Analysts |
| **VALUATION_DASHBOARD_GUIDE.md** | Valuation analysis | 15 min | Analysts |

### 🏗️ Technical

| Document | Purpose | Time | Audience |
|----------|---------|------|----------|
| **TECHNICAL_ARCHITECTURE.md** | System architecture | 30 min | Developers |
| **DATA_STRUCTURE_FOR_ANALYSTS.md** | Data model | 15 min | Developers |

### 📚 Reference

| Document | Purpose | Time | Audience |
|----------|---------|------|----------|
| **HCRIS_QUICK_REFERENCE.md** | HCRIS worksheet reference | 10 min | Analysts |
| **HCRIS_VALUATION_METHODOLOGY.md** | Valuation methodology | 20 min | Analysts |

### 🗂️ Archive (Historical)

| Document | Purpose | Status |
|----------|---------|--------|
| **ETL_MULTI_STATE_UPDATE.md** | ETL expansion notes | Archived |
| **ETL_REDESIGN_SUMMARY.md** | ETL redesign | Archived |
| **WORKSHEET_ETL_BATCH.md** | Batch processing | Archived |
| **DATABASE_BUILD_COMPLETE.md** | Build notes | Archived |

### 🧹 Maintenance

| Document | Purpose | Time |
|----------|---------|------|
| **CLEANUP_GUIDE.md** | File cleanup instructions | 5 min |

---

## 💻 Development Workflow

### Local Development Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd Hospital-Dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run with authentication
python app_with_auth.py

# 4. Access
http://localhost:8050
```

### Database Setup (If Starting Fresh)

```bash
# Run ETL pipeline
cd etl
python create_duckdb_tables.py
python create_balance_sheet.py
python create_revenue.py
python create_revenue_expenses.py
python create_costs_a000.py
python create_costs_b100.py
python create_fund_balance_changes.py

# Build optimized database
cd ../scripts
python build_database.py

# Takes 20-40 minutes for full database
```

### Development Commands

```bash
# Run different dashboards locally
python app_with_auth.py           # Main app with auth
python dashboard.py                # KPI dashboard only
python dashboard_worksheets_v2.py  # Worksheet viewer
python valuation_dashboard.py      # Valuation dashboard

# Run with production server (gunicorn)
gunicorn app:server --bind 127.0.0.1:8050

# Check Python syntax
python -m py_compile <filename>.py

# View database
sqlite3 data/auth.db
duckdb hospital_analytics.duckdb
```

---

## 🌐 Deployment Options

### Option 1: Render (Recommended)

**Why**: Easiest, 750 hrs/mo free, auto HTTPS

```bash
# 1. Push to GitHub
git push origin main

# 2. Visit render.com
# 3. New Web Service → Connect repo
# 4. Click "Create"
# 5. Done!
```

**Auto-detected**:
- ✅ Procfile
- ✅ requirements.txt
- ✅ Python version (runtime.txt)

**URL**: `https://your-app.onrender.com`

### Option 2: Railway

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

### Option 3: Fly.io

```bash
curl -L https://fly.io/install.sh | sh
fly launch
fly deploy
```

**See**: DEPLOYMENT_GUIDE.md for complete instructions

---

## 🔄 Data Pipeline

### Source Data: CMS HCRIS

**What**: Hospital Cost Report Information System
**Format**: CSV files (Form 2552-10)
**Years**: 2020-2024
**Size**: ~5,000 hospitals per year

### ETL Pipeline (12 Scripts)

```
Source CSV → DuckDB → Transformations → Parquet → Analytics DB
```

**ETL Scripts**:

| Script | Purpose | Output |
|--------|---------|--------|
| `create_duckdb_tables.py` | Load CSV to DuckDB | Source tables |
| `create_balance_sheet.py` | Transform Worksheet G | Balance sheet |
| `create_revenue.py` | Transform Worksheet G-2 | Revenue |
| `create_revenue_expenses.py` | Transform Worksheet G-3 | Revenue & expenses |
| `create_costs_a000.py` | Transform Worksheet A | Cost detail |
| `create_costs_b100.py` | Transform Worksheet B-1 | Cost allocation |
| `create_fund_balance_changes.py` | Transform Worksheet G-1 | Fund changes |
| `create_all_worksheets.py` | All worksheets | Complete data |
| `create_income_statement.py` | Income statement | Derived |
| `create_expense_detail.py` | Expense breakdown | Derived |

### Database Build

```bash
# Pre-compute KPIs and benchmarks
scripts/build_database.py

# Output: hospital_analytics.duckdb (3.5 GB)
# Contains:
# - Pre-computed KPIs for all hospitals
# - National/State/Type benchmarks
# - Optimized for fast queries
```

**Result**: Lightning-fast dashboard (no computation on query)

---

## 🔒 Security & Authentication

### Security Features

✅ **Password Security**:
- bcrypt hashing (never stores plain text)
- Strong password requirements (8+ chars, mixed case, digit)
- Salt per password

✅ **Session Security**:
- Server-side sessions
- 24-hour expiration
- Secure session IDs (32-byte random)
- HttpOnly cookies (in production)

✅ **Database Security**:
- SQL injection protection (parameterized queries)
- User input validation
- Email format validation

✅ **Audit Trail**:
- All login attempts logged
- Registration events logged
- IP address tracking (production)
- User agent tracking

### User Types

| Type | Use Case | Features |
|------|----------|----------|
| **Company** | Organizations | Admin + employees, subscription tiers |
| **Employee** | Team member | Linked to company, role-based access |
| **Individual** | Independent | Full access, personal subscription |

### Database Schema

**Tables**:
- `companies` - Company accounts
- `employees` - Employee accounts
- `individuals` - Individual accounts
- `sessions` - Active sessions
- `audit_log` - Security events
- `hospital_access` - Hospital permissions (future)

**See**: AUTHENTICATION_GUIDE.md for complete API

---

## 🔧 Troubleshooting

### Common Issues

#### "Module not found: bcrypt"
```bash
pip install bcrypt
```

#### "Database not found"
```bash
# Create auth database (automatic on first run)
python app_with_auth.py

# Or rebuild analytics database
cd scripts
python build_database.py
```

#### "Port already in use"
```bash
# Change port
PORT=8051 python app.py
```

#### "Session expired"
- Sessions expire after 24 hours
- Just log in again

#### App won't deploy
- Check logs in platform dashboard
- Verify requirements.txt is complete
- Ensure Procfile is correct

### Performance Issues

**Slow queries?**
- Use pre-computed database (build_database.py)
- Check database optimization

**Slow startup?**
- First startup on free tiers takes 30-60 seconds
- Use UptimeRobot to keep app awake

---

## 🗺️ Roadmap

### ✅ Completed (v1.0)

- [x] KPI dashboard with 78 hierarchical KPIs
- [x] Authentication system (3 user types)
- [x] Cloud deployment (Render, Railway, Fly.io)
- [x] Worksheet viewer
- [x] Valuation dashboard
- [x] Benchmark comparisons
- [x] Complete documentation

### 🚧 In Progress

- [ ] PostgreSQL support (persistent database)
- [ ] Hospital-level permissions
- [ ] Team collaboration features

### 📅 Planned (v2.0)

- [ ] Password reset via email
- [ ] Two-factor authentication (2FA)
- [ ] OAuth integration (Google, Microsoft)
- [ ] Advanced role-based access control
- [ ] Company admin dashboard
- [ ] Real-time data updates
- [ ] Custom reports and exports
- [ ] Mobile responsive improvements
- [ ] API access with API keys
- [ ] Webhook integrations

### 💡 Future Ideas

- [ ] Machine learning predictions
- [ ] Anomaly detection
- [ ] Automated insights
- [ ] Natural language queries
- [ ] White-label deployments
- [ ] Multi-tenancy
- [ ] SaaS version

---

## 📞 Support & Resources

### Documentation

- **This Guide**: Complete reference
- **Quick Starts**: 3-5 minute guides for common tasks
- **Full Guides**: Comprehensive documentation
- **API Reference**: AUTHENTICATION_GUIDE.md

### Getting Help

1. **Check documentation** in this guide
2. **Review relevant quick start** guide
3. **Check troubleshooting** section
4. **Review code comments** (well-documented)
5. **Check platform docs** (Render, Railway, etc.)

### External Resources

- **CMS HCRIS Data**: [CMS.gov](https://www.cms.gov/Research-Statistics-Data-and-Systems/Downloadable-Public-Use-Files/Cost-Reports)
- **Dash Documentation**: [plotly.com/dash](https://plotly.com/dash/)
- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Railway Docs**: [docs.railway.app](https://docs.railway.app)

---

## 🎓 Learning Path

### For End Users (Analysts)

1. ✅ Read: AUTH_QUICKSTART.md (3 min)
2. ✅ Create account and log in
3. ✅ Read: KPI_HIERARCHY_DOCUMENTATION.md (15 min)
4. ✅ Explore dashboard
5. ✅ Read: DASHBOARD_WORKSHEETS_GUIDE.md (10 min)
6. ✅ Try worksheet viewer

**Total Time**: ~30 minutes to full proficiency

### For Developers

1. ✅ Read: MASTER_GUIDE.md (this file - 20 min)
2. ✅ Read: TECHNICAL_ARCHITECTURE.md (30 min)
3. ✅ Read: AUTHENTICATION_GUIDE.md (30 min)
4. ✅ Set up locally (QUICKSTART.md - 10 min)
5. ✅ Review code structure
6. ✅ Make changes and test
7. ✅ Deploy to Render (DEPLOY_QUICKSTART.md - 5 min)

**Total Time**: ~2 hours to full understanding

### For DevOps

1. ✅ Read: DEPLOYMENT_GUIDE.md (20 min)
2. ✅ Test local deployment (5 min)
3. ✅ Deploy to platform (5 min)
4. ✅ Configure environment (10 min)
5. ✅ Set up monitoring (10 min)
6. ✅ Configure custom domain (5 min)

**Total Time**: ~1 hour to production deployment

---

## 📊 Project Statistics

### Code Metrics

- **Total Lines of Code**: ~15,000
- **Python Files**: 28
- **Documentation Files**: 20
- **Total Files**: ~60

### Features

- **Dashboards**: 4
- **KPIs**: 78 (hierarchical)
- **HCRIS Worksheets**: 15+
- **User Types**: 3
- **Deployment Platforms**: 4

### Documentation

- **Total Docs**: 20 files
- **Quick Starts**: 3
- **Full Guides**: 7
- **Reference**: 3
- **Archive**: 5

---

## 🏆 Best Practices

### For Users

1. **Use strong passwords** (8+ chars, mixed case, digit)
2. **Log out** when done on shared computers
3. **Review audit log** periodically (admin users)
4. **Backup data** if using local database

### For Developers

1. **Read documentation** before coding
2. **Test locally** before deploying
3. **Use environment variables** for config
4. **Follow project structure**
5. **Comment your code**
6. **Keep dependencies updated**

### For Deployment

1. **Set DEBUG=false** in production
2. **Use HTTPS** (automatic on all platforms)
3. **Monitor logs** regularly
4. **Set up alerts** for downtime
5. **Regular backups** of production database
6. **Test before deploying**

---

## 🎯 Summary

### What You Have

A **production-ready** hospital analytics platform with:
- ✅ Comprehensive KPI analytics (78 KPIs)
- ✅ Secure authentication (3 user types)
- ✅ Cloud deployment ready (free hosting)
- ✅ Complete documentation
- ✅ Professional UI/UX
- ✅ Scalable architecture

### What You Can Do

1. **Deploy immediately** to free cloud hosting (5 minutes)
2. **Analyze hospitals** with 78 hierarchical KPIs
3. **Benchmark performance** against peers
4. **Collaborate** with team members
5. **Explore data** via multiple dashboards
6. **Export reports** and insights

### Next Steps

1. Choose your quick start path (see top of guide)
2. Follow the appropriate guide
3. Deploy or run locally
4. Create account and start analyzing!

---

**Version**: 1.0
**Last Updated**: 2025-11-16
**Status**: Production Ready ✅
**License**: See project root

---

## 📝 Quick Reference Card

```
╔══════════════════════════════════════════════════════════╗
║         HOSPITAL DASHBOARD - QUICK REFERENCE              ║
╠══════════════════════════════════════════════════════════╣
║                                                           ║
║  🚀 DEPLOY IN 5 MIN: DEPLOY_QUICKSTART.md               ║
║  🔐 SET UP AUTH: AUTH_QUICKSTART.md                     ║
║  💻 RUN LOCALLY: python app_with_auth.py                ║
║  📖 FULL DOCS: MASTER_GUIDE.md (this file)              ║
║                                                           ║
║  🎯 Main App: http://localhost:8050                     ║
║  📊 78 KPIs: Three-level hierarchy                      ║
║  👥 Users: Companies, Employees, Individuals            ║
║  ☁️ Hosting: Render (free), Railway, Fly.io            ║
║                                                           ║
║  📁 Key Files:                                          ║
║    • app.py - Production entry                          ║
║    • app_with_auth.py - Local with auth                 ║
║    • dashboard.py - Main KPI dashboard                  ║
║    • kpi_hierarchy_config.py - 78 KPIs                  ║
║    • auth_manager.py - Authentication                    ║
║                                                           ║
║  🔑 Password: 8+ chars, uppercase, lowercase, digit     ║
║  ⏰ Sessions: 24-hour expiration                        ║
║  💾 Database: SQLite (auth), DuckDB (analytics)         ║
║  🔒 Security: bcrypt, sessions, audit log               ║
║                                                           ║
╚══════════════════════════════════════════════════════════╝
```

---

**Need help?** Start with the appropriate quick start guide, then refer back to this master guide as needed. All paths lead to success! 🎉
