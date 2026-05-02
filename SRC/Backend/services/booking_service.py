import secrets
from datetime import timedelta
from uuid import UUID

from sqlalchemy import and_, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.config import get_settings
from SRC.Backend.core.errors import (
    CancelWindowClosedError,
    CapacityExceededError,
    IntakeAnswerMissingError,
    NotFoundError,
    NotOwnerError,
    RescheduleWindowClosedError,
    SameSlotRescheduleError,
    SlotUnavailableError,
)
from SRC.Backend.core.time import utc_day_bounds_for_local_date, utcnow
from SRC.Backend.db.models import (
    Appointment,
    AppointmentAnswer,
    AppointmentQuestion,
    AppointmentType,
    AuditLog,
    GeneratedSlot,
    SlotCapacityLog,
    User,
    WaitlistEntry,
)
from SRC.Backend.services import appointment_service
from SRC.Backend.services.notification_service import queue_email

LOCK_SLOT_SQL = """SELECT * FROM generated_slots
  WHERE id = :slot_id AND is_blocked = FALSE AND booked_count < max_capacity
  FOR UPDATE SKIP LOCKED"""


def _confirmation_code() -> str:
    return secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:10].upper()


async def _required_question_ids(session: AsyncSession, appointment_type_id: UUID) -> set[UUID]:
    result = await session.execute(
        select(AppointmentQuestion.id).where(
            AppointmentQuestion.appointment_type_id == appointment_type_id,
            AppointmentQuestion.is_mandatory.is_(True),
        )
    )
    return set(result.scalars().all())


def _answer_text(value) -> str | None:
    if isinstance(value, (dict, list)):
        return None
    return str(value)


async def availability(
    session: AsyncSession,
    *,
    appointment_type_id: UUID,
    resource_id: UUID | None,
    target_date,
    tz_offset_minutes: int,
) -> list[dict]:
    start_utc, end_utc = utc_day_bounds_for_local_date(target_date, tz_offset_minutes)
    stmt = (
        select(GeneratedSlot)
        .where(
            GeneratedSlot.appointment_type_id == appointment_type_id,
            GeneratedSlot.start_datetime >= start_utc,
            GeneratedSlot.start_datetime < end_utc,
            GeneratedSlot.is_blocked.is_(False),
        )
        .order_by(GeneratedSlot.start_datetime.asc(), GeneratedSlot.id.asc())
    )
    if resource_id:
        stmt = stmt.where(GeneratedSlot.resource_id == resource_id)
    rows = (await session.execute(stmt)).scalars().all()
    waitlist_rows = await session.execute(
        select(WaitlistEntry.slot_id)
        .where(WaitlistEntry.slot_id.in_([row.id for row in rows]))
        .where(WaitlistEntry.status.in_(["waiting", "offered"]))
    )
    waitlist_slot_ids = set(waitlist_rows.scalars().all())
    result = []
    for row in rows:
        remaining = row.max_capacity - row.booked_count
        is_reserved = row.id in waitlist_slot_ids
        status = "waitlist" if is_reserved else "full" if remaining <= 0 else "available"
        result.append(
            {
            "slot_id": row.id,
            "start_datetime": row.start_datetime,
            "end_datetime": row.end_datetime,
            "remaining_capacity": remaining,
            "max_capacity": row.max_capacity,
            "resource_id": row.resource_id,
            "status": status,
            "is_waitlist_reserved": is_reserved,
        }
        )
    return result


