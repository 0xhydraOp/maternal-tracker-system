# Maternal Patient Tracking System

## Overview

This project is an offline desktop application used to track maternal patients and their scheduled check-up visits.

The application runs entirely offline and is compiled into a Windows `.exe` using PyInstaller.

**Technology stack:**
- Python
- PySide6 (GUI framework)
- SQLite (database)
- pandas + openpyxl (Excel export/import)
- PyInstaller (for creating `.exe`)

**Date format (everywhere across the board):**
- **Display:** `dd-mm-yyyy` (e.g. 15-03-2026) — all UI, tables, reports, exports
- **Storage:** `yyyy-mm-dd` (ISO) — database only, internal use

---

## Core Features

The system manages:
- Patient records (with village, motivator, remarks)
- Motivator tracking (built-in + custom motivators)
- Visit scheduling (1st, 2nd, 3rd, Final Visit)
- Visit reminders (due soon, overdue)
- Role-based access (ADMIN / STAFF)
- Change logs (all field edits)
- Activity log (admin actions)
- Backup system (automatic daily + manual)
- Reporting (Patient List, Visit Completion, Motivator Performance, Monthly Summary, Charts)
- Excel export and import
- Dark / light theme

---

## UI Polish

- **Status bar** – bottom of main window; shows brief feedback (e.g. "Patient saved successfully", "Data refreshed", "Backup created successfully", "Import complete")
- **About dialog** – app name, version, copyright; opened from sidebar footer
- **Tooltips** – on sidebar nav buttons (including shortcuts: Ctrl+N, Ctrl+F)
- **Minimum window size** – 1024×600 px
- **Cursor feedback** – wait cursor during heavy operations (stats refresh, backup, import, patient load, export)
- **Splash screen** – shows app name and version (e.g. "v1.0.0 · Loading...") on startup
- **Placeholders** – on Patient Search filters (Patient Name, Patient ID, Mobile, Village, Motivator, Block/Municipality)

---

## Patient Data Fields

Each patient record contains:

| Field | Description |
|-------|-------------|
| Serial Number | Auto-generated |
| Patient Name | Required |
| Patient ID | Unique, auto-generated (PT&lt;seq&gt;-&lt;MM&gt;-&lt;YYYY&gt;) |
| Mobile Number | Required |
| Village Name | Required |
| LMP Date | Last Menstrual Period, required |
| EDD Date | Expected Delivery Date (auto-calculated from LMP) |
| Motivator Name | Required |
| 1st Visit | Same as Entry Date (read-only) |
| 2nd Visit | Date (manual entry) |
| 3rd Visit | Date (manual entry) |
| Final Visit | Date (manual entry; locks record when set) |
| Entry Date | Registration date (read-only in Patient Entry) |
| Remarks | Optional notes |
| Record Locked | 0 or 1 (set when Final Visit is entered) |
| District | Fixed (Murshidabad) |
| Block | Optional; selectable from district blocks |
| Municipality | Optional; selectable from district municipalities |
| Ward Number | Optional; for municipality records |

---

## Automatic Calculations

- **EDD** = LMP + 280 days (calculated automatically from LMP; user may override)
- **1st Visit** = Entry Date (always; not editable separately)
- **2nd, 3rd, Final Visit** = entered manually by user

---

## Validation Rules

- Patient ID must be unique (auto-generated on new registration)
- Duplicate Patient ID prevents save
- Duplicate detection for new patients: same name + mobile (digits normalized) or same name + village
- Mobile: 10–15 digits
- LMP date cannot be in the future
- Phone numbers may repeat
- **Visit order**: 1st Visit = Entry Date; 2nd ≥ 1st; 3rd ≥ 2nd; Final ≥ 3rd (or 2nd if 3rd empty)

---

## Record Locking

- When **Final Visit** is entered, the record becomes locked
- **STAFF** cannot edit locked records (including inline edits in Patient Search)
- Only **ADMIN** can unlock records (via Administration → Patient Management → Unlock)

---

## User Roles

### ADMIN
- Add and edit all patient records
- Unlock locked records
- Manage users (add, edit, delete); cannot delete the last administrator
- View change logs
- Manage custom motivators
- View reports
- Trigger manual backup and restore
- Change settings (admin password, backup folder, dark mode)
- Delete patients

### STAFF
- Add patients
- Update visit dates and remarks (inline in Patient Search, or via Patient Entry)
- Search and export records
- View reports
- Cannot edit locked records, delete patients, unlock records, or access Administration

---

## Change Log System

All edits to patient records are logged in `change_logs`:
- Patient ID
- Field name
- Old value
- New value
- Changed by (username)
- Change time

