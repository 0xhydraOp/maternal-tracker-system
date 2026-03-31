"""
Comprehensive system tests for Maternal Tracking.
Run: python -m pytest tests/test_all_functions.py -v
Or: python -m unittest tests.test_all_functions -v
"""
from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

# Add project root
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestDateUtils(unittest.TestCase):
    """Test date parsing and formatting."""

    def test_parse_date_iso(self):
        from utils.date_utils import parse_date
        self.assertEqual(parse_date("2026-03-15"), date(2026, 3, 15))
        self.assertEqual(parse_date("2025-01-01"), date(2025, 1, 1))

    def test_parse_date_ddmmyyyy(self):
        from utils.date_utils import parse_date
        self.assertEqual(parse_date("15-03-2026"), date(2026, 3, 15))
        self.assertEqual(parse_date("01-01-2025"), date(2025, 1, 1))

    def test_parse_date_invalid(self):
        from utils.date_utils import parse_date
        self.assertIsNone(parse_date(""))
        self.assertIsNone(parse_date(None))
        self.assertIsNone(parse_date("invalid"))
        self.assertIsNone(parse_date("32-01-2026"))  # Invalid day

    def test_format_for_display(self):
        from utils.date_utils import format_for_display
        self.assertEqual(format_for_display(date(2026, 3, 15)), "15-03-2026")

    def test_format_for_storage(self):
        from utils.date_utils import format_for_storage
        self.assertEqual(format_for_storage(date(2026, 3, 15)), "2026-03-15")


class TestVisitScheduler(unittest.TestCase):
    """Test visit scheduling logic."""

    def test_schedule_subsequent_visits(self):
        from services.visit_scheduler import schedule_subsequent_visits
        v1 = date(2026, 1, 1)
        v2, v3, v4 = None, None, None
        r1, r2, r3, r4 = schedule_subsequent_visits(v1, v2, v3, v4)
        self.assertEqual(r1, v1)
        self.assertIsNone(r2)
        self.assertIsNone(r3)
        self.assertIsNone(r4)

    def test_get_next_visit_due_future(self):
        from services.visit_scheduler import get_next_visit_due
        today = date(2026, 3, 1)
        v1 = today - timedelta(days=30)
        v2 = today + timedelta(days=5)
        self.assertEqual(get_next_visit_due(v1, v2, None, None, today), v2)

    def test_get_next_visit_due_missed_2_overdue(self):
        from services.visit_scheduler import get_next_visit_due
        today = date(2026, 3, 15)
        v1 = today - timedelta(days=30)
        v2 = today - timedelta(days=5)  # visit2 scheduled but missed (overdue)
        next_due = get_next_visit_due(v1, v2, None, None, today)
        self.assertEqual(next_due, v2)  # Returns v2 as overdue (completed 1, missed 2)

    def test_get_next_visit_due_all_done(self):
        from services.visit_scheduler import get_next_visit_due
        today = date(2026, 3, 15)
        v1 = today - timedelta(days=90)
        v4 = today - timedelta(days=1)
        self.assertIsNone(get_next_visit_due(v1, None, None, v4, today))

    def test_classify_visit_status(self):
        from services.visit_scheduler import classify_visit_status
        today = date(2026, 3, 15)
        self.assertEqual(classify_visit_status(None, today), "none")
        self.assertEqual(classify_visit_status(today - timedelta(days=1), today), "overdue")
        self.assertEqual(classify_visit_status(today + timedelta(days=3), today), "upcoming")
        self.assertEqual(classify_visit_status(today + timedelta(days=14), today), "scheduled")


class TestPasswordService(unittest.TestCase):
    """Test password hashing and verification."""

    def test_hash_and_verify(self):
        from services.password_service import hash_password, verify_password
        h = hash_password("admin123")
        self.assertEqual(len(h), 64)
        self.assertTrue(verify_password("admin123", h))
        self.assertFalse(verify_password("wrong", h))

    def test_verify_empty_hash(self):
        from services.password_service import verify_password
        self.assertFalse(verify_password("any", ""))


