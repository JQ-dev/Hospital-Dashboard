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
"""

import dash
from dash import dcc, html, Input, Output, State, callback, ALL, MATCH, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.paths import (
    BALANCE_SHEET_OUTPUT,
    REVENUE_OUTPUT,
    REVENUE_EXPENSES_OUTPUT,
    COSTS_A000_OUTPUT,
    COSTS_B100_OUTPUT
)
from config.mappings import DB_COLUMN_TO_KPI_KEY, KPI_KEY_TO_DB_COLUMN
from data.data_manager import HospitalDataManager
from utils.kpi_helpers import (
    calculate_importance_score,
    calculate_dynamic_priority,
    calculate_percentile_rank,
    calculate_trend,
    create_sparkline,
    get_professional_datatable_style
)
from components.kpi_cards import (
    create_kpi_card,
    create_enhanced_level1_kpi_card,
    create_hierarchical_kpi_card
)
from pages.layouts import (
    get_hospital_options,
    get_main_dashboard_layout,
    get_level2_page_layout
)

# ============================================================================
# VALUATION FUNCTIONS
# ============================================================================

def load_valuation_income_statement(ccn, fiscal_year):
    """Load income statement data for valuation analysis"""
    con = data_manager.get_connection()
    try:
        query = """
        SELECT
            Line_Name,
            Section,
            Subsection,
            Value
        FROM income_statement_long
        WHERE Provider_Number = ?
            AND Fiscal_Year = ?
        ORDER BY Line
        """
        df = con.execute(query, [int(ccn), int(fiscal_year)]).df()
        con.close()
        return df
    except Exception as e:
        print(f"Error loading income statement for valuation: {e}")
        con.close()
        return pd.DataFrame()

def load_valuation_expense_detail(ccn, fiscal_year):
    """Load detailed expense breakdown for valuation analysis"""
    con = data_manager.get_connection()
    try:
        query = """
        SELECT
            Expense_Category,
            Category_Description,
            Category_Type,
            Column_Description,
            SUM(Value) as Total_Expense
        FROM expense_detail
        WHERE Provider_Number = ?
            AND Fiscal_Year = ?
            AND Column_Description = 'Final_Adjusted'
        GROUP BY Expense_Category, Category_Description, Category_Type, Column_Description
        ORDER BY Total_Expense DESC
        """
        df = con.execute(query, [int(ccn), int(fiscal_year)]).df()
        con.close()
        return df
    except Exception as e:
        print(f"Error loading expense detail for valuation: {e}")
        con.close()
        return pd.DataFrame()


# ============================================================================
# THREE-LEVEL KPI HIERARCHY
# Based on Hospital HCRIS Data (CMS Form 2552-10)
# ============================================================================

# Import the complete KPI hierarchy from separate config file
from kpi_hierarchy_config import (
    KPI_HIERARCHY,
    KPI_METADATA,
    get_level_1_kpis,
    get_level_2_kpis,
    get_level_3_kpis,
    get_kpi_lineage,
    flatten_kpi_hierarchy
)

# Three-Level KPI Hierarchy Structure:
# - Level 1: 6 top-level strategic KPIs (financial health, efficiency, sustainability)
# - Level 2: 4 driver KPIs per Level 1 (24 total) - key components/influencers
# - Level 3: 2 sub-driver KPIs per Level 2 (48 total) - granular breakdowns
# Total: 78 KPIs across the hierarchy

# Mapping from database column names to KPI_METADATA keys
# This allows us to show KPIs even when column names don't match metadata keys
# DB_COLUMN_TO_KPI_KEY and KPI_KEY_TO_DB_COLUMN moved to config/mappings.py
# Helper functions moved to utils/kpi_helpers.py


# ============================================================================
# DASH APP
# ============================================================================

# Initialize Flask server
import flask
server = flask.Flask(__name__)

# ============================================================================
# FLASK ROUTES FOR LANDING PAGE
# ============================================================================

@server.route('/')
def landing_page():
    """Serve the static landing page at root"""
    return flask.send_file('index.html')

@server.route('/styles.css')
def styles():
    """Serve the CSS file for landing page"""
    return flask.send_file('styles.css')

# Initialize app
app = dash.Dash(
    __name__,
    server=server,
    url_base_pathname='/app/',  # Dash app runs at /app/
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True
)
app.config.suppress_callback_exceptions = True

# Initialize data manager
data_manager = HospitalDataManager()

print("Loading hospitals from parquet files...")
hospital_options = get_hospital_options(data_manager)
print(f"Hospital options ready: {len(hospital_options)} hospitals")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_percentile_rank(value, p25, median, p75):
    """Determine which quartile the value falls into"""
    if pd.isna(value) or p25 is None or median is None or p75 is None:
        return None, 'secondary'

    if value <= p25:
        return 'Bottom Quartile', 'danger'
    elif value <= median:
        return 'Below Median', 'warning'
    elif value <= p75:
        return 'Above Median', 'info'
    else:
        return 'Top Quartile', 'success'


def create_sparkline(values, fiscal_years):
    """Create a mini sparkline chart for trend"""
    if len(values) < 2:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(fiscal_years),
        y=list(values),
        mode='lines',
        line=dict(color='#2C3E50', width=2),
        fill='tozeroy',
        fillcolor='rgba(44, 62, 80, 0.1)'
    ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=50,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        hovermode=False
    )

    return fig


def calculate_trend(values):
    """Calculate trend direction and magnitude"""
    if len(values) < 2:
        return 'stable', 0

    recent = values[0]
    older = values[1]

    if pd.isna(recent) or pd.isna(older) or older == 0:
        return 'stable', 0

    change_pct = ((recent - older) / abs(older)) * 100

    if abs(change_pct) < 2:
        return 'stable', change_pct
    elif change_pct > 0:
        return 'up', change_pct
    else:
        return 'down', change_pct


# KPI card creation functions moved to components/kpi_cards.py

# ============================================================================
# APP LAYOUT
# ============================================================================

# Helper function to format currency
def format_currency(value):
    """Format value in millions with 2 decimals (no currency symbols)"""
    if pd.isna(value) or value == 0:
        return "0.00"
    # Convert to millions with 2 decimal places
    value_in_millions = value / 1e6
    return f"{value_in_millions:.2f}"

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# URL routing callback
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """Route between main dashboard and Level 2 drill-down pages"""
    if pathname and pathname.startswith('/level2/'):
        kpi_key = pathname.split('/')[-1]
        # TODO: Get the current CCN from somewhere (for now use default)
        return get_level2_page_layout(kpi_key, ccn='310001', data_manager=data_manager)
    return get_main_dashboard_layout(hospital_options)


# ============================================================================
# CALLBACKS
# ============================================================================

@app.callback(
    [Output('hospital-name', 'children'),
     Output('hospital-type', 'children'),
     Output('benchmark-group', 'children'),
     Output('peer-count', 'children'),
     Output('kpi-cards-container', 'children')],
    [Input('hospital-dropdown', 'value'),
     Input('sort-importance', 'n_clicks'),
     Input('sort-performance', 'n_clicks'),
     Input('sort-trend', 'n_clicks')]
)
def update_dashboard(ccn, sort_imp, sort_perf, sort_trend):
    """Main callback to update entire dashboard - shows all benchmark levels on each card"""

    # Get hospital metadata
    hospital_type = data_manager.classify_hospital_type(ccn)
    state_code = str(ccn)[:2]

    # Get KPI data
    kpi_data = data_manager.calculate_kpis(ccn)

    if kpi_data.empty:
        return "N/A", "N/A", "N/A", "N/A", html.Div("No data available")

    latest_year = kpi_data['Fiscal_Year'].max()

    # Calculate Level 2 KPIs
    print(f"Calculating Level 2 KPIs for {ccn}, year {latest_year}...")
    l2_kpis = data_manager.calculate_level2_kpis(ccn, latest_year)
    if l2_kpis:
        print(f"Level 2 KPIs calculated: {sum(1 for v in l2_kpis.values() if v is not None)}/{len(l2_kpis)} KPIs")
    else:
        print("Level 2 KPIs not available (worksheet database not connected)")

    # Calculate Level 3 KPIs
    print(f"Calculating Level 3 KPIs for {ccn}, year {latest_year}...")
    l3_kpis = data_manager.calculate_level3_kpis(ccn, latest_year)
    if l3_kpis:
        print(f"Level 3 KPIs calculated: {sum(1 for v in l3_kpis.values() if v is not None)}/{len(l3_kpis)} KPIs")
    else:
        print("Level 3 KPIs not available (worksheet database not connected)")

    # Calculate ALL 4 benchmark levels (for new enhanced card design)
    # Order: State & Type (most specific), State, Hospital Type, National (broadest)
    print(f"Calculating benchmarks for {ccn} at all levels...")
    all_benchmarks = {
        'state_hospital_type': data_manager.get_benchmarks(ccn, latest_year, 'State_Hospital_Type'),
        'state': data_manager.get_benchmarks(ccn, latest_year, 'State'),
        'hospital_type': data_manager.get_benchmarks(ccn, latest_year, 'Hospital_Type'),
        'national': data_manager.get_benchmarks(ccn, latest_year, 'National')
    }
    # Use state & type (most specific) as primary benchmark for display purposes (shown in header)
    benchmark_data = all_benchmarks['state_hospital_type']
    print(f"Benchmarks calculated: State & Type={all_benchmarks['state_hospital_type']['provider_count']}, State={all_benchmarks['state']['provider_count']}, Type={all_benchmarks['hospital_type']['provider_count']}, National={all_benchmarks['national']['provider_count']} peers")

    # Create KPI cards
    kpi_cards = []
    kpi_rankings = []

    # Define the 6 Level 1 KPIs from to_do.txt - ONLY show these
    LEVEL_1_KPIS = {
        'Net_Income_Margin',                      # L1 KPI 1: Net Income Margin
        'AR_Days',                                # L1 KPI 2: Days in Net Patient AR
        'Operating_Expense_per_Adjusted_Discharge',  # L1 KPI 3: Operating Expense per Adjusted Discharge
        'Medicare_CCR',                           # L1 KPI 4: Medicare Cost-to-Charge Ratio
        'Bad_Debt_Charity_Pct',                   # L1 KPI 5: Bad Debt + Charity %
        'Current_Ratio'                           # L1 KPI 6: Current Ratio
    }

    # Loop through database columns and map to KPI_METADATA keys
    for db_col in kpi_data.columns:
        # Skip non-KPI columns
        if db_col in ['Provider_Number', 'Fiscal_Year']:
            continue

        # Map database column to KPI metadata key
        kpi_key = DB_COLUMN_TO_KPI_KEY.get(db_col, db_col)

        # Skip if not in metadata
        if kpi_key not in KPI_METADATA:
            continue

        # FILTER: Only show Level 1 KPIs from to_do.txt
        if kpi_key not in LEVEL_1_KPIS:
            continue

        # Get KPI metadata
        kpi_meta = KPI_METADATA.get(kpi_key, {})
        higher_is_better = kpi_meta.get('higher_is_better', True)

        # Get KPI values across years (use database column name)
        kpi_values = kpi_data[db_col].values
        kpi_value = kpi_values[0] if len(kpi_values) > 0 else None

        # Get benchmark (use metadata key)
        benchmark_kpis = benchmark_data.get('kpis', {})
        kpi_benchmark = benchmark_kpis.get(kpi_key, {})
        median = kpi_benchmark.get('Median')

        # Calculate DYNAMIC priority
        dynamic_priority = calculate_dynamic_priority(kpi_key, kpi_value, median, higher_is_better)

        # Calculate performance gap
        if kpi_value and median:
            if higher_is_better:
                perf_gap = median - kpi_value
            else:
                perf_gap = kpi_value - median
        else:
            perf_gap = 0

        # Calculate trend
        trend_direction, trend_pct = calculate_trend(kpi_values)

        kpi_rankings.append({
            'kpi_key': kpi_key,
            'db_column': db_col,  # Store for data access
            'dynamic_priority': dynamic_priority,
            'importance': calculate_importance_score(kpi_key),
            'perf_gap': abs(perf_gap),
            'trend_pct': abs(trend_pct),
            'kpi_value': kpi_value,
            'kpi_values': kpi_values
        })

    # Determine sort order
    ctx = dash.callback_context
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'sort-performance':
            kpi_rankings.sort(key=lambda x: x['perf_gap'], reverse=True)
        elif button_id == 'sort-trend':
            kpi_rankings.sort(key=lambda x: x['trend_pct'], reverse=True)
        else:
            kpi_rankings.sort(key=lambda x: x['dynamic_priority'], reverse=True)
    else:
        kpi_rankings.sort(key=lambda x: x['dynamic_priority'], reverse=True)

    # Create cards in sorted order (use ENHANCED cards with all benchmark levels)
    for idx, ranking in enumerate(kpi_rankings):
        card = create_enhanced_level1_kpi_card(
            kpi_key=ranking['kpi_key'],
            kpi_value=ranking['kpi_value'],
            kpi_trend_values=ranking['kpi_values'],
            fiscal_years=kpi_data['Fiscal_Year'].values,
            all_benchmarks=all_benchmarks,  # Pass all 4 benchmark levels
            rank=idx + 1,
            l2_kpis=l2_kpis,
            l3_kpis=l3_kpis,
            ccn=ccn,
            fiscal_year=latest_year,
            db_column=ranking['db_column']  # Pass database column name for benchmark lookup
        )
        # 3 cards per row: width=12 (full on mobile), lg=4 (3 per row on desktop)
        kpi_cards.append(dbc.Col(card, width=12, lg=4))

    # Layout cards in grid
    cards_grid = dbc.Row(kpi_cards)

    return (
        f"CCN {ccn}",
        hospital_type,
        benchmark_data.get('group_name', 'N/A'),
        f"{benchmark_data.get('provider_count', 0):,}",
        cards_grid
    )


# Expand/Collapse Level 2 KPIs callback
@app.callback(
    [Output({'type': 'l2-collapse', 'index': MATCH}, 'is_open'),
     Output({'type': 'expand-icon', 'index': MATCH}, 'className')],
    [Input({'type': 'expand-btn', 'index': MATCH}, 'n_clicks')],
    [State({'type': 'l2-collapse', 'index': MATCH}, 'is_open')],
    prevent_initial_call=True
)
def toggle_l2_kpis(n_clicks, is_open):
    """Toggle Level 2 KPIs visibility"""
    if n_clicks:
        new_state = not is_open
        # Change icon based on state
        icon_class = "fas fa-chevron-up me-2" if new_state else "fas fa-chevron-down me-2"
        return new_state, icon_class
    return is_open, "fas fa-chevron-down me-2"


# Level 3 expand/collapse callback
@app.callback(
    [Output({'type': 'l3-collapse', 'index': MATCH}, 'is_open'),
     Output({'type': 'expand-l3-icon', 'index': MATCH}, 'className')],
    [Input({'type': 'expand-l3-btn', 'index': MATCH}, 'n_clicks')],
    [State({'type': 'l3-collapse', 'index': MATCH}, 'is_open')],
    prevent_initial_call=True
)
def toggle_l3_kpis(n_clicks, is_open):
    """Toggle Level 3 KPIs visibility"""
    if n_clicks:
        new_state = not is_open
        # Change icon based on state
        icon_class = "fas fa-chevron-up me-1" if new_state else "fas fa-chevron-down me-1"
        return new_state, icon_class
    return is_open, "fas fa-chevron-down me-1"


# Modal callbacks
@app.callback(
    [Output("data-modal", "is_open"),
     Output("modal-title", "children"),
     Output("modal-body", "children")],
    [Input({'type': 'view-data-btn', 'index': ALL}, 'n_clicks'),
     Input("close-modal", "n_clicks")],
    [State("data-modal", "is_open"),
     State('hospital-dropdown', 'value')],
    prevent_initial_call=True
)
def toggle_modal(view_clicks, close_clicks, _is_open, ccn):
    """Handle modal open/close and populate with KPI data table"""
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update

    trigger_id = ctx.triggered[0]['prop_id']

    # If no actual click happened (just a re-render), don't update
    if not trigger_id or trigger_id == '.':
        return dash.no_update, dash.no_update, dash.no_update

    # Close modal
    if 'close-modal' in trigger_id:
        return False, "", ""

    # Open modal with KPI data - only if a button was actually clicked
    if 'view-data-btn' in trigger_id:
        # Check if this was an actual click (not None and > 0)
        if view_clicks and any(clicks for clicks in view_clicks if clicks and clicks > 0):
            # Extract KPI key from button ID
            import json
            button_id = json.loads(trigger_id.split('.')[0])
            kpi_key = button_id['index']

            # Get KPI data
            kpi_data = data_manager.calculate_kpis(ccn)

            if kpi_data.empty:
                return True, "No Data", html.Div("No data available for this hospital", className="alert alert-warning")

            # Get KPI metadata
            kpi_meta = KPI_METADATA.get(kpi_key, {})

            # Create table with all years
            table_data = kpi_data[['Fiscal_Year', kpi_key]].copy()
            table_data = table_data.sort_values('Fiscal_Year', ascending=True)

            # Format values
            fmt = kpi_meta.get('format', '.2f')
            unit = kpi_meta.get('unit', '')

            table_data['Formatted_Value'] = table_data[kpi_key].apply(
                lambda x: f"{x:{fmt}}{unit}" if pd.notna(x) else "N/A"
            )

            # Create table
            display_df = table_data[['Fiscal_Year', 'Formatted_Value']].rename(
                columns={'Fiscal_Year': 'Year', 'Formatted_Value': kpi_meta.get('name', kpi_key)}
            )

            table = dbc.Table.from_dataframe(
                display_df,
                striped=True,
                bordered=True,
                hover=True,
                responsive=True,
                className="table-sm"
            )

            # Create modal title
            title = f"{kpi_meta.get('name', kpi_key)} - Historical Data"

            # Create body
            body = html.Div([
                html.P([
                    html.Strong("Description: "),
                    kpi_meta.get('description', 'No description available')
                ], className="text-muted mb-2"),
                html.P([
                    html.Strong("Target Range: "),
                    f"{kpi_meta.get('target_range', (0, 0))[0]}-{kpi_meta.get('target_range', (0, 0))[1]}{unit}"
                ], className="text-muted mb-3"),
                table
            ])

            return True, title, body
        else:
            # Button rendered but not clicked - don't update
            return dash.no_update, dash.no_update, dash.no_update

    return dash.no_update, dash.no_update, dash.no_update


# ============================================================================
# FINANCIALS TAB CALLBACKS
# ============================================================================

# Update header hospital info (shared across tabs)
@app.callback(
    [Output('header-hospital-name', 'children'),
     Output('header-hospital-type', 'children')],
    [Input('hospital-dropdown', 'value')]
)
def update_header_info(ccn):
    """Update hospital info in header"""
    hospital_type = data_manager.classify_hospital_type(ccn)
    return f"CCN {ccn}", hospital_type


# Update footer to show data source
@app.callback(
    Output('footer-datasource', 'children'),
    [Input('hospital-dropdown', 'value')]  # Trigger on load
)
def update_footer(_):
    """Show data source in footer"""
    if data_manager.use_database:
        return f"Data Source: DuckDB Database ({data_manager.db_path}) | With Indexes for Fast Queries"
    else:
        return "Data Source: CMS HCRIS Parquet Files | No database (slower)"


# Helper functions for name cleaning and detection
def clean_re_line_name(name):
    """Remove Rev&Exp prefix from revenue & expenses line names"""
    if pd.isna(name):
        return ''
    name = str(name).strip()
    # Split on first space and take the rest
    parts = name.split(maxsplit=1)
    if len(parts) > 1:
        return parts[1].strip()
    return name

def clean_cost_line_name(name):
    """Remove Cost prefix from cost line names"""
    if pd.isna(name):
        return ''
    name = str(name).strip()
    # Cost lines may have prefixes like "Cost "
    if name.startswith('Cost '):
        return name[5:].strip()
    return name

def is_subtotal_line(name):
    """Detect if a line is a subtotal/total line"""
    if pd.isna(name):
        return False
    name = str(name).lower().strip()
    subtotal_keywords = ['total', 'subtotal', 'net ', 'gross', 'sum of']
    return any(keyword in name for keyword in subtotal_keywords)

# Helper function to create professional multi-year financial table
def create_multiyear_financial_table(df, title, statement_type):
    """Create a professionally formatted financial statement table with all years as columns"""
    if df is None or df.empty:
        return html.Div("No data available", className="alert alert-info")

    # Get unique years and sort (oldest to newest, so newest is on right)
    years = sorted(df['Fiscal_Year'].unique())

    # Pivot data to get years as columns
    # First, create a unique key for each line item and clean detail names
    # Include Line number for proper ordering

    # Handle unknown categories with sequential naming
    unknown_counters = {'major': 0, 'sub': 0}

    def get_category_name(value, level):
        """Get category name, handling blanks with sequential numbers"""
        if pd.notna(value) and str(value).strip():
            return str(value).strip()
        else:
            unknown_counters[level] += 1
            return f"Other {unknown_counters[level]}"

    if statement_type == 'balance_sheet':
        # Use Acc_name for clean names (no prefixes)
        df['major'] = df['Acc_level2'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = df['Acc_level3'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['Acc_name'].fillna('Unknown item')
        df['is_subtotal'] = df['Acc_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    elif statement_type == 'revenue':
        # Revenue hierarchy: Revenue_Center -> Revenue_Group -> Revenue_Subgroup -> Revenue_Subgroup_Detail
        df['major'] = df['Revenue_Center'].apply(lambda x: get_category_name(x, 'major') if pd.notna(x) and str(x).strip() else '')
        df['sub'] = df['Revenue_Group'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['sub2'] = df['Revenue_Subgroup'].apply(lambda x: get_category_name(x, 'sub2') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['Revenue_Subgroup_Detail'].fillna('Unknown item')
        df['is_subtotal'] = df['Revenue_Subgroup_Detail'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['sub2'] + '|' + df['Line'].astype(str)

    elif statement_type == 'revenue_expenses':
        # Revenue & Expenses: Sort by Line, indent by RE_Level (1 or 2)
        df['clean_name'] = df['RE_Line_Name'].apply(clean_re_line_name)
        df['level'] = df['RE_Level'].fillna(1).astype(int)  # Level 1 or 2
        df['detail'] = df['clean_name'].replace('', 'Unknown item')
        df['is_subtotal'] = df['clean_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        # Use line_num directly for sorting, level for grouping
        df['line_key'] = df['Line'].astype(str)

    elif statement_type == 'costs':
        # Clean Cost_Center_Name
        df['clean_name'] = df['Cost_Center_Name'].apply(clean_cost_line_name)
        df['major'] = df['Cost_Class'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = df['Cost_Allocation_Type'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['clean_name'].replace('', 'Unknown item')
        df['is_subtotal'] = df['clean_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    elif statement_type == 'cost-summary':
        # Cost Summary from B100 (lines 3000-20200, column 2600)
        df['major'] = df['Account_group'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = ''  # No subcategories for cost summary
        df['detail'] = df['Account_name'].fillna('Unknown item')
        df['is_subtotal'] = df['Account_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['Line'].astype(str)

    elif statement_type == 'fund_balance_changes':
        # Fund Balance Changes (similar structure to balance sheet)
        df['major'] = df['Acc_level1'].apply(lambda x: get_category_name(x, 'major'))
        df['sub'] = df['Acc_level2'].apply(lambda x: get_category_name(x, 'sub') if pd.notna(x) and str(x).strip() else '')
        df['detail'] = df['Acc_name'].fillna('Unknown item')
        df['is_subtotal'] = df['Acc_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    elif statement_type == 'detailed-costs':
        # Detailed Costs (Schedule A + B combined, unpivoted by cost component)
        # Structure: Account_name (cost center) → Cost_Component (subgroup) → Value
        df['major'] = df['Account_name'].fillna('Unknown Cost Center')
        df['sub'] = df['Cost_Component'].fillna('Unknown Component')
        df['detail'] = ''  # No detail level for unpivoted structure
        df['is_subtotal'] = df['Account_name'].apply(is_subtotal_line)
        df['line_num'] = pd.to_numeric(df['Line'].fillna('99999'), errors='coerce')
        df['line_key'] = df['major'] + '|' + df['sub'] + '|' + df['Line'].astype(str)

    else:
        return html.Div("Unknown statement type", className="alert alert-warning")

    # Pivot: one row per line_key, columns for each year
    # Include line_num and is_subtotal in index for sorting
    # Dynamically build index columns based on statement type
    index_cols = ['line_key']

    if 'major' in df.columns:
        # For balance_sheet, revenue, costs (hierarchical structure)
        index_cols.extend(['major', 'sub'])
        if 'sub2' in df.columns:
            index_cols.append('sub2')
        if 'sub3' in df.columns:
            index_cols.append('sub3')
    elif 'level' in df.columns:
        # For revenue_expenses (flat structure with level)
        index_cols.append('level')

    index_cols.extend(['detail', 'line_num', 'is_subtotal'])

    pivot_df = df.pivot_table(
        index=index_cols,
        columns='Fiscal_Year',
        values='Value',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Group data by major categories (with support for up to 4 levels)
    # Skip grouping for revenue_expenses (it uses flat structure)
    grouped_data = {}

    if statement_type != 'revenue_expenses':
        for _, row in pivot_df.iterrows():
            major = row['major']
            sub = row['sub']
            sub2 = row.get('sub2', '')
            sub3 = row.get('sub3', '')
            detail = row['detail']
            line_num = row['line_num']
            is_subtotal = row['is_subtotal']

            # Get values for each year
            year_values = {year: row.get(year, 0) for year in years}

            # Build nested structure: major -> sub -> sub2 -> sub3 -> items
            if major not in grouped_data:
                grouped_data[major] = {}

            sub_key = sub if sub else '_items'
            if sub_key not in grouped_data[major]:
                grouped_data[major][sub_key] = {}

            # For revenue with 4 levels, use sub2 as next level
            if sub2:
                sub2_key = sub2 if sub2 else '_items'
                if sub2_key not in grouped_data[major][sub_key]:
                    grouped_data[major][sub_key][sub2_key] = {}

                if sub3:
                    sub3_key = sub3 if sub3 else '_items'
                    if sub3_key not in grouped_data[major][sub_key][sub2_key]:
                        grouped_data[major][sub_key][sub2_key][sub3_key] = []

                    grouped_data[major][sub_key][sub2_key][sub3_key].append({
                        'detail': detail,
                        'line_num': line_num,
                        'is_subtotal': is_subtotal,
                        'year_values': year_values
                    })
                else:
                    # 3 levels only
                    if '_items' not in grouped_data[major][sub_key][sub2_key]:
                        grouped_data[major][sub_key][sub2_key]['_items'] = []
                    grouped_data[major][sub_key][sub2_key]['_items'].append({
                        'detail': detail,
                        'line_num': line_num,
                        'is_subtotal': is_subtotal,
                        'year_values': year_values
                    })
            else:
                # 2 levels only (original logic)
                if '_items' not in grouped_data[major][sub_key]:
                    grouped_data[major][sub_key]['_items'] = []
                grouped_data[major][sub_key]['_items'].append({
                    'detail': detail,
                    'line_num': line_num,
                    'is_subtotal': is_subtotal,
                    'year_values': year_values
                })

    # Build table rows
    table_rows = []

    # Helper function to calculate totals recursively
    def calc_totals_recursive(data, years):
        totals = {year: 0 for year in years}
        if isinstance(data, list):
            # Base case: list of items
            for item in data:
                if not item.get('is_subtotal', False):
                    for year in years:
                        totals[year] += item['year_values'].get(year, 0)
        elif isinstance(data, dict):
            # Recursive case: dict of sub-categories
            for value in data.values():
                sub_totals = calc_totals_recursive(value, years)
                for year in years:
                    totals[year] += sub_totals[year]
        return totals

    # Helper function to get minimum line number from nested structure
    def get_min_line_num(data):
        """Recursively find the minimum line number in a nested structure"""
        if isinstance(data, list):
            # Base case: list of items
            return min([item['line_num'] for item in data], default=999999)
        elif isinstance(data, dict):
            # Recursive case: dict of sub-categories
            min_nums = []
            for key, value in data.items():
                if key != '_items':
                    min_nums.append(get_min_line_num(value))
                else:
                    # _items is a list
                    min_nums.append(get_min_line_num(value))
            return min(min_nums, default=999999) if min_nums else 999999
        return 999999

    # Use statement-specific rendering
    if statement_type == 'revenue_expenses':
        # Revenue & Expenses: Simple rendering sorted by line, indented by level (1 or 2)
        sorted_items = sorted(pivot_df.to_dict('records'), key=lambda x: x['line_num'])

        for item in sorted_items:
            level = item.get('level', 1)
            detail = item['detail']
            is_subtotal = item.get('is_subtotal', False)

            # Determine indentation based on level
            if level == 1:
                padding_class = "ps-2"
                row_class = "table-secondary"
                use_bold = True
            else:  # level == 2
                padding_class = "ps-4"
                row_class = ""
                use_bold = is_subtotal

            # Create row
            if use_bold or is_subtotal:
                row_cells = [html.Td(html.Strong(detail), className=padding_class)]
            else:
                row_cells = [html.Td(detail, className=padding_class)]

            for year in years:
                value = item.get(year, 0)
                if use_bold or is_subtotal:
                    row_cells.append(html.Td(html.Strong(format_currency(value)), className="text-end"))
                else:
                    row_cells.append(html.Td(format_currency(value), className="text-end"))

            if is_subtotal:
                table_rows.append(html.Tr(row_cells, className="table-info"))
            elif row_class:
                table_rows.append(html.Tr(row_cells, className=row_class))
            else:
                table_rows.append(html.Tr(row_cells))

    elif statement_type == 'revenue':
        # Revenue-specific rendering: 3 levels (Revenue_Center -> Revenue_Group -> Revenue_Subgroup -> Detail)
        for major, subcats in sorted(grouped_data.items()):
            # Level 1: Revenue_Center (major) - ps-2
            major_totals = calc_totals_recursive(subcats, years)
            major_row_cells = [html.Td(html.Strong(major), className="text-uppercase ps-2")]
            for year in years:
                major_row_cells.append(
                    html.Td(html.Strong(format_currency(major_totals[year])), className="text-end")
                )
            table_rows.append(html.Tr(major_row_cells, className="table-primary"))

            # Level 2: Revenue_Group (sub) - ps-3 - sort by minimum line number
            for sub, sub_data in sorted(subcats.items(), key=lambda x: get_min_line_num(x[1])):
                if sub and sub != '_items':
                    sub_totals = calc_totals_recursive(sub_data, years)
                    sub_row_cells = [html.Td(html.Strong(sub), className="ps-3")]
                    for year in years:
                        sub_row_cells.append(
                            html.Td(html.Strong(format_currency(sub_totals[year])), className="text-end")
                        )
                    table_rows.append(html.Tr(sub_row_cells, className="table-secondary"))

                    # Level 3: Revenue_Subgroup (sub2) - ps-4 - sort by minimum line number
                    if isinstance(sub_data, dict):
                        for sub2, items_data in sorted(sub_data.items(), key=lambda x: get_min_line_num(x[1]) if x[0] != '_items' else 0):
                            if sub2 and sub2 != '_items':
                                sub2_totals = calc_totals_recursive(items_data, years)
                                sub2_row_cells = [html.Td(sub2, className="ps-4 fw-bold")]
                                for year in years:
                                    sub2_row_cells.append(
                                        html.Td(format_currency(sub2_totals[year]), className="text-end")
                                    )
                                table_rows.append(html.Tr(sub2_row_cells, style={'background-color': '#f8f9fa'}))

                            # Detail items: Revenue_Subgroup_Detail - ps-5
                            items_list = items_data.get('_items', []) if isinstance(items_data, dict) else items_data
                            if isinstance(items_list, list):
                                sorted_items = sorted(items_list, key=lambda x: x['line_num'])
                                for item in sorted_items:
                                    is_subtotal = item.get('is_subtotal', False)
                                    if is_subtotal:
                                        detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-5 fw-bold")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                                    else:
                                        detail_row_cells = [html.Td(item['detail'], className="ps-5")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells))
    else:
        # Generic rendering for other statement types (balance_sheet, revenue_expenses, costs)

        # Sort major categories - use line numbers for costs, custom order for balance sheet
        if statement_type == 'balance_sheet' or statement_type == 'fund_balance_changes':
            # For balance sheet: Assets first, then Liabilities, then Fund Balances
            def sort_major(item):
                major = item[0]
                if major == 'Assets':
                    return '0'
                elif major == 'Liabilities':
                    return '1'
                elif 'Fund' in major or 'Equity' in major or 'Balance' in major:
                    return '2'
                else:
                    return '3_' + major  # Other categories at end
            sorted_majors = sorted(grouped_data.items(), key=sort_major)
        else:
            # For costs and other statements: sort by minimum line number
            sorted_majors = sorted(grouped_data.items(), key=lambda x: get_min_line_num(x[1]))

        for major, subcats in sorted_majors:
            # Calculate major category totals for each year
            major_totals = calc_totals_recursive(subcats, years)

            # Major category header row
            major_row_cells = [html.Td(html.Strong(major), className="text-uppercase ps-2")]
            for year in years:
                major_row_cells.append(
                    html.Td(html.Strong(format_currency(major_totals[year])), className="text-end")
                )
            table_rows.append(html.Tr(major_row_cells, className="table-primary"))

            # Process subcategories (level 2) - sort by minimum line number
            for subcat, sub_data in sorted(subcats.items(), key=lambda x: get_min_line_num(x[1])):
                if subcat and subcat != '_items':
                    # Subcategory header row (Level 2)
                    subcat_totals = calc_totals_recursive(sub_data, years)
                    subcat_row_cells = [html.Td(f"  {subcat}", className="fw-bold ps-3")]
                    for year in years:
                        subcat_row_cells.append(
                            html.Td(format_currency(subcat_totals[year]), className="text-end fw-bold")
                        )
                    table_rows.append(html.Tr(subcat_row_cells, className="table-secondary"))

                # Check if sub_data contains another level or items
                if isinstance(sub_data, dict):
                    for sub2_key, sub2_data in sorted(sub_data.items(), key=lambda x: get_min_line_num(x[1]) if x[0] != '_items' else 0):
                        if sub2_key and sub2_key != '_items':
                            # Level 3 header (sub2)
                            sub2_totals = calc_totals_recursive(sub2_data, years)
                            sub2_row_cells = [html.Td(f"    {sub2_key}", className="fw-bold ps-4")]
                            for year in years:
                                sub2_row_cells.append(
                                    html.Td(format_currency(sub2_totals[year]), className="text-end")
                                )
                            table_rows.append(html.Tr(sub2_row_cells, style={'background-color': '#f8f9fa'}))

                        # Check if sub2_data contains another level or items
                        if isinstance(sub2_data, dict):
                            for sub3_key, sub3_data in sorted(sub2_data.items(), key=lambda x: get_min_line_num(x[1]) if x[0] != '_items' else 0):
                                if sub3_key and sub3_key != '_items':
                                    # Level 4 header (sub3)
                                    sub3_totals = calc_totals_recursive(sub3_data, years)
                                    sub3_row_cells = [html.Td(f"      {sub3_key}", className="ps-5")]
                                    for year in years:
                                        sub3_row_cells.append(
                                            html.Td(format_currency(sub3_totals[year]), className="text-end")
                                        )
                                    table_rows.append(html.Tr(sub3_row_cells, style={'background-color': '#fafafa'}))

                                # Render items at level 5 (detail items under level 4 header)
                                items_list = sub3_data if isinstance(sub3_data, list) else sub3_data.get('_items', [])
                                sorted_items = sorted(items_list, key=lambda x: x['line_num'])
                                for item in sorted_items:
                                    is_subtotal = item.get('is_subtotal', False)
                                    if is_subtotal:
                                        # Subtotals at level 5 (indented under level 4)
                                        detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-6 fw-bold")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                                    else:
                                        # Regular detail items at level 5
                                        detail_row_cells = [html.Td(item['detail'], className="ps-6")]
                                        for year in years:
                                            detail_row_cells.append(
                                                html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                            )
                                        table_rows.append(html.Tr(detail_row_cells))
                        elif isinstance(sub2_data, list):
                            # Items directly at level 4 (under level 3 header)
                            sorted_items = sorted(sub2_data, key=lambda x: x['line_num'])
                            for item in sorted_items:
                                is_subtotal = item.get('is_subtotal', False)
                                if is_subtotal:
                                    # Subtotals at level 4
                                    detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-5 fw-bold")]
                                    for year in years:
                                        detail_row_cells.append(
                                            html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                        )
                                    table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                                else:
                                    # Regular detail items at level 4
                                    detail_row_cells = [html.Td(item['detail'], className="ps-5")]
                                    for year in years:
                                        detail_row_cells.append(
                                            html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                        )
                                    table_rows.append(html.Tr(detail_row_cells))
                elif isinstance(sub_data, list):
                    # Items directly at level 3 (under level 2 header, original 2-level structure)
                    sorted_items = sorted(sub_data, key=lambda x: x['line_num'])
                    for item in sorted_items:
                        is_subtotal = item.get('is_subtotal', False)
                        if is_subtotal:
                            # Subtotals at level 3
                            detail_row_cells = [html.Td(html.Strong(item['detail']), className="ps-4 fw-bold")]
                            for year in years:
                                detail_row_cells.append(
                                    html.Td(html.Strong(format_currency(item['year_values'].get(year, 0))), className="text-end fw-bold")
                                )
                            table_rows.append(html.Tr(detail_row_cells, className="table-info"))
                        else:
                            # Regular detail items at level 3
                            detail_row_cells = [html.Td(item['detail'], className="ps-4")]
                            for year in years:
                                detail_row_cells.append(
                                    html.Td(format_currency(item['year_values'].get(year, 0)), className="text-end")
                                )
                            table_rows.append(html.Tr(detail_row_cells))

    # Create table header with years - Professional styling
    header_cells = [html.Th("Account", className="text-start",
                           style={'min-width': '300px', 'backgroundColor': '#34495e', 'color': 'white',
                                  'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'})]
    for year in years:
        header_cells.append(html.Th(str(int(year)), className="text-end",
                                   style={'min-width': '130px', 'backgroundColor': '#34495e', 'color': 'white',
                                          'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'}))

    # Create table with professional styling
    table = dbc.Table([
        html.Thead(html.Tr(header_cells)),
        html.Tbody(table_rows)
    ], bordered=True, hover=True, responsive=True, className="table-sm",
       style={'font-size': '0.9rem', 'borderRadius': '8px', 'overflow': 'hidden',
              'boxShadow': '0 2px 8px rgba(0,0,0,0.08)', 'border': '1px solid #dee2e6'})

    return html.Div([
        html.H5(title, className="mb-3",
               style={'color': '#2c3e50', 'fontWeight': '600', 'fontSize': '1.3rem'}),
        html.P([
            html.Strong("Note: "),
            f"All amounts in millions (USD). Showing {len(years)} fiscal years: {min(years)} - {max(years)}"
        ], className="text-muted mb-3", style={'fontSize': '0.95rem'}),
        html.Div(table, style={'overflowX': 'auto'})
    ])


# Load Balance Sheet data
@app.callback(
    Output('balance-sheet-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('fund-type-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_balance_sheet(ccn, fund_type, active_subtab):
    """Load and display balance sheet for all years, filtered by fund type"""
    # Only load if this tab is active
    if active_subtab != 'subtab-balance-sheet':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    if not fund_type:
        fund_type = 'General Fund'

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Query database table directly (FAST with indexes)
            # Use CASE statement to create Column_name from Column if it doesn't exist
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Acc_level1, Acc_level2, Acc_level3, Line, 
                    CASE
                        WHEN "Column" = '00100' THEN 'General Fund'
                        WHEN "Column" = '00200' THEN 'Specific Purpose Fund'
                        WHEN "Column" = '00300' THEN 'Endowment Fund'
                        WHEN "Column" = '00400' THEN 'Plant Fund'
                        ELSE "Column"
                    END as Column_name,
                    Acc_name,
                    Value
                FROM balance_sheet
                WHERE Provider_Number = ?
                  AND CASE
                        WHEN "Column" = '00100' THEN 'General Fund'
                        WHEN "Column" = '00200' THEN 'Specific Purpose Fund'
                        WHEN "Column" = '00300' THEN 'Endowment Fund'
                        WHEN "Column" = '00400' THEN 'Plant Fund'
                        ELSE "Column"
                      END = ?
                ORDER BY Fiscal_Year, Line
            """, [int(ccn), fund_type]).df()
        else:
            # Fallback to parquet (has Column_name field)
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Acc_level1, Acc_level2, Acc_level3, Line, Column_name, Acc_name,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ? AND Column_name = ?
                ORDER BY Fiscal_Year, Line
            """, [data_manager.balance_sheet_path, int(ccn), fund_type]).df()

        con.close()

        if df.empty:
            return html.Div(f"No balance sheet data available for this hospital in {fund_type}", className="alert alert-warning")

        return create_multiyear_financial_table(df, f"Balance Sheet - {fund_type}", 'balance_sheet')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading balance sheet: {str(e)}", className="alert alert-danger")


# Load Revenue data
@app.callback(
    Output('revenue-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_revenue(ccn, active_subtab):
    """Load and display revenue detail for all years"""
    # Only load if this tab is active
    if active_subtab != 'subtab-revenue':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Query database table directly (FAST with indexes)
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, Revenue_Group, Revenue_Subgroup, Revenue_Subgroup_Detail, Revenue_Center,
                    Value
                FROM revenue
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, Line 
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, Revenue_Group, Revenue_Subgroup, Revenue_Subgroup_Detail, Revenue_Center,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, Line 
            """, [data_manager.revenue_path, int(ccn)]).df()

        con.close()

        if df.empty:
            return html.Div("No revenue data available for this hospital", className="alert alert-warning")

        return create_multiyear_financial_table(df, "Revenue Detail", 'revenue')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading revenue: {str(e)}", className="alert alert-danger")


