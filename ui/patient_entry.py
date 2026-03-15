from __future__ import annotations

import sqlite3
from datetime import date, timedelta, datetime
from typing import Optional, List

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QDateEdit,
    QFrame,
    QWidget,
)

from database.init_db import get_connection
from utils.date_utils import DATE_FORMAT_DISPLAY, parse_date as parse_date_flex
from services.change_logger import log_change
from services.motivator_service import add_custom_motivator, get_all_motivator_names
from services.village_service import get_all_village_names


MOTIVATOR_OTHERS = "Others"

# Sentinel for "no date" in optional visit fields (3rd, Final) - displays as empty
EMPTY_DATE_SENTINEL = QDate(1900, 1, 1)

MOTIVATOR_NAMES: List[str] = [
    "SAJEM B.C LAB",
    "LALTU S.N.H",
    "HAPI ROSE",
    "YEADUL DA",
    "SAHIN RMP",
    "RAJJAK MAMA",
    "PANNA DA",
    "CH ASIM",
    "PRITAM S.LAB",
    "CH",
    "CH SA",
    "RUHUL AMIN",
    "SAJIRUL",
    "JAHANGIR S.N.H",
    "ASIR DA",
    "SADDAM GOLI",
    "CH A",
    "SAJEM DA B.C",
    "MONI DA",
    "DALIM MAMA",
    "IKBAL P MEDICIN",
    "LOTIB",
    "ROHIM S T",
    "JARJISH",
    "SAMIM RMP",
    "AWAL TULIP",
    "RAJU DA",
    "SOURAV M R",
    "SIRATUL HAQUE",
    "NOBINUR DA",
    "ANAWAR RMP B.C",
    "SAHABODDIN",
    "NURAMIN TEE",
    "PAN CACHI",
    "RAFI SR",
    "RAHUL RM",
    "ALI DA",
    "MAMOTA DI TULIP",
    "JAHANGIR DA MV",
    "SUMON Z.H",
    "ASIT DA MONI",
    "JUMA DA",
    "ALAM DA",
    "NASIM DA",
    "BACHU S LAB",
    "RUHUL CACA",
    "SEBA",
    "BAPI DIPALI",
    "JOSNA",
    "KABIRUK RMP",
    "HASIBUL DA",
    "JAHIR RMP",
    "RAJA ROSE",
    "SUBOL DA",
    "JHUNTU DA",
    "DSS DA BC LAB",
    "HASIBUL DA L L.",
    "HASIBUL DA L.L",
    "ABBAS DA",
    "TOHIDUL PK",
    "SONKUDA",
    "NAYON DA",
    "KUTUBUDDIN RMP",
    "ASHIT DA",
    "SAJIDA MASI S.N.H/",
    "LUTFUR",
    "JAKIR DA J ALI",
    "JUNU DA",
    "MOMI DA",
    "MONIRUL 3STAR",
    "RANI N.H",
    "FORIDA ASHA",
    "CHAINA D",
    "ELIYAS IDIYAL",
    "SOVA DI",
    "SADHIN",
    "LALTU DA",
    "ASIMDA LIFE CARE",
    "KHOKON BC",
    "SIFA MEDICIN",
    "NASIM DA L.C",
    "RAHUL RL",
    "RAJU DA U B",
    "MERINA ASHA",
    "SELIM AYESHA",
    "INJA L.C",
    "RAKI IDIYAL STAF",
    "KHADIJA",
    "KABIRUL RMP",
    "NABINUR DA",
    "RAMJAN DA",
    "SITARUL HAQUE ME.",
    "ABU ROSE",
    "MUNNA MAMU",
    "TUJAM D",
    "DAS DA B.C",
    "KALU FAL",
    "RAJ MICRO",
    "MANNAP RMP",
    "SAHIN ROSE",
    "SAHIL N S N H",
    "JOSNA D",
    "NAJIBUL RMP",
    "NASIM NASRAT",
    "FARUK C.DAS",
    "RAHUL R M",
    "RAJA RMP",
    "JHUMA DA NASROT",
    "BABY LALGOLA",
    "HASIBUL L.L",
    "BITTU DA DRIVAR",
    "TOUFIK",
    "SAHIL",
    "DELERA KHALA",
    "TINKU DA S .N.H",
    "CH.T",
    "MITU DA LIFE C.",
    "UDAY DA",
    "RAHUL LAB",
    "JHONTU DA",
    "CH T.",
    "LUFUL MAMA",
    "FORID DA",
    "JOSNA DI",
    "NAYON 3STAR",
    "ROBI",
    "REKHA CACHI",
    "RAHUL R.M",
    "MAFIKUL B.C",
    "MARA DA",
    "MONIRUL RMP",
    "AMINUL DA",
    "TOHIDUL L.L",
    "HABIBUR RMP",
    "JABBAR DA S SIR",
    "JADOB",
    "NARGISH 3 STAR",
    "SILTU HASPITAL",
    "SULTAN",
    "MAJARUL",
    "GOLDEN LAB",
    "CH SE",
    "BIKRAM R.L",
    "FITU ANDALUS",
    "JHUNTU DA K.C",
    "RAHUL SAHARA M.",
    "TAHAMINA SNH",
    "RAJOB",
    "LUTFUR MAMA",
    "HILAL",
    "FARUK C .DAS",
    "JAHANGIR M.V",
    "IDIYAL STAF",
    "ENAMUL DA",
    "GAFFAR ENT",
    "RAMES KAKA",
    "MASTAR MEDICAL",
    "JAKIR DA J.ALI",
    "FARUK.C. DAS",
    "AYESHA MEDICIN",
    "HASIBUL",
    "SELINA ASHA",
    "RUPA ASHA MASI",
    "JHUMA DA",
    "IKBAL MOLLA",
    "REJINA DI",
    "ABU HASPITAL",
    "TINKU DA",
    "MYNUL CACA",
    "BAPI DA B.C",
    "TAHAMINA S.N.H.",
    "ROHIM",
    "ALAMIN Z.H.",
    "APTAB DA",
    "MIRKASIM CACA",
    "ANARUL ROSE",
    "RAKIB SR",
    "S LAB",
    "ANIKUL ROSE",
    "MUNNA PARAG STAF",
    "SAMRAT",
    "ISMETARA L.G",
    "ABUHENA RMP",
    "ILIYAS IDIYAL",
    "JAYEB ALI",
    "JHONTU DA K.C",
    "ALIMA TULIP",
    "BADOR RMP",
    "SAIJODDIN",
    "RAKI AKTARUL SIR",
    "SAJJAD L.L",
    "VANU MASI",
    "YEAKUB RMP AMI",
    "RAJ OT",
    "RIMA DI",
    "JHURI BALA",
    "LIFE LINE",
    "HASAN B.C",
    "HIDAY AMI",
    "NUPUR S.N.H",
    "TOHIDUL P.K",
    "HASIBUL DA LL",
    "ALOM DA RENBWO",
    "REKHA CACHI D",
    "HABIB P.K",
    "RAKIB BANDHAN",
    "SONKU DA",
    "LALON BOSUNDARA",
    "SEULI ASHA",
    "SILON NEW S.N.H",
    "TAJEL",
    "FARUK GOLI",
    "YOUSUF DA",
    "DIPAK DA N.S N.H",
    "SELINA",
    "CHOTON INDIA",
    "SOHEL LALTU",
    "AKKAS DA",
    "SOHEL",
    "SIMA DI",
    "SABANA TULIP",
    "MOHIDUL RMP",
    "SABIRUL DA H.P",
    "ABUHENA L.C",
    "HAPIJUL",
    "JABBAR DA S.N.SIR",
    "ALOM BANDHON",
    "REKHA MASI N.H",
    "ARFA MASI",
    "DIPAK S.LAB",
    "DR",
    "LALBANU",
    "SAHIN DA ROSE",
    "BABI D",
    "TAJEL DA",
    "PAPPU N.N",
    "NIRMALA MASI",
    "MAINUL R.M",
    "DIPAK DA",
    "HAPI DA",
    "MANOWAR",
    "SAFI",
    "ROKIYA DI",
    "ROKI LALGOLA",
    "JABBAR DA",
    "BAPI DA DIPALI",
    "RUBEL RMP",
    "BABOR RMP",
    "JISAN",
    "MITHU L.C",
    "MOUSUMI BNH",
    "RAJU APPOLO",
    "SURAT DA",
    "MOMIN RMP",
    "BONKIM RMP",
    "ABBASUDDIN",
    "NASRAT MEDICIN",
    "NUR AMIN TEE",
    "TOHIDUL",
    "NURMAHAL MASI",
    "RIYAZ L.L",
    "AKKHAY DA",
    "BACHU N S NH",
    "SAHINA D",
    "RAKI RMP",
    "HAMIM S.RUY",
    "BABOR NOSIPUR",
    "BIJOLA MASI",
    "SILTU WIFE",
    "PALAS DR",
    "RANI",
    "RAJ LAB",
    "JHARNA DI",
    "ABBAS DA J.S",
    "NASIM DA NASNAL",
    "LAILA MASI",
    "HASIBUL RMP",
    "SAMRAT 3 STAR",
    "3 STAR",
    "UJJAL DA",
    "CHINA",
    "REJINA D",
    "MOUSUMI B.N.H",
    "ALAMIN Z.H",
    "LALON DA BNH",
    "KAJI R.M",
    "TINKU DA S.N.H",
    "JIYAUR RMP",
    "INJA LC",
    "SUKCHAND CACA",
    "MILON J.ALAM",
    "SUMON RMP",
    "LUTFUR DA",
    "PALAS RMP",
    "RAHUL R L",
    "SIRATUL H.Q",
    "JAKIR DA",
    "SUROJ N.K SAW",
    "FITU",
    "YOUSUF DA B.C",
    "SOHEL M.H",
    "HAMIM S.ROY",
    "HELT POINT",
    "PANNN DA",
    "SAMOR RMP",
    "ALO FARMECI",
    "REKHA MASI S.N.H",
    "LALBAG LAB",
    "SAMRAT 3STAR",
    "HRIDAY RMP",
    "HASAN RMP AMI",
    "PRITAM DA",
    "ASLAM DA",
    "RINKU DA",
    "BAPI DA",
    "MAKSED CACA",
    "SOMNATH S. LAB",
    "NASRAT",
    "JAKIR J ALI",
    "MUJAHIR RMP",
    "B.N.H",
    "SELIM L.C",
    "KHADIJA CH",
    "BELLAL DA",
    "ANARUL DA",
    "AINUL",
    "SAFI DA",
    "ALAMGIR",
    "SELIM RMP",
    "ALOM DA",
    "SURO",
    "RAKI LAB",
    "MASUM",
    "ATAUR DA HASPITAL",
    "KHOKON B.C",
    "ABUHENA",
    "IBRAHIM",
    "TUJAM",
    "KHOKON B. C",
    "MINTU DA",
    "NUR",
    "RAHUL R.L",
    "SARVANU MICRO",
    "MYNUL ROSE",
    "BACHHU N.H",
    "SIMA DI ASHA",
    "JAHANGIR DA M.V",
    "ASIM IDEL",
    "MASI",
    "FIROJ MARA",
    "RAKI AKT",
    "PAPPU DA ANDALUS",
    "PROSANTO DA",
    "RAJESH DA BNH",
    "ASHOK DA TEE",
    "GABBU HASPITAL",
    "SYFUL",
    "SEBA MEDICIN",
    "NIJAM MAMA",
    "HYDAR RMP",
    "SELINA ROSE LAB",
    "JHORNA DI",
    "MAMA BNH",
    "PROBIR DA",
    "RAJA DIPALI",
    "YEADUL",
    "JAKIR J.ALI",
]


