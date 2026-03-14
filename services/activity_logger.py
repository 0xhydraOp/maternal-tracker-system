"""
Activity logger for admin actions.
Logs user add/edit/delete, patient delete, settings changes.
"""
from __future__ import annotations

from datetime import datetime

from database.init_db import get_connection


def log_admin_activity(action: str, details: str, username: str) -> None:
    """Log an admin action to the activity_log table."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO activity_log (action, details, performed_by, performed_at)
            VALUES (?, ?, ?, ?)
            """,
            (action, details, username, datetime.now().isoformat()),
        )
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()
