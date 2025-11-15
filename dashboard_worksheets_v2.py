"""
Hospital Analytics Dashboard - Worksheet-Based Version (Simplified)

This dashboard displays CMS HCRIS worksheet data from the DuckDB database.
Uses simpler callback structure for better compatibility.

Author: JQ-dev
Date: 2025-11-08
"""

import dash
from dash import dcc, html, Input, Output, State, callback, dash_table, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import duckdb
import pandas as pd
import numpy as np
from pathlib import Path

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

# Configuration
BASE_DIR = Path(__file__).parent
DATABASE_PATH = BASE_DIR / 'data' / 'hospital_worksheets.duckdb'

# Available worksheets
WORKSHEETS = [
    ('A000000', 'General Service Cost Centers'),
    ('A6000A0', 'Reclassifications'),
    ('A700001', 'Reconciliation of Capital Costs Centers'),
    ('A700002', 'Reconciliation of Capital Costs Centers'),
    ('A700003', 'Reconciliation of Capital Costs Centers'),
    ('A800000', 'Adjustments to Expenses'),
    ('A810000', 'Costs Incurred - Related Organizations'),
    ('A820010', 'Provider-Based Physicians Adjustments'),
    ('B000001', 'Cost Allocation - General Service Costs'),
    ('B000002', 'Cost Allocation - General Service Costs'),
    ('B100000', 'Cost Allocation - General Service Costs'),
    ('C000001', 'Cost Allocation - General Service Costs'),
    ('G000000', 'Balance Sheet'),
    ('G100000', 'Statement of Changes in Fund Balances'),
    ('G200000', 'Statement of Patient Revenues'),
    ('G300000', 'Statement of Revenues'),
    ('S000001', 'Settlement Summary'),
    ('S100001', 'Hospital Uncompensated & Indigent Care Data'),
    ('S200001', 'Hospital & Healthcare Complex ID Data'),
    ('S300001', 'Statistical Data'),
    ('S300002', 'Statistical Data'),
    ('S300004', 'Hospital Wage Related Costs'),
    ('S300005', 'Hospital Wage Related Costs'),
    ('S410000', 'Hospital Wage Related Costs'),
    ('S500000', 'Hospital Renal Dialysis Department'),
]

# Database connection
def get_db_connection():
    """Get read-only database connection"""
    return duckdb.connect(str(DATABASE_PATH), read_only=True)

# Get provider list
def get_provider_list():
    """Get list of all providers"""
    con = get_db_connection()
    providers = con.execute("""
        SELECT DISTINCT Provider_Number, state_code
        FROM provider_list
        ORDER BY state_code, Provider_Number
    """).df()
    con.close()

    return [
        {
            'label': f"{row['Provider_Number']} ({row['state_code']})",
            'value': row['Provider_Number']
        }
        for _, row in providers.iterrows()
    ]

# ==============================================================================
# LAYOUT
# ==============================================================================

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("Hospital Analytics Dashboard - Worksheets", className="text-primary mt-4 mb-2"),
            html.P("CMS HCRIS Worksheet Data Explorer", className="text-muted mb-4"),
        ])
    ]),

    # Hospital Selection
    dbc.Row([
        dbc.Col([
            html.Label("Select Hospital:", className="fw-bold"),
            dcc.Dropdown(
                id='hospital-dropdown',
                options=get_provider_list(),
                placeholder="Select a hospital",
                className="mb-3"
            )
        ], width=6),
        dbc.Col([
            html.Label("Select Fiscal Year:", className="fw-bold"),
            dcc.Dropdown(
                id='year-dropdown',
                options=[],
                placeholder="Select fiscal year",
                className="mb-3"
            )
        ], width=3)
    ]),

    # Hospital Info
    dbc.Row([
        dbc.Col([
            html.Div(id='hospital-info', className="mb-4")
        ])
    ]),

    # Main Content - Worksheet Tabs
    dbc.Row([
        dbc.Col([
            dbc.Tabs(id="worksheet-tabs", active_tab="tab-b000001", children=[
                dbc.Tab(
                    label=f"{code} - {name}",
                    tab_id=f"tab-{code.lower()}",
                )
                for code, name in WORKSHEETS
            ]),
            html.Div(id='worksheet-content', className="mt-4")
        ])
    ], className="mt-4"),

    # Footer
    html.Hr(className="my-5"),
    html.Footer([
        html.P("Data source: CMS HCRIS - hospital_worksheets.duckdb", className="text-center text-muted")
    ])

], fluid=True, className="py-4")


# ==============================================================================
# CALLBACKS
# ==============================================================================

