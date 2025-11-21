"""
Balance Worksheets Callbacks - Worksheets G, G-1, G-2, G-3
Extracted from dashboard.py lines 1701-2512
"""

from dash import Input, Output, html, dash_table
import dash_bootstrap_components as dbc


def register_callbacks(app, data_manager):
    """Register all balance worksheets callbacks"""

    # Worksheet G callbacks
    @app.callback(
        [Output('worksheet-g-year-dropdown', 'options'),
         Output('worksheet-g-year-dropdown', 'value')],
        [Input('hospital-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def populate_worksheet_g_years(ccn, active_subtab):
        """Populate year dropdown for Worksheet G"""
        if active_subtab != 'subtab-worksheet-g' or not ccn:
            return [], None
        return [{'label': str(year), 'value': year} for year in range(2018, 2024)], 2023

    @app.callback(
        Output('worksheet-g-content', 'children'),
        [Input('hospital-dropdown', 'value'),
         Input('worksheet-g-year-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def load_worksheet_g(ccn, selected_year, active_subtab):
        """Load Worksheet G (Balance Sheet) for selected year"""
        if active_subtab != 'subtab-worksheet-g':
            return html.Div()
        if not ccn or not selected_year:
            return html.Div("Please select a hospital and year", className="alert alert-info")
        return html.Div("Worksheet G data loading not yet implemented", className="alert alert-info")

    # Worksheet G-1 callbacks
    @app.callback(
        [Output('worksheet-g1-year-dropdown', 'options'),
         Output('worksheet-g1-year-dropdown', 'value')],
        [Input('hospital-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def populate_worksheet_g1_years(ccn, active_subtab):
        """Populate year dropdown for Worksheet G-1"""
        if active_subtab != 'subtab-worksheet-g1' or not ccn:
            return [], None
        return [{'label': str(year), 'value': year} for year in range(2018, 2024)], 2023

    @app.callback(
        Output('worksheet-g1-content', 'children'),
        [Input('hospital-dropdown', 'value'),
         Input('worksheet-g1-year-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def load_worksheet_g1(ccn, selected_year, active_subtab):
        """Load Worksheet G-1 (Fund Balance Changes) for selected year"""
        if active_subtab != 'subtab-worksheet-g1':
            return html.Div()
        if not ccn or not selected_year:
            return html.Div("Please select a hospital and year", className="alert alert-info")
        return html.Div("Worksheet G-1 data loading not yet implemented", className="alert alert-info")

    # Worksheet G-2 callbacks
    @app.callback(
        [Output('worksheet-g2-year-dropdown', 'options'),
         Output('worksheet-g2-year-dropdown', 'value')],
        [Input('hospital-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def populate_worksheet_g2_years(ccn, active_subtab):
        """Populate year dropdown for Worksheet G-2"""
        if active_subtab != 'subtab-worksheet-g2' or not ccn:
            return [], None
        return [{'label': str(year), 'value': year} for year in range(2018, 2024)], 2023

    @app.callback(
        Output('worksheet-g2-content', 'children'),
        [Input('hospital-dropdown', 'value'),
         Input('worksheet-g2-year-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def load_worksheet_g2(ccn, selected_year, active_subtab):
        """Load Worksheet G-2 (Revenue) for selected year"""
        if active_subtab != 'subtab-worksheet-g2':
            return html.Div()
        if not ccn or not selected_year:
            return html.Div("Please select a hospital and year", className="alert alert-info")
        return html.Div("Worksheet G-2 data loading not yet implemented", className="alert alert-info")

    # Worksheet G-3 callbacks
    @app.callback(
        [Output('worksheet-g3-year-dropdown', 'options'),
         Output('worksheet-g3-year-dropdown', 'value')],
        [Input('hospital-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def populate_worksheet_g3_years(ccn, active_subtab):
        """Populate year dropdown for Worksheet G-3"""
        if active_subtab != 'subtab-worksheet-g3' or not ccn:
            return [], None
        return [{'label': str(year), 'value': year} for year in range(2018, 2024)], 2023

    @app.callback(
        Output('worksheet-g3-content', 'children'),
        [Input('hospital-dropdown', 'value'),
         Input('worksheet-g3-year-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def load_worksheet_g3(ccn, selected_year, active_subtab):
        """Load Worksheet G-3 (Revenue & Expenses) for selected year"""
        if active_subtab != 'subtab-worksheet-g3':
            return html.Div()
        if not ccn or not selected_year:
            return html.Div("Please select a hospital and year", className="alert alert-info")
        return html.Div("Worksheet G-3 data loading not yet implemented", className="alert alert-info")
