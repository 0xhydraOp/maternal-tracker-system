from __future__ import annotations

from datetime import date, timedelta
from typing import List, Tuple, Any

import pandas as pd
from PySide6.QtCore import QEvent, QObject, Qt, QDate, QSettings, QTimer
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QCompleter,
    QDateEdit,
    QDialog,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

from database.init_db import get_connection
from utils.date_utils import (
    DATE_FORMAT_DISPLAY,
    format_for_display,
    format_for_storage,
    parse_date as parse_date_flex,
    EMPTY_DATE_SENTINEL,
    EMPTY_DATE_SENTINEL_ALT,
)
from services.change_logger import log_change
from services.location_service import get_block_names, get_municipality_names
from services.motivator_service import get_all_motivator_names
from services.visit_scheduler import UPCOMING_DAYS, EDD_UPCOMING_DAYS, get_next_visit_due
from ui.patient_entry import PatientEntryDialog


class DateEditDelegate(QStyledItemDelegate):
    """Delegate for date columns - QDateEdit with calendar popup."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._date_format = DATE_FORMAT_DISPLAY

    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat(self._date_format)
        editor.setFrame(False)
        editor.setMinimumDate(QDate(EMPTY_DATE_SENTINEL.year, EMPTY_DATE_SENTINEL.month, EMPTY_DATE_SENTINEL.day))
        editor.setSpecialValueText("")
        return editor

    def setEditorData(self, editor, index):
        val = index.model().data(index, Qt.EditRole)
        if val:
            d = parse_date_flex(val)
            if d and d != EMPTY_DATE_SENTINEL and d != EMPTY_DATE_SENTINEL_ALT:
                editor.setDate(QDate(d.year, d.month, d.day))
                return
        editor.setDate(QDate(EMPTY_DATE_SENTINEL.year, EMPTY_DATE_SENTINEL.month, EMPTY_DATE_SENTINEL.day))

    def setModelData(self, editor, model, index):
        qd = editor.date()
        if not qd.isValid():
            model.setData(index, "", Qt.EditRole)
            return
        qd_py = date(qd.year(), qd.month(), qd.day())
        if qd_py == EMPTY_DATE_SENTINEL or qd_py == EMPTY_DATE_SENTINEL_ALT:
            model.setData(index, "", Qt.EditRole)
        else:
            model.setData(index, qd.toString(self._date_format), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class TableEnterKeyFilter(QObject):
    """Event filter: Enter key on table opens selected patient."""

    def __init__(self, table: QTableWidget, callback, parent=None):
        super().__init__(parent)
        self._table = table
        self._callback = callback

    def eventFilter(self, obj, event):
        if obj == self._table and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                row = self._table.currentRow()
                if row >= 0:
                    self._callback(row, 0)
                    return True
        return super().eventFilter(obj, event)


class PatientSearchDialog(QDialog):
    """
    Patient search and export dialog.
    Supports filtering by key fields and exporting the current result
    set to Excel using pandas + openpyxl.
    """

    def __init__(
        self,
        username: str,
        role: str = "STAFF",
        parent=None,
        filter_mode: str | None = None,
        status_callback=None,
    ):
        super().__init__(parent)
        self.username = username
        self.role = role.upper() if role else "STAFF"
        self._filter_mode = filter_mode  # "due_soon", "overdue", "edd_30", "today_entries", "all"
        self._status_callback = status_callback
        self.setWindowTitle("All Patient Records" if filter_mode == "all" else "Patient Search")

        self._all_rows: List[Tuple[Any, ...]] = []
        self._filter_debounce_timer = QTimer(self)
        self._filter_debounce_timer.setSingleShot(True)
        self._filter_debounce_timer.timeout.connect(self._apply_filters)

        self._build_ui()
        QShortcut(QKeySequence("Escape"), self, self.reject)
        self._restore_column_widths()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Date filter: All / Date Range / Month / Week / Year
        date_filter_bar = QHBoxLayout()
        date_filter_bar.setSpacing(8)
        date_filter_bar.addWidget(QLabel("Filter by entry date:"))
        self.date_filter_combo = QComboBox()
        self.date_filter_combo.setMinimumWidth(160)
        self.date_filter_combo.setMinimumHeight(28)
        self.date_filter_combo.addItems(["All", "Date Range", "This Month", "This Week", "This Year"])
        self.date_filter_combo.currentTextChanged.connect(self._on_date_filter_changed)
        date_filter_bar.addWidget(self.date_filter_combo)
        self.from_date_edit = QDateEdit()
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setDisplayFormat(DATE_FORMAT_DISPLAY)
        self.from_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.from_date_edit.setMinimumWidth(120)
        self.from_date_edit.setMinimumHeight(28)
        self.from_date_edit.setVisible(False)
        self.to_date_edit = QDateEdit()
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setDisplayFormat(DATE_FORMAT_DISPLAY)
        self.to_date_edit.setDate(QDate.currentDate())
        self.to_date_edit.setMinimumWidth(120)
        self.to_date_edit.setMinimumHeight(28)
        self.to_date_edit.setVisible(False)
        self.to_label = QLabel("to")
        self.to_label.setVisible(False)
        date_filter_bar.addWidget(self.from_date_edit)
        date_filter_bar.addWidget(self.to_label)
        date_filter_bar.addWidget(self.to_date_edit)
        date_filter_bar.addSpacing(24)
        date_filter_bar.addWidget(QLabel("Filter by Block/Municipality:"))
        self._block_names = list(get_block_names())
        self._municipality_names = list(get_municipality_names())
        self.location_type_combo = QComboBox()
        self.location_type_combo.setMinimumWidth(140)
        self.location_type_combo.setMinimumHeight(28)
        self.location_type_combo.addItems(["All", "Block", "Municipality"])
        self.location_type_combo.setCurrentIndex(0)
        self.location_type_combo.currentTextChanged.connect(self._on_location_type_changed)
        date_filter_bar.addWidget(self.location_type_combo)
        self.location_value_combo = QComboBox()
        self.location_value_combo.setMinimumWidth(160)
        self.location_value_combo.setMinimumHeight(28)
        self.location_value_combo.setVisible(False)
        self.location_value_combo.setEditable(True)
        self.location_value_combo.currentTextChanged.connect(self._schedule_filter)
        date_filter_bar.addWidget(self.location_value_combo)
        date_filter_bar.addStretch()
        layout.addLayout(date_filter_bar)

        # Compact horizontal filter bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)
        self.name_filter = QLineEdit()
        self.name_filter.setPlaceholderText("Patient Name")
        self.name_filter.setMinimumWidth(120)
        self.patient_id_filter = QLineEdit()
        self.patient_id_filter.setPlaceholderText("Patient ID")
        self.patient_id_filter.setMinimumWidth(100)
        self.mobile_filter = QLineEdit()
        self.mobile_filter.setPlaceholderText("Mobile")
        self.mobile_filter.setMinimumWidth(100)
        self.motivator_filter = QComboBox()
        self.motivator_filter.setEditable(True)
        self.motivator_filter.setMinimumWidth(120)
        self.motivator_filter.lineEdit().setPlaceholderText("Motivator")
        self.motivator_filter.addItem("Motivator", None)  # First option = no filter, always visible
        self.motivator_filter.addItems(get_all_motivator_names())
        self.motivator_filter.setCurrentIndex(0)  # Show "Motivator" (no filter) by default
        self.village_filter = QLineEdit()
        self.village_filter.setPlaceholderText("Village")
        self.village_filter.setMinimumWidth(100)

        filter_bar.addWidget(self.name_filter)
        filter_bar.addWidget(self.patient_id_filter)
        filter_bar.addWidget(self.mobile_filter)
        filter_bar.addWidget(self.motivator_filter)
        filter_bar.addWidget(self.village_filter)

        layout.addLayout(filter_bar)

        # Action buttons
        btn_row = QHBoxLayout()
        self.search_btn = QPushButton("Search")
        self.search_btn.setToolTip("Apply filters to search patients")
        self.search_btn.clicked.connect(self._apply_filters)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setToolTip("Reload data from database")
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear all filters")
        self.clear_btn.clicked.connect(self.clear_filters)
        self.export_btn = QPushButton("Export to Excel")
        self.export_btn.setToolTip("Export filtered results to Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_selected_btn = QPushButton("Export Selected")
        self.export_selected_btn.setToolTip("Export only selected rows to Excel")
        self.export_selected_btn.clicked.connect(self.export_selected_to_excel)

        btn_row.addWidget(self.search_btn)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.export_selected_btn)
        btn_row.addWidget(self.export_btn)

        layout.addLayout(btn_row)

        # Table with native header - always visible, styled via styles.py
        self._col_widths = [75, 130, 100, 100, 100, 110, 100, 70, 110, 100, 90, 90, 95, 95, 70, 120, 100]
        self.table = QTableWidget()
        self.table.setObjectName("patientSearchTable")
        self.table.setColumnCount(17)
        self.table.setHorizontalHeaderLabels([
            "Serial No", "Entry Date", "Patient Name", "Patient ID", "Block", "Municipality",
            "Village", "Ward", "Mobile", "Motivator", "LMP Date", "EDD Date", "1st Visit",
            "2nd Visit", "3rd Visit", "Final Visit", "Remarks",
        ])
        h_header = self.table.horizontalHeader()
        h_header.setVisible(True)
        h_header.setMinimumHeight(44)
        self.table.verticalHeader().setVisible(False)  # We have Serial No column; avoid dark row-number bar
        for col in range(17):
            self.table.setColumnWidth(col, self._col_widths[col])
        self.table.setEditTriggers(QTableWidget.DoubleClicked)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.setAlternatingRowColors(False)  # Avoid rows looking "selected" by default
        h_header.setStretchLastSection(True)
        for col in range(16):
            h_header.setSectionResizeMode(col, QHeaderView.Interactive)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setShowGrid(True)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.installEventFilter(TableEnterKeyFilter(self.table, self.open_selected_patient, self))
        date_delegate = DateEditDelegate(self.table)
        for col in (1, 10, 11, 12, 13, 14, 15):  # Entry Date, LMP, EDD, visits
            self.table.setItemDelegateForColumn(col, date_delegate)
        layout.addWidget(self.table, 1)

        # Result count and loading indicator
        self.status_bar = QHBoxLayout()
        self.result_count_label = QLabel("")
        self.result_count_label.setObjectName("resultCountLabel")
        self.loading_label = QLabel("")
        self.loading_label.setObjectName("loadingLabel")
        self.status_bar.addWidget(self.result_count_label)
        self.status_bar.addStretch()
        self.status_bar.addWidget(self.loading_label)
        layout.addLayout(self.status_bar)

        # Columns: 0=Serial, 1=EntryDate, 2=Name, 3=PatientID, 4=Block, 5=Municipality, 6=Village, 7=Ward, 8=Mobile, 9=Motivator, 10=LMP, 11=EDD, 12-15=Visits, 16=Remarks
        self._editable_cols = {11, 12, 13, 14, 15, 16}  # EDD, 1st/2nd/3rd/Final Visit, Remarks (Entry Date read-only)
        self._date_cols = {11, 12, 13, 14, 15}
        self._patient_id_col = 3
        self._suppress_item_changed = False

        # Load all patients initially
        self._load_all_patients()

        # Date filter - show/hide from-to, trigger filter on change (connected at line 123)
        self._on_date_filter_changed(self.date_filter_combo.currentText())
        self.from_date_edit.dateChanged.connect(self._apply_filters)
        self.to_date_edit.dateChanged.connect(self._apply_filters)

        # Live filtering (debounced)
        self.name_filter.textChanged.connect(self._schedule_filter)
        self.patient_id_filter.textChanged.connect(self._schedule_filter)
        self.mobile_filter.textChanged.connect(self._schedule_filter)
        self.motivator_filter.currentTextChanged.connect(self._schedule_filter)
        self.village_filter.textChanged.connect(self._schedule_filter)

    def _schedule_filter(self) -> None:
        """Debounce live filtering (250 ms) to avoid lag while typing."""
        self._filter_debounce_timer.stop()
        self._filter_debounce_timer.start(250)

    def _on_location_type_changed(self, text: str) -> None:
        """When Block or Municipality selected, show the value combo with searchable names."""
        self.location_value_combo.blockSignals(True)
        self.location_value_combo.clear()
        self.location_value_combo.setCompleter(None)
        self.location_value_combo.setVisible(False)
        if text == "Block":
            self.location_value_combo.setVisible(True)
            self.location_value_combo.lineEdit().setPlaceholderText("Type or select block...")
            self.location_value_combo.addItem("Select block...")
            self.location_value_combo.addItems(self._block_names)
            self.location_value_combo.setCurrentIndex(0)
            completer = QCompleter(self._block_names)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            completer.setModelSorting(QCompleter.UnsortedModel)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            self.location_value_combo.setCompleter(completer)
        elif text == "Municipality":
            self.location_value_combo.setVisible(True)
            self.location_value_combo.lineEdit().setPlaceholderText("Type or select municipality...")
            self.location_value_combo.addItem("Select municipality...")
            self.location_value_combo.addItems(self._municipality_names)
            self.location_value_combo.setCurrentIndex(0)
            completer = QCompleter(self._municipality_names)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            completer.setModelSorting(QCompleter.UnsortedModel)
            completer.setCompletionMode(QCompleter.PopupCompletion)
            self.location_value_combo.setCompleter(completer)
        self.location_value_combo.blockSignals(False)
        self._apply_filters()

    def _on_refresh(self) -> None:
        """Reload data from database."""
        self._load_all_patients()

    def _restore_column_widths(self) -> None:
        """Restore saved column widths from settings."""
        settings = QSettings("MaternalTracker", "PatientSearch")
        for col in range(17):
            w = settings.value(f"col_{col}", None, type=int)
            if w is not None and w > 0:
                self.table.setColumnWidth(col, w)

    def _save_column_widths(self) -> None:
        """Save column widths to settings."""
        settings = QSettings("MaternalTracker", "PatientSearch")
        for col in range(17):
            settings.setValue(f"col_{col}", self.table.columnWidth(col))

    def closeEvent(self, event) -> None:
        self._save_column_widths()
        super().closeEvent(event)

    def _on_date_filter_changed(self, text: str) -> None:
        """Show/hide from-to date pickers when Date Range is selected."""
        is_range = text == "Date Range"
        self.from_date_edit.setVisible(is_range)
        self.to_date_edit.setVisible(is_range)
        self.to_label.setVisible(is_range)
        self._apply_filters()

    def _load_all_patients(self) -> None:
        self.loading_label.setText("Loading...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        conn = None
        try:
            conn = get_connection()
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
                    remarks,
                    record_locked
                FROM patients
                ORDER BY entry_date ASC, serial_number ASC
                """
            )
            self._all_rows = cur.fetchall()
        finally:
            if conn is not None:
                conn.close()
            QApplication.restoreOverrideCursor()

        self._apply_filters()

    def _apply_filters(self) -> None:
        today = date.today()
        upcoming_limit = today + timedelta(days=UPCOMING_DAYS)
        edd_limit = today + timedelta(days=EDD_UPCOMING_DAYS)

        name_f = self.name_filter.text().strip().lower()
        pid_f = self.patient_id_filter.text().strip().lower()
        mobile_f = self.mobile_filter.text().strip().lower()
        motivator_f = self.motivator_filter.currentText().strip().lower()
        location_type = self.location_type_combo.currentText()
        location_val = self.location_value_combo.currentText().strip()
        block_f = ""
        municipality_f = ""
        if location_type == "Block" and location_val and location_val not in ("Select block...", ""):
            block_f = location_val.lower()
        elif location_type == "Municipality" and location_val and location_val not in ("Select municipality...", ""):
            municipality_f = location_val.lower()
        village_f = self.village_filter.text().strip().lower()

        def parse_date(s: Any) -> date | None:
            return parse_date_flex(s)

        # Date filter by entry_date
        date_filter_type = self.date_filter_combo.currentText()
        from_d = self.from_date_edit.date().toPython() if date_filter_type == "Date Range" else None
        to_d = self.to_date_edit.date().toPython() if date_filter_type == "Date Range" else None
        if date_filter_type == "This Week":
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            from_d, to_d = week_start, week_end
        elif date_filter_type == "This Month":
            from_d = today.replace(day=1)
            if today.month == 12:
                to_d = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                to_d = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        elif date_filter_type == "This Year":
            from_d = today.replace(month=1, day=1)
            to_d = today.replace(month=12, day=31)

        def matches(row: Tuple[Any, ...]) -> bool:
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
                entry_date,
                remarks,
                _record_locked,
            ) = row

            if name_f and name_f not in str(patient_name or "").lower():
                return False
            if pid_f and pid_f not in str(patient_id or "").lower():
                return False
            if mobile_f and mobile_f not in str(mobile_number or "").lower():
                return False
            if motivator_f and motivator_f.lower() != "motivator" and motivator_f not in str(motivator_name or "").lower():
                return False
            if block_f and str(block_name or "").lower() != block_f:
                return False
            if municipality_f and str(municipality_name or "").lower() != municipality_f:
                return False
            if village_f and village_f not in str(village_name or "").lower():
                return False

            # Entry date range filter
            if from_d is not None and to_d is not None:
                ent = parse_date(entry_date)
                if not ent or not (from_d <= ent <= to_d):
                    return False

            if self._filter_mode == "due_soon":
                v1, v2, v3, v4 = parse_date(visit1), parse_date(visit2), parse_date(visit3), parse_date(final_visit)
                next_due = get_next_visit_due(v1, v2, v3, v4, today, record_locked=bool(_record_locked))
                if not next_due or not (today <= next_due <= upcoming_limit):
                    return False
            elif self._filter_mode == "overdue":
                v1, v2, v3, v4 = parse_date(visit1), parse_date(visit2), parse_date(visit3), parse_date(final_visit)
                next_due = get_next_visit_due(v1, v2, v3, v4, today, record_locked=bool(_record_locked))
                if not next_due or next_due >= today:
                    return False
            elif self._filter_mode == "edd_30":
                edd = parse_date(edd_date)
                if not edd or not (today <= edd <= edd_limit):
                    return False
            elif self._filter_mode == "today_entries":
                ent = parse_date(entry_date)
                if not ent or ent != today:
                    return False

            return True

        self.loading_label.setText("Loading...")
        filtered = [row for row in self._all_rows if matches(row)]
        self._populate_table(filtered)

        self.loading_label.setText("")

    def _populate_table(self, rows: List[Tuple[Any, ...]]) -> None:
        self._suppress_item_changed = True

        # All rows - header is native table header
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
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
                _entry_date,
                remarks,
                record_locked,
            ) = row

            display_values = [
                serial_number,
                _entry_date,
                patient_name,
                patient_id,
                block_name,
                municipality_name,
                village_name,
                ward_number,
                mobile_number,
                motivator_name,
                lmp_date,
                edd_date,
                visit1,
                visit2,
                visit3,
                final_visit,
                remarks,
            ]

            for c, value in enumerate(display_values):
                # Date columns: display as dd-mm-yyyy
                if c in (1, 10, 11, 12, 13, 14, 15):
                    d = parse_date_flex(value)
                    disp = format_for_display(d) if d else ("" if value is None else str(value))
                else:
                    disp = "" if value is None else str(value)
                item = QTableWidgetItem(disp)
                if c == self._patient_id_col:  # Patient ID - store patient_id and record_locked
                    item.setData(Qt.UserRole, value)
                    item.setData(Qt.UserRole + 1, bool(record_locked))
                if c in self._editable_cols:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, c, item)

        # Avoid resizeColumnsToContents - it overrides user's saved column widths
        self._suppress_item_changed = False

        # Clear selection - nothing selected until user explicitly selects
        self.table.clearSelection()
        self.table.setCurrentCell(-1, -1)

        # Result count
        if len(rows) == 0:
            self.result_count_label.setText("No records match your filters.")
        else:
            self.result_count_label.setText(f"{len(rows)} record(s) found.")

    def clear_filters(self) -> None:
        self.name_filter.clear()
        self.patient_id_filter.clear()
        self.mobile_filter.clear()
        self.motivator_filter.setCurrentIndex(0)  # Reset to "Motivator" (no filter)
        self.location_type_combo.setCurrentIndex(0)  # Reset to "All"
        self.location_value_combo.setVisible(False)
        self.location_value_combo.clear()
        self.village_filter.clear()
        self.date_filter_combo.setCurrentIndex(0)  # Reset to "All"

        self._apply_filters()

    def _on_cell_double_clicked(self, row: int, column: int) -> None:
        if column in self._editable_cols:
            return  # Let delegate handle in-place edit
        self.open_selected_patient(row, column)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._suppress_item_changed:
            return
        col = item.column()
        if col not in self._editable_cols:
            return
        row = item.row()
        patient_id_item = self.table.item(row, self._patient_id_col)
        if not patient_id_item:
            return
        patient_id = patient_id_item.data(Qt.UserRole) or patient_id_item.text()
        if not patient_id:
            return
        # STAFF cannot edit locked records (Final Visit completed)
        record_locked = patient_id_item.data(Qt.UserRole + 1)
        if self.role == "STAFF" and record_locked:
            QMessageBox.warning(
                self,
                "Record Locked",
                "This record is locked (Final Visit completed). Only ADMIN users can edit locked records.",
            )
            self._suppress_item_changed = True
            self._apply_filters()
            self._suppress_item_changed = False
            return
        new_val = item.text().strip() or None
        if col in self._date_cols and new_val:
            parsed = parse_date_flex(new_val)
            if not parsed:
                QMessageBox.warning(
                    self, "Invalid Date",
                    "Please use DD-MM-YYYY format (e.g. 15-03-2026)."
                )
                self._suppress_item_changed = True
                self._apply_filters()
                self._suppress_item_changed = False
                return
            new_val = format_for_storage(parsed)
        field_map = {11: "edd_date", 12: "visit1", 13: "visit2", 14: "visit3", 15: "final_visit", 16: "remarks"}
        field = field_map[col]
        conn = get_connection()
        try:
            cur = conn.cursor()
            # Validate visit order for date fields
            if field in ("visit1", "visit2", "visit3", "final_visit") and new_val:
                cur.execute(
                    "SELECT entry_date, visit1, visit2, visit3, final_visit FROM patients WHERE patient_id = ?",
                    (patient_id,),
                )
                row_data = cur.fetchone()
                if row_data:
                    entry_str, v1_str, v2_str, v3_str, final_str = row_data
                    entry_d = parse_date_flex(entry_str)
                    v1_d = parse_date_flex(v1_str)
                    v2_d = parse_date_flex(v2_str)
                    v3_d = parse_date_flex(v3_str)
                    final_d = parse_date_flex(final_str)
                    new_d = parse_date_flex(new_val) if isinstance(new_val, str) else None
                    if new_d:
                        if field == "visit1":
                            # 1st Visit must equal Entry Date - update both together
                            new_val = format_for_storage(new_d)
                            cur.execute(
                                "UPDATE patients SET visit1 = ?, entry_date = ? WHERE patient_id = ?",
                                (new_val, new_val, patient_id),
                            )
                            log_change(
                                patient_id=patient_id,
                                field_name="visit1",
                                old_value=v1_str,
                                new_value=new_val,
                                changed_by=self.username,
                            )
                            log_change(
                                patient_id=patient_id,
                                field_name="entry_date",
                                old_value=entry_str,
                                new_value=new_val,
                                changed_by=self.username,
                            )
                            conn.commit()
                            self._suppress_item_changed = True
                            self._apply_filters()
                            self._suppress_item_changed = False
                            return
                        elif field == "visit2":
                            if v1_d and new_d < v1_d:
                                QMessageBox.warning(
                                    self, "Validation",
                                    "2nd Visit cannot be before 1st Visit.",
                                )
                                self._suppress_item_changed = True
                                self._apply_filters()
                                self._suppress_item_changed = False
                                return
                        elif field == "visit3":
                            if v2_d and new_d < v2_d:
                                QMessageBox.warning(
                                    self, "Validation",
                                    "3rd Visit cannot be before 2nd Visit.",
                                )
                                self._suppress_item_changed = True
                                self._apply_filters()
                                self._suppress_item_changed = False
                                return
                        elif field == "final_visit":
                            prev = v3_d or v2_d or v1_d
                            if prev and new_d < prev:
                                QMessageBox.warning(
                                    self, "Validation",
                                    "Final Visit cannot be before the previous visit.",
                                )
                                self._suppress_item_changed = True
                                self._apply_filters()
                                self._suppress_item_changed = False
                                return

            cur.execute(
                f"SELECT {field} FROM patients WHERE patient_id = ?",
                (patient_id,),
            )
            old_val = cur.fetchone()
            old_val = old_val[0] if old_val else None
            cur.execute(
                f"UPDATE patients SET {field} = ? WHERE patient_id = ?",
                (new_val, patient_id),
            )
            if field == "final_visit" and new_val:
                cur.execute(
                    "UPDATE patients SET record_locked = 1 WHERE patient_id = ?",
                    (patient_id,),
                )
            conn.commit()
            log_change(
                patient_id=patient_id,
                field_name=field,
                old_value=old_val,
                new_value=new_val,
                changed_by=self.username,
            )
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Save Failed", str(e))
        finally:
            conn.close()

    def open_selected_patient(self, row: int, column: int) -> None:
        item = self.table.item(row, self._patient_id_col)
        if not item:
            return
        patient_id = item.data(Qt.UserRole) or item.text()
        if not patient_id:
            return

        dialog = PatientEntryDialog(username=self.username, role=self.role, parent=self)
        dialog.patient_id_edit.setText(str(patient_id))
        dialog.load_patient()
        if dialog.exec() == QDialog.Accepted:
            # Reload data and re-apply filters to refresh the table
            self._load_all_patients()

    def export_to_excel(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel File",
            "patients.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not path:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            # Build a DataFrame from the currently displayed table rows
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

            df = pd.DataFrame(data)
            df.to_excel(path, index=False, engine="openpyxl")
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not export to Excel:\n{exc}",
            )
            return
        finally:
            QApplication.restoreOverrideCursor()

        if self._status_callback:
            self._status_callback(f"Exported {len(df)} record(s) to Excel.")
        QMessageBox.information(
            self,
            "Export Complete",
            f"Exported {len(df)} record(s) to:\n{path}",
        )

    def export_selected_to_excel(self) -> None:
        """Export only selected rows to Excel."""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select one or more rows to export.",
            )
            return
        rows = sorted(set(item.row() for item in selected))
        if not rows:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select one or more rows to export.",
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Selected to Excel",
            "patients_selected.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not path:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
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
            for row in rows:
                row_data = {}
                for col, key in enumerate(headers):
                    item = self.table.item(row, col)
                    row_data[key] = item.text() if item is not None else ""
                data.append(row_data)

            df = pd.DataFrame(data)
            df.to_excel(path, index=False, engine="openpyxl")
            if self._status_callback:
                self._status_callback(f"Exported {len(df)} selected record(s) to Excel.")
            QMessageBox.information(
                self,
                "Export Complete",
                f"Exported {len(df)} selected record(s) to:\n{path}",
            )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not export to Excel:\n{exc}",
            )
        finally:
            QApplication.restoreOverrideCursor()

