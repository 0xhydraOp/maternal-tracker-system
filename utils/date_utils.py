"""
Central date format and parsing utilities.
Display format: dd-mm-yyyy across the application.
Storage format: yyyy-mm-dd (ISO) for database compatibility.
"""
from __future__ import annotations

from datetime import date
from typing import Optional


# Display format for all UI (dd-mm-yyyy)
DATE_FORMAT_DISPLAY = "dd-MM-yyyy"

# Storage format for database (yyyy-mm-dd, ISO)
DATE_FORMAT_STORAGE = "yyyy-MM-dd"


def parse_date(s: Optional[str]) -> Optional[date]:
    """
    Parse date string. Accepts both dd-mm-yyyy and yyyy-mm-dd.
    Returns None for invalid or empty input.
    """
    if not s:
        return None
    s = str(s).strip()[:10]
    if not s:
        return None
    try:
        # Try yyyy-mm-dd (ISO) first
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            return date.fromisoformat(s)
        # Try dd-mm-yyyy
        if len(s) == 10 and s[2] == "-" and s[5] == "-":
            parts = s.split("-")
            return date(int(parts[2]), int(parts[1]), int(parts[0]))
    except (ValueError, TypeError, IndexError):
        pass
    return None


def format_for_display(d: date) -> str:
    """Format date for display (dd-mm-yyyy)."""
    return d.strftime("%d-%m-%Y")


def format_for_storage(d: date) -> str:
    """Format date for database storage (yyyy-mm-dd)."""
    return d.isoformat()
