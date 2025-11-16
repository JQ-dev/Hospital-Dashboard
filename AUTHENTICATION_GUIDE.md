# Hospital Dashboard Authentication System

## Overview

The Hospital Dashboard now includes a comprehensive, secure authentication system supporting three user types:

1. **Company Accounts** - Organizations with multiple team members
2. **Employee Accounts** - Team members belonging to a company
3. **Individual Accounts** - Independent healthcare professionals

## Features

### Security
- ✅ Password hashing with bcrypt
- ✅ Email validation
- ✅ Strong password requirements (min 8 chars, uppercase, lowercase, digit)
- ✅ Session management with automatic expiration
- ✅ Audit logging for security events
- ✅ Account status tracking (active/inactive)

### User Experience
- ✅ Clean, professional login interface
- ✅ Easy registration with account type selection
- ✅ User-friendly error messages
- ✅ Responsive design
- ✅ Remember me functionality
- ✅ Session persistence

### Multi-User Support
- ✅ Company hierarchies (admin + employees)
- ✅ Employee limits based on subscription tier
- ✅ Role-based access (analyst, manager, director, executive)
- ✅ Department organization

## Quick Start

### 1. Install Required Dependencies

```bash
pip install bcrypt dash dash-bootstrap-components flask
```

### 2. Run the Authenticated Dashboard

```bash
python app_with_auth.py
```

### 3. Access the Dashboard

Open your browser to: `http://127.0.0.1:8050`

## User Account Types

### Company Account

**Use Case**: Healthcare organizations with multiple team members

**Registration Fields**:
- Company Name *
- Company Email *
- Phone (optional)
- Address (optional)
- Administrator Name *
- Administrator Email *
- Password *

**Features**:
- Company ID for employee registration
- Employee management
- Subscription tiers (basic, professional, enterprise)
- Configurable employee limits

**Default Settings**:
- Max Employees: 10
- Subscription Tier: Basic

### Employee Account

**Use Case**: Team members working for a registered company

**Registration Fields**:
- Company ID * (provided by administrator)
- First Name *
- Last Name *
- Email *
- Role (analyst, manager, director, executive)
- Department (optional)
- Password *

**Features**:
- Linked to parent company
- Role-based permissions
- Department organization
- Individual analytics tracking

### Individual Account

**Use Case**: Independent healthcare professionals, consultants, or researchers

**Registration Fields**:
- First Name *
- Last Name *
- Email *
- Organization (optional)
- Phone (optional)
- Password *

**Features**:
- Full dashboard access
- Personal analytics
- Subscription tiers (free, pro, enterprise)

## Password Requirements

All passwords must meet these security requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Examples**:
- ✅ `MyPassword123`
- ✅ `SecureP@ss1`
- ❌ `password` (no uppercase, no digit)
- ❌ `Pass123` (too short)

## Database Schema

### Tables

#### `companies`
Stores company account information
- `company_id` (PK)
- `company_name` (unique)
- `company_email` (unique)
- `admin_name`
- `admin_email` (unique)
- `password_hash`
- `phone`, `address`
- `status` (active/inactive)
- `subscription_tier`
- `max_employees`
- `created_at`, `last_login`

#### `employees`
Stores employee account information
- `employee_id` (PK)
- `company_id` (FK → companies)
- `email` (unique)
- `password_hash`
- `first_name`, `last_name`
- `role`, `department`
- `status` (active/inactive)
- `created_at`, `last_login`

#### `individuals`
Stores individual account information
- `individual_id` (PK)
- `email` (unique)
- `password_hash`
- `first_name`, `last_name`
- `organization`, `phone`
- `status` (active/inactive)
- `subscription_tier`
- `created_at`, `last_login`

#### `sessions`
Manages active user sessions
- `session_id` (PK)
- `user_type`, `user_id`, `user_email`
- `created_at`, `expires_at`
- `last_activity`

