"""
Service for motivator names: admin-added custom_motivators + names from "Others" > "Please specify".
Optional MOTIVATOR_NAMES in patient_entry is usually empty; populate via Administration > Motivators.
"""
from __future__ import annotations

from typing import List

from database.init_db import get_connection


def get_all_motivator_names() -> List[str]:
    """Return MOTIVATOR_NAMES (if any) + custom_motivators from DB."""
    from ui.patient_entry import MOTIVATOR_NAMES  # lazy import to avoid circular

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM custom_motivators ORDER BY name")
        custom = [row[0] for row in cur.fetchall()]
    finally:
        conn.close()
    # Merge: base list + custom (avoid duplicates, preserve order)
    seen = set(MOTIVATOR_NAMES)
    result = list(MOTIVATOR_NAMES)
    for name in custom:
        if name and name.strip() and name not in seen:
            result.append(name.strip())
            seen.add(name.strip())
    return result


def add_custom_motivator(name: str) -> None:
    """Add a motivator name to the custom list (from Others > Please specify)."""
    name = (name or "").strip()
    if not name:
        return
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO custom_motivators (name) VALUES (?)",
            (name,),
        )
        conn.commit()
    finally:
        conn.close()
