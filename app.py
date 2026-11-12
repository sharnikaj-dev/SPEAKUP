"""
SPEAKUP Application Factory and Entry Point
Creates and configures the Flask application, registers blueprints,
and attaches database teardown handlers.
"""

from flask import Flask
from config import Config
from db import close_db
from routes.auth import auth_bp
from routes.main import main_bp

def create_app():
    """
    Application factory pattern.
    Instantiates Flask app, loads configuration, and registers blueprints.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure database connection is closed after every request
    app.teardown_appcontext(close_db)

    # Register modular blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    # Run development server
    app.run(debug=True, host='127.0.0.1', port=5000)