#### `audit_log`
Security audit trail
- `log_id` (PK)
- `user_type`, `user_id`, `user_email`
- `action` (login_success, login_failed, registration, etc.)
- `status`, `details`
- `ip_address`, `user_agent`
- `created_at`

#### `hospital_access`
Hospital-level permissions (future feature)
- `access_id` (PK)
- `user_type`, `user_id`
- `provider_number`
- `access_level` (read/write/admin)
- `granted_at`

## File Structure

```
Hospital-Dashboard/
├── app_with_auth.py              # Main authenticated application
├── auth_models.py                # Database models and schema
├── auth_manager.py               # Authentication logic
├── auth_components.py            # UI components (login/registration)
├── data/
│   └── auth.db                   # SQLite authentication database
├── dashboard.py                  # Original dashboard (unauthenticated)
└── AUTHENTICATION_GUIDE.md       # This file
```

## API Reference

### AuthManager Class

#### Authentication Methods

```python
from auth_manager import auth_manager

# Authenticate a user
success, user_type, user_dict, message = auth_manager.authenticate(
    email="user@example.com",
    password="MyPassword123"
)

# Validate password strength
valid, message = auth_manager.validate_password_strength("MyPassword123")

# Hash a password
password_hash = auth_manager.hash_password("MyPassword123")

# Verify a password
is_valid = auth_manager.verify_password("MyPassword123", password_hash)
```

#### Registration Methods

```python
# Register a company
company_data = {
    'company_name': 'Acme Healthcare',
    'company_email': 'info@acme.com',
    'admin_name': 'John Doe',
    'admin_email': 'john@acme.com',
    'phone': '(123) 456-7890',
    'address': '123 Main St'
}
success, company_id, message = auth_manager.register_company(
    company_data,
    password="AdminPass123"
)

# Register an employee
employee_data = {
    'company_id': 1,
    'first_name': 'Jane',
    'last_name': 'Smith',
    'email': 'jane@acme.com',
    'role': 'analyst',
    'department': 'Finance'
}
success, employee_id, message = auth_manager.register_employee(
    employee_data,
    password="EmployeePass123"
)

# Register an individual
individual_data = {
    'first_name': 'Bob',
    'last_name': 'Johnson',
    'email': 'bob@example.com',
    'organization': 'General Hospital',
    'phone': '(555) 123-4567'
}
success, individual_id, message = auth_manager.register_individual(
    individual_data,
    password="IndividualPass123"
)
```

#### Session Management

```python
# Create a session
session_id = auth_manager.create_session(user_type, user_dict)

# Validate a session
valid, user_type, user_id, user_email = auth_manager.validate_session(session_id)

# Get user from session
user_dict, user_type = auth_manager.get_user_from_session(session_id)

# Delete a session (logout)
auth_manager.delete_session(session_id)

# Cleanup expired sessions
deleted_count = auth_manager.cleanup_expired_sessions()
```

### AuthDatabase Class

```python
from auth_models import AuthDatabase

db = AuthDatabase('data/auth.db')

# Check if email exists
exists = db.email_exists('user@example.com')

# Get user by email
user_dict, user_type = db.get_user_by_email('user@example.com')

# Get company employees
employees = db.get_company_employees(company_id=1)

# Log an action
db.log_action(
    action='login_success',
    user_type='individual',
    user_id=123,
    user_email='user@example.com',
    status='success'
)
```

## Usage Examples

### Example 1: Company Registration Flow

```python
# 1. Admin registers company
company_data = {
    'company_name': 'City Hospital',
    'company_email': 'admin@cityhospital.com',
    'admin_name': 'Dr. Sarah Johnson',
    'admin_email': 'sarah@cityhospital.com'
}
success, company_id, msg = auth_manager.register_company(
    company_data,
    "SecurePass123"
)
print(f"Company ID: {company_id}")  # Save this for employees

# 2. Employee joins using company ID
employee_data = {
    'company_id': company_id,  # From step 1
    'first_name': 'Mike',
    'last_name': 'Chen',
    'email': 'mike@cityhospital.com',
    'role': 'analyst'
}
success, emp_id, msg = auth_manager.register_employee(
    employee_data,
    "EmployeePass123"
)

# 3. Login
success, user_type, user_dict, msg = auth_manager.authenticate(
    'mike@cityhospital.com',
    'EmployeePass123'
)

# 4. Create session
session_id = auth_manager.create_session(user_type, user_dict)
```

