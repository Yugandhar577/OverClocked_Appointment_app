from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.errors import InvalidTransitionError, NotFoundError
from SRC.Backend.core.time import utcnow
from SRC.Backend.db.models import Appointment, AuditLog, User

ALLOWED_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"completed", "cancelled", "rescheduled", "no_show"},
    "cancelled": set(),
    "completed": set(),
    "rescheduled": set(),
    "no_show": set(),
}


async def transition(
    session: AsyncSession,
    appointment_id: UUID,
    target_status: str,
    actor: User | None,
    reason: str | None = None,
) -> Appointment:
    appointment = await session.get(Appointment, appointment_id)
    if not appointment:
        raise NotFoundError("appointment")

    current = appointment.status
    if target_status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(current, target_status)

    appointment.status = target_status
    if target_status == "confirmed":
        appointment.confirmed_at = utcnow()
    if target_status == "cancelled":
        appointment.cancelled_at = utcnow()
        appointment.cancellation_reason = reason

    session.add(
        AuditLog(
            actor_id=actor.id if actor else None,
            action="STATUS_TRANSITION",
            entity_type="appointments",
            entity_id=appointment.id,
            old_value={"status": current},
            new_value={"status": target_status, "reason": reason},
        )
    )
    return appointment
