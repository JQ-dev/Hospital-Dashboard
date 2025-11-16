"""
User Authentication Models and Database Schema

Supports three user types:
1. Companies (organizations with multiple employees)
2. Employees (belonging to a company)
3. Individuals (independent users)

Security features:
- Password hashing with bcrypt
- Email validation
- Account status tracking
- Last login tracking
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import re


class AuthDatabase:
    """Manages the authentication database"""

    def __init__(self, db_path='data/auth.db'):
        """Initialize authentication database"""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        """Create database tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Companies table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                company_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL UNIQUE,
                company_email TEXT NOT NULL UNIQUE,
                admin_name TEXT NOT NULL,
                admin_email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                status TEXT DEFAULT 'active',
                subscription_tier TEXT DEFAULT 'basic',
                max_employees INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                UNIQUE(company_name)
            )
        """)

        # Employees table (linked to companies)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                role TEXT DEFAULT 'analyst',
                department TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies (company_id),
                UNIQUE(email)
            )
        """)

        # Individuals table (independent users)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS individuals (
                individual_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                organization TEXT,
                phone TEXT,
                status TEXT DEFAULT 'active',
                subscription_tier TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                UNIQUE(email)
            )
        """)

        # Hospital access permissions (which hospitals can users access)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hospital_access (
                access_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_type TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                provider_number TEXT NOT NULL,
                access_level TEXT DEFAULT 'read',
                granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_type, user_id, provider_number)
            )
        """)

        # Session tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_type TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                user_email TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Audit log for security
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_type TEXT,
                user_id INTEGER,
                user_email TEXT,
                action TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def email_exists(self, email):
        """Check if email already exists in any user table"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check companies
        cursor.execute("SELECT 1 FROM companies WHERE admin_email = ? OR company_email = ?",
                      (email, email))
        if cursor.fetchone():
            conn.close()
            return True

        # Check employees
        cursor.execute("SELECT 1 FROM employees WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return True

        # Check individuals
        cursor.execute("SELECT 1 FROM individuals WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return True

        conn.close()
        return False

    def company_name_exists(self, company_name):
        """Check if company name already exists"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM companies WHERE company_name = ?", (company_name,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def get_user_by_email(self, email):
        """
        Get user by email from any user type
        Returns: (user_dict, user_type) or (None, None)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check companies (admin email)
        cursor.execute("SELECT * FROM companies WHERE admin_email = ?", (email,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row), 'company'

        # Check employees
        cursor.execute("SELECT * FROM employees WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row), 'employee'

        # Check individuals
        cursor.execute("SELECT * FROM individuals WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return dict(row), 'individual'

        conn.close()
        return None, None

    def create_company(self, company_data):
        """
        Create a new company account

        company_data should include:
        - company_name
        - company_email
        - admin_name
        - admin_email
        - password_hash
        - phone (optional)
        - address (optional)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO companies
                (company_name, company_email, admin_name, admin_email, password_hash, phone, address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                company_data['company_name'],
                company_data['company_email'],
                company_data['admin_name'],
                company_data['admin_email'],
                company_data['password_hash'],
                company_data.get('phone'),
                company_data.get('address')
            ))
            company_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return True, company_id, "Company account created successfully"
        except sqlite3.IntegrityError as e:
            conn.close()
            return False, None, f"Company name or email already exists"
        except Exception as e:
            conn.close()
            return False, None, f"Error creating company: {str(e)}"

    def create_employee(self, employee_data):
        """
        Create a new employee account

        employee_data should include:
        - company_id
        - email
        - password_hash
        - first_name
        - last_name
        - role (optional)
        - department (optional)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if company exists
        cursor.execute("SELECT max_employees FROM companies WHERE company_id = ?",
                      (employee_data['company_id'],))
        company = cursor.fetchone()
        if not company:
            conn.close()
            return False, None, "Company not found"

        # Check employee limit
        cursor.execute("SELECT COUNT(*) as count FROM employees WHERE company_id = ?",
                      (employee_data['company_id'],))
        count = cursor.fetchone()['count']
        if count >= company['max_employees']:
            conn.close()
            return False, None, f"Employee limit reached ({company['max_employees']})"

        try:
            cursor.execute("""
                INSERT INTO employees
                (company_id, email, password_hash, first_name, last_name, role, department)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                employee_data['company_id'],
                employee_data['email'],
                employee_data['password_hash'],
                employee_data['first_name'],
                employee_data['last_name'],
                employee_data.get('role', 'analyst'),
                employee_data.get('department')
            ))
            employee_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return True, employee_id, "Employee account created successfully"
        except sqlite3.IntegrityError:
            conn.close()
            return False, None, "Email already exists"
        except Exception as e:
            conn.close()
            return False, None, f"Error creating employee: {str(e)}"

    def create_individual(self, individual_data):
        """
        Create a new individual account

        individual_data should include:
        - email
        - password_hash
        - first_name
        - last_name
        - organization (optional)
        - phone (optional)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO individuals
                (email, password_hash, first_name, last_name, organization, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                individual_data['email'],
                individual_data['password_hash'],
                individual_data['first_name'],
                individual_data['last_name'],
                individual_data.get('organization'),
                individual_data.get('phone')
            ))
            individual_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return True, individual_id, "Individual account created successfully"
        except sqlite3.IntegrityError:
            conn.close()
            return False, None, "Email already exists"
        except Exception as e:
            conn.close()
            return False, None, f"Error creating individual account: {str(e)}"

    def update_last_login(self, user_type, user_id):
        """Update last login timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()

        table_map = {
            'company': ('companies', 'company_id'),
            'employee': ('employees', 'employee_id'),
            'individual': ('individuals', 'individual_id')
        }

        if user_type in table_map:
            table, id_col = table_map[user_type]
            cursor.execute(f"""
                UPDATE {table}
                SET last_login = CURRENT_TIMESTAMP
                WHERE {id_col} = ?
            """, (user_id,))
            conn.commit()

        conn.close()

    def log_action(self, action, user_type=None, user_id=None, user_email=None,
                   status='success', details=None, ip_address=None, user_agent=None):
        """Log action to audit log"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO audit_log
            (user_type, user_id, user_email, action, status, details, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_type, user_id, user_email, action, status, details, ip_address, user_agent))

        conn.commit()
        conn.close()

    def get_company_employees(self, company_id):
        """Get all employees for a company"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT employee_id, email, first_name, last_name, role, department,
                   status, created_at, last_login
            FROM employees
            WHERE company_id = ?
            ORDER BY last_name, first_name
        """, (company_id,))

        employees = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return employees

    def get_user_display_name(self, user_type, user_dict):
        """Get display name for user"""
        if user_type == 'company':
            return f"{user_dict['company_name']} ({user_dict['admin_name']})"
        elif user_type == 'employee':
            return f"{user_dict['first_name']} {user_dict['last_name']}"
        elif user_type == 'individual':
            return f"{user_dict['first_name']} {user_dict['last_name']}"
        return "Unknown User"