Logged fields: patient_name, mobile_number, village_name, lmp_date, edd_date, motivator_name, visit1, visit2, visit3, final_visit, entry_date, remarks, record_locked.

---

## Dashboard

- **Keyboard shortcuts:** Ctrl+N (Register Patient), Ctrl+F (Search Patients)
- Statistics cards (clickable to open filtered Patient Search):
- **Next Visit Due This Week** – next scheduled visit is within 7 days
- **Overdue Visits** – next scheduled visit is in the past; detects "missed" visits (completed 1 missed 2, completed 12 missed 3, completed 123 missed final) via chain rule and `record_locked`
- **EDD Within 30 Days** – expected delivery in next 30 days
- **Today's Entries** – patients registered today

---

## Patient Search

- Filters: Patient Name, Patient ID, Mobile, Motivator, Village, Block/Municipality, Entry Date (presets: All, Last 7 days, Last 30 days, This Month, This Year, Custom range)
- Column order: Serial No, Entry Date, Patient Name, Patient ID, Block, Municipality, Village, Ward, Mobile, Motivator, LMP Date, EDD Date, 1st Visit, 2nd Visit, 3rd Visit, Final Visit, Remarks
- Inline editing: EDD, visit dates, and Remarks (double-click to edit); visit order validated (2nd ≥ 1st, 3rd ≥ 2nd, final ≥ previous)
- Export to Excel (all or selected rows)
- Enter key opens selected patient; debounced live filtering
- STAFF cannot edit locked records inline

---

## Reports

Organized layout with filters in group boxes and result counts. Reports refresh automatically when navigating to the Reports tab.

- **Patient List** – filters (date presets: All, Last 7/30 days, This Month/Year, Custom; motivator, patient name, village, Block/Municipality); Apply/Export buttons; result count; export to Excel; custom date range auto-swaps if From > To
- **Visit Completion** – completion rates for 1st, 2nd, 3rd, Final Visit
- **Motivator Performance** – patients and visit completion by motivator; includes **Final %** (finalized completion percentage per motivator)
- **Monthly Summary** – registrations, visits, overdue, EDD, completed (last 12 months)
- **Block & Municipality** – tables showing patient counts and visits completed by block and by municipality
- **Charts**:
  - Registrations per month (12 months ending with selected month/year)
  - Top Motivators – top 15 by patient count
  - Motivator Month-wise Performance – select any motivator, view their registrations per month for past 12 months (month/year selector)
  - Patients by Village – top 15

---

## Backup System

- **Automatic daily backup** on app startup and every 24 hours
- **Configurable backup folder** (Settings in Administration)
- **Naming format:** `backup_YYYY_MM_DD.db`
- Keeps latest 30 backups; older ones deleted automatically
- **Manual backup** – save copy to user-chosen location
- **Restore** – restore from a `.db` file; creates pre-restore backup before overwriting

---

## Excel Import

- Import patient records from Excel
- Supported columns: patient name, mobile, village, lmp, edd, motivator, visit1–3, final visit, entry date, remarks, serial number, district, block, municipality, ward
- Patient ID auto-generated if not in file
- Skips rows with missing patient name, missing mobile, invalid mobile (not 10–15 digits), or duplicate Patient ID
- Visit order enforced: visit1 = entry_date; visit2 ≥ visit1; visit3 ≥ visit2; final ≥ visit3
- On duplicate Patient ID (IntegrityError): skips row if ID from Excel; retries with new auto-generated ID (up to 5 times) if ID was auto-generated
- Returns imported count and skipped count
- Saves copy of imported file to backup folder

---

## Database Structure

### patients
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| serial_number | INTEGER |
| patient_name | TEXT NOT NULL |
| patient_id | TEXT NOT NULL UNIQUE |
| mobile_number | TEXT |
| village_name | TEXT |
| district_name | TEXT |
| block_name | TEXT |
| municipality_name | TEXT |
| ward_number | TEXT |
| lmp_date | TEXT |
| edd_date | TEXT |
| motivator_name | TEXT |
| visit1 | TEXT |
| visit2 | TEXT |
| visit3 | TEXT |
| final_visit | TEXT |
| entry_date | TEXT |
| record_locked | INTEGER DEFAULT 0 |
| remarks | TEXT |
| created_at | TEXT |

### users
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| username | TEXT NOT NULL UNIQUE |
| password_hash | TEXT NOT NULL |
| role | TEXT NOT NULL |
| created_at | TEXT |

### change_logs
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| patient_id | TEXT NOT NULL |
| field_name | TEXT NOT NULL |
| old_value | TEXT |
| new_value | TEXT |
| changed_by | TEXT NOT NULL |
| changed_at | TEXT |

