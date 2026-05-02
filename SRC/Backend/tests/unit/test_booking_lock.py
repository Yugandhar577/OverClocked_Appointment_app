"""
Backend documentation for `tests/unit/test_booking_lock.py`.

This test module documents expected backend behavior and protects critical booking workflows from regressions.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from pathlib import Path

from SRC.Backend.services.booking_service import LOCK_SLOT_SQL


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_unit_booking_calls_for_update_skip_locked():
    source = Path("SRC/Backend/services/booking_service.py").read_text(encoding="utf-8")
    assert "FOR UPDATE SKIP LOCKED" in LOCK_SLOT_SQL
    assert "SELECT * FROM generated_slots" in source
    assert "AND is_blocked = FALSE AND booked_count < max_capacity" in source


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_unit_booking_has_retryable_lock_error():
    source = Path("SRC/Backend/services/booking_service.py").read_text(encoding="utf-8")
    errors = Path("SRC/Backend/core/errors.py").read_text(encoding="utf-8")
    assert "_raise_slot_lock_or_unavailable" in source
    assert "BookingInProgressError" in source
    assert 'detail = "booking_in_progress"' in errors
