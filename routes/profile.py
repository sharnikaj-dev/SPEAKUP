"""
SPEAKUP Profile Management Routes
Handles learner profile setup, editing, and progress initialization.
Blueprint: profile_bp
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db
from routes.auth import login_required

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

# -----------------------------------------------------------------------------
# Constant Options for Form Dropdowns
# -----------------------------------------------------------------------------
NATIVE_LANGUAGES = ['Tamil', 'Hindi', 'Telugu', 'Malayalam', 'Kannada', 'Other']
BACKGROUNDS = ['School student', 'College student', 'Job seeker', 'Working professional']
GOALS = [
    'Daily conversation',
    'Academic communication',
    'Workplace communication',
    'Interview preparation'
]

# -----------------------------------------------------------------------------
# Helper Decorator
# -----------------------------------------------------------------------------
def profile_required(view):
    """
    Decorator ensuring the authenticated user has completed their profile setup.
    Redirects un-profiled users to /profile/setup.
    """
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM profiles WHERE user_id = %s", (session['user_id'],))
        profile = cursor.fetchone()
        cursor.close()

        if not profile:
            flash('Please complete your profile setup first.', 'warning')
            return redirect(url_for('profile.setup'))

        return view(**kwargs)
    return wrapped_view


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@profile_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """
    Initial profile setup for new learners.
    - Captures native language, background, and goal.
    - Assigns Level 1 as initial current level (not editable).
    - Initializes progress records for all 5 levels (Level 1 unlocked, others locked).
    """
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # If the user already created a profile, send them directly to the dashboard
    cursor.execute("SELECT id FROM profiles WHERE user_id = %s", (user_id,))
    existing_profile = cursor.fetchone()
    if existing_profile:
        cursor.close()
        return redirect(url_for('main.dashboard'))

    # Fetch Level 1 information to display as read-only current level
    cursor.execute("SELECT id, level_number, title FROM levels WHERE level_number = 1")
    level_one = cursor.fetchone()

    if request.method == 'POST':
        native_language = request.form.get('native_language', '').strip()
        background = request.form.get('background', '').strip()
        goal = request.form.get('goal', '').strip()

        # Server-side validation against allowed options
        if not native_language or not background or not goal:
            flash('Please select an option for all fields.', 'error')
            return render_template(
                'profile_setup.html',
                languages=NATIVE_LANGUAGES,
                backgrounds=BACKGROUNDS,
                goals=GOALS,
                level_one=level_one,
                selected_language=native_language,
                selected_background=background,
                selected_goal=goal
            )

        if native_language not in NATIVE_LANGUAGES:
            flash('Invalid native language selected.', 'error')
            return render_template('profile_setup.html', languages=NATIVE_LANGUAGES, backgrounds=BACKGROUNDS, goals=GOALS, level_one=level_one)

        if background not in BACKGROUNDS:
            flash('Invalid background selected.', 'error')
            return render_template('profile_setup.html', languages=NATIVE_LANGUAGES, backgrounds=BACKGROUNDS, goals=GOALS, level_one=level_one)

        if goal not in GOALS:
            flash('Invalid goal selected.', 'error')
            return render_template('profile_setup.html', languages=NATIVE_LANGUAGES, backgrounds=BACKGROUNDS, goals=GOALS, level_one=level_one)

        try:
            level_one_id = level_one['id'] if level_one else 1

            # 1. Insert new profile
            insert_profile_sql = """
                INSERT INTO profiles (user_id, native_language, background, goal, current_level_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_profile_sql, (user_id, native_language, background, goal, level_one_id))

            # 2. Fetch all levels to initialize progress rows
            cursor.execute("SELECT id, level_number FROM levels ORDER BY level_number ASC")
            all_levels = cursor.fetchall()

            # 3. Insert progress for each level: Level 1 = 'unlocked', rest = 'locked'
            insert_progress_sql = """
                INSERT INTO progress (user_id, level_id, status)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE status = VALUES(status)
            """
            for lvl in all_levels:
                status = 'unlocked' if lvl['level_number'] == 1 else 'locked'
                cursor.execute(insert_progress_sql, (user_id, lvl['id'], status))

            db.commit()
            flash('Profile setup complete! Welcome to Level 1.', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.rollback()
            flash(f'Error saving profile: {e}', 'error')
            return render_template(
                'profile_setup.html',
                languages=NATIVE_LANGUAGES,
                backgrounds=BACKGROUNDS,
                goals=GOALS,
                level_one=level_one,
                selected_language=native_language,
                selected_background=background,
                selected_goal=goal
            )
        finally:
            cursor.close()

    cursor.close()
    return render_template(
        'profile_setup.html',
        languages=NATIVE_LANGUAGES,
        backgrounds=BACKGROUNDS,
        goals=GOALS,
        level_one=level_one
    )


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """
    Learner profile edit route.
    Allows changing native_language, background, and goal only.
    Level is strictly read-only and cannot be altered here.
    """
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Fetch existing profile
    cursor.execute("""
        SELECT p.native_language, p.background, p.goal, p.current_level_id, l.level_number, l.title AS level_title
        FROM profiles p
        LEFT JOIN levels l ON p.current_level_id = l.id
        WHERE p.user_id = %s
    """, (user_id,))
    profile = cursor.fetchone()

    # If user has no profile yet, redirect to setup
    if not profile:
        cursor.close()
        flash('Please complete your initial profile setup first.', 'warning')
        return redirect(url_for('profile.setup'))

    if request.method == 'POST':
        native_language = request.form.get('native_language', '').strip()
        background = request.form.get('background', '').strip()
        goal = request.form.get('goal', '').strip()

        # Validation
        if not native_language or not background or not goal:
            flash('All fields are required.', 'error')
            cursor.close()
            return render_template('profile_edit.html', profile=profile, languages=NATIVE_LANGUAGES, backgrounds=BACKGROUNDS, goals=GOALS)

        if native_language not in NATIVE_LANGUAGES or background not in BACKGROUNDS or goal not in GOALS:
            flash('Invalid selection submitted.', 'error')
            cursor.close()
            return render_template('profile_edit.html', profile=profile, languages=NATIVE_LANGUAGES, backgrounds=BACKGROUNDS, goals=GOALS)

        try:
            update_sql = """
                UPDATE profiles
                SET native_language = %s, background = %s, goal = %s
                WHERE user_id = %s
            """
            cursor.execute(update_sql, (native_language, background, goal, user_id))
            db.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.rollback()
            flash(f'Error updating profile: {e}', 'error')
        finally:
            cursor.close()

    cursor.close()
    return render_template(
        'profile_edit.html',
        profile=profile,
        languages=NATIVE_LANGUAGES,
        backgrounds=BACKGROUNDS,
        goals=GOALS
    )
