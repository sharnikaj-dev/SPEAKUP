"""
SPEAKUP Configuration Module
Reads environment variables from .env to keep secrets secure.
"""

import os
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()

class Config:
    """Application configuration class loaded into Flask app.config."""
    
    # Secret key for session cookie signing and CSRF protection
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key-change-me')
    
    # Database connection parameters
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'speakup')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
