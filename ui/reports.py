from __future__ import annotations

from datetime import date
from typing import List, Tuple, Any, Optional

import pandas as pd
from PySide6.QtCore import Qt, QDate
from datetime import timedelta

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSet,
    QBarSeries,
    QChart,
    QChartView,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
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
    QScrollArea,
)

from database.init_db import get_connection
from utils.date_utils import DATE_FORMAT_DISPLAY, format_for_display, parse_date as parse_date_flex
from services.motivator_service import get_all_motivator_names


class ReportsWidget(QWidget):
    """
    Reports screen with filters (Entry Date, Month, Year, Motivator, Patient Name)
    and Excel export.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_rows: List[Tuple[Any, ...]] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.tabs = QTabWidget()

        # Tab 1: Patient List (existing)
        patient_tab = QWidget()
        pt_layout = QVBoxLayout(patient_tab)
        pt_layout.setSpacing(12)

        # Top: From Date - To Date filter
        date_range_row = QHBoxLayout()
        date_range_row.setSpacing(12)

        def make_date_edit():
            e = QDateEdit()
            e.setCalendarPopup(True)
            e.setDisplayFormat(DATE_FORMAT_DISPLAY)
            return e

        date_range_row.addWidget(QLabel("From Date:"))
        self.from_date_edit = make_date_edit()
        self.from_date_edit.setDate(QDate(date.today().year, 1, 1))
        date_range_row.addWidget(self.from_date_edit)
        date_range_row.addWidget(QLabel("To Date:"))
        self.to_date_edit = make_date_edit()
        self.to_date_edit.setDate(QDate(date.today().year, date.today().month, date.today().day))
        date_range_row.addWidget(self.to_date_edit)
        date_range_row.addStretch()
        pt_layout.addLayout(date_range_row)

        # Below: Month, Year, Motivator, Patient Name, Village
        filters_layout = QFormLayout()
        filters_layout.setHorizontalSpacing(20)
        filters_layout.setVerticalSpacing(10)

        self.month_combo = QComboBox()
        self.month_combo.addItem("Any", None)
        for m in range(1, 13):
            self.month_combo.addItem(date(2000, m, 1).strftime("%B"), m)

        self.year_combo = QComboBox()
        self.year_combo.addItem("Any", None)
        current_year = date.today().year
        for y in range(current_year, current_year - 20, -1):
            self.year_combo.addItem(str(y), y)

        self.motivator_filter = QComboBox()
        self.motivator_filter.setEditable(True)
        self.motivator_filter.addItem("Any", None)
        self.motivator_filter.addItems(get_all_motivator_names())

        self.patient_name_filter = QLineEdit()
        self.patient_name_filter.setPlaceholderText("Filter by patient name...")

        self.village_filter = QLineEdit()
        self.village_filter.setPlaceholderText("Filter by village...")

        filters_layout.addRow("Month:", self.month_combo)
        filters_layout.addRow("Year:", self.year_combo)
        filters_layout.addRow("Motivator:", self.motivator_filter)
        filters_layout.addRow("Patient Name:", self.patient_name_filter)
        filters_layout.addRow("Village:", self.village_filter)

        pt_layout.addLayout(filters_layout)

        btn_row = QHBoxLayout()
        self.apply_btn = QPushButton("Apply Filters")
        self.apply_btn.clicked.connect(self._apply_filters)
        self.export_btn = QPushButton("Export to Excel")
        self.export_btn.clicked.connect(self._export_to_excel)
        btn_row.addWidget(self.apply_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.export_btn)
        pt_layout.addLayout(btn_row)

        self.table = QTableWidget()
        self.table.setObjectName("dataTable")
        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels(
            [
                "Serial No",
                "Entry Date",
                "Patient Name",
                "Patient ID",
                "Village",
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
        self.table.horizontalHeader().setVisible(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        pt_layout.addWidget(self.table)

        self.tabs.addTab(patient_tab, "Patient List")

        # Tab 2: Visit Completion Rate
        self.visit_completion_table = QTableWidget()
        self.visit_completion_table.setObjectName("dataTable")
        self.visit_completion_table.setColumnCount(5)
        self.visit_completion_table.setHorizontalHeaderLabels(
            ["Visit", "Completed", "Total", "Pending", "Completion %"]
        )
        self.visit_completion_table.horizontalHeader().setVisible(True)
        self.visit_completion_table.horizontalHeader().setMinimumHeight(40)
        self.visit_completion_table.horizontalHeader().setStretchLastSection(True)
        visit_tab = QWidget()
        v_layout = QVBoxLayout(visit_tab)
        v_layout.setSpacing(12)
        v_layout.addWidget(QLabel("Visit completion rates across all patients:"))
        v_layout.addWidget(self.visit_completion_table)
        self.tabs.addTab(visit_tab, "Visit Completion")

        # Tab 3: Motivator Performance
        self.motivator_table = QTableWidget()
        self.motivator_table.setObjectName("dataTable")
        self.motivator_table.setColumnCount(5)
        self.motivator_table.setHorizontalHeaderLabels(
            ["Motivator", "Total Patients", "Visit 1 Done", "Visit 2 Done", "Final Done"]
        )
        self.motivator_table.horizontalHeader().setVisible(True)
        self.motivator_table.horizontalHeader().setMinimumHeight(40)
        self.motivator_table.horizontalHeader().setStretchLastSection(True)
        motiv_tab = QWidget()
        m_layout = QVBoxLayout(motiv_tab)
        m_layout.setSpacing(12)
        m_layout.addWidget(QLabel("Patients and visit completion by motivator:"))
        m_layout.addWidget(self.motivator_table)
        self.tabs.addTab(motiv_tab, "Motivator Performance")

        # Tab 4: Monthly Summary
        self.monthly_table = QTableWidget()
        self.monthly_table.setObjectName("dataTable")
        self.monthly_table.setColumnCount(6)
        self.monthly_table.setHorizontalHeaderLabels(
            ["Month", "New Registrations", "Visits in Month", "Overdue", "EDD in Month", "Completed"]
        )
        self.monthly_table.horizontalHeader().setVisible(True)
        self.monthly_table.horizontalHeader().setMinimumHeight(40)
        self.monthly_table.horizontalHeader().setStretchLastSection(True)
        monthly_tab = QWidget()
        mo_layout = QVBoxLayout(monthly_tab)
        mo_layout.setSpacing(12)
        mo_layout.addWidget(QLabel("Monthly summary (last 12 months):"))
        mo_layout.addWidget(self.monthly_table)
        self.tabs.addTab(monthly_tab, "Monthly Summary")

        # Tab 5: Charts
        charts_tab = QWidget()
        charts_layout = QVBoxLayout(charts_tab)
        charts_layout.setSpacing(12)
        charts_scroll = QScrollArea()
        charts_scroll.setWidgetResizable(True)
        charts_scroll_content = QWidget()
        charts_scroll_layout = QVBoxLayout(charts_scroll_content)

        self.registrations_chart_view = QChartView()
        self.registrations_chart_view.setMinimumHeight(280)
        self.registrations_chart_view.setRenderHint(QPainter.Antialiasing)
        charts_scroll_layout.addWidget(QLabel("Registrations per month (last 12 months):"))
        charts_scroll_layout.addWidget(self.registrations_chart_view)

        self.motivator_chart_view = QChartView()
        self.motivator_chart_view.setMinimumHeight(280)
        self.motivator_chart_view.setRenderHint(QPainter.Antialiasing)
        charts_scroll_layout.addWidget(QLabel("Top motivators by patient count:"))
        charts_scroll_layout.addWidget(self.motivator_chart_view)

        charts_scroll.setWidget(charts_scroll_content)
        charts_layout.addWidget(charts_scroll)
        self.tabs.addTab(charts_tab, "Charts")

        layout.addWidget(self.tabs)

        self._load_data()
        self._apply_filters()
        self._load_visit_completion()
        self._load_motivator_performance()
        self._load_monthly_summary()
        self._load_charts()

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
                    village_name,
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
        from_date = None
        if self.from_date_edit.date().isValid():
            qd = self.from_date_edit.date()
            from_date = date(qd.year(), qd.month(), qd.day())

        to_date = None
        if self.to_date_edit.date().isValid():
            qd = self.to_date_edit.date()
            to_date = date(qd.year(), qd.month(), qd.day())

        month = self.month_combo.currentData()
        year = self.year_combo.currentData()
        motivator_f = self.motivator_filter.currentText().strip().lower()
        name_f = self.patient_name_filter.text().strip().lower()
        village_f = self.village_filter.text().strip().lower()

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
                village_name,
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
            if month and (not ent or ent.month != month):
                continue
            if year and (not ent or ent.year != year):
                continue
            if motivator_f and motivator_f != "any" and motivator_f not in str(motivator_name or "").lower():
                continue
            if name_f and name_f not in str(patient_name or "").lower():
                continue
            if village_f and village_f not in str(village_name or "").lower():
                continue

            filtered.append(row)

        self._populate_table(filtered)

    def _populate_table(self, rows: List[Tuple[Any, ...]]) -> None:
        # Column order: Serial, Entry Date, Patient Name, Patient ID, Village, Mobile, Motivator, LMP, EDD, Visits
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            (serial_number, patient_name, patient_id, mobile_number, motivator_name,
             village_name, lmp_date, edd_date, visit1, visit2, visit3, final_visit, entry_date, remarks) = row
            display_values = [
                serial_number, entry_date, patient_name, patient_id, village_name,
                mobile_number, motivator_name, lmp_date, edd_date, visit1, visit2, visit3, final_visit, remarks,
            ]
            for c, value in enumerate(display_values):
                # Date columns (1, 7-12): display as dd-mm-yyyy
                if c in (1, 7, 8, 9, 10, 11, 12):
                    d = parse_date_flex(value)
                    disp = format_for_display(d) if d else ("" if value is None else str(value))
                else:
                    disp = "" if value is None else str(value)
                item = QTableWidgetItem(disp)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()

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
            "village_name",
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
        self.visit_completion_table.resizeColumnsToContents()

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
            self.motivator_table.setItem(r, 0, QTableWidgetItem(str(motivator)))
            self.motivator_table.setItem(r, 1, QTableWidgetItem(str(total or 0)))
            self.motivator_table.setItem(r, 2, QTableWidgetItem(str(v1 or 0)))
            self.motivator_table.setItem(r, 3, QTableWidgetItem(str(v2 or 0)))
            self.motivator_table.setItem(r, 4, QTableWidgetItem(str(v4 or 0)))
        self.motivator_table.resizeColumnsToContents()

    def _load_monthly_summary(self) -> None:
        """Load monthly summary for last 12 months."""
        today = date.today()
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT entry_date, visit1, visit2, visit3, final_visit, edd_date
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

            for idx, (entry_str, v1, v2, v3, final, edd_str) in enumerate(all_rows):
                ent = parse_date_flex(entry_str)
                if ent and month_start <= ent <= month_end:
                    new_reg += 1

                edd = parse_date_flex(edd_str)
                if edd and month_start <= edd <= month_end:
                    edd_in_month += 1

                final_d = parse_date_flex(final)
                if final_d and month_start <= final_d <= month_end:
                    completed += 1

                for v_str in (v1, v2, v3, final):
                    v = parse_date_flex(v_str)
                    if v and month_start <= v <= month_end:
                        visits_in_month.add(idx)
                        if v < today:
                            overdue += 1
                        break

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
        self.monthly_table.resizeColumnsToContents()

    def _load_charts(self) -> None:
        """Load bar charts for registrations per month and motivator performance."""
        today = date.today()
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT entry_date FROM patients")
            entry_dates = [parse_date_flex(r[0]) for r in cur.fetchall()]
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
        finally:
            conn.close()

        # Registrations per month (last 12 months)
        reg_data = []
        categories = []
        for i in range(12):
            m = today.month - 1 - i
            y = today.year
            while m < 1:
                m += 12
                y -= 1
            month_start = date(y, m, 1)
            count = sum(1 for d in entry_dates if d and month_start <= d <= (date(y, 12, 31) if m == 12 else date(y, m + 1, 1) - timedelta(days=1)))
            reg_data.append(count)
            categories.append(month_start.strftime("%b %Y"))

        categories.reverse()
        reg_data.reverse()

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
