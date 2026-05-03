"""
Backend documentation for `services/booking_service.py`.

This service module owns business rules and database coordination so route handlers and UI code stay simple.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

import re
import secrets
from datetime import timedelta
from uuid import UUID

from sqlalchemy import and_, func, select, text, update

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PHONE_RE = re.compile(r"^[\d\s+\-()\[\]]{7,20}$")
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.config import get_settings
from SRC.Backend.core.booking_access import can_view_booking, ids_equal, is_admin
from SRC.Backend.core.errors import (
    BookingInProgressError,
    CancelWindowClosedError,
    CapacityExceededError,
    IntakeAnswerInvalidError,
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


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def _confirmation_code() -> str:
    return secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:10].upper()


# Explanation:
# `_confirmation_code` generates a short human-friendly confirmation code
# derived from a URL-safe token. It's designed to be compact and usable in
# communications.
#
# Alternative (commented): use an incremental sequence per-organiser or
# a short hash of appointment id for reproducible codes.
#
# def _confirmation_code_seq():
#     # allocate from a sequence and format
#     pass


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def _required_question_ids(session: AsyncSession, appointment_type_id: UUID) -> set[UUID]:
    result = await session.execute(
        select(AppointmentQuestion.id).where(
            AppointmentQuestion.appointment_type_id == appointment_type_id,
            AppointmentQuestion.is_mandatory.is_(True),
        )
    )
    return set(result.scalars().all())


# Explanation:
# `_required_question_ids` returns mandatory question ids for an
# appointment type to validate intake answers on booking creation.
#
# Alternative (commented): fetch and cache question definitions per
# appointment type to reduce repeated queries.
#
# async def _required_question_ids_cached(...):
#     pass


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def _answer_text(value) -> str | None:
    if isinstance(value, (dict, list)):
        return None
    return str(value)


def _validate_answer_value(question: AppointmentQuestion, value) -> str | None:
    """Return an error message if the answer value is invalid for the question's answer_type, else None."""
    text_value = str(value).strip() if not isinstance(value, (dict, list)) else ""
    if not text_value:
        return None
    if question.answer_type == "email" and not _EMAIL_RE.match(text_value):
        return "Enter a valid email address"
    if question.answer_type == "phone" and not _PHONE_RE.match(text_value):
        return "Enter a valid phone number"
    return None


# Explanation:
# `_answer_text` converts scalar answers to text while preserving
# structured answers in `answer_json`. This avoids double-serializing
# JSON for structured inputs.
#
# Alternative (commented): always store JSON and derive text when
# needed in views, simplifying storage format at the cost of queries.
#
# def _answer_text_always_json(value):
#     return json.dumps(value)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
async def _raise_slot_lock_or_unavailable(session: AsyncSession, slot_id: UUID) -> None:
    slot = await session.get(GeneratedSlot, slot_id)
    if slot and not slot.is_blocked and slot.booked_count < slot.max_capacity:
        raise BookingInProgressError()
    raise SlotUnavailableError()


# Explanation:
# `_raise_slot_lock_or_unavailable` distinguishes two cases that both make
# the `FOR UPDATE SKIP LOCKED` query return no row:
# 1. the slot is genuinely full/blocked/missing, or
# 2. another transaction currently owns the lock and is booking it.
# The second case returns a retryable domain error so the frontend can
# show a better message and refresh availability instead of implying the
# slot is permanently gone.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
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


# Explanation:
# `availability` lists generated slots in a date range and returns their
# remaining capacity and waitlist status. It is careful to compute the
# remaining capacity using `booked_count` and `max_capacity`.
#
# Alternative (commented): include live reservations by checking a
# temporary reservation table for pending holds (useful for cart flows).
#
# async def availability_with_holds(...):
#     # combine generated slots with temporary holds
#     pass


