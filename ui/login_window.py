from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
)

from database.init_db import get_connection
from services.password_service import hash_password, verify_password


class LoginWindow(QDialog):
    """
    Simple login dialog that validates against the `users` table.
    This is a starter implementation and can be expanded with
    password hashing and role-based behavior.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Maternal Tracking - Login")
        self._build_ui()

        self.username: str | None = None
        self.role: str | None = None

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        self.setMinimumWidth(360)
        self.setMinimumHeight(280)

        # Login type: Admin or Staff
        login_type_label = QLabel("Login as:")
        login_type_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(login_type_label)
        self.login_as_admin = QRadioButton("Login as Admin")
        self.login_as_staff = QRadioButton("Login as Staff")
        self.login_as_admin.setChecked(True)
        type_row = QHBoxLayout()
        type_row.addWidget(self.login_as_admin)
        type_row.addWidget(self.login_as_staff)
        type_row.addStretch()
        layout.addLayout(type_row)
        layout.addSpacing(12)

        form_layout = QFormLayout()
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        form_layout.addRow(QLabel("Username:"), self.username_edit)
        form_layout.addRow(QLabel("Password:"), self.password_edit)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.button_box.accepted.connect(self.handle_login)
        self.button_box.rejected.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.button_box)

        layout.addLayout(btn_layout)

    def handle_login(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter username and password.")
            return

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT username, password_hash, role FROM users WHERE username = ?",
                (username,),
            )
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
            return

        db_username, password_hash, role = row
        role = (role or "").upper()

        if not verify_password(password, password_hash or ""):
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
            return

        # Migrate plain-text password to hash on successful login
        from services.password_service import is_hashed
        if not is_hashed(password_hash or ""):
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE users SET password_hash = ? WHERE username = ?",
                    (hash_password(password), db_username),
                )
                conn.commit()
            finally:
                conn.close()

        # Validate login type matches user role
        login_as_admin = self.login_as_admin.isChecked()
        if login_as_admin and role != "ADMIN":
            QMessageBox.warning(
                self,
                "Login Failed",
                "This account is not an Admin. Please select 'Login as Staff'.",
            )
            return
        if not login_as_admin and role != "STAFF":
            QMessageBox.warning(
                self,
                "Login Failed",
                "This account is not a Staff. Please select 'Login as Admin'.",
            )
            return

        self.username = db_username
        self.role = role
        self.accept()

