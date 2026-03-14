"""
Change Password dialog - allows users to change their own password.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from database.init_db import get_connection
from services.password_service import hash_password, verify_password


class ChangePasswordDialog(QDialog):
    """Dialog for user to change their own password."""

    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self.username = username
        self.setWindowTitle("Change Password")
        layout = QFormLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        self.setMinimumWidth(360)
        self.current_edit = QLineEdit()
        self.current_edit.setEchoMode(QLineEdit.Password)
        self.current_edit.setPlaceholderText("Current password")
        layout.addRow("Current Password:", self.current_edit)
        self.new_edit = QLineEdit()
        self.new_edit.setEchoMode(QLineEdit.Password)
        self.new_edit.setPlaceholderText("New password")
        layout.addRow("New Password:", self.new_edit)
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit.setPlaceholderText("Confirm new password")
        layout.addRow("Confirm New:", self.confirm_edit)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._do_change)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def _do_change(self) -> None:
        current = self.current_edit.text()
        new_pwd = self.new_edit.text()
        confirm = self.confirm_edit.text()
        if not current:
            QMessageBox.warning(self, "Validation", "Enter your current password.")
            return
        if not new_pwd:
            QMessageBox.warning(self, "Validation", "Enter a new password.")
            return
        if new_pwd != confirm:
            QMessageBox.warning(self, "Validation", "New password and confirmation do not match.")
            return
        if len(new_pwd) < 6:
            QMessageBox.warning(self, "Validation", "New password must be at least 6 characters.")
            return
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT password_hash FROM users WHERE username = ?",
                (self.username,),
            )
            row = cur.fetchone()
            if not row:
                QMessageBox.warning(self, "Error", "User not found.")
                return
            if not verify_password(current, row[0] or ""):
                QMessageBox.warning(self, "Error", "Current password is incorrect.")
                return
            cur.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (hash_password(new_pwd), self.username),
            )
            conn.commit()
            QMessageBox.information(self, "Success", "Password changed successfully.")
            self.accept()
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()
