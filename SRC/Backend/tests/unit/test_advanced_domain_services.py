"""
Backend documentation for `tests/unit/test_advanced_domain_services.py`.

This test module documents expected backend behavior and protects critical booking workflows from regressions.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from SRC.Backend.services.assignment_service import AssignmentCandidate, AssignmentRequest, choose_resource
from SRC.Backend.services.notification_workflow_service import MissingTemplateValueError, render_template
from SRC.Backend.services.policy_service import is_late_cancellation, late_cancel_fee, reliability_score
from SRC.Backend.services.recurring_service import expand_recurrence


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_assignment_prefers_available_preferred_resource():
    preferred = uuid4()
    other = uuid4()

    assert choose_resource(
        [
            AssignmentCandidate(resource_id=other, workload=0),
            AssignmentCandidate(resource_id=preferred, workload=10),
        ],
        AssignmentRequest(preferred_resource_id=preferred),
    ) == preferred


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_recurring_weekly_expansion():
    assert expand_recurrence(date(2026, 5, 2), "weekly", 3) == [
        date(2026, 5, 2),
        date(2026, 5, 9),
        date(2026, 5, 16),
    ]


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_policy_fee_and_reliability_score():
    slot_start = datetime(2026, 5, 2, 12, 0, tzinfo=timezone.utc)
    now = datetime(2026, 5, 2, 11, 30, tzinfo=timezone.utc)

    assert is_late_cancellation(slot_start, now=now, deadline_minutes=60)
    assert late_cancel_fee(True, Decimal("50")) == Decimal("50")
    assert reliability_score(10, no_shows=1, late_cancellations=2) == 60


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_notification_template_requires_values():
    assert render_template("Hello $customer", {"customer": "Asha"}) == "Hello Asha"
    with pytest.raises(MissingTemplateValueError):
        render_template("Hello $customer", {})
