"""
Simple Data Verification Tool
Shows which tables have data for a given CCN and year
"""

import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import duckdb
from pathlib import Path

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Simple Data Verification"
)

# Database paths
DB_PATH = Path('data/hospital_analytics.duckdb')
WORKSHEET_DB_PATH = Path('data/hospital_worksheets.duckdb')

def get_database_connection(db_path):
    """Get database connection"""
    try:
        if not db_path.exists():
            return None
        return duckdb.connect(str(db_path), read_only=True)
    except Exception as e:
        print(f"Error connecting to {db_path}: {e}")
        return None

def get_available_tables(con):
    """Get list of tables in database"""
    if con is None:
        return []
    try:
        result = con.execute("SHOW TABLES").df()
        return result['name'].tolist()
    except:
        return []

def check_data_for_ccn_year(con, ccn, year):
    """Check which tables have data for given CCN and year"""
    if con is None:
        return []

    tables = get_available_tables(con)
    results = []

    for table in tables:
        try:
            # Check if table has required columns
            schema = con.execute(f"DESCRIBE {table}").df()
            has_provider = 'Provider_Number' in schema['column_name'].values
            has_fiscal = 'Fiscal_Year' in schema['column_name'].values or 'fiscal_year' in schema['column_name'].values

            if not has_provider or not has_fiscal:
                continue

            # Determine fiscal year column
            fiscal_col = 'Fiscal_Year' if 'Fiscal_Year' in schema['column_name'].values else 'fiscal_year'

            # Count records
            count_result = con.execute(f"""
                SELECT COUNT(*) as cnt
                FROM {table}
                WHERE CAST(Provider_Number AS VARCHAR) = ?
                  AND {fiscal_col} = ?
            """, [str(ccn), int(year)]).fetchone()

            count = count_result[0] if count_result else 0

            if count > 0:
                results.append({'table': table, 'count': count})

        except Exception as e:
            continue

    return results

# Layout
app.layout = dbc.Container([
    html.H1("Simple Data Verification", className="my-4"),

    dbc.Row([
        dbc.Col([
            dbc.Label("Database:"),
            dbc.RadioItems(
                id='db-selector',
                options=[
                    {'label': 'Main Analytics DB', 'value': 'main'},
                    {'label': 'Worksheet DB', 'value': 'worksheet'}
                ],
                value='worksheet',
                inline=True
            )
        ], width=12, className="mb-3")
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Label("Hospital CCN:"),
            dcc.Input(
                id='ccn-input',
                type='text',
                placeholder='Enter CCN (e.g., 341325)',
                className='form-control'
            )
        ], width=4),

        dbc.Col([
            dbc.Label("Fiscal Year:"),
            dcc.Dropdown(
                id='year-selector',
                options=[
                    {'label': '2020', 'value': 2020},
                    {'label': '2021', 'value': 2021},
                    {'label': '2022', 'value': 2022},
                    {'label': '2023', 'value': 2023},
                    {'label': '2024', 'value': 2024}
                ],
                value=2024,
                clearable=False
            )
        ], width=4),

        dbc.Col([
            html.Br(),
            dbc.Button("Check Data", id='check-button', color='primary', className='mt-2')
        ], width=4)
    ]),

    html.Hr(),

    html.Div(id='output', className='mt-4')

], fluid=True, style={'maxWidth': '1200px', 'padding': '20px'})

@app.callback(
    Output('output', 'children'),
    [Input('check-button', 'n_clicks')],
    [Input('db-selector', 'value'),
     Input('ccn-input', 'value'),
     Input('year-selector', 'value')]
)
def check_data(n_clicks, db_type, ccn, year):
    """Check data availability"""
    if not ccn:
        return html.P("Enter a CCN and click 'Check Data'", className='text-muted')

    # Get database connection
    db_path = DB_PATH if db_type == 'main' else WORKSHEET_DB_PATH
    con = get_database_connection(db_path)

    if con is None:
        return html.Div([
            html.H4("Error", className='text-danger'),
            html.P(f"Could not connect to {db_path}")
        ])

    # Get database name
    db_name = "Main Analytics Database" if db_type == 'main' else "Worksheet Database"

    # Check data
    results = check_data_for_ccn_year(con, ccn, year)
    con.close()

    # Format output
    if not results:
        return html.Div([
            html.H4(f"Results for CCN {ccn}, Year {year}", className='text-primary'),
            html.P(f"Database: {db_name}"),
            html.Hr(),
            html.P("No data found for this CCN/Year combination", className='text-warning')
        ])

    # Create text output
    output_text = []
    output_text.append(f"=== CCN {ccn} - {db_name} - Year {year} ===\n\n")
    output_text.append(f"Tables with data ({len(results)} found):\n\n")

    total_records = 0
    for r in results:
        output_text.append(f"  • {r['table']}: {r['count']} records\n")
        total_records += r['count']

    output_text.append(f"\nTotal records across all tables: {total_records}")

    return html.Div([
        html.H4(f"Results for CCN {ccn}, Year {year}", className='text-primary'),
        html.P(f"Database: {db_name}"),
        html.Hr(),
        html.Pre(''.join(output_text), style={
            'backgroundColor': '#f8f9fa',
            'padding': '20px',
            'borderRadius': '5px',
            'fontFamily': 'monospace',
            'fontSize': '14px'
        })
    ])

if __name__ == '__main__':
    print("=" * 80)
    print("Simple Data Verification Tool")
    print("=" * 80)
    print("Starting server on http://localhost:8052")
    print("=" * 80)

    app.run(debug=True, port=8052, host='0.0.0.0')
