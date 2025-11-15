"""
Simple test dashboard to verify Dash is working
"""
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import duckdb
from pathlib import Path

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

DATABASE_PATH = Path(__file__).parent / 'data' / 'hospital_worksheets.duckdb'

app.layout = dbc.Container([
    html.H1("Test Dashboard", className="mt-4"),
    html.P("If you can see this, Dash is working!"),

    dcc.Dropdown(
        id='test-dropdown',
        options=[
            {'label': 'Option 1', 'value': '1'},
            {'label': 'Option 2', 'value': '2'},
        ],
        placeholder="Select an option"
    ),

    html.Div(id='test-output', className="mt-4")
])

@app.callback(
    Output('test-output', 'children'),
    Input('test-dropdown', 'value')
)
def update_output(value):
    if not value:
        return "Select an option from the dropdown"

    # Test database
    con = duckdb.connect(str(DATABASE_PATH), read_only=True)
    count = con.execute("SELECT COUNT(*) FROM provider_list").fetchone()[0]
    con.close()

    return f"You selected: {value}. Database has {count} providers."

if __name__ == '__main__':
    print("Test dashboard starting on http://localhost:8052")
    app.run(debug=True, port=8052)
