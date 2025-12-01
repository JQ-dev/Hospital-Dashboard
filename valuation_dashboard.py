"""
Interactive Hospital Valuation Dashboard
Shows how changes in revenue, expenses, and margins affect hospital valuation
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import duckdb
from pathlib import Path
import numpy as np

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Hospital Valuation Dashboard"

# Database path
DB_PATH = Path(__file__).parent / "data" / "hospital_analytics.duckdb"

# Connect to DuckDB
def get_db_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)

# Load data function
def load_hospital_list():
    """Load list of hospitals for dropdown"""
    conn = get_db_connection()
    try:
        query = """
        SELECT DISTINCT
            Provider_Number,
            MAX(Fiscal_Year) as latest_year
        FROM income_statement_long
        GROUP BY Provider_Number
        ORDER BY Provider_Number
        LIMIT 500
        """
        df = conn.execute(query).df()
        conn.close()
        return df
    except Exception as e:
        print(f"Error loading hospital list: {e}")
        conn.close()
        return pd.DataFrame({'Provider_Number': [], 'latest_year': []})

def load_income_statement(provider_number, fiscal_year):
    """Load income statement data for a provider"""
    conn = get_db_connection()
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
        df = conn.execute(query, [provider_number, int(fiscal_year)]).df()
        conn.close()
        return df
    except Exception as e:
        print(f"Error loading income statement: {e}")
        conn.close()
        return pd.DataFrame()

def load_expense_detail(provider_number, fiscal_year):
    """Load detailed expense breakdown"""
    conn = get_db_connection()
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
        df = conn.execute(query, [provider_number, int(fiscal_year)]).df()
        conn.close()
        return df
    except Exception as e:
        print(f"Error loading expense detail: {e}")
        conn.close()
        return pd.DataFrame()

# App layout
app.layout = html.Div([
    html.Div([
        html.H1("Interactive Hospital Valuation Dashboard",
                style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 10}),
        html.P("Analyze how changes in revenue, expenses, and margins affect hospital valuation",
               style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': 16}),
    ], style={'backgroundColor': '#ecf0f1', 'padding': '20px', 'marginBottom': '20px'}),

    # Hospital selector
    html.Div([
        html.Div([
            html.Label("Select Hospital:", style={'fontWeight': 'bold', 'fontSize': 14}),
            dcc.Dropdown(
                id='hospital-dropdown',
                options=[],
                value=None,
                placeholder="Select a hospital...",
                style={'width': '400px'}
            ),
        ], style={'display': 'inline-block', 'marginRight': '30px'}),

        html.Div([
            html.Label("Fiscal Year:", style={'fontWeight': 'bold', 'fontSize': 14}),
            dcc.Dropdown(
                id='year-dropdown',
                options=[],
                value=None,
                placeholder="Select year...",
                style={'width': '200px'}
            ),
        ], style={'display': 'inline-block', 'marginRight': '30px'}),

        html.Button('Load Data', id='load-button', n_clicks=0,
                    style={'marginTop': '24px', 'padding': '10px 20px',
                           'backgroundColor': '#3498db', 'color': 'white',
                           'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'}),
    ], style={'padding': '20px', 'backgroundColor': 'white', 'marginBottom': '20px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),

    # Store components for data
    dcc.Store(id='income-statement-data'),
    dcc.Store(id='expense-detail-data'),
    dcc.Store(id='baseline-metrics'),

    # Main content area
    html.Div(id='dashboard-content', style={'padding': '20px'}),
], style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh', 'fontFamily': 'Arial, sans-serif'})


# Callback to populate hospital dropdown
@app.callback(
    Output('hospital-dropdown', 'options'),
    Input('hospital-dropdown', 'id')
)
def populate_hospitals(_):
    hospitals = load_hospital_list()
    if hospitals.empty:
        return []
    return [{'label': f"Provider {row['Provider_Number']}", 'value': row['Provider_Number']}
            for _, row in hospitals.iterrows()]


# Callback to populate year dropdown based on selected hospital
@app.callback(
    Output('year-dropdown', 'options'),
    Output('year-dropdown', 'value'),
    Input('hospital-dropdown', 'value')
)
def populate_years(provider_number):
    if not provider_number:
        return [], None

    conn = get_db_connection()
    try:
        query = """
        SELECT DISTINCT Fiscal_Year
        FROM income_statement_long
        WHERE Provider_Number = ?
        ORDER BY Fiscal_Year DESC
        """
        df = conn.execute(query, [provider_number]).df()
        conn.close()

        if df.empty:
            return [], None

        years = df['Fiscal_Year'].tolist()
        return [{'label': str(year), 'value': year} for year in years], years[0]
    except Exception as e:
        print(f"Error loading years for provider {provider_number}: {e}")
        conn.close()
        return [], None


# Main callback to load data and render dashboard
@app.callback(
    [Output('income-statement-data', 'data'),
     Output('expense-detail-data', 'data'),
     Output('baseline-metrics', 'data'),
     Output('dashboard-content', 'children')],
    [Input('load-button', 'n_clicks')],
    [State('hospital-dropdown', 'value'),
     State('year-dropdown', 'value')]
)
def load_and_render_dashboard(n_clicks, provider_number, fiscal_year):
    if n_clicks == 0 or not provider_number or not fiscal_year:
        return None, None, None, html.Div([
            html.P("Please select a hospital and fiscal year, then click 'Load Data'.",
                   style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': 18, 'marginTop': '50px'})
        ])

    # Load data
    income_df = load_income_statement(provider_number, fiscal_year)
    expense_df = load_expense_detail(provider_number, fiscal_year)

    if income_df.empty:
        return None, None, None, html.Div([
            html.P("No data found for the selected hospital and year.",
                   style={'textAlign': 'center', 'color': '#e74c3c', 'fontSize': 18, 'marginTop': '50px'})
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

    # Calculate baseline EBITDA (simplified - would need depreciation/interest from other worksheets)
    # For now, use Operating Income as proxy
    baseline['ebitda'] = baseline.get('operating_income', 0)
    baseline['operating_margin'] = (baseline.get('operating_income', 0) /
                                     baseline.get('net_revenue', 1) * 100) if baseline.get('net_revenue', 0) != 0 else 0
    baseline['ebitda_margin'] = (baseline.get('ebitda', 0) /
                                  baseline.get('net_revenue', 1) * 100) if baseline.get('net_revenue', 0) != 0 else 0

    # Create dashboard layout
    dashboard_layout = html.Div([
        # Row 1: Key Metrics Cards
        html.Div([
            html.Div([
                html.H4("Net Patient Revenue", style={'color': '#7f8c8d', 'fontSize': 14}),
                html.H2(f"${baseline.get('net_revenue', 0):,.0f}", style={'color': '#2c3e50', 'marginTop': 5}),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center', 'width': '23%',
                      'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.H4("Operating Income", style={'color': '#7f8c8d', 'fontSize': 14}),
                html.H2(f"${baseline.get('operating_income', 0):,.0f}", style={'color': '#27ae60', 'marginTop': 5}),
                html.P(f"{baseline['operating_margin']:.1f}% margin", style={'color': '#7f8c8d', 'fontSize': 12}),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center', 'width': '23%',
                      'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.H4("EBITDA (Est.)", style={'color': '#7f8c8d', 'fontSize': 14}),
                html.H2(f"${baseline.get('ebitda', 0):,.0f}", style={'color': '#3498db', 'marginTop': 5}),
                html.P(f"{baseline['ebitda_margin']:.1f}% margin", style={'color': '#7f8c8d', 'fontSize': 12}),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center', 'width': '23%',
                      'display': 'inline-block', 'marginRight': '2%'}),

            html.Div([
                html.H4("Valuation (8x EBITDA)", style={'color': '#7f8c8d', 'fontSize': 14}),
                html.H2(f"${baseline.get('ebitda', 0) * 8:,.0f}",
                        style={'color': '#e67e22', 'marginTop': 5}),
                html.P("Estimated Value", style={'color': '#7f8c8d', 'fontSize': 12}),
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center', 'width': '23%',
                      'display': 'inline-block'}),
        ], style={'marginBottom': '30px'}),

        # Row 2: Sensitivity Analysis Controls
        html.Div([
            html.H3("Valuation Sensitivity Analysis", style={'color': '#2c3e50', 'marginBottom': 20}),
            html.P("Adjust the sliders below to see how changes affect valuation:",
                   style={'color': '#7f8c8d', 'marginBottom': 20}),

            html.Div([
                # Revenue Change
                html.Div([
                    html.Label("Revenue Change (%)", style={'fontWeight': 'bold'}),
                    dcc.Slider(
                        id='revenue-slider',
                        min=-20, max=20, step=1, value=0,
                        marks={i: f"{i:+d}%" for i in range(-20, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], style={'marginBottom': '30px'}),

                # Operating Margin Change
                html.Div([
                    html.Label("Operating Margin Change (percentage points)", style={'fontWeight': 'bold'}),
                    dcc.Slider(
                        id='margin-slider',
                        min=-10, max=10, step=0.5, value=0,
                        marks={i: f"{i:+.0f}pp" for i in range(-10, 11, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], style={'marginBottom': '30px'}),

                # Expense Change
                html.Div([
                    html.Label("Operating Expense Change (%)", style={'fontWeight': 'bold'}),
                    dcc.Slider(
                        id='expense-slider',
                        min=-20, max=20, step=1, value=0,
                        marks={i: f"{i:+d}%" for i in range(-20, 21, 5)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], style={'marginBottom': '30px'}),

                # Valuation Multiple
                html.Div([
                    html.Label("EBITDA Valuation Multiple", style={'fontWeight': 'bold'}),
                    dcc.Slider(
                        id='multiple-slider',
                        min=4, max=14, step=0.5, value=8,
                        marks={i: f"{i}x" for i in range(4, 15, 2)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                ], style={'marginBottom': '20px'}),
            ], style={'backgroundColor': 'white', 'padding': '30px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
        ], style={'marginBottom': '30px'}),

        # Row 3: Adjusted Metrics Display
        html.Div(id='adjusted-metrics', style={'marginBottom': '30px'}),

        # Row 4: Visualizations
        html.Div([
            # Income Statement Waterfall
            html.Div([
                dcc.Graph(id='income-waterfall'),
            ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '4%'}),

            # Valuation Sensitivity Chart
            html.Div([
                dcc.Graph(id='valuation-sensitivity'),
            ], style={'width': '48%', 'display': 'inline-block'}),
        ], style={'marginBottom': '30px'}),

        # Row 5: Expense Breakdown
        html.Div([
            html.Div([
                html.H3("Expense Breakdown by Category", style={'color': '#2c3e50', 'marginBottom': 20}),
                dcc.Graph(id='expense-breakdown'),
            ], style={'backgroundColor': 'white', 'padding': '30px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'width': '48%',
                      'display': 'inline-block', 'marginRight': '4%'}),

            html.Div([
                html.H3("Expense by Type", style={'color': '#2c3e50', 'marginBottom': 20}),
                dcc.Graph(id='expense-type-breakdown'),
            ], style={'backgroundColor': 'white', 'padding': '30px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'width': '48%',
                      'display': 'inline-block'}),
        ]),
    ])

    return (income_df.to_dict('records'),
            expense_df.to_dict('records'),
            baseline,
            dashboard_layout)


# Callback for sensitivity analysis calculations and visualizations
@app.callback(
    [Output('adjusted-metrics', 'children'),
     Output('income-waterfall', 'figure'),
     Output('valuation-sensitivity', 'figure'),
     Output('expense-breakdown', 'figure'),
     Output('expense-type-breakdown', 'figure')],
    [Input('revenue-slider', 'value'),
     Input('margin-slider', 'value'),
     Input('expense-slider', 'value'),
     Input('multiple-slider', 'value')],
    [State('baseline-metrics', 'data'),
     State('income-statement-data', 'data'),
     State('expense-detail-data', 'data')]
)
def update_sensitivity_analysis(revenue_change, margin_change, expense_change, multiple,
                                 baseline, income_data, expense_data):
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
        # Adjust operating income to achieve target margin
        target_margin = (base_operating_income / base_revenue * 100) + margin_change
        adj_operating_income = adj_revenue * (target_margin / 100)
        adj_expenses = adj_revenue - adj_operating_income

    adj_ebitda = adj_operating_income  # Simplified
    adj_valuation = adj_ebitda * multiple

    # Calculate changes
    revenue_change_amt = adj_revenue - base_revenue
    expense_change_amt = adj_expenses - base_expenses
    operating_income_change = adj_operating_income - base_operating_income
    ebitda_change = adj_ebitda - baseline.get('ebitda', 0)
    valuation_change = adj_valuation - (baseline.get('ebitda', 0) * 8)

    # Adjusted metrics display with professional styling
    adjusted_metrics_layout = html.Div([
        html.H3("Adjusted Valuation Metrics",
               style={'color': '#2c3e50', 'fontWeight': '600', 'marginBottom': '20px', 'fontSize': '1.3rem'}),
        html.Div([
            # Original vs Adjusted comparison
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Metric", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                        html.Th("Original", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'textAlign': 'right', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                        html.Th("Adjusted", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'textAlign': 'right', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                        html.Th("Change ($)", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'textAlign': 'right', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                        html.Th("Change (%)", style={'backgroundColor': '#34495e', 'color': 'white', 'padding': '14px', 'textAlign': 'right', 'fontWeight': '600', 'fontSize': '0.95rem'}),
                    ])
                ]),
                html.Tbody([
                    # Revenue Row
                    html.Tr([
                        html.Td("Net Patient Revenue", style={'padding': '12px', 'fontWeight': '500', 'color': '#2c3e50'}),
                        html.Td(f"${base_revenue:,.0f}", style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                        html.Td(f"${adj_revenue:,.0f}", style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                        html.Td(f"${revenue_change_amt:+,.0f}",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem',
                                       'color': '#27ae60' if revenue_change_amt >= 0 else '#e74c3c', 'fontWeight': '600'}),
                        html.Td(f"{revenue_change:+.1f}%",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem',
                                       'color': '#27ae60' if revenue_change >= 0 else '#e74c3c', 'fontWeight': '600'}),
                    ], style={'backgroundColor': 'white'}),
                    # Expenses Row
                    html.Tr([
                        html.Td("Operating Expenses", style={'padding': '12px', 'fontWeight': '500', 'color': '#2c3e50'}),
                        html.Td(f"${base_expenses:,.0f}", style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                        html.Td(f"${adj_expenses:,.0f}", style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                        html.Td(f"${expense_change_amt:+,.0f}",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem',
                                       'color': '#e74c3c' if expense_change_amt >= 0 else '#27ae60', 'fontWeight': '600'}),
                        html.Td(f"{(expense_change_amt/base_expenses*100) if base_expenses != 0 else 0:+.1f}%",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem',
                                       'color': '#e74c3c' if expense_change_amt >= 0 else '#27ae60', 'fontWeight': '600'}),
                    ], style={'backgroundColor': '#f8f9fa'}),
                    # Operating Income Row (Highlighted)
                    html.Tr([
                        html.Td("Operating Income", style={'padding': '12px', 'color': '#2c3e50', 'fontWeight': '700'}),
                        html.Td(f"${base_operating_income:,.0f}",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                        html.Td(f"${adj_operating_income:,.0f}",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                        html.Td(f"${operating_income_change:+,.0f}",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem',
                                       'color': '#27ae60' if operating_income_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                        html.Td(f"{(operating_income_change/base_operating_income*100) if base_operating_income != 0 else 0:+.1f}%",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem',
                                       'color': '#27ae60' if operating_income_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                    ], style={'backgroundColor': '#e8f4f8', 'borderTop': '2px solid #3498db', 'borderBottom': '2px solid #3498db'}),
                    # EBITDA Row (Highlighted)
                    html.Tr([
                        html.Td("EBITDA (Est.)", style={'padding': '12px', 'color': '#2c3e50', 'fontWeight': '700'}),
                        html.Td(f"${baseline.get('ebitda', 0):,.0f}",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                        html.Td(f"${adj_ebitda:,.0f}",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem'}),
                        html.Td(f"${ebitda_change:+,.0f}",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem',
                                       'color': '#27ae60' if ebitda_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                        html.Td(f"{(ebitda_change/baseline.get('ebitda', 1)*100):+.1f}%",
                                style={'padding': '12px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '0.95rem',
                                       'color': '#27ae60' if ebitda_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                    ], style={'backgroundColor': '#f8f9fa'}),
                    # Valuation Row (Most Important - Gold Highlight)
                    html.Tr([
                        html.Td(f"Enterprise Valuation ({multiple}x EBITDA)", style={'padding': '14px', 'color': '#2c3e50', 'fontWeight': '700', 'fontSize': '1.05rem'}),
                        html.Td(f"${baseline.get('ebitda', 0) * 8:,.0f}",
                                style={'padding': '14px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '1.05rem', 'fontWeight': '700'}),
                        html.Td(f"${adj_valuation:,.0f}",
                                style={'padding': '14px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '1.05rem',
                                       'color': '#f39c12', 'fontWeight': '700'}),
                        html.Td(f"${valuation_change:+,.0f}",
                                style={'padding': '14px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '1.05rem',
                                       'color': '#27ae60' if valuation_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                        html.Td(f"{(valuation_change/(baseline.get('ebitda', 1) * 8)*100):+.1f}%",
                                style={'padding': '14px', 'textAlign': 'right', 'fontFamily': 'monospace', 'fontSize': '1.05rem',
                                       'color': '#27ae60' if valuation_change >= 0 else '#e74c3c', 'fontWeight': '700'}),
                    ], style={'backgroundColor': '#fff9e6', 'borderTop': '3px solid #f39c12', 'borderBottom': '3px solid #f39c12'}),
                ]),
            ], style={'width': '100%', 'borderCollapse': 'collapse', 'boxShadow': '0 2px 8px rgba(0,0,0,0.08)',
                     'border': '1px solid #dee2e6', 'borderRadius': '8px', 'overflow': 'hidden'}),
        ]),
    ], style={'backgroundColor': 'white', 'padding': '30px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})

    # Create waterfall chart for income statement
    waterfall_fig = go.Figure(go.Waterfall(
        name="Income Statement",
        orientation="v",
        measure=["relative", "relative", "total", "relative", "total"],
        x=["Net Revenue", "Operating Expenses", "Operating Income", "Other Income (Net)", "Net Income"],
        textposition="outside",
        text=[f"${adj_revenue:,.0f}", f"-${adj_expenses:,.0f}", f"${adj_operating_income:,.0f}",
              f"${baseline.get('other_income', 0) - baseline.get('other_expenses', 0):+,.0f}",
              f"${adj_operating_income + baseline.get('other_income', 0) - baseline.get('other_expenses', 0):,.0f}"],
        y=[adj_revenue, -adj_expenses, None,
           baseline.get('other_income', 0) - baseline.get('other_expenses', 0), None],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))

    waterfall_fig.update_layout(
        title="Adjusted Income Statement Flow",
        showlegend=False,
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )

    # Create valuation sensitivity chart
    # Show how valuation changes with different scenarios
    scenarios = ['Base Case', 'Current Scenario']
    valuations = [baseline.get('ebitda', 0) * 8, adj_valuation]
    colors = ['#3498db', '#e67e22' if valuation_change >= 0 else '#e74c3c']

    valuation_fig = go.Figure(data=[
        go.Bar(x=scenarios, y=valuations, marker_color=colors, text=valuations,
               texttemplate='$%{text:,.0f}', textposition='outside')
    ])

    valuation_fig.update_layout(
        title=f"Valuation Comparison (Change: ${valuation_change:+,.0f})",
        yaxis_title="Valuation ($)",
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=False
    )

    # Create expense breakdown charts
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

        # Expense by type (pie chart)
        expense_type_summary = expense_df.groupby('Category_Type')['Total_Expense'].sum().reset_index()
        expense_type_fig = px.pie(
            expense_type_summary,
            values='Total_Expense',
            names='Category_Type',
            title="Expense Distribution by Type"
        )
        expense_type_fig.update_layout(height=400)
    else:
        expense_cat_fig = {}
        expense_type_fig = {}

    return adjusted_metrics_layout, waterfall_fig, valuation_fig, expense_cat_fig, expense_type_fig


if __name__ == '__main__':
    app.run(debug=True, port=8051)