### Example 2: Individual User Flow

```python
# 1. Register
individual_data = {
    'first_name': 'Dr. Emily',
    'last_name': 'Rodriguez',
    'email': 'emily@healthcare.com',
    'organization': 'Independent Consultant'
}
success, user_id, msg = auth_manager.register_individual(
    individual_data,
    "StrongPass123"
)

# 2. Login
success, user_type, user_dict, msg = auth_manager.authenticate(
    'emily@healthcare.com',
    'StrongPass123'
)

# 3. Get user info
user_info = auth_manager.get_user_info(user_type, user_dict)
print(f"Welcome, {user_info['display_name']}!")
```

## Security Best Practices

### For Developers

1. **Never store plain text passwords** - Always use `hash_password()`
2. **Validate all inputs** - Use built-in validation methods
3. **Check session validity** - Always validate sessions before granting access
4. **Log security events** - Use the audit log for all important actions
5. **Use HTTPS in production** - Never transmit credentials over HTTP
6. **Implement rate limiting** - Prevent brute force attacks
7. **Regular session cleanup** - Run `cleanup_expired_sessions()` periodically

### For Administrators

1. **Use strong passwords** - Follow the password requirements
2. **Protect Company IDs** - Only share with authorized employees
3. **Monitor audit logs** - Review for suspicious activity
4. **Manage employee limits** - Adjust based on subscription tier
5. **Deactivate unused accounts** - Set status to 'inactive'

## Troubleshooting

### Common Issues

#### "Email already exists"
- **Cause**: Email is registered under any user type
- **Solution**: Use a different email or reset password (feature coming soon)

#### "Company not found" (employee registration)
- **Cause**: Invalid Company ID
- **Solution**: Get correct Company ID from your administrator

#### "Employee limit reached"
- **Cause**: Company has reached max_employees
- **Solution**: Upgrade subscription tier or remove inactive employees

#### "Invalid email or password"
- **Cause**: Incorrect credentials or inactive account
- **Solution**: Verify email/password, check if account is active

#### "Session expired"
- **Cause**: Session older than 24 hours
- **Solution**: Log in again

### Database Issues

#### Reset database
```bash
# WARNING: This deletes all users!
rm data/auth.db
python app_with_auth.py  # Creates new database
```

#### View database
```bash
sqlite3 data/auth.db
.tables  # List tables
SELECT * FROM companies;
SELECT * FROM employees;
SELECT * FROM individuals;
.quit
```

## Future Enhancements

### Planned Features
- [ ] Password reset via email
- [ ] Two-factor authentication (2FA)
- [ ] OAuth integration (Google, Microsoft)
- [ ] Hospital-level permissions
- [ ] Advanced role-based access control
- [ ] Team analytics and reporting
- [ ] Company admin dashboard
- [ ] API key authentication
- [ ] SAML/SSO support for enterprises

### Integration Roadmap
- [ ] Full dashboard integration with authentication
- [ ] User-specific hospital access lists
- [ ] Shared dashboards and reports
- [ ] Commenting and collaboration features
- [ ] Activity feeds

## Support

### Getting Help
- Review this documentation
- Check the database schema
- Review audit logs for errors
- Check code comments in auth_*.py files

### Reporting Issues
For bugs or feature requests, document:
1. User type (company/employee/individual)
2. Steps to reproduce
3. Error messages from audit log
4. Expected vs actual behavior

## License

This authentication system is part of the Hospital KPI Dashboard project.

---

**Last Updated**: 2025-11-16
**Version**: 1.0
**Database**: SQLite (auth.db)
**Security**: bcrypt password hashing, session-based authentication
