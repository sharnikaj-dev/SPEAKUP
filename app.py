import json
import os
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, abort, jsonify)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

from llm import analyze_turn, llm_ready, LLMError  # noqa: E402
from retry import retry_passed  # noqa: E402

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Test each connection before use and refresh old ones, so a MySQL restart
# doesn't leave Flask holding dead connections.
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True,
                                           "pool_recycle": 280}
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

db = SQLAlchemy(app)

# ---------- Options for the profile form ----------
LANGUAGES = ["Tamil", "Hindi", "Telugu", "Malayalam", "Kannada", "Other"]
LEVELS = ["Beginner", "Intermediate", "Advanced"]
GOALS = ["Daily communication", "Academic communication",
         "Workplace communication", "Interview preparation"]
TRAINERS = [
    {"id": "male_human",   "name": "Alex",  "icon": "👨‍🏫", "desc": "Calm and professional"},
    {"id": "female_human", "name": "Maya",  "icon": "👩‍🏫", "desc": "Warm and encouraging"},
    {"id": "dog",          "name": "Buddy", "icon": "🐶",  "desc": "Playful and friendly"},
    {"id": "cat",          "name": "Luna",  "icon": "🐱",  "desc": "Cool and gentle"},
    {"id": "cartoon",      "name": "Zippy", "icon": "🤖",  "desc": "Fun and energetic"},
]
TRAINER_IDS = {t["id"] for t in TRAINERS}

# Icons are kept in Python (not in the database) for each level number
LEVEL_ICONS = {1: "👋", 2: "☕", 3: "🎓", 4: "🎤", 5: "🌟"}

# ---------- Chat limits (protects your AI bill) ----------
MAX_MESSAGE_CHARS = 500
RETRY_LIMIT = 3          # tries before the trainer shows the answer and moves on
MAX_USER_MESSAGES_PER_DAY = int(os.environ.get("MAX_MESSAGES_PER_DAY", "100"))
FEEDBACK_KEYS = ("has_mistake", "category", "original", "corrected",
                 "explanation_english", "explanation_native", "better_version")


# ---------- Models ----------
class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    profile = db.relationship("Profile", backref="user", uselist=False)


class Profile(db.Model):
    __tablename__ = "profiles"
    profile_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"),
                        unique=True, nullable=False)
    native_language = db.Column(db.String(50), nullable=False)
    english_level = db.Column(db.String(20), nullable=False)
    learning_goal = db.Column(db.String(50), nullable=False)
    trainer = db.Column(db.String(20), nullable=False)


class Level(db.Model):
    __tablename__ = "levels"
    level_id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    scenarios = db.relationship("Scenario", backref="level",
                                order_by="Scenario.scenario_id")


class Scenario(db.Model):
    __tablename__ = "scenarios"
    scenario_id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey("levels.level_id"),
                         nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    opening_line = db.Column(db.String(255), nullable=False)


class LevelProgress(db.Model):
    __tablename__ = "level_progress"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"),
                        nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey("levels.level_id"),
                         nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    completed_at = db.Column(db.DateTime)
    __table_args__ = (db.UniqueConstraint("user_id", "level_id",
                                          name="uq_user_level"),)


class PracticeSession(db.Model):
    __tablename__ = "practice_sessions"
    session_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"),
                        nullable=False)
    scenario_id = db.Column(db.Integer, db.ForeignKey("scenarios.scenario_id"),
                            nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    scenario = db.relationship("Scenario")
    messages = db.relationship("Message", backref="practice_session",
                               order_by="Message.message_id")


class Message(db.Model):
    __tablename__ = "conversation_messages"
    message_id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer,
                           db.ForeignKey("practice_sessions.session_id"),
                           nullable=False)
    sender = db.Column(db.String(10), nullable=False)   # "trainer" or "user"
    text = db.Column(db.Text, nullable=False)
    feedback_json = db.Column(db.Text)                  # feedback on a user message
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Mistake(db.Model):
    __tablename__ = "mistakes"
    mistake_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("practice_sessions.session_id"),
                           nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey("conversation_messages.message_id"))
    category = db.Column(db.String(30), nullable=False)
    learner_text = db.Column(db.Text, nullable=False)        # what the learner said
    original_text = db.Column(db.Text)                       # the wrong part
    corrected_text = db.Column(db.Text, nullable=False)
    explanation_english = db.Column(db.Text)
    explanation_native = db.Column(db.Text)
    pending_reply = db.Column(db.Text)       # trainer reply shown after the retry
    status = db.Column(db.String(10), nullable=False, default="pending")  # pending / fixed / skipped / missed
    attempts = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)


