PROJECT_SPEC.md
# Maternal Patient Tracking System

## Overview

This project is an offline desktop application used to track maternal patients and their scheduled check-up visits.

The application must run entirely offline and later be compiled into a Windows `.exe`.

Technology stack:

- Python
- PySide6 (GUI framework)
- SQLite (database)
- PyInstaller (for creating `.exe`)

---

# Core Features

The system will manage:

- Patient records
- Motivator tracking
- Visit scheduling
- Visit reminders
- Role-based access
- Change logs
- Backup system
- Reporting

---

# Patient Data Fields

Each patient record must contain the following fields:

Serial Number (auto generated)

Patient Name

Patient ID (must be unique)

Mobile Number

LMP Date (Last Menstrual Period)

EDD Date (Expected Delivery Date)

Motivator Name

1st Visit

2nd Visit

3rd Visit

Final Visit

Entry Date

Final Motivator Name

---

# Automatic Calculations

EDD must be calculated automatically.

EDD = LMP + 280 days

Users should not manually enter EDD.

---

# Visit Scheduling Logic

Visit scheduling follows this rule:

1st Visit → entered manually

2nd Visit = 1st Visit + 60 days

3rd Visit = 2nd Visit + 60 days

Final Visit = 3rd Visit + 60 days

---

# Visit Edit Rule

If any visit date is edited manually:

All later visits must automatically recalculate.

Example:

If 2nd Visit changes,
then 3rd Visit and Final Visit must update automatically.

---

# Validation Rules

Patient ID must be unique.

If the system detects a duplicate Patient ID:

The record must NOT be saved.

Phone numbers are allowed to repeat.

---

# Record Locking

Once Final Visit is entered:

The patient record becomes locked.

Locked records cannot be modified by STAFF users.

Only ADMIN users can unlock records.

---

# User Roles

The system must support two user roles.

## ADMIN

Admins can:

- Add patients
- Edit all records
- Unlock locked records
- View change logs
- Manage users
- View reports
- Trigger manual backup

## STAFF

Staff users can:

- Add patients
- Update visit dates
- Search records
- View reports

Staff users cannot:

- Edit Patient ID
- Delete records
- Unlock locked records
- View change logs

---

# Change Log System

All edits must be recorded.

When a visit date is changed:

The system must log:

Patient ID  
Field Name  
Old Value  
New Value  
Changed By  
Change Time

Logs are stored in a table called:

change_logs

---

# Dashboard

The dashboard must display the following statistics:

Patients with visits due within 7 days

Overdue visits

EDD within 30 days

Entries created today

Each statistic should be clickable to open the relevant records.

---

# Visit Reminder Logic

Visits must be classified as:

Upcoming (within 7 days)

Overdue (date already passed)

Completed

These should be visually highlighted.

Example:

Red → overdue  
Orange → due soon  
Green → completed

---

# Reports

The system must allow filtering records by:

Entry Date

Month

Year

Motivator

Patient Name

Reports must support export to Excel.

---

# Database Structure

The system uses SQLite.

## patients table

id  
serial_number  
patient_name  
patient_id (unique)  
mobile_number  
lmp_date  
edd_date  
motivator_name  
visit1  
visit2  
visit3  
final_visit  
entry_date  
final_motivator  
record_locked  
created_at

---

## users table

id  
username  
password_hash  
role  
created_at

---

## change_logs table

id  
patient_id  
field_name  
old_value  
new_value  
changed_by  
changed_at

---

# Backup System

The system must create automatic daily backups.

Backup files must be stored inside:

/backups

Naming format:

backup_YYYY_MM_DD.db

Example:

backup_2026_03_12.db

The system should keep the latest 30 backups only.

Older backups may be deleted automatically.

---

# Application Screens

The program must include the following screens:

Login Screen

Dashboard

Patient Entry Screen

Patient Search Screen

Record Viewer

Change Log Viewer

Admin User Management

Backup Manager

Reports Screen

---

# Project Structure

The project should follow this folder structure:

main.py

database/

ui/

models/

services/

backups/

---

# Compilation

The application must be compiled into a Windows executable using:

pyinstaller --onefile main.py