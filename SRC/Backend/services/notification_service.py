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


async def queue_notification(
    session: AsyncSession,
    *,
    event_type: str,
    appointment,
    appointment_type,
    slot=None,
    recipient_id: UUID | None = None,
) -> list[Notification]:
    from SRC.Backend.db.models import Organization, User
    from SRC.Backend.services import mail_template_service, template_service

    organiser = await session.get(User, appointment_type.organiser_id)
    org_id = organiser.organization_id if organiser else None
    org = (await session.get(Organization, org_id)) if org_id else None
    context = template_service.build_context(appointment, appointment_type, org, slot)

    target_recipient = recipient_id or appointment.customer_id
    created: list[Notification] = []
    template_type, template_attr, channel = _template_for_event(event_type)

    if not template_type:
        notification = Notification(
            appointment_id=appointment.id,
            recipient_id=target_recipient,
            channel="email",
            event_type=event_type,
            subject=f"Update: {appointment.confirmation_code}",
            body=f"Your booking {appointment.confirmation_code} - {event_type}.",
            status="queued",
        )
        session.add(notification)
        return [notification]

    template_id = getattr(appointment_type, template_attr, None) if template_attr else None
    template = await mail_template_service.get(session, template_id, org_id) if template_id else None
    if template is None:
        template = await mail_template_service.get_default(session, template_type)
    if template is None:
        return created

    subject = template_service.render(template.subject or "", context) if template.subject else None
    body = template_service.render(template.body_html, context)
    notification = Notification(
        appointment_id=appointment.id,
        recipient_id=target_recipient,
        channel=channel,
        event_type=event_type,
        subject=subject if channel == "email" else None,
        body=body,
        status="queued",
    )
    session.add(notification)
    created.append(notification)
    return created


def _template_for_event(event_type: str) -> tuple[str | None, str | None, str]:
    if event_type in {"booking_created", "booking_confirmed", "booking_pending"}:
        return "booking_confirmation", "booking_email_template_id", "email"
    if event_type == "booking_cancelled":
        return "cancellation", "cancellation_email_template_id", "email"
    if event_type.startswith("reminder_email"):
        return "reminder_email", "reminder_email_template_id", "email"
    if event_type.startswith("reminder_sms"):
        return "reminder_sms", "reminder_sms_template_id", "sms"
    return None, None, "email"
