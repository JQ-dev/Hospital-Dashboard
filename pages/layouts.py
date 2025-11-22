"""
Page layouts for Hospital Dashboard

This module contains the layout functions for different pages in the dashboard.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc

from config.mappings import DB_COLUMN_TO_KPI_KEY
from components.kpi_cards import create_enhanced_level1_kpi_card
from kpi_hierarchy_config import KPI_HIERARCHY


def get_hospital_options(data_manager):
    """Get list of hospitals from parquet files for dropdown"""
    try:
        hospitals_df = data_manager.get_available_hospitals()
        print(f"Found {len(hospitals_df)} hospitals in parquet files")

        if hospitals_df.empty:
            print("No hospitals found, using default")
            return [{'label': '010001 - Default Hospital, State 01', 'value': '010001'}]

        options = []
        for _, row in hospitals_df.iterrows():
            provider_num = row['Provider_Number']
            ccn = str(int(provider_num)).zfill(6)
            state = str(int(row['State_Code'])).zfill(2)
            hosp_type = data_manager.classify_hospital_type(ccn)
            year_count = row.get('Year_Count', 'N/A')
            label = f"{ccn} - {hosp_type}, State {state} ({year_count} years)"
            options.append({'label': label, 'value': ccn})

        print(f"Generated {len(options)} dropdown options")
        return options
    except Exception as e:
        print(f"Error loading hospitals: {e}")
        return [{'label': '010001 - Default Hospital, State 01', 'value': '010001'}]


def get_main_dashboard_layout(hospital_options):
    """
    Main dashboard layout (Level 1 KPIs)

    Args:
        hospital_options: List of hospital dropdown options

    Returns:
        dbc.Container with the complete dashboard layout
    """
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1([
                    html.I(className="fas fa-hospital me-3"),
                    "Hospital Financial Analytics Dashboard"
                ], className="mt-4 mb-2"),
                html.P(
                    "Interactive performance dashboard with KPIs, benchmarks, and detailed financial statements",
                    className="lead text-muted mb-4"
                )
            ])
        ]),

    # Hospital Selection (shared across tabs)
    dbc.Row([
        dbc.Col([
            html.Label("Hospital Selection"),
            dcc.Dropdown(
                id='hospital-dropdown',
                options=hospital_options,
                value=hospital_options[0]['value'] if hospital_options else '310001',
                clearable=False
            )
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H6("Hospital", className="text-muted mb-1"),
                        html.H5(id='header-hospital-name', className="mb-0")
                    ], className="d-inline-block me-4"),
                    html.Div([
                        html.H6("Type", className="text-muted mb-1"),
                        html.H5(id='header-hospital-type', className="mb-0")
                    ], className="d-inline-block")
                ], className="d-flex justify-content-around")
            ], className="shadow-sm")
        ], width=6)
    ], className="mb-4"),

    # Tabs
    dbc.Tabs(id="main-tabs", active_tab="tab-kpi", children=[
        # KPI Dashboard Tab
        dbc.Tab(label="KPI Dashboard", tab_id="tab-kpi", children=[
            html.Div([
                # Summary Stats (Benchmark dropdown removed - all levels now shown on each card)
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Hospital", className="text-muted mb-1"),
                                html.H4(id='hospital-name', className="mb-0")
                            ])
                        ], className="shadow-sm")
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Type", className="text-muted mb-1"),
                                html.H4(id='hospital-type', className="mb-0")
                            ])
                        ], className="shadow-sm")
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Benchmark Group", className="text-muted mb-1"),
                                html.H4(id='benchmark-group', className="mb-0")
                            ])
                        ], className="shadow-sm")
                    ], width=3),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Peer Hospitals", className="text-muted mb-1"),
                                html.H4(id='peer-count', className="mb-0")
                            ])
                        ], className="shadow-sm")
                    ], width=3)
                ], className="mb-4"),

                # Sorting Controls
                dbc.Row([
                    dbc.Col([
                        html.Label("Sort KPIs by:", className="me-2"),
                        dbc.ButtonGroup([
                            dbc.Button("Priority (Dynamic)", id='sort-importance', color="primary", outline=False),
                            dbc.Button("Performance Gap", id='sort-performance', color="primary", outline=True),
                            dbc.Button("Trend Change", id='sort-trend', color="primary", outline=True),
                        ])
                    ], className="d-flex align-items-center")
                ], className="mb-3"),

                # KPI Cards Grid
                html.Div(id='kpi-cards-container'),
            ], className="mt-3")
        ]),

        # Financials Tab
        dbc.Tab(label="Financials", tab_id="tab-financials", children=[
            html.Div([
                html.H5("Multi-Year Financial Statements", className="mt-3 mb-3 text-primary"),
                html.P("All available fiscal years shown as columns (most recent on right)", className="text-muted mb-4"),

                # Financial Statements Sub-Tabs (lazy loading)
                dbc.Tabs(id="financial-subtabs", active_tab="subtab-balance-sheet", children=[
                    # Balance Sheet Sub-Tab
                    dbc.Tab(label="Balance Sheet", tab_id="subtab-balance-sheet", children=[
                        html.Div([
                            # Fund Type Filter
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Fund Type", className="fw-bold mb-2"),
                                    dcc.Dropdown(
                                        id='fund-type-dropdown',
                                        options=[
                                            {'label': 'General Fund', 'value': 'General Fund'},
                                            {'label': 'Specific Purpose Fund', 'value': 'Specific Purpose Fund'},
                                            {'label': 'Combined Total', 'value': 'Combined Total'},
                                            {'label': 'Medicaid Fund', 'value': 'Medicaid Fund'}
                                        ],
                                        value='General Fund',
                                        clearable=False
                                    )
                                ], width=4)
                            ], className="mt-3 mb-3"),
                            # Balance Sheet Content
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='balance-sheet-content')
                                ])
                            ])
                        ])
                    ]),

                    # Revenue Sub-Tab
                    dbc.Tab(label="Revenue Detail", tab_id="subtab-revenue", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='revenue-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Revenue & Expenses Sub-Tab
                    dbc.Tab(label="Revenue & Expenses", tab_id="subtab-revenue-expenses", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='revenue-expenses-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Cost Summary Sub-Tab (NEW - from B100)
                    dbc.Tab(label="Cost Summary", tab_id="subtab-cost-summary", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='cost-summary-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Detailed Costs Sub-Tab (Schedule A - Basic Table)
                    dbc.Tab(label="WORKSHEET A", tab_id="subtab-detailed-costs", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='detailed-costs-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='detailed-costs-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Worksheet B Sub-Tab (Schedule B-1 - Overhead Costs)
                    dbc.Tab(label="WORKSHEET B", tab_id="subtab-worksheet-b", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='worksheet-b-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='worksheet-b-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Worksheet G Sub-Tab (Balance Sheet)
                    dbc.Tab(label="WORKSHEET G", tab_id="subtab-worksheet-g", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='worksheet-g-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='worksheet-g-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Worksheet G-1 Sub-Tab (Fund Balance Changes)
                    dbc.Tab(label="WORKSHEET G-1", tab_id="subtab-worksheet-g1", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='worksheet-g1-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='worksheet-g1-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Worksheet G-2 Sub-Tab (Revenue)
                    dbc.Tab(label="WORKSHEET G-2", tab_id="subtab-worksheet-g2", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='worksheet-g2-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='worksheet-g2-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Worksheet G-3 Sub-Tab (Revenue & Expenses)
                    dbc.Tab(label="WORKSHEET G-3", tab_id="subtab-worksheet-g3", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Fiscal Year:", className="fw-bold"),
                                    dcc.Dropdown(
                                        id='worksheet-g3-year-dropdown',
                                        options=[],  # Will be populated by callback
                                        placeholder="Select a fiscal year",
                                        className="mb-3"
                                    )
                                ], width=3)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='worksheet-g3-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),

                    # Fund Balance Changes Sub-Tab
                    dbc.Tab(label="Fund Balance Changes", tab_id="subtab-fund-balance-changes", children=[
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    html.Div(id='fund-balance-changes-content')
                                ])
                            ], className="mt-3")
                        ])
                    ]),
                ])
            ], className="mt-3")
        ]),

        # CMS Worksheets Tab
        dbc.Tab(label="CMS Worksheets", tab_id="tab-cms-worksheets", children=[
            html.Div([
                # Dropdowns for Year, Hospital, and Worksheet selection
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Fiscal Year:", className="fw-bold"),
                        dcc.Dropdown(
                            id='cms-year-dropdown',
                            placeholder="Select fiscal year",
                            className="mb-3",
                            searchable=False
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label("Select Hospital:", className="fw-bold"),
                        dcc.Dropdown(
                            id='cms-hospital-dropdown',
                            placeholder="Type to search hospital...",
                            className="mb-3",
                            searchable=True
                        )
                    ], width=5),
                    dbc.Col([
                        html.Label("Select Worksheet:", className="fw-bold"),
                        dcc.Dropdown(
                            id='cms-worksheet-dropdown',
                            options=[
                                {'label': 'A000000 - General Service Cost Centers', 'value': 'A000000'},
                                {'label': 'A6000A0 - Reclassifications', 'value': 'A6000A0'},
                                {'label': 'A700001 - Reconciliation of Capital Costs Centers', 'value': 'A700001'},
                                {'label': 'A700002 - Reconciliation of Capital Costs Centers', 'value': 'A700002'},
                                {'label': 'A700003 - Reconciliation of Capital Costs Centers', 'value': 'A700003'},
                                {'label': 'A800000 - Adjustments to Expenses', 'value': 'A800000'},
                                {'label': 'A810000 - Costs Incurred - Related Organizations', 'value': 'A810000'},
                                {'label': 'A820010 - Provider-Based Physicians Adjustments', 'value': 'A820010'},
                                {'label': 'B000001 - Cost Allocation - General Service Costs', 'value': 'B000001'},
                                {'label': 'B000002 - Cost Allocation - General Service Costs', 'value': 'B000002'},
                                {'label': 'B100000 - Cost Allocation - General Service Costs', 'value': 'B100000'},
                                {'label': 'C000001 - Cost Allocation - General Service Costs', 'value': 'C000001'},
                                {'label': 'G000000 - Balance Sheet', 'value': 'G000000'},
                                {'label': 'G100000 - Statement of Changes in Fund Balances', 'value': 'G100000'},
                                {'label': 'G200000 - Statement of Patient Revenues', 'value': 'G200000'},
                                {'label': 'G300000 - Statement of Revenues', 'value': 'G300000'},
                                {'label': 'S000001 - Settlement Summary', 'value': 'S000001'},
                                {'label': 'S100001 - Hospital Uncompensated & Indigent Care Data', 'value': 'S100001'},
                                {'label': 'S200001 - Hospital & Healthcare Complex ID Data', 'value': 'S200001'},
                                {'label': 'S300001 - Statistical Data', 'value': 'S300001'},
                                {'label': 'S300002 - Statistical Data', 'value': 'S300002'},
                                {'label': 'S300004 - Hospital Wage Related Costs', 'value': 'S300004'},
                                {'label': 'S300005 - Hospital Wage Related Costs', 'value': 'S300005'},
                                {'label': 'S410000 - Hospital Wage Related Costs', 'value': 'S410000'},
                                {'label': 'S500000 - Hospital Renal Dialysis Department', 'value': 'S500000'},
                            ],
                            placeholder="Type to search worksheet...",
                            value='A000000',
                            className="mb-3",
                            searchable=True
                        )
                    ], width=5)
                ], className="mb-4"),

                dbc.Row([
                    dbc.Col([
                        html.Div(id='cms-worksheet-content', className="mt-4")
                    ])
                ])
            ], className="mt-3")
        ]),

        # Valuation Analysis Tab
        dbc.Tab(label="Valuation Analysis", tab_id="tab-valuation", children=[
            html.Div([
                html.H5("Interactive Hospital Valuation Dashboard", className="mt-3 mb-3 text-primary"),
                html.P("Analyze how changes in revenue, expenses, and margins affect hospital valuation", className="text-muted mb-4"),

                # Hospital and Year Selection for Valuation
                dbc.Row([
                    dbc.Col([
                        html.Label("Select Fiscal Year:", className="fw-bold"),
                        dcc.Dropdown(
                            id='valuation-year-dropdown',
                            placeholder="Select fiscal year",
                            className="mb-3"
                        )
                    ], width=3),
                    dbc.Col([
                        html.Button('Load Valuation Data', id='valuation-load-button', n_clicks=0,
                                    className="btn btn-primary mt-4")
                    ], width=3)
                ], className="mb-4"),

                # Store components for valuation data
                dcc.Store(id='valuation-income-data'),
                dcc.Store(id='valuation-expense-data'),
                dcc.Store(id='valuation-baseline-metrics'),

                # Valuation content area
                html.Div(id='valuation-content')
            ], className="mt-3")
        ])
    ]),

    # Modal for data table
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id='modal-title')),
        dbc.ModalBody(id='modal-body', style={'overflowX': 'auto'}),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
        ),
    ], id="data-modal", size="xl", is_open=False, scrollable=True),

        # Footer
        html.Hr(className="my-5"),
        html.Footer([
            html.P(id='footer-datasource', className="text-center text-muted")
        ])

    ], fluid=True, className="py-4")


def get_level2_page_layout(kpi_key, ccn, data_manager):
    """
    Level 2 drill-down page showing:
    - L1 KPI card at top left
    - Explanatory text at top right
    - Level 2 driver cards below

    Args:
        kpi_key: The Level 1 KPI key
        ccn: Hospital CCN
        data_manager: HospitalDataManager instance

    Returns:
        dbc.Container with the Level 2 page layout
    """

    # Ensure CCN is properly formatted as 6-digit string with leading zeros
    ccn_str = str(int(ccn)).zfill(6)

    # Get the Level 1 KPI metadata from hierarchy
    # KPI_HIERARCHY is imported at module level from kpi_hierarchy_config
    l1_hierarchy = KPI_HIERARCHY.get(kpi_key, {})
    kpi_name = l1_hierarchy.get('name', kpi_key)

    # Get L2 drivers from hierarchy (nested under 'level_2_kpis')
    l2_drivers_dict = l1_hierarchy.get('level_2_kpis', {})
    l2_driver_keys = list(l2_drivers_dict.keys())

    # Get KPI data for this provider
    kpi_data = data_manager.calculate_kpis(ccn_str)
    latest_year = kpi_data['Fiscal_Year'].max()
    latest_data = kpi_data[kpi_data['Fiscal_Year'] == latest_year].iloc[0]

    # Get all benchmarks for this provider
    all_benchmarks = {
        'state_hospital_type': data_manager.get_benchmarks(ccn_str, latest_year, 'State_Hospital_Type'),
        'state': data_manager.get_benchmarks(ccn_str, latest_year, 'State'),
        'hospital_type': data_manager.get_benchmarks(ccn_str, latest_year, 'Hospital_Type'),
        'national': data_manager.get_benchmarks(ccn_str, latest_year, 'National')
    }

    # Get database column name for the L1 KPI
    l1_db_column = None
    for db_col, meta_key in DB_COLUMN_TO_KPI_KEY.items():
        if meta_key == kpi_key:
            l1_db_column = db_col
            break

    # Get the value for the L1 KPI
    l1_value = latest_data.get(l1_db_column) if l1_db_column else None

    # Get trend data (last 5 years)
    trend_data = kpi_data[kpi_data['Fiscal_Year'] >= latest_year - 4]
    l1_trend_values = trend_data[l1_db_column].values if l1_db_column else []
    fiscal_years = trend_data['Fiscal_Year'].values

    # Create Level 1 card
    l1_card = create_enhanced_level1_kpi_card(
        kpi_key=kpi_key,
        kpi_value=l1_value,
        kpi_trend_values=l1_trend_values,
        fiscal_years=fiscal_years,
        all_benchmarks=all_benchmarks,
        rank=1,
        ccn=ccn,
        fiscal_year=latest_year,
        db_column=l1_db_column
    )

    # Create Level 2 driver cards
    l2_cards = []
    for i, driver_key in enumerate(l2_driver_keys, 1):
        # Get database column name for this L2 driver
        l2_db_column = None
        for db_col, meta_key in DB_COLUMN_TO_KPI_KEY.items():
            if meta_key == driver_key:
                l2_db_column = db_col
                break

        # Get the value for this L2 driver
        l2_value = latest_data.get(l2_db_column) if l2_db_column else None
        l2_trend_values = trend_data[l2_db_column].values if l2_db_column else []

        # Create L2 card
        l2_card = create_enhanced_level1_kpi_card(
            kpi_key=driver_key,
            kpi_value=l2_value,
            kpi_trend_values=l2_trend_values,
            fiscal_years=fiscal_years,
            all_benchmarks=all_benchmarks,
            rank=i,
            ccn=ccn,
            fiscal_year=latest_year,
            db_column=l2_db_column
        )
        l2_cards.append(dbc.Col(l2_card, width=12, lg=6, className="mb-4"))

    return dbc.Container([
        # Back button
        dbc.Row([
            dbc.Col([
                dcc.Link(
                    html.Button([
                        html.I(className="fas fa-arrow-left me-2"),
                        "Back to Dashboard"
                    ], className="btn btn-outline-secondary mt-3"),
                    href="/app/",
                    style={'textDecoration': 'none'}
                )
            ])
        ], className="mb-4"),

        # Header with L1 card on left, explanatory text on right
        dbc.Row([
            dbc.Col([
                l1_card
            ], width=12, lg=6, className="mb-4"),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Understanding the Drivers", className="card-title"),
                        html.P([
                            f"The {kpi_name} KPI is influenced by {len(l2_driver_keys)} key drivers shown below. ",
                            "Each driver card displays its own performance metrics and benchmarks, ",
                            "helping you understand which specific factors are affecting the overall metric."
                        ], className="text-muted"),
                        html.Hr(),
                        html.H6("How to Use This View:"),
                        html.Ul([
                            html.Li("Compare each driver's performance against benchmarks"),
                            html.Li("Identify which drivers are performing well or need improvement"),
                            html.Li("Use the trend data to see if drivers are improving over time"),
                            html.Li("Click on individual drivers to explore their sub-components (Level 3)")
                        ], className="text-muted small")
                    ])
                ], className="h-100 border-info")
            ], width=12, lg=6, className="mb-4")
        ]),

        # Level 2 driver cards
        html.H4(f"{kpi_name} Drivers", className="mb-3"),
        dbc.Row(l2_cards)

    ], fluid=True, className="py-4")
