"""
Financial Statements Callbacks - Balance sheet, revenue, expenses, fund balance
Extracted from dashboard.py lines 1105-2466
"""

from dash import Input, Output, html
import dash_bootstrap_components as dbc
from utils.financial_tables import create_multiyear_financial_table


def register_callbacks(app, data_manager):
    """Register all financial statements callbacks"""

    # Load Balance Sheet data
    @app.callback(
        Output('balance-sheet-content', 'children'),
        [Input('hospital-dropdown', 'value'),
         Input('fund-type-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def load_balance_sheet(ccn, fund_type, active_subtab):
        """Load and display balance sheet for all years, filtered by fund type"""
        # Only load if this tab is active
        if active_subtab != 'subtab-balance-sheet':
            return html.Div()

        if not ccn:
            return html.Div("Please select a hospital", className="alert alert-info")

        if not fund_type:
            fund_type = 'General Fund'

        try:
            con = data_manager.get_connection()
            query = """
            SELECT
                Fiscal_Year,
                Line,
                Acc_level1,
                Acc_level2,
                Acc_level3,
                Acc_name,
                Value
            FROM balance_sheet
            WHERE Provider_Number = ?
                AND Acc_level1 = ?
            ORDER BY Fiscal_Year DESC, Line
            """
            df = con.execute(query, [int(ccn), fund_type]).df()
            con.close()

            if df.empty:
                return html.Div(f"No balance sheet data for {fund_type}", className="alert alert-info")

            return create_multiyear_financial_table(df, f"Balance Sheet - {fund_type}", 'balance_sheet')

        except Exception as e:
            return html.Div(f"Error loading balance sheet: {e}", className="alert alert-danger")

    # Load Revenue detail
    @app.callback(
        Output('revenue-content', 'children'),
        [Input('hospital-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def load_revenue(ccn, active_subtab):
        """Load and display revenue detail for all years"""
        if active_subtab != 'subtab-revenue':
            return html.Div()

        if not ccn:
            return html.Div("Please select a hospital", className="alert alert-info")

        try:
            con = data_manager.get_connection()
            query = """
            SELECT
                Fiscal_Year,
                Line,
                Revenue_Center,
                Revenue_Group,
                Revenue_Subgroup,
                Revenue_Subgroup_Detail,
                Value
            FROM revenue
            WHERE Provider_Number = ?
            ORDER BY Fiscal_Year DESC, Line
            """
            df = con.execute(query, [int(ccn)]).df()
            con.close()

            if df.empty:
                return html.Div("No revenue data available", className="alert alert-info")

            return create_multiyear_financial_table(df, "Revenue Detail", 'revenue')

        except Exception as e:
            return html.Div(f"Error loading revenue: {e}", className="alert alert-danger")

    # Load Revenue & Expenses
    @app.callback(
        Output('revenue-expenses-content', 'children'),
        [Input('hospital-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def load_revenue_expenses(ccn, active_subtab):
        """Load and display revenue & expenses statement for all years"""
        if active_subtab != 'subtab-revenue-expenses':
            return html.Div()

        if not ccn:
            return html.Div("Please select a hospital", className="alert alert-info")

        try:
            con = data_manager.get_connection()
            query = """
            SELECT
                Fiscal_Year,
                Line,
                RE_Line_Name,
                RE_Level,
                Value
            FROM revenue_expenses
            WHERE Provider_Number = ?
            ORDER BY Fiscal_Year DESC, Line
            """
            df = con.execute(query, [int(ccn)]).df()
            con.close()

            if df.empty:
                return html.Div("No revenue & expenses data available", className="alert alert-info")

            return create_multiyear_financial_table(df, "Revenue & Expenses", 'revenue_expenses')

        except Exception as e:
            return html.Div(f"Error loading revenue & expenses: {e}", className="alert alert-danger")

    # Load Cost Summary
    @app.callback(
        Output('cost-summary-content', 'children'),
        [Input('hospital-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def load_cost_summary(ccn, active_subtab):
        """Load and display cost summary for all years"""
        if active_subtab != 'subtab-cost-summary':
            return html.Div()

        if not ccn:
            return html.Div("Please select a hospital", className="alert alert-info")

        # Note: Cost summary data quality issues - show warning
        return html.Div([
            html.Div("⚠️ Cost Summary (Worksheet B100) has known data quality issues", className="alert alert-warning"),
            html.P("We're working on improving this data. Please use the Detailed Costs tab for more accurate information.")
        ])

    # Load Fund Balance Changes
    @app.callback(
        Output('fund-balance-changes-content', 'children'),
        [Input('hospital-dropdown', 'value'),
         Input('financial-subtabs', 'active_tab')]
    )
    def load_fund_balance_changes(ccn, active_subtab):
        """Load and display fund balance changes for all years"""
        if active_subtab != 'subtab-fund-balance-changes':
            return html.Div()

        if not ccn:
            return html.Div("Please select a hospital", className="alert alert-info")

        try:
            con = data_manager.get_connection()
            query = """
            SELECT
                Fiscal_Year,
                Line,
                Acc_level1,
                Acc_level2,
                Acc_name,
                Value
            FROM fund_balance_changes
            WHERE Provider_Number = ?
            ORDER BY Fiscal_Year DESC, Line
            """
            df = con.execute(query, [int(ccn)]).df()
            con.close()

            if df.empty:
                return html.Div("No fund balance changes data available", className="alert alert-info")

            return create_multiyear_financial_table(df, "Fund Balance Changes", 'fund_balance_changes')

        except Exception as e:
            return html.Div(f"Error loading fund balance changes: {e}", className="alert alert-danger")
