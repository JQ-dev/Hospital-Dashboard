"""
Authentication UI Components for Dash

Provides user-friendly login and registration interfaces
"""

import dash_bootstrap_components as dbc
from dash import html, dcc


def create_login_layout():
    """Create the login page layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    # Header
                    html.Div([
                        html.I(className="fas fa-hospital-alt", style={
                            'fontSize': '48px',
                            'color': '#2c3e50',
                            'marginBottom': '20px'
                        }),
                        html.H2("Hospital KPI Dashboard", className="text-center mb-1",
                               style={'color': '#2c3e50', 'fontWeight': '600'}),
                        html.P("Sign in to access your analytics", className="text-center text-muted mb-4")
                    ], className="text-center mb-4"),

                    # Login Card
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Sign In", className="card-title text-center mb-4",
                                   style={'color': '#34495e', 'fontWeight': '600'}),

                            # Alert for messages
                            html.Div(id='login-alert', children=[]),

                            # Email input
                            dbc.Label("Email Address", html_for="login-email", className="fw-bold"),
                            dbc.Input(
                                id="login-email",
                                type="email",
                                placeholder="you@example.com",
                                className="mb-3",
                                style={'fontSize': '15px'}
                            ),

                            # Password input
                            dbc.Label("Password", html_for="login-password", className="fw-bold"),
                            dbc.Input(
                                id="login-password",
                                type="password",
                                placeholder="Enter your password",
                                className="mb-3",
                                style={'fontSize': '15px'},
                                n_submit=0
                            ),

                            # Remember me checkbox
                            dbc.Checkbox(
                                id="login-remember",
                                label="Remember me",
                                className="mb-3"
                            ),

                            # Login button
                            dbc.Button(
                                "Sign In",
                                id="login-button",
                                color="success",
                                className="w-100 mb-3",
                                size="lg",
                                style={'fontWeight': '500'}
                            ),

                            html.Hr(),

                            # Register link
                            html.Div([
                                html.Span("Don't have an account? ", style={'marginRight': '5px'}),
                                dbc.Button("Sign up here", id="show-register-link",
                                      color="link", size="sm", n_clicks=0,
                                      style={'fontWeight': '600', 'padding': '0', 'textDecoration': 'none'})
                            ], className="text-center mb-0")
                        ])
                    ], className="shadow-sm", style={'borderRadius': '12px'}),

                    # Features section
                    html.Div([
                        html.H6("Trusted by Healthcare Professionals", className="text-center mt-4 mb-3 text-muted"),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-shield-alt",
                                          style={'fontSize': '24px', 'color': '#3498db'}),
                                    html.P("Secure & Compliant", className="mt-2 mb-0",
                                          style={'fontSize': '13px', 'fontWeight': '500'})
                                ], className="text-center")
                            ], width=4),
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-chart-line",
                                          style={'fontSize': '24px', 'color': '#2ecc71'}),
                                    html.P("Real-time Analytics", className="mt-2 mb-0",
                                          style={'fontSize': '13px', 'fontWeight': '500'})
                                ], className="text-center")
                            ], width=4),
                            dbc.Col([
                                html.Div([
                                    html.I(className="fas fa-users",
                                          style={'fontSize': '24px', 'color': '#e74c3c'}),
                                    html.P("Team Collaboration", className="mt-2 mb-0",
                                          style={'fontSize': '13px', 'fontWeight': '500'})
                                ], className="text-center")
                            ], width=4)
                        ])
                    ])
                ], style={
                    'maxWidth': '480px',
                    'margin': '0 auto',
                    'padding': '40px 20px'
                })
            ], width=12)
        ], justify="center")
    ], fluid=True, style={'minHeight': '100vh', 'backgroundColor': '#f8f9fa', 'paddingTop': '60px'})


def create_register_layout():
    """Create the registration page layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    # Header
                    html.Div([
                        html.I(className="fas fa-hospital-alt", style={
                            'fontSize': '48px',
                            'color': '#2c3e50',
                            'marginBottom': '20px'
                        }),
                        html.H2("Create Your Account", className="text-center mb-1",
                               style={'color': '#2c3e50', 'fontWeight': '600'}),
                        html.P("Choose your account type to get started", className="text-center text-muted mb-4")
                    ], className="text-center mb-4"),

                    # Account type selector
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Select Account Type", className="mb-3",
                                   style={'color': '#34495e', 'fontWeight': '600'}),

                            dbc.RadioItems(
                                id="register-account-type",
                                options=[
                                    {
                                        'label': html.Div([
                                            html.I(className="fas fa-building me-2"),
                                            html.Strong("Company Account"),
                                            html.Br(),
                                            html.Small("For organizations with multiple team members",
                                                      className="text-muted")
                                        ], className="p-2"),
                                        'value': 'company'
                                    },
                                    {
                                        'label': html.Div([
                                            html.I(className="fas fa-user-tie me-2"),
                                            html.Strong("Employee Account"),
                                            html.Br(),
                                            html.Small("Join your organization's team",
                                                      className="text-muted")
                                        ], className="p-2"),
                                        'value': 'employee'
                                    },
                                    {
                                        'label': html.Div([
                                            html.I(className="fas fa-user me-2"),
                                            html.Strong("Individual Account"),
                                            html.Br(),
                                            html.Small("For independent healthcare professionals",
                                                      className="text-muted")
                                        ], className="p-2"),
                                        'value': 'individual'
                                    }
                                ],
                                value='individual',
                                className="mb-0"
                            )
                        ])
                    ], className="shadow-sm mb-4", style={'borderRadius': '12px'}),

                    # Alert for messages
                    html.Div(id='register-alert', children=[]),

                    # Dynamic registration form
                    html.Div(id='register-form-container')

                ], style={
                    'maxWidth': '600px',
                    'margin': '0 auto',
                    'padding': '40px 20px'
                })
            ], width=12)
        ], justify="center")
    ], fluid=True, style={'minHeight': '100vh', 'backgroundColor': '#f8f9fa', 'paddingTop': '60px'})


