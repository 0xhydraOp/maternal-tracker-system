from __future__ import annotations

from typing import Optional

from database.init_db import get_connection


def log_change(
    patient_id: str,
    field_name: str,
    old_value: Optional[str],
    new_value: Optional[str],
    changed_by: str,
) -> None:
    """
    Insert a single change record into the change_logs table.
    """
    if old_value == new_value:
        return

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO change_logs (
                patient_id,
                field_name,
                old_value,
                new_value,
                changed_by
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (patient_id, field_name, old_value, new_value, changed_by),
        )
        conn.commit()
    finally:
        conn.close()

