"""
Fix invalid visit dates in the database.
- visit1 must equal entry_date
- visit2 >= visit1
- visit3 >= visit2
- final_visit >= visit3
- entry_date cannot be in future (for new: 1st=entry, 2nd=future)

Run: python -m scripts.fix_visit_dates
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.init_db import get_connection
from utils.date_utils import parse_date, format_for_storage


def parse_d(s: str | None) -> date | None:
    if not s:
        return None
    return parse_date(s)


def main() -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT patient_id, entry_date, visit1, visit2, visit3, final_visit
        FROM patients
        """
    )
    rows = cur.fetchall()
    fixed = 0
    today = date.today()

    for patient_id, entry_str, v1_str, v2_str, v3_str, final_str in rows:
        entry_d = parse_d(entry_str)
        v1_d = parse_d(v1_str)
        v2_d = parse_d(v2_str)
        v3_d = parse_d(v3_str)
        final_d = parse_d(final_str)

        updates = {}
        needs_fix = False

        # visit1 must equal entry_date
        if entry_d:
            if v1_d != entry_d:
                updates["visit1"] = format_for_storage(entry_d)
                needs_fix = True
            v1_d = entry_d  # use for subsequent checks
        else:
            # Bad: no entry_date - use today
            if v1_d:
                updates["entry_date"] = format_for_storage(v1_d)
                entry_d = v1_d
                needs_fix = True
            else:
                updates["entry_date"] = format_for_storage(today)
                updates["visit1"] = format_for_storage(today)
                entry_d = today
                v1_d = today
                needs_fix = True

        # visit2 >= visit1
        if v2_d and v1_d and v2_d < v1_d:
            updates["visit2"] = None  # Clear invalid
            v2_d = None
            needs_fix = True

        # visit3 >= visit2 (or visit1 if no visit2)
        prev = v2_d or v1_d
        if v3_d and prev and v3_d < prev:
            updates["visit3"] = None
            v3_d = None
            needs_fix = True

        # final_visit >= visit3 (or visit2 or visit1)
        prev = v3_d or v2_d or v1_d
        if final_d and prev and final_d < prev:
            updates["final_visit"] = None
            needs_fix = True

        if needs_fix and updates:
            set_clauses = []
            params = []
            for col, val in updates.items():
                set_clauses.append(f"{col} = ?")
                params.append(val)
            params.append(patient_id)
            cur.execute(
                f"UPDATE patients SET {', '.join(set_clauses)} WHERE patient_id = ?",
                params,
            )
            fixed += 1
            print(f"Fixed {patient_id}: {updates}")

    conn.commit()
    conn.close()
    print(f"\nFixed {fixed} patient record(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
