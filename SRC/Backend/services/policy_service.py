"""
Backend documentation for `services/policy_service.py`.

This service module owns business rules and database coordination so route handlers and UI code stay simple.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def is_late_cancellation(slot_start: datetime, *, now: datetime | None = None, deadline_minutes: int = 1440) -> bool:
    current = now or datetime.now(timezone.utc)
    return slot_start - current < timedelta(minutes=deadline_minutes)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def late_cancel_fee(is_late: bool, configured_fee: Decimal | None) -> Decimal:
    if not is_late or configured_fee is None:
        return Decimal("0")
    return configured_fee


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def reliability_score(total_bookings: int, no_shows: int, late_cancellations: int) -> int:
    if total_bookings <= 0:
        return 100
    penalty = (no_shows * 20) + (late_cancellations * 10)
    return max(0, min(100, 100 - penalty))
