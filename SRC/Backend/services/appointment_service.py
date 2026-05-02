"""
Backend documentation for `services/appointment_service.py`.

This service module owns business rules and database coordination so route handlers and UI code stay simple.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

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


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
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


# Explanation:
# `transition` validates an appointment status change against the allowed
# transition map, applies timestamps for confirmed/cancelled states, and
# records an audit log entry for traceability.
#
# Alternative (commented): encode transitions as state-machine methods on
# the model or use a workflow library for richer lifecycle management.
#
# def transition_state_machine(appointment, target_status, actor, reason=None):
#     # consult state machine and apply transition
#     pass