### custom_motivators
| Column | Type |
|--------|------|
| name | TEXT PRIMARY KEY |
| added_at | TEXT |

### activity_log
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| action | TEXT NOT NULL |
| details | TEXT |
| performed_by | TEXT NOT NULL |
| performed_at | TEXT NOT NULL |

---

## Application Screens

- **Login** – square window (520×520 px), username/password, default admin/admin123
- **Dashboard** – stats cards, quick actions; status bar; minimum size 1024×600; About button in sidebar footer
- **Patient Entry** – add/edit patient (full form); 1st Visit = Entry Date; motivator "Others" with "Please specify" field
- **Patient Search** – filter, inline edit, export
- **Reports** – Patient List, Visit Completion, Motivator Performance, Monthly Summary, Charts
- **Backup Manager** – manual backup, restore, view backup folder
- **Administration** (ADMIN only):
  - User Management – add, edit, delete users; duplicate username shows validation message; cannot delete last admin
  - Patient Management (edit, delete, unlock) – simplified table with filters
  - Change Logs
  - Custom Motivators
  - Settings (admin password, backup folder, dark mode) – grouped in QGroupBox

---

## Project Structure

```
maternal_tracking/
├── main.py                 # Entry point
├── config.py               # Config (APP_VERSION, admin password, dark mode, backup dir)
├── config.json             # User settings (created at runtime)
├── styles.py               # Light/dark theme stylesheets
├── requirements.txt
├── maternal_tracking.spec  # PyInstaller spec
├── build_exe.ps1           # Build script for .exe
├── build_installer.ps1     # Build Inno Setup installer
├── database/
│   ├── init_db.py          # Schema, migrations
│   └── maternal_tracking.db  # Created at runtime
├── ui/
│   ├── dashboard.py
│   ├── login_window.py
│   ├── patient_entry.py
│   ├── patient_search.py
│   ├── reports.py
│   ├── administration.py
│   └── change_password_dialog.py
├── services/
│   ├── backup_service.py
│   ├── change_logger.py
│   ├── activity_logger.py
│   ├── motivator_service.py
│   ├── village_service.py
│   ├── location_service.py   # District, blocks, municipalities (Murshidabad)
│   ├── password_service.py
│   ├── excel_import_service.py
│   └── visit_scheduler.py
├── utils/
│   ├── date_utils.py
│   └── icon_utils.py
├── assets/
│   ├── icon.png            # App icon (created at runtime if missing)
│   └── icon.ico            # Windows icon (created by build script)
├── scripts/
│   ├── clear_dummy_data.py   # Remove all patient data from DB
│   ├── fix_visit_dates.py    # Repair invalid visit date order
│   └── create_icon_ico.py    # Generate Windows icon
├── tests/
│   └── test_all_functions.py   # Unit tests
├── installer.iss           # Inno Setup script
├── version_info.txt       # Windows exe version metadata
├── LICENSE.txt            # Shown during installer
├── WELCOME.txt            # Installer welcome text
└── backups/               # Created at runtime
```

### Scripts

| Script | Purpose |
|-------|---------|
| `python -m scripts.clear_dummy_data` | Remove all patients and change logs from DB |
| `python -m scripts.fix_visit_dates` | Repair invalid visit date order in existing records |
| `python -m scripts.create_icon_ico` | Generate `icon.ico` for Windows build |

---

## Compilation

### Build executable only

```powershell
.\build_exe.ps1
```

Output: `MaternalTracking.exe` in the project folder.

### Build installer (recommended for distribution)

1. Install [Inno Setup 6](https://jrsoftware.org/isinfo.php)
2. Run:

```powershell
.\build_installer.ps1
```

Output: `dist\MaternalTracker_Setup_1.0.0.exe` — a professional installer with:
- Welcome screen
- License agreement
- Install location choice
- Start Menu and optional Desktop shortcut
- Uninstaller in Add/Remove Programs
- App icon and version info on the .exe

### Manual build

```powershell
pyinstaller --clean --noconfirm maternal_tracking.spec --distpath .
```

When run as `.exe`, config, database, and backups are stored next to the executable. The app detects frozen (compiled) mode and uses paths relative to the executable.

### Run tests

```powershell
python -m unittest tests.test_all_functions -v
```

---

## Configuration

- **Version** – `APP_VERSION` in `config.py` (e.g. 1.0.0); used in splash screen and About dialog
- Stored in `config.json` (created on first settings change):
- `admin_area_password` – password for Administration Area
- `dark_mode` – light or dark theme
- `backup_dir` – path for backup files
