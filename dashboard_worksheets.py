"""
Hospital Analytics Dashboard - Worksheet-Based Version

This dashboard displays CMS HCRIS worksheet data from the DuckDB database.
All worksheets shown with year-by-year columns, Line levels as rows, Column levels as columns.

Author: JQ-dev
Date: 2025-11-08
"""

import dash
from dash import dcc, html, Input, Output, State, callback, ALL, dash_table
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
    ('A700001', 'Statistical Data 1'),
    ('A700002', 'Statistical Data 2'),
    ('A700003', 'Statistical Data 3'),
    ('A800000', 'Inpatient Routine Cost Centers'),
    ('A810000', 'Ancillary Service Cost Centers'),
    ('A820010', 'Outpatient Service Cost Centers'),
    ('B000001', 'Balance Sheet'),
    ('B000002', 'Statement of Revenues and Expenses'),
    ('B100000', 'Cost Allocation - Stepdown'),
    ('C000001', 'Allocation Statistics'),
    ('S000001', 'Part A Settlement'),
    ('S100001', 'Part A Provider Statistical/Reimbursement'),
    ('S200001', 'Part A Bad Debts'),
    ('S300001', 'Part B Settlement'),
    ('S300002', 'Part B Statistical/Reimbursement'),
    ('S300004', 'Part B Bad Debts'),
    ('S300005', 'Part B ASC Cost and Payment'),
    ('S410000', 'Home Health Agency (HHA)'),
    ('S500000', 'Hospice'),
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
        ], width=6)
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
            dbc.Tabs(id="worksheet-tabs", children=[
                dbc.Tab(
                    label=f"{code} - {name}",
                    tab_id=f"tab-{code.lower()}",
                    children=[
                        html.Div([
                            # Year selection
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold mt-3"),
                                    dcc.Dropdown(
                                        id={'type': 'year-dropdown', 'worksheet': code},
                                        options=[],  # Populated by callback
                                        placeholder="Select fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            # Worksheet content
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id={'type': 'worksheet-content', 'worksheet': code})
                                ])
                            ])
                        ])
                    ]
                )
                for code, name in WORKSHEETS
            ])
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
    Output('hospital-info', 'children'),
    Input('hospital-dropdown', 'value')
)
def update_hospital_info(provider_number):
    """Display hospital information"""
    if not provider_number:
        return html.Div("Please select a hospital", className="alert alert-info")

    con = get_db_connection()
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
    con.close()

    if info.empty:
        return html.Div("Hospital not found", className="alert alert-warning")

    row = info.iloc[0]

    return dbc.Card([
        dbc.CardBody([
            html.H5(f"Provider: {row['Provider_Number']}", className="card-title"),
            html.P([
                html.Strong("State: "), f"{row['state_code']}", html.Br(),
                html.Strong("Fiscal Years: "), f"{row['first_fiscal_year']} - {row['last_fiscal_year']} ({row['fiscal_year_count']} years)"
            ])
        ])
    ])


@app.callback(
    Output({'type': 'year-dropdown', 'worksheet': ALL}, 'options'),
    Input('hospital-dropdown', 'value')
)
def populate_year_dropdowns(provider_number):
    """Populate year dropdowns for all worksheets"""
    if not provider_number:
        return [[] for _ in WORKSHEETS]

    con = get_db_connection()

    # Get available years across all worksheets for this provider
    years = con.execute("""
        SELECT DISTINCT fiscal_year
        FROM all_worksheets
        WHERE Provider_Number = ?
        ORDER BY fiscal_year DESC
    """, [provider_number]).df()

    con.close()

    if years.empty:
        return [[] for _ in WORKSHEETS]

    year_options = [{'label': str(year), 'value': year} for year in years['fiscal_year']]

    # Return same options for all worksheets
    return [year_options for _ in WORKSHEETS]


@app.callback(
    Output({'type': 'worksheet-content', 'worksheet': ALL}, 'children'),
    [Input({'type': 'year-dropdown', 'worksheet': ALL}, 'value'),
     Input('hospital-dropdown', 'value')]
)
def update_worksheet_content(selected_years, provider_number):
    """Update content for all worksheet tabs"""

    if not provider_number:
        return [html.Div("Please select a hospital", className="alert alert-info") for _ in WORKSHEETS]

    outputs = []

    con = get_db_connection()

    for i, (worksheet_code, worksheet_name) in enumerate(WORKSHEETS):
        selected_year = selected_years[i] if i < len(selected_years) else None

        if not selected_year:
            outputs.append(html.Div("Please select a fiscal year", className="alert alert-info"))
            continue

        # Query worksheet data
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
            ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
        """, [provider_number, int(selected_year)]).df()

        if df.empty:
            outputs.append(html.Div(
                f"No data available for {worksheet_name} in fiscal year {selected_year}",
                className="alert alert-warning"
            ))
            continue

        # Create pivot table display
        # Rows: Line + line_level1 + line_level2
        # Columns: Column + col_level1 + col_level2

        # Create row labels
        df['Row_Label'] = df.apply(
            lambda x: f"{x['Line']} - {x['line_level1'] or ''} {x['line_level2'] or ''}".strip(),
            axis=1
        )

        # Create column labels
        df['Col_Label'] = df.apply(
            lambda x: f"{x['Column']} - {x['col_level1'] or ''} {x['col_level2'] or ''}".strip(),
            axis=1
        )

        # Pivot the data
        pivot_df = df.pivot_table(
            index=['Line', 'Row_Label'],
            columns=['Column', 'Col_Label'],
            values='Value',
            aggfunc='first'
        ).reset_index()

        # Format the table
        pivot_df.columns = [' '.join(map(str, col)).strip() if isinstance(col, tuple) else col for col in pivot_df.columns]

        # Create DataTable
        columns = [
            {'name': 'Line', 'id': 'Line'},
            {'name': 'Description', 'id': 'Row_Label'}
        ]

        # Add value columns
        for col in pivot_df.columns:
            if col not in ['Line', 'Row_Label']:
                columns.append({
                    'name': col,
                    'id': col,
                    'type': 'numeric',
                    'format': {'specifier': ',.0f'}
                })

        table = dash_table.DataTable(
            data=pivot_df.to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'minWidth': '150px'
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
                    'if': {'column_type': 'numeric'},
                    'textAlign': 'right'
                }
            ],
            page_size=50,
            filter_action='native',
            sort_action='native'
        )

        outputs.append(html.Div([
            html.H5(f"{worksheet_name} - Fiscal Year {selected_year}", className="mb-3"),
            html.P(f"Total rows: {len(pivot_df)}", className="text-muted"),
            table
        ]))

    con.close()

    return outputs


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