@app.callback(
    [Output('hospital-info', 'children'),
     Output('year-dropdown', 'options')],
    Input('hospital-dropdown', 'value')
)
def update_hospital_info(provider_number):
    """Display hospital information and populate year dropdown"""
    if not provider_number:
        return html.Div("Please select a hospital", className="alert alert-info"), []

    con = get_db_connection()

    # Get hospital info
    info = con.execute("""
        SELECT
            Provider_Number,
            state_code,
            first_fiscal_year,
            last_fiscal_year,
            fiscal_year_count
        FROM provider_list
        WHERE Provider_Number = ?
    """, [provider_number]).df()

    # Get available years
    years = con.execute("""
        SELECT DISTINCT fiscal_year
        FROM all_worksheets
        WHERE Provider_Number = ?
        ORDER BY fiscal_year DESC
    """, [provider_number]).df()

    con.close()

    if info.empty:
        return html.Div("Hospital not found", className="alert alert-warning"), []

    row = info.iloc[0]

    info_card = dbc.Card([
        dbc.CardBody([
            html.H5(f"Provider: {row['Provider_Number']}", className="card-title"),
            html.P([
                html.Strong("State: "), f"{row['state_code']}", html.Br(),
                html.Strong("Fiscal Years: "), f"{row['first_fiscal_year']} - {row['last_fiscal_year']} ({row['fiscal_year_count']} years)"
            ])
        ])
    ])

    year_options = [{'label': str(year), 'value': year} for year in years['fiscal_year']]

    return info_card, year_options


@app.callback(
    Output('worksheet-content', 'children'),
    [Input('worksheet-tabs', 'active_tab'),
     Input('hospital-dropdown', 'value'),
     Input('year-dropdown', 'value')]
)
def update_worksheet_content(active_tab, provider_number, selected_year):
    """Update content based on selected worksheet tab"""

    if not provider_number:
        return html.Div("Please select a hospital", className="alert alert-info")

    if not selected_year:
        return html.Div("Please select a fiscal year", className="alert alert-info")

    # Extract worksheet code from tab ID
    worksheet_code = active_tab.replace('tab-', '').upper()

    # Find worksheet name
    worksheet_name = next((name for code, name in WORKSHEETS if code == worksheet_code), worksheet_code)

    con = get_db_connection()

    # Query worksheet data
    table_name = f'worksheet_{worksheet_code.lower()}'

    try:
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
        """, [provider_number, int(selected_year)]).df()
    except Exception as e:
        con.close()
        return html.Div(f"Error loading worksheet: {str(e)}", className="alert alert-danger")

    con.close()

    if df.empty:
        return html.Div(
            f"No data available for {worksheet_name} in fiscal year {selected_year}",
            className="alert alert-warning"
        )

    # Roll-up logic: Keep only rows/columns ending in "00", sum the detail lines
    # Add parent Line and Column for roll-up
    df['Line_Parent'] = df['Line'].str[:3] + '00'  # e.g., '00100' -> '00100', '00101' -> '00100'
    df['Column_Parent'] = df['Column'].str[:3] + '00'

    # Group by parent Line and Column, sum the values
    rollup_df = df.groupby(['Line_Parent', 'Column_Parent'], as_index=False).agg({
        'Value': 'sum',
        'line_level1': 'first',  # Take first description for the parent line
        'line_level2': 'first',
        'col_level1': 'first',
        'col_level2': 'first'
    })

    # Rename back to Line and Column
    rollup_df = rollup_df.rename(columns={'Line_Parent': 'Line', 'Column_Parent': 'Column'})

    # Use rolled-up data
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

    # Create table
    table = dash_table.DataTable(
        data=pivot_df.to_dict('records'),
        columns=columns,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'minWidth': '100px',
            'maxWidth': '300px',
            'whiteSpace': 'normal',
            'height': 'auto',
        },
        style_cell_conditional=[
            {
                'if': {'column_id': 'Line'},
                'width': '80px',
                'textAlign': 'center'
            },
            {
                'if': {'column_id': 'Row_Label'},
                'minWidth': '250px',
                'maxWidth': '400px',
            },
            {
                'if': {'column_type': 'numeric'},
                'textAlign': 'right',
                'minWidth': '120px'
            }
        ],
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'border': '1px solid #dee2e6',
            'textAlign': 'center'
        },
        style_data={
            'border': '1px solid #dee2e6'
        },
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


# ==============================================================================
# RUN APP
# ==============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("HOSPITAL ANALYTICS DASHBOARD - WORKSHEET VERSION")
    print("="*80)
    print(f"Database: {DATABASE_PATH}")
    print(f"Worksheets: {len(WORKSHEETS)}")
    print("Dashboard running at: http://localhost:8050")
    print("="*80 + "\n")

    app.run(debug=True, port=8050)
