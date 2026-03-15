from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from database.init_db import get_connection
from services.password_service import hash_password, verify_password
from utils.icon_utils import get_app_icon


class LoginWindow(QDialog):
    """
    Login dialog that validates against the `users` table.
    Role is derived from the database after successful authentication.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Maternal Tracking - Login")
        self._build_ui()

        self.username: str | None = None
        self.role: str | None = None

    def _build_ui(self) -> None:
        size = 420
        self.setFixedSize(size, size)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        icon_label = QLabel()
        icon_label.setPixmap(get_app_icon().pixmap(64, 64))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title = QLabel("Maternal Tracker")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        layout.addSpacing(8)

        form = QFormLayout()
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")
        form.addRow("Username:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.Password)
        form.addRow("Password:", self.password_edit)

        self.show_password_cb = QCheckBox("Show password")
        self.show_password_cb.toggled.connect(self._on_show_password_toggled)
        form.addRow("", self.show_password_cb)

        layout.addLayout(form)
        layout.addStretch()

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.button_box.accepted.connect(self.handle_login)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.username_edit.setFocus()

    def _on_show_password_toggled(self, checked: bool) -> None:
        self.password_edit.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def handle_login(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter username and password.")
            self.password_edit.clear()
            self.password_edit.setFocus()
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
            self.password_edit.clear()
            self.password_edit.setFocus()
            return

        db_username, password_hash, role = row
        role = (role or "").upper()

        if not verify_password(password, password_hash or ""):
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
            self.password_edit.clear()
            self.password_edit.setFocus()
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

        self.username = db_username
        self.role = role
        self.accept()
