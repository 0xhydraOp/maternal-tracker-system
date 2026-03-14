from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from services.password_service import hash_password


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "maternal_tracking.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Return a SQLite connection. Ensures foreign keys are enabled.
    """
    path = Path(db_path) if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """
    Create all required tables if they do not already exist.
    Schema follows PROJECT_SPEC.md.
    Also ensures there is at least one ADMIN user by creating a
    default `admin` account if the users table is empty.
    """
    conn = get_connection(db_path)
    try:
        cur = conn.cursor()

        # patients table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number INTEGER,
                patient_name TEXT NOT NULL,
                patient_id TEXT NOT NULL UNIQUE,
                mobile_number TEXT,
                village_name TEXT,
                lmp_date TEXT,
                edd_date TEXT,
                motivator_name TEXT,
                visit1 TEXT,
                visit2 TEXT,
                visit3 TEXT,
                final_visit TEXT,
                entry_date TEXT,
                record_locked INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )

        # users table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )

        # Ensure a default admin user exists if table is empty
        cur.execute("SELECT COUNT(*) FROM users;")
        user_count = cur.fetchone()[0] or 0
        if user_count == 0:
            cur.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
                """,
                ("admin", hash_password("admin123"), "ADMIN"),
            )

        # Add village_name column if it doesn't exist (migration for existing DBs)
        try:
            cur.execute("ALTER TABLE patients ADD COLUMN village_name TEXT;")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add remarks column if it doesn't exist (migration for existing DBs)
        try:
            cur.execute("ALTER TABLE patients ADD COLUMN remarks TEXT;")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # custom_motivators: names added via "Others" > "Please specify"
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS custom_motivators (
                name TEXT PRIMARY KEY,
                added_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )

        # activity_log table for admin actions
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                details TEXT,
                performed_by TEXT NOT NULL,
                performed_at TEXT NOT NULL
            );
            """
        )

        # change_logs table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS change_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_by TEXT NOT NULL,
                changed_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            );
            """
        )

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()

