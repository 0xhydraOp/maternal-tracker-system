"""
Remove all dummy/seed patient data from the database.
Keeps: users, custom_motivators, activity_log structure.
Clears: patients, change_logs (patient-related).

Run: python -m scripts.clear_dummy_data
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.init_db import get_connection


def main() -> int:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM patients")
        before = cur.fetchone()[0] or 0

        cur.execute("DELETE FROM change_logs")
        change_logs_deleted = cur.rowcount
        cur.execute("DELETE FROM patients")
        patients_deleted = cur.rowcount

        conn.commit()
        print(f"Deleted {patients_deleted} patients and {change_logs_deleted} change log entries.")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
