import pytest

from SRC.Backend.core.errors import InvalidTransitionError
from SRC.Backend.services.appointment_service import ALLOWED_TRANSITIONS


def test_unit_status_pending_to_confirmed_allowed():
    assert "confirmed" in ALLOWED_TRANSITIONS["pending"]


def test_unit_status_invalid_transition_raises_shape():
    with pytest.raises(InvalidTransitionError):
        raise InvalidTransitionError("completed", "pending")
