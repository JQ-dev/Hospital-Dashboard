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

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://use.fontawesome.com/releases/v6.1.1/css/all.css'
    ],
    suppress_callback_exceptions=True,
    title="Hospital KPI Dashboard"
)

# ============================================================================
# LAYOUT
# ============================================================================

def get_authenticated_layout(user_info):
    """Layout for authenticated users"""
    from dashboard import app as dashboard_app

    # Get the main dashboard layout
    # For now, we'll show a placeholder - in production, integrate full dashboard
    return dbc.Container([
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

            # Quick stats
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5([html.I(className="fas fa-hospital me-2"), "Hospitals"], className="text-muted mb-2"),
                            html.H2("24", className="mb-0", style={'color': '#3498db'})
                        ])
                    ], className="shadow-sm mb-4")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5([html.I(className="fas fa-chart-line me-2"), "KPIs Tracked"], className="text-muted mb-2"),
                            html.H2("78", className="mb-0", style={'color': '#2ecc71'})
                        ])
                    ], className="shadow-sm mb-4")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5([html.I(className="fas fa-calendar me-2"), "Latest Data"], className="text-muted mb-2"),
                            html.H2("2023", className="mb-0", style={'color': '#e74c3c'})
                        ])
                    ], className="shadow-sm mb-4")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5([html.I(className="fas fa-users me-2"), "Team Members"], className="text-muted mb-2"),
                            html.H2(user_info.get('max_employees', '1'), className="mb-0", style={'color': '#f39c12'})
                        ])
                    ], className="shadow-sm mb-4")
                ], width=3)
            ]),

            # Getting started guide
            dbc.Card([
                dbc.CardHeader(html.H5([
                    html.I(className="fas fa-rocket me-2"),
                    "Getting Started"
                ], className="mb-0")),
                dbc.CardBody([
                    html.P("Welcome to the Hospital KPI Dashboard! Here's how to get started:", className="mb-3"),
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            html.I(className="fas fa-database me-2 text-primary"),
                            html.Strong("Step 1: "),
                            "Review the 78-KPI hierarchical structure (6 Level 1, 24 Level 2, 48 Level 3)"
                        ]),
                        dbc.ListGroupItem([
                            html.I(className="fas fa-hospital me-2 text-success"),
                            html.Strong("Step 2: "),
                            "Select hospitals to analyze from the available HCRIS data"
                        ]),
                        dbc.ListGroupItem([
                            html.I(className="fas fa-chart-bar me-2 text-info"),
                            html.Strong("Step 3: "),
                            "Explore KPI drill-downs from strategic metrics to granular sub-drivers"
                        ]),
                        dbc.ListGroupItem([
                            html.I(className="fas fa-users me-2 text-warning"),
                            html.Strong("Step 4: "),
                            "Compare against benchmarks (National, State, Hospital Type)"
                        ])
                    ], flush=True)
                ])
            ], className="shadow-sm mb-4"),

            # Dashboard integration note
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                html.Strong("Note: "),
                "Full dashboard integration is in progress. The complete KPI dashboard with ",
                "interactive visualizations will be available here soon. ",
                "For now, you can access the dashboard by running ",
                html.Code("python dashboard.py"),
                " separately."
            ], color="info")

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
    print("Access the dashboard at: http://127.0.0.1:8050")
    print("\nSupported account types:")
    print("  - Company (organizations with employees)")
    print("  - Employee (part of a company)")
    print("  - Individual (independent users)")
    print("\n" + "="*70 + "\n")

    app.run_server(debug=True, port=8050)
