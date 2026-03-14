from __future__ import annotations

from datetime import date
from pathlib import Path
import shutil

from database.init_db import DB_PATH, BASE_DIR
from config import get_backup_dir


def _get_backup_dir() -> Path:
    return Path(get_backup_dir())


# For backward compatibility - use get_backup_dir_path() in new code
def get_backup_dir_path() -> Path:
    return _get_backup_dir()


def _backup_filename_for_day(day: date) -> Path:
    return _get_backup_dir() / f"backup_{day.year:04d}_{day.month:02d}_{day.day:02d}.db"


MAX_BACKUPS = 30


def ensure_today_backup() -> None:
    """
    Create today's backup file if it does not already exist.
    Keeps only the latest MAX_BACKUPS backups in the backups directory.
    """
    backup_dir = _get_backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)

    today = date.today()
    target = _backup_filename_for_day(today)

    if not DB_PATH.exists():
        return

    if not target.exists():
        shutil.copy2(DB_PATH, target)

    _prune_old_backups()


def _prune_old_backups() -> None:
    """
    Remove older backup files, keeping at most MAX_BACKUPS by modification time.
    """
    backup_dir = _get_backup_dir()
    if not backup_dir.exists():
        return

    backups = sorted(
        backup_dir.glob("backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for old_backup in backups[MAX_BACKUPS:]:
        try:
            old_backup.unlink()
        except OSError:
            # Ignore failures when deleting old backups
            pass


def list_backups() -> list[tuple[Path, str, int]]:
    """
    Return list of (path, date_str, size_bytes) for each backup, newest first.
    """
    backup_dir = _get_backup_dir()
    if not backup_dir.exists():
        return []
    backups = sorted(
        backup_dir.glob("backup_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    result = []
    for p in backups:
        try:
            stat = p.stat()
            name = p.name
            date_str = name.replace("backup_", "").replace(".db", "").replace("_", "-")
            result.append((p, date_str, stat.st_size))
        except OSError:
            pass
    return result


def create_manual_backup() -> Path | None:
    """Create a backup now and return the path, or None on failure."""
    _get_backup_dir().mkdir(parents=True, exist_ok=True)
    today = date.today()
    target = _backup_filename_for_day(today)
    if not DB_PATH.exists():
        return None
    shutil.copy2(DB_PATH, target)
    _prune_old_backups()
    return target


def restore_backup(backup_path: Path) -> bool:
    """Restore database from backup. Returns True on success."""
    if not backup_path.exists() or not backup_path.is_file():
        return False
    try:
        shutil.copy2(backup_path, DB_PATH)
        return True
    except OSError:
        return False