CATEGORY_LABELS = {"grammar": "Grammar", "vocabulary": "Vocabulary",
                   "sentence_formation": "Sentence formation"}


# ---------- Starting data for levels and scenarios ----------
SEED = [
    {
        "number": 1, "name": "Self Introduction",
        "description": "Introduce yourself: name, education, background, interests and goals.",
        "scenarios": [
            ("Introduce yourself", "Say who you are in a few clear sentences.",
             "Hi! Can you introduce yourself?"),
            ("Talk about your education", "Explain what you study and where.",
             "Nice to meet you! What are you studying right now?"),
            ("Share your interests and goals", "Tell me what you enjoy and what you want to achieve.",
             "What are your interests, and what are your goals for the future?"),
        ],
    },
    {
        "number": 2, "name": "Daily Conversation",
        "description": "Everyday situations: asking for information, talking about your day, casual chat.",
        "scenarios": [
            ("Talk about your day", "Describe what you did today or yesterday.",
             "Hi! How was your day? Can you tell me what you did?"),
            ("Ask for information", "Ask politely for directions, timings or help.",
             "Imagine you are at a bus stop and need to find a place. What would you ask me?"),
            ("Casual conversation", "Chat about hobbies, food, movies or weekends.",
             "What do you usually do on weekends?"),
        ],
    },
    {
        "number": 3, "name": "Academic & Workplace",
        "description": "College discussions, team communication, meetings and professional questions.",
        "scenarios": [
            ("College conversation", "Talk to a professor or classmate about your studies.",
             "Hello! I'm your professor. How is your project going so far?"),
            ("Team meeting", "Share an update with your team.",
             "We're in a team meeting. Can you give us a short update on your work?"),
            ("Ask questions professionally", "Ask for clarification in a polite, clear way.",
             "I just explained a new task to you. What questions do you have?"),
        ],
    },
    {
        "number": 4, "name": "Interview Practice",
        "description": "Campus and HR interview practice, including project explanation.",
        "scenarios": [
            ("Tell me about yourself", "The classic opening interview question.",
             "Good morning! Please tell me about yourself."),
            ("Strengths and weaknesses", "Describe your strengths and how you handle weaknesses.",
             "What would you say are your greatest strengths and one area you want to improve?"),
            ("Explain your project", "Describe a project you built, clearly and simply.",
             "I see you worked on a project. Can you explain it to me?"),
            ("HR round", "Answer common HR questions confidently.",
             "Why do you want to join our company?"),
        ],
    },
    {
        "number": 5, "name": "Real-World Challenges",
        "description": "Harder situations: unexpected questions, explaining problems, asking for help, giving opinions.",
        "scenarios": [
            ("Handle an unexpected question", "Stay calm and respond clearly to a surprise question.",
             "Here's a surprise question: if you could change one thing about your college, what would it be?"),
            ("Explain a problem", "Describe a problem and what you tried.",
             "Something went wrong with your task. Can you explain what happened?"),
            ("Request help", "Ask for help politely and specifically.",
             "You are stuck and need support from a senior. What would you say?"),
            ("Give your opinion", "Share and support your opinion.",
             "Do you think students should use AI tools for studying? Why or why not?"),
        ],
    },
]


def seed_data():
    """Insert levels and scenarios the first time the app runs."""
    if Level.query.first():
        return
    for item in SEED:
        level = Level(number=item["number"], name=item["name"],
                      description=item["description"])
        for title, description, opening in item["scenarios"]:
            level.scenarios.append(Scenario(title=title,
                                            description=description,
                                            opening_line=opening))
        db.session.add(level)
    db.session.commit()


# ---------- Helpers ----------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


def trainer_for(profile):
    return next((t for t in TRAINERS if t["id"] == profile.trainer),
                TRAINERS[0])


def completed_numbers(user_id):
    """Set of level numbers this user has completed."""
    rows = (db.session.query(Level.number)
            .join(LevelProgress, LevelProgress.level_id == Level.level_id)
            .filter(LevelProgress.user_id == user_id,
                    LevelProgress.completed.is_(True))
            .all())
    return {r[0] for r in rows}


