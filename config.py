"""
Application configuration.
Admin area password and theme can be changed here or via settings.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
DEFAULT_BACKUP_DIR = str(BASE_DIR / "backups")

DEFAULTS = {
    "admin_area_password": "admin@123",
    "dark_mode": False,
    "backup_dir": DEFAULT_BACKUP_DIR,
}


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULTS, **data}
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULTS.copy()


def _save_config(data: dict) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def get_admin_area_password() -> str:
    return _load_config().get("admin_area_password", DEFAULTS["admin_area_password"])


def set_admin_area_password(password: str) -> None:
    data = _load_config()
    data["admin_area_password"] = password
    _save_config(data)


def get_dark_mode() -> bool:
    return _load_config().get("dark_mode", DEFAULTS["dark_mode"])


def set_dark_mode(enabled: bool) -> None:
    data = _load_config()
    data["dark_mode"] = enabled
    _save_config(data)


def get_backup_dir() -> str:
    return _load_config().get("backup_dir", DEFAULT_BACKUP_DIR)


def set_backup_dir(path: str) -> None:
    data = _load_config()
    data["backup_dir"] = path
    _save_config(data)
