from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Tuple


VISIT_INTERVAL_DAYS = 60
UPCOMING_DAYS = 7
EDD_UPCOMING_DAYS = 30


def schedule_subsequent_visits(
    visit1: Optional[date],
    visit2: Optional[date],
    visit3: Optional[date],
    final_visit: Optional[date],
) -> Tuple[Optional[date], Optional[date], Optional[date], Optional[date]]:
    """
    Apply visit scheduling rules:

    - 1st visit is entered manually.
    - 2nd = 1st + 60 days (if 1st provided and 2nd not manually overridden).
    - 3rd = 2nd + 60 days.
    - Final = 3rd + 60 days.

    This function focuses on the core calculation logic. The caller is
    responsible for deciding when a visit is considered "edited manually"
    and which earlier visits need to be treated as authoritative.
    """
    v1 = visit1
    v2 = visit2
    v3 = visit3
    v4 = final_visit

    if v1 and not v2:
        v2 = v1 + timedelta(days=VISIT_INTERVAL_DAYS)
    if v2 and not v3:
        v3 = v2 + timedelta(days=VISIT_INTERVAL_DAYS)
    if v3 and not v4:
        v4 = v3 + timedelta(days=VISIT_INTERVAL_DAYS)

    return v1, v2, v3, v4


def get_next_visit_due(
    visit1: Optional[date],
    visit2: Optional[date],
    visit3: Optional[date],
    final_visit: Optional[date],
    today: Optional[date] = None,
) -> Optional[date]:
    """Return the next visit due date, or None if all visits done or no visits yet."""
    if today is None:
        today = date.today()
    completed = [d for d in (visit1, visit2, visit3, final_visit) if d and d <= today]
    if not completed:
        return None
    if final_visit and final_visit <= today:
        return None  # All visits done
    last = max(completed)
    return last + timedelta(days=VISIT_INTERVAL_DAYS)


def classify_visit_status(visit_date: Optional[date], today: Optional[date] = None) -> str:
    """
    Classify a visit as 'upcoming', 'overdue', 'completed', or 'none'.
    For scheduled visits, the UI or higher-level code can inspect this
    status and apply appropriate highlighting.
    """
    if today is None:
        today = date.today()

    if visit_date is None:
        return "none"

    if visit_date < today:
        return "overdue"

    delta = (visit_date - today).days
    if 0 <= delta <= UPCOMING_DAYS:
        return "upcoming"

    return "scheduled"

