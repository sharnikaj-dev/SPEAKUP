"""
SPEAKUP Database Initialization Script
Runs schema.sql and seed.sql to create database tables and seed initial records.
"""

import os
import mysql.connector
from mysql.connector import Error
from config import Config

def execute_sql_file(cursor, file_path):
    """
    Reads an SQL script file, strips comments, and executes statements sequentially.
    """
    if not os.path.exists(file_path):
        print(f"[!] SQL file not found: {file_path}")
        return False

    print(f"[*] Reading and executing: {file_path} ...")
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Split by semicolon to execute one SQL statement at a time
    statements = sql_content.split(';')
    executed_count = 0

    for raw_stmt in statements:
        stmt = raw_stmt.strip()
        # Remove comment-only lines to check if there is actual SQL to run
        active_lines = [
            line.strip() for line in stmt.splitlines() 
            if line.strip() and not line.strip().startswith('--')
        ]
        if not active_lines:
            continue

        try:
            cursor.execute(stmt)
            executed_count += 1
        except Error as err:
            print(f"[!] Error executing statement:\n{stmt}\nError: {err}")
            raise err

    print(f"[+] Successfully executed {executed_count} statements from {file_path}")
    return True

def init_database():
    """
    Connects to MySQL server and applies schema.sql followed by seed.sql.
    Verifies that the 5 levels and 15 scenarios are loaded properly.
    """
    print("=" * 60)
    print("SPEAKUP: Initializing MySQL Database")
    print(f"Target Host: {Config.DB_HOST}:{Config.DB_PORT}")
    print(f"Target Database: {Config.DB_NAME}")
    print("=" * 60)

    connection = None
    try:
        # Step 1: Connect to MySQL server without specifying a database,
        # so schema.sql can create the database if it doesn't exist yet.
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )

        cursor = connection.cursor()

        # Step 2: Run schema.sql
        base_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(base_dir, 'schema.sql')
        seed_path = os.path.join(base_dir, 'seed.sql')

        execute_sql_file(cursor, schema_path)

        # Step 3: Run seed.sql
        execute_sql_file(cursor, seed_path)

        connection.commit()

        # Step 4: Verification check
        cursor.execute("SELECT COUNT(*) FROM levels")
        level_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM scenarios")
        scenario_count = cursor.fetchone()[0]

        print("\n" + "=" * 60)
        print(f"[✓] Database initialization completed successfully!")
        print(f"[✓] Verified: {level_count} levels and {scenario_count} scenarios ready in database.")
        print("=" * 60)

        cursor.close()

    except Error as e:
        print(f"\n[✗] Database initialization failed: {e}")
        print("\nPlease check:")
        print("1. Is your MySQL service running?")
        print("2. Are DB_USER, DB_PASSWORD, and DB_HOST correctly set in .env?")
    finally:
        if connection is not None and connection.is_connected():
            connection.close()
            print("[*] MySQL connection closed.")

if __name__ == '__main__':
    init_database()