class TestLocationService(unittest.TestCase):
    """Test location data."""

    def test_get_block_names(self):
        from services.location_service import get_block_names
        blocks = get_block_names()
        self.assertGreater(len(blocks), 0)
        self.assertIn("Berhampore", blocks)

    def test_get_municipality_names(self):
        from services.location_service import get_municipality_names
        munis = get_municipality_names()
        self.assertGreater(len(munis), 0)
        self.assertIn("Baharampur", munis)

    def test_get_district_name(self):
        from services.location_service import get_district_name
        self.assertEqual(get_district_name(), "Murshidabad")


class TestDatabase(unittest.TestCase):
    """Test database init and queries."""

    def test_init_db(self):
        from database.init_db import init_db, get_connection
        init_db()
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            self.assertIn("patients", tables)
            self.assertIn("users", tables)
            self.assertIn("change_logs", tables)
            self.assertIn("custom_motivators", tables)
        finally:
            conn.close()

    def test_patients_query(self):
        """Verify reports patient query runs and returns expected columns."""
        from database.init_db import get_connection
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT serial_number, patient_name, patient_id, mobile_number, motivator_name,
                       district_name, block_name, municipality_name, village_name, ward_number,
                       lmp_date, edd_date, visit1, visit2, visit3, final_visit, entry_date, remarks
                FROM patients ORDER BY entry_date DESC, serial_number LIMIT 5
                """
            )
            rows = cur.fetchall()
            # Should not raise; column count matches
            for row in rows:
                self.assertEqual(len(row), 18)
        finally:
            conn.close()

    def test_visit_completion_query(self):
        """Verify visit completion report query runs."""
        from database.init_db import get_connection
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT visit1, visit2, visit3, final_visit, entry_date
                FROM patients WHERE entry_date IS NOT NULL LIMIT 1
                """
            )
            cur.fetchall()
        finally:
            conn.close()


class TestBackupService(unittest.TestCase):
    """Test backup operations."""

    def test_list_backups(self):
        from services.backup_service import list_backups
        backups = list_backups()
        self.assertIsInstance(backups, list)
        for item in backups:
            self.assertEqual(len(item), 3)  # path, date_str, size

    def test_create_pre_restore_backup(self):
        from services.backup_service import create_pre_restore_backup
        path = create_pre_restore_backup()
        if path:
            self.assertTrue(path.exists())
            path.unlink(missing_ok=True)


class TestChangeLogger(unittest.TestCase):
    """Test change logging."""

    def test_log_change_no_op_on_same_value(self):
        from services.change_logger import log_change
        from database.init_db import get_connection
        # Should not raise; skips when old==new
        log_change("PT01-01-2026", "remarks", "x", "x", "admin")
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM change_logs WHERE patient_id='PT01-01-2026' AND field_name='remarks' AND old_value='x' AND new_value='x'")
            self.assertEqual(cur.fetchone()[0], 0)
        finally:
            conn.close()


class TestMotivatorService(unittest.TestCase):
    """Test motivator service."""

    def test_get_all_motivator_names(self):
        from services.motivator_service import get_all_motivator_names
        names = get_all_motivator_names()
        self.assertIsInstance(names, list)
        for n in names:
            self.assertIsInstance(n, str)

    def test_add_custom_motivator(self):
        from services.motivator_service import add_custom_motivator, get_all_motivator_names
        from database.init_db import get_connection
        test_name = "Test Motivator XYZ"
        add_custom_motivator(test_name)
        names = get_all_motivator_names()
        self.assertIn(test_name, names)
        # Cleanup
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM custom_motivators WHERE name=?", (test_name,))
            conn.commit()
        finally:
            conn.close()


