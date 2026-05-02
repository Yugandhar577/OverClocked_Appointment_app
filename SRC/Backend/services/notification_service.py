from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.db.models import Notification


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
