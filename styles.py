"""Application stylesheets for light and dark themes."""
from __future__ import annotations


def get_stylesheet(dark_mode: bool = False) -> str:
    """Return the application stylesheet for the given theme."""
    if dark_mode:
        return """
        QMainWindow, QDialog, QWidget {
            background-color: #1e1e2e;
        }

        QFormLayout QLabel {
            color: #cdd6f4;
            min-width: 120px;
        }

        QFrame {
            background-color: #2d2d3d;
            border-radius: 10px;
            border: 1px solid #3d3d4d;
            padding: 15px;
        }

        QFrame#sidebar {
            background-color: #1a1a2e;
            border-radius: 0;
            border: none;
            padding: 0;
        }

        QFrame#topBarActions {
            background-color: #2d2d3d;
            border: 1px solid #3d3d4d;
            border-radius: 8px;
        }

        QFrame#sidebarDevSeparator {
            background-color: #45475a;
            max-height: 1px;
            margin: 8px 0;
        }

        QFrame#sidebarDevFooter {
            background-color: rgba(137, 180, 250, 0.08);
            border-radius: 6px;
            border: 1px solid #3d3d4d;
        }

        QFrame#appHeaderBar {
            background-color: #2c3e50;
            border: none;
            border-bottom: 1px solid #3d3d4d;
            border-radius: 0;
            padding: 0;
            min-height: 48px;
        }

        QFrame#appHeaderBar QWidget,
        QFrame#appHeaderBar QLabel,
        QFrame#appHeaderBar QFrame {
            background-color: transparent;
            border: none;
        }

        QFrame#appTitleContainer {
            background-color: #2c3e50;
        }

        QLabel#appTitle {
            font-size: 18px;
            font-weight: bold;
            color: #ffffff;
            background-color: #2c3e50;
            letter-spacing: 1px;
            padding: 4px 0;
        }

        QLabel#sidebarTitle {
            font-size: 16px;
            font-weight: bold;
            color: #cdd6f4;
            padding: 10px;
            margin-bottom: 15px;
        }

        QLabel#sidebarFooter {
            font-size: 11px;
            font-weight: bold;
            color: #89b4fa;
            padding: 8px 4px;
            letter-spacing: 0.5px;
            word-wrap: break-word;
        }

        QLabel {
            color: #cdd6f4;
            font-weight: 600;
            font-size: 13px;
        }

        QLabel#sectionTitle {
            font-size: 15px;
            font-weight: bold;
            color: #cdd6f4;
        }

        QLabel#formLabel {
            color: #cdd6f4;
        }

        QLabel#requiredLabel {
            color: #f38ba8;
        }

        QCheckBox {
            color: #cdd6f4;
        }

        QRadioButton {
            color: #cdd6f4;
            background-color: transparent;
        }

        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border-radius: 8px;
            border: 2px solid #89b4fa;
            background-color: #313244;
        }

        QRadioButton::indicator:checked {
            background-color: #89b4fa;
        }

        QPushButton {
            background-color: #89b4fa;
            color: #1e1e2e;
            border-radius: 6px;
            padding: 8px 14px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #b4befe;
        }

        QPushButton#navButton {
            background-color: transparent;
            color: #a6adc8;
            border-radius: 0;
            padding: 12px;
            text-align: left;
        }

        QPushButton#navButton:hover {
            background-color: #313244;
            color: #cdd6f4;
        }

        QPushButton#navButton[active="true"] {
            background-color: #89b4fa;
            color: #1e1e2e;
        }

        QPushButton#navButton[active="false"] {
            background-color: transparent;
            color: #a6adc8;
        }

        QTabWidget::pane {
            background-color: #2d2d3d;
            border: 1px solid #3d3d4d;
            border-radius: 6px;
            margin-top: -1px;
        }

        QTabBar::tab {
            background-color: #313244;
            color: #cdd6f4;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #45475a;
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            min-width: 70px;
        }

        QTabBar::tab:hover {
            background-color: #45475a;
            color: #cdd6f4;
        }

        QTabBar::tab:selected {
            background-color: #2d2d3d;
            color: #cdd6f4;
            font-weight: bold;
            border-bottom: 1px solid #2d2d3d;
        }

        QDateEdit, QComboBox {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 6px;
        }

        QLineEdit {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 6px;
        }

        QLineEdit:focus {
            border: 2px solid #89b4fa;
        }

        QListView {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
        }

        QListView::item:selected {
            background-color: #89b4fa;
            color: #1e1e2e;
        }

        QGroupBox {
            font-weight: bold;
            color: #cdd6f4;
            border: 1px solid #3d3d4d;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 6px;
            color: #cdd6f4;
        }

        QScrollArea {
            background-color: #1e1e2e;
            border: none;
        }

        QDialogButtonBox QPushButton {
            min-width: 80px;
        }

        QMessageBox {
            background-color: #2d2d3d;
        }

        QCalendarWidget {
            background: #313244;
            border: 1px solid #45475a;
            border-radius: 8px;
        }
        QCalendarWidget QWidget {
            background-color: #313244;
            color: #cdd6f4;
        }
        QCalendarWidget QToolButton {
            background: #45475a;
            color: #cdd6f4;
            border: 1px solid #585b70;
            border-radius: 6px;
            padding: 6px 12px;
            min-width: 32px;
        }
        QCalendarWidget QToolButton:hover {
            background: #585b70;
            border-color: #89b4fa;
        }
        QCalendarWidget QAbstractItemView {
            background: #313244;
            color: #cdd6f4;
            selection-background-color: #89b4fa;
            selection-color: #1e1e2e;
            font-size: 13px;
        }
        QCalendarWidget QWidget#qt_calendar_weekdaycell {
            background: #45475a;
            color: #a6adc8;
            font-weight: bold;
        }

        QTableWidget, QTableView {
            background-color: #313244;
            color: #cdd6f4;
            gridline-color: #45475a;
            selection-background-color: #89b4fa;
            selection-color: #1e1e2e;
        }

        QHeaderView::section {
            background-color: #2c3e50;
            color: #ffffff;
            font-weight: bold;
            font-size: 13px;
            font-family: "Segoe UI", Arial, sans-serif;
            border: none;
            border-bottom: 2px solid #1a252f;
            padding: 8px;
            min-height: 36px;
        }

        QTableWidget::item {
            color: #cdd6f4;
        }

        QTableWidget::item:selected {
            background-color: #89b4fa;
            color: #1e1e2e;
        }

        QTableView::item:hover {
            background-color: #45475a;
        }

        QFrame#cardDueSoon, QFrame#cardOverdue,
        QFrame#cardEddSoon, QFrame#cardTodayEntries,
        QFrame#cardTotalPatients {
            background-color: #2d2d3d;
            color: #cdd6f4;
            border: 1px solid #3d3d4d;
            border-radius: 12px;
        }

        QFrame#cardDueSoon { border-left: 4px solid #89b4fa; }
        QFrame#cardOverdue { border-left: 4px solid #f38ba8; }
        QFrame#cardEddSoon { border-left: 4px solid #a6e3a1; }
        QFrame#cardTodayEntries { border-left: 4px solid #f9e2af; }
        QFrame#cardTotalPatients { border-left: 4px solid #cba6f7; }

        QFrame#cardDueSoon:hover, QFrame#cardOverdue:hover,
        QFrame#cardEddSoon:hover, QFrame#cardTodayEntries:hover,
        QFrame#cardTotalPatients:hover {
            background-color: #363646;
            border-color: #89b4fa;
        }

        QLabel#cardTrend {
            font-size: 11px;
            color: #a6e3a1;
        }

        QLabel#headerDateTime {
            font-size: 12px;
            color: #ffffff;
            background-color: #2c3e50;
            border: none;
            min-width: 220px;
        }

        QFrame#cardOverdue[badge="true"] {
            border-left: 4px solid #f38ba8;
            border: 1px solid #f38ba8;
        }

        QLabel#cardTitle {
            font-size: 14px;
            font-weight: bold;
            color: #cdd6f4;
        }

        QLabel#cardValue {
            font-size: 26px;
            font-weight: bold;
            color: #cdd6f4;
        }

        QLabel#backupFolderPath {
            font-size: 11px;
            color: #a6adc8;
            padding: 4px 0;
        }

        QLabel#resultCountLabel {
            font-size: 12px;
            color: #a6adc8;
        }

        QLabel#loadingLabel {
            font-size: 12px;
            color: #89b4fa;
            font-style: italic;
        }

        QTableWidget QHeaderView::section, QTableView QHeaderView::section,
        QTableWidget#dataTable QHeaderView::section,
        QTableWidget#patientSearchTable QHeaderView::section {
            background-color: #1a365d;
            color: #ffffff;
            font-weight: bold;
            font-size: 13px;
            font-family: "Segoe UI", Arial, sans-serif;
            border: none;
            border-bottom: 2px solid #1a252f;
            padding: 8px;
            min-height: 44px;
            min-width: 80px;
        }

        QTableWidget::item, QTableView::item {
            padding: 6px 8px;
        }

        QFrame#reportsFilterBar {
            background-color: #2d2d3d;
            border: 1px solid #3d3d4d;
            border-radius: 8px;
            padding: 12px;
        }
        QGroupBox#reportsGroup {
            font-weight: bold;
            border: 1px solid #3d3d4d;
            border-radius: 8px;
        }
        QFrame#chartSection {
            background-color: #2d2d3d;
            border: 1px solid #3d3d4d;
            border-radius: 8px;
            padding: 16px;
        }
        """
    # Light theme
    return """
        QMainWindow, QDialog, QWidget {
            background-color: #f5f7fb;
        }

        QFormLayout QLabel {
            color: #2d3436;
            min-width: 120px;
        }

        QFrame {
            background-color: #ffffff;
            border-radius: 10px;
            border: 1px solid #dcdde1;
            padding: 15px;
        }

        QFrame#sidebar {
            background-color: #2c3e50;
            border-radius: 0;
            border: none;
            padding: 0;
        }

        QFrame#topBarActions {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
        }

        QFrame#sidebarDevSeparator {
            background-color: #34495e;
            max-height: 1px;
            margin: 8px 0;
        }

        QFrame#sidebarDevFooter {
            background-color: rgba(44, 123, 229, 0.06);
            border-radius: 6px;
            border: 1px solid #34495e;
        }

        QFrame#appHeaderBar {
            background-color: #2c3e50;
            border: none;
            border-bottom: 1px solid #34495e;
            border-radius: 0;
            padding: 0;
            min-height: 48px;
        }

        QFrame#appHeaderBar QWidget,
        QFrame#appHeaderBar QLabel,
        QFrame#appHeaderBar QFrame {
            background-color: transparent;
            border: none;
        }

        QFrame#appTitleContainer {
            background-color: #2c3e50;
        }

        QLabel#appTitle {
            font-size: 18px;
            font-weight: bold;
            color: #ffffff;
            background-color: #2c3e50;
            letter-spacing: 1px;
            padding: 4px 0;
        }

        QLabel#headerDateTime {
            font-size: 12px;
            color: #ffffff;
            background-color: #2c3e50;
            border: none;
            min-width: 220px;
        }

        QLabel#sidebarTitle {
            font-size: 16px;
            font-weight: bold;
            color: white;
            padding: 10px;
            margin-bottom: 15px;
        }

        QLabel#sidebarFooter {
            font-size: 11px;
            font-weight: bold;
            color: #89b4fa;
            padding: 8px 4px;
            letter-spacing: 0.5px;
            word-wrap: break-word;
        }

        QLabel {
            color: #2d3436;
            font-weight: 600;
            font-size: 13px;
        }

        QLabel#sectionTitle {
            font-size: 15px;
            font-weight: bold;
            color: #2c3e50;
        }

        QLabel#formLabel {
            color: #2d3436;
        }

        QLabel#requiredLabel {
            color: #c0392b;
        }

        QCheckBox {
            color: #2d3436;
        }

        QRadioButton {
            color: #2d3436;
            background-color: transparent;
        }

        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border-radius: 8px;
            border: 2px solid #2c7be5;
            background-color: white;
        }

        QRadioButton::indicator:checked {
            background-color: #2c7be5;
        }

        QPushButton {
            background-color: #2c7be5;
            color: white;
            border-radius: 6px;
            padding: 8px 14px;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #1a5fd0;
        }

        QPushButton#navButton {
            background-color: transparent;
            color: #bdc3c7;
            border-radius: 0;
            padding: 12px;
            text-align: left;
        }

        QPushButton#navButton:hover {
            background-color: #34495e;
            color: white;
        }

        QPushButton#navButton[active="true"] {
            background-color: #1a5fd0;
            color: white;
        }

        QPushButton#navButton[active="false"] {
            background-color: transparent;
            color: #bdc3c7;
        }

        QTabWidget::pane {
            background-color: #ffffff;
            border: 1px solid #dcdde1;
            border-radius: 6px;
            margin-top: -1px;
        }

        QTabBar::tab {
            background-color: #e9ecef;
            color: #2c3e50;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #dee2e6;
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            min-width: 70px;
        }

        QTabBar::tab:hover {
            background-color: #dee2e6;
            color: #2c3e50;
        }

        QTabBar::tab:selected {
            background-color: #ffffff;
            color: #2c3e50;
            font-weight: bold;
            border-bottom: 1px solid #ffffff;
        }

        QDateEdit, QComboBox {
            background-color: white;
            color: #2d3436;
            border: 1px solid #dcdde1;
            border-radius: 6px;
            padding: 6px;
        }

        QLineEdit {
            background-color: white;
            color: #1f2d3d;
            border: 1px solid #cfd4da;
            border-radius: 6px;
            padding: 6px;
        }

        QLineEdit:focus {
            border: 2px solid #2c7be5;
            color: #1f2d3d;
        }

        QListView {
            background-color: white;
            color: black;
            border: 1px solid #cfd4da;
        }

        QListView::item:selected {
            background-color: #2c7be5;
            color: white;
        }

        QGroupBox {
            font-weight: bold;
            color: #2c3e50;
            border: 1px solid #dcdde1;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 6px;
            color: #2c3e50;
        }

        QScrollArea {
            background-color: #f5f7fb;
            border: none;
        }

        QDialogButtonBox QPushButton {
            min-width: 80px;
        }

        QMessageBox {
            background-color: #ffffff;
        }

        QCalendarWidget {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
        }
        QCalendarWidget QWidget {
            background-color: white;
            color: #2c3e50;
        }
        QCalendarWidget QToolButton {
            background: #f8f9fa;
            color: #2c3e50;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 6px 12px;
            min-width: 32px;
        }
        QCalendarWidget QToolButton:hover {
            background: #e9ecef;
            border-color: #2c7be5;
        }
        QCalendarWidget QAbstractItemView {
            background: white;
            color: #2c3e50;
            selection-background-color: #2c7be5;
            selection-color: white;
            font-size: 13px;
        }
        QCalendarWidget QWidget#qt_calendar_weekdaycell {
            background: #e9ecef;
            color: #495057;
            font-weight: bold;
        }

        QTableWidget, QTableView {
            background-color: white;
            color: #2c3e50;
            gridline-color: #dcdde1;
            selection-background-color: #2c7be5;
            selection-color: white;
        }

        QHeaderView::section {
            background-color: #2c3e50;
            color: #ffffff;
            font-weight: bold;
            font-size: 13px;
            font-family: "Segoe UI", Arial, sans-serif;
            border: none;
            border-bottom: 2px solid #1a252f;
            padding: 8px;
            min-height: 36px;
        }

        QTableWidget::item {
            color: #2c3e50;
        }

        QTableWidget::item:selected {
            background-color: #2c7be5;
            color: white;
        }

        QTableView::item:hover {
            background-color: #e3f2fd;
        }

        QFrame#cardDueSoon, QFrame#cardOverdue,
        QFrame#cardEddSoon, QFrame#cardTodayEntries,
        QFrame#cardTotalPatients {
            background-color: #ffffff;
            color: #2d3436;
            border: 1px solid #dcdde1;
            border-radius: 12px;
        }

        QFrame#cardDueSoon { border-left: 4px solid #2c7be5; }
        QFrame#cardOverdue { border-left: 4px solid #e74c3c; }
        QFrame#cardEddSoon { border-left: 4px solid #27ae60; }
        QFrame#cardTodayEntries { border-left: 4px solid #f39c12; }
        QFrame#cardTotalPatients { border-left: 4px solid #8e44ad; }

        QFrame#cardDueSoon:hover, QFrame#cardOverdue:hover,
        QFrame#cardEddSoon:hover, QFrame#cardTodayEntries:hover,
        QFrame#cardTotalPatients:hover {
            background-color: #f8f9fa;
            border-color: #2c7be5;
        }

        QLabel#cardTrend {
            font-size: 11px;
            color: #27ae60;
        }

        QLabel#headerDateTime {
            font-size: 12px;
            color: #ffffff;
            background-color: #2c3e50;
            border: none;
        }

        QFrame#cardOverdue[badge="true"] {
            border-left: 4px solid #e74c3c;
            border: 1px solid #e74c3c;
        }

        QLabel#cardTitle {
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
        }

        QLabel#cardValue {
            font-size: 26px;
            font-weight: bold;
            color: #2c3e50;
        }

        QLabel#sidebarFooter {
            font-size: 11px;
            font-weight: bold;
            font-style: italic;
            color: #89b4fa;
            padding: 8px;
        }

        QLabel#backupFolderPath {
            font-size: 11px;
            color: #6c757d;
            padding: 4px 0;
        }

        QLabel#resultCountLabel {
            font-size: 12px;
            color: #6c757d;
        }

        QLabel#loadingLabel {
            font-size: 12px;
            color: #2c7be5;
            font-style: italic;
        }

        QTableWidget QHeaderView::section, QTableView QHeaderView::section,
        QTableWidget#dataTable QHeaderView::section,
        QTableWidget#patientSearchTable QHeaderView::section {
            background-color: #2c7be5;
            color: #ffffff;
            font-weight: bold;
            font-size: 13px;
            font-family: "Segoe UI", Arial, sans-serif;
            border: none;
            border-bottom: 2px solid #1a5fd0;
            padding: 8px;
            min-height: 44px;
            min-width: 80px;
        }

        QTableWidget::item, QTableView::item {
            padding: 6px 8px;
        }

        QTableWidget#patientSearchTable {
            background-color: white;
            color: #2c3e50;
        }
        QTableWidget#patientSearchTable::item {
            color: #2c3e50;
        }

        QFrame#reportsFilterBar {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 12px;
        }
        QGroupBox#reportsGroup {
            font-weight: bold;
            border: 1px solid #dee2e6;
            border-radius: 8px;
        }
        QFrame#chartSection {
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 16px;
        }
        """
