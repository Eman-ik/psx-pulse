#!/usr/bin/env python
"""
Setup PostgreSQL database and user for PSX Fertilizer platform
Creates psx_fertilizer database and psx user
"""

import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_database():
    """Create database and user"""

    # Try different connection strategies
    strategies = [
        {
            'name': 'Trust auth (no password)',
            'params': {
                'host': 'localhost',
                'port': 5432,
                'user': 'postgres',
                'database': 'postgres',
            }
        },
        {
            'name': 'Postgres with empty password',
            'params': {
                'host': 'localhost',
                'port': 5432,
                'user': 'postgres',
                'password': '',
                'database': 'postgres',
            }
        },
        {
            'name': 'Postgres with default password',
            'params': {
                'host': 'localhost',
                'port': 5432,
                'user': 'postgres',
                'password': 'postgres',
                'database': 'postgres',
            }
        }
    ]

    conn = None
    for strategy in strategies:
        try:
            print(f"\n[TRY] {strategy['name']}...")
            conn = psycopg2.connect(**strategy['params'])
            print(f"[OK] Connected as postgres")
            break
        except Exception as e:
            print(f"[FAIL] {str(e)[:80]}")
            continue

    if not conn:
        print("\n[ERROR] Could not connect to PostgreSQL as postgres user")
        print("Make sure PostgreSQL is running and accessible")
        sys.exit(1)

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        # Check if psx user exists
        cursor.execute("SELECT 1 FROM pg_user WHERE usename = 'psx'")
        user_exists = cursor.fetchone()

        if not user_exists:
            print("\n[CREATE] User 'psx'...")
            cursor.execute("CREATE USER psx WITH PASSWORD 'psx' CREATEDB")
            print("[OK] User created")
        else:
            print("\n[EXISTS] User 'psx' already exists")

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'psx_fertilizer'")
        db_exists = cursor.fetchone()

        if not db_exists:
            print("[CREATE] Database 'psx_fertilizer'...")
            cursor.execute("CREATE DATABASE psx_fertilizer OWNER psx")
            print("[OK] Database created")
        else:
            print("[EXISTS] Database 'psx_fertilizer' already exists")

        # Grant privileges
        print("[GRANT] Granting privileges...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE psx_fertilizer TO psx")
        print("[OK] Privileges granted")

        cursor.close()

        # Now connect to the database and set schema privileges
        print("\n[SETUP] Setting schema privileges...")
        conn2 = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='',
            database='psx_fertilizer'
        ) if 'postgres' in strategy['name'] else None

        if not conn2:
            # Try with password
            try:
                conn2 = psycopg2.connect(
                    host='localhost',
                    port=5432,
                    user='postgres',
                    password='postgres',
                    database='psx_fertilizer'
                )
            except:
                conn2 = conn  # Fallback to existing connection

        if conn2:
            conn2.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor2 = conn2.cursor()

            cursor2.execute("GRANT ALL PRIVILEGES ON SCHEMA public TO psx")
            cursor2.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO psx")
            cursor2.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO psx")
            cursor2.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO psx")

            cursor2.close()
            conn2.close()
            print("[OK] Schema privileges set")

        conn.close()

        print("\n" + "="*60)
        print("DATABASE SETUP COMPLETE!")
        print("="*60)
        print("\nConnection Details:")
        print("  Host: localhost")
        print("  Port: 5432")
        print("  Database: psx_fertilizer")
        print("  User: psx")
        print("  Password: psx")
        print("\nNow run: python backend/scripts/ingest_mock_data.py")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n[ERROR] Setup failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    setup_database()
