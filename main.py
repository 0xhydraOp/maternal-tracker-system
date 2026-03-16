from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QApplication, QSplashScreen

from config import APP_VERSION, get_dark_mode
from database.init_db import init_db
from services.backup_service import ensure_today_backup
from styles import get_stylesheet
from ui.login_window import LoginWindow
from ui.dashboard import DashboardWindow
from utils.icon_utils import get_app_icon


def main() -> int:
    # Ensure database and tables exist and a default admin user is present if needed.
    init_db()

    app = QApplication(sys.argv)
    app.setWindowIcon(get_app_icon())

    # Splash screen while app loads
    pixmap = QPixmap(400, 200)
    pixmap.fill(QColor("#2c3e50"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("white"))
    painter.setFont(QFont("Segoe UI", 18))
    painter.drawText(pixmap.rect(), 0x0084, "Maternal Tracker System")
    painter.setFont(QFont("Segoe UI", 10))
    painter.drawText(0, 0, pixmap.width(), pixmap.height() - 20, 0x0084, f"v{APP_VERSION}  ·  Loading...")
    painter.end()
    splash = QSplashScreen(pixmap)
    splash.show()
    app.processEvents()

    # Global font for better readability
    app.setFont(QFont("Segoe UI", 10))

    # Global stylesheet - light or dark theme from config
    app.setStyleSheet(get_stylesheet(get_dark_mode()))

    # Perform an immediate backup for today and set up a daily timer.
    ensure_today_backup()

    timer = QTimer()
    timer.timeout.connect(ensure_today_backup)
    timer.start(24 * 60 * 60 * 1000)  # 24 hours

    login = LoginWindow()
    if login.exec() != LoginWindow.Accepted or not login.username or not login.role:
        splash.close()
        return 0

    window = DashboardWindow(username=login.username, role=login.role)
    window.showMaximized()
    splash.finish(window)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

