# Maternal Patient Tracking System

This is a desktop application for tracking maternal patients, their scheduled visits, and related administration data. It is designed to run fully offline and uses:

- Python
- PySide6 (GUI)
- SQLite (database)

## Project Layout

- `main.py` – Application entry point
- `database/` – SQLite database and initialization scripts
- `models/` – Data models
- `services/` – Business logic (visit scheduling, backups, etc.)
- `ui/` – PySide6 UI components
- `backups/` – Automatic and manual backup files

## Setup

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
python main.py
```

## Building the Executable

To build a single-file Windows executable:

```bash
pyinstaller --onefile main.py
```

