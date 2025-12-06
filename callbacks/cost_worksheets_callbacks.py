"""
Cost Worksheets Callbacks - Detailed costs (Worksheet A) and overhead costs (Worksheet B)
Extracted from dashboard.py lines 1365-1697
"""

from dash import Input, Output, html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from utils.kpi_helpers import get_professional_datatable_style
from config.paths import COSTS_A000_OUTPUT, COSTS_B100_OUTPUT


def register_callbacks(app, data_manager):
    """Register all cost worksheets callbacks"""

    # Populate year dropdown for detailed costs
    @app.callback(
        [Output('detailed-costs-year-dropdown', 'options'),
         Output('detailed-costs-year-dropdown', 'value')],
        [Input('hospital-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def populate_detailed_costs_years(ccn, active_subtab):
        """Populate available years for detailed costs when hospital is selected"""
        if active_subtab != 'subtab-detailed-costs' or not ccn:
            return [], None

        try:
            con = data_manager.get_connection()
            if data_manager.use_database:
                years_df = con.execute("""
                    SELECT DISTINCT Fiscal_Year
                    FROM costs_a000
                    WHERE Provider_Number = ?
                    ORDER BY Fiscal_Year DESC
                """, [int(ccn)]).df()
            else:
                costs_a000_path = str(COSTS_A000_OUTPUT / '**/*.parquet')
                years_df = con.execute("""
                    SELECT DISTINCT Fiscal_Year
                    FROM read_parquet(?, hive_partitioning=1)
                    WHERE Provider_Number = ?
                    ORDER BY Fiscal_Year DESC
                """, [costs_a000_path, int(ccn)]).df()
            con.close()

            if years_df.empty:
                return [], None

            years = years_df['Fiscal_Year'].tolist()
            options = [{'label': str(int(year)), 'value': int(year)} for year in years]
            default_value = int(years[0])  # Most recent year
            return options, default_value
        except Exception as e:
            # Log error but return empty to avoid crashing the UI
            import logging
            logging.getLogger(__name__).debug(f"Error loading years for detailed costs: {e}")
            return [], None

    # Load detailed costs (Worksheet A)
    @app.callback(
        Output('detailed-costs-content', 'children'),
        [Input('hospital-dropdown', 'value'),
         Input('detailed-costs-year-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def load_detailed_costs(ccn, selected_year, active_subtab):
        """Load and display detailed costs from Schedule A for selected year"""
        # Only load if this tab is active (important for performance!)
        if active_subtab != 'subtab-detailed-costs':
            return html.Div()

        if not ccn:
            return html.Div("Please select a hospital", className="alert alert-info")

        if not selected_year:
            return html.Div("Please select a fiscal year", className="alert alert-info")

        try:
            con = data_manager.get_connection()

            if data_manager.use_database:
                # Simple query: get A000 data for the selected year and pivot columns based on Cost_type
                df = con.execute("""
                    SELECT
                        Line,
                        Account_group,
                        Account_name,
                        MAX(CASE WHEN "Column" = '00100' THEN Value ELSE 0 END) as Salaries,
                        MAX(CASE WHEN "Column" = '00200' THEN Value ELSE 0 END) as Other,
                        MAX(CASE WHEN "Column" = '00600' THEN Value ELSE 0 END) as Adjustments
                    FROM costs_a000
                    WHERE Provider_Number = ?
                        AND Fiscal_Year = ?
                        AND Account_name is not null
                    GROUP BY Line, Account_group, Account_name
                    ORDER BY CAST(Line AS INTEGER)
                """, [int(ccn), int(selected_year)]).df()
            else:
                # Fallback to parquet
                costs_a000_path = str(COSTS_A000_OUTPUT / '**/*.parquet')
                df = con.execute("""
                    SELECT
                        Line,
                        Account_group,
                        Account_name,
                        MAX(CASE WHEN "Column" = '00100' THEN Value ELSE 0 END) as Salaries,
                        MAX(CASE WHEN "Column" = '00200' THEN Value ELSE 0 END) as Other,
                        MAX(CASE WHEN "Column" = '00600' THEN Value ELSE 0 END) as Adjustments
                    FROM read_parquet(?, hive_partitioning=1)
                    WHERE Provider_Number = ?
                        AND Fiscal_Year = ?
                    GROUP BY Line, Account_group, Account_name
                    ORDER BY CAST(Line AS INTEGER)
                """, [costs_a000_path, int(ccn), int(selected_year)]).df()

            con.close()

            if df.empty:
                return html.Div(f"No detailed costs data available for fiscal year {selected_year}", className="alert alert-warning")

            # Format table with professional styling
            pro_style = get_professional_datatable_style()

            table = dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[
                    {'name': 'Line', 'id': 'Line'},
                    {'name': 'Account Group', 'id': 'Account_group'},
                    {'name': 'Account Name', 'id': 'Account_name'},
                    {'name': 'Salaries', 'id': 'Salaries', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
                    {'name': 'Other', 'id': 'Other', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
                    {'name': 'Adjustments', 'id': 'Adjustments', 'type': 'numeric', 'format': {'specifier': '$,.0f'}},
                ],
                style_table=pro_style['style_table'],
                style_cell=pro_style['style_cell'],
                style_cell_conditional=pro_style['style_cell_conditional'] + [
                    {
                        'if': {'column_id': 'Account_group'},
                        'fontWeight': '600',
                        'color': '#5a6c7d'
                    },
                    {
                        'if': {'column_id': 'Account_name'},
                        'minWidth': '200px',
                        'fontWeight': '500'
                    }
                ],
                style_header=pro_style['style_header'],
                style_data=pro_style['style_data'],
                style_data_conditional=pro_style['style_data_conditional'],
                page_size=50,
                filter_action='native',
                sort_action='native'
            )

            return html.Div([
                html.H5(f"Worksheet A - Cost Report (Fiscal Year {selected_year})", className="mb-3"),
                table
            ])
        except Exception as e:
            import traceback
            traceback.print_exc()
            return html.Div(f"Error loading detailed costs: {str(e)}", className="alert alert-danger")

    # Populate year dropdown for Worksheet B
    @app.callback(
        [Output('worksheet-b-year-dropdown', 'options'),
         Output('worksheet-b-year-dropdown', 'value')],
        [Input('hospital-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def populate_worksheet_b_years(ccn, active_subtab):
        """Populate available years for worksheet B when hospital is selected"""
        if active_subtab != 'subtab-worksheet-b' or not ccn:
            return [], None

        try:
            con = data_manager.get_connection()
            if data_manager.use_database:
                years_df = con.execute("""
                    SELECT DISTINCT Fiscal_Year
                    FROM costs_b100
                    WHERE Provider_Number = ?
                    ORDER BY Fiscal_Year DESC
                """, [int(ccn)]).df()
            else:
                costs_b100_path = str(COSTS_B100_OUTPUT / '**/*.parquet')
                years_df = con.execute("""
                    SELECT DISTINCT Fiscal_Year
                    FROM read_parquet(?, hive_partitioning=1)
                    WHERE Provider_Number = ?
                    ORDER BY Fiscal_Year DESC
                """, [costs_b100_path, int(ccn)]).df()
            con.close()

            if years_df.empty:
                return [], None

            years = years_df['Fiscal_Year'].tolist()
            options = [{'label': str(int(year)), 'value': int(year)} for year in years]
            default_value = int(years[0])  # Most recent year
            return options, default_value
        except Exception as e:
            # Log error but return empty to avoid crashing the UI
            import logging
            logging.getLogger(__name__).debug(f"Error loading years for worksheet B: {e}")
            return [], None

    # Load Worksheet B (Overhead Costs)
    @app.callback(
        Output('worksheet-b-content', 'children'),
        [Input('hospital-dropdown', 'value'),
         Input('worksheet-b-year-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def load_worksheet_b(ccn, selected_year, active_subtab):
        """Load and display worksheet B (Schedule B-1 - Overhead Costs) for selected year"""
        # Only load if this tab is active (important for performance!)
        if active_subtab != 'subtab-worksheet-b':
            return html.Div()

        if not ccn:
            return html.Div("Please select a hospital", className="alert alert-info")

        if not selected_year:
            return html.Div("Please select a fiscal year", className="alert alert-info")

        try:
            con = data_manager.get_connection()

            if data_manager.use_database:
                # Get all overhead centers with their column values for sorting
                df = con.execute("""
                    SELECT
                        Line,
                        Account_group,
                        Account_name,
                        "Column",
                        Overhead_center,
                        Value
                    FROM costs_b100
                    WHERE Provider_Number = ?
                        AND Fiscal_Year = ?
                        AND Account_name IS NOT NULL
                        AND Overhead_center IS NOT NULL
                    ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
                """, [int(ccn), int(selected_year)]).df()
            else:
                # Fallback to parquet
                costs_b100_path = str(COSTS_B100_OUTPUT / '**/*.parquet')
                df = con.execute("""
                    SELECT
                        Line,
                        Account_group,
                        Account_name,
                        "Column",
                        Overhead_center,
                        Value
                    FROM read_parquet(?, hive_partitioning=1)
                    WHERE Provider_Number = ?
                        AND Fiscal_Year = ?
                        AND Account_name IS NOT NULL
                        AND Overhead_center IS NOT NULL
                    ORDER BY CAST(Line AS INTEGER), CAST("Column" AS INTEGER)
                """, [costs_b100_path, int(ccn), int(selected_year)]).df()

            con.close()

            if df.empty:
                return html.Div(f"No worksheet B data available for fiscal year {selected_year}", className="alert alert-warning")

            # Create mapping of Overhead_center to Column for sorting
            column_mapping = df[['Overhead_center', 'Column']].drop_duplicates()
            column_mapping['Column_Int'] = column_mapping['Column'].astype(int)
            column_mapping = column_mapping.sort_values('Column_Int')
            overhead_order = column_mapping['Overhead_center'].tolist()

            # Pivot the dataframe to have overhead centers as columns
            pivot_df = df.pivot_table(
                index=['Line', 'Account_group', 'Account_name'],
                columns='Overhead_center',
                values='Value',
                aggfunc='sum',
                fill_value=0
            ).reset_index()

            # Reorder columns based on Column value
            base_cols = ['Line', 'Account_group', 'Account_name']
            ordered_overhead_cols = [col for col in overhead_order if col in pivot_df.columns]
            pivot_df = pivot_df[base_cols + ordered_overhead_cols]

            # Build column definitions dynamically based on overhead centers present
            columns = [
                {'name': 'Line', 'id': 'Line'},
                {'name': 'Account Group', 'id': 'Account_group'},
                {'name': 'Account Name', 'id': 'Account_name'},
            ]

            # Add columns for each overhead center (already sorted by Column value)
            for col in pivot_df.columns[3:]:  # Skip Line, Account_group, Account_name
                columns.append({
                    'name': col,
                    'id': col,
                    'type': 'numeric',
                    'format': {'specifier': '$,.0f'}
                })

            # Format table with professional styling
            pro_style = get_professional_datatable_style()

            table = dash_table.DataTable(
                data=pivot_df.to_dict('records'),
                columns=columns,
                style_table=pro_style['style_table'],
                style_cell=pro_style['style_cell'],
                style_cell_conditional=pro_style['style_cell_conditional'] + [
                    {
                        'if': {'column_id': 'Account_group'},
                        'fontWeight': '600',
                        'color': '#5a6c7d'
                    },
                    {
                        'if': {'column_id': 'Account_name'},
                        'minWidth': '200px',
                        'fontWeight': '500'
                    }
                ],
                style_header=pro_style['style_header'],
                style_data=pro_style['style_data'],
                style_data_conditional=pro_style['style_data_conditional'],
                page_size=50,
                filter_action='native',
                sort_action='native'
            )

            return html.Div([
                html.H5(f"Worksheet B - Overhead Costs (Fiscal Year {selected_year})", className="mb-3"),
                table
            ])
        except Exception as e:
            import traceback
            traceback.print_exc()
            return html.Div(f"Error loading worksheet B: {str(e)}", className="alert alert-danger")
