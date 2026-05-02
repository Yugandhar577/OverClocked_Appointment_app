from SRC.Backend.services.organization_service import ALLOWED_ORG_STATUSES, merge_report_notes, normalize_domain


def test_normalize_domain_trims_and_lowercases():
    assert normalize_domain("  Example.COM ") == "example.com"


def test_merge_report_notes_chains():
    assert merge_report_notes(None, "first") == "first"
    assert merge_report_notes("a", "b") == "a\n---\nb"
    assert merge_report_notes("a\n", "  x  ") == "a\n---\nx"


def test_allowed_org_statuses_is_closed_set():
    assert "active" in ALLOWED_ORG_STATUSES
    assert "aborted" in ALLOWED_ORG_STATUSES
