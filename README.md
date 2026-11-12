# SPEAKUP - Conversational English Practice Platform

A college mini project providing an interactive, AI-driven conversational English-practice platform. Learners practice dialogues in realistic scenarios, receive instant grammar corrections and native-language explanations, and track progress across levels.

---

## Tech Stack
- **Frontend**: HTML5, Vanilla CSS, Vanilla JavaScript, Jinja2 Templates (No React / Tailwind / UI Frameworks).
- **Backend**: Python 3 + Flask (modular architecture using Blueprints).
- **Database**: MySQL with `mysql-connector-python` using parameterized queries (No ORM).
- **Security**: Password hashing via `werkzeug.security` (`pbkdf2:sha256`), session management via Flask sessions.
- **Configuration**: `python-dotenv` reading from `.env`.

---

## Project Structure
```text
speakup/
├── app.py                     # Application factory and entry point
├── config.py                  # Loads environment variables from .env
├── db.py                      # MySQL database connection helper
├── init_db.py                 # Executes schema.sql and seed.sql to setup DB
├── requirements.txt           # Python dependencies
├── .env.example               # Template for environment variables
├── .gitignore                 # Git exclusion rules (.env, venv, pycache)
├── schema.sql                 # Full MySQL database schema (all 9 tables)
├── seed.sql                   # 5 Levels & 15 Scenarios (safe to rerun)
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Register, login, logout & route decorators
│   ├── main.py                # Home, Dashboard, and Level scenario views
│   └── profile.py             # Profile setup & edit blueprint (/profile)
├── templates/
│   ├── base.html              # Base layout with navbar, alerts, footer
│   ├── index.html             # Public landing page
│   ├── register.html          # User registration page
│   ├── login.html             # User login page
│   ├── profile_setup.html     # Learner profile onboarding
│   ├── profile_edit.html      # Learner profile settings
│   ├── dashboard.html         # Curriculum dashboard with 5 levels
│   └── level.html             # Level scenarios and AI partner previews
├── static/
│   ├── css/
│   │   └── style.css          # Responsive calm teal/blue design system
│   └── js/
│       └── main.js            # Alert dismissals & UX helpers
└── README.md                  # Project documentation & setup instructions
```

---

## Setup Instructions (Windows)

### Prerequisites
- Python 3.8+ installed and added to `PATH`.
- MySQL Server (e.g., MySQL Community Server, XAMPP, or WAMP) running on your machine.

---

### Step 1: Open Terminal / PowerShell in the Project Directory
```powershell
cd "c:\Users\user\OneDrive\Dokumen\miniproject -2\speakup"
```

---

### Step 2: Create and Activate a Python Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

---

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables
Copy `.env.example` to create your local `.env` file if you haven't already:
```powershell
copy .env.example .env
```
Ensure your MySQL credentials in `.env` are correct:
```ini
SECRET_KEY=speakup_dev_secret_key_change_me_in_production
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
DB_NAME=speakup
```

---

### Step 5: Run Database Initialization (Seed Levels & Scenarios)
Run the initialization script to populate all 5 levels and 15 scenarios:
```powershell
python init_db.py
```
*(This script is idempotent: running it again will safely update rows without creating duplicate levels or scenarios).*

---

### Step 6: Run the Flask Application
```powershell
python app.py
```
Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## Step 2 Verification & Testing Checklist

1. **New User Registration & Profile Redirection**:
   - Register a new account at `/register` (e.g. `user1@example.com`).
   - Log in with the credentials.
   - **Verification**: You are automatically redirected to `/profile/setup` with a prompt: *"Please complete your profile setup to get started."*
   - Attempting to visit `/dashboard` directly redirects you back to `/profile/setup`.

2. **Profile Setup Submission (`/profile/setup`)**:
   - Select:
     - **Native Language**: `Tamil` (or Hindi, Telugu, etc.)
     - **Background**: `College student`
     - **Goal**: `Interview preparation`
     - Note that **Starting Level** is fixed to **Level 1 (Self-Introduction)**.
   - Submit the form.
   - **Verification**:
     - Database inserts profile with `current_level_id = 1`.
     - Database inserts progress rows for all 5 levels (Level 1 is `unlocked`, Levels 2 to 5 are `locked`).
     - You are redirected to `/dashboard` with a success message: *"Profile setup complete! Welcome to Level 1."*

3. **Dashboard Curriculum View (`/dashboard`)**:
   - **Welcome Header**: Shows user's name, native language (`Tamil`), background (`College student`), and goal (`Interview preparation`).
   - **Progress Card**: Shows *"0 of 5 levels completed"* with a 0% progress bar.
   - **Levels Grid**: Displays all 5 levels:
     - **Level 1 (Self-Introduction)**: Shows **🔓 Unlocked** badge, 3 scenarios, and an active **View Scenarios &rarr;** button.
     - **Levels 2 to 5**: Greyed out with **🔒 Locked** badges and disabled **Locked 🔒** buttons.

4. **Profile Editing (`/profile/edit`)**:
   - Click **Edit Profile** in the dashboard header (or in the navbar).
   - Change your native language to `Hindi` or goal to `Daily conversation`.
   - Submit the form.
   - **Verification**: Changes reflect on the dashboard banner. The current level remains unchanged.

5. **Level Scenarios Page (`/level/1`)**:
   - On the dashboard, click **View Scenarios &rarr;** on Level 1.
   - **Verification**: Opens `/level/1` displaying:
     - Back button to Dashboard (`&larr; Back to Dashboard`).
     - Level banner: *"Level 1: Self-Introduction"*, description, and **🔓 Unlocked** badge.
     - 3 Scenario Cards:
       1. *Meeting a New Classmate*
       2. *Introducing Yourself at a Club*
       3. *Introducing Yourself to a Teacher*
     - Each card displays the scenario description, AI persona prompt, and the AI's opening conversation line.
     - Action buttons are marked with *"Start Conversation (Coming in Step 3)"*.

6. **Locked Level Security Check**:
   - In the browser address bar, try navigating directly to `http://127.0.0.1:5000/level/2` (or `/level/3`, `/level/4`, `/level/5`).
   - **Verification**: You are immediately blocked, redirected back to `/dashboard`, and shown a warning flash message:
     *"Level 2 (Daily Conversation) is locked. Complete previous levels to unlock it."*