# Load Revenue & Expenses data
@app.callback(
    Output('revenue-expenses-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_revenue_expenses(ccn, active_subtab):
    """Load and display revenue & expenses statement for all years"""
    # Only load if this tab is active
    if active_subtab != 'subtab-revenue-expenses':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Query database table directly (FAST with indexes)
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, RE_Report, RE_Account, RE_Line_Name,
                    COALESCE(RE_Level, 999) as RE_Level,
                    Value
                FROM revenue_expenses
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, RE_Level, RE_Report, Line
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, RE_Report, RE_Account, RE_Line_Name,
                    COALESCE(RE_Level, 999) as RE_Level,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, RE_Level, RE_Report, Line
            """, [data_manager.revenue_expenses_path, int(ccn)]).df()

        con.close()

        if df.empty:
            return html.Div("No revenue & expenses data available for this hospital", className="alert alert-warning")

        return create_multiyear_financial_table(df, "Revenue & Expenses Statement", 'revenue_expenses')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading revenue & expenses: {str(e)}", className="alert alert-danger")


# Load Cost Summary data (from B100, lines 3000-20200, column 2600)
@app.callback(
    Output('cost-summary-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_cost_summary(ccn, active_subtab):
    """Load and display cost summary from B100 worksheet"""
    # Only load if this tab is active (important for performance!)
    if active_subtab != 'subtab-cost-summary':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Query database table directly (FAST with indexes)
            # Filter: Lines 3000-20200, Column 2600 (Total)
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    CAST(Line AS INTEGER) as Line,
                    Account_group,
                    Account_name,
                    Value
                FROM costs_b100
                WHERE Provider_Number = ?
                  AND CAST(Line AS INTEGER) >= 3000
                  AND CAST(Line AS INTEGER) <= 20200
                  AND "Column" = '02600'
                ORDER BY Fiscal_Year, CAST(Line AS INTEGER)
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet
            costs_b100_path = str(COSTS_B100_OUTPUT / '**/*.parquet')
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    CAST(Line AS INTEGER) as Line,
                    Account_group,
                    Account_name,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                  AND CAST(Line AS INTEGER) >= 3000
                  AND CAST(Line AS INTEGER) <= 20200
                  AND "Column" = '02600'
                ORDER BY Fiscal_Year, CAST(Line AS INTEGER)
            """, [costs_b100_path, int(ccn)]).df()

        con.close()

        if df.empty:
            return html.Div([
                html.H5("Cost Summary Data Unavailable", className="alert-heading"),
                html.P([
                    "Cost Summary data is currently unavailable due to a known data quality issue with the B100 worksheet. ",
                    "The summary lines (3000-20200) in the CMS HCRIS data lack provider identifiers."
                ]),
                html.P([
                    "Please use the ",
                    html.Strong("Costs Detail"),
                    " tab instead for comprehensive cost center analysis."
                ]),
                html.P([
                    html.Em("Note: This will be fixed in a future ETL update.")
                ], className="mb-0")
            ], className="alert alert-warning")

        return create_multiyear_financial_table(df, "Cost Summary", 'cost-summary')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading cost summary: {str(e)}", className="alert alert-danger")


# Populate year dropdown for Detailed Costs
@app.callback(
    Output('detailed-costs-year-dropdown', 'options'),
    Output('detailed-costs-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_detailed_costs_years(ccn, active_subtab):
    """Populate available years for detailed costs when hospital is selected"""
    if active_subtab != 'subtab-detailed-costs' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM costs_a000
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            costs_a000_path = str(COSTS_A000_OUTPUT / '**/*.parquet')
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [costs_a000_path, int(ccn)]).df()
        con.close()

        if years_df.empty:
            return [], None

        years = years_df['Fiscal_Year'].tolist()
        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])  # Most recent year
        return options, default_value
    except:
        return [], None


