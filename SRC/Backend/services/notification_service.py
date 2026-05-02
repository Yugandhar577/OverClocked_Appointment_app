"""
Backend documentation for `services/notification_service.py`.

This service module owns business rules and database coordination so route handlers and UI code stay simple.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.db.models import Notification


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def queue_email(
    session: AsyncSession,
    *,
    event_type: str,
    body: str,
    subject: str | None = None,
    recipient_id: UUID | None = None,
    appointment_id: UUID | None = None,
) -> Notification:
    notification = Notification(
        appointment_id=appointment_id,
        recipient_id=recipient_id,
        channel="email",
        event_type=event_type,
        subject=subject,
        body=body,
        status="queued",
    )
    session.add(notification)
    return notification
