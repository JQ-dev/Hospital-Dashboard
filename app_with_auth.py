"""
Hospital KPI Dashboard with Authentication

Secure, multi-user dashboard supporting:
- Company accounts (organizations with employees)
- Employee accounts (part of a company)
- Individual accounts (independent users)

Features:
- Secure password hashing (bcrypt)
- Session management
- Role-based access control
- User-friendly login/registration
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import flask
from flask import session as flask_session
import secrets

# Import authentication modules
from auth_manager import auth_manager
from auth_components import (
    create_login_layout,
    create_register_layout,
    create_company_register_form,
    create_employee_register_form,
    create_individual_register_form,
    create_user_menu
)

# Initialize Flask server
server = flask.Flask(__name__)
server.secret_key = secrets.token_hex(32)  # Secret key for Flask sessions

# ============================================================================
# FLASK ROUTES FOR LANDING PAGE
# ============================================================================

@server.route('/')
def landing_page():
    """Serve the static landing page at root"""
    return flask.send_file('index.html')

@server.route('/styles.css')
def styles():
    """Serve the CSS file for landing page"""
    return flask.send_file('styles.css')

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    server=server,
    url_base_pathname='/app/',  # Dash app runs at /app/
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://use.fontawesome.com/releases/v6.1.1/css/all.css'
    ],
    suppress_callback_exceptions=True,
    title="Hospital KPI Dashboard"
)

# ============================================================================
# DATA MANAGER INITIALIZATION (from dashboard.py)
# ============================================================================

# Import dashboard components
from dashboard import HospitalDataManager

# Initialize data manager at module level (same as dashboard.py)
data_manager = HospitalDataManager()

# Get available hospitals dynamically (same as dashboard.py)
def get_hospital_options():
    """Get list of hospitals from parquet files for dropdown"""
    try:
        hospitals_df = data_manager.get_available_hospitals()
        print(f"[AUTH-APP] Found {len(hospitals_df)} hospitals in parquet files")

        if hospitals_df.empty:
            print("[AUTH-APP] No hospitals found, using default")
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

        print(f"[AUTH-APP] Loaded {len(options)} hospitals total")
        return options
    except Exception as e:
        print(f"[AUTH-APP] Error loading hospitals: {e}")
        import traceback
        traceback.print_exc()
        return [{'label': '010001 - Default Hospital, State 01', 'value': '010001'}]

print("[AUTH-APP] Loading hospitals from parquet files...")
hospital_options = get_hospital_options()
print(f"[AUTH-APP] Hospital options ready: {len(hospital_options)} hospitals")

# ============================================================================
# LAYOUT
# ============================================================================

def get_authenticated_layout(user_info):
    """Layout for authenticated users"""
    return dbc.Container([
        # Welcome Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-info-circle me-2"),
                "Welcome to Hospital KPI Dashboard"
            ])),
            dbc.ModalBody([
                html.H5("Your Comprehensive Healthcare Analytics Platform"),
                html.P("This dashboard provides real-time insights into hospital financial performance using 78 hierarchical KPIs."),
                html.Hr(),
                html.H6("Key Features:"),
                dbc.ListGroup([
                    dbc.ListGroupItem([
                        html.I(className="fas fa-chart-line me-2 text-primary"),
                        html.Strong("3-Level KPI Hierarchy: "),
                        "6 Strategic → 24 Driver → 48 Sub-driver metrics"
                    ]),
                    dbc.ListGroupItem([
                        html.I(className="fas fa-balance-scale me-2 text-success"),
                        html.Strong("Benchmark Comparisons: "),
                        "Compare against National, State, and Hospital Type peers"
                    ]),
                    dbc.ListGroupItem([
                        html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
                        html.Strong("Priority Ranking: "),
                        "KPIs automatically ranked by performance gap and importance"
                    ]),
                    dbc.ListGroupItem([
                        html.I(className="fas fa-chart-area me-2 text-info"),
                        html.Strong("Trend Analysis: "),
                        "Multi-year performance tracking with sparklines"
                    ])
                ], flush=True, className="mb-3"),
                html.P("All KPIs are displayed below, ranked by priority. Use the sorting controls to view by performance gap or trend changes.",
                       className="text-muted mb-0")
            ]),
            dbc.ModalFooter(
                dbc.Button("Get Started", id="close-welcome-modal", color="primary")
            ),
        ], id="welcome-modal", size="lg", is_open=True),

        # Main content
        dbc.Container([
        # Top navigation bar
        dbc.Navbar(
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.A(
                            dbc.Row([
                                dbc.Col(html.I(className="fas fa-hospital-alt", style={'fontSize': '28px'})),
                                dbc.Col(dbc.NavbarBrand("Hospital KPI Dashboard", className="ms-2")),
                            ], align="center", className="g-0"),
                            href="/",
                            style={"textDecoration": "none"}
                        )
                    ], width="auto"),
                    dbc.Col([
                        dbc.Nav([
                            dbc.NavItem(dbc.NavLink("Dashboard", href="/", active=True)),
                            dbc.NavItem(dbc.NavLink("Analytics", href="/analytics")),
                            dbc.NavItem(dbc.NavLink("Reports", href="/reports")),
                            dbc.NavItem(create_user_menu(user_info))
                        ], navbar=True, className="ms-auto")
                    ])
                ], className="w-100", align="center")
            ], fluid=True),
            color="dark",
            dark=True,
            className="mb-4"
        ),

        # Main content area
        dbc.Container([
            # Welcome message
            dbc.Alert([
                html.H4([
                    html.I(className="fas fa-check-circle me-2"),
                    f"Welcome, {user_info['display_name']}!"
                ], className="alert-heading"),
                html.P([
                    f"You are logged in as a {user_info['user_type']} user. ",
                    html.Br(),
                    f"Email: {user_info['email']}"
                ])
            ], color="success", className="mb-4"),

            # Hospital Selector and Benchmark Controls
            dbc.Row([
                dbc.Col([
                    html.H4("Select Hospital", className="mb-3"),
                    dcc.Dropdown(
                        id='auth-hospital-dropdown',
                        options=hospital_options,
                        value=hospital_options[0]['value'] if hospital_options else None,
                        placeholder="Select a hospital...",
                        className="mb-4"
                    )
                ], width=6),
                dbc.Col([
                    html.H4("Benchmark Level", className="mb-3"),
                    dcc.Dropdown(
                        id='auth-benchmark-dropdown',
                        options=[
                            {'label': 'National - All Hospitals', 'value': 'National'},
                            {'label': 'State - Same State', 'value': 'State'},
                            {'label': 'Hospital Type - Same Type', 'value': 'Hospital_Type'},
                            {'label': 'State + Type - Most Specific', 'value': 'State_Hospital_Type'}
                        ],
                        value='State',
                        className="mb-4"
                    )
                ], width=6)
            ]),

            # Summary Stats
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Hospital", className="text-muted mb-1"),
                            html.H4(id='auth-hospital-name', children="Select a hospital", className="mb-0")
                        ])
                    ], className="shadow-sm")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Type", className="text-muted mb-1"),
                            html.H4(id='auth-hospital-type', children="N/A", className="mb-0")
                        ])
                    ], className="shadow-sm")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Benchmark Group", className="text-muted mb-1"),
                            html.H4(id='auth-benchmark-group', children="N/A", className="mb-0")
                        ])
                    ], className="shadow-sm")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Peer Hospitals", className="text-muted mb-1"),
                            html.H4(id='auth-peer-count', children="N/A", className="mb-0")
                        ])
                    ], className="shadow-sm")
                ], width=3)
            ], className="mb-4"),

            # Sorting Controls
            dbc.Row([
                dbc.Col([
                    html.Label("Sort KPIs by:", className="me-2"),
                    dbc.ButtonGroup([
                        dbc.Button("Priority (Dynamic)", id='auth-sort-importance', color="primary", outline=False),
                        dbc.Button("Performance Gap", id='auth-sort-performance', color="primary", outline=True),
                        dbc.Button("Trend Change", id='auth-sort-trend', color="primary", outline=True),
                    ])
                ], className="d-flex align-items-center")
            ], className="mb-3"),

            # All KPI Cards
            html.Div(id='auth-kpi-cards-container', children=[
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "Select a hospital above to view KPI analysis"
                ], color="info")
            ])

        ], fluid=True)
        ], fluid=True)
    ], fluid=True)


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    html.Div(id='page-content')
])


# ============================================================================
# ROUTING CALLBACKS
# ============================================================================

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('session-store', 'data')
)
def display_page(pathname, session_data):
    """Route to appropriate page based on authentication status"""

    # Check if user is authenticated
    if session_data and session_data.get('session_id'):
        session_id = session_data['session_id']
        user_dict, user_type = auth_manager.get_user_from_session(session_id)

        if user_dict and user_type:
            # User is authenticated
            user_info = auth_manager.get_user_info(user_type, user_dict)

            if pathname == '/register':
                # Redirect authenticated users from register page
                return get_authenticated_layout(user_info)
            else:
                return get_authenticated_layout(user_info)

    # User not authenticated - show login or register
    if pathname == '/register':
        return create_register_layout()
    else:
        return create_login_layout()


# ============================================================================
# REGISTRATION FORM CALLBACKS
# ============================================================================

@app.callback(
    Output('register-form-container', 'children'),
    Input('register-account-type', 'value')
)
def update_register_form(account_type):
    """Update registration form based on selected account type"""
    if account_type == 'company':
        return create_company_register_form()
    elif account_type == 'employee':
        return create_employee_register_form()
    else:  # individual
        return create_individual_register_form()


# ============================================================================
# LOGIN CALLBACK
# ============================================================================

@app.callback(
    [Output('login-alert', 'children'),
     Output('session-store', 'data'),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('login-button', 'n_clicks'),
     Input('login-password', 'n_submit')],
    [State('login-email', 'value'),
     State('login-password', 'value'),
     State('session-store', 'data')],
    prevent_initial_call=True
)
def handle_login(n_clicks, n_submit, email, password, current_session):
    """Handle login form submission"""
    if not n_clicks and not n_submit:
        return dash.no_update, dash.no_update, dash.no_update

    # Validate inputs
    if not email or not password:
        alert = dbc.Alert("Please enter both email and password", color="warning")
        return alert, dash.no_update, dash.no_update

    # Authenticate user
    success, user_type, user_dict, message = auth_manager.authenticate(email, password)

    if success:
        # Create session
        session_id = auth_manager.create_session(user_type, user_dict)

        # Store session
        session_data = {
            'session_id': session_id,
            'user_type': user_type
        }

        alert = dbc.Alert(
            [html.I(className="fas fa-check-circle me-2"), message],
            color="success"
        )

        return alert, session_data, '/'
    else:
        alert = dbc.Alert(
            [html.I(className="fas fa-exclamation-triangle me-2"), message],
            color="danger"
        )
        return alert, dash.no_update, dash.no_update


# ============================================================================
# COMPANY REGISTRATION CALLBACK
# ============================================================================

@app.callback(
    Output('register-alert', 'children'),
    Input('register-company-button', 'n_clicks'),
    [State('reg-company-name', 'value'),
     State('reg-company-email', 'value'),
     State('reg-company-phone', 'value'),
     State('reg-company-address', 'value'),
     State('reg-admin-name', 'value'),
     State('reg-admin-email', 'value'),
     State('reg-company-password', 'value'),
     State('reg-company-password-confirm', 'value'),
     State('reg-company-terms', 'value')],
    prevent_initial_call=True
)
def handle_company_registration(n_clicks, company_name, company_email, phone, address,
                                 admin_name, admin_email, password, password_confirm, terms):
    """Handle company registration"""
    if not n_clicks:
        return dash.no_update

    # Validate required fields
    if not all([company_name, company_email, admin_name, admin_email, password]):
        return dbc.Alert("Please fill in all required fields (*)", color="warning")

    # Validate terms acceptance
    if not terms:
        return dbc.Alert("You must agree to the Terms of Service", color="warning")

    # Validate password match
    if password != password_confirm:
        return dbc.Alert("Passwords do not match", color="warning")

    # Prepare company data
    company_data = {
        'company_name': company_name.strip(),
        'company_email': company_email.strip().lower(),
        'admin_name': admin_name.strip(),
        'admin_email': admin_email.strip().lower(),
        'phone': phone.strip() if phone else None,
        'address': address.strip() if address else None
    }

    # Register company
    success, company_id, message = auth_manager.register_company(company_data, password)

    if success:
        return dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            html.Strong("Success! "),
            f"{message} You can now ",
            html.A("sign in", href="/", className="alert-link"),
            f". Your Company ID is: {company_id}"
        ], color="success")
    else:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            message
        ], color="danger")


# ============================================================================
# EMPLOYEE REGISTRATION CALLBACK
# ============================================================================

@app.callback(
    Output('register-alert', 'children', allow_duplicate=True),
    Input('register-employee-button', 'n_clicks'),
    [State('reg-employee-company-id', 'value'),
     State('reg-employee-first-name', 'value'),
     State('reg-employee-last-name', 'value'),
     State('reg-employee-email', 'value'),
     State('reg-employee-role', 'value'),
     State('reg-employee-department', 'value'),
     State('reg-employee-password', 'value'),
     State('reg-employee-password-confirm', 'value'),
     State('reg-employee-terms', 'value')],
    prevent_initial_call=True
)
def handle_employee_registration(n_clicks, company_id, first_name, last_name, email,
                                  role, department, password, password_confirm, terms):
    """Handle employee registration"""
    if not n_clicks:
        return dash.no_update

    # Validate required fields
    if not all([company_id, first_name, last_name, email, password]):
        return dbc.Alert("Please fill in all required fields (*)", color="warning")

    # Validate terms acceptance
    if not terms:
        return dbc.Alert("You must agree to the Terms of Service", color="warning")

    # Validate password match
    if password != password_confirm:
        return dbc.Alert("Passwords do not match", color="warning")

    # Prepare employee data
    employee_data = {
        'company_id': int(company_id),
        'first_name': first_name.strip(),
        'last_name': last_name.strip(),
        'email': email.strip().lower(),
        'role': role,
        'department': department.strip() if department else None
    }

    # Register employee
    success, employee_id, message = auth_manager.register_employee(employee_data, password)

    if success:
        return dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            html.Strong("Success! "),
            f"{message} You can now ",
            html.A("sign in", href="/", className="alert-link"),
            "."
        ], color="success")
    else:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            message
        ], color="danger")


# ============================================================================
# INDIVIDUAL REGISTRATION CALLBACK
# ============================================================================

@app.callback(
    Output('register-alert', 'children', allow_duplicate=True),
    Input('register-individual-button', 'n_clicks'),
    [State('reg-individual-first-name', 'value'),
     State('reg-individual-last-name', 'value'),
     State('reg-individual-email', 'value'),
     State('reg-individual-organization', 'value'),
     State('reg-individual-phone', 'value'),
     State('reg-individual-password', 'value'),
     State('reg-individual-password-confirm', 'value'),
     State('reg-individual-terms', 'value')],
    prevent_initial_call=True
)
def handle_individual_registration(n_clicks, first_name, last_name, email,
                                    organization, phone, password, password_confirm, terms):
    """Handle individual registration"""
    if not n_clicks:
        return dash.no_update

    # Validate required fields
    if not all([first_name, last_name, email, password]):
        return dbc.Alert("Please fill in all required fields (*)", color="warning")

    # Validate terms acceptance
    if not terms:
        return dbc.Alert("You must agree to the Terms of Service", color="warning")

    # Validate password match
    if password != password_confirm:
        return dbc.Alert("Passwords do not match", color="warning")

    # Prepare individual data
    individual_data = {
        'first_name': first_name.strip(),
        'last_name': last_name.strip(),
        'email': email.strip().lower(),
        'organization': organization.strip() if organization else None,
        'phone': phone.strip() if phone else None
    }

    # Register individual
    success, individual_id, message = auth_manager.register_individual(individual_data, password)

    if success:
        return dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            html.Strong("Success! "),
            f"{message} You can now ",
            html.A("sign in", href="/", className="alert-link"),
            "."
        ], color="success")
    else:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            message
        ], color="danger")


# ============================================================================
# LOGOUT CALLBACK
# ============================================================================

@app.callback(
    [Output('session-store', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    Input('logout-button', 'n_clicks'),
    State('session-store', 'data'),
    prevent_initial_call=True
)
def handle_logout(n_clicks, session_data):
    """Handle logout"""
    if not n_clicks:
        return dash.no_update, dash.no_update

    if session_data and session_data.get('session_id'):
        auth_manager.delete_session(session_data['session_id'])

    return {}, '/'


# ============================================================================
# NAVIGATION CALLBACKS
# ============================================================================

@app.callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input('show-register-link', 'n_clicks'),
     Input('show-login-link', 'n_clicks'),
     Input('show-login-link-employee', 'n_clicks'),
     Input('show-login-link-individual', 'n_clicks')],
    prevent_initial_call=True
)
def navigate(register_clicks, login_clicks, login_employee_clicks, login_individual_clicks):
    """Handle navigation between login and register pages"""
    ctx = callback_context

    print(f"[NAVIGATION] Callback triggered! ctx.triggered: {ctx.triggered}")
    print(f"[NAVIGATION] Clicks - register: {register_clicks}, login: {login_clicks}, employee: {login_employee_clicks}, individual: {login_individual_clicks}")

    # More robust check for triggered component
    if not ctx.triggered or not ctx.triggered[0]:
        print("[NAVIGATION] No trigger detected, returning no_update")
        return dash.no_update

    # Get the ID of the component that triggered the callback
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"[NAVIGATION] Triggered ID: {triggered_id}")

    # Route based on which link was clicked
    if triggered_id == 'show-register-link':
        print("[NAVIGATION] Navigating to /register")
        return '/register'
    elif triggered_id in ['show-login-link', 'show-login-link-employee', 'show-login-link-individual']:
        print("[NAVIGATION] Navigating to /")
        return '/'

    print("[NAVIGATION] No match, returning no_update")
    return dash.no_update


# ============================================================================
# DASHBOARD INTEGRATION CALLBACKS
# ============================================================================

@app.callback(
    Output('welcome-modal', 'is_open'),
    Input('close-welcome-modal', 'n_clicks'),
    prevent_initial_call=True
)
def close_welcome(n_clicks):
    """Close welcome modal"""
    return False


@app.callback(
    [Output('auth-hospital-name', 'children'),
     Output('auth-hospital-type', 'children'),
     Output('auth-benchmark-group', 'children'),
     Output('auth-peer-count', 'children'),
     Output('auth-kpi-cards-container', 'children')],
    [Input('auth-hospital-dropdown', 'value'),
     Input('auth-benchmark-dropdown', 'value'),
     Input('auth-sort-importance', 'n_clicks'),
     Input('auth-sort-performance', 'n_clicks'),
     Input('auth-sort-trend', 'n_clicks')],
    prevent_initial_call=True
)
def load_all_kpis(ccn, benchmark_level, sort_imp, sort_perf, sort_trend):
    """Load all KPIs for selected hospital with sorting"""
    if not ccn:
        return "Select a hospital", "N/A", "N/A", "N/A", dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "Select a hospital above to view KPI analysis"
        ], color="info")

    try:
        # Import KPI functions from dashboard (data_manager already initialized at module level)
        from dashboard import (
            create_kpi_card,
            calculate_dynamic_priority,
            calculate_trend
        )
        from kpi_hierarchy_config import KPI_METADATA
        import pandas as pd

        # Get hospital metadata
        hospital_type = data_manager.classify_hospital_type(ccn)
        state_code = str(ccn)[:2]

        # Get KPI data
        kpi_data = data_manager.calculate_kpis(ccn)

        if kpi_data.empty:
            return f"CCN {ccn}", "N/A", "N/A", "N/A", dbc.Alert("No data available for this hospital", color="warning")

        latest_year = kpi_data['Fiscal_Year'].max()

        # Get benchmarks
        print(f"[AUTH-DASHBOARD] Calculating benchmarks for {ccn} at {benchmark_level} level...")
        benchmark_data = data_manager.get_benchmarks(ccn, latest_year, benchmark_level)
        print(f"[AUTH-DASHBOARD] Benchmarks calculated: {benchmark_data.get('provider_count', 0)} peers")

        # Rank KPIs by priority
        kpi_rankings = []
        for kpi_key in KPI_METADATA.keys():
            if kpi_key not in kpi_data.columns:
                continue

            kpi_meta = KPI_METADATA.get(kpi_key, {})
            higher_is_better = kpi_meta.get('higher_is_better', True)

            kpi_values = kpi_data[kpi_key].values
            kpi_value = kpi_values[0] if len(kpi_values) > 0 else None

            benchmark_kpis = benchmark_data.get('kpis', {})
            kpi_benchmark = benchmark_kpis.get(kpi_key, {})
            median = kpi_benchmark.get('Median')

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
                'dynamic_priority': dynamic_priority,
                'perf_gap': abs(perf_gap),
                'trend_pct': abs(trend_pct),
                'kpi_value': kpi_value,
                'kpi_values': kpi_values
            })

        # Determine sort order
        ctx = dash.callback_context
        if ctx.triggered:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if button_id == 'auth-sort-performance':
                kpi_rankings.sort(key=lambda x: x['perf_gap'], reverse=True)
            elif button_id == 'auth-sort-trend':
                kpi_rankings.sort(key=lambda x: x['trend_pct'], reverse=True)
            else:
                kpi_rankings.sort(key=lambda x: x['dynamic_priority'], reverse=True)
        else:
            kpi_rankings.sort(key=lambda x: x['dynamic_priority'], reverse=True)

        # Create all cards
        kpi_cards = []
        for idx, ranking in enumerate(kpi_rankings):
            card = create_kpi_card(
                kpi_key=ranking['kpi_key'],
                kpi_value=ranking['kpi_value'],
                kpi_trend_values=ranking['kpi_values'],
                fiscal_years=kpi_data['Fiscal_Year'].values,
                benchmark_data=benchmark_data,
                rank=idx + 1,
                importance_score=ranking['dynamic_priority']
            )
            kpi_cards.append(dbc.Col(card, width=12, lg=6, xl=4))

        cards_grid = dbc.Row(kpi_cards)

        return (
            f"CCN {ccn}",
            hospital_type,
            benchmark_data.get('group_name', 'N/A'),
            f"{benchmark_data.get('provider_count', 0):,}",
            cards_grid
        )

    except Exception as e:
        print(f"Error loading KPIs: {e}")
        import traceback
        traceback.print_exc()
        return f"CCN {ccn}", "Error", "Error", "0", dbc.Alert(f"Error loading KPI data: {str(e)}", color="danger")


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == '__main__':
    # Cleanup expired sessions on startup
    cleaned = auth_manager.cleanup_expired_sessions()
    if cleaned > 0:
        print(f"Cleaned up {cleaned} expired sessions")

    print("\n" + "="*70)
    print("Hospital KPI Dashboard with Authentication")
    print("="*70)
    print("\nServer starting...")
    print("Landing Page: http://127.0.0.1:8050")
    print("Dashboard App: http://127.0.0.1:8050/app")
    print("\nSupported account types:")
    print("  - Company (organizations with employees)")
    print("  - Employee (part of a company)")
    print("  - Individual (independent users)")
    print("\n" + "="*70 + "\n")

    app.run_server(debug=True, port=8050)