class PatientEntryDialog(QDialog):
    """
    Patient entry and edit dialog.
    Supports automatic EDD calculation.
    1st Visit = Entry Date (read-only); 2nd, 3rd, Final Visit are manual.
    Writes change_logs when visit dates are modified.
    """

    def __init__(self, username: str, role: str = "STAFF", parent=None):
        super().__init__(parent)
        self.username = username
        self.role = role.upper() if role else "STAFF"
        self.setWindowTitle("Patient Entry")
        self.resize(980, 600)
        self._build_ui()
        self._setup_shortcuts()

        self._loaded_patient_exists = False
        self._record_locked = False
        self._dirty = False

    def _mark_dirty(self) -> None:
        """Mark form as having unsaved changes."""
        self._dirty = True

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_patient)
        QShortcut(QKeySequence("Escape"), self, self._maybe_reject)

    def _maybe_reject(self) -> None:
        """Reject (close) after confirming if there are unsaved changes."""
        if self._confirm_discard():
            self.reject()

    def _confirm_discard(self) -> bool:
        """Return True if user confirms discard (or no unsaved changes)."""
        if not self._dirty:
            return True
        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save before closing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if reply == QMessageBox.Save:
            self.save_patient()
            return not self._dirty  # True if save succeeded
        if reply == QMessageBox.Discard:
            return True
        return False

    def closeEvent(self, event) -> None:
        """Intercept close (X button) to confirm unsaved changes."""
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()

    def reject(self) -> None:
        """Override reject to confirm before closing with unsaved changes."""
        if self._confirm_discard():
            super().reject()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        main_split = QHBoxLayout()
        main_split.setSpacing(16)

        self.name_edit = QLineEdit()
        self.patient_id_edit = QLineEdit()
        self.patient_id_edit.setReadOnly(True)
        self.mobile_edit = QLineEdit()
        self.village_combo = QComboBox()
        self.village_combo.setEditable(True)
        self.village_combo.addItems(get_all_village_names())

        today_qdate = QDate.currentDate()

        def make_date_edit():
            e = QDateEdit()
            e.setCalendarPopup(True)
            e.setDisplayFormat(DATE_FORMAT_DISPLAY)
            return e

        self.lmp_edit = make_date_edit()
        self.lmp_edit.setDate(today_qdate)

        self.edd_edit = make_date_edit()
        self.edd_edit.setDate(today_qdate)

        self.motivator_combo = QComboBox()
        self.motivator_combo.setEditable(False)
        self.motivator_combo.addItems(get_all_motivator_names())
        self.motivator_combo.addItem(MOTIVATOR_OTHERS)
        self.motivator_combo.currentTextChanged.connect(self._on_motivator_changed)

        self.motivator_other_edit = QLineEdit()
        self.motivator_other_edit.setPlaceholderText("Please specify")

        self.visit1_edit = make_date_edit()
        self.visit1_edit.setReadOnly(True)  # 1st Visit = Entry Date (always)
        self.visit2_edit = make_date_edit()
        self.visit2_edit.setMinimumDate(EMPTY_DATE_SENTINEL)
        self.visit2_edit.setSpecialValueText("")
        self.visit3_edit = make_date_edit()
        self.visit3_edit.setMinimumDate(EMPTY_DATE_SENTINEL)
        self.visit3_edit.setSpecialValueText("")
        self.final_visit_edit = make_date_edit()
        self.final_visit_edit.setMinimumDate(EMPTY_DATE_SENTINEL)
        self.final_visit_edit.setSpecialValueText("")
        self.remarks_edit = QLineEdit()
        self.remarks_edit.setPlaceholderText("Optional notes")
        self.entry_date_edit = make_date_edit()
        self.entry_date_edit.setReadOnly(True)  # Entry Date not editable anywhere
        self.entry_date_edit.setDate(today_qdate)

        # Ensure fields have a good clickable height
        self._editable_widgets = [
            self.name_edit,
            self.mobile_edit,
            self.village_combo,
            self.motivator_combo,
            self.motivator_other_edit,
            self.lmp_edit,
            self.edd_edit,
            self.visit1_edit,
            self.visit2_edit,
            self.visit3_edit,
            self.final_visit_edit,
            self.remarks_edit,
            self.entry_date_edit,
        ]
        for widget in [self.patient_id_edit] + self._editable_widgets:
            widget.setMinimumHeight(32)

        def make_label(text: str, required: bool = False) -> QLabel:
            label = QLabel(text + (" *" if required else ""))
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setObjectName("requiredLabel" if required else "formLabel")
            return label

        def make_section(title: str) -> tuple[QFrame, QVBoxLayout]:
            frame = QFrame()
            vbox = QVBoxLayout(frame)
            vbox.setSpacing(10)
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            title_label.setObjectName("sectionTitle")
            vbox.addWidget(title_label)
            return frame, vbox

        # Left column: Patient Information
        info_frame, info_layout = make_section("Patient Information")
        info_form = QFormLayout()
        info_form.setHorizontalSpacing(20)
        info_form.setVerticalSpacing(10)
        info_form.addRow(make_label("Patient Name:", required=True), self.name_edit)
        info_form.addRow(make_label("Patient ID (auto):"), self.patient_id_edit)
        info_form.addRow(make_label("Mobile Number:", required=True), self.mobile_edit)
        info_form.addRow(make_label("Village Name:", required=True), self.village_combo)
        motivator_container = QFrame()
        motivator_vbox = QVBoxLayout(motivator_container)
        motivator_vbox.setContentsMargins(0, 0, 0, 0)
        motivator_vbox.addWidget(self.motivator_combo)
        self.motivator_specify_widget = QWidget()
        specify_layout = QHBoxLayout(self.motivator_specify_widget)
        specify_layout.setContentsMargins(0, 6, 0, 0)
        specify_layout.addWidget(QLabel("Please specify:"))
        specify_layout.addWidget(self.motivator_other_edit, 1)
        motivator_vbox.addWidget(self.motivator_specify_widget)
        self.motivator_specify_widget.setVisible(False)
        info_form.addRow(make_label("Motivator Name:", required=True), motivator_container)
        info_form.addRow(make_label("Entry Date:"), self.entry_date_edit)
        info_layout.addLayout(info_form)

        # Right column: Pregnancy + Visit
        right_column = QVBoxLayout()
        right_column.setSpacing(12)

        preg_frame, preg_layout = make_section("Pregnancy Dates")
        preg_form = QFormLayout()
        preg_form.setHorizontalSpacing(20)
        preg_form.setVerticalSpacing(10)
        preg_form.addRow(make_label("LMP Date:", required=True), self.lmp_edit)
        preg_form.addRow(make_label("EDD Date:"), self.edd_edit)
        preg_layout.addLayout(preg_form)

        visit_frame, visit_layout = make_section("Visit Tracking")
        visit_form = QFormLayout()
        visit_form.setHorizontalSpacing(20)
        visit_form.setVerticalSpacing(10)
        visit_form.addRow(make_label("1st Visit:"), self.visit1_edit)
        visit_form.addRow(make_label("2nd Visit:"), self.visit2_edit)
        visit_form.addRow(make_label("3rd Visit:"), self.visit3_edit)
        visit_form.addRow(make_label("Final Visit:"), self.final_visit_edit)
        visit_form.addRow(make_label("Remarks:"), self.remarks_edit)
        visit_layout.addLayout(visit_form)

        main_split.addWidget(info_frame, 1)
        right_container = QVBoxLayout()
        right_container.addWidget(preg_frame)
        right_container.addWidget(visit_frame)
        main_split.addLayout(right_container, 1)

        layout.addLayout(main_split)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        self.button_box.accepted.connect(self.save_patient)
        self.button_box.rejected.connect(self.reject)

        self.unlock_check = QCheckBox("Unlock record (ADMIN only)")
        self.unlock_check.setVisible(False)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.unlock_check)
        btn_layout.addStretch()
        btn_layout.addWidget(self.button_box)

        layout.addLayout(btn_layout)

        # Entry Date = today; 1st Visit = same as Entry Date for new records
        self.entry_date_edit.setDate(QDate.currentDate())
        self.visit1_edit.setDate(self.entry_date_edit.date())

        # Keep 2nd, 3rd, Final Visit blank (entered later)
        self.visit2_edit.setDate(EMPTY_DATE_SENTINEL)  # Displays empty until user selects
        self.visit3_edit.setDate(EMPTY_DATE_SENTINEL)  # Displays empty until user selects
        self.final_visit_edit.setDate(EMPTY_DATE_SENTINEL)  # Displays empty until user selects

        # When Entry Date changes, update 1st Visit to match
        self.entry_date_edit.dateChanged.connect(self._update_first_visit)

        # Wire up automatic EDD calculation from LMP only
        self.lmp_edit.dateChanged.connect(self._update_edd_from_lmp)
        self._update_edd_from_lmp()

        # Auto-generate Patient ID for new registrations
        if not self.patient_id_edit.text().strip():
            self._generate_patient_id()

        # Track unsaved changes for close confirmation
        self.name_edit.textChanged.connect(self._mark_dirty)
        self.mobile_edit.textChanged.connect(self._mark_dirty)
        self.village_combo.currentTextChanged.connect(self._mark_dirty)
        self.motivator_combo.currentTextChanged.connect(self._mark_dirty)
        self.motivator_other_edit.textChanged.connect(self._mark_dirty)
        self.lmp_edit.dateChanged.connect(self._mark_dirty)
        self.edd_edit.dateChanged.connect(self._mark_dirty)
        self.visit1_edit.dateChanged.connect(self._mark_dirty)
        self.visit2_edit.dateChanged.connect(self._mark_dirty)
        self.visit3_edit.dateChanged.connect(self._mark_dirty)
        self.final_visit_edit.dateChanged.connect(self._mark_dirty)
        self.remarks_edit.textChanged.connect(self._mark_dirty)

        self._dirty = False  # Reset after initial setup

    def _generate_patient_id(self) -> None:
        """
        Generate a Patient ID of the form PT<seq>-<MM>-<YYYY>,
        where seq resets every month based on existing records.
        """
        today = datetime.today()
        month = today.strftime("%m")
        year = today.strftime("%Y")

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*) FROM patients
                WHERE strftime('%m', entry_date) = ? AND strftime('%Y', entry_date) = ?
                """,
                (month, year),
            )
            count = cur.fetchone()[0] or 0
        finally:
            conn.close()

        next_num = count + 1
        patient_id = f"PT{next_num:02d}-{month}-{year}"
        self.patient_id_edit.setText(patient_id)

    def _qdate_to_date(self, qd: QDate) -> Optional[date]:
        if not qd.isValid():
            return None
        return date(qd.year(), qd.month(), qd.day())

    def _date_to_qdate(self, d: Optional[date]) -> QDate:
        if d is None:
            return QDate()  # invalid
        return QDate(d.year, d.month, d.day)

    def _update_edd_from_lmp(self) -> None:
        lmp = self._qdate_to_date(self.lmp_edit.date())
        if not lmp:
            return
        edd = lmp + timedelta(days=280)
        self.edd_edit.setDate(self._date_to_qdate(edd))

    def _refresh_motivator_combo(self, select_name: Optional[str] = None) -> None:
        """Reload motivator combo with base + custom names (after adding new via Others)."""
        current = select_name or self.motivator_combo.currentText()
        self.motivator_combo.clear()
        self.motivator_combo.addItems(get_all_motivator_names())
        self.motivator_combo.addItem(MOTIVATOR_OTHERS)
        idx = self.motivator_combo.findText(current)
        if idx >= 0:
            self.motivator_combo.setCurrentIndex(idx)

    def _on_motivator_changed(self, text: str) -> None:
        """Show 'Please specify' box when 'Others' is selected."""
        is_others = text == MOTIVATOR_OTHERS
        self.motivator_specify_widget.setVisible(is_others)
        if is_others:
            if not getattr(self, "_record_locked", False):
                self.motivator_other_edit.setReadOnly(False)
                self.motivator_other_edit.setEnabled(True)
            self.motivator_other_edit.setFocus()
        else:
            self.motivator_other_edit.clear()

    def _set_read_only(self, locked: bool) -> None:
        """Disable editing when record is locked and user is STAFF."""
        for w in self._editable_widgets:
            if hasattr(w, "setReadOnly"):
                w.setReadOnly(locked)
            w.setEnabled(not locked)
        self.visit1_edit.setReadOnly(True)  # 1st Visit always = Entry Date (never editable)
        # 2nd, 3rd, Final Visit must stay editable when record is not locked
        if not locked:
            self.visit2_edit.setReadOnly(False)
            self.visit3_edit.setReadOnly(False)
            self.final_visit_edit.setReadOnly(False)
        self.button_box.button(QDialogButtonBox.Save).setEnabled(not locked)
        if locked:
            self.unlock_check.setVisible(False)

    def _set_locked_for_admin(self, locked: bool) -> None:
        """Show unlock option for ADMIN when record is locked."""
        self.unlock_check.setVisible(locked and self.role == "ADMIN")
        self.unlock_check.setChecked(False)

    def _update_first_visit(self, qdate: QDate) -> None:
        """When Entry Date changes, set 1st Visit to the same date."""
        self.visit1_edit.setDate(qdate)

    def load_patient(self) -> None:
        patient_id = self.patient_id_edit.text().strip()
        if not patient_id:
            return

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    patient_name,
                    patient_id,
                    mobile_number,
                    village_name,
                    lmp_date,
                    edd_date,
                    motivator_name,
                    visit1,
                    visit2,
                    visit3,
                    final_visit,
                    entry_date,
                    record_locked,
                    remarks
                FROM patients
                WHERE patient_id = ?
                """,
                (patient_id,),
            )
            row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return

        (
            patient_name,
            _pid,
            mobile_number,
            village_name,
            lmp_date_str,
            edd_date_str,
            motivator_name,
            visit1_str,
            visit2_str,
            visit3_str,
            final_visit_str,
            entry_date_str,
            record_locked,
            remarks_str,
        ) = row

        self._record_locked = bool(record_locked)
        if self._record_locked and self.role == "STAFF":
            self._set_read_only(True)
            QMessageBox.information(
                self,
                "Record Locked",
                "This record is locked (Final Visit completed). Only ADMIN users can edit locked records.",
            )
        elif self._record_locked and self.role == "ADMIN":
            self._set_locked_for_admin(True)
        else:
            self._set_read_only(False)
            self.unlock_check.setVisible(False)

        self.name_edit.setText(patient_name or "")
        self.mobile_edit.setText(mobile_number or "")
        village = village_name or ""
        idx = self.village_combo.findText(village)
        if idx >= 0:
            self.village_combo.setCurrentIndex(idx)
        else:
            self.village_combo.setCurrentText(village)
        if motivator_name and motivator_name in get_all_motivator_names():
            self.motivator_combo.setCurrentText(motivator_name)
            self.motivator_other_edit.clear()
            self.motivator_specify_widget.setVisible(False)
        elif motivator_name:
            self.motivator_combo.setCurrentText(MOTIVATOR_OTHERS)
            self.motivator_other_edit.setText(motivator_name)
            self.motivator_specify_widget.setVisible(True)
        else:
            self.motivator_combo.setCurrentIndex(0)
            self.motivator_other_edit.clear()
            self.motivator_specify_widget.setVisible(False)

        for editor, value in (
            (self.lmp_edit, lmp_date_str),
            (self.edd_edit, edd_date_str),
            (self.entry_date_edit, entry_date_str),
            (self.visit1_edit, entry_date_str),  # 1st Visit = Entry Date
            (self.visit2_edit, visit2_str),
            (self.visit3_edit, visit3_str),
            (self.final_visit_edit, final_visit_str),
        ):
            d = parse_date_flex(value)
            if d:
                editor.setDate(self._date_to_qdate(d))
            elif editor in (self.visit2_edit, self.visit3_edit, self.final_visit_edit):
                editor.setDate(EMPTY_DATE_SENTINEL)  # Show empty until user selects

        self.remarks_edit.setText(remarks_str or "")

        self._loaded_patient_exists = True
        self._dirty = False  # Reset after loading
        # LMP not editable when editing existing record (required for new)
        self.lmp_edit.setReadOnly(True)

    def _get_date_str(self, editor: QDateEdit) -> Optional[str]:
        d = self._qdate_to_date(editor.date())
        return d.isoformat() if d else None

    def _get_optional_visit_date_str(self, editor: QDateEdit) -> Optional[str]:
        """For 3rd/Final Visit: return None when empty (sentinel), else date string."""
        qd = editor.date()
        if not qd.isValid() or qd == EMPTY_DATE_SENTINEL:
            return None
        return date(qd.year(), qd.month(), qd.day()).isoformat()

    def save_patient(self) -> None:
        # Block STAFF from saving locked records
        if self._record_locked and self.role == "STAFF":
            QMessageBox.warning(
                self,
                "Cannot Save",
                "This record is locked. Only ADMIN users can edit locked records.",
            )
            return

        patient_name = self.name_edit.text().strip()
        patient_id = self.patient_id_edit.text().strip()

        # New registration: required fields
        mobile_number = self.mobile_edit.text().strip()
        village_name = self.village_combo.currentText().strip()
        motivator_selection = self.motivator_combo.currentText().strip()
        motivator_name = (
            self.motivator_other_edit.text().strip()
            if motivator_selection == MOTIVATOR_OTHERS
            else motivator_selection
        )

        if not patient_name or not mobile_number or not village_name or not motivator_name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please fill all mandatory fields: Patient Name, Mobile Number, Village Name, and Motivator Name.",
            )
            return
        if motivator_selection == MOTIVATOR_OTHERS and not self.motivator_other_edit.text().strip():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please specify the motivator name when 'Others' is selected.",
            )
            return

        # When Others + new name: add to pre-loaded list for future use
        if motivator_selection == MOTIVATOR_OTHERS and motivator_name:
            add_custom_motivator(motivator_name)
            self._refresh_motivator_combo(motivator_name)

        # LMP Date is mandatory
        lmp_date = self._qdate_to_date(self.lmp_edit.date())
        if not lmp_date or not self.lmp_edit.date().isValid():
            QMessageBox.warning(
                self,
                "Validation Error",
                "LMP Date is required.",
            )
            return

        # Phone validation: digits only, 10-15 digits
        digits_only = "".join(c for c in mobile_number if c.isdigit())
        if len(digits_only) < 10:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Mobile number must contain at least 10 digits.",
            )
            return
        if len(digits_only) > 15:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Mobile number must not exceed 15 digits.",
            )
            return

        if lmp_date > date.today():
            QMessageBox.warning(
                self,
                "Validation Error",
                "LMP date cannot be in the future.",
            )
            return

        # Duplicate detection for new patients: same name+mobile or name+village
        # Use normalized digits for mobile comparison (handles "123 456 7890" vs "1234567890")
        if not self._loaded_patient_exists:
            digits_only = "".join(c for c in mobile_number if c.isdigit())
            conn_check = get_connection()
            try:
                cur_check = conn_check.cursor()
                cur_check.execute(
                    """
                    SELECT patient_id, patient_name, mobile_number, village_name FROM patients
                    WHERE LOWER(patient_name) = LOWER(?)
                    """,
                    (patient_name,),
                )
                dup = None
                for row in cur_check.fetchall():
                    pid, pname, db_mobile, db_village = row
                    db_digits = "".join(c for c in (db_mobile or "") if c.isdigit())
                    same_mobile = db_digits and digits_only and db_digits == digits_only
                    same_village = (village_name or "").lower() == (db_village or "").lower()
                    if same_mobile or same_village:
                        dup = (pid, pname)
                        break
            finally:
                conn_check.close()
            if dup:
                reply = QMessageBox.question(
                    self,
                    "Possible Duplicate",
                    f"A patient with similar details already exists:\n\n"
                    f"Patient ID: {dup[0]}\nName: {dup[1]}\n\n"
                    "Do you want to add this patient anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return

        lmp_date_str = self._get_date_str(self.lmp_edit)
        edd_date_str = self._get_date_str(self.edd_edit)
        visit1_str = self._get_date_str(self.visit1_edit)
        visit2_str = self._get_optional_visit_date_str(self.visit2_edit)
        visit3_str = self._get_optional_visit_date_str(self.visit3_edit)
        final_visit_str = self._get_optional_visit_date_str(self.final_visit_edit)
        entry_date_str = self._get_date_str(self.entry_date_edit)

        conn = get_connection()
        try:
            cur = conn.cursor()

            # Determine if this is a new or existing patient
            cur.execute(
                """
                SELECT
                    id,
                    serial_number,
                    patient_name,
                    mobile_number,
                    village_name,
                    lmp_date,
                    edd_date,
                    motivator_name,
                    visit1,
                    visit2,
                    visit3,
                    final_visit,
                    entry_date,
                    record_locked,
                    patient_id,
                    remarks
                FROM patients
                WHERE patient_id = ?
                """,
                (patient_id,),
            )
            existing = cur.fetchone()

            if existing is None:
                # New patient: use Patient ID from field (set by _generate_patient_id())
                if not entry_date_str:
                    today = date.today()
                    entry_date_str = today.isoformat()

                # Use visit dates from form (visit1 = Entry Date; 2nd/3rd/Final can be entered)
                visit1_str = self._get_date_str(self.visit1_edit)
                visit2_str = self._get_optional_visit_date_str(self.visit2_edit)
                visit3_str = self._get_optional_visit_date_str(self.visit3_edit)
                final_visit_str = self._get_optional_visit_date_str(self.final_visit_edit)

                cur.execute("SELECT COALESCE(MAX(serial_number), 0) + 1 FROM patients")
                serial_number = cur.fetchone()[0] or 1

                record_locked = 1 if final_visit_str else 0

                remarks_str = self.remarks_edit.text().strip() or None
                try:
                    cur.execute(
                        """
                        INSERT INTO patients (
                            serial_number,
                            patient_name,
                            patient_id,
                            mobile_number,
                            village_name,
                            lmp_date,
                            edd_date,
                            motivator_name,
                            visit1,
                            visit2,
                            visit3,
                            final_visit,
                            entry_date,
                            record_locked,
                            remarks
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            serial_number,
                            patient_name,
                            patient_id,
                            mobile_number,
                            village_name,
                            lmp_date_str,
                            edd_date_str,
                            motivator_name,
                            visit1_str,
                            visit2_str,
                            visit3_str,
                            final_visit_str,
                            entry_date_str,
                            record_locked,
                            remarks_str,
                        ),
                    )
                except sqlite3.IntegrityError:
                    conn.rollback()
                    reply = QMessageBox.question(
                        self,
                        "Duplicate Patient ID",
                        f"Patient ID '{patient_id}' already exists.\n\n"
                        "Would you like to load the existing record for editing?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if reply == QMessageBox.Yes:
                        self.load_patient()
                    return
            else:
                # Existing patient: log all field changes then update
                (
                    _,
                    serial_number,
                    old_patient_name,
                    old_mobile_number,
                    old_village_name,
                    old_lmp_date,
                    old_edd_date,
                    old_motivator_name,
                    old_visit1,
                    old_visit2,
                    old_visit3,
                    old_final_visit,
                    old_entry_date,
                    old_record_locked,
                    existing_pid,
                    old_remarks,
                ) = existing

                # Do not change patient_id when editing
                patient_id = existing_pid

                remarks_str = self.remarks_edit.text().strip() or None

                all_fields = [
                    ("patient_name", old_patient_name, patient_name),
                    ("mobile_number", old_mobile_number, mobile_number),
                    ("village_name", old_village_name, village_name),
                    ("lmp_date", old_lmp_date, lmp_date_str),
                    ("edd_date", old_edd_date, edd_date_str),
                    ("motivator_name", old_motivator_name, motivator_name),
                    ("visit1", old_visit1, visit1_str),
                    ("visit2", old_visit2, visit2_str),
                    ("visit3", old_visit3, visit3_str),
                    ("final_visit", old_final_visit, final_visit_str),
                    ("entry_date", old_entry_date, entry_date_str),
                    ("remarks", old_remarks, remarks_str),
                ]
                for field_name, old, new in all_fields:
                    if old != new:
                        log_change(
                            patient_id=patient_id,
                            field_name=field_name,
                            old_value=old,
                            new_value=new,
                            changed_by=self.username,
                        )

                # ADMIN can unlock via checkbox; otherwise keep lock if final_visit set
                if self.role == "ADMIN" and self.unlock_check.isChecked():
                    record_locked = 0
                    if old_record_locked != 0:
                        log_change(
                            patient_id=patient_id,
                            field_name="record_locked",
                            old_value=old_record_locked,
                            new_value=0,
                            changed_by=self.username,
                        )
                else:
                    record_locked = 1 if final_visit_str else 0

                cur.execute(
                    """
                    UPDATE patients
                    SET
                        patient_name = ?,
                        mobile_number = ?,
                        village_name = ?,
                        lmp_date = ?,
                        edd_date = ?,
                        motivator_name = ?,
                        visit1 = ?,
                        visit2 = ?,
                        visit3 = ?,
                        final_visit = ?,
                        entry_date = ?,
                        record_locked = ?,
                        remarks = ?
                    WHERE patient_id = ?
                    """,
                    (
                        patient_name,
                        mobile_number,
                        village_name,
                        lmp_date_str,
                        edd_date_str,
                        motivator_name,
                        visit1_str,
                        visit2_str,
                        visit3_str,
                        final_visit_str,
                        entry_date_str,
                        record_locked,
                        remarks_str,
                        patient_id,
                    ),
                )

            conn.commit()
        except Exception as exc:
            conn.rollback()
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Could not save patient record:\n{exc}",
            )
            return
        finally:
            conn.close()

        self._dirty = False
        self.accept()

