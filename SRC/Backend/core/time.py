"""
Backend documentation for `core/time.py`.

This core utility module centralizes shared backend behavior such as security, dependency injection, errors, or time handling.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from datetime import UTC, date, datetime, timedelta


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def utcnow() -> datetime:
    return datetime.now(UTC)

# Function explanation:
# `utcnow` returns the current UTC-aware datetime. Centralizing UTC
# retrieval helps ensure consistent timezone-aware timestamps across
# the codebase and simplifies testing by allowing injection or mocking.
#
# Alternative (commented): provide a testable provider that can be
# overridden in tests or configured for deterministic time values.
#
# class TimeProvider:
#     def now(self) -> datetime:
#         return datetime.now(UTC)
#
# time_provider = TimeProvider()
#
# def utcnow() -> datetime:
#     return time_provider.now()


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def utc_day_bounds_for_local_date(value: date, tz_offset_minutes: int = 0) -> tuple[datetime, datetime]:
    local_midnight_as_utc = datetime(value.year, value.month, value.day, tzinfo=UTC) - timedelta(minutes=tz_offset_minutes)
    return local_midnight_as_utc, local_midnight_as_utc + timedelta(days=1)


# Function explanation:
# `utc_day_bounds_for_local_date` computes the UTC datetime range that
# corresponds to a full local date for a particular timezone offset. The
# `tz_offset_minutes` parameter shifts the local midnight to UTC, allowing
# generation of inclusive day ranges for queries or schedule generation.
#
# Alternative (commented): use `zoneinfo` and proper timezone-aware
# conversions for named timezones rather than minute offsets. This is
# more accurate for DST and real-world timezones.
#
# from zoneinfo import ZoneInfo
#
# def utc_day_bounds_for_local_date_zone(value: date, tz_name: str) -> tuple[datetime, datetime]:
#     tz = ZoneInfo(tz_name)
#     local_start = datetime(value.year, value.month, value.day, tzinfo=tz)
#     utc_start = local_start.astimezone(UTC)
#     return utc_start, (utc_start + timedelta(days=1))
