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
    from SRC.Backend.services import notification_settings_service, template_service

    organiser = await session.get(User, appointment_type.organiser_id)
    org_id = organiser.organization_id if organiser else None

    notif_settings = await notification_settings_service.get_or_create(session, org_id)

    org = (await session.get(Organization, org_id)) if org_id else None
    context = template_service.build_context(appointment, appointment_type, org, slot)

    target_recipient = recipient_id or appointment.customer_id
    created: list[Notification] = []

    if notif_settings.email_enabled:
        if event_type == "booking_created":
            subject = template_service.render(notif_settings.booking_confirmation_subject, context)
            body = template_service.render(notif_settings.booking_confirmation_body, context)
        elif event_type == "booking_cancelled":
            subject = template_service.render(notif_settings.cancellation_subject, context)
            body = template_service.render(notif_settings.cancellation_body, context)
        elif event_type in ("booking_confirmed", "booking_pending"):
            subject = template_service.render(notif_settings.booking_confirmation_subject, context)
            body = template_service.render(notif_settings.booking_confirmation_body, context)
        elif event_type == "reminder_email":
            subject = template_service.render(notif_settings.reminder_email_subject, context)
            body = template_service.render(notif_settings.reminder_email_body, context)
        else:
            subject = f"Update: {appointment.confirmation_code}"
            body = f"Your booking {appointment.confirmation_code} — {event_type}."

        notif = Notification(
            appointment_id=appointment.id,
            recipient_id=target_recipient,
            channel="email",
            event_type=event_type,
            subject=subject,
            body=body,
            status="queued",
        )
        session.add(notif)
        created.append(notif)

    if notif_settings.sms_enabled and event_type in ("booking_created", "booking_cancelled", "reminder_sms"):
        sms_body = template_service.render(notif_settings.reminder_sms_body, context)
        sms_notif = Notification(
            appointment_id=appointment.id,
            recipient_id=target_recipient,
            channel="sms",
            event_type=event_type,
            body=sms_body,
            status="queued",
        )
        session.add(sms_notif)
        created.append(sms_notif)

    return created
