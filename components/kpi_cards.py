"""
KPI Card Components

This module contains functions for creating different types of KPI cards:
- create_kpi_card: Basic interactive KPI card
- create_enhanced_level1_kpi_card: Enhanced Level 1 KPI card with 4 benchmark levels
- create_hierarchical_kpi_card: Hierarchical KPI card with expandable Level 2/3 drivers
"""

from dash import dcc, html
import dash_bootstrap_components as dbc
import pandas as pd

from kpi_hierarchy_config import KPI_METADATA
from utils.kpi_helpers import (
    calculate_percentile_rank,
    calculate_trend,
    create_sparkline
)


def create_kpi_card(kpi_key, kpi_value, kpi_trend_values, fiscal_years,
                    benchmark_data, rank, importance_score):
    """
    Create an interactive KPI card

    Front: Shows KPI value, trend, benchmark comparison
    """
    meta = KPI_METADATA.get(kpi_key, {})
    kpi_name = meta.get('name', kpi_key)
    category = meta.get('category', 'General')
    unit = meta.get('unit', '')
    fmt = meta.get('format', '.1f')
    higher_is_better = meta.get('higher_is_better', True)

    # Get benchmark comparison
    benchmark_kpis = benchmark_data.get('kpis', {})
    kpi_benchmark = benchmark_kpis.get(kpi_key, {})
    p25 = kpi_benchmark.get('P25')
    median = kpi_benchmark.get('Median')
    p75 = kpi_benchmark.get('P75')
    mean = kpi_benchmark.get('Mean')

    # Calculate performance vs benchmark
    perf_label, perf_color = calculate_percentile_rank(kpi_value, p25, median, p75)

    # Calculate trend
    trend_direction, trend_pct = calculate_trend(kpi_trend_values)

    # Trend icon
    trend_icons = {
        'up': '↑',
        'down': '↓',
        'stable': '→'
    }
    trend_colors = {
        'up': 'success' if higher_is_better else 'danger',
        'down': 'danger' if higher_is_better else 'success',
        'stable': 'secondary'
    }

    # Create sparkline
    sparkline_fig = create_sparkline(kpi_trend_values, fiscal_years)

    # Card content
    card = dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H6(kpi_name, className="mb-0"),
                    html.Small(category, className="text-muted")
                ], width=8),
                dbc.Col([
                    dbc.Badge(f"#{rank}", color="primary", className="float-end")
                ], width=4)
            ])
        ]),
        dbc.CardBody([
            # Main KPI Value
            html.Div([
                html.H2(
                    f"{kpi_value:{fmt}}{unit}" if not pd.isna(kpi_value) else "N/A",
                    className="mb-2"
                ),
                dbc.Badge(
                    f"{trend_icons[trend_direction]} {abs(trend_pct):.1f}%",
                    color=trend_colors[trend_direction],
                    className="me-2"
                ),
            ]),

            # Sparkline
            html.Div([
                dcc.Graph(
                    figure=sparkline_fig,
                    config={'displayModeBar': False},
                    style={'height': '50px'}
                )
            ], className="mt-2 mb-3"),

            # Benchmark Comparison
            html.Div([
                html.Hr(),
                html.Small("Benchmark Comparison", className="text-muted d-block mb-2"),
                html.Div([
                    html.Strong(f"Mean: {format(mean, fmt)}{unit}" if mean else "Mean: N/A",
                               className="text-primary me-3"),
                    dbc.Badge(perf_label if perf_label else "N/A", color=perf_color, className="me-2")
                ], className="mb-2"),
                dbc.Progress([
                    dbc.Progress(value=25, color="danger", bar=True),
                    dbc.Progress(value=25, color="warning", bar=True),
                    dbc.Progress(value=25, color="info", bar=True),
                    dbc.Progress(value=25, color="success", bar=True),
                ], className="mb-2", style={'height': '8px'}),
                dbc.Row([
                    dbc.Col(html.Small(f"P25: {format(p25, fmt)}{unit}" if p25 else "N/A"), width=4),
                    dbc.Col(html.Small(f"Median: {format(median, fmt)}{unit}" if median else "N/A"), width=4),
                    dbc.Col(html.Small(f"P75: {format(p75, fmt)}{unit}" if p75 else "N/A"), width=4)
                ])
            ]),

            # Importance Score
            html.Hr(),
            html.Div([
                html.Small(f"Importance Score: {importance_score:.0f}/100", className="text-muted"),
                dbc.Progress(value=importance_score, max=100, className="mt-1",
                           color="primary", style={'height': '4px'})
            ]),

            # View Data Button
            html.Hr(),
            dbc.Button(
                [html.I(className="fas fa-table me-2"), "View Data"],
                id={'type': 'view-data-btn', 'index': kpi_key},
                color="outline-primary",
                size="sm",
                className="w-100"
            )
        ])
    ], className="shadow-sm mb-3", style={'height': '100%'})

    return card


