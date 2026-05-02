"""
Backend documentation for `services/notification_workflow_service.py`.

This service module owns business rules and database coordination so route handlers and UI code stay simple.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from string import Template


# Backend note: Groups related backend data or behavior for a single domain concept.
class MissingTemplateValueError(ValueError):
    pass


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def render_template(template: str, values: dict[str, object]) -> str:
    try:
        return Template(template).substitute({key: "" if value is None else str(value) for key, value in values.items()})
    except KeyError as exc:
        raise MissingTemplateValueError(str(exc)) from exc


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def channel_payload(channel: str, *, recipient: str, subject: str | None, body: str) -> dict[str, str | None]:
    if channel not in {"email", "sms", "whatsapp"}:
        raise ValueError("unsupported notification channel")
    return {"channel": channel, "recipient": recipient, "subject": subject, "body": body}
