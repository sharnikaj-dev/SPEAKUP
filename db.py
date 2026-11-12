"""
SPEAKUP Database Helper Module
Manages MySQL connections using mysql-connector-python without an ORM.
Reuses the connection across a single HTTP request using Flask's 'g' object.
"""

import mysql.connector
from mysql.connector import Error
from flask import g
from config import Config

def get_db_connection():
    """
    Creates and returns a raw connection to the MySQL database.
    Reads host, port, user, password, and database from Config.
    """
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )
        return connection
    except Error as e:
        print(f"[DB Error] Failed to connect to MySQL database '{Config.DB_NAME}': {e}")
        return None

def get_db():
    """
    Provides a per-request database connection stored in Flask's global 'g' object.
    If no connection exists for the current request context, one is created.
    """
    if 'db' not in g or g.db is None or not g.db.is_connected():
        g.db = get_db_connection()
    return g.db

def close_db(e=None):
    """
    Closes the database connection at the end of each request lifecycle.
    Registered with app.teardown_appcontext.
    """
    db = g.pop('db', None)
    if db is not None and db.is_connected():
        db.close()