def create_enhanced_level1_kpi_card(kpi_key, kpi_value, kpi_trend_values, fiscal_years,
                                     all_benchmarks, rank, l2_kpis=None, l3_kpis=None, ccn=None, fiscal_year=None, db_column=None):
    """
    Create enhanced Level 1 KPI card with:
    - 5-year trend visualization
    - All 4 benchmark levels (ordered from most to least specific):
      1. Hospital Type and State (most specific)
      2. Hospitals in State
      3. Hospital Type
      4. Hospital Nationwide (broadest)
    - KPI description and explanation
    - Expandable Level 2/3 drivers
    - Clean, aesthetic layout

    Args:
        kpi_key: KPI identifier
        kpi_value: Current value
        kpi_trend_values: 5-year historical values
        fiscal_years: Years for trend
        all_benchmarks: Dict with benchmarks (state_hospital_type, state, hospital_type, national)
        rank: KPI priority rank
        l2_kpis: Level 2 KPI values
        l3_kpis: Level 3 KPI values
        ccn: Provider number
        fiscal_year: Current fiscal year
    """
    meta = KPI_METADATA.get(kpi_key, {})
    kpi_name = meta.get('name', kpi_key)
    category = meta.get('category', 'General')
    description = meta.get('description', 'No description available')
    unit = meta.get('unit', '')
    fmt = meta.get('format', '.1f')
    higher_is_better = meta.get('higher_is_better', True)

    # Calculate 5-year trend
    trend_direction, trend_pct = calculate_trend(kpi_trend_values)

    # Create 5-year trend sparkline
    sparkline_fig = create_sparkline(kpi_trend_values, fiscal_years)

    # Trend indicator
    if higher_is_better:
        trend_color = 'success' if trend_direction == 'up' else ('danger' if trend_direction == 'down' else 'secondary')
        trend_icon = 'fa-arrow-up' if trend_direction == 'up' else ('fa-arrow-down' if trend_direction == 'down' else 'fa-minus')
    else:
        trend_color = 'danger' if trend_direction == 'up' else ('success' if trend_direction == 'down' else 'secondary')
        trend_icon = 'fa-arrow-down' if trend_direction == 'up' else ('fa-arrow-up' if trend_direction == 'down' else 'fa-minus')

    # Build benchmark comparison table for ALL levels
    # Order: State & Type (most specific), State, Hospital Type, National (broadest)
    benchmark_rows = []
    benchmark_levels = [
        ('state_hospital_type', 'Hospital Type and State', all_benchmarks.get('state_hospital_type')),
        ('state', 'Hospitals in State', all_benchmarks.get('state')),
        ('hospital_type', 'Hospital Type', all_benchmarks.get('hospital_type')),
        ('national', 'Hospital Nationwide', all_benchmarks.get('national'))
    ]

    for level_key, level_name, benchmark_data in benchmark_levels:
        if benchmark_data:
            # Use db_column if provided (benchmarks use database column names, not KPI metadata keys)
            bench_lookup_key = db_column if db_column else kpi_key
            kpi_bench = benchmark_data.get('kpis', {}).get(bench_lookup_key, {})
            p25 = kpi_bench.get('P25')
            median = kpi_bench.get('Median')
            p75 = kpi_bench.get('P75')
            peer_count = benchmark_data.get('provider_count', 0)

            # Determine performance vs this benchmark
            if median and kpi_value is not None and not pd.isna(kpi_value):
                perf_label, perf_color = calculate_percentile_rank(kpi_value, p25, median, p75)
                perf_badge = dbc.Badge(perf_label, color=perf_color, className="ms-2", style={'fontSize': '0.7rem'})
            else:
                perf_badge = dbc.Badge("N/A", color="secondary", className="ms-2", style={'fontSize': '0.7rem'})

            benchmark_rows.append(
                html.Tr([
                    html.Td([
                        html.Strong(level_name, style={'fontSize': '0.85rem'}),
                        html.Br(),
                        html.Small(f"{peer_count} peers", className="text-muted", style={'fontSize': '0.7rem'})
                    ]),
                    html.Td(f"{format(p25, fmt)}{unit}" if p25 else "—", style={'fontSize': '0.85rem', 'textAlign': 'center'}),
                    html.Td([
                        html.Strong(f"{format(median, fmt)}{unit}" if median else "—"),
                        perf_badge
                    ], style={'fontSize': '0.85rem', 'textAlign': 'center'}),
                    html.Td(f"{format(p75, fmt)}{unit}" if p75 else "—", style={'fontSize': '0.85rem', 'textAlign': 'center'}),
                ], style={'borderBottom': '1px solid #dee2e6'})
            )
        else:
            benchmark_rows.append(
                html.Tr([
                    html.Td(html.Strong(level_name, style={'fontSize': '0.85rem'})),
                    html.Td("—", colSpan=3, className="text-muted text-center", style={'fontSize': '0.85rem'})
                ], style={'borderBottom': '1px solid #dee2e6'})
            )

    benchmark_table = dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("Benchmark", style={'fontSize': '0.75rem', 'color': '#6c757d'}),
                html.Th("P25", style={'fontSize': '0.75rem', 'color': '#6c757d', 'textAlign': 'center'}),
                html.Th("Median", style={'fontSize': '0.75rem', 'color': '#6c757d', 'textAlign': 'center'}),
                html.Th("P75", style={'fontSize': '0.75rem', 'color': '#6c757d', 'textAlign': 'center'}),
            ])
        ]),
        html.Tbody(benchmark_rows)
    ], size="sm", borderless=True, className="mb-0")

    # Create card
    card = dbc.Card([
        # Header with rank, category, and drill-down button
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span(f"#{rank}", className="badge bg-primary me-2", style={'fontSize': '0.8rem'}),
                        html.Span(category, className="text-muted", style={'fontSize': '0.8rem'})
                    ])
                ], width=8),
                dbc.Col([
                    dcc.Link(
                        html.Button([
                            html.I(className="fas fa-chart-line me-1"),
                            "Drill Down"
                        ], className="btn btn-sm btn-outline-primary", style={'fontSize': '0.75rem'}),
                        href=f"/level2/{kpi_key}",
                        style={'textDecoration': 'none'}
                    )
                ], width=4, className="text-end")
            ])
        ], className="py-2", style={'background': '#f8f9fa', 'borderBottom': '2px solid #dee2e6'}),

        dbc.CardBody([
            # KPI Name
            html.H5(kpi_name, className="mb-2", style={'fontWeight': '600', 'color': '#212529'}),

            # Current Value with Trend
            html.Div([
                html.H2([
                    f"{format(kpi_value, fmt)}{unit}" if not pd.isna(kpi_value) else "N/A",
                    html.Span([
                        html.I(className=f"fas {trend_icon} ms-3"),
                        f" {abs(trend_pct):.1f}%"
                    ], className=f"text-{trend_color}", style={'fontSize': '1rem', 'fontWeight': 'normal'})
                ], className="mb-3", style={'fontWeight': '700', 'color': '#212529'}),
            ]),

            # Description
            html.P(description, className="text-muted mb-3", style={'fontSize': '0.9rem', 'lineHeight': '1.4'}),

            # 5-Year Trend Title
            html.H6("5-Year Trend", className="mb-2", style={'fontSize': '0.9rem', 'fontWeight': '600', 'color': '#495057'}),

            # Sparkline
            dcc.Graph(
                figure=sparkline_fig,
                config={'displayModeBar': False},
                style={'height': '60px', 'marginBottom': '1rem'}
            ),

            # Benchmark Comparison Title
            html.H6("Benchmark Comparison", className="mb-2", style={'fontSize': '0.9rem', 'fontWeight': '600', 'color': '#495057'}),

            # Benchmark Table
            benchmark_table,

        ], className="p-3")
    ], className="shadow-sm h-100", style={'border': '1px solid #dee2e6', 'borderRadius': '0.5rem'})

    return card


