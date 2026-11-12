"""
SPEAKUP Authentication Routes
Handles user registration, login, logout, password hashing, and session management.
Includes authentication and authorization decorators for route protection.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

# Create the authentication blueprint
auth_bp = Blueprint('auth', __name__)


# -----------------------------------------------------------------------------
# Decorators for Route Protection
# -----------------------------------------------------------------------------

def login_required(view):
    """
    Decorator that restricts route access to logged-in users only.
    Redirects unauthenticated users to the login page with a flash notice.
    """
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


def role_required(required_role):
    """
    Decorator generator that checks if the logged-in user possesses a specific role.
    Useful for future admin panels or restricted routes.
    """
    def decorator(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if 'user_id' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('user_role') != required_role:
                flash('Access denied: You do not have permission for this resource.', 'error')
                return redirect(url_for('main.dashboard'))
            return view(**kwargs)
        return wrapped_view
    return decorator


def admin_required(view):
    """
    Convenience decorator for admin-only routes.
    """
    return role_required('admin')(view)


# -----------------------------------------------------------------------------
# Authentication Routes
# -----------------------------------------------------------------------------

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route.
    Validates form data, checks for existing emails, hashes password,
    and inserts the user record into the MySQL database.
    """
    # If the user is already logged in, redirect straight to dashboard
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        if not name or not email or not password or not confirm_password:
            flash('All fields are required.', 'error')
            return render_template('register.html', name=name, email=email)

        if len(name) < 2:
            flash('Name must be at least 2 characters long.', 'error')
            return render_template('register.html', name=name, email=email)

        if '@' not in email or '.' not in email.split('@')[-1]:
            flash('Please enter a valid email address.', 'error')
            return render_template('register.html', name=name, email=email)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html', name=name, email=email)

        if password != confirm_password:
            flash('Passwords do not match. Please re-enter.', 'error')
            return render_template('register.html', name=name, email=email)

        # Database operations
        db = get_db()
        if not db:
            flash('Database connection unavailable. Please contact the administrator.', 'error')
            return render_template('register.html', name=name, email=email)

        cursor = db.cursor(dictionary=True)

        try:
            # Check if email is already taken using parameterized query
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('An account with this email address already exists.', 'error')
                return render_template('register.html', name=name, email=email)

            # Securely hash password using werkzeug
            password_hash = generate_password_hash(password)

            # Parameterized insert query to prevent SQL injection
            insert_query = """
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (name, email, password_hash, 'user'))
            db.commit()

            flash('Registration successful! Please log in with your credentials.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.rollback()
            flash(f'An unexpected error occurred during registration: {e}', 'error')
            return render_template('register.html', name=name, email=email)
        finally:
            cursor.close()

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route.
    Validates credentials against stored password hashes and initializes session.
    """
    # If already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Server-side validation
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('login.html', email=email)

        db = get_db()
        if not db:
            flash('Database connection unavailable. Please contact the administrator.', 'error')
            return render_template('login.html', email=email)

        cursor = db.cursor(dictionary=True)

        try:
            # Fetch user by email using parameterized query
            query = "SELECT id, name, email, password_hash, role FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            user = cursor.fetchone()

            # Verify existence and password hash
            if user and check_password_hash(user['password_hash'], password):
                # Set up session variables
                session.clear()
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_email'] = user['email']
                session['user_role'] = user['role']

                # Check if user already completed profile setup
                cursor.execute("SELECT id FROM profiles WHERE user_id = %s", (user['id'],))
                user_profile = cursor.fetchone()

                if not user_profile:
                    flash(f'Welcome, {user["name"]}! Please complete your profile setup to get started.', 'info')
                    return redirect(url_for('profile.setup'))

                flash(f'Welcome back, {user["name"]}!', 'success')
                return redirect(url_for('main.dashboard'))
            else:
                flash('Invalid email or password.', 'error')
                return render_template('login.html', email=email)

        except Exception as e:
            flash(f'An unexpected error occurred during login: {e}', 'error')
            return render_template('login.html', email=email)
        finally:
            cursor.close()

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """
    Logs out the current user by clearing the session.
    """
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))