def create_company_register_form():
    """Create company registration form"""
    return dbc.Card([
        dbc.CardBody([
            html.H5("Company Registration", className="mb-4",
                   style={'color': '#34495e', 'fontWeight': '600'}),

            # Company Information
            html.H6("Company Information", className="mb-3 text-muted"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Company Name *", className="fw-bold"),
                    dbc.Input(id="reg-company-name", placeholder="Acme Healthcare", className="mb-3")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Company Email *", className="fw-bold"),
                    dbc.Input(id="reg-company-email", type="email",
                             placeholder="info@company.com", className="mb-3")
                ], width=6),
                dbc.Col([
                    dbc.Label("Phone", className="fw-bold"),
                    dbc.Input(id="reg-company-phone", placeholder="(123) 456-7890", className="mb-3")
                ], width=6)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Address", className="fw-bold"),
                    dbc.Input(id="reg-company-address", placeholder="123 Main St, City, State", className="mb-3")
                ], width=12)
            ]),

            html.Hr(),

            # Administrator Information
            html.H6("Administrator Information", className="mb-3 text-muted"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Admin Name *", className="fw-bold"),
                    dbc.Input(id="reg-admin-name", placeholder="John Doe", className="mb-3")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Admin Email *", className="fw-bold"),
                    dbc.Input(id="reg-admin-email", type="email",
                             placeholder="admin@company.com", className="mb-3")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Password *", className="fw-bold"),
                    dbc.Input(id="reg-company-password", type="password",
                             placeholder="Min 8 chars, include uppercase, lowercase, number", className="mb-2")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Confirm Password *", className="fw-bold"),
                    dbc.Input(id="reg-company-password-confirm", type="password",
                             placeholder="Re-enter password", className="mb-3")
                ], width=12)
            ]),

            # Terms checkbox
            dbc.Checkbox(
                id="reg-company-terms",
                label="I agree to the Terms of Service and Privacy Policy",
                className="mb-3"
            ),

            # Register button
            dbc.Button(
                "Create Company Account",
                id="register-company-button",
                color="primary",
                className="w-100 mb-3",
                size="lg"
            ),

            html.Hr(),

            html.Div([
                html.Span("Already have an account? ", style={'marginRight': '5px'}),
                dbc.Button("Sign in here", id="show-login-link",
                      color="link", size="sm", n_clicks=0,
                      style={'fontWeight': '600', 'padding': '0', 'textDecoration': 'none'})
            ], className="text-center mb-0")
        ])
    ], className="shadow-sm", style={'borderRadius': '12px'})


