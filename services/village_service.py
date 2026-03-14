"""Service to fetch village names from existing patient data."""
from __future__ import annotations

from typing import List

from database.init_db import get_connection


def get_all_village_names() -> List[str]:
    """Return sorted list of distinct village names from patients table."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT DISTINCT village_name FROM patients WHERE village_name IS NOT NULL AND village_name != '' ORDER BY village_name"
        )
        return [row[0] for row in cur.fetchall() if row[0]]
    finally:
        conn.close()