# Backend note: Creates a new domain record after validation and keeps side effects scoped to this workflow.
async def create(session: AsyncSession, payload, actor: User) -> tuple[Appointment, GeneratedSlot, AppointmentType, str]:
    async with session.begin():
        appointment_type = await session.get(AppointmentType, payload.appointment_type_id)
        if not appointment_type:
            raise NotFoundError("appointment_type")

        slot_result = await session.execute(text(LOCK_SLOT_SQL), {"slot_id": payload.slot_id})
        slot_row = slot_result.mappings().first()
        if slot_row is None:
            await _raise_slot_lock_or_unavailable(session, payload.slot_id)
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

        # Validate answer values against their question's answer_type (email format, phone format, etc.)
        answer_by_question_id = {answer.question_id: answer for answer in payload.answers}
        if answer_by_question_id:
            questions_result = await session.execute(
                select(AppointmentQuestion).where(
                    AppointmentQuestion.appointment_type_id == payload.appointment_type_id,
                    AppointmentQuestion.id.in_(answer_by_question_id.keys()),
                )
            )
            for question in questions_result.scalars():
                answer = answer_by_question_id[question.id]
                err = _validate_answer_value(question, answer.value)
                if err:
                    raise IntakeAnswerInvalidError(question.id, err)

        status = "pending" if appointment_type.requires_confirmation or appointment_type.is_paid else "confirmed"
        customer = payload.customer_info
        # If any email-type question was answered, use that as customer_email.
        # This connects the "Email Address" question directly to notification delivery.
        email_from_question: str | None = None
        for q_id, ans in answer_by_question_id.items():
            q = await session.get(AppointmentQuestion, q_id)
            if q and q.answer_type == "email" and isinstance(ans.value, str) and ans.value.strip():
                email_from_question = ans.value.strip()
                break
        # Priority: email from question > customer_info email > actor's account email
        customer_email = email_from_question or (customer.email if customer else None) or actor.email
        appointment = Appointment(
            appointment_type_id=payload.appointment_type_id,
            slot_id=payload.slot_id,
            customer_id=actor.id,
            resource_id=slot_row["resource_id"],
            status=status,
            people_count=payload.people_count,
            confirmation_code=_confirmation_code(),
            customer_full_name=customer.full_name if customer else actor.full_name,
            customer_email=customer_email,
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


# Explanation:
# `create` performs an atomic booking workflow: it locks the slot row
# (SKIP LOCKED), validates capacity and answers, creates the appointment
# and answers, updates slot counts, logs the change, and queues an email.
#
# Alternative (commented): use a queuing approach where booking requests
# are enqueued and processed by a single worker to avoid distributed
# locking complexity at scale.
#
# async def create_via_queue(session, payload, actor):
#     # place booking request in queue and return pending result
#     pass


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
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
    if actor and not can_view_booking(actor, appointment, appointment_type):
        raise NotOwnerError()
    return {
        **appointment.__dict__,
        "slot_start": slot.start_datetime,
        "slot_end": slot.end_datetime,
        "appointment_title": appointment_type.title,
        "venue": appointment_type.venue,
    }


# Explanation:
# `get_booking_detail` composes appointment data and related slot/type
# info into a dictionary for API responses; it enforces ownership checks
# when an `actor` is provided.
#
# Alternative (commented): return a strongly-typed Pydantic model instead
# of a raw dict to enforce contracts at the service boundary.
#
# def get_booking_detail_model(...):
#     return BookingDetailModel(...)


# Backend note: Collects a filtered collection for API or service consumers while preserving existing response contracts.
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


# Explanation:
# `list_for_customer` returns a paginated list of bookings for the
# customer, supporting simple `upcoming`/`past` filtering.
#
# Alternative (commented): use a dedicated read replica or reporting
# database for heavy listing queries to offload primary DB.
#
# async def list_for_customer_replica(...):
#     pass


# Backend note: Collects a filtered collection for API or service consumers while preserving existing response contracts.
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


# Explanation:
# `list_for_organiser` returns bookings for an organiser with filtering
# and pagination similar to the customer listing.
#
# Alternative (commented): return pre-aggregated statistics for dashboards
# and allow drill-down queries for details.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
def _window_closed(slot_start, minutes: int | None) -> bool:
    if minutes is None:
        return False
    return utcnow() + timedelta(minutes=minutes) > slot_start


# Explanation:
# `_window_closed` checks whether an action (cancel/reschedule) is
# allowed based on `minutes` before the slot. It returns False when no
# window is configured.
#
# Alternative (commented): compute windows per-user or per-role for more
# flexible cancellation policies.


# Backend note: Moves a booking-like record through cancellation handling without bypassing business rules.
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
        if not can_view_booking(actor, appointment, appointment_type):
            raise NotOwnerError()
        if ids_equal(actor.id, appointment.customer_id) and not bypass_window and _window_closed(slot.start_datetime, appointment_type.cancel_before_minutes):
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


# Explanation:
# `cancel` runs inside a transaction, validates permissions and windows,
# updates slot counts and appointment status via `appointment_service`,
# logs the change and queues a cancellation email.
#
# Alternative (commented): implement soft-cancel for manual review or
# schedule a background job to finalize refunds and external actions.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
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
        if not ids_equal(appointment_type.organiser_id, actor.id) and not is_admin(actor):
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


# Explanation:
# `confirm` validates organiser rights, transitions appointment state
# using `appointment_service`, and queues a confirmation email.
#
# Alternative (commented): allow batch confirmations and rate-limit
# confirmation emails to avoid spam.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
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
        if not can_view_booking(actor, old, appointment_type):
            raise NotOwnerError()
        if ids_equal(actor.id, old.customer_id) and _window_closed(old_slot.start_datetime, appointment_type.reschedule_before_minutes):
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


# Explanation:
# `reschedule` performs checks on windows and availability, locks old
# and new slots appropriately, creates a new appointment copying answers
# and updates slot counts atomically.
#
# Alternative (commented): perform a tentative hold on the new slot and
# require confirmation within a time window to prevent instant double-booking.