# Load Detailed Costs data (Schedule A - Basic Table)
@app.callback(
    Output('detailed-costs-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('detailed-costs-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_detailed_costs(ccn, selected_year, active_subtab):
    """Load and display detailed costs from Schedule A for selected year"""
    # Only load if this tab is active (important for performance!)
    if active_subtab != 'subtab-detailed-costs':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    if not selected_year:
        return html.Div("Please select a fiscal year", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Simple query: get A000 data for the selected year and pivot columns based on Cost_type
            df = con.execute("""
                SELECT
                    --Line,
                    Account_group,
                    Account_name,
                    MAX(CASE WHEN "Column" = '00100' THEN Value ELSE 0 END) as Salaries,
                    MAX(CASE WHEN "Column" = '00200' THEN Value ELSE 0 END) as Other,

                    MAX(CASE WHEN "Column" = '00600' THEN Value ELSE 0 END) as Adjustments

                FROM costs_a000
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Account_name is not null
                GROUP BY Line, Account_group, Account_name
                ORDER BY CAST(Line AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet
            costs_a000_path = str(COSTS_A000_OUTPUT / '**/*.parquet')
            df = con.execute("""
                SELECT
                    Line,
                    Account_group,
                    Account_name,
                    MAX(CASE WHEN "Column" = '00100' THEN Value ELSE 0 END) as Salaries,
                    MAX(CASE WHEN "Column" = '00200' THEN Value ELSE 0 END) as Other,
                    MAX(CASE WHEN "Column" = '00600' THEN Value ELSE 0 END) as Adjustments
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                GROUP BY Line, Account_group, Account_name
                ORDER BY CAST(Line AS INTEGER)
            """, [costs_a000_path, int(ccn), int(selected_year)]).df()

        con.close()

        if df.empty:
            return html.Div(f"No detailed costs data available for fiscal year {selected_year}", className="alert alert-warning")

        # Create a simple table
        from dash import dash_table

        # Format table with professional styling
        pro_style = get_professional_datatable_style()

        table = dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[
                {'name': 'Line', 'id': 'Line'},
                {'name': 'Account Group', 'id': 'Account_group'},
                {'name': 'Account Name', 'id': 'Account_name'},
                {'name': 'Salaries', 'id': 'Salaries', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
                {'name': 'Other', 'id': 'Other', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
                {'name': 'Adjustments', 'id': 'Adjustments', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
            ],
            style_table=pro_style['style_table'],
            style_cell=pro_style['style_cell'],
            style_cell_conditional=pro_style['style_cell_conditional'] + [
                {
                    'if': {'column_id': 'Account_group'},
                    'fontWeight': '600',
                    'color': '#5a6c7d'
                },
                {
                    'if': {'column_id': 'Account_name'},
                    'minWidth': '200px',
                    'fontWeight': '500'
                }
            ],
            style_header=pro_style['style_header'],
            style_data=pro_style['style_data'],
            style_data_conditional=pro_style['style_data_conditional'],
            page_size=50,
            filter_action='native',
            sort_action='native'
        )

        return html.Div([
            html.H5(f"Worksheet A - Cost Report (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading detailed costs: {str(e)}", className="alert alert-danger")


# Populate year dropdown for Worksheet B
@app.callback(
    Output('worksheet-b-year-dropdown', 'options'),
    Output('worksheet-b-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_worksheet_b_years(ccn, active_subtab):
    """Populate available years for worksheet B when hospital is selected"""
    if active_subtab != 'subtab-worksheet-b' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM costs_b100
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            costs_b100_path = str(COSTS_B100_OUTPUT / '**/*.parquet')
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [costs_b100_path, int(ccn)]).df()
        con.close()

        if years_df.empty:
            return [], None

        years = years_df['Fiscal_Year'].tolist()
        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])  # Most recent year
        return options, default_value
    except Exception as e:
        return [], None


# Load Worksheet B data
@app.callback(
    Output('worksheet-b-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('worksheet-b-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_worksheet_b(ccn, selected_year, active_subtab):
    """Load and display worksheet B (Schedule B-1 - Overhead Costs) for selected year"""
    # Only load if this tab is active (important for performance!)
    if active_subtab != 'subtab-worksheet-b':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    if not selected_year:
        return html.Div("Please select a fiscal year", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Get all overhead centers with their column values for sorting
            df = con.execute("""
                SELECT
                    Line,
                    Account_group,
                    Account_name,
                    "Column",
                    Overhead_center,
                    Value
                FROM costs_b100
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Account_name IS NOT NULL
                    AND Overhead_center IS NOT NULL
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet
            costs_b100_path = str(COSTS_B100_OUTPUT / '**/*.parquet')
            df = con.execute("""
                SELECT
                    Line,
                    Account_group,
                    Account_name,
                    "Column",
                    Overhead_center,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Account_name IS NOT NULL
                    AND Overhead_center IS NOT NULL
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [costs_b100_path, int(ccn), int(selected_year)]).df()

        con.close()

        if df.empty:
            return html.Div(f"No worksheet B data available for fiscal year {selected_year}", className="alert alert-warning")

        # Create mapping of Overhead_center to Column for sorting
        column_mapping = df[['Overhead_center', 'Column']].drop_duplicates()
        column_mapping['Column_Int'] = column_mapping['Column'].astype(int)
        column_mapping = column_mapping.sort_values('Column_Int')
        overhead_order = column_mapping['Overhead_center'].tolist()

        # Pivot the dataframe to have overhead centers as columns
        pivot_df = df.pivot_table(
            index=['Line', 'Account_group', 'Account_name'],
            columns='Overhead_center',
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Reorder columns based on Column value
        base_cols = ['Line', 'Account_group', 'Account_name']
        ordered_overhead_cols = [col for col in overhead_order if col in pivot_df.columns]
        pivot_df = pivot_df[base_cols + ordered_overhead_cols]

        # Create a simple table
        from dash import dash_table

        # Build column definitions dynamically based on overhead centers present
        columns = [
            {'name': 'Line', 'id': 'Line'},
            {'name': 'Account Group', 'id': 'Account_group'},
            {'name': 'Account Name', 'id': 'Account_name'},
        ]

        # Add columns for each overhead center (already sorted by Column value)
        for col in pivot_df.columns[3:]:  # Skip Line, Account_group, Account_name
            columns.append({
                'name': col,
                'id': col,
                'type': 'numeric',
                'format': {'specifier': '$,.0f'}
            })

        # Format table with professional styling
        pro_style = get_professional_datatable_style()

        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table=pro_style['style_table'],
            style_cell=pro_style['style_cell'],
            style_cell_conditional=pro_style['style_cell_conditional'] + [
                {
                    'if': {'column_id': 'Account_group'},
                    'fontWeight': '600',
                    'color': '#5a6c7d'
                },
                {
                    'if': {'column_id': 'Account_name'},
                    'minWidth': '200px',
                    'fontWeight': '500'
                }
            ],
            style_header=pro_style['style_header'],
            style_data=pro_style['style_data'],
            style_data_conditional=pro_style['style_data_conditional'],
            page_size=50,
            filter_action='native',
            sort_action='native'
        )

        return html.Div([
            html.H5(f"Worksheet B - Overhead Costs (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet B: {str(e)}", className="alert alert-danger")


# Populate year dropdown for Worksheet G
@app.callback(
    Output('worksheet-g-year-dropdown', 'options'),
    Output('worksheet-g-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_worksheet_g_years(ccn, active_subtab):
    """Populate available years for worksheet G when hospital is selected"""
    if active_subtab != 'subtab-worksheet-g' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM balance_sheet
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            balance_sheet_path = str(BALANCE_SHEET_OUTPUT / '**/*.parquet')
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [balance_sheet_path, int(ccn)]).df()
        con.close()

        if years_df.empty:
            return [], None

        years = years_df['Fiscal_Year'].tolist()
        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])  # Most recent year
        return options, default_value
    except Exception as e:
        return [], None


# Load Worksheet G data
@app.callback(
    Output('worksheet-g-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('worksheet-g-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_worksheet_g(ccn, selected_year, active_subtab):
    """Load and display worksheet G (Balance Sheet) for selected year"""
    # Only load if this tab is active (important for performance!)
    if active_subtab != 'subtab-worksheet-g':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    if not selected_year:
        return html.Div("Please select a fiscal year", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Get balance sheet data with Line and Column for sorting
            df = con.execute("""
                SELECT
                    Line,
                    "Column",
                    Acc_level2,
                    Acc_level3,
                    Acc_name,
                    Column_name,
                    Value
                FROM balance_sheet
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Acc_name IS NOT NULL
                    AND Column_name IS NOT NULL
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet
            balance_sheet_path = str(BALANCE_SHEET_OUTPUT / '**/*.parquet')
            df = con.execute("""
                SELECT
                    Line,
                    "Column",
                    Acc_level2,
                    Acc_level3,
                    Acc_name,
                    Column_name,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Acc_name IS NOT NULL
                    AND Column_name IS NOT NULL
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [balance_sheet_path, int(ccn), int(selected_year)]).df()

        con.close()

        if df.empty:
            return html.Div(f"No worksheet G data available for fiscal year {selected_year}", className="alert alert-warning")

        # Create mapping of Column_name to Column for sorting
        column_mapping = df[['Column_name', 'Column']].drop_duplicates()
        column_mapping['Column_Int'] = column_mapping['Column'].astype(int)
        column_mapping = column_mapping.sort_values('Column_Int')
        column_order = column_mapping['Column_name'].tolist()

        # Pivot the dataframe to have Column_name as columns
        pivot_df = df.pivot_table(
            index=['Line', 'Acc_level2', 'Acc_level3', 'Acc_name'],
            columns='Column_name',
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Reorder columns based on Column value
        base_cols = ['Line', 'Acc_level2', 'Acc_level3', 'Acc_name']
        ordered_column_cols = [col for col in column_order if col in pivot_df.columns]
        pivot_df = pivot_df[base_cols + ordered_column_cols]

        # Create a simple table
        from dash import dash_table

        # Build column definitions dynamically
        columns = [
            {'name': 'Line', 'id': 'Line'},
            {'name': 'Level 2', 'id': 'Acc_level2'},
            {'name': 'Level 3', 'id': 'Acc_level3'},
            {'name': 'Account Name', 'id': 'Acc_name'},
        ]

        # Add columns for each column name (already sorted by Column value)
        for col in pivot_df.columns[4:]:  # Skip Line, Acc_level2, Acc_level3, Acc_name
            columns.append({
                'name': col,
                'id': col,
                'type': 'numeric',
                'format': {'specifier': '$,.0f'}
            })

        # Format table with professional styling
        pro_style = get_professional_datatable_style()

        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table=pro_style['style_table'],
            style_cell=pro_style['style_cell'],
            style_cell_conditional=pro_style['style_cell_conditional'] + [
                {
                    'if': {'column_id': 'Acc_level2'},
                    'fontWeight': '600',
                    'color': '#5a6c7d'
                },
                {
                    'if': {'column_id': 'Acc_name'},
                    'minWidth': '200px',
                    'fontWeight': '500'
                }
            ],
            style_header=pro_style['style_header'],
            style_data=pro_style['style_data'],
            style_data_conditional=pro_style['style_data_conditional'],
            page_size=50,
            filter_action='native',
            sort_action='native'
        )

        return html.Div([
            html.H5(f"Worksheet G - Balance Sheet (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet G: {str(e)}", className="alert alert-danger")


# ============================================================================
# WORKSHEET G-1 CALLBACKS (FUND BALANCE CHANGES)
# ============================================================================

# Populate year dropdown for Worksheet G-1
@app.callback(
    Output('worksheet-g1-year-dropdown', 'options'),
    Output('worksheet-g1-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_worksheet_g1_years(ccn, active_subtab):
    """Populate available years for worksheet G-1 when hospital is selected"""
    if active_subtab != 'subtab-worksheet-g1' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM fund_balance_changes
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet files
            fund_balance_parquet = Path('data/db_parquets/fund_balance_changes_long')
            df_list = []
            for partition_dir in fund_balance_parquet.glob('Fiscal_Year=*'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return [], None

            years_df = pd.concat(df_list, ignore_index=True)[['Fiscal_Year']].drop_duplicates()
            years_df = years_df.sort_values('Fiscal_Year', ascending=False)

        years = years_df['Fiscal_Year'].tolist()
        if not years:
            return [], None

        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])

        return options, default_value
    except Exception as e:
        print(f"Error populating worksheet G-1 years: {e}")
        import traceback
        traceback.print_exc()
        return [], None


# Load Worksheet G-1 data
@app.callback(
    Output('worksheet-g1-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('worksheet-g1-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_worksheet_g1(ccn, selected_year, active_subtab):
    """Load and display worksheet G-1 (Fund Balance Changes) for selected year"""
    if active_subtab != 'subtab-worksheet-g1':
        return html.Div()

    if not ccn or not selected_year:
        return html.Div("Please select a hospital and fiscal year.", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Get fund balance changes data with Line and Column for sorting
            df = con.execute("""
                SELECT
                    Line,
                    "Column",
                    Acc_level2,
                    Acc_level3,
                    Acc_name,
                    Value
                FROM fund_balance_changes
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                    AND Acc_name IS NOT NULL
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet files
            fund_balance_parquet = Path('data/db_parquets/fund_balance_changes_long')
            df_list = []
            for partition_dir in fund_balance_parquet.glob(f'Fiscal_Year={selected_year}'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return html.Div("No data available for this hospital and year.", className="alert alert-warning")

            df = pd.concat(df_list, ignore_index=True)
            df = df[df['Acc_name'].notna()]
            df['Line_Int'] = df['Line'].astype(int)
            df['Column_Int'] = df['Column'].astype(int)
            df = df.sort_values(['Line_Int', 'Column_Int'])

        if df.empty:
            return html.Div("No data available for this hospital and year.", className="alert alert-warning")

        # Create mapping of Column to Column for sorting (use Column code as display name)
        column_mapping = df[['Column']].drop_duplicates()
        column_mapping['Column_Int'] = column_mapping['Column'].astype(int)
        column_mapping = column_mapping.sort_values('Column_Int')
        column_order = column_mapping['Column'].tolist()

        # Pivot the dataframe to have Column as columns
        pivot_df = df.pivot_table(
            index=['Line', 'Acc_level2', 'Acc_level3', 'Acc_name'],
            columns='Column',
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Reorder columns based on Column value
        base_cols = ['Line', 'Acc_level2', 'Acc_level3', 'Acc_name']
        ordered_column_cols = [col for col in column_order if col in pivot_df.columns]
        pivot_df = pivot_df[base_cols + ordered_column_cols]

        # Create DataTable with dynamic columns
        columns = [
            {'name': 'Line', 'id': 'Line'},
            {'name': 'Level 2', 'id': 'Acc_level2'},
            {'name': 'Level 3', 'id': 'Acc_level3'},
            {'name': 'Account Name', 'id': 'Acc_name'},
        ]

        # Add value columns with currency formatting
        for col in pivot_df.columns[4:]:
            columns.append({
                'name': col,
                'id': col,
                'type': 'numeric',
                'format': {'specifier': '$,.0f'}
            })

        # Format table with professional styling
        pro_style = get_professional_datatable_style()

        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table=pro_style['style_table'],
            style_cell=pro_style['style_cell'],
            style_cell_conditional=pro_style['style_cell_conditional'] + [
                {
                    'if': {'column_id': 'Acc_level2'},
                    'fontWeight': '600',
                    'color': '#5a6c7d'
                },
                {
                    'if': {'column_id': 'Acc_name'},
                    'minWidth': '200px',
                    'fontWeight': '500'
                }
            ],
            style_header=pro_style['style_header'],
            style_data=pro_style['style_data'],
            style_data_conditional=pro_style['style_data_conditional'],
            page_size=50,
            filter_action='native',
            sort_action='native'
        )

        return html.Div([
            html.H5(f"Worksheet G-1 - Fund Balance Changes (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet G-1: {str(e)}", className="alert alert-danger")


# ============================================================================
# WORKSHEET G-2 CALLBACKS (REVENUE)
# ============================================================================

# Populate year dropdown for Worksheet G-2
@app.callback(
    Output('worksheet-g2-year-dropdown', 'options'),
    Output('worksheet-g2-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_worksheet_g2_years(ccn, active_subtab):
    """Populate available years for worksheet G-2 when hospital is selected"""
    if active_subtab != 'subtab-worksheet-g2' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM revenue
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet files
            revenue_parquet = Path('data/db_parquets/revenue_long')
            df_list = []
            for partition_dir in revenue_parquet.glob('Fiscal_Year=*'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return [], None

            years_df = pd.concat(df_list, ignore_index=True)[['Fiscal_Year']].drop_duplicates()
            years_df = years_df.sort_values('Fiscal_Year', ascending=False)

        years = years_df['Fiscal_Year'].tolist()
        if not years:
            return [], None

        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])

        return options, default_value
    except Exception as e:
        print(f"Error populating worksheet G-2 years: {e}")
        import traceback
        traceback.print_exc()
        return [], None


# Load Worksheet G-2 data
@app.callback(
    Output('worksheet-g2-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('worksheet-g2-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_worksheet_g2(ccn, selected_year, active_subtab):
    """Load and display worksheet G-2 (Revenue) for selected year"""
    if active_subtab != 'subtab-worksheet-g2':
        return html.Div()

    if not ccn or not selected_year:
        return html.Div("Please select a hospital and fiscal year.", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Get revenue data with Line and Column for sorting
            # Note: Fill nulls with 'Unknown' to avoid filtering out data
            df = con.execute("""
                SELECT
                    Line,
                    "Column",
                    COALESCE(Revenue_Group, 'Unknown') as Revenue_Group,
                    COALESCE(Revenue_Subgroup, 'Unknown') as Revenue_Subgroup,
                    COALESCE(Revenue_Subgroup_Detail, 'Unknown') as Revenue_Subgroup_Detail,
                    COALESCE(Revenue_Center, 'Unknown') as Revenue_Center,
                    Value
                FROM revenue
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet files
            revenue_parquet = Path('data/db_parquets/revenue_long')
            df_list = []
            for partition_dir in revenue_parquet.glob(f'Fiscal_Year={selected_year}'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return html.Div("No data available for this hospital and year.", className="alert alert-warning")

            df = pd.concat(df_list, ignore_index=True)
            # Fill nulls with 'Unknown' instead of filtering them out
            df['Revenue_Group'] = df['Revenue_Group'].fillna('Unknown')
            df['Revenue_Subgroup'] = df['Revenue_Subgroup'].fillna('Unknown')
            df['Revenue_Subgroup_Detail'] = df['Revenue_Subgroup_Detail'].fillna('Unknown')
            df['Revenue_Center'] = df['Revenue_Center'].fillna('Unknown')
            df['Line_Int'] = df['Line'].astype(int)
            df['Column_Int'] = df['Column'].astype(int)
            df = df.sort_values(['Line_Int', 'Column_Int'])

        if df.empty:
            return html.Div("No data available for this hospital and year.", className="alert alert-warning")

        # Create mapping of Revenue_Center to Column for sorting
        column_mapping = df[['Revenue_Center', 'Column']].drop_duplicates()
        column_mapping['Column_Int'] = column_mapping['Column'].astype(int)
        column_mapping = column_mapping.sort_values('Column_Int')
        column_order = column_mapping['Revenue_Center'].tolist()

        # Pivot the dataframe to have Revenue_Center as columns
        pivot_df = df.pivot_table(
            index=['Line', 'Revenue_Group', 'Revenue_Subgroup', 'Revenue_Subgroup_Detail'],
            columns='Revenue_Center',
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Reorder columns based on Column value
        base_cols = ['Line', 'Revenue_Group', 'Revenue_Subgroup', 'Revenue_Subgroup_Detail']
        ordered_column_cols = [col for col in column_order if col in pivot_df.columns]
        pivot_df = pivot_df[base_cols + ordered_column_cols]

        # Create DataTable with dynamic columns
        columns = [
            {'name': 'Line', 'id': 'Line'},
            {'name': 'Revenue Group', 'id': 'Revenue_Group'},
            {'name': 'Revenue Subgroup', 'id': 'Revenue_Subgroup'},
            {'name': 'Revenue Detail', 'id': 'Revenue_Subgroup_Detail'},
        ]

        # Add value columns with currency formatting
        for col in pivot_df.columns[4:]:
            columns.append({
                'name': col,
                'id': col,
                'type': 'numeric',
                'format': {'specifier': '$,.0f'}
            })

        # Format table with professional styling
        pro_style = get_professional_datatable_style()

        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table=pro_style['style_table'],
            style_cell=pro_style['style_cell'],
            style_cell_conditional=pro_style['style_cell_conditional'] + [
                {
                    'if': {'column_id': 'Revenue_Group'},
                    'fontWeight': '600',
                    'color': '#5a6c7d'
                },
                {
                    'if': {'column_id': 'Revenue_Subgroup_Detail'},
                    'minWidth': '200px',
                    'fontWeight': '500'
                }
            ],
            style_header=pro_style['style_header'],
            style_data=pro_style['style_data'],
            style_data_conditional=pro_style['style_data_conditional'],
            page_size=50,
            filter_action='native',
            sort_action='native'
        )

        return html.Div([
            html.H5(f"Worksheet G-2 - Revenue (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet G-2: {str(e)}", className="alert alert-danger")


# ============================================================================
# WORKSHEET G-3 CALLBACKS (REVENUE & EXPENSES)
# ============================================================================

# Populate year dropdown for Worksheet G-3
@app.callback(
    Output('worksheet-g3-year-dropdown', 'options'),
    Output('worksheet-g3-year-dropdown', 'value'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def populate_worksheet_g3_years(ccn, active_subtab):
    """Populate available years for worksheet G-3 when hospital is selected"""
    if active_subtab != 'subtab-worksheet-g3' or not ccn:
        return [], None

    try:
        con = data_manager.get_connection()
        if data_manager.use_database:
            years_df = con.execute("""
                SELECT DISTINCT Fiscal_Year
                FROM revenue_expenses
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year DESC
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet files
            revenue_expenses_parquet = Path('data/db_parquets/revenue_expenses_long')
            df_list = []
            for partition_dir in revenue_expenses_parquet.glob('Fiscal_Year=*'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return [], None

            years_df = pd.concat(df_list, ignore_index=True)[['Fiscal_Year']].drop_duplicates()
            years_df = years_df.sort_values('Fiscal_Year', ascending=False)

        years = years_df['Fiscal_Year'].tolist()
        if not years:
            return [], None

        options = [{'label': str(int(year)), 'value': int(year)} for year in years]
        default_value = int(years[0])

        return options, default_value
    except Exception as e:
        print(f"Error populating worksheet G-3 years: {e}")
        import traceback
        traceback.print_exc()
        return [], None


# Load Worksheet G-3 data
@app.callback(
    Output('worksheet-g3-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('worksheet-g3-year-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_worksheet_g3(ccn, selected_year, active_subtab):
    """Load and display worksheet G-3 (Revenue & Expenses) for selected year"""
    if active_subtab != 'subtab-worksheet-g3':
        return html.Div()

    if not ccn or not selected_year:
        return html.Div("Please select a hospital and fiscal year.", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Get revenue & expenses data with Line and Column for sorting
            # Use Account_Name and Column (RE_Column_Name is all NULL in the data)
            df = con.execute("""
                SELECT
                    Line,
                    "Column",
                    COALESCE(Account_Name, 'Unknown') as Account_Name,
                    Value
                FROM revenue_expenses
                WHERE Provider_Number = ?
                    AND Fiscal_Year = ?
                ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
            """, [int(ccn), int(selected_year)]).df()
        else:
            # Fallback to parquet files
            revenue_expenses_parquet = Path('data/db_parquets/revenue_expenses_long')
            df_list = []
            for partition_dir in revenue_expenses_parquet.glob(f'Fiscal_Year={selected_year}'):
                for state_dir in partition_dir.glob('State_Code=*'):
                    parquet_files = list(state_dir.glob('*.parquet'))
                    if parquet_files:
                        df_temp = pd.read_parquet(state_dir)
                        df_temp = df_temp[df_temp['Provider_Number'] == int(ccn)]
                        if not df_temp.empty:
                            df_list.append(df_temp)

            if not df_list:
                return html.Div("No data available for this hospital and year.", className="alert alert-warning")

            df = pd.concat(df_list, ignore_index=True)
            df['Account_Name'] = df['Account_Name'].fillna('Unknown')
            df['Line_Int'] = df['Line'].astype(int)
            df['Column_Int'] = df['Column'].astype(int)
            df = df.sort_values(['Line_Int', 'Column_Int'])

        if df.empty:
            return html.Div("No data available for this hospital and year.", className="alert alert-warning")

        # Create mapping of Column codes for sorting (use Column as display name)
        column_mapping = df[['Column']].drop_duplicates()
        column_mapping['Column_Int'] = column_mapping['Column'].astype(int)
        column_mapping = column_mapping.sort_values('Column_Int')
        column_order = column_mapping['Column'].tolist()

        # Pivot the dataframe to have Column as columns
        pivot_df = df.pivot_table(
            index=['Line', 'Account_Name'],
            columns='Column',
            values='Value',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Reorder columns based on Column value
        base_cols = ['Line', 'Account_Name']
        ordered_column_cols = [col for col in column_order if col in pivot_df.columns]
        pivot_df = pivot_df[base_cols + ordered_column_cols]

        # Create DataTable with dynamic columns
        columns = [
            {'name': 'Line', 'id': 'Line'},
            {'name': 'Account', 'id': 'Account_Name'},
        ]

        # Add value columns with currency formatting
        for col in pivot_df.columns[2:]:
            columns.append({
                'name': col,
                'id': col,
                'type': 'numeric',
                'format': {'specifier': '$,.0f'}
            })

        # Format table with professional styling
        pro_style = get_professional_datatable_style()

        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table=pro_style['style_table'],
            style_cell=pro_style['style_cell'],
            style_cell_conditional=pro_style['style_cell_conditional'] + [
                {
                    'if': {'column_id': 'Account_Name'},
                    'minWidth': '200px',
                    'fontWeight': '500'
                }
            ],
            style_header=pro_style['style_header'],
            style_data=pro_style['style_data'],
            style_data_conditional=pro_style['style_data_conditional'],
            page_size=50,
            filter_action='native',
            sort_action='native'
        )

        return html.Div([
            html.H5(f"Worksheet G-3 - Revenue & Expenses (Fiscal Year {selected_year})", className="mb-3"),
            table
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet G-3: {str(e)}", className="alert alert-danger")


# Load Fund Balance Changes data
@app.callback(
    Output('fund-balance-changes-content', 'children'),
    [Input('hospital-dropdown', 'value'),
     Input('financial-subtabs', 'active_tab')]
)
def load_fund_balance_changes(ccn, active_subtab):
    """Load and display fund balance changes for all years"""
    # Only load if this tab is active
    if active_subtab != 'subtab-fund-balance-changes':
        return html.Div()

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    try:
        con = data_manager.get_connection()

        if data_manager.use_database:
            # Query database table directly (FAST with indexes)
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, Acc_level1, Acc_level2, Acc_level3, Acc_name,
                    Value
                FROM fund_balance_changes
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, Line
            """, [int(ccn)]).df()
        else:
            # Fallback to parquet
            df = con.execute("""
                SELECT
                    Fiscal_Year,
                    Line, Acc_level1, Acc_level2, Acc_level3, Acc_name,
                    Value
                FROM read_parquet(?, hive_partitioning=1)
                WHERE Provider_Number = ?
                ORDER BY Fiscal_Year, Line
            """, [data_manager.balance_sheet_path, int(ccn)]).df()

        con.close()

        if df.empty:
            return html.Div("No fund balance changes data available for this hospital", className="alert alert-warning")

        # The data structure is similar to balance sheet, so we can use the same formatter
        # Just need to ensure it has the expected column structure
        return create_multiyear_financial_table(df, "Statement of Changes in Fund Balances", 'fund_balance_changes')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading fund balance changes: {str(e)}", className="alert alert-danger")


# ============================================================================
# CMS WORKSHEETS CALLBACKS
# ============================================================================

@app.callback(
    [Output('cms-hospital-dropdown', 'options'),
     Output('cms-hospital-dropdown', 'value')],
    Input('main-tabs', 'active_tab')
)
def populate_cms_hospital_dropdown(active_tab):
    """Populate hospital dropdown for CMS Worksheets tab"""
    if active_tab != 'tab-cms-worksheets':
        return [], None

    try:
        worksheets_db_path = Path(__file__).parent / 'data' / 'hospital_worksheets.duckdb'
        con = duckdb.connect(str(worksheets_db_path), read_only=True)

        providers = con.execute("""
            SELECT DISTINCT Provider_Number, state_code
            FROM provider_list
            ORDER BY state_code, Provider_Number
        """).df()

        con.close()

        options = [
            {
                'label': f"{row['Provider_Number']} ({row['state_code']})",
                'value': row['Provider_Number']
            }
            for _, row in providers.iterrows()
        ]

        # Set first hospital as default
        default_value = options[0]['value'] if options else None

        return options, default_value
    except Exception as e:
        print(f"Error loading CMS hospitals: {e}")
        return [], None


@app.callback(
    [Output('cms-year-dropdown', 'options'),
     Output('cms-year-dropdown', 'value')],
    Input('cms-hospital-dropdown', 'value')
)
def populate_cms_year_dropdown(provider_number):
    """Populate year dropdown based on selected hospital"""
    if not provider_number:
        return [], None

    try:
        worksheets_db_path = Path(__file__).parent / 'data' / 'hospital_worksheets.duckdb'
        con = duckdb.connect(str(worksheets_db_path), read_only=True)

        years = con.execute("""
            SELECT DISTINCT fiscal_year
            FROM all_worksheets
            WHERE Provider_Number = ?
            ORDER BY fiscal_year DESC
        """, [provider_number]).df()

        con.close()

        options = [{'label': str(year), 'value': year} for year in years['fiscal_year']]

        # Set most recent year as default
        default_value = options[0]['value'] if options else None

        return options, default_value
    except Exception as e:
        print(f"Error loading years: {e}")
        return [], None


@app.callback(
    Output('cms-worksheet-content', 'children'),
    [Input('cms-worksheet-dropdown', 'value'),
     Input('cms-hospital-dropdown', 'value'),
     Input('cms-year-dropdown', 'value')]
)
def update_cms_worksheet_content(worksheet_code, ccn, selected_year):
    """Update content based on selected CMS worksheet dropdown"""

    if not ccn:
        return html.Div("Please select a hospital", className="alert alert-info")

    if not selected_year:
        return html.Div("Please select a fiscal year", className="alert alert-info")

    if not worksheet_code:
        return html.Div("Please select a worksheet", className="alert alert-info")

    # worksheet_code is now directly from the dropdown value
    worksheet_code = worksheet_code.upper()

    # Worksheet names mapping
    WORKSHEET_NAMES = {
        'A000000': 'General Service Cost Centers',
        'A6000A0': 'Reclassifications',
        'A700001': 'Reconciliation of Capital Costs Centers',
        'A700002': 'Reconciliation of Capital Costs Centers',
        'A700003': 'Reconciliation of Capital Costs Centers',
        'A800000': 'Adjustments to Expenses',
        'A810000': 'Costs Incurred - Related Organizations',
        'A820010': 'Provider-Based Physicians Adjustments',
        'B000001': 'Cost Allocation - General Service Costs',
        'B000002': 'Cost Allocation - General Service Costs',
        'B100000': 'Cost Allocation - General Service Costs',
        'C000001': 'Cost Allocation - General Service Costs',
        'G000000': 'Balance Sheet',
        'G100000': 'Statement of Changes in Fund Balances',
        'G200000': 'Statement of Patient Revenues',
        'G300000': 'Statement of Revenues',
        'S000001': 'Settlement Summary',
        'S100001': 'Hospital Uncompensated & Indigent Care Data',
        'S200001': 'Hospital & Healthcare Complex ID Data',
        'S300001': 'Statistical Data',
        'S300002': 'Statistical Data',
        'S300004': 'Hospital Wage Related Costs',
        'S300005': 'Hospital Wage Related Costs',
        'S410000': 'Hospital Wage Related Costs',
        'S500000': 'Hospital Renal Dialysis Department',
    }

    worksheet_name = WORKSHEET_NAMES.get(worksheet_code, worksheet_code)

    try:
        # Connect to the worksheets database
        worksheets_db_path = Path(__file__).parent / 'data' / 'hospital_worksheets.duckdb'
        con = duckdb.connect(str(worksheets_db_path), read_only=True)

        # Query worksheet data
        # Sanitize worksheet_code to prevent SQL injection (only allow alphanumeric characters)
        if not worksheet_code.replace('_', '').isalnum():
            con.close()
            return html.Div(f"Invalid worksheet code", className="alert alert-danger")

        table_name = f'worksheet_{worksheet_code.lower()}'

        df = con.execute(f"""
            SELECT
                Line,
                "Column",
                line_level1,
                line_level2,
                col_level1,
                col_level2,
                Value
            FROM {table_name}
            WHERE Provider_Number = ?
                AND fiscal_year = ?
            ORDER BY Line, "Column"
        """, [ccn, int(selected_year)]).df()

        con.close()

        if df.empty:
            return html.Div(
                f"No data available for {worksheet_name} in fiscal year {selected_year}",
                className="alert alert-warning"
            )

        # Roll-up logic: Keep only rows/columns ending in "00", sum the detail lines
        df['Line_Parent'] = df['Line'].str[:3] + '00'
        df['Column_Parent'] = df['Column'].str[:3] + '00'

        # Group by parent Line and Column, sum the values
        rollup_df = df.groupby(['Line_Parent', 'Column_Parent'], as_index=False).agg({
            'Value': 'sum',
            'line_level1': 'first',
            'line_level2': 'first',
            'col_level1': 'first',
            'col_level2': 'first'
        })

        # Rename back to Line and Column
        rollup_df = rollup_df.rename(columns={'Line_Parent': 'Line', 'Column_Parent': 'Column'})
        df = rollup_df

        # Convert to string and fill NaN values with empty strings for display
        df['line_level1'] = df['line_level1'].astype(str).replace('nan', '').replace('<NA>', '')
        df['line_level2'] = df['line_level2'].astype(str).replace('nan', '').replace('<NA>', '')
        df['col_level1'] = df['col_level1'].astype(str).replace('nan', '').replace('<NA>', '')
        df['col_level2'] = df['col_level2'].astype(str).replace('nan', '').replace('<NA>', '')

        # Filter out rows where ALL line and column levels are empty
        df = df[
            (df['line_level1'] != '') | (df['line_level2'] != '') |
            (df['col_level1'] != '') | (df['col_level2'] != '')
        ]

        # Create row labels (Line + descriptions)
        df['Row_Label'] = df.apply(
            lambda x: f"{x['Line']} | {x['line_level1']} {x['line_level2']}".strip(),
            axis=1
        )

        # Create column labels (Column + descriptions)
        df['Col_Label'] = df.apply(
            lambda x: f"{x['Column']} | {x['col_level1']} {x['col_level2']}".strip() if x['col_level1'] or x['col_level2'] else x['Column'],
            axis=1
        )

        # Get unique columns in order
        col_order = df[['Column', 'Col_Label']].drop_duplicates().sort_values('Column')

        # Pivot the data
        pivot_df = df.pivot_table(
            index=['Line', 'Row_Label'],
            columns='Col_Label',
            values='Value',
            aggfunc='first'
        ).reset_index()

        # Reorder columns based on original Column order
        ordered_cols = ['Line', 'Row_Label'] + [col for col in col_order['Col_Label'] if col in pivot_df.columns]
        pivot_df = pivot_df[ordered_cols]

        # Create DataTable columns
        columns = [
            {'name': 'Line', 'id': 'Line', 'type': 'text'},
            {'name': 'Description', 'id': 'Row_Label', 'type': 'text'}
        ]

        # Add value columns
        for col in pivot_df.columns:
            if col not in ['Line', 'Row_Label']:
                columns.append({
                    'name': col,
                    'id': col,
                    'type': 'numeric',
                    'format': {'specifier': ',.2f'}
                })

        # Create table with professional styling
        pro_style = get_professional_datatable_style()

        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table=pro_style['style_table'],
            style_cell=pro_style['style_cell'],
            style_cell_conditional=[
                {
                    'if': {'column_id': 'Line'},
                    'width': '90px',
                    'textAlign': 'center',
                    'fontWeight': '600',
                    'color': '#5a6c7d',
                    'backgroundColor': '#f0f3f5'
                },
                {
                    'if': {'column_id': 'Row_Label'},
                    'minWidth': '280px',
                    'maxWidth': '450px',
                    'fontWeight': '500',
                    'paddingLeft': '16px'
                },
                {
                    'if': {'column_type': 'numeric'},
                    'textAlign': 'right',
                    'minWidth': '130px',
                    'fontFamily': 'Monaco, Consolas, "Courier New", monospace',
                    'fontWeight': '500',
                    'paddingRight': '16px'
                }
            ],
            style_header=pro_style['style_header'],
            style_data=pro_style['style_data'],
            style_data_conditional=pro_style['style_data_conditional'],
            page_size=100,
            filter_action='native',
            sort_action='native',
            export_format='xlsx',
            export_headers='display'
        )

        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H5(f"{worksheet_name} - Fiscal Year {selected_year}", className="mb-3"),
                    html.P([
                        html.Strong("Total rows: "), f"{len(pivot_df):,} | ",
                        html.Strong("Total columns: "), f"{len(pivot_df.columns)-2:,}"
                    ], className="text-muted mb-3"),
                ])
            ]),
            dbc.Row([
                dbc.Col([
                    table
                ])
            ])
        ])

    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"Error loading worksheet: {str(e)}", className="alert alert-danger")


# ============================================================================
# VALUATION TAB CALLBACKS
# ============================================================================

@app.callback(
    Output('valuation-year-dropdown', 'options'),
    Input('hospital-dropdown', 'value')
)
def populate_valuation_years(ccn):
    """Populate year dropdown for valuation tab based on selected hospital"""
    if not ccn:
        return []

    con = data_manager.get_connection()
    try:
        query = """
        SELECT DISTINCT Fiscal_Year
        FROM income_statement_long
        WHERE Provider_Number = ?
        ORDER BY Fiscal_Year DESC
        """
        df = con.execute(query, [int(ccn)]).df()
        con.close()

        if df.empty:
            return []

        years = df['Fiscal_Year'].tolist()
        return [{'label': str(year), 'value': year} for year in years]
    except:
        con.close()
        return []


@app.callback(
    [Output('valuation-income-data', 'data'),
     Output('valuation-expense-data', 'data'),
     Output('valuation-baseline-metrics', 'data'),
     Output('valuation-content', 'children')],
    [Input('valuation-load-button', 'n_clicks')],
    [State('hospital-dropdown', 'value'),
     State('valuation-year-dropdown', 'value')]
)
def load_valuation_data(n_clicks, ccn, fiscal_year):
    """Load and display valuation data"""
    if n_clicks == 0 or not ccn or not fiscal_year:
        return None, None, None, html.Div([
            html.P("Please select a fiscal year and click 'Load Valuation Data'.",
                   className="text-center text-muted mt-4")
        ])

    # Load data
    income_df = load_valuation_income_statement(ccn, fiscal_year)
    expense_df = load_valuation_expense_detail(ccn, fiscal_year)

    if income_df.empty:
        return None, None, None, html.Div([
            html.P("No income statement data found for the selected hospital and year.",
                   className="text-center text-danger mt-4")
        ])

    # Calculate baseline metrics
    baseline = {}
    for _, row in income_df.iterrows():
        if row['Line_Name'] == 'Net_Patient_Revenue':
            baseline['net_revenue'] = row['Value']
        elif row['Line_Name'] == 'Operating_Income':
            baseline['operating_income'] = row['Value']
        elif row['Line_Name'] == 'Net_Income':
            baseline['net_income'] = row['Value']
        elif row['Line_Name'] == 'Total_Operating_Expenses':
            baseline['operating_expenses'] = row['Value']
        elif row['Line_Name'] == 'Total_Other_Income':
            baseline['other_income'] = row['Value']
        elif row['Line_Name'] == 'Total_Other_Expenses':
            baseline['other_expenses'] = row['Value']

    # Calculate baseline EBITDA (simplified - using Operating Income as proxy)
    baseline['ebitda'] = baseline.get('operating_income', 0)
    baseline['operating_margin'] = (baseline.get('operating_income', 0) /
                                     baseline.get('net_revenue', 1) * 100) if baseline.get('net_revenue', 0) != 0 else 0
    baseline['ebitda_margin'] = (baseline.get('ebitda', 0) /
                                  baseline.get('net_revenue', 1) * 100) if baseline.get('net_revenue', 0) != 0 else 0

    # Create dashboard layout
    valuation_layout = html.Div([
        # Row 1: Key Metrics Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Net Patient Revenue", className="text-muted mb-2"),
                        html.H4(f"${baseline.get('net_revenue', 0):,.0f}", className="text-primary mb-0")
                    ])
                ], className="shadow-sm")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Operating Income", className="text-muted mb-2"),
                        html.H4(f"${baseline.get('operating_income', 0):,.0f}", className="text-success mb-0"),
                        html.Small(f"{baseline['operating_margin']:.1f}% margin", className="text-muted")
                    ])
                ], className="shadow-sm")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("EBITDA (Est.)", className="text-muted mb-2"),
                        html.H4(f"${baseline.get('ebitda', 0):,.0f}", className="text-info mb-0"),
                        html.Small(f"{baseline['ebitda_margin']:.1f}% margin", className="text-muted")
                    ])
                ], className="shadow-sm")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Valuation (8x EBITDA)", className="text-muted mb-2"),
                        html.H4(f"${baseline.get('ebitda', 0) * 8:,.0f}", className="text-warning mb-0"),
                        html.Small("Estimated Value", className="text-muted")
                    ])
                ], className="shadow-sm")
            ], width=3)
        ], className="mb-4"),

        # Row 2: Sensitivity Analysis Controls
        dbc.Card([
            dbc.CardBody([
                html.H5("Valuation Sensitivity Analysis", className="mb-3"),
                html.P("Adjust the sliders below to see how changes affect valuation:", className="text-muted mb-4"),

                # Revenue Change
                html.Div([
                    html.Label("Revenue Change (%)", className="fw-bold"),
                    dcc.Slider(
                        id='revenue-slider',
                        min=-20, max=20, step=1, value=0,
                        marks={i: f"{i:+d}%" for i in range(-20, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], className="mb-4"),

                # Operating Margin Change
                html.Div([
                    html.Label("Operating Margin Change (percentage points)", className="fw-bold"),
                    dcc.Slider(
                        id='margin-slider',
                        min=-10, max=10, step=0.5, value=0,
                        marks={i: f"{i:+.0f}pp" for i in range(-10, 11, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], className="mb-4"),

                # Expense Change
                html.Div([
                    html.Label("Operating Expense Change (%)", className="fw-bold"),
                    dcc.Slider(
                        id='expense-slider',
                        min=-20, max=20, step=1, value=0,
                        marks={i: f"{i:+d}%" for i in range(-20, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], className="mb-4"),

                # Valuation Multiple
                html.Div([
                    html.Label("EBITDA Valuation Multiple", className="fw-bold"),
                    dcc.Slider(
                        id='multiple-slider',
                        min=4, max=14, step=0.5, value=8,
                        marks={i: f"{i}x" for i in range(4, 15, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], className="mb-3"),
            ])
        ], className="shadow-sm mb-4"),

        # Row 3: Adjusted Metrics Display
        html.Div(id='valuation-adjusted-metrics', className="mb-4"),

        # Row 4: Visualizations
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='valuation-waterfall'),
            ], width=6),
            dbc.Col([
                dcc.Graph(id='valuation-sensitivity'),
            ], width=6)
        ], className="mb-4"),

        # Row 5: Expense Breakdown
        dbc.Row([
            dbc.Col([
                dcc.Graph(id='valuation-expense-breakdown'),
            ], width=6),
            dbc.Col([
                dcc.Graph(id='valuation-expense-type'),
            ], width=6)
        ])
    ])

    return (income_df.to_dict('records'),
            expense_df.to_dict('records') if not expense_df.empty else [],
            baseline,
            valuation_layout)


@app.callback(
    [Output('valuation-adjusted-metrics', 'children'),
     Output('valuation-waterfall', 'figure'),
     Output('valuation-sensitivity', 'figure'),
     Output('valuation-expense-breakdown', 'figure'),
     Output('valuation-expense-type', 'figure')],
    [Input('revenue-slider', 'value'),
     Input('margin-slider', 'value'),
     Input('expense-slider', 'value'),
     Input('multiple-slider', 'value')],
    [State('valuation-baseline-metrics', 'data'),
     State('valuation-income-data', 'data'),
     State('valuation-expense-data', 'data')]
)
def update_valuation_analysis(revenue_change, margin_change, expense_change, multiple,
                                baseline, income_data, expense_data):
    """Update valuation analysis based on slider inputs"""
    if not baseline:
        return html.Div(), {}, {}, {}, {}

    # Calculate adjusted metrics
    base_revenue = baseline.get('net_revenue', 0)
    base_expenses = baseline.get('operating_expenses', 0)
    base_operating_income = baseline.get('operating_income', 0)

    # Apply changes
    adj_revenue = base_revenue * (1 + revenue_change / 100)
    adj_expenses = base_expenses * (1 + expense_change / 100)
    adj_operating_income = adj_revenue - adj_expenses

    # Apply margin change (as percentage point change)
    if margin_change != 0:
        target_margin = (base_operating_income / base_revenue * 100) + margin_change
        adj_operating_income = adj_revenue * (target_margin / 100)
        adj_expenses = adj_revenue - adj_operating_income

    adj_ebitda = adj_operating_income
    adj_valuation = adj_ebitda * multiple

    # Calculate changes
    revenue_change_amt = adj_revenue - base_revenue
    expense_change_amt = adj_expenses - base_expenses
    operating_income_change = adj_operating_income - base_operating_income
    ebitda_change = adj_ebitda - baseline.get('ebitda', 0)
    valuation_change = adj_valuation - (baseline.get('ebitda', 0) * 8)

    # Adjusted metrics table with professional styling
    adjusted_metrics_layout = dbc.Card([
        dbc.CardBody([
            html.H5("Adjusted Valuation Metrics",
                   style={'color': '#2c3e50', 'fontWeight': '600', 'marginBottom': '20px', 'fontSize': '1.3rem'}),
            html.Div([
                dbc.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Metric", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                            html.Th("Original", className="text-end", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                            html.Th("Adjusted", className="text-end", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                            html.Th("Change ($)", className="text-end", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                            html.Th("Change (%)", className="text-end", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'})
                        ])
                    ]),
                    html.Tbody([
                        # Revenue Row
                        html.Tr([
                            html.Td("Net Patient Revenue", style={'padding': '12px', 'fontWeight': '500', 'color': '#2c3e50'}),
                            html.Td(f"${base_revenue:,.0f}", className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(f"${adj_revenue:,.0f}", className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(f"${revenue_change_amt:+,.0f}", className="text-end",
                                   style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if revenue_change_amt >= 0 else '#e74c3c', 'fontWeight': '600'}),
                            html.Td(f"{revenue_change:+.1f}%", className="text-end",
                                   style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if revenue_change >= 0 else '#e74c3c', 'fontWeight': '600'})
                        ], style={'backgroundColor': 'white'}),
                        # Expenses Row
                        html.Tr([
                            html.Td("Operating Expenses", style={'padding': '12px', 'fontWeight': '500', 'color': '#2c3e50'}),
                            html.Td(f"${base_expenses:,.0f}", className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(f"${adj_expenses:,.0f}", className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(f"${expense_change_amt:+,.0f}", className="text-end",
                                   style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#e74c3c' if expense_change_amt >= 0 else '#27ae60', 'fontWeight': '600'}),
                            html.Td(f"{(expense_change_amt/base_expenses*100) if base_expenses != 0 else 0:+.1f}%", className="text-end",
                                   style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#e74c3c' if expense_change_amt >= 0 else '#27ae60', 'fontWeight': '600'})
                        ], style={'backgroundColor': '#f8f9fa'}),
                        # Operating Income Row (Highlighted)
                        html.Tr([
                            html.Td(html.Strong("Operating Income"), style={'padding': '12px', 'color': '#2c3e50', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"${base_operating_income:,.0f}"), className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(html.Strong(f"${adj_operating_income:,.0f}"), className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(html.Strong(f"${operating_income_change:+,.0f}"),
                                   className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if operating_income_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"{(operating_income_change/base_operating_income*100) if base_operating_income != 0 else 0:+.1f}%"),
                                   className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if operating_income_change >= 0 else '#e74c3c', 'fontWeight': '700'})
                        ], style={'backgroundColor': '#e8f4f8', 'borderTop': '2px solid #3498db', 'borderBottom': '2px solid #3498db'}),
                        # EBITDA Row (Highlighted)
                        html.Tr([
                            html.Td(html.Strong("EBITDA (Est.)"), style={'padding': '12px', 'color': '#2c3e50', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"${baseline.get('ebitda', 0):,.0f}"), className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(html.Strong(f"${adj_ebitda:,.0f}"), className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                            html.Td(html.Strong(f"${ebitda_change:+,.0f}"),
                                   className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if ebitda_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"{(ebitda_change/baseline.get('ebitda', 1)*100):+.1f}%"),
                                   className="text-end", style={'padding': '12px', 'fontFamily': 'monospace', 'fontSize': '0.95rem', 'color': '#27ae60' if ebitda_change >= 0 else '#e74c3c', 'fontWeight': '700'})
                        ], style={'backgroundColor': '#f8f9fa'}),
                        # Valuation Row (Most Important - Gold Highlight)
                        html.Tr([
                            html.Td(html.Strong(f"Enterprise Valuation ({multiple}x EBITDA)"), style={'padding': '14px', 'color': '#2c3e50', 'fontWeight': '700', 'fontSize': '1.05rem'}),
                            html.Td(html.Strong(f"${baseline.get('ebitda', 0) * 8:,.0f}"), className="text-end",
                                   style={'padding': '14px', 'fontFamily': 'monospace', 'fontSize': '1.05rem', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"${adj_valuation:,.0f}"), className="text-end",
                                   style={'padding': '14px', 'fontFamily': 'monospace', 'fontSize': '1.05rem', 'color': '#f39c12', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"${valuation_change:+,.0f}"),
                                   className="text-end", style={'padding': '14px', 'fontFamily': 'monospace', 'fontSize': '1.05rem', 'color': '#27ae60' if valuation_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                            html.Td(html.Strong(f"{(valuation_change/(baseline.get('ebitda', 1) * 8)*100):+.1f}%"),
                                   className="text-end", style={'padding': '14px', 'fontFamily': 'monospace', 'fontSize': '1.05rem', 'color': '#27ae60' if valuation_change >= 0 else '#e74c3c', 'fontWeight': '700'})
                        ], style={'backgroundColor': '#fff9e6', 'borderTop': '3px solid #f39c12', 'borderBottom': '3px solid #f39c12'})
                    ])
                ], className="mb-0",
                   style={'border': '1px solid #dee2e6', 'borderRadius': '8px', 'overflow': 'hidden', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'})
            ])
        ], style={'padding': '24px'})
    ], className="shadow-sm", style={'borderRadius': '10px', 'border': 'none'})

    # Create waterfall chart
    waterfall_fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["relative", "relative", "total"],
        x=["Net Revenue", "Operating Expenses", "Operating Income"],
        textposition="outside",
        text=[f"${adj_revenue:,.0f}", f"-${adj_expenses:,.0f}", f"${adj_operating_income:,.0f}"],
        y=[adj_revenue, -adj_expenses, None],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))

    waterfall_fig.update_layout(
        title="Adjusted Income Statement Flow",
        showlegend=False,
        height=400
    )

    # Create valuation sensitivity chart
    scenarios = ['Base Case', 'Current Scenario']
    valuations = [baseline.get('ebitda', 0) * 8, adj_valuation]
    colors = ['#3498db', '#27ae60' if valuation_change >= 0 else '#e74c3c']

    valuation_fig = go.Figure(data=[
        go.Bar(x=scenarios, y=valuations, marker_color=colors, text=valuations,
               texttemplate='$%{text:,.0f}', textposition='outside')
    ])

    valuation_fig.update_layout(
        title=f"Valuation Comparison (Change: ${valuation_change:+,.0f})",
        yaxis_title="Valuation ($)",
        height=400,
        showlegend=False
    )

    # Create expense breakdown charts
    expense_cat_fig = {}
    expense_type_fig = {}

    if expense_data:
        expense_df = pd.DataFrame(expense_data)

        # Expense by category
        expense_cat_fig = px.bar(
            expense_df.nlargest(10, 'Total_Expense'),
            x='Total_Expense',
            y='Expense_Category',
            orientation='h',
            title="Top 10 Expense Categories",
            labels={'Total_Expense': 'Total Expense ($)', 'Expense_Category': 'Category'},
            color='Total_Expense',
            color_continuous_scale='Reds'
        )
        expense_cat_fig.update_layout(height=400, showlegend=False)

        # Expense by type
        expense_type_summary = expense_df.groupby('Category_Type')['Total_Expense'].sum().reset_index()
        expense_type_fig = px.pie(
            expense_type_summary,
            values='Total_Expense',
            names='Category_Type',
            title="Expense Distribution by Type"
        )
        expense_type_fig.update_layout(height=400)

    return adjusted_metrics_layout, waterfall_fig, valuation_fig, expense_cat_fig, expense_type_fig


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("STARTING HOSPITAL KPI SCORECARD DASHBOARD")
    print("="*80)

    # Show correct data source
    if data_manager.use_precomputed:
        print(f"Data source: Optimized Database with Pre-Computed KPIs")
    elif data_manager.use_database:
        print(f"Data source: Database (raw tables only)")
    else:
        print(f"Data source: Parquet files (no database)")

    print(f"Available hospitals: {len(hospital_options)}")
    print(f"Landing Page: http://localhost:8050")
    print(f"Dashboard App: http://localhost:8050/app")
    print("="*80 + "\n")
    app.run(debug=True, port=8050)