def level_status(level, done):
    """completed / unlocked / locked"""
    if level.number in done:
        return "completed"
    if level.number == 1 or (level.number - 1) in done:
        return "unlocked"
    return "locked"


def render_setup(profile):
    return render_template("profile_setup.html", profile=profile,
                           languages=LANGUAGES, levels=LEVELS,
                           goals=GOALS, trainers=TRAINERS)


# ---------- Public pages ----------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or len(password) < 8:
            flash("Please fill all fields. Password needs at least 8 characters.")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.")
            return render_template("register.html")

        user = User(name=name, email=email,
                    password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()

        session.clear()
        session["user_id"] = user.user_id
        return redirect(url_for("profile_setup"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.user_id
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------- Logged-in pages ----------
@app.route("/profile/setup", methods=["GET", "POST"])
@login_required
def profile_setup():
    user = current_user()
    profile = user.profile

    if request.method == "POST":
        language = request.form.get("native_language")
        level = request.form.get("english_level")
        goal = request.form.get("learning_goal")
        trainer = request.form.get("trainer")

        if (language not in LANGUAGES or level not in LEVELS
                or goal not in GOALS or trainer not in TRAINER_IDS):
            flash("Please choose an option in every section.")
            return render_setup(profile)

        if profile is None:
            profile = Profile(user_id=user.user_id)
            db.session.add(profile)

        profile.native_language = language
        profile.english_level = level
        profile.learning_goal = goal
        profile.trainer = trainer
        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_setup(profile)


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    if not user.profile:
        return redirect(url_for("profile_setup"))

    done = completed_numbers(user.user_id)
    levels = Level.query.order_by(Level.number).all()
    levels_view = [
        {"level": lv,
         "icon": LEVEL_ICONS.get(lv.number, "⭐"),
         "status": level_status(lv, done)}
        for lv in levels
    ]
    return render_template("dashboard.html", profile=user.profile,
                           trainer=trainer_for(user.profile),
                           levels_view=levels_view)


@app.route("/levels/<int:level_id>")
@login_required
def level_detail(level_id):
    user = current_user()
    if not user.profile:
        return redirect(url_for("profile_setup"))

    level = db.session.get(Level, level_id)
    if level is None:
        abort(404)

    status = level_status(level, completed_numbers(user.user_id))
    if status == "locked":
        flash(f"Complete Level {level.number - 1} to unlock Level {level.number}.")
        return redirect(url_for("dashboard"))

    return render_template("level.html", level=level, status=status,
                           icon=LEVEL_ICONS.get(level.number, "⭐"),
                           trainer=trainer_for(user.profile))


@app.route("/scenario/<int:scenario_id>")
@login_required
def scenario_start(scenario_id):
    user = current_user()
    if not user.profile:
        return redirect(url_for("profile_setup"))

    scenario = db.session.get(Scenario, scenario_id)
    if scenario is None:
        abort(404)

    status = level_status(scenario.level, completed_numbers(user.user_id))
    if status == "locked":
        flash("That level is still locked.")
        return redirect(url_for("dashboard"))

    return render_template("scenario.html", scenario=scenario,
                           trainer=trainer_for(user.profile))


# ---------- Conversation ----------
def get_owned_session(session_id, user):
    ps = db.session.get(PracticeSession, session_id)
    if ps is None or ps.user_id != user.user_id:
        abort(404)
    return ps


def messages_today(user_id):
    start = datetime.utcnow().replace(hour=0, minute=0, second=0,
                                      microsecond=0)
    return (db.session.query(Message)
            .join(PracticeSession,
                  Message.session_id == PracticeSession.session_id)
            .filter(PracticeSession.user_id == user_id,
                    Message.sender == "user",
                    or_(Message.feedback_json.is_(None),
                        Message.feedback_json.notlike('%"retry"%')),
                    Message.created_at >= start)
            .count())


def pending_mistake(ps):
    return Mistake.query.filter_by(session_id=ps.session_id,
                                   status="pending").first()


def finish_mistake(mistake, status):
    mistake.status = status
    mistake.resolved_at = datetime.utcnow()


def reveal_reply(ps, mistake):
    """Show the trainer reply that was held back until the retry was done."""
    reply = mistake.pending_reply or "Let's keep going! Tell me more."
    db.session.add(Message(session_id=ps.session_id, sender="trainer", text=reply))
    mistake.pending_reply = None
    return reply


def handle_retry(ps, mistake, text):
    mistake.attempts += 1
    passed = retry_passed(text, mistake.learner_text, mistake.corrected_text)

    if passed:
        mode, note = "retry_passed", "✓ Well done! That's correct."
        finish_mistake(mistake, "fixed")
    elif mistake.attempts >= RETRY_LIMIT:
        mode = "retry_gave_up"
        note = f"No problem. The correct sentence is: {mistake.corrected_text}"
        finish_mistake(mistake, "missed")
    else:
        mode = "retry_again"
        note = f"Almost! Try again: {mistake.corrected_text}"

    fb = {"retry": True, "passed": passed, "note": note}
    db.session.add(Message(session_id=ps.session_id, sender="user", text=text,
                           feedback_json=json.dumps(fb)))
    reply = reveal_reply(ps, mistake) if mode != "retry_again" else None
    db.session.commit()
    return jsonify(mode=mode, note=note, reply=reply,
                   target=mistake.corrected_text)


def message_views(ps):
    views = []
    for m in ps.messages:
        feedback = None
        if m.feedback_json:
            try:
                feedback = json.loads(m.feedback_json)
            except ValueError:
                feedback = None
        views.append({"sender": m.sender, "text": m.text,
                      "feedback": feedback})
    return views


@app.route("/scenario/<int:scenario_id>/start", methods=["POST"])
@login_required
def start_session(scenario_id):
    user = current_user()
    if not user.profile:
        return redirect(url_for("profile_setup"))

    scenario = db.session.get(Scenario, scenario_id)
    if scenario is None:
        abort(404)
    if level_status(scenario.level, completed_numbers(user.user_id)) == "locked":
        flash("That level is still locked.")
        return redirect(url_for("dashboard"))

    ps = PracticeSession(user_id=user.user_id, scenario_id=scenario.scenario_id)
    db.session.add(ps)
    db.session.flush()
    db.session.add(Message(session_id=ps.session_id, sender="trainer",
                           text=scenario.opening_line))
    db.session.commit()
    return redirect(url_for("practice_session", session_id=ps.session_id))


@app.route("/session/<int:session_id>")
@login_required
def practice_session(session_id):
    user = current_user()
    if not user.profile:
        return redirect(url_for("profile_setup"))
    ps = get_owned_session(session_id, user)
    return render_template("session.html", ps=ps, scenario=ps.scenario,
                           messages=message_views(ps),
                           trainer=trainer_for(user.profile),
                           native_language=user.profile.native_language,
                           demo=not llm_ready(),
                           max_chars=MAX_MESSAGE_CHARS,
                           pending=pending_mistake(ps))


@app.route("/session/<int:session_id>/message", methods=["POST"])
@login_required
def send_message(session_id):
    user = current_user()
    if not user.profile:
        return jsonify(error="Please complete your profile first."), 400
    ps = get_owned_session(session_id, user)
    if ps.status != "active":
        return jsonify(error="This session has ended."), 400

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify(error="Please type something first."), 400
    if len(text) > MAX_MESSAGE_CHARS:
        return jsonify(error=f"Please keep it under {MAX_MESSAGE_CHARS} characters."), 400

    # A mistake is waiting for a retry: check the retry, no AI call needed.
    pending = pending_mistake(ps)
    if pending:
        return handle_retry(ps, pending, text)

    if messages_today(user.user_id) >= MAX_USER_MESSAGES_PER_DAY:
        return jsonify(error="You've reached today's practice limit. Come back tomorrow!"), 429

    history = [{"sender": m.sender, "text": m.text} for m in ps.messages]
    profile = user.profile
    trainer = trainer_for(profile)

    try:
        result = analyze_turn(
            trainer=trainer,
            scenario={"title": ps.scenario.title,
                      "description": ps.scenario.description},
            profile={"native_language": profile.native_language,
                     "english_level": profile.english_level,
                     "learning_goal": profile.learning_goal},
            history=history,
            learner_text=text,
        )
    except LLMError:
        return jsonify(error="Your trainer is unavailable right now. Please try again in a moment."), 503

    feedback = {k: result.get(k, "") for k in FEEDBACK_KEYS}
    feedback["has_mistake"] = bool(feedback["has_mistake"])
    demo = bool(result.get("demo"))

    user_msg = Message(session_id=ps.session_id, sender="user", text=text,
                       feedback_json=json.dumps(feedback))
    db.session.add(user_msg)

    if feedback["has_mistake"]:
        # Hold the trainer's reply back until the learner retries the sentence.
        db.session.flush()
        db.session.add(Mistake(
            user_id=user.user_id, session_id=ps.session_id,
            message_id=user_msg.message_id,
            category=feedback["category"], learner_text=text,
            original_text=feedback["original"],
            corrected_text=feedback["corrected"],
            explanation_english=feedback["explanation_english"],
            explanation_native=feedback["explanation_native"],
            pending_reply=result["reply"]))
        db.session.commit()
        return jsonify(mode="needs_retry", feedback=feedback,
                       target=feedback["corrected"], reply=None, demo=demo)

    db.session.add(Message(session_id=ps.session_id, sender="trainer",
                           text=result["reply"]))
    db.session.commit()
    return jsonify(mode="normal", feedback=feedback, reply=result["reply"],
                   demo=demo)


@app.route("/session/<int:session_id>/skip-retry", methods=["POST"])
@login_required
def skip_retry(session_id):
    user = current_user()
    ps = get_owned_session(session_id, user)
    pending = pending_mistake(ps)
    if not pending:
        return jsonify(error="There is nothing to skip."), 400
    finish_mistake(pending, "skipped")
    reply = reveal_reply(ps, pending)
    db.session.commit()
    return jsonify(mode="skipped", reply=reply)


@app.route("/session/<int:session_id>/end", methods=["POST"])
@login_required
def end_session(session_id):
    user = current_user()
    ps = get_owned_session(session_id, user)
    if ps.status == "active":
        ps.status = "completed"
        ps.ended_at = datetime.utcnow()
        open_mistake = pending_mistake(ps)
        if open_mistake:
            finish_mistake(open_mistake, "skipped")
        db.session.commit()
    flash("Session saved. Great practice!")
    return redirect(url_for("level_detail", level_id=ps.scenario.level_id))


@app.route("/mistakes")
@login_required
def mistakes_page():
    user = current_user()
    if not user.profile:
        return redirect(url_for("profile_setup"))
    items = (Mistake.query.filter_by(user_id=user.user_id)
             .order_by(Mistake.created_at.desc()).limit(500).all())

    cats = {}
    for m in items:
        c = cats.setdefault(m.category, {
            "label": CATEGORY_LABELS.get(m.category, m.category.title()),
            "count": 0, "fixed": 0})
        c["count"] += 1
        c["fixed"] += 1 if m.status == "fixed" else 0
    categories = sorted(cats.values(), key=lambda c: c["count"], reverse=True)
    top = categories[0]["count"] if categories else 1
    for c in categories:
        c["pct"] = round(100 * c["count"] / top)

    return render_template(
        "mistakes.html", items=items[:30], total=len(items),
        fixed=sum(1 for m in items if m.status == "fixed"),
        categories=categories, labels=CATEGORY_LABELS,
        language=user.profile.native_language)


# ---------- Testing helpers (only work when debug=True) ----------
@app.route("/dev/complete-level/<int:level_id>", methods=["POST"])
@login_required
def dev_complete_level(level_id):
    if not app.debug:
        abort(404)
    user = current_user()
    level = db.session.get(Level, level_id)
    if level is None:
        abort(404)
    if level_status(level, completed_numbers(user.user_id)) == "locked":
        return redirect(url_for("dashboard"))

    progress = LevelProgress.query.filter_by(user_id=user.user_id,
                                             level_id=level_id).first()
    if progress is None:
        progress = LevelProgress(user_id=user.user_id, level_id=level_id)
        db.session.add(progress)
    progress.completed = True
    progress.completed_at = datetime.utcnow()
    db.session.commit()
    flash(f"(Test) Level {level.number} marked complete.")
    return redirect(url_for("dashboard"))


@app.route("/dev/reset-progress", methods=["POST"])
@login_required
def dev_reset_progress():
    if not app.debug:
        abort(404)
    LevelProgress.query.filter_by(user_id=current_user().user_id).delete()
    db.session.commit()
    flash("(Test) Progress reset.")
    return redirect(url_for("dashboard"))


with app.app_context():
    db.create_all()
    seed_data()


if __name__ == "__main__":
    app.run(debug=True)