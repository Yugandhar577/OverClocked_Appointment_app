from datetime import datetime, timedelta, timezone
from decimal import Decimal


def is_late_cancellation(slot_start: datetime, *, now: datetime | None = None, deadline_minutes: int = 1440) -> bool:
    current = now or datetime.now(timezone.utc)
    return slot_start - current < timedelta(minutes=deadline_minutes)


def late_cancel_fee(is_late: bool, configured_fee: Decimal | None) -> Decimal:
    if not is_late or configured_fee is None:
        return Decimal("0")
    return configured_fee


def reliability_score(total_bookings: int, no_shows: int, late_cancellations: int) -> int:
    if total_bookings <= 0:
        return 100
    penalty = (no_shows * 20) + (late_cancellations * 10)
    return max(0, min(100, 100 - penalty))
