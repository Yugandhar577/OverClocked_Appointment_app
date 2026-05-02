import logging
from datetime import timedelta

from sqlalchemy import select

from SRC.Backend.core.time import utcnow
from SRC.Backend.db.models import Appointment, AppointmentType, AppointmentTypeReminder, GeneratedSlot, Notification
from SRC.Backend.db.session import async_session_factory
from SRC.Backend.services.notification_service import queue_notification

logger = logging.getLogger(__name__)


async def enqueue_due_reminders() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            now = utcnow()
            window_end = now + timedelta(hours=720)
            rows = (
                await session.execute(
                    select(Appointment, AppointmentType, GeneratedSlot, AppointmentTypeReminder)
                    .join(AppointmentType, AppointmentType.id == Appointment.appointment_type_id)
                    .join(GeneratedSlot, GeneratedSlot.id == Appointment.slot_id)
                    .join(AppointmentTypeReminder, AppointmentTypeReminder.appointment_type_id == AppointmentType.id)
                    .where(
                        Appointment.status == "confirmed",
                        GeneratedSlot.start_datetime > now,
                        GeneratedSlot.start_datetime <= window_end,
                    )
                )
            ).all()

            queued = 0
            for appointment, appointment_type, slot, reminder in rows:
                if now < slot.start_datetime - timedelta(hours=reminder.hours_before):
                    continue
                event_type = f"reminder_{reminder.channel}_{reminder.hours_before}"
                existing = await session.scalar(
                    select(Notification).where(
                        Notification.appointment_id == appointment.id,
                        Notification.event_type == event_type,
                        Notification.channel == reminder.channel,
                        Notification.status.in_(["queued", "sent"]),
                    )
                )
                if existing:
                    continue
                created = await queue_notification(
                    session,
                    event_type=event_type,
                    appointment=appointment,
                    appointment_type=appointment_type,
                    slot=slot,
                    recipient_id=appointment.customer_id,
                )
                queued += len(created)

            if queued:
                logger.info("reminder_dispatcher: queued %d notifications", queued)
