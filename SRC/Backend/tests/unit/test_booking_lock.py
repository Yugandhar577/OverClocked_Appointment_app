from pathlib import Path

from SRC.Backend.services.booking_service import LOCK_SLOT_SQL


def test_unit_booking_calls_for_update_skip_locked():
    source = Path("SRC/Backend/services/booking_service.py").read_text(encoding="utf-8")
    assert "FOR UPDATE SKIP LOCKED" in LOCK_SLOT_SQL
    assert "SELECT * FROM generated_slots" in source
    assert "AND is_blocked = FALSE AND booked_count < max_capacity" in source
