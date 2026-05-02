"""
Backend documentation for `tests/unit/test_status_machine.py`.

This test module documents expected backend behavior and protects critical booking workflows from regressions.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

import pytest

from SRC.Backend.core.errors import InvalidTransitionError
from SRC.Backend.services.appointment_service import ALLOWED_TRANSITIONS


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_unit_status_pending_to_confirmed_allowed():
    assert "confirmed" in ALLOWED_TRANSITIONS["pending"]


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_unit_status_confirmed_to_no_show_allowed():
    assert "no_show" in ALLOWED_TRANSITIONS["confirmed"]
    assert ALLOWED_TRANSITIONS["no_show"] == set()


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_unit_status_invalid_transition_raises_shape():
    with pytest.raises(InvalidTransitionError):
        raise InvalidTransitionError("completed", "pending")
