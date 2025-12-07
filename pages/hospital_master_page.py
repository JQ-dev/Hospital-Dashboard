"""
Hospital Master Data Page
==========================

Comprehensive hospital directory with:
- Searchable table of all hospitals
- Filtering by state, type, status
- CCN, NPI, name, address, city, zip code
- Hospital group/system affiliation
- Historical changes tracking
- Export capabilities

This page provides the master hospital reference data that combines:
- HCRIS fiscal year data
- CMS Provider of Services (POS) information
- Historical identifier changes
"""

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Register this page
dash.register_page(__name__, path='/hospital-master', name='Hospital Directory')

# Database configuration
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'hospital_analytics.duckdb'


def get_hospital_master_data(filters=None):
    """
    Load hospital master data from database

    Args:
        filters: Dict of filter criteria
            - state_codes: List of state codes
            - hospital_types: List of hospital types
            - statuses: List of statuses
            - search_text: Search string for name/ccn/npi

    Returns:
        pandas DataFrame
    """
    if not DB_PATH.exists():
        return pd.DataFrame()

    con = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        # Check if hospital_master table exists
        tables = con.execute("SHOW TABLES").fetchall()
        table_names = [t[0] for t in tables]

        if 'hospital_master' not in table_names:
            return pd.DataFrame()

        # Build query with filters using parameterized queries to prevent SQL injection
        where_clauses = []
        params = []

        if filters:
            if filters.get('state_codes'):
                placeholders = ', '.join(['?' for _ in filters['state_codes']])
                where_clauses.append(f"state_code IN ({placeholders})")
                params.extend(filters['state_codes'])

            if filters.get('hospital_types'):
                placeholders = ', '.join(['?' for _ in filters['hospital_types']])
                where_clauses.append(f"hospital_type IN ({placeholders})")
                params.extend(filters['hospital_types'])

            if filters.get('statuses'):
                placeholders = ', '.join(['?' for _ in filters['statuses']])
                where_clauses.append(f"status IN ({placeholders})")
                params.extend(filters['statuses'])

            if filters.get('search_text'):
                search = filters['search_text'].lower()
                where_clauses.append("""
                    (LOWER(hospital_name) LIKE ?
                     OR LOWER(city) LIKE ?
                     OR ccn LIKE ?
                     OR npi LIKE ?)
                """)
                search_pattern = f'%{search}%'
                params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
            SELECT
                ccn,
                hospital_name,
                npi,
                street_address,
                city,
                state_code,
                zip_code,
                county_name,
                phone_number,
                hospital_type,
                ownership_type,
                hospital_system_name,
                status,
                total_beds,
                first_fiscal_year,
                last_fiscal_year,
                total_years_reported,
                certification_date,
                termination_date,
                data_quality_score,
                data_source
            FROM hospital_master
            {where_sql}
            ORDER BY state_code, city, hospital_name
        """

        df = con.execute(query, params).df()
        return df

    except Exception as e:
        logger.error(f"Error loading hospital master data: {e}")
        return pd.DataFrame()
    finally:
        con.close()


def get_filter_options():
    """Get unique values for filter dropdowns"""

    if not DB_PATH.exists():
        return {}, {}, {}

    con = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        # Check if table exists
        tables = con.execute("SHOW TABLES").fetchall()
        if 'hospital_master' not in [t[0] for t in tables]:
            return {}, {}, {}

        # Get unique states
        states = con.execute("""
            SELECT DISTINCT state_code, COUNT(*) as count
            FROM hospital_master
            WHERE state_code IS NOT NULL
            GROUP BY state_code
            ORDER BY state_code
        """).df()

        state_options = [
            {'label': f"{row['state_code']} ({row['count']:,} hospitals)", 'value': row['state_code']}
            for _, row in states.iterrows()
        ]

        # Get unique hospital types
        types = con.execute("""
            SELECT DISTINCT hospital_type, COUNT(*) as count
            FROM hospital_master
            WHERE hospital_type IS NOT NULL
            GROUP BY hospital_type
            ORDER BY count DESC
        """).df()

        type_options = [
            {'label': f"{row['hospital_type']} ({row['count']:,})", 'value': row['hospital_type']}
            for _, row in types.iterrows()
        ]

        # Get unique statuses
        statuses = con.execute("""
            SELECT DISTINCT status, COUNT(*) as count
            FROM hospital_master
            WHERE status IS NOT NULL
            GROUP BY status
            ORDER BY count DESC
        """).df()

        status_options = [
            {'label': f"{row['status']} ({row['count']:,})", 'value': row['status']}
            for _, row in statuses.iterrows()
        ]

        return state_options, type_options, status_options

    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        return [], [], []
    finally:
        con.close()


def get_summary_stats():
    """Get summary statistics for the dashboard"""

    if not DB_PATH.exists():
        return {}

    con = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        tables = con.execute("SHOW TABLES").fetchall()
        if 'hospital_master' not in [t[0] for t in tables]:
            return {}

        stats = con.execute("""
            SELECT
                COUNT(*) as total_hospitals,
                COUNT(DISTINCT state_code) as total_states,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_hospitals,
                SUM(CASE WHEN hospital_name IS NOT NULL THEN 1 ELSE 0 END) as hospitals_with_names,
                SUM(CASE WHEN street_address IS NOT NULL THEN 1 ELSE 0 END) as hospitals_with_addresses,
                SUM(CASE WHEN npi IS NOT NULL THEN 1 ELSE 0 END) as hospitals_with_npi,
                SUM(CASE WHEN hospital_system_name IS NOT NULL THEN 1 ELSE 0 END) as hospitals_in_systems,
                ROUND(AVG(data_quality_score), 1) as avg_quality_score,
                SUM(total_beds) as total_beds_all
            FROM hospital_master
        """).fetchone()

        return {
            'total_hospitals': stats[0] or 0,
            'total_states': stats[1] or 0,
            'active_hospitals': stats[2] or 0,
            'hospitals_with_names': stats[3] or 0,
            'hospitals_with_addresses': stats[4] or 0,
            'hospitals_with_npi': stats[5] or 0,
            'hospitals_in_systems': stats[6] or 0,
            'avg_quality_score': stats[7] or 0,
            'total_beds': stats[8] or 0
        }

    except Exception as e:
        logger.error(f"Error getting summary stats: {e}")
        return {}
    finally:
        con.close()


def create_summary_cards():
    """Create summary statistics cards"""

    stats = get_summary_stats()

    if not stats:
        return html.Div("Hospital master data not yet created. Run: python etl/build_hospital_master.py",
                       className="alert alert-warning")

    cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{stats['total_hospitals']:,}", className="text-primary"),
                    html.P("Total Hospitals", className="text-muted mb-0")
                ])
            ], className="text-center mb-3")
        ], width=6, lg=3),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{stats['active_hospitals']:,}", className="text-success"),
                    html.P("Active Hospitals", className="text-muted mb-0")
                ])
            ], className="text-center mb-3")
        ], width=6, lg=3),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{stats['total_states']}", className="text-info"),
                    html.P("States", className="text-muted mb-0")
                ])
            ], className="text-center mb-3")
        ], width=6, lg=3),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"{stats['avg_quality_score']}/100", className="text-warning"),
                    html.P("Avg Data Quality", className="text-muted mb-0")
                ])
            ], className="text-center mb-3")
        ], width=6, lg=3),
    ])

    return cards


def create_filters_panel():
    """Create filters panel"""

    state_options, type_options, status_options = get_filter_options()

    panel = dbc.Card([
        dbc.CardHeader(html.H5("Filters", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Search (Name, City, CCN, NPI)", className="fw-bold"),
                    dbc.Input(
                        id='hospital-search-input',
                        type='text',
                        placeholder='Enter search term...',
                        debounce=True
                    )
                ], width=12, lg=6, className="mb-3"),

                dbc.Col([
                    html.Label("State", className="fw-bold"),
                    dcc.Dropdown(
                        id='hospital-state-filter',
                        options=state_options,
                        multi=True,
                        placeholder='All states'
                    )
                ], width=12, lg=2, className="mb-3"),

                dbc.Col([
                    html.Label("Hospital Type", className="fw-bold"),
                    dcc.Dropdown(
                        id='hospital-type-filter',
                        options=type_options,
                        multi=True,
                        placeholder='All types'
                    )
                ], width=12, lg=2, className="mb-3"),

                dbc.Col([
                    html.Label("Status", className="fw-bold"),
                    dcc.Dropdown(
                        id='hospital-status-filter',
                        options=status_options,
                        multi=True,
                        placeholder='All statuses',
                        value=['Active']  # Default to Active only
                    )
                ], width=12, lg=2, className="mb-3"),
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Button("Clear Filters", id='clear-filters-btn', color="secondary", size="sm", className="me-2"),
                    dbc.Button("Export to CSV", id='export-hospitals-btn', color="primary", size="sm"),
                    dcc.Download(id="download-hospitals-csv")
                ], width=12)
            ])
        ])
    ], className="mb-4")

    return panel


# Layout
layout = dbc.Container([
    html.H2("Hospital Master Directory", className="mt-4 mb-4"),

    html.P([
        "Comprehensive hospital reference data combining CMS HCRIS and Provider of Services (POS) information. ",
        "Includes CCN codes, NPIs, names, addresses, and hospital groups with historical change tracking."
    ], className="lead mb-4"),

    # Summary cards
    html.Div(id='hospital-summary-cards', children=create_summary_cards()),

    # Filters
    html.Div(id='hospital-filters-panel', children=create_filters_panel()),

    # Results count
    html.Div(id='hospital-results-count', className="mb-3"),

    # Hospital data table
    html.Div(id='hospital-table-container', children=[
        html.Div("Loading hospital data...", className="text-center text-muted")
    ]),

    # Hospital detail modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id='hospital-detail-title')),
        dbc.ModalBody(id='hospital-detail-body'),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-hospital-detail", className="ms-auto")
        ),
    ], id="hospital-detail-modal", size="lg", is_open=False),

], fluid=True)


# Callbacks
@callback(
    [Output('hospital-table-container', 'children'),
     Output('hospital-results-count', 'children')],
    [Input('hospital-search-input', 'value'),
     Input('hospital-state-filter', 'value'),
     Input('hospital-type-filter', 'value'),
     Input('hospital-status-filter', 'value'),
     Input('clear-filters-btn', 'n_clicks')]
)
def update_hospital_table(search_text, states, types, statuses, clear_clicks):
    """Update hospital table based on filters"""

    # Handle clear filters
    if ctx.triggered_id == 'clear-filters-btn':
        search_text = None
        states = None
        types = None
        statuses = ['Active']

    # Build filters
    filters = {}
    if search_text:
        filters['search_text'] = search_text
    if states:
        filters['state_codes'] = states
    if types:
        filters['hospital_types'] = types
    if statuses:
        filters['statuses'] = statuses
    elif ctx.triggered_id != 'clear-filters-btn':
        # Default to Active if no status selected and not clearing
        filters['statuses'] = ['Active']

    # Load data
    df = get_hospital_master_data(filters)

    if df.empty:
        return (
            html.Div("No hospitals found matching criteria. Try adjusting filters.",
                    className="alert alert-info"),
            ""
        )

    # Create results count
    results_count = html.Div([
        html.Strong(f"{len(df):,} hospitals"),
        " found"
    ], className="text-muted")

    # Prepare display columns
    display_columns = [
        {'name': 'CCN', 'id': 'ccn'},
        {'name': 'Hospital Name', 'id': 'hospital_name'},
        {'name': 'NPI', 'id': 'npi'},
        {'name': 'City', 'id': 'city'},
        {'name': 'State', 'id': 'state_code'},
        {'name': 'Zip', 'id': 'zip_code'},
        {'name': 'Type', 'id': 'hospital_type'},
        {'name': 'Ownership', 'id': 'ownership_type'},
        {'name': 'System/Group', 'id': 'hospital_system_name'},
        {'name': 'Beds', 'id': 'total_beds'},
        {'name': 'Status', 'id': 'status'},
        {'name': 'Years', 'id': 'total_years_reported'},
    ]

    # Create DataTable
    table = dash_table.DataTable(
        id='hospital-master-table',
        columns=display_columns,
        data=df.to_dict('records'),
        filter_action='native',
        sort_action='native',
        page_action='native',
        page_size=50,
        page_current=0,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontSize': '14px',
            'fontFamily': 'sans-serif'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'border': '1px solid #dee2e6'
        },
        style_data={
            'border': '1px solid #dee2e6'
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{status} = "Active"'},
                'backgroundColor': '#e8f5e9'
            },
            {
                'if': {'filter_query': '{status} = "Likely Closed"'},
                'backgroundColor': '#ffebee',
                'color': '#888'
            },
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#fafafa'
            }
        ],
        style_cell_conditional=[
            {'if': {'column_id': 'ccn'}, 'width': '80px', 'fontFamily': 'monospace'},
            {'if': {'column_id': 'npi'}, 'width': '100px', 'fontFamily': 'monospace'},
            {'if': {'column_id': 'hospital_name'}, 'width': '250px', 'fontWeight': '500'},
            {'if': {'column_id': 'city'}, 'width': '150px'},
            {'if': {'column_id': 'state_code'}, 'width': '60px'},
            {'if': {'column_id': 'zip_code'}, 'width': '90px'},
            {'if': {'column_id': 'hospital_type'}, 'width': '120px'},
            {'if': {'column_id': 'total_beds'}, 'width': '70px', 'textAlign': 'right'},
            {'if': {'column_id': 'total_years_reported'}, 'width': '70px', 'textAlign': 'right'},
        ],
        row_selectable='single',
        selected_rows=[]
    )

    return table, results_count


@callback(
    Output("download-hospitals-csv", "data"),
    Input("export-hospitals-btn", "n_clicks"),
    [State('hospital-search-input', 'value'),
     State('hospital-state-filter', 'value'),
     State('hospital-type-filter', 'value'),
     State('hospital-status-filter', 'value')],
    prevent_initial_call=True
)
def export_hospitals(n_clicks, search_text, states, types, statuses):
    """Export filtered hospital data to CSV"""

    if not n_clicks:
        return None

    # Build filters
    filters = {}
    if search_text:
        filters['search_text'] = search_text
    if states:
        filters['state_codes'] = states
    if types:
        filters['hospital_types'] = types
    if statuses:
        filters['statuses'] = statuses

    # Load data
    df = get_hospital_master_data(filters)

    if df.empty:
        return None

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hospital_directory_{timestamp}.csv"

    return dcc.send_data_frame(df.to_csv, filename, index=False)


@callback(
    Output('hospital-state-filter', 'value'),
    Output('hospital-type-filter', 'value'),
    Output('hospital-status-filter', 'value'),
    Output('hospital-search-input', 'value'),
    Input('clear-filters-btn', 'n_clicks'),
    prevent_initial_call=True
)
def clear_filters(n_clicks):
    """Clear all filters"""
    return None, None, ['Active'], None