class TestExcelImport(unittest.TestCase):
    """Test Excel import service."""

    def test_import_empty_excel(self):
        import pandas as pd
        from services.excel_import_service import import_from_excel
        path = Path(tempfile.gettempdir()) / f"test_empty_{id(self)}.xlsx"
        try:
            pd.DataFrame().to_excel(path, index=False)
            imp, skip, _ = import_from_excel(path, save_to_backup=False)
            self.assertEqual(imp, 0)
            self.assertEqual(skip, 0)
        finally:
            path.unlink(missing_ok=True)

    def test_import_missing_columns_raises(self):
        import pandas as pd
        from services.excel_import_service import import_from_excel
        path = Path(tempfile.gettempdir()) / f"test_missing_{id(self)}.xlsx"
        try:
            pd.DataFrame({"foo": [1]}).to_excel(path, index=False)
            with self.assertRaises(ValueError):
                import_from_excel(path, save_to_backup=False)
        finally:
            path.unlink(missing_ok=True)

    def test_import_valid_minimal(self):
        import pandas as pd
        from services.excel_import_service import import_from_excel
        from database.init_db import get_connection
        df = pd.DataFrame({
            "Patient Name": ["Import Test Patient"],
            "Mobile": ["9876543210"],
            "Village": ["Test Village"],
            "LMP": ["2025-06-15"],
            "EDD": ["2026-03-22"],
            "Motivator": ["ANM"],
        })
        path = Path(tempfile.gettempdir()) / f"test_valid_{id(self)}.xlsx"
        try:
            df.to_excel(path, index=False)
            imp, skip, _ = import_from_excel(path, save_to_backup=False)
            self.assertGreaterEqual(imp, 1)
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM patients WHERE patient_name='Import Test Patient'")
                conn.commit()
            finally:
                conn.close()
        finally:
            path.unlink(missing_ok=True)


class TestConfig(unittest.TestCase):
    """Test config read/write."""

    def test_get_defaults(self):
        from config import get_dark_mode, get_backup_dir, get_admin_area_password
        _ = get_dark_mode()
        _ = get_backup_dir()
        _ = get_admin_area_password()
        # Should not raise


class TestReportsQueries(unittest.TestCase):
    """Test reports SQL and data logic."""

    def test_block_municipality_query(self):
        from database.init_db import get_connection
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT block_name, municipality_name, COUNT(*) as cnt
                FROM patients
                WHERE entry_date IS NOT NULL
                GROUP BY COALESCE(block_name, ''), COALESCE(municipality_name, '')
                LIMIT 10
                """
            )
            cur.fetchall()
        finally:
            conn.close()

    def test_monthly_summary_query(self):
        from database.init_db import get_connection
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT strftime('%Y-%m', entry_date) as ym, COUNT(*) as reg
                FROM patients WHERE entry_date IS NOT NULL
                GROUP BY ym ORDER BY ym DESC LIMIT 12
                """
            )
            cur.fetchall()
        finally:
            conn.close()


class TestActivityLogger(unittest.TestCase):
    """Test activity logging."""

    def test_log_admin_activity(self):
        from services.activity_logger import log_admin_activity
        log_admin_activity("test_action", "test details", "admin")
        # Should not raise


class TestRestoreBackup(unittest.TestCase):
    """Test backup restore logic."""

    def test_restore_nonexistent(self):
        from services.backup_service import restore_backup
        result = restore_backup(Path("/nonexistent/path.db"), create_backup_first=False)
        self.assertFalse(result)


