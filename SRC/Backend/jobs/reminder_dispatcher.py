import logging
from datetime import timedelta

from sqlalchemy import select

from SRC.Backend.core.time import utcnow
from SRC.Backend.db.models import Appointment, AppointmentType, GeneratedSlot, Notification, Organization, User
from SRC.Backend.db.session import async_session_factory
from SRC.Backend.services import notification_settings_service, template_service

logger = logging.getLogger(__name__)


async def enqueue_due_reminders() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            now = utcnow()
            window_end = now + timedelta(hours=48)

            rows = (
                await session.execute(
                    select(Appointment, AppointmentType, GeneratedSlot)
                    .join(AppointmentType, AppointmentType.id == Appointment.appointment_type_id)
                    .join(GeneratedSlot, GeneratedSlot.id == Appointment.slot_id)
                    .where(
                        Appointment.status == "confirmed",
                        GeneratedSlot.start_datetime > now,
                        GeneratedSlot.start_datetime <= window_end,
                    )
                )
            ).all()

            queued = 0
            for appointment, appointment_type, slot in rows:
                organiser = await session.get(User, appointment_type.organiser_id)
                org_id = organiser.organization_id if organiser else None
                notif_settings = await notification_settings_service.get_or_create(session, org_id)
                org = (await session.get(Organization, org_id)) if org_id else None
                context = template_service.build_context(appointment, appointment_type, org, slot)

                if notif_settings.email_enabled:
                    email_hours = notification_settings_service.resolve_reminder_hours(
                        notif_settings, appointment_type, "email"
                    )
                    if email_hours is not None and now >= slot.start_datetime - timedelta(hours=email_hours):
                        already_sent = await session.scalar(
                            select(Notification).where(
                                Notification.appointment_id == appointment.id,
                                Notification.event_type == "reminder_email",
                                Notification.channel == "email",
                                Notification.status.in_(["queued", "sent"]),
                            )
                        )
                        if not already_sent:
                            subject = template_service.render(notif_settings.reminder_email_subject, context)
                            body = template_service.render(notif_settings.reminder_email_body, context)
                            session.add(Notification(
                                appointment_id=appointment.id,
                                recipient_id=appointment.customer_id,
                                channel="email",
                                event_type="reminder_email",
                                subject=subject,
                                body=body,
                                status="queued",
                            ))
                            queued += 1

                if notif_settings.sms_enabled:
                    sms_hours = notification_settings_service.resolve_reminder_hours(
                        notif_settings, appointment_type, "sms"
                    )
                    if sms_hours is not None and now >= slot.start_datetime - timedelta(hours=sms_hours):
                        already_sent = await session.scalar(
                            select(Notification).where(
                                Notification.appointment_id == appointment.id,
                                Notification.event_type == "reminder_sms",
                                Notification.channel == "sms",
                                Notification.status.in_(["queued", "sent"]),
                            )
                        )
                        if not already_sent:
                            sms_body = template_service.render(notif_settings.reminder_sms_body, context)
                            session.add(Notification(
                                appointment_id=appointment.id,
                                recipient_id=appointment.customer_id,
                                channel="sms",
                                event_type="reminder_sms",
                                body=sms_body,
                                status="queued",
                            ))
                            queued += 1

            if queued:
                logger.info("reminder_dispatcher: queued %d notifications", queued)
