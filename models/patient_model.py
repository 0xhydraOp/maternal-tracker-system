from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


@dataclass
class Patient:
    """
    In-memory representation of a patient record.
    The database schema is defined in `database/init_db.py`.
    """

    id: Optional[int] = None
    serial_number: Optional[int] = None
    patient_name: str | None = None
    patient_id: str | None = None
    mobile_number: str | None = None
    lmp_date: Optional[date] = None
    edd_date: Optional[date] = None
    motivator_name: str | None = None
    visit1: Optional[date] = None
    visit2: Optional[date] = None
    visit3: Optional[date] = None
    final_visit: Optional[date] = None
    entry_date: Optional[date] = None
    record_locked: bool = False

    def calculate_edd(self) -> Optional[date]:
        """
        Calculate EDD as LMP + 280 days.
        """
        if not self.lmp_date:
            return None
        return self.lmp_date + timedelta(days=280)

