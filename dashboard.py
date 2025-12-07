"""
Hospital KPI Scorecard - Interactive Dash Application

Features:
1. Interactive KPI cards with flip animation
2. Hospital and benchmark level selection
3. KPI ranking by importance (Impact × Ease of Change)
4. Trend visualizations (sparklines)
5. Benchmark comparison (National, State, Hospital Type, State+Type)
6. Color-coded performance indicators
7. Sortable and filterable KPI grid
8. Detailed table views with all data

Data Source: Parquet files (no database needed)

REFACTORED: Code organized into modular structure
- callbacks/ - All Dash callbacks organized by feature
- utils/ - Helper functions (formatting, tables, calculations)
- data_loaders/ - Data loading functions
- components/ - UI components
- pages/ - Page layouts
"""

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from pathlib import Path
import sys

from utils.logging_config import get_logger

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import configuration
from config.paths import (
    BALANCE_SHEET_OUTPUT,
    REVENUE_OUTPUT,
    REVENUE_EXPENSES_OUTPUT,
    COSTS_A000_OUTPUT,
    COSTS_B100_OUTPUT
)

# Import data manager
from data.data_manager import HospitalDataManager

# Import page layouts
from pages.layouts import get_hospital_options

# Import all callback modules
from callbacks import (
    dashboard_callbacks,
    financial_statements_callbacks,
    cost_worksheets_callbacks,
    balance_worksheets_callbacks,
    cms_worksheets_callbacks,
    valuation_callbacks
)

logger = get_logger(__name__)

# ============================================================================
# DASH APP INITIALIZATION
# ============================================================================

# Initialize app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True
)
app.config.suppress_callback_exceptions = True

# Initialize data manager
data_manager = HospitalDataManager()

logger.info("Loading hospitals from parquet files...")
hospital_options = get_hospital_options(data_manager)
logger.info(f"Hospital options ready: {len(hospital_options)} hospitals")

# ============================================================================
# APP LAYOUT
# ============================================================================

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='selected-hospital-store', data='310001'),  # Store for selected hospital (persists across navigation)
    html.Div(id='page-content')
])

# ============================================================================
# REGISTER ALL CALLBACKS
# ============================================================================

# Register dashboard callbacks (main dashboard, routing, UI interactions)
dashboard_callbacks.register_callbacks(app, data_manager, hospital_options)

# Register financial statements callbacks (balance sheet, revenue, expenses)
financial_statements_callbacks.register_callbacks(app, data_manager)

# Register cost worksheets callbacks (detailed costs, worksheet B)
cost_worksheets_callbacks.register_callbacks(app, data_manager)

# Register balance worksheets callbacks (worksheets G, G-1, G-2, G-3)
balance_worksheets_callbacks.register_callbacks(app, data_manager)

# Register CMS worksheets callbacks (generic CMS worksheets viewer)
cms_worksheets_callbacks.register_callbacks(app, data_manager)

# Register valuation callbacks (valuation analysis with sensitivity)
valuation_callbacks.register_callbacks(app, data_manager)

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    logger.info("\n" + "="*70)
    logger.info("Hospital KPI Dashboard")
    logger.info("="*70)

    # Show data source information
    if data_manager.use_database:
        logger.info(f"[OK] Data Source: DuckDB Database ({data_manager.db_path})")
        logger.info("[OK] Performance: Fast queries with indexes")
    else:
        logger.warning("[WARN] Data Source: Parquet files (no database)")
        logger.warning("[WARN] Performance: Slower queries, consider creating database")

    logger.info(f"[OK] Hospitals loaded: {len(hospital_options)}")
    logger.info("="*70)
    logger.info("\nStarting server at http://127.0.0.1:8050")
    logger.info("   Press Ctrl+C to stop\n")

    app.run(debug=True, host='127.0.0.1', port=8050)
