"""
Import patient records from Excel files.
Adds records to the database and saves a copy of the Excel file to the backup folder.
"""
from __future__ import annotations

import shutil
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from database.init_db import get_connection
from services.backup_service import get_backup_dir_path
from services.location_service import get_district_name
from utils.date_utils import parse_date, format_for_storage, EMPTY_DATE_SENTINEL, EMPTY_DATE_SENTINEL_ALT


# Column name mappings: Excel header -> DB field
COLUMN_MAP = {
    "patient_name": ["patient name", "name", "patient_name", "patientname"],
    "patient_id": ["patient id", "patient_id", "patientid", "id"],
    "mobile_number": ["mobile", "mobile number", "phone", "mobile_number", "contact"],
    "village_name": ["village", "village name", "village_name"],
    "district_name": ["district", "district name", "district_name"],
    "block_name": ["block", "block name", "block_name"],
    "municipality_name": ["municipality", "municipality name", "municipality_name"],
    "ward_number": ["ward", "ward number", "ward_number", "ward no"],
    "lmp_date": ["lmp", "lmp date", "lmp_date", "last menstrual period"],
    "edd_date": ["edd", "edd date", "edd_date", "expected date of delivery"],
    "motivator_name": ["motivator", "motivator name", "motivator_name"],
    "visit1": ["visit 1", "visit1", "first visit", "1st visit"],
    "visit2": ["visit 2", "visit2", "second visit", "2nd visit"],
    "visit3": ["visit 3", "visit3", "third visit", "3rd visit"],
    "final_visit": ["final visit", "final_visit", "final visit date"],
    "entry_date": ["entry date", "entry_date", "entry", "date of entry"],
    "serial_number": ["serial", "serial number", "serial_number", "sr no", "s.no"],
    "remarks": ["remarks", "remark", "notes", "comments"],
}


def _find_column(df: pd.DataFrame, field: str) -> Optional[str]:
    """Find Excel column name that maps to the given DB field."""
    candidates = COLUMN_MAP.get(field, [field])
    cols_lower = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None


def _to_date(val) -> Optional[str]:
    """Convert value to storage date string (yyyy-mm-dd)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, date):
        d = val
    elif isinstance(val, datetime):
        d = val.date()
    else:
        s = str(val).strip()
        if not s:
            return None
        d = parse_date(s)
    if not d or d == EMPTY_DATE_SENTINEL or d == EMPTY_DATE_SENTINEL_ALT:
        return None
    return format_for_storage(d)


def _to_str(val) -> Optional[str]:
    """Convert value to string for DB."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s else None


def _generate_patient_id(cur, entry_date: date) -> str:
    """
    Generate Patient ID in format PT<seq>-<MM>-<YYYY>,
    where seq is the next number for that month/year.
    """
    month = entry_date.strftime("%m")
    year = entry_date.strftime("%Y")
    cur.execute(
        """
        SELECT COUNT(*) FROM patients
        WHERE strftime('%m', entry_date) = ? AND strftime('%Y', entry_date) = ?
        """,
        (month, year),
    )
    count = cur.fetchone()[0] or 0
    next_num = count + 1
    return f"PT{next_num:02d}-{month}-{year}"


