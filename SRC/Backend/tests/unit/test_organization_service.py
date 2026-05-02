"""
Backend documentation for `tests/unit/test_organization_service.py`.

This test module documents expected backend behavior and protects critical booking workflows from regressions.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from SRC.Backend.services.organization_service import ALLOWED_ORG_STATUSES, merge_report_notes, normalize_domain


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_normalize_domain_trims_and_lowercases():
    assert normalize_domain("  Example.COM ") == "example.com"


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_merge_report_notes_chains():
    assert merge_report_notes(None, "first") == "first"
    assert merge_report_notes("a", "b") == "a\n---\nb"
    assert merge_report_notes("a\n", "  x  ") == "a\n---\nx"


# Backend note: Asserts a specific backend behavior so future changes can be checked safely.
def test_allowed_org_statuses_is_closed_set():
    assert "active" in ALLOWED_ORG_STATUSES
    assert "aborted" in ALLOWED_ORG_STATUSES
