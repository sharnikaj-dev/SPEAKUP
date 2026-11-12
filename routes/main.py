"""
SPEAKUP Main Routes
Handles general site views including:
- Public landing page (/)
- Learner Dashboard (/dashboard)
- Level & Scenario details (/level/<id>)
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash
from db import get_db
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
    Learner Dashboard.
    - Requires active session and completed profile.
    - Displays welcome message with name, native language, and goal.
    - Displays progress summary (X of 5 levels completed).
    - Lists the 5 learning levels with status badges (Locked, Unlocked, Completed)
      and scenario count.
    """
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # 1. Fetch user and profile details
    cursor.execute("""
        SELECT u.name, p.native_language, p.background, p.goal, p.current_level_id
        FROM users u
        JOIN profiles p ON u.id = p.user_id
        WHERE u.id = %s
    """, (user_id,))
    profile = cursor.fetchone()

    # Guard: A logged-in user without a profile must not access the dashboard
    if not profile:
        cursor.close()
        flash('Please complete your profile setup first.', 'warning')
        return redirect(url_for('profile.setup'))

    # 2. Fetch the 5 levels with user-specific progress status and scenario counts
    cursor.execute("""
        SELECT 
            l.id,
            l.level_number,
            l.title,
            l.description,
            COALESCE(pr.status, 'locked') AS status,
            COUNT(s.id) AS scenario_count
        FROM levels l
        LEFT JOIN progress pr ON l.id = pr.level_id AND pr.user_id = %s
        LEFT JOIN scenarios s ON l.id = s.level_id
        GROUP BY l.id, l.level_number, l.title, l.description, pr.status
        ORDER BY l.level_number ASC
    """, (user_id,))
    levels = cursor.fetchall()

    cursor.close()

    # 3. Calculate overall completion progress
    total_levels = len(levels) if levels else 5
    completed_levels = sum(1 for lvl in levels if lvl['status'] == 'completed')
    completion_percentage = int((completed_levels / total_levels) * 100) if total_levels > 0 else 0

    return render_template(
        'dashboard.html',
        profile=profile,
        levels=levels,
        total_levels=total_levels,
        completed_levels=completed_levels,
        completion_percentage=completion_percentage
    )


@main_bp.route('/level/<int:level_id>')
@login_required
def level_detail(level_id):
    """
    Level Scenarios Page.
    - Requires active session and profile.
    - Verifies that the level exists and is unlocked or completed for the current user.
    - If locked, flashes a warning and redirects back to /dashboard.
    - Displays all scenarios for the level.
    """
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # 1. Check if user has a profile
    cursor.execute("SELECT id FROM profiles WHERE user_id = %s", (user_id,))
    if not cursor.fetchone():
        cursor.close()
        flash('Please complete your profile setup first.', 'warning')
        return redirect(url_for('profile.setup'))

    # 2. Fetch the requested level
    cursor.execute("SELECT id, level_number, title, description FROM levels WHERE id = %s", (level_id,))
    level = cursor.fetchone()

    if not level:
        cursor.close()
        flash('The requested level does not exist.', 'error')
        return redirect(url_for('main.dashboard'))

    # 3. Check progress status for this level
    cursor.execute("""
        SELECT status 
        FROM progress 
        WHERE user_id = %s AND level_id = %s
    """, (user_id, level_id))
    prog = cursor.fetchone()
    level_status = prog['status'] if prog else 'locked'

    # Security check: Locked levels cannot be opened directly via URL
    if level_status == 'locked':
        cursor.close()
        flash(f"Level {level['level_number']} ({level['title']}) is locked. Complete previous levels to unlock it.", 'warning')
        return redirect(url_for('main.dashboard'))

    # 4. Fetch all scenarios for this level
    cursor.execute("""
        SELECT id, level_id, title, description, ai_role_prompt, opening_message
        FROM scenarios
        WHERE level_id = %s
        ORDER BY id ASC
    """, (level_id,))
    scenarios = cursor.fetchall()

    cursor.close()

    return render_template(
        'level.html',
        level=level,
        level_status=level_status,
        scenarios=scenarios
    )