def create_hierarchical_kpi_card(kpi_key, kpi_value, kpi_trend_values, fiscal_years,
                                  benchmark_data, rank, importance_score, l2_kpis=None, l3_kpis=None, ccn=None, fiscal_year=None):
    """
    Create a hierarchical KPI card with expandable Level 2 and Level 3 drivers

    Args:
        kpi_key: Level 1 KPI identifier
        kpi_value: Current value
        kpi_trend_values: Historical values
        fiscal_years: Years for trend
        benchmark_data: Benchmark comparison data
        rank: KPI rank
        importance_score: Importance score
        l2_kpis: Dictionary of Level 2 KPI values (optional)
        l3_kpis: Dictionary of Level 3 KPI values (optional)
        ccn: Provider number for calculating L2/L3 KPIs on demand
        fiscal_year: Fiscal year for L2/L3 KPI calculation
    """
    meta = KPI_METADATA.get(kpi_key, {})
    kpi_name = meta.get('name', kpi_key)
    category = meta.get('category', 'General')
    unit = meta.get('unit', '')
    fmt = meta.get('format', '.1f')

    # L2 KPI metadata mapping with L3 sub-drivers (using KPI_METADATA keys, not DB columns)
    # Maps ALL 6 Level 1 KPIs from to_do.txt to their Level 2 drivers (with L3 sub-drivers where implemented)
    L2_KPI_INFO = {
        # L1 KPI 1: Net Income Margin
        'Net_Income_Margin': {
            'kpis': [
                {'key': 'L2_1_1_Operating_Expense_Ratio', 'name': 'Operating Expense Ratio', 'unit': '%', 'fmt': '.2f', 'l3_kpis': []},
                {
                    'key': 'L2_1_2_Non_Operating_Income_Pct', 'name': 'Non-Operating Income %', 'unit': '%', 'fmt': '.2f',
                    'l3_kpis': [
                        {'key': 'L3_1_2_1_Investment_Income_Share', 'name': 'Investment Income Share', 'unit': '%', 'fmt': '.2f'},
                        {'key': 'L3_1_2_2_Donation_Grant_Pct', 'name': 'Donation/Grant %', 'unit': '%', 'fmt': '.2f'},
                    ]
                },
                {
                    'key': 'L2_1_3_Payer_Mix_Medicare_Pct', 'name': 'Payer Mix - Medicare %', 'unit': '%', 'fmt': '.2f',
                    'l3_kpis': [
                        {'key': 'L3_1_3_1_Medicare_Inpatient_Days_Pct', 'name': 'Medicare Inpatient Days %', 'unit': '%', 'fmt': '.2f'},
                    ]
                },
                {
                    'key': 'L2_1_4_Capital_Cost_Pct_of_Expenses', 'name': 'Capital Cost % of Expenses', 'unit': '%', 'fmt': '.2f',
                    'l3_kpis': [
                        {'key': 'L3_1_4_1_Depreciation_Pct_of_Capital', 'name': 'Depreciation % of Capital', 'unit': '%', 'fmt': '.2f'},
                        {'key': 'L3_1_4_2_Interest_Expense_Ratio', 'name': 'Interest Expense Ratio', 'unit': '%', 'fmt': '.2f'},
                    ]
                },
            ]
        },
        # L1 KPI 2: Days in AR
        'AR_Days': {
            'kpis': [
                {'key': 'L2_2_1_Denial_Rate', 'name': 'Denial Rate', 'unit': '%', 'fmt': '.2f', 'l3_kpis': []},
                {
                    'key': 'L2_2_2_Payer_Mix_Commercial_Pct', 'name': 'Payer_Mix - Commercial %', 'unit': '%', 'fmt': '.2f',
                    'l3_kpis': [
                        {'key': 'L3_2_2_1_Commercial_Inpatient_Pct', 'name': 'Commercial Inpatient %', 'unit': '%', 'fmt': '.2f'},
                        {'key': 'L3_2_2_2_Self_Pay_Pct', 'name': 'Self-Pay %', 'unit': '%', 'fmt': '.2f'},
                    ]
                },
                {'key': 'L2_2_3_Billing_Efficiency_Ratio', 'name': 'Billing Efficiency Ratio', 'unit': 'ratio', 'fmt': '.2f', 'l3_kpis': []},
                {'key': 'L2_2_4_Collection_Rate', 'name': 'Collection Rate', 'unit': '%', 'fmt': '.2f', 'l3_kpis': []},
            ]
        },
        # L1 KPI 3: Operating Expense per Adjusted Discharge
        'Operating_Expense_per_Adjusted_Discharge': {
            'kpis': [
                {'key': 'L2_3_1_Labor_Cost_per_Discharge', 'name': 'Labor Cost per Discharge', 'unit': '$', 'fmt': '.2f', 'l3_kpis': []},
                {'key': 'L2_3_2_Supply_Cost_per_Discharge', 'name': 'Supply Cost per Discharge', 'unit': '$', 'fmt': '.2f', 'l3_kpis': []},
                {'key': 'L2_3_3_Overhead_Allocation_Ratio', 'name': 'Overhead Allocation Ratio', 'unit': '%', 'fmt': '.2f', 'l3_kpis': []},
                {'key': 'L2_3_4_Case_Mix_Index', 'name': 'Case Mix Index', 'unit': 'ratio', 'fmt': '.3f', 'l3_kpis': []},
            ]
        },
        # L1 KPI 4: Medicare CCR
        'Medicare_CCR': {
            'kpis': [
                {'key': 'L2_4_1_Ancillary_Cost_Ratio', 'name': 'Ancillary Cost Ratio', 'unit': '%', 'fmt': '.2f', 'l3_kpis': []},
                {'key': 'L2_4_2_Charge_Inflation_Rate', 'name': 'Charge Inflation Rate', 'unit': '%', 'fmt': '.2f', 'l3_kpis': []},
                {'key': 'L2_4_3_Adjustment_Impact', 'name': 'Adjustment Impact on Costs', 'unit': '%', 'fmt': '.2f', 'l3_kpis': []},
                {'key': 'L2_4_4_Utilization_Mix', 'name': 'Utilization Mix', 'unit': '%', 'fmt': '.2f', 'l3_kpis': []},
            ]
        },
        # L1 KPI 5: Bad Debt + Charity %
        'Bad_Debt_Charity_Pct': {
            'kpis': [
                {
                    'key': 'L2_5_1_Charity_Care_Charge_Ratio', 'name': 'Charity Care Charge Ratio', 'unit': '%', 'fmt': '.2f',
                    'l3_kpis': [
                        {'key': 'L3_5_1_1_Insured_Charity_Pct', 'name': 'Insured Charity %', 'unit': '%', 'fmt': '.2f'},
                        {'key': 'L3_5_1_2_Non_Covered_Charity_Pct', 'name': 'Non-Covered Charity %', 'unit': '%', 'fmt': '.2f'},
                    ]
                },
                {'key': 'L2_5_2_Bad_Debt_Recovery_Rate', 'name': 'Bad Debt Recovery Rate', 'unit': '%', 'fmt': '.2f', 'l3_kpis': []},
                {'key': 'L2_5_3_Uninsured_Patient_Pct', 'name': 'Uninsured Patient %', 'unit': '%', 'fmt': '.2f', 'l3_kpis': []},
                {
                    'key': 'L2_5_4_Medicaid_Shortfall_Pct', 'name': 'Medicaid Shortfall %', 'unit': '%', 'fmt': '.2f',
                    'l3_kpis': [
                        {'key': 'L3_5_4_1_Medicaid_Days_Pct', 'name': 'Medicaid Days %', 'unit': '%', 'fmt': '.2f'},
                        {'key': 'L3_5_4_2_Medicaid_Payment_to_Cost', 'name': 'Medicaid Payment-to-Cost', 'unit': '%', 'fmt': '.2f'},
                    ]
                },
            ]
        },
        # L1 KPI 6: Current Ratio
        'Current_Ratio': {
            'kpis': [
                {'key': 'L2_6_1_Cash_Pct_of_Assets', 'name': 'Cash + Equivalents % of Assets', 'unit': '%', 'fmt': '.2f', 'l3_kpis': []},
                {
                    'key': 'L2_6_2_Current_Liabilities_Ratio', 'name': 'Current Liabilities Ratio', 'unit': '%', 'fmt': '.2f',
                    'l3_kpis': [
                        {'key': 'L3_6_2_1_Accounts_Payable_Pct', 'name': 'Accounts Payable %', 'unit': '%', 'fmt': '.2f'},
                        {'key': 'L3_6_2_2_Short_Term_Debt_Pct', 'name': 'Short-Term Debt %', 'unit': '%', 'fmt': '.2f'},
                    ]
                },
                {'key': 'L2_6_3_Inventory_Turnover', 'name': 'Inventory Turnover', 'unit': 'ratio', 'fmt': '.2f', 'l3_kpis': []},
                {
                    'key': 'L2_6_4_Fund_Balance_Pct_Change', 'name': 'Fund Balance % Change', 'unit': '%', 'fmt': '.2f',
                    'l3_kpis': [
                        {'key': 'L3_6_4_1_Retained_Earnings_Pct', 'name': 'Retained Earnings %', 'unit': '%', 'fmt': '.2f'},
                        {'key': 'L3_6_4_2_Depreciation_Impact', 'name': 'Depreciation Impact', 'unit': '%', 'fmt': '.2f'},
                    ]
                },
            ]
        }
    }

    # Check if this KPI has L2 drivers
    has_l2_kpis = kpi_key in L2_KPI_INFO and l2_kpis is not None
    l2_info = L2_KPI_INFO.get(kpi_key, {})
    l2_kpi_list = l2_info.get('kpis', [])

    # Create basic card (same as create_kpi_card)
    benchmark_kpis = benchmark_data.get('kpis', {})
    kpi_benchmark = benchmark_kpis.get(kpi_key, {})
    p25 = kpi_benchmark.get('P25')
    median = kpi_benchmark.get('Median')
    p75 = kpi_benchmark.get('P75')
    mean = kpi_benchmark.get('Mean')

    perf_label, perf_color = calculate_percentile_rank(kpi_value, p25, median, p75)
    trend, trend_pct = calculate_trend(kpi_trend_values)

    # Trend icon
    trend_icon = {
        'up': 'fa-arrow-up',
        'down': 'fa-arrow-down',
        'stable': 'fa-minus'
    }.get(trend, 'fa-minus')

    trend_color = {
        'up': 'success',
        'down': 'danger',
        'stable': 'secondary'
    }.get(trend, 'secondary')

    # Build L2 KPI section with L3 drill-down
    l2_section = []
    if has_l2_kpis and l2_kpi_list:
        l2_cards = []
        for l2_idx, l2_meta in enumerate(l2_kpi_list):
            l2_key = l2_meta['key']
            l2_name = l2_meta['name']
            l2_unit = l2_meta['unit']
            l2_fmt = l2_meta['fmt']
            l2_value = l2_kpis.get(l2_key) if l2_kpis else None
            l3_kpi_list = l2_meta.get('l3_kpis', [])

            if l2_value is not None:
                l2_display = f"{l2_value:{l2_fmt}}{l2_unit}"
                l2_color = "light"
            else:
                l2_display = "N/A"
                l2_color = "secondary"

            # Build L3 KPI section for this L2 KPI
            l3_section = []
            has_l3_kpis = len(l3_kpi_list) > 0 and l3_kpis is not None

            if has_l3_kpis:
                l3_items = []
                for l3_meta in l3_kpi_list:
                    l3_key = l3_meta['key']
                    l3_name = l3_meta['name']
                    l3_unit = l3_meta['unit']
                    l3_fmt = l3_meta['fmt']
                    l3_value = l3_kpis.get(l3_key) if l3_kpis else None

                    if l3_value is not None:
                        l3_display = f"{l3_value:{l3_fmt}}{l3_unit}"
                    else:
                        l3_display = "N/A"

                    l3_items.append(
                        html.Div([
                            html.Small(l3_name, className="text-muted", style={'fontSize': '0.75rem'}),
                            html.Span(f": {l3_display}", className="fw-bold ms-1", style={'fontSize': '0.85rem'})
                        ], className="mb-1")
                    )

                # L3 collapse section with expand button
                l3_section = [
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-chevron-down me-1",
                                   id={'type': 'expand-l3-icon', 'index': f"{kpi_key}_{l2_key}"},
                                   style={'fontSize': '0.7rem'}),
                             html.Small("Sub-Drivers", style={'fontSize': '0.75rem'})],
                            id={'type': 'expand-l3-btn', 'index': f"{kpi_key}_{l2_key}"},
                            color="link",
                            size="sm",
                            className="p-0 text-decoration-none"
                        ),
                        dbc.Collapse([
                            html.Div(l3_items, className="mt-2 ps-2 border-start border-2 border-primary")
                        ], id={'type': 'l3-collapse', 'index': f"{kpi_key}_{l2_key}"}, is_open=False)
                    ], className="mt-2")
                ]

            # Create L2 card with optional L3 section
            l2_card_content = [
                html.Small(l2_name, className="text-muted d-block mb-1"),
                html.H6(l2_display, className="mb-0")
            ]

            if l3_section:
                l2_card_content.extend(l3_section)

            l2_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody(l2_card_content, className="py-2")
                    ], color=l2_color, outline=True, className="mb-2")
                ], width=12)
            )

        l2_section = [
            html.Hr(className="my-2"),
            dbc.Collapse([
                html.Div([
                    html.Small("KEY DRIVERS", className="text-muted fw-bold d-block mb-2"),
                    dbc.Row(l2_cards)
                ], className="p-2 bg-light rounded")
            ], id={'type': 'l2-collapse', 'index': kpi_key}, is_open=False)
        ]

    # Expand button (only if has L2 KPIs)
    expand_button = []
    if has_l2_kpis:
        expand_button = [
            html.Hr(),
            dbc.Button(
                [html.I(className="fas fa-chevron-down me-2", id={'type': 'expand-icon', 'index': kpi_key}),
                 "View Drivers"],
                id={'type': 'expand-btn', 'index': kpi_key},
                color="outline-secondary",
                size="sm",
                className="w-100"
            )
        ]

    card = dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.Span(f"#{rank}", className="badge bg-primary me-2"),
                html.Span(category, className="text-muted small")
            ], className="d-flex justify-content-between align-items-center")
        ]),
        dbc.CardBody([
            # KPI Name
            html.H6(kpi_name, className="card-title mb-3"),

            # KPI Value
            html.H3([
                f"{format(kpi_value, fmt)}{unit}" if not pd.isna(kpi_value) else "N/A",
                html.Span([
                    html.I(className=f"fas {trend_icon} ms-2"),
                    f" {abs(trend_pct):.1f}%"
                ], className=f"text-{trend_color} ms-2", style={'fontSize': '16px'})
            ], className="mb-2"),

            # Trend Sparkline
            html.Div([
                dcc.Graph(
                    figure=create_sparkline(kpi_trend_values, fiscal_years),
                    config={'displayModeBar': False},
                    style={'height': '50px'}
                )
            ], className="mt-2 mb-3"),

            # Benchmark Comparison
            html.Div([
                html.Hr(),
                html.Small("Benchmark Comparison", className="text-muted d-block mb-2"),
                html.Div([
                    html.Strong(f"Mean: {format(mean, fmt)}{unit}" if mean else "Mean: N/A",
                               className="text-primary me-3"),
                    dbc.Badge(perf_label if perf_label else "N/A", color=perf_color, className="me-2")
                ], className="mb-2"),
                dbc.Progress([
                    dbc.Progress(value=25, color="danger", bar=True),
                    dbc.Progress(value=25, color="warning", bar=True),
                    dbc.Progress(value=25, color="info", bar=True),
                    dbc.Progress(value=25, color="success", bar=True),
                ], className="mb-2", style={'height': '8px'}),
                dbc.Row([
                    dbc.Col(html.Small(f"P25: {format(p25, fmt)}{unit}" if p25 else "N/A"), width=4),
                    dbc.Col(html.Small(f"Median: {format(median, fmt)}{unit}" if median else "N/A"), width=4),
                    dbc.Col(html.Small(f"P75: {format(p75, fmt)}{unit}" if p75 else "N/A"), width=4)
                ])
            ]),

            # Level 2 KPIs (collapsible)
            *l2_section,

            # Expand button (if has L2)
            *expand_button
        ])
    ], className="shadow-sm mb-3", style={'height': '100%'})

    return card
