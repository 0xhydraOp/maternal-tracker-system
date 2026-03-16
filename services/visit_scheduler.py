from __future__ import annotations

from datetime import date
from typing import Optional, Tuple


UPCOMING_DAYS = 7
EDD_UPCOMING_DAYS = 30


def schedule_subsequent_visits(
    visit1: Optional[date],
    visit2: Optional[date],
    visit3: Optional[date],
    final_visit: Optional[date],
) -> Tuple[Optional[date], Optional[date], Optional[date], Optional[date]]:
    """
    Return visit dates as-is. No automatic interval scheduling.
    All visit dates are entered manually by the user.
    """
    return visit1, visit2, visit3, final_visit


def get_next_visit_due(
    visit1: Optional[date],
    visit2: Optional[date],
    visit3: Optional[date],
    final_visit: Optional[date],
    today: Optional[date] = None,
    record_locked: bool = False,
) -> Optional[date]:
    """
    Return the next visit due date, or None if all visits done or no visits yet.
    Uses only scheduled (entered) visit dates - no interval projection.

    A visit is considered "completed" only when the next visit in sequence exists
    (or for final: when record_locked). This allows "missed" visits (scheduled
    in the past but not done) to be detected as overdue.
    """
    if today is None:
        today = date.today()
    # Future visits (scheduled dates in the future) - next due is earliest of those
    future = [d for d in (visit1, visit2, visit3, final_visit) if d and d > today]
    if future:
        return min(future)
    # No future visits - use chain rule for completed
    # visit1 completed: visit2 exists; visit2: visit3 exists; visit3: final exists; final: record_locked
    completed: list[date] = []
    if visit1 and visit1 <= today and visit2:
        completed.append(visit1)
    if visit2 and visit2 <= today and visit3:
        completed.append(visit2)
    if visit3 and visit3 <= today and final_visit:
        completed.append(visit3)
    if final_visit and final_visit <= today and record_locked:
        completed.append(final_visit)
    if not completed:
        return None
    last_done = max(completed)
    next_scheduled = [d for d in (visit1, visit2, visit3, final_visit) if d and d > last_done]
    return min(next_scheduled) if next_scheduled else None


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

