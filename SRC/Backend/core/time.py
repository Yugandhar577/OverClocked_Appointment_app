from datetime import UTC, date, datetime, timedelta


def utcnow() -> datetime:
    return datetime.now(UTC)


def utc_day_bounds_for_local_date(value: date, tz_offset_minutes: int = 0) -> tuple[datetime, datetime]:
    local_midnight_as_utc = datetime(value.year, value.month, value.day, tzinfo=UTC) - timedelta(minutes=tz_offset_minutes)
    return local_midnight_as_utc, local_midnight_as_utc + timedelta(days=1)