async def create(session: AsyncSession, payload, actor: User) -> tuple[Appointment, GeneratedSlot, AppointmentType, str]:
    async with session.begin():
        appointment_type = await session.get(AppointmentType, payload.appointment_type_id)
        if not appointment_type:
            raise NotFoundError("appointment_type")

        slot_result = await session.execute(text(LOCK_SLOT_SQL), {"slot_id": payload.slot_id})
        slot_row = slot_result.mappings().first()
        if slot_row is None:
            raise SlotUnavailableError()
        if slot_row["appointment_type_id"] != payload.appointment_type_id:
            raise SlotUnavailableError()
        if payload.resource_id and slot_row["resource_id"] != payload.resource_id:
            raise SlotUnavailableError()
        if slot_row["booked_count"] + payload.people_count > slot_row["max_capacity"]:
            raise CapacityExceededError()

        required_ids = await _required_question_ids(session, payload.appointment_type_id)
        answered_ids = {answer.question_id for answer in payload.answers}
        missing = required_ids - answered_ids
        if missing:
            raise IntakeAnswerMissingError(next(iter(missing)))

        status = "pending" if appointment_type.requires_confirmation or appointment_type.is_paid else "confirmed"
        customer = payload.customer_info
        appointment = Appointment(
            appointment_type_id=payload.appointment_type_id,
            slot_id=payload.slot_id,
            customer_id=actor.id,
            resource_id=slot_row["resource_id"],
            status=status,
            people_count=payload.people_count,
            confirmation_code=_confirmation_code(),
            customer_full_name=customer.full_name if customer else actor.full_name,
            customer_email=customer.email if customer else actor.email,
            customer_phone=customer.phone if customer else actor.phone,
            confirmed_at=utcnow() if status == "confirmed" else None,
        )
        session.add(appointment)
        await session.flush()

        for answer in payload.answers:
            value = answer.value
            session.add(
                AppointmentAnswer(
                    appointment_id=appointment.id,
                    question_id=answer.question_id,
                    answer_text=_answer_text(value),
                    answer_json=value if isinstance(value, (dict, list)) else None,
                )
            )

        await session.execute(
            update(GeneratedSlot)
            .where(GeneratedSlot.id == payload.slot_id)
            .values(booked_count=GeneratedSlot.booked_count + payload.people_count)
        )
        session.add(
            SlotCapacityLog(
                slot_id=payload.slot_id,
                appointment_id=appointment.id,
                delta=payload.people_count,
                new_count=slot_row["booked_count"] + payload.people_count,
            )
        )
        session.add(
            AuditLog(
                actor_id=actor.id,
                action="CREATE_BOOKING",
                entity_type="appointments",
                entity_id=appointment.id,
                new_value={"slot_id": str(payload.slot_id), "people_count": payload.people_count, "status": status},
            )
        )
        queue_email(
            session,
            event_type="booking_created",
            appointment_id=appointment.id,
            recipient_id=actor.id,
            subject="Booking created",
            body=f"Booking {appointment.confirmation_code} is {status}.",
        )

    slot = await session.get(GeneratedSlot, payload.slot_id)
    organiser = await session.get(User, appointment_type.organiser_id)
    organiser_name = organiser.full_name if organiser else "Organiser"
    await session.commit()
    return appointment, slot, appointment_type, organiser_name


async def get_booking_detail(session: AsyncSession, booking_id: UUID, actor: User | None = None) -> dict:
    stmt = (
        select(Appointment, GeneratedSlot, AppointmentType)
        .join(GeneratedSlot, GeneratedSlot.id == Appointment.slot_id)
        .join(AppointmentType, AppointmentType.id == Appointment.appointment_type_id)
        .where(Appointment.id == booking_id)
    )
    row = (await session.execute(stmt)).first()
    if not row:
        raise NotFoundError("appointment")
    appointment, slot, appointment_type = row
    if actor and actor.id not in {appointment.customer_id, appointment_type.organiser_id} and "admin" not in getattr(actor, "roles_snapshot", []):
        raise NotOwnerError()
    return {
        **appointment.__dict__,
        "slot_start": slot.start_datetime,
        "slot_end": slot.end_datetime,
        "appointment_title": appointment_type.title,
        "venue": appointment_type.venue,
    }


