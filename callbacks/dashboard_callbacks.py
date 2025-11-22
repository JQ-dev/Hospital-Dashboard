"""
Dashboard Callbacks - Main dashboard, routing, and UI interactions
"""

import dash
from dash import Input, Output, State, html, ALL, MATCH, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import json

from config.mappings import DB_COLUMN_TO_KPI_KEY
from kpi_hierarchy_config import KPI_METADATA
from utils.kpi_helpers import (
    calculate_importance_score,
    calculate_dynamic_priority,
    calculate_trend
)
from components.kpi_cards import create_enhanced_level1_kpi_card
from pages.layouts import get_main_dashboard_layout, get_level2_page_layout


def register_callbacks(app, data_manager, hospital_options):
    """Register all dashboard-related callbacks"""

    # URL routing callback
    @app.callback(
        Output('page-content', 'children'),
        Input('url', 'pathname'),
        State('selected-hospital-store', 'data')  # Use State, not Input - only read when pathname changes
    )
    def display_page(pathname, selected_ccn):
        """Route between main dashboard and Level 2 drill-down pages"""
        if pathname and pathname.startswith('/level2/'):
            kpi_key = pathname.split('/')[-1]
            # Use the selected hospital from the store, fallback to default if not available
            ccn = selected_ccn if selected_ccn else '310001'
            return get_level2_page_layout(kpi_key, ccn=ccn, data_manager=data_manager)
        return get_main_dashboard_layout(hospital_options)

    @app.callback(
        [Output('hospital-name', 'children'),
         Output('hospital-type', 'children'),
         Output('benchmark-group', 'children'),
         Output('peer-count', 'children'),
         Output('kpi-cards-container', 'children'),
         Output('selected-hospital-store', 'data')],  # Update the store with selected hospital
        [Input('hospital-dropdown', 'value'),
         Input('sort-importance', 'n_clicks'),
         Input('sort-performance', 'n_clicks'),
         Input('sort-trend', 'n_clicks')]
    )
    def update_dashboard(ccn, sort_imp, sort_perf, sort_trend):
        """Main callback to update entire dashboard - shows all benchmark levels on each card"""

        # Ensure CCN is properly formatted as 6-digit string with leading zeros
        ccn_str = str(int(ccn)).zfill(6)

        # Get hospital metadata
        hospital_type = data_manager.classify_hospital_type(ccn_str)
        state_code = ccn_str[:2]

        # DEBUG: Log data source status
        print(f"\n[DEBUG] Data Manager Status:")
        print(f"  - Using database: {data_manager.use_database}")
        print(f"  - Using precomputed KPIs: {data_manager.use_precomputed}")
        print(f"  - Using worksheets: {data_manager.use_worksheets}")
        print(f"  - Worksheet tables available: {len(data_manager.worksheet_tables) if data_manager.worksheet_tables else 0}")

        # Get KPI data
        kpi_data = data_manager.calculate_kpis(ccn)

        print(f"\n[DEBUG] KPI Data for CCN {ccn}:")
        print(f"  - DataFrame shape: {kpi_data.shape}")
        print(f"  - Columns: {list(kpi_data.columns)}")
        if not kpi_data.empty:
            print(f"  - Fiscal years: {sorted(kpi_data['Fiscal_Year'].unique())}")
            print(f"  - Sample data (first row): {kpi_data.iloc[0].to_dict() if len(kpi_data) > 0 else 'No rows'}")

        if kpi_data.empty:
            print("[DEBUG] No KPI data available - returning early")
            return "N/A", "N/A", "N/A", "N/A", html.Div("No data available"), ccn

        latest_year = kpi_data['Fiscal_Year'].max()

        # Calculate Level 2 KPIs
        print(f"Calculating Level 2 KPIs for {ccn}, year {latest_year}...")
        l2_kpis = data_manager.calculate_level2_kpis(ccn, latest_year)
        if l2_kpis:
            print(f"Level 2 KPIs calculated: {sum(1 for v in l2_kpis.values() if v is not None)}/{len(l2_kpis)} KPIs")
        else:
            print("Level 2 KPIs not available (worksheet database not connected)")

        # Calculate Level 3 KPIs
        print(f"Calculating Level 3 KPIs for {ccn}, year {latest_year}...")
        l3_kpis = data_manager.calculate_level3_kpis(ccn, latest_year)
        if l3_kpis:
            print(f"Level 3 KPIs calculated: {sum(1 for v in l3_kpis.values() if v is not None)}/{len(l3_kpis)} KPIs")
        else:
            print("Level 3 KPIs not available (worksheet database not connected)")

        # Calculate ALL 4 benchmark levels (for new enhanced card design)
        # Order: State & Type (most specific), State, Hospital Type, National (broadest)
        print(f"Calculating benchmarks for {ccn} at all levels...")
        all_benchmarks = {
            'state_hospital_type': data_manager.get_benchmarks(ccn, latest_year, 'State_Hospital_Type'),
            'state': data_manager.get_benchmarks(ccn, latest_year, 'State'),
            'hospital_type': data_manager.get_benchmarks(ccn, latest_year, 'Hospital_Type'),
            'national': data_manager.get_benchmarks(ccn, latest_year, 'National')
        }
        # Use state & type (most specific) as primary benchmark for display purposes (shown in header)
        benchmark_data = all_benchmarks['state_hospital_type']
        print(f"Benchmarks calculated: State & Type={all_benchmarks['state_hospital_type']['provider_count']}, State={all_benchmarks['state']['provider_count']}, Type={all_benchmarks['hospital_type']['provider_count']}, National={all_benchmarks['national']['provider_count']} peers")

        # Create KPI cards
        kpi_cards = []
        kpi_rankings = []

        # Define the 6 Level 1 KPIs from to_do.txt - ONLY show these
        LEVEL_1_KPIS = {
            'Net_Income_Margin',                      # L1 KPI 1: Net Income Margin
            'AR_Days',                                # L1 KPI 2: Days in Net Patient AR
            'Operating_Expense_per_Adjusted_Discharge',  # L1 KPI 3: Operating Expense per Adjusted Discharge
            'Medicare_CCR',                           # L1 KPI 4: Medicare Cost-to-Charge Ratio
            'Bad_Debt_Charity_Pct',                   # L1 KPI 5: Bad Debt + Charity %
            'Current_Ratio'                           # L1 KPI 6: Current Ratio
        }

        # Create a reverse mapping to find database columns for each KPI key
        kpi_key_to_db_col = {}
        for db_col in kpi_data.columns:
            if db_col not in ['Provider_Number', 'Fiscal_Year']:
                kpi_key = DB_COLUMN_TO_KPI_KEY.get(db_col, db_col)
                kpi_key_to_db_col[kpi_key] = db_col

        # DEBUG: Log KPI key to column mapping
        print(f"\n[DEBUG] KPI Key to DB Column Mapping:")
        for k, v in kpi_key_to_db_col.items():
            print(f"  {k} -> {v}")

        # Loop through ALL Level 1 KPIs to ensure all 6 show up
        for kpi_key in LEVEL_1_KPIS:
            # Skip if not in metadata
            if kpi_key not in KPI_METADATA:
                print(f"[DEBUG] Skipping {kpi_key} - not in KPI_METADATA")
                continue

            # Get KPI metadata
            kpi_meta = KPI_METADATA.get(kpi_key, {})
            higher_is_better = kpi_meta.get('higher_is_better', True)

            # Check if we have data for this KPI
            db_col = kpi_key_to_db_col.get(kpi_key)

            if db_col and db_col in kpi_data.columns:
                # We have data - use actual values
                kpi_values = kpi_data[db_col].values
                kpi_value = kpi_values[0] if len(kpi_values) > 0 else None
                print(f"[DEBUG] {kpi_key}: Found column '{db_col}', value = {kpi_value}")
            else:
                # No data available - show as "Data Not Available"
                kpi_values = [None] * len(kpi_data)
                kpi_value = None
                db_col = None  # Mark as no column available
                print(f"[DEBUG] {kpi_key}: No column found (looked for '{kpi_key}' -> '{db_col}'), value = None")

            # Get benchmark (use metadata key)
            benchmark_kpis = benchmark_data.get('kpis', {})
            kpi_benchmark = benchmark_kpis.get(kpi_key, {})
            median = kpi_benchmark.get('Median')

            # Calculate DYNAMIC priority
            dynamic_priority = calculate_dynamic_priority(kpi_key, kpi_value, median, higher_is_better)

            # Calculate performance gap
            if kpi_value and median:
                if higher_is_better:
                    perf_gap = median - kpi_value
                else:
                    perf_gap = kpi_value - median
            else:
                perf_gap = 0

            # Calculate trend
            trend_direction, trend_pct = calculate_trend(kpi_values)

            kpi_rankings.append({
                'kpi_key': kpi_key,
                'db_column': db_col,  # Will be None if no data
                'dynamic_priority': dynamic_priority,
                'importance': calculate_importance_score(kpi_key),
                'perf_gap': abs(perf_gap),
                'trend_pct': abs(trend_pct),
                'kpi_value': kpi_value,
                'kpi_values': kpi_values
            })

        # Determine sort order
        ctx = dash.callback_context
        if ctx.triggered:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if button_id == 'sort-performance':
                kpi_rankings.sort(key=lambda x: x['perf_gap'], reverse=True)
            elif button_id == 'sort-trend':
                kpi_rankings.sort(key=lambda x: x['trend_pct'], reverse=True)
            else:
                kpi_rankings.sort(key=lambda x: x['dynamic_priority'], reverse=True)
        else:
            kpi_rankings.sort(key=lambda x: x['dynamic_priority'], reverse=True)

        # Create cards in sorted order (use ENHANCED cards with all benchmark levels)
        for idx, ranking in enumerate(kpi_rankings):
            card = create_enhanced_level1_kpi_card(
                kpi_key=ranking['kpi_key'],
                kpi_value=ranking['kpi_value'],
                kpi_trend_values=ranking['kpi_values'],
                fiscal_years=kpi_data['Fiscal_Year'].values,
                all_benchmarks=all_benchmarks,  # Pass all 4 benchmark levels
                rank=idx + 1,
                l2_kpis=l2_kpis,
                l3_kpis=l3_kpis,
                ccn=ccn,
                fiscal_year=latest_year,
                db_column=ranking['db_column'],  # Pass database column name for benchmark lookup
                data_manager=data_manager,  # Pass data_manager for fetching base calculation data
                kpi_data_df=kpi_data  # Pass the full kpi_data DataFrame
            )
            # 3 cards per row: width=12 (full on mobile), lg=4 (3 per row on desktop)
            kpi_cards.append(dbc.Col(card, width=12, lg=4))

        # Layout cards in grid
        cards_grid = dbc.Row(kpi_cards)

        return (
            f"CCN {ccn}",
            hospital_type,
            benchmark_data.get('group_name', 'N/A'),
            f"{benchmark_data.get('provider_count', 0):,}",
            cards_grid,
            ccn  # Store the selected hospital CCN for drill-down navigation
        )

    # Sync hospital dropdown with store when navigating back from drill-down
    @app.callback(
        Output('hospital-dropdown', 'value'),
        Input('url', 'pathname'),
        State('selected-hospital-store', 'data')
    )
    def sync_dropdown_with_store(pathname, stored_ccn):
        """When returning to main dashboard, restore the selected hospital from store"""
        # Only update dropdown when on main dashboard (not drill-down pages)
        if not pathname or pathname == '/' or not pathname.startswith('/level2/'):
            return stored_ccn if stored_ccn else '310001'
        # For drill-down pages, don't update (prevents error when dropdown doesn't exist)
        return dash.no_update

    # Expand/Collapse Level 2 KPIs callback
    @app.callback(
        [Output({'type': 'l2-collapse', 'index': MATCH}, 'is_open'),
         Output({'type': 'expand-icon', 'index': MATCH}, 'className')],
        [Input({'type': 'expand-btn', 'index': MATCH}, 'n_clicks')],
        [State({'type': 'l2-collapse', 'index': MATCH}, 'is_open')],
        prevent_initial_call=True
    )
    def toggle_l2_kpis(n_clicks, is_open):
        """Toggle Level 2 KPIs visibility"""
        if n_clicks:
            new_state = not is_open
            # Change icon based on state
            icon_class = "fas fa-chevron-up me-2" if new_state else "fas fa-chevron-down me-2"
            return new_state, icon_class
        return is_open, "fas fa-chevron-down me-2"

    # Level 3 expand/collapse callback
    @app.callback(
        [Output({'type': 'l3-collapse', 'index': MATCH}, 'is_open'),
         Output({'type': 'expand-l3-icon', 'index': MATCH}, 'className')],
        [Input({'type': 'expand-l3-btn', 'index': MATCH}, 'n_clicks')],
        [State({'type': 'l3-collapse', 'index': MATCH}, 'is_open')],
        prevent_initial_call=True
    )
    def toggle_l3_kpis(n_clicks, is_open):
        """Toggle Level 3 KPIs visibility"""
        if n_clicks:
            new_state = not is_open
            # Change icon based on state
            icon_class = "fas fa-chevron-up me-1" if new_state else "fas fa-chevron-down me-1"
            return new_state, icon_class
        return is_open, "fas fa-chevron-down me-1"

    # Modal callbacks
    @app.callback(
        [Output("data-modal", "is_open"),
         Output("modal-title", "children"),
         Output("modal-body", "children")],
        [Input({'type': 'view-data-btn', 'index': ALL}, 'n_clicks'),
         Input("close-modal", "n_clicks")],
        [State("data-modal", "is_open"),
         State('hospital-dropdown', 'value')],
        prevent_initial_call=True
    )
    def toggle_modal(view_clicks, close_clicks, _is_open, ccn):
        """Handle modal open/close and populate with KPI data table"""
        ctx = dash.callback_context

        if not ctx.triggered:
            return dash.no_update, dash.no_update, dash.no_update

        trigger_id = ctx.triggered[0]['prop_id']

        # If no actual click happened (just a re-render), don't update
        if not trigger_id or trigger_id == '.':
            return dash.no_update, dash.no_update, dash.no_update

        # Close modal
        if 'close-modal' in trigger_id:
            return False, "", ""

        # Open modal with KPI data - only if a button was actually clicked
        if 'view-data-btn' in trigger_id:
            # Check if this was an actual click (not None and > 0)
            if view_clicks and any(clicks for clicks in view_clicks if clicks and clicks > 0):
                # Extract KPI key from button ID
                button_id = json.loads(trigger_id.split('.')[0])
                kpi_key = button_id['index']

                # Get KPI data
                kpi_data = data_manager.calculate_kpis(ccn)

                if kpi_data.empty:
                    return True, "No Data", html.Div("No data available for this hospital", className="alert alert-warning")

                # Get KPI metadata
                kpi_meta = KPI_METADATA.get(kpi_key, {})

                # Create table with all years
                table_data = kpi_data[['Fiscal_Year', kpi_key]].copy()
                table_data = table_data.sort_values('Fiscal_Year', ascending=True)

                # Format values
                fmt = kpi_meta.get('format', '.2f')
                unit = kpi_meta.get('unit', '')

                table_data['Formatted_Value'] = table_data[kpi_key].apply(
                    lambda x: f"{x:{fmt}}{unit}" if pd.notna(x) else "N/A"
                )

                # Create table
                display_df = table_data[['Fiscal_Year', 'Formatted_Value']].rename(
                    columns={'Fiscal_Year': 'Year', 'Formatted_Value': kpi_meta.get('name', kpi_key)}
                )

                table = dbc.Table.from_dataframe(
                    display_df,
                    striped=True,
                    bordered=True,
                    hover=True,
                    responsive=True,
                    className="table-sm"
                )

                # Create modal title
                title = f"{kpi_meta.get('name', kpi_key)} - Historical Data"

                # Create body
                body = html.Div([
                    html.P([
                        html.Strong("Description: "),
                        kpi_meta.get('description', 'No description available')
                    ], className="text-muted mb-2"),
                    html.P([
                        html.Strong("Target Range: "),
                        f"{kpi_meta.get('target_range', (0, 0))[0]}-{kpi_meta.get('target_range', (0, 0))[1]}{unit}"
                    ], className="text-muted mb-3"),
                    table
                ])

                return True, title, body
            else:
                # Button rendered but not clicked - don't update
                return dash.no_update, dash.no_update, dash.no_update

        return dash.no_update, dash.no_update, dash.no_update

    # Update header hospital info (shared across tabs)
    @app.callback(
        [Output('header-hospital-name', 'children'),
         Output('header-hospital-type', 'children')],
        [Input('hospital-dropdown', 'value')]
    )
    def update_header_info(ccn):
        """Update hospital info in header"""
        hospital_type = data_manager.classify_hospital_type(ccn)
        return f"CCN {ccn}", hospital_type

    # Update footer to show data source
    @app.callback(
        Output('footer-datasource', 'children'),
        [Input('hospital-dropdown', 'value')]  # Trigger on load
    )
    def update_footer(_):
        """Show data source in footer"""
        if data_manager.use_database:
            return f"Data Source: DuckDB Database ({data_manager.db_path}) | With Indexes for Fast Queries"
        else:
            return "Data Source: CMS HCRIS Parquet Files | No database (slower)"
