from __future__ import annotations

from datetime import date, timedelta
from typing import List, Tuple, Any, Optional

import pandas as pd
from PySide6.QtCore import Qt, QDate, QMargins

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSet,
    QBarSeries,
    QChart,
    QChartView,
    QValueAxis,
)
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QDateEdit,
    QTabWidget,
    QGroupBox,
    QFrame,
    QScrollArea,
)

from database.init_db import get_connection
from utils.date_utils import DATE_FORMAT_DISPLAY, format_for_display, parse_date as parse_date_flex
from services.location_service import get_block_names, get_municipality_names
from services.motivator_service import get_all_motivator_names
from services.visit_scheduler import get_next_visit_due


class ReportsWidget(QWidget):
    """
    Reports screen with filters (Entry Date, Month, Year, Motivator, Patient Name)
    and Excel export.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_rows: List[Tuple[Any, ...]] = []
        self._build_ui()

    def refresh_reports(self) -> None:
        """Reload all report data (call when navigating to Reports or after data changes)."""
        current_motivator = self.motivator_filter.currentText()
        self.motivator_filter.blockSignals(True)
        self.motivator_filter.clear()
        self.motivator_filter.addItem("Any motivator", None)
        self.motivator_filter.addItems(get_all_motivator_names())
        idx = self.motivator_filter.findText(current_motivator)
        if idx >= 0:
            self.motivator_filter.setCurrentIndex(idx)
        self.motivator_filter.blockSignals(False)
        self.location_type_combo.setCurrentIndex(0)
        self.location_value_combo.setVisible(False)
        self.location_value_combo.clear()
        self._load_data()
        self._apply_filters()
        self._load_visit_completion()
        self._load_motivator_performance()
        self._load_monthly_summary()
        self._load_block_municipality()
        self._load_charts()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        self.setMinimumWidth(1000)  # Ensure Reports area doesn't shrink too much
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMinimumHeight(550)

        def make_date_edit():
            e = QDateEdit()
            e.setCalendarPopup(True)
            e.setDisplayFormat(DATE_FORMAT_DISPLAY)
            e.setMaximumWidth(110)
            return e

        # Tab 1: Patient List
        patient_tab = QWidget()
        pt_layout = QVBoxLayout(patient_tab)
        pt_layout.setSpacing(12)
        pt_layout.setContentsMargins(0, 0, 0, 0)

        # Filter bar in a styled frame
        filter_frame = QFrame()
        filter_frame.setObjectName("reportsFilterBar")
        filter_bar = QHBoxLayout(filter_frame)
        filter_bar.setSpacing(12)
        self.date_preset_combo = QComboBox()
        self.date_preset_combo.addItems([
            "All", "Last 7 days", "Last 30 days", "This Month", "This Year", "Custom"
        ])
        self.date_preset_combo.setMinimumWidth(110)
        self.date_preset_combo.currentTextChanged.connect(self._on_date_preset_changed)
        filter_bar.addWidget(QLabel("Date:"))
        filter_bar.addWidget(self.date_preset_combo)

        self.from_date_edit = make_date_edit()
        self.from_date_edit.setDate(QDate(date.today().year, 1, 1))
        self.to_date_edit = make_date_edit()
        self.to_date_edit.setDate(QDate(date.today().year, date.today().month, date.today().day))
        self.to_label = QLabel("to")
        self.from_date_edit.setVisible(False)
        self.to_label.setVisible(False)
        self.to_date_edit.setVisible(False)
        self.from_date_edit.dateChanged.connect(self._apply_filters)
        self.to_date_edit.dateChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.from_date_edit)
        filter_bar.addWidget(self.to_label)
        filter_bar.addWidget(self.to_date_edit)

        self.patient_name_filter = QLineEdit()
        self.patient_name_filter.setPlaceholderText("Patient...")
        self.patient_name_filter.setMaximumWidth(120)
        filter_bar.addWidget(self.patient_name_filter)

        self.motivator_filter = QComboBox()
        self.motivator_filter.setEditable(True)
        self.motivator_filter.addItem("Any motivator", None)
        self.motivator_filter.addItems(get_all_motivator_names())
        self.motivator_filter.setMaximumWidth(130)
        filter_bar.addWidget(self.motivator_filter)

        self.village_filter = QLineEdit()
        self.village_filter.setPlaceholderText("Village...")
        self.village_filter.setMaximumWidth(100)
        filter_bar.addWidget(self.village_filter)

        filter_bar.addWidget(QLabel("Block/Municipality:"))
        self._block_names = list(get_block_names())
        self._municipality_names = list(get_municipality_names())
        self.location_type_combo = QComboBox()
        self.location_type_combo.setMinimumWidth(100)
        self.location_type_combo.addItems(["All", "Block", "Municipality"])
        self.location_type_combo.setCurrentIndex(0)
        self.location_type_combo.currentTextChanged.connect(self._on_location_type_changed)
        filter_bar.addWidget(self.location_type_combo)
        self.location_value_combo = QComboBox()
        self.location_value_combo.setMinimumWidth(130)
        self.location_value_combo.setVisible(False)
        self.location_value_combo.currentTextChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.location_value_combo)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply_filters)
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self._export_to_excel)
        filter_bar.addWidget(self.apply_btn)
        filter_bar.addWidget(self.export_btn)

        self.result_count_label = QLabel("")
        self.result_count_label.setObjectName("resultCountLabel")
        filter_bar.addStretch()
        filter_bar.addWidget(self.result_count_label)

        pt_layout.addWidget(filter_frame)

        self.table = QTableWidget()
        self.table.setObjectName("dataTable")
        self.table.setColumnCount(17)
        self.table.setHorizontalHeaderLabels(
            [
                "Serial No",
                "Entry Date",
                "Patient Name",
                "Patient ID",
                "Block",
                "Municipality",
                "Village",
                "Ward",
                "Mobile",
                "Motivator",
                "LMP Date",
                "EDD Date",
                "1st Visit",
                "2nd Visit",
                "3rd Visit",
                "Final Visit",
                "Remarks",
            ]
        )
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setMinimumSectionSize(80)
        self.table.setMinimumHeight(380)
        # Column widths so all content is fully visible; total ~1650px
        col_widths = [70, 95, 130, 100, 110, 120, 100, 65, 100, 120, 95, 95, 90, 90, 90, 95, 110]
        self.table.setMinimumWidth(sum(col_widths))
        for col, width in enumerate(col_widths):
            self.table.setColumnWidth(col, width)
        # Wrap in scroll area so table scrolls horizontally when window is narrow
        table_scroll = QScrollArea()
        table_scroll.setWidget(self.table)
        table_scroll.setWidgetResizable(False)  # Keep table size so horizontal scroll works
        table_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        table_scroll.setFrameShape(QFrame.NoFrame)
        table_scroll.setMinimumHeight(400)
        pt_layout.addWidget(table_scroll)

        self.tabs.addTab(patient_tab, "Patients")

        # Tab 2: Visit Completion
        visit_tab = QWidget()
        visit_tab_layout = QVBoxLayout(visit_tab)
        visit_tab_layout.setContentsMargins(0, 0, 0, 0)
        visit_group = QGroupBox("Visit Completion")
        visit_group.setObjectName("reportsGroup")
        v_layout = QVBoxLayout(visit_group)
        v_layout.setContentsMargins(16, 20, 16, 16)
        self.visit_completion_table = QTableWidget()
        self.visit_completion_table.setObjectName("dataTable")
        self.visit_completion_table.setColumnCount(5)
        self.visit_completion_table.setHorizontalHeaderLabels(
            ["Visit", "Completed", "Total", "Pending", "Completion %"]
        )
        self.visit_completion_table.setShowGrid(True)
        self.visit_completion_table.horizontalHeader().setVisible(True)
        self.visit_completion_table.horizontalHeader().setMinimumHeight(36)
        self.visit_completion_table.horizontalHeader().setMinimumSectionSize(80)
        self.visit_completion_table.horizontalHeader().setStretchLastSection(True)
        self.visit_completion_table.setMinimumWidth(480)
        for col, w in enumerate([120, 90, 70, 80, 100]):  # Ensure numeric columns fully visible
            self.visit_completion_table.setColumnWidth(col, w)
        v_layout.addWidget(self.visit_completion_table)
        visit_tab_layout.addWidget(visit_group)
        self.tabs.addTab(visit_tab, "Visits")

        # Tab 3: Motivator Performance
        motiv_tab = QWidget()
        motiv_tab_layout = QVBoxLayout(motiv_tab)
        motiv_tab_layout.setContentsMargins(0, 0, 0, 0)
        motiv_group = QGroupBox("By Motivator")
        motiv_group.setObjectName("reportsGroup")
        m_layout = QVBoxLayout(motiv_group)
        m_layout.setContentsMargins(16, 20, 16, 16)
        self.motivator_table = QTableWidget()
        self.motivator_table.setObjectName("dataTable")
        self.motivator_table.setColumnCount(6)
        self.motivator_table.setHorizontalHeaderLabels(
            ["Motivator", "Total", "Visit 1", "Visit 2", "Final", "Final %"]
        )
        self.motivator_table.horizontalHeader().setVisible(True)
        self.motivator_table.horizontalHeader().setMinimumHeight(36)
        self.motivator_table.horizontalHeader().setMinimumSectionSize(80)
        self.motivator_table.horizontalHeader().setStretchLastSection(True)
        self.motivator_table.setMinimumWidth(500)
        self.motivator_table.setShowGrid(True)
        for col, w in enumerate([180, 70, 80, 80, 70, 80]):  # Ensure numeric columns fully visible
            self.motivator_table.setColumnWidth(col, w)
        m_layout.addWidget(self.motivator_table)
        motiv_tab_layout.addWidget(motiv_group)
        self.tabs.addTab(motiv_tab, "Motivators")

        # Tab 4: Monthly Summary
        monthly_tab = QWidget()
        monthly_tab_layout = QVBoxLayout(monthly_tab)
        monthly_tab_layout.setContentsMargins(0, 0, 0, 0)
        monthly_group = QGroupBox("Last 12 Months")
        monthly_group.setObjectName("reportsGroup")
        mo_layout = QVBoxLayout(monthly_group)
        mo_layout.setContentsMargins(16, 20, 16, 16)
        self.monthly_table = QTableWidget()
        self.monthly_table.setObjectName("dataTable")
        self.monthly_table.setColumnCount(6)
        self.monthly_table.setHorizontalHeaderLabels(
            ["Month", "New Reg.", "Visits", "Overdue", "EDD", "Completed"]
        )
        self.monthly_table.horizontalHeader().setVisible(True)
        self.monthly_table.horizontalHeader().setMinimumHeight(36)
        self.monthly_table.horizontalHeader().setMinimumSectionSize(80)
        self.monthly_table.horizontalHeader().setStretchLastSection(True)
        self.monthly_table.setMinimumWidth(550)
        self.monthly_table.setShowGrid(True)
        for col, w in enumerate([120, 80, 70, 80, 70, 90]):  # Month, New Reg., Visits, Overdue, EDD, Completed
            self.monthly_table.setColumnWidth(col, w)
        mo_layout.addWidget(self.monthly_table)
        monthly_tab_layout.addWidget(monthly_group)
        self.tabs.addTab(monthly_tab, "Monthly")

        # Tab 5: Block & Municipality
        block_muni_tab = QWidget()
        bm_layout = QVBoxLayout(block_muni_tab)
        bm_layout.setContentsMargins(0, 0, 0, 0)

        block_group = QGroupBox("By Block")
        block_group.setObjectName("reportsGroup")
        bl_layout = QVBoxLayout(block_group)
        bl_layout.setContentsMargins(16, 20, 16, 16)
        self.block_table = QTableWidget()
        self.block_table.setObjectName("dataTable")
        self.block_table.setColumnCount(3)
        self.block_table.setHorizontalHeaderLabels(["Block/Municipality", "Patients", "Visits Completed"])
        self.block_table.horizontalHeader().setVisible(True)
        self.block_table.horizontalHeader().setMinimumHeight(36)
        self.block_table.horizontalHeader().setMinimumSectionSize(80)
        self.block_table.setMinimumWidth(450)
        self.block_table.setShowGrid(True)
        for col, w in enumerate([240, 100, 130]):
            self.block_table.setColumnWidth(col, w)
        self.block_table.horizontalHeader().setStretchLastSection(False)
        bl_layout.addWidget(self.block_table)
        bm_layout.addWidget(block_group)

        muni_group = QGroupBox("By Municipality")
        muni_group.setObjectName("reportsGroup")
        mu_layout = QVBoxLayout(muni_group)
        mu_layout.setContentsMargins(16, 20, 16, 16)
        self.municipality_table = QTableWidget()
        self.municipality_table.setObjectName("dataTable")
        self.municipality_table.setColumnCount(3)
        self.municipality_table.setHorizontalHeaderLabels(["Block/Municipality", "Patients", "Visits Completed"])
        self.municipality_table.horizontalHeader().setVisible(True)
        self.municipality_table.horizontalHeader().setMinimumHeight(36)
        self.municipality_table.horizontalHeader().setMinimumSectionSize(80)
        self.municipality_table.setMinimumWidth(450)
        self.municipality_table.setShowGrid(True)
        for col, w in enumerate([240, 100, 130]):
            self.municipality_table.setColumnWidth(col, w)
        self.municipality_table.horizontalHeader().setStretchLastSection(False)
        mu_layout.addWidget(self.municipality_table)
        bm_layout.addWidget(muni_group)

        self.tabs.addTab(block_muni_tab, "Block & Municipality")

        # Tab 6: Charts
        charts_tab = QWidget()
        charts_main = QVBoxLayout(charts_tab)
        charts_main.setContentsMargins(0, 0, 0, 0)
        charts_scroll = QScrollArea()
        charts_scroll.setWidgetResizable(True)
        charts_scroll.setFrameShape(QFrame.NoFrame)
        charts_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        charts_content = QWidget()
        charts_layout = QVBoxLayout(charts_content)
        charts_layout.setSpacing(20)

        def add_chart_section(title: str, chart_view: QChartView, extra_widgets: QWidget | None = None) -> None:
            section = QFrame()
            section.setObjectName("chartSection")
            s_layout = QVBoxLayout(section)
            s_layout.setContentsMargins(16, 16, 16, 16)
            s_layout.setSpacing(8)
            header = QHBoxLayout()
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet("font-weight: bold; font-size: 14px;")
            header.addWidget(title_lbl)
            if extra_widgets:
                header.addStretch()
                if isinstance(extra_widgets, QHBoxLayout):
                    header.addLayout(extra_widgets)
                else:
                    header.addWidget(extra_widgets)
            s_layout.addLayout(header)
            chart_view.setMinimumHeight(240)
            chart_view.setRenderHint(QPainter.Antialiasing)
            s_layout.addWidget(chart_view)
            charts_layout.addWidget(section)

        self.reg_month_combo = QComboBox()
        for m in range(1, 13):
            self.reg_month_combo.addItem(date(2000, m, 1).strftime("%B"), m)
        self.reg_year_combo = QComboBox()
        current_year = date.today().year
        for y in range(current_year, current_year - 10, -1):
            self.reg_year_combo.addItem(str(y), y)
        self.reg_month_combo.setCurrentIndex(date.today().month - 1)
        self.reg_year_combo.setCurrentIndex(0)
        reg_selector = QHBoxLayout()
        reg_selector.addWidget(QLabel("View:"))
        reg_selector.addWidget(self.reg_month_combo)
        reg_selector.addWidget(self.reg_year_combo)
        self.reg_month_combo.currentIndexChanged.connect(lambda: self._load_registrations_chart())
        self.reg_year_combo.currentIndexChanged.connect(lambda: self._load_registrations_chart())

        self.registrations_chart_view = QChartView()
        self.motivator_chart_view = QChartView()
        self.motivator_month_chart_view = QChartView()
        self.motivator_month_chart_view.setMinimumWidth(800)
        self.motivator_month_chart_view.setMinimumHeight(280)
        self.village_chart_view = QChartView()

        # Motivator month-wise: motivator selector + month/year for past 12 months
        self.motiv_month_combo = QComboBox()
        self.motiv_year_combo = QComboBox()
        current_year = date.today().year
        for y in range(current_year, current_year - 10, -1):
            self.motiv_year_combo.addItem(str(y), y)
        self.motiv_year_combo.setCurrentIndex(0)
        for m in range(1, 13):
            self.motiv_month_combo.addItem(date(2000, m, 1).strftime("%B"), m)
        self.motiv_month_combo.setCurrentIndex(date.today().month - 1)
        self.motivator_select_combo = QComboBox()
        self.motivator_select_combo.setMinimumWidth(160)
        motiv_selector = QHBoxLayout()
        motiv_selector.addWidget(QLabel("Motivator:"))
        motiv_selector.addWidget(self.motivator_select_combo)
        motiv_selector.addWidget(QLabel("View 12 months ending:"))
        motiv_selector.addWidget(self.motiv_month_combo)
        motiv_selector.addWidget(self.motiv_year_combo)
        self.motivator_select_combo.currentIndexChanged.connect(lambda: self._load_motivator_month_chart())
        self.motiv_month_combo.currentIndexChanged.connect(lambda: self._load_motivator_month_chart())
        self.motiv_year_combo.currentIndexChanged.connect(lambda: self._load_motivator_month_chart())

        add_chart_section("Registrations per Month", self.registrations_chart_view, reg_selector)
        add_chart_section("Top Motivators", self.motivator_chart_view)
        add_chart_section("Motivator Month-wise Performance", self.motivator_month_chart_view, motiv_selector)
        add_chart_section("Patients by Village", self.village_chart_view)

        charts_scroll.setWidget(charts_content)
        charts_main.addWidget(charts_scroll)
        self.tabs.addTab(charts_tab, "Charts")

        layout.addWidget(self.tabs)

        self._load_data()
        self._apply_filters()
        self._load_visit_completion()
        self._load_motivator_performance()
        self._load_monthly_summary()
        self._load_block_municipality()
        self._load_charts()

    def _on_date_preset_changed(self, text: str) -> None:
        show_custom = text == "Custom"
        self.from_date_edit.setVisible(show_custom)
        self.to_label.setVisible(show_custom)
        self.to_date_edit.setVisible(show_custom)
        self._apply_filters()

    def _on_location_type_changed(self, text: str) -> None:
        """Show block or municipality dropdown when selected."""
        self.location_value_combo.blockSignals(True)
        self.location_value_combo.clear()
        self.location_value_combo.setVisible(False)
        if text == "Block":
            self.location_value_combo.setVisible(True)
            self.location_value_combo.addItem("All blocks")
            self.location_value_combo.addItems(self._block_names)
            self.location_value_combo.setCurrentIndex(0)
        elif text == "Municipality":
            self.location_value_combo.setVisible(True)
            self.location_value_combo.addItem("All municipalities")
            self.location_value_combo.addItems(self._municipality_names)
            self.location_value_combo.setCurrentIndex(0)
        self.location_value_combo.blockSignals(False)
        self._apply_filters()

    def _load_data(self) -> None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    serial_number,
                    patient_name,
                    patient_id,
                    mobile_number,
                    motivator_name,
                    district_name,
                    block_name,
                    municipality_name,
                    village_name,
                    ward_number,
                    lmp_date,
                    edd_date,
                    visit1,
                    visit2,
                    visit3,
                    final_visit,
                    entry_date,
                    remarks
                FROM patients
                ORDER BY entry_date DESC, serial_number
                """
            )
            self._all_rows = list(cur.fetchall())
        finally:
            conn.close()

    def _apply_filters(self) -> None:
        today = date.today()
        preset = self.date_preset_combo.currentText()
        from_date = to_date = None
        if preset == "Last 7 days":
            to_date = today
            from_date = today - timedelta(days=6)
        elif preset == "Last 30 days":
            to_date = today
            from_date = today - timedelta(days=29)
        elif preset == "This Month":
            from_date = today.replace(day=1)
            if today.month == 12:
                to_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                to_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        elif preset == "This Year":
            from_date = today.replace(month=1, day=1)
            to_date = today.replace(month=12, day=31)
        elif preset == "Custom":
            if self.from_date_edit.date().isValid():
                qd = self.from_date_edit.date()
                from_date = date(qd.year(), qd.month(), qd.day())
            if self.to_date_edit.date().isValid():
                qd = self.to_date_edit.date()
                to_date = date(qd.year(), qd.month(), qd.day())
            if from_date and to_date and from_date > to_date:
                from_date, to_date = to_date, from_date

        motivator_f = self.motivator_filter.currentText().strip().lower()
        if motivator_f in ("any", "any motivator"):
            motivator_f = ""
        name_f = self.patient_name_filter.text().strip().lower()
        village_f = self.village_filter.text().strip().lower()
        location_type = self.location_type_combo.currentText()
        location_val = (self.location_value_combo.currentText() or "").strip()
        block_f = ""
        municipality_f = ""
        if location_type == "Block" and location_val and location_val not in ("All blocks", ""):
            block_f = location_val.lower()
        elif location_type == "Municipality" and location_val and location_val not in ("All municipalities", ""):
            municipality_f = location_val.lower()

        def parse_date(s: Any) -> Optional[date]:
            return parse_date_flex(s)

        filtered = []
        for row in self._all_rows:
            (
                serial_number,
                patient_name,
                patient_id,
                mobile_number,
                motivator_name,
                district_name,
                block_name,
                municipality_name,
                village_name,
                ward_number,
                lmp_date,
                edd_date,
                visit1,
                visit2,
                visit3,
                final_visit,
                entry_date_str,
                remarks,
            ) = row

            ent = parse_date(entry_date_str)
            if from_date and (not ent or ent < from_date):
                continue
            if to_date and (not ent or ent > to_date):
                continue
            if motivator_f and motivator_f not in str(motivator_name or "").lower():
                continue
            if name_f and name_f not in str(patient_name or "").lower():
                continue
            if village_f and village_f not in str(village_name or "").lower():
                continue
            if block_f and str(block_name or "").lower() != block_f:
                continue
            if municipality_f and str(municipality_name or "").lower() != municipality_f:
                continue

            filtered.append(row)

        self._populate_table(filtered)
        self.result_count_label.setText(f"{len(filtered)} record(s)")

    def _populate_table(self, rows: List[Tuple[Any, ...]]) -> None:
        # Column order: Serial, Entry Date, Patient Name, Patient ID, Block, Municipality, Village, Ward, Mobile, Motivator, LMP, EDD, Visits, Remarks
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            (serial_number, patient_name, patient_id, mobile_number, motivator_name,
             _district_name, block_name, municipality_name, village_name, ward_number,
             lmp_date, edd_date, visit1, visit2, visit3, final_visit, entry_date, remarks) = row
            display_values = [
                serial_number, entry_date, patient_name, patient_id, block_name, municipality_name,
                village_name, ward_number, mobile_number, motivator_name,
                lmp_date, edd_date, visit1, visit2, visit3, final_visit, remarks,
            ]
            for c, value in enumerate(display_values):
                # Date columns (1, 10-15): display as dd-mm-yyyy
                if c in (1, 10, 11, 12, 13, 14, 15):
                    d = parse_date_flex(value)
                    disp = format_for_display(d) if d else ("" if value is None else str(value))
                else:
                    disp = "" if value is None else str(value)
                item = QTableWidgetItem(disp)
                self.table.setItem(r, c, item)
        # Avoid resizeColumnsToContents - can cause half-visible numbers; use explicit widths

    def _export_to_excel(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel File",
            "reports.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not path:
            return

        headers = [
            "serial_number",
            "entry_date",
            "patient_name",
            "patient_id",
            "block_name",
            "municipality_name",
            "village_name",
            "ward_number",
            "mobile_number",
            "motivator_name",
            "lmp_date",
            "edd_date",
            "visit1",
            "visit2",
            "visit3",
            "final_visit",
            "remarks",
        ]
        data: List[dict] = []
        for row in range(self.table.rowCount()):
            row_data = {}
            for col, key in enumerate(headers):
                item = self.table.item(row, col)
                row_data[key] = item.text() if item is not None else ""
            data.append(row_data)

        try:
            df = pd.DataFrame(data)
            df.to_excel(path, index=False, engine="openpyxl")
            QMessageBox.information(
                self,
                "Export Complete",
                f"Exported {len(df)} record(s) to:\n{path}",
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not export to Excel:\n{exc}",
            )

    def _load_visit_completion(self) -> None:
        """Load visit completion rate report."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN visit1 IS NOT NULL AND visit1 != '' THEN 1 ELSE 0 END) as v1,
                    SUM(CASE WHEN visit2 IS NOT NULL AND visit2 != '' THEN 1 ELSE 0 END) as v2,
                    SUM(CASE WHEN visit3 IS NOT NULL AND visit3 != '' THEN 1 ELSE 0 END) as v3,
                    SUM(CASE WHEN final_visit IS NOT NULL AND final_visit != '' THEN 1 ELSE 0 END) as v4
                FROM patients
                """
            )
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return
        total, v1, v2, v3, v4 = row
        total = total or 0
        v1, v2, v3, v4 = v1 or 0, v2 or 0, v3 or 0, v4 or 0

        def pct(done: int, tot: int) -> str:
            return f"{(100 * done / tot):.1f}%" if tot else "0%"

        rows_data = [
            ("1st Visit", v1, total, total - v1, pct(v1, total)),
            ("2nd Visit", v2, total, total - v2, pct(v2, total)),
            ("3rd Visit", v3, total, total - v3, pct(v3, total)),
            ("Final Visit", v4, total, total - v4, pct(v4, total)),
        ]
        self.visit_completion_table.setRowCount(len(rows_data))
        for r, (visit, done, tot, pend, pct_str) in enumerate(rows_data):
            self.visit_completion_table.setItem(r, 0, QTableWidgetItem(visit))
            self.visit_completion_table.setItem(r, 1, QTableWidgetItem(str(done)))
            self.visit_completion_table.setItem(r, 2, QTableWidgetItem(str(tot)))
            self.visit_completion_table.setItem(r, 3, QTableWidgetItem(str(pend)))
            self.visit_completion_table.setItem(r, 4, QTableWidgetItem(pct_str))
        # Keep explicit column widths - avoid resizeColumnsToContents

    def _load_motivator_performance(self) -> None:
        """Load motivator performance report."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    COALESCE(motivator_name, 'Unknown') as motivator,
                    COUNT(*) as total,
                    SUM(CASE WHEN visit1 IS NOT NULL AND visit1 != '' THEN 1 ELSE 0 END) as v1,
                    SUM(CASE WHEN visit2 IS NOT NULL AND visit2 != '' THEN 1 ELSE 0 END) as v2,
                    SUM(CASE WHEN final_visit IS NOT NULL AND final_visit != '' THEN 1 ELSE 0 END) as v4
                FROM patients
                GROUP BY motivator_name
                ORDER BY total DESC
                """
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        self.motivator_table.setRowCount(len(rows))
        for r, (motivator, total, v1, v2, v4) in enumerate(rows):
            tot = total or 0
            final_count = v4 or 0
            final_pct = f"{(100 * final_count / tot):.1f}%" if tot else "0%"
            self.motivator_table.setItem(r, 0, QTableWidgetItem(str(motivator)))
            self.motivator_table.setItem(r, 1, QTableWidgetItem(str(tot)))
            self.motivator_table.setItem(r, 2, QTableWidgetItem(str(v1 or 0)))
            self.motivator_table.setItem(r, 3, QTableWidgetItem(str(v2 or 0)))
            self.motivator_table.setItem(r, 4, QTableWidgetItem(str(final_count)))
            self.motivator_table.setItem(r, 5, QTableWidgetItem(final_pct))
        # Keep explicit column widths - avoid resizeColumnsToContents

    def _load_monthly_summary(self) -> None:
        """Load monthly summary for last 12 months."""
        today = date.today()
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT entry_date, visit1, visit2, visit3, final_visit, edd_date, record_locked
                FROM patients
                """
            )
            all_rows = cur.fetchall()
        finally:
            conn.close()

        months_data = []
        for i in range(12):
            m = today.month - 1 - i
            y = today.year
            while m < 1:
                m += 12
                y -= 1
            month_start = date(y, m, 1)
            month_end = date(y, 12, 31) if m == 12 else date(y, m + 1, 1) - timedelta(days=1)

            new_reg = overdue = edd_in_month = completed = 0
            visits_in_month = set()  # patient indices with visit in this month

            for idx, row in enumerate(all_rows):
                entry_str, v1, v2, v3, final, edd_str = row[:6]
                record_locked = bool(row[6]) if len(row) > 6 else False
                ent = parse_date_flex(entry_str)
                if ent and month_start <= ent <= month_end:
                    new_reg += 1

                edd = parse_date_flex(edd_str)
                if edd and month_start <= edd <= month_end:
                    edd_in_month += 1

                final_d = parse_date_flex(final)
                if final_d and month_start <= final_d <= month_end:
                    completed += 1

                v1_d = parse_date_flex(v1)
                v2_d = parse_date_flex(v2)
                v3_d = parse_date_flex(v3)
                for v in (v1_d, v2_d, v3_d, final_d):
                    if v and month_start <= v <= month_end:
                        visits_in_month.add(idx)
                        break

                next_due = get_next_visit_due(v1_d, v2_d, v3_d, final_d, today, record_locked=record_locked)
                # Only count overdue when next_due is in the month AND has passed (truly overdue)
                if next_due and month_start <= next_due <= month_end and next_due < today:
                    has_visit_in_month = any(
                        v and month_start <= v <= month_end
                        for v in (v1_d, v2_d, v3_d, final_d)
                    )
                    if not has_visit_in_month:
                        overdue += 1

            months_data.append((
                month_start.strftime("%B %Y"),
                str(new_reg),
                str(len(visits_in_month)),
                str(overdue),
                str(edd_in_month),
                str(completed),
            ))

        self.monthly_table.setRowCount(len(months_data))
        for r, row in enumerate(months_data):
            for c, val in enumerate(row):
                self.monthly_table.setItem(r, c, QTableWidgetItem(val))
        # Keep explicit column widths - do not resize to avoid half-visible numbers

    def _load_block_municipality(self) -> None:
        """Load block-wise and municipality-wise patient and visit counts."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT block_name, COUNT(*) as patients,
                    SUM(CASE WHEN final_visit IS NOT NULL AND final_visit != '' THEN 1 ELSE 0 END) as completed
                FROM patients
                WHERE block_name IS NOT NULL AND block_name != ''
                GROUP BY block_name
                """
            )
            block_data = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

            block_table_data = []
            for b in get_block_names():
                p, c = block_data.get(b, (0, 0))
                block_table_data.append((b, str(p), str(c)))

            self.block_table.setRowCount(len(block_table_data))
            for r, (name, patients, completed) in enumerate(block_table_data):
                self.block_table.setItem(r, 0, QTableWidgetItem(name))
                self.block_table.setItem(r, 1, QTableWidgetItem(patients))
                self.block_table.setItem(r, 2, QTableWidgetItem(completed))

            cur.execute(
                """
                SELECT municipality_name, COUNT(*) as patients,
                    SUM(CASE WHEN final_visit IS NOT NULL AND final_visit != '' THEN 1 ELSE 0 END) as completed
                FROM patients
                WHERE municipality_name IS NOT NULL AND municipality_name != ''
                GROUP BY municipality_name
                """
            )
            muni_data = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

            muni_table_data = []
            for m in get_municipality_names():
                p, c = muni_data.get(m, (0, 0))
                muni_table_data.append((m, str(p), str(c)))

            self.municipality_table.setRowCount(len(muni_table_data))
            for r, (name, patients, completed) in enumerate(muni_table_data):
                self.municipality_table.setItem(r, 0, QTableWidgetItem(name))
                self.municipality_table.setItem(r, 1, QTableWidgetItem(patients))
                self.municipality_table.setItem(r, 2, QTableWidgetItem(completed))
        finally:
            conn.close()

    def _load_registrations_chart(self) -> None:
        """Load registrations chart for 12 months ending with selected month/year."""
        sel_month = self.reg_month_combo.currentData()
        sel_year = self.reg_year_combo.currentData()
        if not sel_month or not sel_year:
            return
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT entry_date FROM patients")
            entry_dates = [parse_date_flex(r[0]) for r in cur.fetchall()]
        finally:
            conn.close()

        # 12 months ending with selected month (rightmost bar = selected month)
        reg_data = []
        categories = []
        for i in range(11, -1, -1):
            m = sel_month - i
            y = sel_year
            while m < 1:
                m += 12
                y -= 1
            while m > 12:
                m -= 12
                y += 1
            month_start = date(y, m, 1)
            month_end = date(y, 12, 31) if m == 12 else date(y, m + 1, 1) - timedelta(days=1)
            count = sum(1 for d in entry_dates if d and month_start <= d <= month_end)
            reg_data.append(count)
            categories.append(month_start.strftime("%b %Y"))

        reg_set = QBarSet("Registrations")
        reg_set.append(reg_data)
        reg_series = QBarSeries()
        reg_series.append(reg_set)
        reg_chart = QChart()
        reg_chart.addSeries(reg_series)
        reg_chart.setTitle("New Patient Registrations per Month")
        reg_chart.setAnimationOptions(QChart.SeriesAnimations)
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        reg_chart.addAxis(axis_x, Qt.AlignBottom)
        reg_series.attachAxis(axis_x)
        axis_y = QValueAxis()
        axis_y.setRange(0, max(reg_data) + 1 if reg_data else 1)
        reg_chart.addAxis(axis_y, Qt.AlignLeft)
        reg_series.attachAxis(axis_y)
        reg_chart.legend().setVisible(False)
        self.registrations_chart_view.setChart(reg_chart)

    def _load_motivator_month_chart(self) -> None:
        """Load motivator month-wise performance for past 12 months."""
        motivator = self.motivator_select_combo.currentData()
        sel_month = self.motiv_month_combo.currentData()
        sel_year = self.motiv_year_combo.currentData()
        if not sel_month or not sel_year:
            return

        if not motivator:
            # Show placeholder with month labels when no motivator selected
            categories = []
            for i in range(11, -1, -1):
                m = sel_month - i
                y = sel_year
                while m < 1:
                    m += 12
                    y -= 1
                while m > 12:
                    m -= 12
                    y += 1
                month_start = date(y, m, 1)
                categories.append(month_start.strftime("%b '%y"))
            reg_set = QBarSet("Registrations")
            reg_set.append([0] * 12)
            reg_series = QBarSeries()
            reg_series.append(reg_set)
            motiv_chart = QChart()
            motiv_chart.addSeries(reg_series)
            motiv_chart.setTitle("Select a motivator to view their month-wise performance")
            motiv_chart.setAnimationOptions(QChart.SeriesAnimations)
            motiv_chart.setMargins(QMargins(45, 10, 10, 85))
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            axis_x.setLabelsAngle(-45)
            motiv_chart.addAxis(axis_x, Qt.AlignBottom)
            reg_series.attachAxis(axis_x)
            axis_y = QValueAxis()
            axis_y.setRange(0, 5)
            motiv_chart.addAxis(axis_y, Qt.AlignLeft)
            reg_series.attachAxis(axis_y)
            motiv_chart.legend().setVisible(False)
            self.motivator_month_chart_view.setChart(motiv_chart)
            return

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT entry_date FROM patients WHERE motivator_name = ?",
                (motivator,),
            )
            entry_dates = [parse_date_flex(r[0]) for r in cur.fetchall()]
        finally:
            conn.close()

        # 12 months ending with selected month
        month_data = []
        categories = []
        for i in range(11, -1, -1):
            m = sel_month - i
            y = sel_year
            while m < 1:
                m += 12
                y -= 1
            while m > 12:
                m -= 12
                y += 1
            month_start = date(y, m, 1)
            month_end = date(y, 12, 31) if m == 12 else date(y, m + 1, 1) - timedelta(days=1)
            count = sum(1 for d in entry_dates if d and month_start <= d <= month_end)
            month_data.append(count)
            categories.append(month_start.strftime("%b '%y"))

        reg_set = QBarSet("Registrations")
        reg_set.append(month_data)
        reg_series = QBarSeries()
        reg_series.append(reg_set)
        motiv_chart = QChart()
        motiv_chart.addSeries(reg_series)
        motiv_chart.setTitle(f"Registrations per Month: {motivator}")
        motiv_chart.setAnimationOptions(QChart.SeriesAnimations)
        motiv_chart.setMargins(QMargins(45, 10, 10, 85))
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsAngle(-45)
        motiv_chart.addAxis(axis_x, Qt.AlignBottom)
        reg_series.attachAxis(axis_x)
        axis_y = QValueAxis()
        axis_y.setRange(0, max(month_data) + 1 if month_data else 1)
        motiv_chart.addAxis(axis_y, Qt.AlignLeft)
        reg_series.attachAxis(axis_y)
        motiv_chart.legend().setVisible(False)
        self.motivator_month_chart_view.setChart(motiv_chart)

    def _load_charts(self) -> None:
        """Load bar charts for registrations, motivators, and villages."""
        motivator_rows = []
        village_rows = []
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT motivator_name, COUNT(*) as cnt
                FROM patients
                WHERE motivator_name IS NOT NULL AND motivator_name != ''
                GROUP BY motivator_name
                ORDER BY cnt DESC
                LIMIT 15
                """
            )
            motivator_rows = cur.fetchall()
            cur.execute(
                """
                SELECT motivator_name FROM patients
                WHERE motivator_name IS NOT NULL AND motivator_name != ''
                GROUP BY motivator_name
                ORDER BY motivator_name
                """
            )
            motivator_names_for_select = [r[0] for r in cur.fetchall()]
            cur.execute(
                """
                SELECT COALESCE(village_name, 'Unknown') as village, COUNT(*) as cnt
                FROM patients
                GROUP BY village_name
                ORDER BY cnt DESC
                LIMIT 15
                """
            )
            village_rows = cur.fetchall()
        finally:
            conn.close()

        # Populate motivator selector for month-wise chart
        self.motivator_select_combo.blockSignals(True)
        self.motivator_select_combo.clear()
        self.motivator_select_combo.addItem("Select motivator...", None)
        for name in motivator_names_for_select:
            self.motivator_select_combo.addItem(str(name), name)
        self.motivator_select_combo.blockSignals(False)

        self._load_registrations_chart()
        self._load_motivator_month_chart()

        # Motivator performance (top 15)
        motiv_names = [str(r[0])[:20] for r in motivator_rows]
        motiv_counts = [r[1] for r in motivator_rows]

        motiv_set = QBarSet("Patients")
        motiv_set.append(motiv_counts)

        motiv_series = QBarSeries()
        motiv_series.append(motiv_set)

        motiv_chart = QChart()
        motiv_chart.addSeries(motiv_series)
        motiv_chart.setTitle("Patients per Motivator (Top 15)")
        motiv_chart.setAnimationOptions(QChart.SeriesAnimations)

        motiv_axis_x = QBarCategoryAxis()
        motiv_axis_x.append(motiv_names if motiv_names else ["No data"])
        motiv_chart.addAxis(motiv_axis_x, Qt.AlignBottom)
        motiv_series.attachAxis(motiv_axis_x)

        motiv_axis_y = QValueAxis()
        motiv_axis_y.setRange(0, (max(motiv_counts) + 1) if motiv_counts else 5)
        motiv_chart.addAxis(motiv_axis_y, Qt.AlignLeft)
        motiv_series.attachAxis(motiv_axis_y)

        motiv_chart.legend().setVisible(False)
        self.motivator_chart_view.setChart(motiv_chart)

        # Village-wise (top 15)
        village_names = [str(r[0])[:20] for r in village_rows]
        village_counts = [r[1] for r in village_rows]

        village_set = QBarSet("Patients")
        village_set.append(village_counts)

        village_series = QBarSeries()
        village_series.append(village_set)

        village_chart = QChart()
        village_chart.addSeries(village_series)
        village_chart.setTitle("Patients per Village (Top 15)")
        village_chart.setAnimationOptions(QChart.SeriesAnimations)

        village_axis_x = QBarCategoryAxis()
        village_axis_x.append(village_names if village_names else ["No data"])
        village_chart.addAxis(village_axis_x, Qt.AlignBottom)
        village_series.attachAxis(village_axis_x)

        village_axis_y = QValueAxis()
        village_axis_y.setRange(0, (max(village_counts) + 1) if village_counts else 5)
        village_chart.addAxis(village_axis_y, Qt.AlignLeft)
        village_series.attachAxis(village_axis_y)

        village_chart.legend().setVisible(False)
        self.village_chart_view.setChart(village_chart)