def create_employee_register_form():
    """Create employee registration form"""
    return dbc.Card([
        dbc.CardBody([
            html.H5("Employee Registration", className="mb-4",
                   style={'color': '#34495e', 'fontWeight': '600'}),

            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "You need a Company ID from your organization administrator to register as an employee."
            ], color="info", className="mb-4"),

            # Employee Information
            dbc.Row([
                dbc.Col([
                    dbc.Label("Company ID *", className="fw-bold"),
                    dbc.Input(id="reg-employee-company-id", type="number",
                             placeholder="Provided by your administrator", className="mb-3")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("First Name *", className="fw-bold"),
                    dbc.Input(id="reg-employee-first-name", placeholder="John", className="mb-3")
                ], width=6),
                dbc.Col([
                    dbc.Label("Last Name *", className="fw-bold"),
                    dbc.Input(id="reg-employee-last-name", placeholder="Doe", className="mb-3")
                ], width=6)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Email *", className="fw-bold"),
                    dbc.Input(id="reg-employee-email", type="email",
                             placeholder="john.doe@company.com", className="mb-3")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Role", className="fw-bold"),
                    dbc.Select(
                        id="reg-employee-role",
                        options=[
                            {'label': 'Analyst', 'value': 'analyst'},
                            {'label': 'Manager', 'value': 'manager'},
                            {'label': 'Director', 'value': 'director'},
                            {'label': 'Executive', 'value': 'executive'}
                        ],
                        value='analyst',
                        className="mb-3"
                    )
                ], width=6),
                dbc.Col([
                    dbc.Label("Department", className="fw-bold"),
                    dbc.Input(id="reg-employee-department", placeholder="Finance", className="mb-3")
                ], width=6)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Password *", className="fw-bold"),
                    dbc.Input(id="reg-employee-password", type="password",
                             placeholder="Min 8 chars, include uppercase, lowercase, number", className="mb-2")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Confirm Password *", className="fw-bold"),
                    dbc.Input(id="reg-employee-password-confirm", type="password",
                             placeholder="Re-enter password", className="mb-3")
                ], width=12)
            ]),

            # Terms checkbox
            dbc.Checkbox(
                id="reg-employee-terms",
                label="I agree to the Terms of Service and Privacy Policy",
                className="mb-3"
            ),

            # Register button
            dbc.Button(
                "Create Employee Account",
                id="register-employee-button",
                color="primary",
                className="w-100 mb-3",
                size="lg"
            ),

            html.Hr(),

            html.Div([
                html.Span("Already have an account? ", style={'marginRight': '5px'}),
                dbc.Button("Sign in here", id="show-login-link-employee",
                      color="link", size="sm", n_clicks=0,
                      style={'fontWeight': '600', 'padding': '0', 'textDecoration': 'none'})
            ], className="text-center mb-0")
        ])
    ], className="shadow-sm", style={'borderRadius': '12px'})


def create_individual_register_form():
    """Create individual registration form"""
    return dbc.Card([
        dbc.CardBody([
            html.H5("Individual Registration", className="mb-4",
                   style={'color': '#34495e', 'fontWeight': '600'}),

            # Personal Information
            dbc.Row([
                dbc.Col([
                    dbc.Label("First Name *", className="fw-bold"),
                    dbc.Input(id="reg-individual-first-name", placeholder="John", className="mb-3")
                ], width=6),
                dbc.Col([
                    dbc.Label("Last Name *", className="fw-bold"),
                    dbc.Input(id="reg-individual-last-name", placeholder="Doe", className="mb-3")
                ], width=6)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Email *", className="fw-bold"),
                    dbc.Input(id="reg-individual-email", type="email",
                             placeholder="john.doe@example.com", className="mb-3")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Organization", className="fw-bold"),
                    dbc.Input(id="reg-individual-organization",
                             placeholder="Hospital or organization name (optional)", className="mb-3")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Phone", className="fw-bold"),
                    dbc.Input(id="reg-individual-phone", placeholder="(123) 456-7890", className="mb-3")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Password *", className="fw-bold"),
                    dbc.Input(id="reg-individual-password", type="password",
                             placeholder="Min 8 chars, include uppercase, lowercase, number", className="mb-2")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Confirm Password *", className="fw-bold"),
                    dbc.Input(id="reg-individual-password-confirm", type="password",
                             placeholder="Re-enter password", className="mb-3")
                ], width=12)
            ]),

            # Terms checkbox
            dbc.Checkbox(
                id="reg-individual-terms",
                label="I agree to the Terms of Service and Privacy Policy",
                className="mb-3"
            ),

            # Register button
            dbc.Button(
                "Create Individual Account",
                id="register-individual-button",
                color="primary",
                className="w-100 mb-3",
                size="lg"
            ),

            html.Hr(),

            html.Div([
                html.Span("Already have an account? ", style={'marginRight': '5px'}),
                dbc.Button("Sign in here", id="show-login-link-individual",
                      color="link", size="sm", n_clicks=0,
                      style={'fontWeight': '600', 'padding': '0', 'textDecoration': 'none'})
            ], className="text-center mb-0")
        ])
    ], className="shadow-sm", style={'borderRadius': '12px'})


def create_user_menu(user_info):
    """Create user menu dropdown for authenticated users"""
    display_name = user_info.get('display_name', 'User')
    user_type = user_info.get('user_type', 'individual')

    # Get icon based on user type
    icon_map = {
        'company': 'fa-building',
        'employee': 'fa-user-tie',
        'individual': 'fa-user'
    }
    icon = icon_map.get(user_type, 'fa-user')

    return dbc.DropdownMenu(
        children=[
            dbc.DropdownMenuItem(
                [html.I(className=f"fas {icon} me-2"), display_name],
                header=True
            ),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem(
                [html.I(className="fas fa-user-circle me-2"), "Profile"],
                id="user-profile-link"
            ),
            dbc.DropdownMenuItem(
                [html.I(className="fas fa-cog me-2"), "Settings"],
                id="user-settings-link"
            ),
            dbc.DropdownMenuItem(divider=True),
            dbc.DropdownMenuItem(
                [html.I(className="fas fa-sign-out-alt me-2"), "Logout"],
                id="logout-button",
                style={'color': '#e74c3c'}
            ),
        ],
        label=[
            html.I(className=f"fas {icon} me-2"),
            display_name
        ],
        color="light",
        className="ms-2"
    )
