from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.errors import AppError, NotFoundError, NotOwnerError
from SRC.Backend.db.models import AppointmentType, AppointmentTypeReminder, User


async def list_for_type(session: AsyncSession, appointment_type_id: UUID) -> list[AppointmentTypeReminder]:
    rows = (
        await session.execute(
            select(AppointmentTypeReminder)
            .where(AppointmentTypeReminder.appointment_type_id == appointment_type_id)
            .order_by(AppointmentTypeReminder.channel.asc(), AppointmentTypeReminder.hours_before.asc())
        )
    ).scalars().all()
    return list(rows)


async def replace(session: AsyncSession, appointment_type_id: UUID, reminders: list, actor: User) -> list[AppointmentTypeReminder]:
    pairs = [(row.channel, row.hours_before) for row in reminders]
    if len(set(pairs)) != len(pairs):
        raise AppError({"detail": "duplicate_reminder"})
    for channel in ("email", "sms"):
        if sum(1 for pair in pairs if pair[0] == channel) > 5:
            raise AppError({"detail": "too_many_reminders", "channel": channel})

    async with session.begin():
        appointment_type = await session.get(AppointmentType, appointment_type_id)
        if not appointment_type:
            raise NotFoundError("appointment_type")
        if appointment_type.organiser_id != actor.id and "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
        await session.execute(delete(AppointmentTypeReminder).where(AppointmentTypeReminder.appointment_type_id == appointment_type_id))
        created = []
        for row in reminders:
            reminder = AppointmentTypeReminder(
                appointment_type_id=appointment_type_id,
                channel=row.channel,
                hours_before=row.hours_before,
            )
            session.add(reminder)
            created.append(reminder)
        await session.flush()
    return created
