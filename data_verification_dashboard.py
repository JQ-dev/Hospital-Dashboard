"""
Data Verification Dashboard
Independent dashboard to verify data availability across hospitals, tables, and years
Runs on port 8051 (separate from main dashboard on 8050)
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import duckdb
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    title="Data Verification Dashboard"
)

# Database paths
DB_PATH = Path("data/hospital_analytics.duckdb")
WORKSHEET_DB_PATH = Path("data/hospital_worksheets.duckdb")

# Color scheme for availability
COLORS = {
    'full': '#28a745',      # Green - full data
    'partial': '#ffc107',   # Yellow - partial data
    'minimal': '#fd7e14',   # Orange - minimal data
    'none': '#dc3545',      # Red - no data
    'not_checked': '#e9ecef'  # Gray - not checked yet
}

def get_database_connection(db_path):
    """Get read-only connection to database"""
    if Path(db_path).exists():
        return duckdb.connect(str(db_path), read_only=True)
    return None

def get_available_tables(con):
    """Get list of all tables in database"""
    if con is None:
        return []
    try:
        tables_df = con.execute("SHOW TABLES").df()
        return sorted(tables_df['name'].tolist())
    except duckdb.Error as e:
        logger.error(f"Database error getting tables: {e}")
        return []
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return []

def get_hospitals_list(con):
    """Get list of all hospitals with metadata"""
    if con is None:
        return pd.DataFrame()

    try:
        # Try to get from hospital_kpis table first
        hospitals = con.execute("""
            SELECT DISTINCT
                Provider_Number,
                MIN(Fiscal_Year) as First_Year,
                MAX(Fiscal_Year) as Last_Year,
                COUNT(DISTINCT Fiscal_Year) as Year_Count
            FROM hospital_kpis
            GROUP BY Provider_Number
            ORDER BY Provider_Number
        """).df()
        return hospitals
    except duckdb.Error as e:
        logger.debug(f"hospital_kpis table not available: {e}")
        try:
            # Fallback to balance_sheet if available
            hospitals = con.execute("""
                SELECT DISTINCT
                    Provider_Number,
                    MIN(Fiscal_Year) as First_Year,
                    MAX(Fiscal_Year) as Last_Year,
                    COUNT(DISTINCT Fiscal_Year) as Year_Count
                FROM balance_sheet
                GROUP BY Provider_Number
                ORDER BY Provider_Number
            """).df()
            return hospitals
        except duckdb.Error as e:
            logger.debug(f"balance_sheet table not available: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading hospitals from balance_sheet: {e}")
            return pd.DataFrame()

def check_table_data_for_hospital(con, table_name, provider_number):
    """Check if table has data for a specific hospital"""
    if con is None:
        return {'status': 'none', 'record_count': 0, 'years': []}

    try:
        # Check if table has Provider_Number column
        schema = con.execute(f"DESCRIBE {table_name}").df()
        has_provider_col = 'Provider_Number' in schema['column_name'].values
        has_fiscal_year = 'Fiscal_Year' in schema['column_name'].values or 'fiscal_year' in schema['column_name'].values

        if not has_provider_col:
            return {'status': 'not_applicable', 'record_count': 0, 'years': []}

        # Format provider number - ensure it's a string and handle different formats
        provider_str = str(provider_number).strip()

        # Get record count for this hospital
        if has_fiscal_year:
            result = con.execute(f"""
                SELECT
                    COUNT(*) as cnt,
                    COALESCE(MIN(Fiscal_Year), MIN(fiscal_year)) as min_year,
                    COALESCE(MAX(Fiscal_Year), MAX(fiscal_year)) as max_year,
                    COUNT(DISTINCT COALESCE(Fiscal_Year, fiscal_year)) as year_count
                FROM {table_name}
                WHERE CAST(Provider_Number AS VARCHAR) = ?
            """, [provider_str]).fetchone()

            record_count = result[0] if result else 0
            min_year = result[1] if result and result[1] else None
            max_year = result[2] if result and result[2] else None
            year_count = result[3] if result else 0

            years = list(range(int(min_year), int(max_year) + 1)) if min_year and max_year else []
        else:
            result = con.execute(f"""
                SELECT COUNT(*) as cnt
                FROM {table_name}
                WHERE CAST(Provider_Number AS VARCHAR) = ?
            """, [provider_str]).fetchone()
            record_count = result[0] if result else 0
            years = []
            year_count = 0

        # Determine status based on record count
        if record_count == 0:
            status = 'none'
        elif record_count < 10:
            status = 'minimal'
        elif record_count < 100:
            status = 'partial'
        else:
            status = 'full'

        return {
            'status': status,
            'record_count': record_count,
            'years': years,
            'year_count': year_count
        }
    except Exception as e:
        logger.error(f"Error checking {table_name} for {provider_number}: {e}", exc_info=True)
        return {'status': 'error', 'record_count': 0, 'years': [], 'year_count': 0}

def check_table_data_by_year(con, table_name):
    """Get data availability by year for a specific table"""
    if con is None:
        return pd.DataFrame()

    try:
        # Check if table has Fiscal_Year column
        schema = con.execute(f"DESCRIBE {table_name}").df()
        has_provider_col = 'Provider_Number' in schema['column_name'].values
        has_fiscal_year = 'Fiscal_Year' in schema['column_name'].values or 'fiscal_year' in schema['column_name'].values

        if not has_provider_col or not has_fiscal_year:
            return pd.DataFrame()

        # Determine which fiscal year column to use
        fiscal_year_col = 'Fiscal_Year' if 'Fiscal_Year' in schema['column_name'].values else 'fiscal_year'

        # Get counts by provider and year
        result = con.execute(f"""
            SELECT
                Provider_Number,
                {fiscal_year_col} as Year,
                COUNT(*) as Record_Count
            FROM {table_name}
            GROUP BY Provider_Number, {fiscal_year_col}
            ORDER BY Provider_Number, {fiscal_year_col}
        """).df()

        return result
    except Exception as e:
        logger.error(f"Error checking {table_name} by year: {e}")
        return pd.DataFrame()

def check_all_tables_for_hospital(con, tables_list, provider_number):
    """Get data availability across all tables for a specific hospital by year"""
    if con is None or not tables_list:
        return pd.DataFrame()

    provider_str = str(provider_number).strip()
    all_data = []

    logger.debug(f"Checking {len(tables_list)} tables for hospital {provider_number}")
    tables_checked = 0
    tables_with_data = 0
    tables_skipped = 0

    for table_name in tables_list:
        try:
            # Check if table has required columns
            schema = con.execute(f"DESCRIBE {table_name}").df()
            has_provider_col = 'Provider_Number' in schema['column_name'].values
            has_fiscal_year = 'Fiscal_Year' in schema['column_name'].values or 'fiscal_year' in schema['column_name'].values

            if not has_provider_col or not has_fiscal_year:
                tables_skipped += 1
                logger.debug(f"[SKIP] {table_name} - Missing required columns (Provider_Number: {has_provider_col}, Fiscal_Year: {has_fiscal_year})")
                continue

            tables_checked += 1

            # Determine which fiscal year column to use
            fiscal_year_col = 'Fiscal_Year' if 'Fiscal_Year' in schema['column_name'].values else 'fiscal_year'

            # Get counts by year for this hospital
            result = con.execute(f"""
                SELECT
                    {fiscal_year_col} as Year,
                    COUNT(*) as Record_Count
                FROM {table_name}
                WHERE CAST(Provider_Number AS VARCHAR) = ?
                GROUP BY {fiscal_year_col}
                ORDER BY {fiscal_year_col}
            """, [provider_str]).df()

            if not result.empty:
                result['Table'] = table_name
                all_data.append(result)
                tables_with_data += 1
                logger.debug(f"[OK] {table_name} - Found {len(result)} years with data")
            else:
                logger.debug(f"[EMPTY] {table_name} - No data for this hospital")

        except Exception as e:
            logger.warning(f"[ERROR] {table_name}: {e}")
            continue

    logger.debug(f"[SUMMARY] Checked: {tables_checked}, With Data: {tables_with_data}, Skipped: {tables_skipped}")

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        logger.debug(f"[RESULT] Combined DataFrame has {len(combined_df)} rows across {len(all_data)} tables")
        return combined_df
    else:
        logger.debug(f"[RESULT] No data found for hospital {provider_number}")
        return pd.DataFrame()

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-database me-3"),
                "Data Verification Dashboard"
            ], className="text-primary mb-2"),
            html.P("Verify data availability across hospitals, tables, and years",
                   className="text-muted mb-4")
        ])
    ]),

    # Database Status
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5([
                    html.I(className="fas fa-server me-2"),
                    "Database Status"
                ])),
                dbc.CardBody([
                    html.Div(id='db-status')
                ])
            ], className="mb-4")
        ])
    ]),

    # Tabs for different views
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Hospital × Table Matrix", tab_id="hospital-table",
                       label_style={"cursor": "pointer"}),
                dbc.Tab(label="Table × Year Matrix", tab_id="table-year",
                       label_style={"cursor": "pointer"}),
                dbc.Tab(label="Summary Statistics", tab_id="summary",
                       label_style={"cursor": "pointer"})
            ], id="tabs", active_tab="hospital-table")
        ])
    ]),

    html.Br(),

    # Tab content
    html.Div(id='tab-content'),

    # Store components
    dcc.Store(id='hospitals-data'),
    dcc.Store(id='tables-data'),
    dcc.Interval(id='load-trigger', interval=1000, n_intervals=0, max_intervals=1)

], fluid=True, style={'padding': '20px'})

@app.callback(
    Output('db-status', 'children'),
    Input('load-trigger', 'n_intervals')
)
def update_db_status(n):
    """Display database connection status"""
    main_db_exists = DB_PATH.exists()
    worksheet_db_exists = WORKSHEET_DB_PATH.exists()

    cards = []

    # Main database
    if main_db_exists:
        con = get_database_connection(DB_PATH)
        tables = get_available_tables(con)
        con.close() if con else None

        cards.append(dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4([
                        html.I(className="fas fa-check-circle text-success me-2"),
                        "Main Analytics DB"
                    ]),
                    html.P(f"Path: {DB_PATH}", className="mb-1 small text-muted"),
                    html.P(f"Tables: {len(tables)}", className="mb-0")
                ])
            ], color="light")
        ], width=6))
    else:
        cards.append(dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4([
                        html.I(className="fas fa-times-circle text-danger me-2"),
                        "Main Analytics DB"
                    ]),
                    html.P(f"Not found at: {DB_PATH}", className="mb-0 small text-danger")
                ])
            ], color="light")
        ], width=6))

    # Worksheet database
    if worksheet_db_exists:
        con = get_database_connection(WORKSHEET_DB_PATH)
        tables = get_available_tables(con)
        con.close() if con else None

        cards.append(dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4([
                        html.I(className="fas fa-check-circle text-success me-2"),
                        "Worksheet DB"
                    ]),
                    html.P(f"Path: {WORKSHEET_DB_PATH}", className="mb-1 small text-muted"),
                    html.P(f"Tables: {len(tables)}", className="mb-0")
                ])
            ], color="light")
        ], width=6))
    else:
        cards.append(dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4([
                        html.I(className="fas fa-times-circle text-danger me-2"),
                        "Worksheet DB"
                    ]),
                    html.P(f"Not found at: {WORKSHEET_DB_PATH}", className="mb-0 small text-danger")
                ])
            ], color="light")
        ], width=6))

    return dbc.Row(cards)

@app.callback(
    [Output('hospitals-data', 'data'),
     Output('tables-data', 'data')],
    Input('load-trigger', 'n_intervals')
)
def load_initial_data(n):
    """Load hospitals and tables data"""
    hospitals_list = []
    tables_dict = {'main': [], 'worksheet': []}

    # Load from main database
    if DB_PATH.exists():
        con = get_database_connection(DB_PATH)
        hospitals_df = get_hospitals_list(con)
        if not hospitals_df.empty:
            hospitals_list = hospitals_df.to_dict('records')
        tables_dict['main'] = get_available_tables(con)
        con.close() if con else None

    # Load from worksheet database
    if WORKSHEET_DB_PATH.exists():
        con = get_database_connection(WORKSHEET_DB_PATH)
        tables_dict['worksheet'] = get_available_tables(con)
        con.close() if con else None

    return hospitals_list, tables_dict

@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'),
     Input('hospitals-data', 'data'),
     Input('tables-data', 'data')]
)
def render_tab_content(active_tab, hospitals_data, tables_data):
    """Render content based on active tab"""
    if not hospitals_data or not tables_data:
        return dbc.Alert("Loading data...", color="info")

    if active_tab == "hospital-table":
        return render_hospital_table_matrix(hospitals_data, tables_data)
    elif active_tab == "table-year":
        return render_table_year_matrix(hospitals_data, tables_data)
    elif active_tab == "summary":
        return render_summary_stats(hospitals_data, tables_data)

    return html.Div("Select a tab")

def render_hospital_table_matrix(hospitals_data, tables_data):
    """Render hospital × table matrix view"""
    if not hospitals_data:
        return dbc.Alert("No hospital data available", color="warning")

    # Limit to first 50 hospitals for performance
    hospitals_subset = hospitals_data[:50]

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Hospital × Table Data Availability Matrix"),
                html.P(f"Showing first {len(hospitals_subset)} of {len(hospitals_data)} hospitals",
                       className="text-muted"),
            ])
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            dbc.Label("Select Database:"),
                            dbc.RadioItems(
                                id='db-selector-ht',
                                options=[
                                    {'label': 'Main Analytics DB', 'value': 'main'},
                                    {'label': 'Worksheet DB', 'value': 'worksheet'}
                                ],
                                value='main',
                                inline=True,
                                className="mt-2"
                            )
                        ]),
                        html.Div([
                            dbc.Label("Select Table:", className="mt-3"),
                            dcc.Dropdown(
                                id='table-selector-ht',
                                options=[],
                                value=None,
                                placeholder="Select a table..."
                            )
                        ])
                    ]),
                    dbc.CardBody([
                        dcc.Loading([
                            html.Div(id='hospital-table-matrix')
                        ])
                    ])
                ])
            ])
        ])
    ], fluid=True)

def render_table_year_matrix(hospitals_data, tables_data):
    """Render table × year matrix view"""
    # Create hospital options for dropdown
    hospital_options = [{'label': f"CCN {h['Provider_Number']}", 'value': h['Provider_Number']}
                        for h in hospitals_data[:100]] if hospitals_data else []

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Table × Year Data Availability Matrix"),
                html.P("View all tables and their record counts by year for a selected hospital",
                       className="text-muted"),
            ])
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            dbc.Label("Select Database:"),
                            dbc.RadioItems(
                                id='db-selector-ty',
                                options=[
                                    {'label': 'Main Analytics DB', 'value': 'main'},
                                    {'label': 'Worksheet DB', 'value': 'worksheet'}
                                ],
                                value='main',
                                inline=True,
                                className="mt-2"
                            )
                        ]),
                        html.Div([
                            dbc.Label("Select Hospital CCN:", className="mt-3"),
                            dcc.Dropdown(
                                id='hospital-selector-ty',
                                options=hospital_options,
                                value=hospital_options[0]['value'] if hospital_options else None,
                                placeholder="Select a hospital...",
                                clearable=False
                            )
                        ])
                    ]),
                    dbc.CardBody([
                        dcc.Loading([
                            html.Div(id='table-year-matrix')
                        ])
                    ])
                ])
            ])
        ])
    ], fluid=True)

def render_summary_stats(hospitals_data, tables_data):
    """Render summary statistics"""
    total_hospitals = len(hospitals_data)
    main_tables = len(tables_data.get('main', []))
    worksheet_tables = len(tables_data.get('worksheet', []))

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("Summary Statistics"),
            ])
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2(f"{total_hospitals:,}", className="text-primary"),
                        html.P("Total Hospitals", className="mb-0")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2(f"{main_tables}", className="text-success"),
                        html.P("Main DB Tables", className="mb-0")
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H2(f"{worksheet_tables}", className="text-info"),
                        html.P("Worksheet Tables", className="mb-0")
                    ])
                ])
            ], width=4)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Available Tables")),
                    dbc.CardBody([
                        html.H6("Main Analytics Database:", className="mt-2"),
                        html.Ul([html.Li(t) for t in tables_data.get('main', [])[:20]]),
                        html.P(f"... and {len(tables_data.get('main', [])) - 20} more"
                               if len(tables_data.get('main', [])) > 20 else "",
                               className="text-muted"),

                        html.H6("Worksheet Database:", className="mt-4"),
                        html.Ul([html.Li(t) for t in tables_data.get('worksheet', [])[:20]]),
                        html.P(f"... and {len(tables_data.get('worksheet', [])) - 20} more"
                               if len(tables_data.get('worksheet', [])) > 20 else "",
                               className="text-muted")
                    ])
                ])
            ])
        ])
    ], fluid=True)

# Update dropdowns based on database selection
@app.callback(
    Output('table-selector-ht', 'options'),
    [Input('db-selector-ht', 'value'),
     Input('tables-data', 'data')]
)
def update_table_dropdown_ht(db_type, tables_data):
    """Update table dropdown for hospital-table view"""
    if not tables_data:
        return []

    tables = tables_data.get(db_type, [])
    return [{'label': t, 'value': t} for t in tables]

@app.callback(
    Output('table-selector-ty', 'options'),
    [Input('db-selector-ty', 'value'),
     Input('tables-data', 'data')]
)
def update_table_dropdown_ty(db_type, tables_data):
    """Update table dropdown for table-year view"""
    if not tables_data:
        return []

    tables = tables_data.get(db_type, [])
    return [{'label': t, 'value': t} for t in tables]

# Render hospital-table matrix
@app.callback(
    Output('hospital-table-matrix', 'children'),
    [Input('table-selector-ht', 'value'),
     Input('db-selector-ht', 'value'),
     Input('hospitals-data', 'data')]
)
def update_hospital_table_matrix(table_name, db_type, hospitals_data):
    """Generate hospital × table matrix with years as columns"""
    if not table_name or not hospitals_data:
        return dbc.Alert("Select a table to view data availability", color="info")

    # Get database connection
    db_path = DB_PATH if db_type == 'main' else WORKSHEET_DB_PATH
    con = get_database_connection(db_path)

    if con is None:
        return dbc.Alert("Database not available", color="danger")

    # Get year-based data for this table
    year_data = check_table_data_by_year(con, table_name)
    con.close()

    if year_data.empty:
        return dbc.Alert("No year-based data available for this table", color="warning")

    # Limit to first 50 hospitals
    hospitals_subset = [h['Provider_Number'] for h in hospitals_data[:50]]
    year_data = year_data[year_data['Provider_Number'].isin(hospitals_subset)]

    # Pivot data: CCN as rows, years as columns
    pivot_df = year_data.pivot(index='Provider_Number', columns='Year', values='Record_Count')
    pivot_df = pivot_df.fillna(0).astype(int)

    # Reset index to make CCN a column
    pivot_df = pivot_df.reset_index()
    pivot_df = pivot_df.rename(columns={'Provider_Number': 'CCN'})

    # Sort columns: CCN first, then years in order
    year_cols = [col for col in pivot_df.columns if col != 'CCN']
    year_cols_sorted = sorted(year_cols)
    df = pivot_df[['CCN'] + year_cols_sorted]

    # Create simple table with years as columns
    # Build column definitions
    columns = [{'name': 'CCN', 'id': 'CCN'}] + \
              [{'name': str(year), 'id': year} for year in year_cols_sorted]

    # Build style conditions for color coding based on record counts
    style_conditions = []
    for year_col in year_cols_sorted:
        # Full (100+)
        style_conditions.append({
            'if': {
                'filter_query': f'{{{year_col}}} >= 100',
                'column_id': year_col
            },
            'backgroundColor': COLORS['full'],
            'color': 'white'
        })
        # Partial (10-99)
        style_conditions.append({
            'if': {
                'filter_query': f'{{{year_col}}} >= 10 && {{{year_col}}} < 100',
                'column_id': year_col
            },
            'backgroundColor': COLORS['partial'],
            'color': 'black'
        })
        # Minimal (1-9)
        style_conditions.append({
            'if': {
                'filter_query': f'{{{year_col}}} > 0 && {{{year_col}}} < 10',
                'column_id': year_col
            },
            'backgroundColor': COLORS['minimal'],
            'color': 'white'
        })
        # None (0)
        style_conditions.append({
            'if': {
                'filter_query': f'{{{year_col}}} = 0',
                'column_id': year_col
            },
            'backgroundColor': COLORS['none'],
            'color': 'white'
        })

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span("Legend: ", className="fw-bold me-3"),
                    html.Span("Full (100+ records)", className="badge me-2",
                             style={'backgroundColor': COLORS['full']}),
                    html.Span("Partial (10-99 records)", className="badge me-2",
                             style={'backgroundColor': COLORS['partial']}),
                    html.Span("Minimal (1-9 records)", className="badge me-2",
                             style={'backgroundColor': COLORS['minimal']}),
                    html.Span("None (0 records)", className="badge me-2",
                             style={'backgroundColor': COLORS['none']})
                ], className="mb-3")
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=columns,
                    style_data_conditional=style_conditions,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'center',
                        'padding': '10px',
                        'minWidth': '60px'
                    },
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'CCN'},
                            'textAlign': 'left',
                            'fontWeight': 'bold'
                        }
                    ],
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold',
                        'textAlign': 'center'
                    },
                    page_size=50,
                    sort_action='native',
                    filter_action='native'
                )
            ])
        ])
    ])

# Render table-year matrix
@app.callback(
    Output('table-year-matrix', 'children'),
    [Input('hospital-selector-ty', 'value'),
     Input('db-selector-ty', 'value'),
     Input('hospitals-data', 'data'),
     Input('tables-data', 'data')]
)
def update_table_year_matrix(selected_hospital, db_type, hospitals_data, tables_data):
    """Generate table × year matrix showing all tables for selected hospital"""
    if not hospitals_data or not tables_data or not selected_hospital:
        return dbc.Alert("Select a hospital to view data availability", color="info")

    # Get database connection
    db_path = DB_PATH if db_type == 'main' else WORKSHEET_DB_PATH
    con = get_database_connection(db_path)

    if con is None:
        return dbc.Alert("Database not available", color="danger")

    # Get list of tables for selected database
    available_tables = tables_data.get(db_type, [])

    # Get all tables data for the selected hospital
    all_tables_data = check_all_tables_for_hospital(con, available_tables, selected_hospital)
    con.close()

    if all_tables_data.empty:
        return dbc.Alert([
            html.H5(f"No year-based data found for CCN {selected_hospital}", className="alert-heading"),
            html.P([
                "This could mean:",
                html.Ul([
                    html.Li("The hospital has no data in any tables with both Provider_Number and Fiscal_Year columns"),
                    html.Li("The CCN may not exist in this database"),
                    html.Li("The tables may not have temporal (year-based) data"),
                ])
            ]),
            html.Hr(),
            html.P([
                "Check the console/terminal output for detailed debugging information about which tables were checked.",
            ], className="mb-0 small")
        ], color="warning")

    # Pivot data: rows=tables, columns=years
    pivot_df = all_tables_data.pivot(index='Table', columns='Year', values='Record_Count')
    pivot_df = pivot_df.fillna(0).astype(int)

    # Sort columns (years) in order
    pivot_df = pivot_df.sort_index(axis=1)

    # Reset index to make Table a column
    pivot_df = pivot_df.reset_index()

    # Get year columns
    year_cols = [col for col in pivot_df.columns if col != 'Table']
    year_cols_sorted = sorted(year_cols)

    # Reorder columns: Table first, then years
    df = pivot_df[['Table'] + year_cols_sorted]

    # Create simple table with years as columns
    # Build column definitions
    columns = [{'name': 'Table', 'id': 'Table'}] + \
              [{'name': str(year), 'id': year} for year in year_cols_sorted]

    # Build style conditions for color coding based on record counts
    style_conditions = []
    for year_col in year_cols_sorted:
        # Full (100+)
        style_conditions.append({
            'if': {
                'filter_query': f'{{{year_col}}} >= 100',
                'column_id': year_col
            },
            'backgroundColor': COLORS['full'],
            'color': 'white'
        })
        # Partial (10-99)
        style_conditions.append({
            'if': {
                'filter_query': f'{{{year_col}}} >= 10 && {{{year_col}}} < 100',
                'column_id': year_col
            },
            'backgroundColor': COLORS['partial'],
            'color': 'black'
        })
        # Minimal (1-9)
        style_conditions.append({
            'if': {
                'filter_query': f'{{{year_col}}} > 0 && {{{year_col}}} < 10',
                'column_id': year_col
            },
            'backgroundColor': COLORS['minimal'],
            'color': 'white'
        })
        # None (0)
        style_conditions.append({
            'if': {
                'filter_query': f'{{{year_col}}} = 0',
                'column_id': year_col
            },
            'backgroundColor': COLORS['none'],
            'color': 'white'
        })

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span("Legend: ", className="fw-bold me-3"),
                    html.Span("Full (100+ records)", className="badge me-2",
                             style={'backgroundColor': COLORS['full']}),
                    html.Span("Partial (10-99 records)", className="badge me-2",
                             style={'backgroundColor': COLORS['partial']}),
                    html.Span("Minimal (1-9 records)", className="badge me-2",
                             style={'backgroundColor': COLORS['minimal']}),
                    html.Span("None (0 records)", className="badge me-2",
                             style={'backgroundColor': COLORS['none']})
                ], className="mb-3")
            ])
        ]),
        dbc.Row([
            dbc.Col([
                dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=columns,
                    style_data_conditional=style_conditions,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'center',
                        'padding': '10px',
                        'minWidth': '60px'
                    },
                    style_cell_conditional=[
                        {
                            'if': {'column_id': 'Table'},
                            'textAlign': 'left',
                            'fontWeight': 'bold',
                            'minWidth': '150px'
                        }
                    ],
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold',
                        'textAlign': 'center'
                    },
                    page_size=50,
                    sort_action='native',
                    filter_action='native'
                )
            ])
        ])
    ])

if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("Data Verification Dashboard")
    logger.info("=" * 80)
    logger.info(f"Main Database: {DB_PATH}")
    logger.info(f"Worksheet Database: {WORKSHEET_DB_PATH}")
    logger.info(f"Starting server on http://localhost:8051")
    logger.info("=" * 80)

    app.run(debug=True, port=8051, host='0.0.0.0')
