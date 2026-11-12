"""
SPEAKUP Main Routes
Handles general site views including the landing page and the user dashboard.
"""

from flask import Blueprint, render_template, session
from routes.auth import login_required

# Create the main blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    Public landing page for SPEAKUP.
    Introduces the platform, features, and provides links to register/login.
    """
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Learner dashboard placeholder.
    Accessible only to authenticated users via the @login_required decorator.
    """
    user_name = session.get('user_name', 'Learner')
    return render_template('dashboard.html', user_name=user_name)
