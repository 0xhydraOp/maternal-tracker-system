"""
Administration Area - Admin-only panel for user management, patient management,
change logs, and custom motivators.
"""
from __future__ import annotations

from typing import List, Tuple, Any, Optional

from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QMessageBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDialogButtonBox,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QDateEdit,
    QCheckBox,
    QInputDialog,
    QFileDialog,
    QFrame,
)

from config import (
    get_admin_area_password,
    set_admin_area_password,
    get_dark_mode,
    set_dark_mode,
    get_backup_dir,
    set_backup_dir,
)
from database.init_db import get_connection
from utils.date_utils import DATE_FORMAT_DISPLAY
from services.motivator_service import add_custom_motivator, get_all_motivator_names
from services.password_service import hash_password
from services.activity_logger import log_admin_activity
from ui.patient_entry import PatientEntryDialog


class AdministrationWidget(QWidget):
    """
    Administration Area - Admin can manage users, patients, view change logs,
    and manage custom motivators.
    """

    def __init__(self, username: str, role: str = "ADMIN", parent=None):
        super().__init__(parent)
        self.username = username
        self.role = role.upper()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        admin_title = QLabel("Administration Area - Full system control (ADMIN only)")
        admin_title.setObjectName("sectionTitle")
        admin_title.setWordWrap(True)
        layout.addWidget(admin_title)
        layout.addSpacing(12)

        # Database stats summary panel
        stats_frame = QFrame()
        stats_frame.setObjectName("topBarActions")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(24)
        self.stats_patients_label = QLabel("Patients: 0")
        self.stats_users_label = QLabel("Users: 0")
        self.stats_logs_label = QLabel("Change Logs: 0")
        for lbl in (self.stats_patients_label, self.stats_users_label, self.stats_logs_label):
            lbl.setObjectName("sectionTitle")
        stats_layout.addWidget(self.stats_patients_label)
        stats_layout.addWidget(self.stats_users_label)
        stats_layout.addWidget(self.stats_logs_label)
        stats_layout.addStretch()
        layout.addWidget(stats_frame)
        layout.addSpacing(8)

        tabs = QTabWidget()
        tabs.addTab(self._build_users_tab(), "User Management")
        tabs.addTab(self._build_patients_tab(), "Patient Management")
        tabs.addTab(self._build_change_logs_tab(), "Change Logs")
        tabs.addTab(self._build_motivators_tab(), "Custom Motivators")
        tabs.addTab(self._build_settings_tab(), "Settings")
        layout.addWidget(tabs)

    def _refresh_stats(self) -> None:
        """Update database stats summary panel."""
        patients = users = logs = 0
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM patients")
            patients = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM users")
            users = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM change_logs")
            logs = cur.fetchone()[0] or 0
        finally:
            conn.close()
        self.stats_patients_label.setText(f"Patients: {patients}")
        self.stats_users_label.setText(f"Users: {users}")
        self.stats_logs_label.setText(f"Change Logs: {logs}")

    def _build_users_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add User")
        add_btn.clicked.connect(self._add_user)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_users)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.users_table = QTableWidget()
        self.users_table.setObjectName("dataTable")
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Created"])
        self.users_table.horizontalHeader().setVisible(True)
        self.users_table.horizontalHeader().setMinimumHeight(40)
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setSelectionMode(QTableWidget.SingleSelection)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.cellDoubleClicked.connect(lambda r, c: self._edit_user())
        layout.addWidget(self.users_table)
        edit_row = QHBoxLayout()
        edit_btn = QPushButton("Edit User")
        edit_btn.clicked.connect(self._edit_user)
        delete_btn = QPushButton("Delete User")
        delete_btn.clicked.connect(self._delete_user)
        edit_row.addWidget(edit_btn)
        edit_row.addWidget(delete_btn)
        edit_row.addStretch()
        layout.addLayout(edit_row)
        self._load_users()
        return w

    def _build_patients_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)
        # Patient filters
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Patient ID:"))
        self.patient_id_filter = QLineEdit()
        self.patient_id_filter.setPlaceholderText("Filter...")
        self.patient_id_filter.setMaximumWidth(120)
        self.patient_id_filter.textChanged.connect(self._load_patients)
        filter_row.addWidget(self.patient_id_filter)
        filter_row.addWidget(QLabel("Name:"))
        self.patient_name_filter = QLineEdit()
        self.patient_name_filter.setPlaceholderText("Filter...")
        self.patient_name_filter.setMaximumWidth(120)
        self.patient_name_filter.textChanged.connect(self._load_patients)
        filter_row.addWidget(self.patient_name_filter)
        filter_row.addWidget(QLabel("Village:"))
        self.patient_village_filter = QLineEdit()
        self.patient_village_filter.setPlaceholderText("Filter...")
        self.patient_village_filter.setMaximumWidth(120)
        self.patient_village_filter.textChanged.connect(self._load_patients)
        filter_row.addWidget(self.patient_village_filter)
        filter_row.addWidget(QLabel("Motivator:"))
        self.patient_motivator_filter = QComboBox()
        self.patient_motivator_filter.setEditable(True)
        self.patient_motivator_filter.blockSignals(True)
        self.patient_motivator_filter.addItem("All")
        self.patient_motivator_filter.addItems(get_all_motivator_names())
        self.patient_motivator_filter.setCurrentIndex(0)
        self.patient_motivator_filter.blockSignals(False)
        self.patient_motivator_filter.setMaximumWidth(140)
        self.patient_motivator_filter.currentTextChanged.connect(self._load_patients)
        filter_row.addWidget(self.patient_motivator_filter)
        filter_row.addStretch()
        layout.addLayout(filter_row)
        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_patients)
        edit_btn = QPushButton("Edit Selected Patient")
        edit_btn.clicked.connect(self._edit_patient)
        delete_btn = QPushButton("Delete Selected Patient")
        delete_btn.clicked.connect(self._delete_patient)
        unlock_btn = QPushButton("Unlock Selected Record")
        unlock_btn.clicked.connect(self._unlock_patient)
        btn_row.addWidget(refresh_btn)
        btn_row.addWidget(edit_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addWidget(unlock_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.patients_table = QTableWidget()
        self.patients_table.setObjectName("dataTable")
        self.patients_table.setColumnCount(9)
        self.patients_table.setHorizontalHeaderLabels(
            ["Entry Date", "Patient Name", "Patient ID", "Village", "Mobile", "Motivator", "Final Visit", "Remarks", "Locked"]
        )
        self.patients_table.horizontalHeader().setVisible(True)
        self.patients_table.horizontalHeader().setMinimumHeight(40)
        self.patients_table.horizontalHeader().setStretchLastSection(True)
        self.patients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.patients_table.setSelectionMode(QTableWidget.SingleSelection)
        self.patients_table.setAlternatingRowColors(True)
        self.patients_table.cellDoubleClicked.connect(lambda r, c: self._edit_patient())
        layout.addWidget(self.patients_table)
        self._load_patients()
        return w

    def _build_change_logs_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)
        # Filters: From Date, To Date, Patient ID, Changed By
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("From:"))
        self.log_from_date = QDateEdit()
        self.log_from_date.setCalendarPopup(True)
        self.log_from_date.setDisplayFormat(DATE_FORMAT_DISPLAY)
        self.log_from_date.setDate(QDate(date.today().year, 1, 1))
        filter_row.addWidget(self.log_from_date)
        filter_row.addWidget(QLabel("To:"))
        self.log_to_date = QDateEdit()
        self.log_to_date.setCalendarPopup(True)
        self.log_to_date.setDisplayFormat(DATE_FORMAT_DISPLAY)
        self.log_to_date.setDate(QDate.currentDate())
        filter_row.addWidget(self.log_to_date)
        filter_row.addWidget(QLabel("Patient ID:"))
        self.log_patient_filter = QLineEdit()
        self.log_patient_filter.setPlaceholderText("Filter by patient...")
        self.log_patient_filter.setMaximumWidth(120)
        filter_row.addWidget(self.log_patient_filter)
        filter_row.addWidget(QLabel("Changed By:"))
        self.log_user_filter = QLineEdit()
        self.log_user_filter.setPlaceholderText("Filter by user...")
        self.log_user_filter.setMaximumWidth(120)
        filter_row.addWidget(self.log_user_filter)
        layout.addLayout(filter_row)
        btn_row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_change_logs)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.logs_table = QTableWidget()
        self.logs_table.setObjectName("dataTable")
        self.logs_table.setColumnCount(6)
        self.logs_table.horizontalHeader().setVisible(True)
        self.logs_table.horizontalHeader().setMinimumHeight(40)
        self.logs_table.setHorizontalHeaderLabels(
            ["Date", "Patient ID", "Field", "Old Value", "New Value", "Changed By"]
        )
        self.logs_table.horizontalHeader().setStretchLastSection(True)
        self.logs_table.setAlternatingRowColors(True)
        layout.addWidget(self.logs_table)
        self._load_change_logs()
        return w

    def _build_motivators_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add New Motivator")
        add_btn.clicked.connect(self._add_motivator)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_motivators)
        delete_btn = QPushButton("Remove Selected")
        delete_btn.clicked.connect(self._delete_motivator)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(refresh_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.motivators_table = QTableWidget()
        self.motivators_table.setObjectName("dataTable")
        self.motivators_table.setColumnCount(2)
        self.motivators_table.setHorizontalHeaderLabels(["Name", "Added At"])
        self.motivators_table.horizontalHeader().setVisible(True)
        self.motivators_table.horizontalHeader().setMinimumHeight(40)
        self.motivators_table.horizontalHeader().setStretchLastSection(True)
        self.motivators_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.motivators_table.setAlternatingRowColors(True)
        layout.addWidget(self.motivators_table)
        self._load_motivators()
        return w

    def _build_settings_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        # Admin Area Password
        pwd_group = QWidget()
        pwd_form = QFormLayout(pwd_group)
        self.admin_pwd_edit = QLineEdit()
        self.admin_pwd_edit.setEchoMode(QLineEdit.Password)
        self.admin_pwd_edit.setPlaceholderText("Current: admin@123 (change to set new)")
        pwd_btn = QPushButton("Set Admin Area Password")
        pwd_btn.clicked.connect(self._set_admin_password)
        pwd_form.addRow("Admin Area Password:", self.admin_pwd_edit)
        pwd_form.addRow("", pwd_btn)
        layout.addWidget(QLabel("Change the password required to access Administration Area:"))
        layout.addWidget(pwd_group)

        # Backup folder path
        backup_layout = QFormLayout()
        self.backup_label = QLabel(get_backup_dir())
        self.backup_label.setObjectName("backupFolderPath")
        self.backup_label.setWordWrap(True)
        change_backup_btn = QPushButton("Change Backup Folder...")
        change_backup_btn.clicked.connect(self._change_backup_folder)
        backup_layout.addRow("Backup folder:", self.backup_label)
        backup_layout.addRow("", change_backup_btn)
        layout.addWidget(QLabel("Database backup location:"))
        layout.addLayout(backup_layout)

        # Dark Mode
        self.dark_mode_check = QCheckBox("Enable Dark Mode")
        self.dark_mode_check.setChecked(get_dark_mode())
        self.dark_mode_check.stateChanged.connect(self._on_dark_mode_changed)
        layout.addWidget(self.dark_mode_check)
        layout.addWidget(QLabel("(Theme applies immediately when toggled)"))

        layout.addStretch()
        return w

    def _change_backup_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder", get_backup_dir())
        if folder:
            set_backup_dir(folder)
            self.backup_label.setText(folder)
            log_admin_activity("SETTINGS_CHANGE", f"Backup folder changed to: {folder}", self.username)
            QMessageBox.information(self, "Saved", "Backup folder updated. New backups will use this location.")

    def _set_admin_password(self) -> None:
        pwd = self.admin_pwd_edit.text().strip()
        if not pwd:
            QMessageBox.warning(self, "Validation", "Enter a password.")
            return
        set_admin_area_password(pwd)
        self.admin_pwd_edit.clear()
        self.admin_pwd_edit.setPlaceholderText("Password updated")
        log_admin_activity("SETTINGS_CHANGE", "Admin area password updated", self.username)
        QMessageBox.information(self, "Saved", "Admin Area password has been updated.")

    def _on_dark_mode_changed(self, state: int) -> None:
        from PySide6.QtWidgets import QApplication
        set_dark_mode(state == 2)  # Qt.Checked = 2
        from styles import get_stylesheet
        app = QApplication.instance()
        if app:
            app.setStyleSheet(get_stylesheet(get_dark_mode()))
        QMessageBox.information(
            self,
            "Theme Updated",
            "Theme has been applied. It will persist on next launch.",
        )

    def _load_users(self) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, username, role, created_at FROM users ORDER BY id")
            rows = cur.fetchall()
        finally:
            conn.close()
        self.users_table.setRowCount(len(rows))
        for i, (uid, uname, role, created) in enumerate(rows):
            self.users_table.setItem(i, 0, QTableWidgetItem(str(uid)))
            self.users_table.setItem(i, 1, QTableWidgetItem(uname or ""))
            self.users_table.setItem(i, 2, QTableWidgetItem(role or ""))
            self.users_table.setItem(i, 3, QTableWidgetItem(created or ""))
        self.users_table.resizeColumnsToContents()
        self._refresh_stats()

    def _add_user(self) -> None:
        dlg = UserEditDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            username = dlg.username_edit.text().strip()
            password = dlg.password_edit.text()
            role = dlg.role_combo.currentText()
            if not username or not password:
                QMessageBox.warning(self, "Validation", "Username and password required.")
                return
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, hash_password(password), role),
                )
                conn.commit()
                log_admin_activity("USER_ADD", f"Added user: {username} (role: {role})", self.username)
                QMessageBox.information(self, "Success", f"User '{username}' added.")
                self._load_users()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Error", str(e))
            finally:
                conn.close()

    def _edit_user(self) -> None:
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Edit", "Select a user to edit.")
            return
        uid_item = self.users_table.item(row, 0)
        uname_item = self.users_table.item(row, 1)
        role_item = self.users_table.item(row, 2)
        if not uid_item or not uname_item or not role_item:
            QMessageBox.warning(self, "Edit", "Invalid row data.")
            return
        uid = uid_item.text()
        uname = uname_item.text()
        role = role_item.text()
        dlg = UserEditDialog(username=uname, role=role, parent=self, is_edit=True)
        if dlg.exec() == QDialog.Accepted:
            new_uname = dlg.username_edit.text().strip()
            new_password = dlg.password_edit.text()
            new_role = dlg.role_combo.currentText()
            if not new_uname:
                QMessageBox.warning(self, "Validation", "Username required.")
                return
            conn = get_connection()
            try:
                cur = conn.cursor()
                if new_password:
                    cur.execute(
                        "UPDATE users SET username=?, password_hash=?, role=? WHERE id=?",
                        (new_uname, hash_password(new_password), new_role, int(uid)),
                    )
                else:
                    cur.execute(
                        "UPDATE users SET username=?, role=? WHERE id=?",
                        (new_uname, new_role, int(uid)),
                    )
                conn.commit()
                log_admin_activity("USER_EDIT", f"Updated user: {new_uname}", self.username)
                QMessageBox.information(self, "Success", "User updated.")
                self._load_users()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "Error", str(e))
            finally:
                conn.close()

    def _confirm_delete(self, title: str, message: str) -> bool:
        """Require user to type DELETE to confirm. Returns True if confirmed."""
        text, ok = QInputDialog.getText(
            self, title, f"{message}\n\nType DELETE (in capitals) to confirm:"
        )
        return ok and text.strip() == "DELETE"

    def _delete_user(self) -> None:
        row = self.users_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Delete", "Select a user to delete.")
            return
        uname_item = self.users_table.item(row, 1)
        if not uname_item:
            QMessageBox.warning(self, "Delete", "Invalid row data.")
            return
        uname = uname_item.text()
        if uname == self.username:
            QMessageBox.warning(self, "Delete", "You cannot delete your own account.")
            return
        if not self._confirm_delete("Delete User", f"Permanently delete user '{uname}'? This cannot be undone."):
            return
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE username=?", (uname,))
            conn.commit()
            log_admin_activity("USER_DELETE", f"Deleted user: {uname}", self.username)
            QMessageBox.information(self, "Success", "User deleted.")
            self._load_users()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

    def _load_patients(self) -> None:
        pid_f = getattr(self, "patient_id_filter", None)
        name_f = getattr(self, "patient_name_filter", None)
        village_f = getattr(self, "patient_village_filter", None)
        motivator_f = getattr(self, "patient_motivator_filter", None)

        pid_val = pid_f.text().strip().lower() if pid_f else ""
        name_val = name_f.text().strip().lower() if name_f else ""
        village_val = village_f.text().strip().lower() if village_f else ""
        motivator_txt = motivator_f.currentText().strip().lower() if motivator_f else ""
        motivator_val = motivator_txt if motivator_txt and motivator_txt != "all" else None

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT patient_id, patient_name, mobile_number, village_name,
                       motivator_name, entry_date, record_locked, final_visit, remarks
                FROM patients ORDER BY entry_date DESC
                """
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        filtered = []
        for row in rows:
            pid, name, mobile, village, motivator, entry, locked, final, remarks = row
            if pid_val and pid_val not in str(pid or "").lower():
                continue
            if name_val and name_val not in str(name or "").lower():
                continue
            if village_val and village_val not in str(village or "").lower():
                continue
            if motivator_val and motivator_val not in str(motivator or "").lower():
                continue
            filtered.append(row)

        # Column order: Entry Date, Name, Patient ID, Village, Mobile, Motivator, Final Visit, Remarks, Locked
        self.patients_table.setRowCount(len(filtered))
        for i, row in enumerate(filtered):
            pid, name, mobile, village, motivator, entry, locked, final, remarks = row
            display = [entry, name, pid, village, mobile, motivator, final, remarks or "", locked]
            for j, val in enumerate(display):
                self.patients_table.setItem(i, j, QTableWidgetItem("" if val is None else str(val)))
        self.patients_table.resizeColumnsToContents()
        self._refresh_stats()

    def _edit_patient(self) -> None:
        row = self.patients_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Edit", "Select a patient to edit.")
            return
        pid_item = self.patients_table.item(row, 2)
        if not pid_item:
            QMessageBox.warning(self, "Edit", "Invalid row data.")
            return
        pid = pid_item.text()
        dialog = PatientEntryDialog(
            username=self.username, role=self.role, parent=self.window()
        )
        dialog.patient_id_edit.setText(pid)
        dialog.load_patient()
        if dialog.exec() == QDialog.Accepted:
            self._load_patients()
            self._refresh_stats()

    def _delete_patient(self) -> None:
        row = self.patients_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Delete", "Select a patient to delete.")
            return
        pid_item = self.patients_table.item(row, 2)
        name_item = self.patients_table.item(row, 1)
        if not pid_item or not name_item:
            QMessageBox.warning(self, "Delete", "Invalid row data.")
            return
        pid = pid_item.text()
        name = name_item.text()
        if not self._confirm_delete("Delete Patient", f"Permanently delete patient '{name}' ({pid})? This cannot be undone."):
            return
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM change_logs WHERE patient_id=?", (pid,))
            cur.execute("DELETE FROM patients WHERE patient_id=?", (pid,))
            conn.commit()
            log_admin_activity("PATIENT_DELETE", f"Deleted patient: {name} ({pid})", self.username)
            QMessageBox.information(self, "Success", "Patient deleted.")
            self._load_patients()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

    def _unlock_patient(self) -> None:
        row = self.patients_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Unlock", "Select a patient to unlock.")
            return
        pid_item = self.patients_table.item(row, 2)
        locked_item = self.patients_table.item(row, 8)
        if not pid_item or not locked_item:
            QMessageBox.warning(self, "Unlock", "Invalid row data.")
            return
        pid = pid_item.text()
        locked = locked_item.text()
        if locked != "1" and locked.lower() != "true":
            QMessageBox.information(self, "Unlock", "Record is not locked.")
            return
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("UPDATE patients SET record_locked=0 WHERE patient_id=?", (pid,))
            conn.commit()
            QMessageBox.information(self, "Success", "Record unlocked.")
            self._load_patients()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

    def _load_change_logs(self) -> None:
        from_date = self.log_from_date.date()
        to_date = self.log_to_date.date()
        patient_f = self.log_patient_filter.text().strip().lower()
        user_f = self.log_user_filter.text().strip().lower()
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT changed_at, patient_id, field_name, old_value, new_value, changed_by
                FROM change_logs ORDER BY changed_at DESC LIMIT 1000
                """
            )
            rows = cur.fetchall()
        finally:
            conn.close()
        # Apply filters
        filtered = []
        for row in rows:
            changed_at, patient_id, field_name, old_val, new_val, changed_by = row
            if from_date.isValid():
                try:
                    d = date.fromisoformat(str(changed_at or "")[:10])
                    if QDate(d.year, d.month, d.day) < from_date:
                        continue
                except (ValueError, TypeError):
                    pass
            if to_date.isValid():
                try:
                    d = date.fromisoformat(str(changed_at or "")[:10])
                    if QDate(d.year, d.month, d.day) > to_date:
                        continue
                except (ValueError, TypeError):
                    pass
            if patient_f and patient_f not in str(patient_id or "").lower():
                continue
            if user_f and user_f not in str(changed_by or "").lower():
                continue
            filtered.append(row)
        rows = filtered
        self.logs_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.logs_table.setItem(i, j, QTableWidgetItem("" if val is None else str(val)))
        self.logs_table.resizeColumnsToContents()
        self._refresh_stats()

    def _load_motivators(self) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT name, added_at FROM custom_motivators ORDER BY name")
            rows = cur.fetchall()
        finally:
            conn.close()
        self.motivators_table.setRowCount(len(rows))
        for i, (name, added) in enumerate(rows):
            self.motivators_table.setItem(i, 0, QTableWidgetItem(name or ""))
            self.motivators_table.setItem(i, 1, QTableWidgetItem(added or ""))
        self.motivators_table.resizeColumnsToContents()

    def _add_motivator(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Add New Motivator")
        layout = QFormLayout(dlg)
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("Enter motivator name")
        layout.addRow("Motivator Name:", name_edit)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)
        if dlg.exec() == QDialog.Accepted:
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Validation", "Please enter a motivator name.")
                return
            add_custom_motivator(name)
            QMessageBox.information(self, "Success", f"Motivator '{name}' added.")
            self._load_motivators()

    def _delete_motivator(self) -> None:
        row = self.motivators_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Remove", "Select a motivator to remove.")
            return
        name = self.motivators_table.item(row, 0).text()
        reply = QMessageBox.question(
            self, "Remove Motivator",
            f"Remove '{name}' from custom motivators list?\n\nPatients with this motivator will keep it.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM custom_motivators WHERE name=?", (name,))
            conn.commit()
            QMessageBox.information(self, "Success", "Motivator removed from list.")
            self._load_motivators()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()


class UserEditDialog(QDialog):
    """Dialog to add or edit a user."""

    def __init__(
        self,
        username: str = "",
        role: str = "STAFF",
        parent=None,
        is_edit: bool = False,
    ):
        super().__init__(parent)
        self.setWindowTitle("Edit User" if is_edit else "Add User")
        layout = QFormLayout(self)
        self.username_edit = QLineEdit()
        self.username_edit.setText(username)
        self.username_edit.setPlaceholderText("Username")
        layout.addRow("Username:", self.username_edit)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Leave blank to keep current" if is_edit else "Password")
        layout.addRow("Password:", self.password_edit)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["STAFF", "ADMIN"])
        idx = self.role_combo.findText(role)
        if idx >= 0:
            self.role_combo.setCurrentIndex(idx)
        layout.addRow("Role:", self.role_combo)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)
