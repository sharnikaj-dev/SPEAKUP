# SPEAKUP - Conversational English Practice Platform

A college mini project providing an interactive, AI-driven conversational English-practice platform. Learners practice dialogues in realistic scenarios, receive instant grammar corrections and native-language explanations, and track progress across levels.

---

## Tech Stack (Step 1)
- **Frontend**: HTML5, Vanilla CSS, Vanilla JavaScript, Jinja2 Templates (No React / Tailwind / UI Frameworks).
- **Backend**: Python 3 + Flask (modular architecture using Blueprints).
- **Database**: MySQL with `mysql-connector-python` using parameterized queries (No ORM).
- **Security**: Password hashing via `werkzeug.security` (`pbkdf2:sha256`), session management via Flask sessions.
- **Configuration**: `python-dotenv` reading from `.env`.

---

## Project Structure
```text
speakup/
├── app.py                # Application factory and entry point
├── config.py             # Loads environment variables from .env
├── db.py                 # MySQL database connection helper
├── init_db.py            # Executes schema.sql and seed.sql to setup DB
├── requirements.txt      # Python dependencies
├── .env.example          # Template for environment variables
├── .gitignore            # Git exclusion rules (.env, venv, pycache)
├── schema.sql            # Full MySQL database schema (all 9 tables)
├── seed.sql              # Seed data placeholder
├── routes/
│   ├── __init__.py
│   ├── auth.py           # Register, login, logout & route decorators
│   └── main.py           # Home and dashboard routes
├── templates/
│   ├── base.html         # Base layout with navbar, alerts, footer
│   ├── index.html        # Public landing page
│   ├── register.html     # User registration page
│   ├── login.html        # User login page
│   └── dashboard.html    # Welcome dashboard placeholder
├── static/
│   ├── css/
│   │   └── style.css     # Responsive teal/blue styling & rounded cards
│   └── js/
│       └── main.js       # Alert dismissals & UX helpers
└── README.md             # Project documentation & setup instructions
```

---

## Setup Instructions (Windows)

### Prerequisites
- Python 3.8+ installed and added to `PATH`.
- MySQL Server (e.g., MySQL Community Server, XAMPP, or WAMP) running on your machine.

---

### Step 1: Open Terminal / PowerShell in the Project Directory
Navigate into the `speakup` folder:
```powershell
cd "c:\Users\user\OneDrive\Dokumen\miniproject -2\speakup"
```

---

### Step 2: Create and Activate a Python Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```
*(When activated, your prompt will show `(venv)` at the beginning).*

---

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables
Copy `.env.example` to create your local `.env` file:
```powershell
copy .env.example .env
```
Open `.env` in any text editor and adjust your MySQL credentials (especially `DB_PASSWORD`):
```ini
SECRET_KEY=speakup_dev_secret_key_change_me_in_production
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_mysql_password
DB_NAME=speakup
```

---

### Step 5: Initialize the MySQL Database
Ensure your MySQL service is running, then execute:
```powershell
python init_db.py
```
This script connects to MySQL, creates the `speakup` database, and sets up all 9 required tables (`users`, `levels`, `profiles`, `scenarios`, `conversations`, `messages`, `feedback`, `mistakes`, `progress`).

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

## Testing Checklist for Step 1

1. **Home Page (`/`)**:
   - Verify page loads with title, hero section, feature cards, and "Get Started" / "Log In" buttons.
   - Navbar shows "Home", "Log In", and "Get Started".

2. **User Registration (`/register`)**:
   - **Validation Tests**:
     - Submit empty form &rarr; expect *"All fields are required."*
     - Enter invalid email (e.g., `user@domain`) &rarr; expect *"Please enter a valid email address."*
     - Enter password shorter than 6 characters &rarr; expect *"Password must be at least 6 characters long."*
     - Enter mismatched passwords &rarr; expect *"Passwords do not match."*
   - **Successful Registration**:
     - Enter valid details (e.g., Name: `Alice`, Email: `alice@example.com`, Password: `password123`).
     - Submit &rarr; redirects to `/login` with success alert: *"Registration successful! Please log in with your credentials."*
   - **Duplicate Email Test**:
     - Try registering again with `alice@example.com` &rarr; expect *"An account with this email address already exists."*

3. **User Login (`/login`)**:
   - Enter wrong password &rarr; expect *"Invalid email or password."*
   - Enter registered credentials (`alice@example.com` / `password123`) &rarr; redirects to `/dashboard` with flash message: *"Welcome back, Alice!"*.

4. **Dashboard (`/dashboard`)**:
   - Verify welcome card displays *"Welcome back, Alice!"*.
   - Navbar now shows *"Dashboard"*, *"Hi, Alice"*, and *"Log Out"*.
   - Copy the URL `http://127.0.0.1:5000/dashboard`, log out, and try pasting it in an incognito window &rarr; redirects to `/login` with message: *"Please log in to access this page."* (verifying `@login_required` decorator).

5. **Log Out (`/logout`)**:
   - Click "Log Out" in the navbar &rarr; redirects to home page with notice: *"You have been logged out successfully."*
   - Navbar reverts to showing "Log In" and "Get Started".