async def list_for_customer(session: AsyncSession, actor: User, status: str | None, page: int, page_size: int) -> tuple[list[dict], int]:
    now = utcnow()
    stmt = (
        select(Appointment, GeneratedSlot, AppointmentType)
        .join(GeneratedSlot, GeneratedSlot.id == Appointment.slot_id)
        .join(AppointmentType, AppointmentType.id == Appointment.appointment_type_id)
        .where(Appointment.customer_id == actor.id)
        .order_by(GeneratedSlot.start_datetime.desc(), Appointment.id.desc())
    )
    count_stmt = select(func.count()).select_from(Appointment).where(Appointment.customer_id == actor.id)
    if status == "upcoming":
        stmt = stmt.where(GeneratedSlot.start_datetime >= now, Appointment.status.in_(["pending", "confirmed"]))
        count_stmt = count_stmt.join(GeneratedSlot, GeneratedSlot.id == Appointment.slot_id).where(
            GeneratedSlot.start_datetime >= now,
            Appointment.status.in_(["pending", "confirmed"]),
        )
    elif status == "past":
        stmt = stmt.where((GeneratedSlot.start_datetime < now) | Appointment.status.in_(["cancelled", "completed", "rescheduled"]))
        count_stmt = count_stmt.join(GeneratedSlot, GeneratedSlot.id == Appointment.slot_id).where(
            (GeneratedSlot.start_datetime < now) | Appointment.status.in_(["cancelled", "completed", "rescheduled"])
        )
    rows = (await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))).all()
    total = await session.scalar(count_stmt)
    return [
        {
            **appointment.__dict__,
            "slot_start": slot.start_datetime,
            "slot_end": slot.end_datetime,
            "appointment_title": appointment_type.title,
            "venue": appointment_type.venue,
        }
        for appointment, slot, appointment_type in rows
    ], total or 0


