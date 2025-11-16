# Authentication System - Quick Start Guide

## 🚀 Get Started in 3 Minutes

### 1. Install Dependencies

```bash
pip install bcrypt dash dash-bootstrap-components flask
```

Or use the requirements file:

```bash
pip install -r requirements_auth.txt
```

### 2. Run the Authenticated Dashboard

```bash
python app_with_auth.py
```

### 3. Open Your Browser

Navigate to: **http://127.0.0.1:8050**

You'll see the professional login page!

## 📝 Create Your First Account

### Option A: Individual User (Recommended for testing)

1. Click "Sign up here" on the login page
2. Select **Individual Account**
3. Fill in the form:
   - First Name: `John`
   - Last Name: `Doe`
   - Email: `john@example.com`
   - Password: `TestPass123` (must include uppercase, lowercase, and number)
   - Confirm password
   - Check "I agree to Terms"
4. Click "Create Individual Account"
5. Sign in with your credentials!

### Option B: Company Account (For teams)

1. Click "Sign up here" on the login page
2. Select **Company Account**
3. Fill in company details:
   - Company Name: `Acme Healthcare`
   - Company Email: `info@acme.com`
   - Admin Name: `Jane Smith`
   - Admin Email: `jane@acme.com`
   - Password: `AdminPass123`
4. Note the **Company ID** from the success message
5. Share Company ID with employees for registration

### Option C: Employee Account

1. Get Company ID from your administrator
2. Click "Sign up here" on the login page
3. Select **Employee Account**
4. Fill in:
   - Company ID: `1` (from your admin)
   - Name, email, role, department
   - Password: `EmployeePass123`
5. Sign in!

## 🔐 Security Features

✅ **Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

✅ **Security Measures**:
- Passwords hashed with bcrypt (never stored in plain text)
- Automatic session expiration (24 hours)
- Email validation
- Audit logging for all security events
- Protection against SQL injection

## 📊 What's Included

### Authentication Files
- `app_with_auth.py` - Main authenticated application
- `auth_models.py` - Database schema (6 tables)
- `auth_manager.py` - Authentication logic & password hashing
- `auth_components.py` - Beautiful login/registration UI

### Database
- Location: `data/auth.db` (created automatically)
- Type: SQLite
- Tables: companies, employees, individuals, sessions, audit_log, hospital_access

### Documentation
- `AUTHENTICATION_GUIDE.md` - Complete documentation (API, security, troubleshooting)
- `AUTH_QUICKSTART.md` - This file
- `requirements_auth.txt` - Dependencies

## 🎨 User Interface Features

- **Professional Design**: Clean, modern interface inspired by leading SaaS platforms
- **Responsive**: Works on desktop, tablet, and mobile
- **Icons**: Font Awesome icons throughout
- **Validation**: Real-time form validation
- **Alerts**: User-friendly success/error messages
- **User Menu**: Dropdown with profile, settings, and logout

## 👥 Account Types Comparison

| Feature | Individual | Employee | Company |
|---------|-----------|----------|---------|
| Independent access | ✅ | ❌ | ✅ |
| Team collaboration | ❌ | ✅ | ✅ |
| Employee management | ❌ | ❌ | ✅ |
| Company ID required | ❌ | ✅ | ❌ |
| Subscription tiers | ✅ | ❌ | ✅ |

## 🔧 Common Tasks

### View Registered Users

```bash
sqlite3 data/auth.db
```

```sql
-- View all companies
SELECT company_id, company_name, admin_email, created_at FROM companies;

-- View all employees
SELECT employee_id, first_name, last_name, email, company_id FROM employees;

-- View all individuals
SELECT individual_id, first_name, last_name, email FROM individuals;

-- View active sessions
SELECT user_type, user_email, created_at FROM sessions;

-- View audit log
SELECT action, user_email, status, created_at FROM audit_log ORDER BY created_at DESC LIMIT 10;

.quit
```

### Reset Database (WARNING: Deletes all users!)

```bash
rm data/auth.db
python app_with_auth.py  # Creates fresh database
```

### Test Password Hashing

```python
from auth_manager import auth_manager

# Hash a password
hashed = auth_manager.hash_password("TestPassword123")
print(f"Hashed: {hashed}")

# Verify password
is_valid = auth_manager.verify_password("TestPassword123", hashed)
print(f"Valid: {is_valid}")  # True

is_valid = auth_manager.verify_password("WrongPassword", hashed)
print(f"Valid: {is_valid}")  # False
```

## 🐛 Troubleshooting

### "Email already exists"
Each email can only be registered once. Use a different email or reset the database.

### "Company not found" (employee registration)
Make sure you have the correct Company ID from your administrator.

### "Module not found: bcrypt"
Install dependencies: `pip install bcrypt`

### Database locked error
Close any other connections to `data/auth.db` (like SQLite browser)

### Session expired
Sessions expire after 24 hours. Just log in again.

## 📚 Learn More

- **Full Documentation**: See `AUTHENTICATION_GUIDE.md`
- **API Reference**: See `AUTHENTICATION_GUIDE.md` → API Reference section
- **Security Best Practices**: See `AUTHENTICATION_GUIDE.md` → Security section
- **Database Schema**: See `AUTHENTICATION_GUIDE.md` → Database Schema section

## 🎯 Next Steps

1. ✅ Create your first account
2. ✅ Log in successfully
3. ✅ Explore the authenticated dashboard
4. 📖 Read `AUTHENTICATION_GUIDE.md` for advanced features
5. 🔐 Review security best practices
6. 🚀 Integrate with full Hospital KPI Dashboard (coming soon)

## 💡 Pro Tips

- **For Testing**: Use individual accounts (quickest setup)
- **For Teams**: Create company account first, then add employees
- **Company ID**: Always save it! Employees need it to register
- **Password Strength**: Use a password manager for secure passwords
- **Session Management**: Sessions auto-expire after 24 hours
- **Audit Log**: Review `/data/auth.db` → `audit_log` table for security events

## ✨ Features Coming Soon

- Password reset via email
- Two-factor authentication (2FA)
- OAuth (Google, Microsoft)
- Hospital-level permissions
- Full dashboard integration
- Team analytics
- Company admin panel

---

**Need Help?** Check `AUTHENTICATION_GUIDE.md` for comprehensive documentation.

**Version**: 1.0 | **Last Updated**: 2025-11-16