def import_from_excel(
    excel_path: Path,
    save_to_backup: bool = True,
) -> tuple[int, int, Optional[Path]]:
    """
    Import patient records from an Excel file.
    Returns (imported_count, skipped_count, backup_copy_path).
    Patient ID is auto-generated (PT<seq>-<MM>-<YYYY>) when not in Excel.
    Skips rows where patient_name is missing or patient_id already exists.
    """
    df = pd.read_excel(excel_path, engine="openpyxl")
    if df.empty:
        return 0, 0, None

    # Map columns (patient_id is optional - will be auto-generated if missing)
    col_patient_name = _find_column(df, "patient_name")
    col_patient_id = _find_column(df, "patient_id")
    col_mobile = _find_column(df, "mobile_number")
    col_village = _find_column(df, "village_name")
    col_district = _find_column(df, "district_name")
    col_block = _find_column(df, "block_name")
    col_municipality = _find_column(df, "municipality_name")
    col_ward = _find_column(df, "ward_number")
    col_lmp = _find_column(df, "lmp_date")
    col_edd = _find_column(df, "edd_date")
    col_motivator = _find_column(df, "motivator_name")
    col_visit1 = _find_column(df, "visit1")
    col_visit2 = _find_column(df, "visit2")
    col_visit3 = _find_column(df, "visit3")
    col_final = _find_column(df, "final_visit")
    col_entry = _find_column(df, "entry_date")
    col_remarks = _find_column(df, "remarks")
    col_serial = _find_column(df, "serial_number")

    if not col_patient_name:
        raise ValueError(
            "Excel must have a 'Patient Name' column. "
            "Supported headers: patient name, mobile, village, lmp, edd, motivator, visit1, visit2, visit3, final visit, entry date. "
            "Patient ID is auto-generated when not provided."
        )
    if not col_mobile:
        raise ValueError(
            "Excel must have a 'Mobile' column (required, 10-15 digits)."
        )

    conn = get_connection()
    imported = 0
    skipped = 0

    try:
        cur = conn.cursor()
        today_str = format_for_storage(date.today())

        for idx, row in df.iterrows():
            patient_name = _to_str(row.get(col_patient_name))
            if not patient_name:
                skipped += 1
                continue

            mobile = _to_str(row.get(col_mobile)) if col_mobile else None
            if not mobile:
                skipped += 1
                continue
            digits = "".join(c for c in mobile if c.isdigit())
            if len(digits) < 10 or len(digits) > 15:
                skipped += 1
                continue

            # Use patient_id from Excel if present, else auto-generate
            patient_id = _to_str(row.get(col_patient_id)) if col_patient_id else None
            if not patient_id:
                entry_d = parse_date(row.get(col_entry)) if col_entry else None
                entry_date = entry_d or date.today()
                patient_id = _generate_patient_id(cur, entry_date)

            # Check if already exists
            cur.execute("SELECT 1 FROM patients WHERE patient_id = ?", (patient_id,))
            if cur.fetchone():
                skipped += 1
                continue

            serial = row.get(col_serial)
            try:
                serial_int = int(float(serial)) if serial is not None and not (isinstance(serial, float) and pd.isna(serial)) else None
            except (ValueError, TypeError):
                serial_int = None

            patient_id_from_excel = bool(_to_str(row.get(col_patient_id)) if col_patient_id else False)
            entry_date = parse_date(row.get(col_entry)) if col_entry else None
            entry_date = entry_date or date.today()
            entry_str = format_for_storage(entry_date)
            visit1_str = entry_str  # visit1 always = entry_date
            v2 = parse_date(row.get(col_visit2)) if col_visit2 else None
            v3 = parse_date(row.get(col_visit3)) if col_visit3 else None
            final = parse_date(row.get(col_final)) if col_final else None
            # Enforce visit order: visit2 >= visit1, visit3 >= visit2, final >= visit3
            if v2 and v2 < entry_date:
                v2 = None
            if v3 and (v2 or entry_date) and v3 < (v2 or entry_date):
                v3 = None
            if final and (v3 or v2 or entry_date) and final < (v3 or v2 or entry_date):
                final = None

            inserted = False
            for _ in range(5 if not patient_id_from_excel else 1):
                try:
                    district = _to_str(row.get(col_district)) if col_district else get_district_name()
                    block = _to_str(row.get(col_block)) if col_block else None
                    municipality = _to_str(row.get(col_municipality)) if col_municipality else None
                    ward = _to_str(row.get(col_ward)) if col_ward else None
                    cur.execute(
                        """
                        INSERT INTO patients (
                            serial_number, patient_name, patient_id, mobile_number, village_name,
                            district_name, block_name, municipality_name, ward_number,
                            lmp_date, edd_date, motivator_name, visit1, visit2, visit3, final_visit,
                            entry_date, record_locked, created_at, remarks
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                        """,
                        (
                            serial_int,
                            patient_name,
                            patient_id,
                            mobile,
                            _to_str(row.get(col_village)),
                            district,
                            block,
                            municipality,
                            ward,
                            _to_date(row.get(col_lmp)),
                            _to_date(row.get(col_edd)),
                            _to_str(row.get(col_motivator)),
                            visit1_str,
                            format_for_storage(v2) if v2 else None,
                            format_for_storage(v3) if v3 else None,
                            format_for_storage(final) if final else None,
                            entry_str,
                            datetime.now().isoformat(),
                            _to_str(row.get(col_remarks)) if col_remarks else None,
                        ),
                    )
                    imported += 1
                    inserted = True
                    break
                except sqlite3.IntegrityError:
                    if patient_id_from_excel:
                        skipped += 1
                        break
                    patient_id = _generate_patient_id(cur, entry_date)
            if not inserted and not patient_id_from_excel:
                skipped += 1

        conn.commit()
    finally:
        conn.close()

    backup_path = None
    if save_to_backup and imported > 0:
        imports_dir = get_backup_dir_path() / "imports"
        imports_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = imports_dir / f"imported_{stamp}_{excel_path.name}"
        shutil.copy2(excel_path, backup_path)

    return imported, skipped, backup_path
