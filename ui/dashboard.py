from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import os
import shutil
import sys

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QShortcut, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QVBoxLayout,
    QWidget,
)

from config import get_admin_area_password
from database.init_db import get_connection
from utils.date_utils import parse_date as parse_date_flex
from services.backup_service import (
    get_backup_dir_path,
    list_backups,
    create_manual_backup,
    restore_backup,
)
from services.excel_import_service import import_from_excel
from services.visit_scheduler import UPCOMING_DAYS, EDD_UPCOMING_DAYS
from ui.administration import AdministrationWidget
from ui.change_password_dialog import ChangePasswordDialog
from ui.login_window import LoginWindow
from ui.patient_entry import PatientEntryDialog
from ui.patient_search import PatientSearchDialog
from ui.reports import ReportsWidget


class DashboardWindow(QMainWindow):
    """
    Main application window with left sidebar navigation and
    stacked content area.
    """
    logout_requested = Signal()

    def __init__(self, username: str, role: str, parent=None):
        super().__init__(parent)
        self.username = username
        self.role = role

        self.setWindowTitle("Maternal Tracking")
        self._build_ui()
        self._update_header_datetime()
        self._datetime_timer = QTimer(self)
        self._datetime_timer.timeout.connect(self._update_header_datetime)
        self._datetime_timer.start(60000)  # Update every minute
        self.refresh_stats()
        self._setup_shortcuts()

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+N"), self, self.open_patient_entry)
        QShortcut(QKeySequence("Ctrl+F"), self, self.open_patient_search_dialog)

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(12)

        title_label = QLabel("Maternal Tracker System")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("sidebarTitle")

        sidebar_layout.addWidget(title_label)

        style = self.style()

        self.dashboard_btn = QPushButton(
            style.standardIcon(QStyle.SP_ComputerIcon), "  Dashboard"
        )
        self.dashboard_btn.setObjectName("navButton")
        self.dashboard_btn.clicked.connect(lambda: self._set_active_page(0))

        self.register_btn = QPushButton(
            style.standardIcon(QStyle.SP_FileDialogNewFolder), "  Register Patient"
        )
        self.register_btn.setObjectName("navButton")
        self.register_btn.clicked.connect(lambda: self._set_active_page(1))

        self.search_btn = QPushButton(
            style.standardIcon(QStyle.SP_FileDialogContentsView), "  Search Patients"
        )
        self.search_btn.setObjectName("navButton")
        self.search_btn.clicked.connect(lambda: self._set_active_page(2))

        self.reports_btn = QPushButton(
            style.standardIcon(QStyle.SP_FileDialogDetailedView), "  Reports"
        )
        self.reports_btn.setObjectName("navButton")
        self.reports_btn.clicked.connect(lambda: self._set_active_page(3))

        self.backup_btn = QPushButton(
            style.standardIcon(QStyle.SP_DialogSaveButton), "  Backup Manager"
        )
        self.backup_btn.setObjectName("navButton")
        self.backup_btn.clicked.connect(lambda: self._set_active_page(4))

        self.admin_btn = QPushButton(
            style.standardIcon(QStyle.SP_FileDialogInfoView), "  Administration Area"
        )
        self.admin_btn.setObjectName("navButton")
        self.admin_btn.clicked.connect(self._open_administration)
        self.admin_btn.setVisible(self.role.upper() == "ADMIN")

        for btn in (
            self.dashboard_btn,
            self.register_btn,
            self.search_btn,
            self.reports_btn,
            self.backup_btn,
            self.admin_btn,
        ):
            btn.setProperty("active", "false")
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        self.change_password_btn = QPushButton(
            style.standardIcon(QStyle.SP_DialogApplyButton), "  Change Password"
        )
        self.change_password_btn.setObjectName("navButton")
        self.change_password_btn.clicked.connect(self._change_password)
        sidebar_layout.addWidget(self.change_password_btn)

        self.logout_btn = QPushButton(
            style.standardIcon(QStyle.SP_DialogCloseButton), "  Logout"
        )
        self.logout_btn.setObjectName("navButton")
        self.logout_btn.clicked.connect(self._logout)
        sidebar_layout.addWidget(self.logout_btn)

        # Developer section - footer block with divider
        dev_separator = QFrame()
        dev_separator.setObjectName("sidebarDevSeparator")
        dev_separator.setFrameShape(QFrame.HLine)
        dev_separator.setFrameShadow(QFrame.Sunken)
        sidebar_layout.addWidget(dev_separator)

        dev_footer = QFrame()
        dev_footer.setObjectName("sidebarDevFooter")
        dev_footer.setMinimumHeight(80)
        dev_layout = QVBoxLayout(dev_footer)
        dev_layout.setContentsMargins(8, 12, 8, 8)
        dev_layout.setSpacing(4)
        dev_label = QLabel(
            "Developed by Robiul\u00A0Molla\n"
            "iamrobiul94@gmail.com\n"
            "+91 7029655755"
        )
        dev_label.setAlignment(Qt.AlignCenter)
        dev_label.setObjectName("sidebarFooter")
        dev_label.setWordWrap(True)
        dev_layout.addWidget(dev_label)
        sidebar_layout.addWidget(dev_footer)

        # Main content area with header bar
        content_wrapper = QWidget()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top header bar - date/time left, app name + logo right
        header_style = self.style()
        header_bar = QFrame()
        header_bar.setObjectName("appHeaderBar")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(20, 12, 24, 12)
        self.header_datetime_label = QLabel()
        self.header_datetime_label.setObjectName("headerDateTime")
        self.header_datetime_label.setMinimumWidth(200)
        self.header_datetime_label.setAutoFillBackground(False)
        header_layout.addWidget(self.header_datetime_label)
        header_layout.addStretch()
        title_container = QWidget()
        title_container.setAutoFillBackground(False)
        title_h = QHBoxLayout(title_container)
        title_h.setContentsMargins(0, 0, 0, 0)
        title_h.setSpacing(10)
        header_icon = QLabel()
        header_icon.setAutoFillBackground(False)
        header_pix = header_style.standardPixmap(QStyle.SP_ComputerIcon)
        if not header_pix.isNull():
            header_icon.setPixmap(header_pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_icon.setFixedSize(32, 32)
        header_icon.setAlignment(Qt.AlignCenter)
        title_h.addWidget(header_icon)
        self.app_title_label = QLabel("Maternal Tracker System")
        self.app_title_label.setObjectName("appTitle")
        self.app_title_label.setAutoFillBackground(False)
        title_h.addWidget(self.app_title_label)
        header_layout.addWidget(title_container)

        content_layout.addWidget(header_bar)
        self.stack = QStackedWidget()

        # Page 0: Dashboard
        self.dashboard_page = QWidget()
        dash_layout = QVBoxLayout(self.dashboard_page)
        dash_layout.setContentsMargins(24, 24, 24, 24)
        dash_layout.setSpacing(20)
        style = self.style()

        # Top bar quick actions + Refresh - grouped in styled container
        top_bar_frame = QFrame()
        top_bar_frame.setObjectName("topBarActions")
        top_bar = QHBoxLayout(top_bar_frame)
        top_bar.setContentsMargins(16, 12, 16, 12)
        top_bar.setSpacing(12)
        self.new_patient_btn = QPushButton("New / Edit Patient")
        self.new_patient_btn.clicked.connect(self.open_patient_entry)
        self.search_dialog_btn = QPushButton("Search / Export Patients")
        self.search_dialog_btn.clicked.connect(self.open_patient_search_dialog)
        self.refresh_stats_btn = QPushButton(
            style.standardIcon(QStyle.SP_BrowserReload), " Refresh"
        )
        self.refresh_stats_btn.clicked.connect(self._on_refresh_stats_clicked)
        top_bar.addWidget(self.new_patient_btn)
        top_bar.addWidget(self.search_dialog_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.refresh_stats_btn)
        dash_layout.addWidget(top_bar_frame)

        # Statistics cards section - 2 rows so all cards fully visible, no side cut
        cards_layout = QGridLayout()
        cards_layout.setSpacing(20)
        cards_layout.setContentsMargins(0, 8, 0, 0)

        def make_card(
            title: str,
            object_name: str,
            filter_mode: str | None,
            icon_style: QStyle.StandardPixmap,
            tooltip: str,
            row: int,
            col: int,
            col_span: int = 1,
        ) -> tuple[QFrame, QLabel, QLabel | None]:
            frame = QFrame()
            frame.setObjectName(object_name)
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setMinimumHeight(110)
            frame.setMinimumWidth(180)
            frame.setCursor(Qt.PointingHandCursor)
            frame.setToolTip(tooltip)

            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(14)
            shadow.setXOffset(0)
            shadow.setYOffset(3)
            shadow.setColor(QColor(0, 0, 0, 60))
            frame.setGraphicsEffect(shadow)

            h = QHBoxLayout(frame)
            h.setContentsMargins(16, 16, 16, 16)
            h.setSpacing(12)
            icon_label = QLabel()
            pix = style.standardPixmap(icon_style)
            if not pix.isNull():
                icon_label.setPixmap(pix.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon_label.setFixedSize(36, 36)
            icon_label.setAlignment(Qt.AlignCenter)
            h.addWidget(icon_label)

            v = QVBoxLayout()
            v.setSpacing(4)
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            title_label.setObjectName("cardTitle")
            title_label.setToolTip(tooltip)

            value_label = QLabel("0")
            value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            value_label.setObjectName("cardValue")
            value_label.setToolTip(tooltip)

            trend_label = QLabel()
            trend_label.setObjectName("cardTrend")
            trend_label.setVisible(False)

            v.addWidget(title_label)
            v.addWidget(value_label)
            v.addWidget(trend_label)
            v.addStretch()
            h.addLayout(v, 1)

            cards_layout.addWidget(frame, row, col, 1, col_span)
            if filter_mode:
                frame.mousePressEvent = lambda e, fm=filter_mode: self._open_search_with_filter(fm)
            return frame, value_label, trend_label

        _, self.due_soon_label, _ = make_card(
            "Next Visit Due This Week",
            "cardDueSoon",
            "due_soon",
            QStyle.SP_FileDialogContentsView,
            "Patients whose next scheduled visit (1st, 2nd, 3rd, or Final) is within the next 7 days. Click to view.",
            0, 0,
        )
        _, self.overdue_label, _ = make_card(
            "Overdue Visits",
            "cardOverdue",
            "overdue",
            QStyle.SP_MessageBoxWarning,
            "Patients with at least one visit date that has already passed. Click to view.",
            0, 1,
        )
        _, self.edd_30_label, _ = make_card(
            "EDD Within 30 Days",
            "cardEddSoon",
            "edd_30",
            QStyle.SP_FileDialogInfoView,
            "Patients with Expected Delivery Date in the next 30 days. Click to view.",
            0, 2,
        )
        _, self.today_entries_label, _ = make_card(
            "Today's Entries",
            "cardTodayEntries",
            "today_entries",
            QStyle.SP_FileDialogNewFolder,
            "Patients registered today. Click to view.",
            1, 0,
        )
        _, self.total_patients_label, self.total_patients_trend = make_card(
            "Total Patients",
            "cardTotalPatients",
            "all",
            QStyle.SP_ComputerIcon,
            "All patient records. Click to view and filter by date.",
            1, 1,
            2,  # col_span: balance layout by spanning 2 columns
        )

        dash_layout.addLayout(cards_layout)
        self.stack.addWidget(self.dashboard_page)

        # Page 1: Register Patient
        self.register_page = QWidget()
        reg_layout = QVBoxLayout(self.register_page)
        reg_layout.setContentsMargins(24, 24, 24, 24)
        reg_label = QLabel("Register new maternal patient records.")
        reg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        reg_layout.addWidget(reg_label)
        reg_layout.addSpacing(12)
        reg_button = QPushButton("Open Patient Entry Form")
        reg_button.clicked.connect(self.open_patient_entry)
        reg_layout.addWidget(reg_button)
        reg_layout.addStretch()

        self.stack.addWidget(self.register_page)

        # Page 2: Search Patients
        self.search_page = QWidget()
        s_layout = QVBoxLayout(self.search_page)
        s_layout.setContentsMargins(24, 24, 24, 24)
        s_label = QLabel("Search, filter, and export patient records.")
        s_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        s_layout.addWidget(s_label)
        s_layout.addSpacing(12)
        s_button = QPushButton("Open Patient Search")
        s_button.clicked.connect(self.open_patient_search_dialog)
        s_layout.addWidget(s_button)
        s_layout.addStretch()

        self.stack.addWidget(self.search_page)

        # Page 3: Reports
        self.reports_page = ReportsWidget()
        self.stack.addWidget(self.reports_page)

        # Page 4: Backup Manager
        self.backup_page = QWidget()
        b_layout = QVBoxLayout(self.backup_page)
        b_layout.setContentsMargins(24, 24, 24, 24)
        b_layout.setSpacing(16)

        # Header with backup folder path
        b_header = QVBoxLayout()
        b_label = QLabel("Manage database backups")
        b_label.setObjectName("sectionTitle")
        b_header.addWidget(b_label)
        self.backup_folder_label = QLabel(f"Backup folder: {get_backup_dir_path()}")
        self.backup_folder_label.setObjectName("backupFolderPath")
        self.backup_folder_label.setWordWrap(True)
        b_header.addWidget(self.backup_folder_label)
        b_layout.addLayout(b_header)

        # Action buttons - grouped
        b_btn_row = QHBoxLayout()
        self.backup_now_btn = QPushButton("Create Backup Now")
        self.backup_now_btn.clicked.connect(self._do_manual_backup)
        self.refresh_backup_btn = QPushButton("Refresh List")
        self.refresh_backup_btn.clicked.connect(self._refresh_backup_list)
        self.open_folder_btn = QPushButton("Open Backup Folder")
        self.open_folder_btn.clicked.connect(self._open_backup_folder)
        b_btn_row.addWidget(self.backup_now_btn)
        b_btn_row.addWidget(self.refresh_backup_btn)
        b_btn_row.addWidget(self.open_folder_btn)
        b_btn_row.addStretch()
        b_layout.addLayout(b_btn_row)

        # Backups table
        b_table_label = QLabel("Available backups (newest first). Select one to restore or save elsewhere.")
        b_layout.addWidget(b_table_label)
        self.backup_table = QTableWidget()
        self.backup_table.setObjectName("dataTable")
        self.backup_table.setColumnCount(4)
        self.backup_table.setHorizontalHeaderLabels(["Date", "Size", "Filename", "Path"])
        self.backup_table.horizontalHeader().setVisible(True)
        self.backup_table.horizontalHeader().setMinimumHeight(40)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.backup_table.setSelectionMode(QTableWidget.SingleSelection)
        self.backup_table.setAlternatingRowColors(True)
        self.backup_table.horizontalHeader().setStretchLastSection(True)
        self.backup_table.setColumnHidden(3, True)
        self.backup_table.setMinimumHeight(200)
        b_layout.addWidget(self.backup_table)

        # Row actions
        b_action_row = QHBoxLayout()
        self.restore_btn = QPushButton("Restore Selected")
        self.restore_btn.clicked.connect(self._restore_selected_backup)
        self.save_to_pc_btn = QPushButton("Save Selected to Location...")
        self.save_to_pc_btn.clicked.connect(self._save_backup_to_pc)
        self.restore_from_file_btn = QPushButton("Restore from File...")
        self.restore_from_file_btn.clicked.connect(self._restore_from_file)
        b_action_row.addWidget(self.restore_btn)
        b_action_row.addWidget(self.save_to_pc_btn)
        b_action_row.addWidget(self.restore_from_file_btn)
        b_action_row.addStretch()
        b_layout.addLayout(b_action_row)

        # Import section
        b_import_sep = QFrame()
        b_import_sep.setFrameShape(QFrame.HLine)
        b_import_sep.setFrameShadow(QFrame.Sunken)
        b_layout.addWidget(b_import_sep)
        b_import_label = QLabel("Import patient records from Excel")
        b_import_label.setObjectName("sectionTitle")
        b_layout.addWidget(b_import_label)
        self.import_excel_btn = QPushButton("Import from Excel...")
        self.import_excel_btn.clicked.connect(self._import_from_excel)
        b_layout.addWidget(self.import_excel_btn)

        self.stack.addWidget(self.backup_page)

        # Page 5: Administration Area (ADMIN only)
        self.admin_page = AdministrationWidget(
            username=self.username, role=self.role, parent=self
        )
        self.stack.addWidget(self.admin_page)

        root_layout.addWidget(sidebar)
        content_layout.addWidget(self.stack, 1)
        root_layout.addWidget(content_wrapper, 1)

        self.setCentralWidget(central)

        # Default page
        self._set_active_page(0)

    def _update_header_datetime(self) -> None:
        """Update the date/time display in the header."""
        now = datetime.now()
        # Shorter format to prevent truncation: "Sun, 10 Mar 2024  02:21 AM"
        self.header_datetime_label.setText(now.strftime("%a, %d %b %Y  %I:%M %p"))

    def _on_refresh_stats_clicked(self) -> None:
        """Refresh stats with loading skeleton."""
        self.due_soon_label.setText("▮▮")
        self.overdue_label.setText("▮▮")
        self.edd_30_label.setText("▮▮")
        self.today_entries_label.setText("▮▮")
        self.total_patients_label.setText("▮▮")
        self.total_patients_trend.setVisible(False)
        QApplication.processEvents()
        self.refresh_stats()

    def refresh_stats(self) -> None:
        today = date.today()
        upcoming_limit = today + timedelta(days=UPCOMING_DAYS)
        edd_limit = today + timedelta(days=EDD_UPCOMING_DAYS)

        conn = get_connection()
        try:
            cur = conn.cursor()

            # Next Visit Due This Week: count only when patient's NEXT visit (earliest future) is within 7 days
            cur.execute(
                """
                SELECT visit1, visit2, visit3, final_visit FROM patients
                """
            )
            due_soon_count = 0
            for row in cur.fetchall():
                visit_dates = []
                for v in row:
                    if v:
                        d = parse_date_flex(v)
                        if d:
                            visit_dates.append(d)
                future = [d for d in visit_dates if d >= today]
                if future:
                    next_visit = min(future)
                    if today <= next_visit <= upcoming_limit:
                        due_soon_count += 1

            # Overdue visits (any visit date before today)
            cur.execute(
                """
                SELECT COUNT(*) FROM patients
                WHERE (
                    (visit1 IS NOT NULL AND visit1 < ?)
                    OR (visit2 IS NOT NULL AND visit2 < ?)
                    OR (visit3 IS NOT NULL AND visit3 < ?)
                    OR (final_visit IS NOT NULL AND final_visit < ?)
                )
                """,
                (
                    today.isoformat(),
                    today.isoformat(),
                    today.isoformat(),
                    today.isoformat(),
                ),
            )
            overdue_count = cur.fetchone()[0] or 0

            # EDD within 30 days
            cur.execute(
                """
                SELECT COUNT(*) FROM patients
                WHERE edd_date BETWEEN ? AND ?
                """,
                (today.isoformat(), edd_limit.isoformat()),
            )
            edd_soon_count = cur.fetchone()[0] or 0

            # Entries created today
            cur.execute(
                """
                SELECT COUNT(*) FROM patients
                WHERE date(entry_date) = date(?)
                """,
                (today.isoformat(),),
            )
            today_entries_count = cur.fetchone()[0] or 0

            # Total patients
            cur.execute("SELECT COUNT(*) FROM patients")
            total_patients_count = cur.fetchone()[0] or 0

            # New registrations this week (for trend)
            week_start = today - timedelta(days=today.weekday())
            cur.execute(
                "SELECT COUNT(*) FROM patients WHERE date(entry_date) >= ?",
                (week_start.isoformat(),),
            )
            this_week_new = cur.fetchone()[0] or 0

        finally:
            conn.close()

        self.due_soon_label.setText(str(due_soon_count))
        self.overdue_label.setText(str(overdue_count))
        self.edd_30_label.setText(str(edd_soon_count))
        self.today_entries_label.setText(str(today_entries_count))
        self.total_patients_label.setText(str(total_patients_count))

        if this_week_new > 0:
            self.total_patients_trend.setText(f"+{this_week_new} this week")
            self.total_patients_trend.setVisible(True)
        else:
            self.total_patients_trend.setVisible(False)

        # Badge highlight for overdue card when count > 0
        overdue_card = self.dashboard_page.findChild(QFrame, "cardOverdue")
        if overdue_card:
            overdue_card.setProperty("badge", "true" if overdue_count > 0 else "false")
            overdue_card.style().unpolish(overdue_card)
            overdue_card.style().polish(overdue_card)

    def _change_password(self) -> None:
        dialog = ChangePasswordDialog(username=self.username, parent=self)
        dialog.exec()

    def _logout(self) -> None:
        self.hide()
        login = LoginWindow()
        if login.exec() == QDialog.Accepted and login.username and login.role:
            self.username = login.username
            self.role = login.role.upper()
            self.admin_btn.setVisible(self.role == "ADMIN")
            # Refresh admin page with new user
            self.stack.removeWidget(self.admin_page)
            self.admin_page = AdministrationWidget(
                username=self.username, role=self.role, parent=self
            )
            self.stack.addWidget(self.admin_page)
            self.showMaximized()
        else:
            self.close()
            QApplication.instance().quit()

    def _open_administration(self) -> None:
        """Prompt for admin password before opening Administration Area."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Administration Area - Enter Password")
        layout = QFormLayout(dlg)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        dlg.setMinimumWidth(320)
        pwd_edit = QLineEdit()
        pwd_edit.setEchoMode(QLineEdit.Password)
        pwd_edit.setPlaceholderText("Enter password")
        layout.addRow("Password:", pwd_edit)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)
        if dlg.exec() == QDialog.Accepted:
            if pwd_edit.text().strip() == get_admin_area_password():
                self._set_active_page(5)
            else:
                QMessageBox.warning(
                    self,
                    "Access Denied",
                    "Incorrect password. You cannot access the Administration Area.",
                )

    def _set_active_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if index == 4:
            self._refresh_backup_list()

        nav_buttons = [
            self.dashboard_btn,
            self.register_btn,
            self.search_btn,
            self.reports_btn,
            self.backup_btn,
            self.admin_btn,
        ]
        for i, btn in enumerate(nav_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def open_patient_entry(self) -> None:
        dialog = PatientEntryDialog(username=self.username, role=self.role, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_stats()

    def _open_search_with_filter(self, filter_mode: str) -> None:
        dialog = PatientSearchDialog(
            username=self.username, role=self.role, parent=self, filter_mode=filter_mode
        )
        dialog.exec()
        self.refresh_stats()

    def open_patient_search_dialog(self) -> None:
        dialog = PatientSearchDialog(username=self.username, role=self.role, parent=self)
        dialog.exec()
        # Stats may have changed if user edited records from search dialog
        self.refresh_stats()

    def _refresh_backup_list(self) -> None:
        backups = list_backups()
        self.backup_table.setRowCount(len(backups))
        for i, (path, date_str, size_bytes) in enumerate(backups):
            # Format date as dd-mm-yyyy
            try:
                parts = date_str.split("-")
                if len(parts) == 3:
                    date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
            except (IndexError, ValueError):
                pass
            size_str = f"{size_bytes / (1024*1024):.2f} MB" if size_bytes >= 1024*1024 else f"{size_bytes // 1024} KB"
            self.backup_table.setItem(i, 0, QTableWidgetItem(date_str))
            self.backup_table.setItem(i, 1, QTableWidgetItem(size_str))
            self.backup_table.setItem(i, 2, QTableWidgetItem(path.name))
            self.backup_table.setItem(i, 3, QTableWidgetItem(str(path)))
            self.backup_table.item(i, 2).setToolTip(str(path))

    def _do_manual_backup(self) -> None:
        result = create_manual_backup()
        if result:
            QMessageBox.information(
                self, "Backup", f"Backup created successfully:\n{result.name}"
            )
            self._refresh_backup_list()
        else:
            QMessageBox.warning(self, "Backup", "Could not create backup.")

    def _save_backup_to_pc(self) -> None:
        """Save a backup file to a location chosen by the user on their PC."""
        row = self.backup_table.currentRow()
        if row < 0:
            # No selection - create backup now and offer to save
            result = create_manual_backup()
            if not result:
                QMessageBox.warning(self, "Save", "Could not create backup.")
                return
            source_path = result
            self._refresh_backup_list()
        else:
            path_item = self.backup_table.item(row, 3)
            if not path_item:
                return
            source_path = Path(path_item.text())
            if not source_path.exists():
                QMessageBox.warning(
                    self, "Save", "Selected backup file no longer exists."
                )
                return

        default_name = source_path.name
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Backup to PC",
            default_name,
            "Database Files (*.db);;All Files (*)",
        )
        if not path:
            return
        try:
            shutil.copy2(source_path, path)
            QMessageBox.information(
                self,
                "Saved",
                f"Backup saved successfully to:\n{path}",
            )
        except OSError as e:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Could not save backup:\n{e}",
            )

    def _open_backup_folder(self) -> None:
        """Open the backup folder in the system file explorer."""
        import subprocess
        backup_dir = get_backup_dir_path()
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(str(backup_dir))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(backup_dir)], check=True)
            else:
                subprocess.run(["xdg-open", str(backup_dir)], check=True)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Open Folder",
                f"Could not open folder:\n{e}\n\nPath: {backup_dir}",
            )

    def _restore_from_file(self) -> None:
        """Restore from a .db file chosen by the user."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File to Restore",
            str(get_backup_dir_path()),
            "Database Files (*.db);;All Files (*)",
        )
        if not path:
            return
        p = Path(path)
        if not p.exists():
            QMessageBox.warning(self, "Restore", "File not found.")
            return
        reply = QMessageBox.question(
            self,
            "Restore Backup",
            f"Restore from:\n{p.name}\n\n"
            "This will replace the current database. The application will need to be restarted.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes and restore_backup(p):
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Restore Complete")
            msg.setText("Database restored successfully.")
            msg.setInformativeText("The application must restart to use the restored data.")
            restart_btn = msg.addButton("Restart Now", QMessageBox.YesRole)
            later_btn = msg.addButton("Restart Later", QMessageBox.NoRole)
            msg.exec()
            if msg.clickedButton() == restart_btn:
                self._restart_application()
        else:
            QMessageBox.critical(self, "Restore Failed", "Could not restore from backup.")

    def _restore_selected_backup(self) -> None:
        row = self.backup_table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, "Restore", "Please select a backup from the list above."
            )
            return
        path_item = self.backup_table.item(row, 3)
        if not path_item:
            return
        path = Path(path_item.text())
        reply = QMessageBox.question(
            self,
            "Restore Backup",
            f"Are you sure you want to restore from backup?\n\n"
            f"Date: {self.backup_table.item(row, 0).text()}\n\n"
            "This will replace the current database. The application will need to be restarted.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if restore_backup(path):
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Restore Complete")
                msg.setText("Database restored successfully.")
                msg.setInformativeText(
                    "The application must restart to use the restored data."
                )
                restart_btn = msg.addButton("Restart Now", QMessageBox.YesRole)
                later_btn = msg.addButton("Restart Later", QMessageBox.NoRole)
                msg.exec()
                if msg.clickedButton() == restart_btn:
                    self._restart_application()
            else:
                QMessageBox.critical(
                    self, "Restore Failed", "Could not restore from backup."
                )

    def _import_from_excel(self) -> None:
        """Import patient records from an Excel file. Saves a copy to backups/imports/."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel File",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)",
        )
        if not path:
            return
        try:
            imported, skipped, backup_path = import_from_excel(Path(path))
            msg_parts = [f"Imported: {imported} patient(s)"]
            if skipped > 0:
                msg_parts.append(f"Skipped: {skipped} (missing data or duplicate patient ID)")
            if backup_path and imported > 0:
                msg_parts.append(f"\nCopy saved to:\n{backup_path}")
            QMessageBox.information(
                self,
                "Import Complete",
                "\n".join(msg_parts),
            )
            self.refresh_stats()
        except ValueError as e:
            QMessageBox.warning(self, "Import Error", str(e))
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Could not import Excel file:\n{e}",
            )

    def _restart_application(self) -> None:
        """Restart the application to apply restored database."""
        app = QApplication.instance()
        if app:
            QTimer.singleShot(100, self._do_restart)

    def _do_restart(self) -> None:
        app = QApplication.instance()
        if app:
            app.quit()
        os.execv(sys.executable, [sys.executable] + sys.argv)