async def list_for_organiser(
    session: AsyncSession,
    actor: User,
    appointment_type_id: UUID | None,
    status: str | None,
    date_from,
    date_to,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    stmt = (
        select(Appointment, GeneratedSlot, AppointmentType)
        .join(GeneratedSlot, GeneratedSlot.id == Appointment.slot_id)
        .join(AppointmentType, AppointmentType.id == Appointment.appointment_type_id)
        .where(AppointmentType.organiser_id == actor.id)
        .order_by(Appointment.created_at.desc(), Appointment.id.desc())
    )
    count_stmt = (
        select(func.count())
        .select_from(Appointment)
        .join(AppointmentType, AppointmentType.id == Appointment.appointment_type_id)
        .where(AppointmentType.organiser_id == actor.id)
    )
    if appointment_type_id:
        stmt = stmt.where(Appointment.appointment_type_id == appointment_type_id)
        count_stmt = count_stmt.where(Appointment.appointment_type_id == appointment_type_id)
    if status:
        stmt = stmt.where(Appointment.status == status)
        count_stmt = count_stmt.where(Appointment.status == status)
    if date_from:
        stmt = stmt.where(GeneratedSlot.start_datetime >= date_from)
    if date_to:
        stmt = stmt.where(GeneratedSlot.start_datetime <= date_to)
    rows = (await session.execute(stmt.offset((page - 1) * page_size).limit(page_size))).all()
    total = await session.scalar(count_stmt)
    return [
        {
            **appointment.__dict__,
            "slot_start": slot.start_datetime,
            "slot_end": slot.end_datetime,
            "appointment_title": appointment_type.title,
            "venue": appointment_type.venue,
        }
        for appointment, slot, appointment_type in rows
    ], total or 0


def _window_closed(slot_start, minutes: int | None) -> bool:
    if minutes is None:
        return False
    return utcnow() + timedelta(minutes=minutes) > slot_start


async def cancel(session: AsyncSession, booking_id: UUID, actor: User, reason: str | None, bypass_window: bool = False) -> Appointment:
    async with session.begin():
        row = (
            await session.execute(
                select(Appointment, GeneratedSlot, AppointmentType)
                .join(GeneratedSlot, GeneratedSlot.id == Appointment.slot_id)
                .join(AppointmentType, AppointmentType.id == Appointment.appointment_type_id)
                .where(Appointment.id == booking_id)
            )
        ).first()
        if not row:
            raise NotFoundError("appointment")
        appointment, slot, appointment_type = row
        if actor.id not in {appointment.customer_id, appointment_type.organiser_id} and "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
        if actor.id == appointment.customer_id and not bypass_window and _window_closed(slot.start_datetime, appointment_type.cancel_before_minutes):
            raise CancelWindowClosedError()

        await session.execute(text("SELECT * FROM generated_slots WHERE id = :slot_id FOR UPDATE"), {"slot_id": slot.id})
        updated = await appointment_service.transition(session, appointment.id, "cancelled", actor, reason)
        new_count = max(slot.booked_count - appointment.people_count, 0)
        slot.booked_count = new_count
        session.add(SlotCapacityLog(slot_id=slot.id, appointment_id=appointment.id, delta=-appointment.people_count, new_count=new_count))
        queue_email(
            session,
            event_type="booking_cancelled",
            appointment_id=appointment.id,
            recipient_id=appointment.customer_id,
            subject="Booking cancelled",
            body=f"Booking {appointment.confirmation_code} was cancelled.",
        )
    return updated


async def confirm(session: AsyncSession, booking_id: UUID, actor: User) -> Appointment:
    async with session.begin():
        row = (
            await session.execute(
                select(Appointment, AppointmentType)
                .join(AppointmentType, AppointmentType.id == Appointment.appointment_type_id)
                .where(Appointment.id == booking_id)
            )
        ).first()
        if not row:
            raise NotFoundError("appointment")
        appointment, appointment_type = row
        if appointment_type.organiser_id != actor.id and "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
        updated = await appointment_service.transition(session, appointment.id, "confirmed", actor)
        queue_email(
            session,
            event_type="booking_confirmed",
            appointment_id=appointment.id,
            recipient_id=appointment.customer_id,
            subject="Booking confirmed",
            body=f"Booking {appointment.confirmation_code} is confirmed.",
        )
    return updated


async def reschedule(session: AsyncSession, booking_id: UUID, new_slot_id: UUID, actor: User) -> tuple[Appointment, Appointment]:
    async with session.begin():
        row = (
            await session.execute(
                select(Appointment, GeneratedSlot, AppointmentType)
                .join(GeneratedSlot, GeneratedSlot.id == Appointment.slot_id)
                .join(AppointmentType, AppointmentType.id == Appointment.appointment_type_id)
                .where(Appointment.id == booking_id)
            )
        ).first()
        if not row:
            raise NotFoundError("appointment")
        old, old_slot, appointment_type = row
        if old.slot_id == new_slot_id:
            raise SameSlotRescheduleError()
        if actor.id not in {old.customer_id, appointment_type.organiser_id} and "admin" not in getattr(actor, "roles_snapshot", []):
            raise NotOwnerError()
        if actor.id == old.customer_id and _window_closed(old_slot.start_datetime, appointment_type.reschedule_before_minutes):
            raise RescheduleWindowClosedError()

        for slot_id in sorted([old.slot_id, new_slot_id]):
            if slot_id == new_slot_id:
                result = await session.execute(text(LOCK_SLOT_SQL), {"slot_id": slot_id})
                if result.mappings().first() is None:
                    raise SlotUnavailableError()
            else:
                await session.execute(text("SELECT * FROM generated_slots WHERE id = :slot_id FOR UPDATE"), {"slot_id": slot_id})

        new_slot = await session.get(GeneratedSlot, new_slot_id)
        if not new_slot or new_slot.appointment_type_id != old.appointment_type_id:
            raise SlotUnavailableError()
        if new_slot.booked_count + old.people_count > new_slot.max_capacity:
            raise CapacityExceededError()

        carry_status = old.status
        await appointment_service.transition(session, old.id, "rescheduled", actor)
        old_slot.booked_count = max(old_slot.booked_count - old.people_count, 0)
        new_slot.booked_count = new_slot.booked_count + old.people_count

        new_appointment = Appointment(
            appointment_type_id=old.appointment_type_id,
            slot_id=new_slot.id,
            customer_id=old.customer_id,
            resource_id=new_slot.resource_id,
            status="confirmed" if carry_status == "confirmed" else "pending",
            people_count=old.people_count,
            confirmation_code=_confirmation_code(),
            customer_full_name=old.customer_full_name,
            customer_email=old.customer_email,
            customer_phone=old.customer_phone,
            confirmed_at=utcnow() if carry_status == "confirmed" else None,
            rescheduled_from=old.id,
        )
        session.add(new_appointment)
        await session.flush()

        answers = (
            await session.execute(select(AppointmentAnswer).where(AppointmentAnswer.appointment_id == old.id))
        ).scalars().all()
        for answer in answers:
            session.add(
                AppointmentAnswer(
                    appointment_id=new_appointment.id,
                    question_id=answer.question_id,
                    answer_text=answer.answer_text,
                    answer_json=answer.answer_json,
                )
            )
        session.add(SlotCapacityLog(slot_id=old_slot.id, appointment_id=old.id, delta=-old.people_count, new_count=old_slot.booked_count))
        session.add(SlotCapacityLog(slot_id=new_slot.id, appointment_id=new_appointment.id, delta=old.people_count, new_count=new_slot.booked_count))
    return old, new_appointment