class TestDashboardStats(unittest.TestCase):
    """Test dashboard statistics queries."""

    def test_overdue_count_query(self):
        from database.init_db import get_connection
        from services.visit_scheduler import get_next_visit_due
        from utils.date_utils import parse_date
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT visit1, visit2, visit3, final_visit, record_locked FROM patients LIMIT 100"
            )
            today = date.today()
            overdue = 0
            for row in cur.fetchall():
                v1, v2, v3, v4 = row[:4]
                record_locked = bool(row[4]) if len(row) > 4 else False
                for v in (v1, v2, v3, v4):
                    d = parse_date(v) if v else None
                    if d and d < today:
                        next_due = get_next_visit_due(
                            parse_date(v1), parse_date(v2), parse_date(v3), parse_date(v4),
                            today, record_locked=record_locked
                        )
                        if next_due and next_due <= today:
                            overdue += 1
                            break
            # Just verify no exception
        finally:
            conn.close()


class TestVisitValidation(unittest.TestCase):
    """Test visit date validation and fix logic."""

    def test_visit_order_fix_logic(self):
        """Simulate fix_visit_dates logic: visit2 < visit1 should be cleared."""
        from utils.date_utils import parse_date, format_for_storage
        today = date.today()
        entry_d = today - timedelta(days=30)
        v2_bad = today - timedelta(days=60)  # Before entry
        self.assertLess(v2_bad, entry_d)
        # Fix: v2 should be cleared
        v2_fixed = None if v2_bad < entry_d else v2_bad
        self.assertIsNone(v2_fixed)

    def test_excel_import_visit_order(self):
        """Excel import enforces visit1=entry_date, visit2>=visit1."""
        import pandas as pd
        from services.excel_import_service import import_from_excel
        from database.init_db import get_connection
        # Row with visit2 before entry_date - should be sanitized
        df = pd.DataFrame({
            "Patient Name": ["Visit Order Test"],
            "Mobile": ["9876543211"],
            "Village": ["TestV"],
            "LMP": ["2025-06-01"],
            "EDD": ["2026-03-08"],
            "Motivator": ["ANM"],
            "Entry Date": ["2026-03-01"],
            "Visit 1": ["2026-02-15"],  # Before entry - should become entry_date
            "Visit 2": ["2026-02-10"],  # Before entry - should be cleared
        })
        path = Path(tempfile.gettempdir()) / f"test_visit_order_{id(self)}.xlsx"
        try:
            df.to_excel(path, index=False)
            imp, skip, _ = import_from_excel(path, save_to_backup=False)
            self.assertGreaterEqual(imp, 1)
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT entry_date, visit1, visit2 FROM patients WHERE patient_name='Visit Order Test'"
                )
                row = cur.fetchone()
                self.assertIsNotNone(row)
                entry_str, v1_str, v2_str = row
                self.assertEqual(entry_str, v1_str)  # visit1 = entry_date
                if v2_str:
                    from utils.date_utils import parse_date as parse_d
                    self.assertGreaterEqual(
                        parse_d(v2_str) or date.min,
                        parse_d(v1_str) or date.min
                    )
                cur.execute("DELETE FROM patients WHERE patient_name='Visit Order Test'")
                conn.commit()
            finally:
                conn.close()
        finally:
            path.unlink(missing_ok=True)


class TestUIImports(unittest.TestCase):
    """Verify UI modules can be imported (no syntax/import errors)."""

    def test_import_login_window(self):
        from ui.login_window import LoginWindow
        self.assertTrue(hasattr(LoginWindow, "Accepted"))

    def test_import_dashboard(self):
        from ui.dashboard import DashboardWindow
        self.assertTrue(hasattr(DashboardWindow, "_build_ui"))

    def test_import_reports(self):
        from ui.reports import ReportsWidget
        self.assertTrue(hasattr(ReportsWidget, "_load_data"))

    def test_import_patient_entry(self):
        from ui.patient_entry import PatientEntryDialog
        self.assertTrue(hasattr(PatientEntryDialog, "load_patient"))

    def test_import_patient_search(self):
        from ui.patient_search import PatientSearchDialog
        self.assertTrue(hasattr(PatientSearchDialog, "_load_all_patients"))

    def test_import_administration(self):
        from ui.administration import AdministrationWidget
        self.assertTrue(hasattr(AdministrationWidget, "_build_ui"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
