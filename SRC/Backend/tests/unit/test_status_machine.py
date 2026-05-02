import pytest

from SRC.Backend.core.errors import InvalidTransitionError
from SRC.Backend.services.appointment_service import ALLOWED_TRANSITIONS


def test_unit_status_pending_to_confirmed_allowed():
    assert "confirmed" in ALLOWED_TRANSITIONS["pending"]


def test_unit_status_confirmed_to_no_show_allowed():
    assert "no_show" in ALLOWED_TRANSITIONS["confirmed"]
    assert ALLOWED_TRANSITIONS["no_show"] == set()


def test_unit_status_invalid_transition_raises_shape():
    with pytest.raises(InvalidTransitionError):
        raise InvalidTransitionError("completed", "pending")
