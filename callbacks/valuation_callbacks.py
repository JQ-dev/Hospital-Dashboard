"""
Valuation Callbacks - Valuation analysis with sensitivity
Extracted from dashboard.py lines 2822-3211
"""

from dash import Input, Output, html, State, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from data_loaders.valuation import load_valuation_income_statement, load_valuation_expense_detail


def register_callbacks(app, data_manager):
    """Register all valuation callbacks"""

    @app.callback(
        [Output('valuation-year-dropdown', 'options'),
         Output('valuation-year-dropdown', 'value')],
        [Input('hospital-dropdown', 'value')]
    )
    def populate_valuation_years(ccn):
        """Populate year dropdown for valuation tab"""
        if not ccn:
            return [], None
        # TODO: Query available years from income_statement_long
        return [{'label': str(year), 'value': year} for year in range(2018, 2024)], 2023

    @app.callback(
        [Output('valuation-income-data', 'data'),
         Output('valuation-expense-data', 'data'),
         Output('valuation-baseline-metrics', 'children'),
         Output('valuation-sensitivity-controls', 'children')],
        [Input('load-valuation-btn', 'n_clicks')],
        [State('hospital-dropdown', 'value'),
         State('valuation-year-dropdown', 'value')]
    )
    def load_valuation_data(n_clicks, ccn, fiscal_year):
        """Load valuation data and create interactive dashboard"""
        if not n_clicks or not ccn or not fiscal_year:
            return None, None, html.Div(), html.Div()

        # Load data
        income_df = load_valuation_income_statement(data_manager, ccn, fiscal_year)
        expense_df = load_valuation_expense_detail(data_manager, ccn, fiscal_year)

        if income_df.empty:
            return None, None, html.Div("No valuation data available", className="alert alert-warning"), html.Div()

        # TODO: Calculate baseline metrics (revenue, EBITDA, etc.)
        # TODO: Create sensitivity sliders
        # TODO: Return data and controls

        return (
            income_df.to_dict('records'),
            expense_df.to_dict('records'),
            html.Div("Baseline metrics calculation not yet implemented", className="alert alert-info"),
            html.Div()
        )

    @app.callback(
        [Output('adjusted-metrics-table', 'children'),
         Output('waterfall-chart', 'figure'),
         Output('valuation-comparison', 'figure'),
         Output('expense-breakdown', 'figure'),
         Output('expense-distribution', 'figure')],
        [Input('revenue-change-slider', 'value'),
         Input('margin-change-slider', 'value'),
         Input('expense-change-slider', 'value'),
         Input('valuation-multiple-slider', 'value')],
        [State('valuation-income-data', 'data'),
         State('valuation-expense-data', 'data')]
    )
    def update_valuation_analysis(revenue_change, margin_change, expense_change, multiple,
                                   income_data, expense_data):
        """Update valuation analysis based on slider inputs"""
        if not income_data:
            empty_fig = go.Figure()
            return html.Div(), empty_fig, empty_fig, empty_fig, empty_fig

        # TODO: Implement valuation calculations and visualizations
        empty_fig = go.Figure()
        return (
            html.Div("Valuation analysis not yet implemented", className="alert alert-info"),
            empty_fig, empty_fig, empty_fig, empty_fig
        )
