"""
CMS Worksheets Callbacks - Generic CMS worksheets viewer
Extracted from dashboard.py lines 2519-2815
"""

from dash import Input, Output, html, dash_table
import dash_bootstrap_components as dbc


def register_callbacks(app, data_manager):
    """Register all CMS worksheets callbacks"""

    @app.callback(
        [Output('cms-hospital-dropdown', 'options'),
         Output('cms-hospital-dropdown', 'value')],
        [Input('main-tabs', 'active_tab')]
    )
    def populate_cms_hospital_dropdown(active_tab):
        """Populate hospital dropdown for CMS Worksheets tab"""
        if active_tab != 'tab-cms-worksheets':
            return [], None
        # TODO: Query hospitals from worksheets database
        return [], None

    @app.callback(
        [Output('cms-year-dropdown', 'options'),
         Output('cms-year-dropdown', 'value')],
        [Input('cms-hospital-dropdown', 'value')]
    )
    def populate_cms_year_dropdown(provider_number):
        """Populate year dropdown based on selected hospital"""
        if not provider_number:
            return [], None
        # TODO: Query available years
        return [{'label': str(year), 'value': year} for year in range(2018, 2024)], 2023

    @app.callback(
        Output('cms-worksheet-content', 'children'),
        [Input('cms-worksheet-dropdown', 'value'),
         Input('cms-hospital-dropdown', 'value'),
         Input('cms-year-dropdown', 'value')]
    )
    def update_cms_worksheet_content(worksheet_code, ccn, selected_year):
        """Load and display selected CMS worksheet"""
        if not worksheet_code or not ccn or not selected_year:
            return html.Div("Please select a worksheet, hospital, and year", className="alert alert-info")

        # TODO: Implement CMS worksheet loading with roll-up logic
        return html.Div(f"CMS worksheet {worksheet_code} data loading not yet implemented", className="alert alert-info")
