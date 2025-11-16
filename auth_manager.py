"""
Authentication Manager

Handles:
- User authentication (login/logout)
- Password hashing and verification (bcrypt)
- Session management
- Security features
"""

import bcrypt
import secrets
import sqlite3
from datetime import datetime, timedelta
from auth_models import AuthDatabase


class AuthManager:
    """Manages authentication and sessions"""

    def __init__(self, db_path='data/auth.db'):
        """Initialize authentication manager"""
        self.db = AuthDatabase(db_path)
        self.session_duration_hours = 24  # Session expires after 24 hours

    # =========================================================================
    # PASSWORD MANAGEMENT
    # =========================================================================

    def hash_password(self, password):
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password, password_hash):
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False

    def validate_password_strength(self, password):
        """
        Validate password strength
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"

        return True, "Password is strong"

    # =========================================================================
    # AUTHENTICATION
    # =========================================================================

    def authenticate(self, email, password):
        """
        Authenticate a user by email and password

        Returns: (success, user_type, user_dict, message)
        """
        # Get user by email
        user_dict, user_type = self.db.get_user_by_email(email)

        if not user_dict:
            self.db.log_action(
                action='login_failed',
                user_email=email,
                status='failed',
                details='Email not found'
            )
            return False, None, None, "Invalid email or password"

        # Check if account is active
        if user_dict.get('status') != 'active':
            self.db.log_action(
                action='login_failed',
                user_type=user_type,
                user_email=email,
                status='failed',
                details='Account inactive'
            )
            return False, None, None, "Account is not active"

        # Verify password
        password_hash = user_dict['password_hash']
        if not self.verify_password(password, password_hash):
            self.db.log_action(
                action='login_failed',
                user_type=user_type,
                user_email=email,
                status='failed',
                details='Invalid password'
            )
            return False, None, None, "Invalid email or password"

        # Update last login
        user_id = self._get_user_id(user_type, user_dict)
        self.db.update_last_login(user_type, user_id)

        # Log successful login
        self.db.log_action(
            action='login_success',
            user_type=user_type,
            user_id=user_id,
            user_email=email,
            status='success'
        )

        return True, user_type, user_dict, "Login successful"

    def _get_user_id(self, user_type, user_dict):
        """Get user ID based on user type"""
        if user_type == 'company':
            return user_dict['company_id']
        elif user_type == 'employee':
            return user_dict['employee_id']
        elif user_type == 'individual':
            return user_dict['individual_id']
        return None

    # =========================================================================
    # REGISTRATION
    # =========================================================================

    def register_company(self, company_data, password):
        """
        Register a new company

        company_data should include:
        - company_name
        - company_email
        - admin_name
        - admin_email
        - phone (optional)
        - address (optional)
        """
        # Validate email
        if not self.db.validate_email(company_data['admin_email']):
            return False, None, "Invalid admin email format"

        if not self.db.validate_email(company_data['company_email']):
            return False, None, "Invalid company email format"

        # Check if email exists
        if self.db.email_exists(company_data['admin_email']):
            return False, None, "Admin email already registered"

        if self.db.email_exists(company_data['company_email']):
            return False, None, "Company email already registered"

        # Check if company name exists
        if self.db.company_name_exists(company_data['company_name']):
            return False, None, "Company name already registered"

        # Validate password
        valid, msg = self.validate_password_strength(password)
        if not valid:
            return False, None, msg

        # Hash password
        company_data['password_hash'] = self.hash_password(password)

        # Create company
        success, company_id, message = self.db.create_company(company_data)

        if success:
            self.db.log_action(
                action='company_registered',
                user_type='company',
                user_id=company_id,
                user_email=company_data['admin_email'],
                status='success'
            )

        return success, company_id, message

    def register_employee(self, employee_data, password):
        """
        Register a new employee

        employee_data should include:
        - company_id
        - email
        - first_name
        - last_name
        - role (optional)
        - department (optional)
        """
        # Validate email
        if not self.db.validate_email(employee_data['email']):
            return False, None, "Invalid email format"

        # Check if email exists
        if self.db.email_exists(employee_data['email']):
            return False, None, "Email already registered"

        # Validate password
        valid, msg = self.validate_password_strength(password)
        if not valid:
            return False, None, msg

        # Hash password
        employee_data['password_hash'] = self.hash_password(password)

        # Create employee
        success, employee_id, message = self.db.create_employee(employee_data)

        if success:
            self.db.log_action(
                action='employee_registered',
                user_type='employee',
                user_id=employee_id,
                user_email=employee_data['email'],
                status='success'
            )

        return success, employee_id, message

    def register_individual(self, individual_data, password):
        """
        Register a new individual user

        individual_data should include:
        - email
        - first_name
        - last_name
        - organization (optional)
        - phone (optional)
        """
        # Validate email
        if not self.db.validate_email(individual_data['email']):
            return False, None, "Invalid email format"

        # Check if email exists
        if self.db.email_exists(individual_data['email']):
            return False, None, "Email already registered"

        # Validate password
        valid, msg = self.validate_password_strength(password)
        if not valid:
            return False, None, msg

        # Hash password
        individual_data['password_hash'] = self.hash_password(password)

        # Create individual
        success, individual_id, message = self.db.create_individual(individual_data)

        if success:
            self.db.log_action(
                action='individual_registered',
                user_type='individual',
                user_id=individual_id,
                user_email=individual_data['email'],
                status='success'
            )

        return success, individual_id, message

    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================

    def create_session(self, user_type, user_dict):
        """Create a new session for a user"""
        session_id = secrets.token_urlsafe(32)
        user_id = self._get_user_id(user_type, user_dict)
        user_email = self._get_user_email(user_type, user_dict)

        expires_at = datetime.now() + timedelta(hours=self.session_duration_hours)

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sessions (session_id, user_type, user_id, user_email, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, user_type, user_id, user_email, expires_at))

        conn.commit()
        conn.close()

        return session_id

    def _get_user_email(self, user_type, user_dict):
        """Get user email based on user type"""
        if user_type == 'company':
            return user_dict['admin_email']
        elif user_type == 'employee':
            return user_dict['email']
        elif user_type == 'individual':
            return user_dict['email']
        return None

    def validate_session(self, session_id):
        """
        Validate a session

        Returns: (valid, user_type, user_id, user_email)
        """
        if not session_id:
            return False, None, None, None

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_type, user_id, user_email, expires_at
            FROM sessions
            WHERE session_id = ?
        """, (session_id,))

        row = cursor.fetchone()

        if not row:
            conn.close()
            return False, None, None, None

        # Check if session expired
        expires_at = datetime.fromisoformat(row['expires_at'])
        if datetime.now() > expires_at:
            # Delete expired session
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
            conn.close()
            return False, None, None, None

        # Update last activity
        cursor.execute("""
            UPDATE sessions
            SET last_activity = CURRENT_TIMESTAMP
            WHERE session_id = ?
        """, (session_id,))
        conn.commit()

        user_type = row['user_type']
        user_id = row['user_id']
        user_email = row['user_email']

        conn.close()
        return True, user_type, user_id, user_email

    def get_user_from_session(self, session_id):
        """
        Get full user data from session

        Returns: (user_dict, user_type) or (None, None)
        """
        valid, user_type, user_id, user_email = self.validate_session(session_id)

        if not valid:
            return None, None

        # Get user data
        user_dict, _ = self.db.get_user_by_email(user_email)
        return user_dict, user_type

    def delete_session(self, session_id):
        """Delete a session (logout)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get session info for logging
        cursor.execute("SELECT user_type, user_id, user_email FROM sessions WHERE session_id = ?",
                      (session_id,))
        row = cursor.fetchone()

        if row:
            self.db.log_action(
                action='logout',
                user_type=row['user_type'],
                user_id=row['user_id'],
                user_email=row['user_email'],
                status='success'
            )

        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

    def cleanup_expired_sessions(self):
        """Remove all expired sessions"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM sessions
            WHERE expires_at < CURRENT_TIMESTAMP
        """)

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted

    # =========================================================================
    # USER MANAGEMENT
    # =========================================================================

    def get_user_info(self, user_type, user_dict):
        """Get formatted user information"""
        info = {
            'user_type': user_type,
            'display_name': self.db.get_user_display_name(user_type, user_dict),
            'email': self._get_user_email(user_type, user_dict),
            'status': user_dict.get('status'),
            'created_at': user_dict.get('created_at'),
            'last_login': user_dict.get('last_login')
        }

        if user_type == 'company':
            info['company_name'] = user_dict['company_name']
            info['company_id'] = user_dict['company_id']
            info['subscription_tier'] = user_dict.get('subscription_tier')
            info['max_employees'] = user_dict.get('max_employees')

        elif user_type == 'employee':
            info['employee_id'] = user_dict['employee_id']
            info['company_id'] = user_dict['company_id']
            info['role'] = user_dict.get('role')
            info['department'] = user_dict.get('department')
            info['name'] = f"{user_dict['first_name']} {user_dict['last_name']}"

        elif user_type == 'individual':
            info['individual_id'] = user_dict['individual_id']
            info['organization'] = user_dict.get('organization')
            info['subscription_tier'] = user_dict.get('subscription_tier')
            info['name'] = f"{user_dict['first_name']} {user_dict['last_name']}"

        return info


# Singleton instance
auth_manager = AuthManager()
