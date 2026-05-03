"""
Backend documentation for `routes/bookings.py`.

This route module keeps HTTP concerns thin: validate inputs, call service-layer logic, and return typed API responses.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.deps import get_current_user, require_role
from SRC.Backend.db.models import User
from SRC.Backend.db.session import get_db
from SRC.Backend.schemas.bookings import (
    AvailabilitySlot,
    BookingCreate,
    BookingCreateResponse,
    BookingOut,
    CancelRequest,
    RescheduleRequest,
    RescheduleResponse,
)
from SRC.Backend.schemas.common import Paginated
from SRC.Backend.services import booking_service
from SRC.Backend.services.email_delivery import deliver_queued_notifications_for_appointment

router = APIRouter(tags=["bookings"])


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/availability", response_model=list[AvailabilitySlot])
async def availability(
    appointment_type_id: UUID,
    date: date,
    resource_id: UUID | None = None,
    tz_offset_minutes: int = 0,
    session: AsyncSession = Depends(get_db),
):
    return await booking_service.availability(
        session,
        appointment_type_id=appointment_type_id,
        resource_id=resource_id,
        target_date=date,
        tz_offset_minutes=tz_offset_minutes,
    )


# Explanation:
# `availability` delegates to `booking_service.availability` to compute
# available slots for a given appointment type, date and optional resource.
#
# Alternative (commented): implement a caching layer to avoid repeated
# expensive slot-generation calls for frequently requested dates.
#
# @router.get("/availability")
# async def availability_cached(...):
#     return await cache.get_or_set(key, lambda: booking_service.availability(...))


# Backend note: Creates a new domain record after validation and keeps side effects scoped to this workflow.
@router.post("/bookings", response_model=BookingCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("customer", "admin")),
    session: AsyncSession = Depends(get_db),
):
    appointment, slot, appointment_type, organiser_name = await booking_service.create(session, payload, current_user)
    background_tasks.add_task(deliver_queued_notifications_for_appointment, appointment.id, "booking_created")
    return BookingCreateResponse(
        booking_id=appointment.id,
        status=appointment.status,
        confirmation_code=appointment.confirmation_code,
        slot_start=slot.start_datetime,
        slot_end=slot.end_datetime,
        venue=appointment_type.venue,
        organiser_name=organiser_name,
        payment_required=appointment_type.is_paid,
        payment_url=f"/booking/{appointment.id}/pay" if appointment_type.is_paid else None,
    )


# Explanation:
# `create_booking` is a thin controller that delegates booking creation to
# `booking_service.create` and returns a structured response including the
# booking id, status, and payment URL when required.
#
# Alternative (commented): accept an idempotency key header and persist
# it to avoid duplicate bookings on retry.
#
# @router.post("/bookings")
# async def create_booking_idempotent(..., idempotency_key: str = Header(None)):
#     # lookup existing booking by idempotency_key then create if absent
#     pass


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
@router.get("/bookings/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await booking_service.get_booking_detail(session, booking_id, current_user)


# Explanation:
# `get_booking` returns booking details while enforcing access via
# `get_current_user`. Authorization logic is handled in the service layer.
#
# Alternative (commented): allow organisers to use a special query param
# to include internal fields for admin views.
#
# @router.get("/bookings/{booking_id}")
# async def get_booking_admin(..., include_internal: bool = False):
#     return await booking_service.get_booking_detail(..., include_internal)


# Backend note: Moves a booking-like record through cancellation handling without bypassing business rules.
@router.patch("/bookings/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(
    booking_id: UUID,
    background_tasks: BackgroundTasks,
    payload: CancelRequest | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    appointment = await booking_service.cancel(session, booking_id, current_user, payload.reason if payload else None)
    background_tasks.add_task(deliver_queued_notifications_for_appointment, appointment.id, "booking_cancelled")
    return await booking_service.get_booking_detail(session, appointment.id, current_user)


# Explanation:
# `cancel_booking` invokes the service-level cancel flow which enforces
# windows, notification and refund logic; it then returns the updated
# booking details.
#
# Alternative (commented): provide a `soft_cancel` endpoint that marks
# a booking as pending cancellation for manual review.
#
# @router.patch("/bookings/{booking_id}/cancel")
# async def cancel_booking_soft(...):
#     return await booking_service.soft_cancel(...)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.patch("/bookings/{booking_id}/reschedule", response_model=RescheduleResponse)
async def reschedule_booking(
    booking_id: UUID,
    payload: RescheduleRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    old, new = await booking_service.reschedule(session, booking_id, payload.new_slot_id, current_user)
    return RescheduleResponse(old_id=old.id, new_id=new.id)


# Explanation:
# `reschedule_booking` calls `booking_service.reschedule` to perform the
# atomic move from old slot to new slot, handling capacity and rules.
#
# Alternative (commented): provide a `propose_reschedule` flow that
# creates a tentative booking pending organiser confirmation.
#
# @router.post("/bookings/{booking_id}/reschedule/propose")
# async def propose_reschedule(...):
#     return await booking_service.propose_reschedule(...)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.patch("/bookings/{booking_id}/confirm", response_model=BookingOut)
async def confirm_booking(
    booking_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    appointment = await booking_service.confirm(session, booking_id, current_user)
    background_tasks.add_task(deliver_queued_notifications_for_appointment, appointment.id, "booking_confirmed")
    return await booking_service.get_booking_detail(session, appointment.id, current_user)


# Explanation:
# `confirm_booking` is used by organisers to confirm bookings that require
# explicit confirmation; the service will validate rights and update state.
#
# Alternative (commented): implement bulk confirmation for batch workflows.
#
# @router.patch("/bookings/confirm-bulk")
# async def confirm_bulk(...):
#     return await booking_service.confirm_bulk(...)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/me/appointments", response_model=Paginated)
async def my_appointments(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    items, total = await booking_service.list_for_customer(session, current_user, status, page, page_size)
    return Paginated(items=[BookingOut.model_validate(item).model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


# Explanation:
# `my_appointments` returns a paginated list of bookings for the current
# customer; conversion to `BookingOut` JSON is done server-side for
# consistency.
#
# Alternative (commented): stream results with pagination cursors for
# large datasets instead of offset pagination.
#
# @router.get("/me/appointments")
# async def my_appointments_cursor(...):
#     return await booking_service.list_for_customer_cursor(...)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/organiser/bookings", response_model=Paginated)
async def organiser_bookings(
    appointment_type_id: UUID | None = None,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    items, total = await booking_service.list_for_organiser(
        session,
        current_user,
        appointment_type_id,
        status,
        date_from,
        date_to,
        page,
        page_size,
    )
    return Paginated(items=[BookingOut.model_validate(item).model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


# Explanation:
# `organiser_bookings` returns bookings scoped to the organiser and
# supports filtering by appointment type and date ranges.
#
# Alternative (commented): add async background jobs to precompute
# organiser dashboards for high-throughput systems.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.patch("/organiser/bookings/{booking_id}/cancel", response_model=BookingOut)
async def organiser_cancel_booking(
    booking_id: UUID,
    background_tasks: BackgroundTasks,
    payload: CancelRequest | None = None,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    appointment = await booking_service.cancel(session, booking_id, current_user, payload.reason if payload else None, bypass_window=True)
    background_tasks.add_task(deliver_queued_notifications_for_appointment, appointment.id, "booking_cancelled")
    return await booking_service.get_booking_detail(session, appointment.id, current_user)


# Explanation:
# `organiser_cancel_booking` allows organisers to bypass customer cancel
# windows when cancelling on behalf of customers (e.g., admin action).
#
# Alternative (commented): log a separate audit entry for admin cancellations
# and require two-step confirmation for destructive actions.


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/organiser/calendar")
async def organiser_calendar(
    view: str = "week",
    start: datetime | None = None,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    items, _total = await booking_service.list_for_organiser(session, current_user, None, None, None, None, 1, 200)
    return {"view": view, "start": start, "items": items}


# Explanation:
# `organiser_calendar` assembles a calendar view for an organiser by
# reusing the list_for_organiser service call and returning items for UI use.
#
# Alternative (commented): implement a specialized calendar service that
# aggregates slots and bookings into calendar-friendly structures.
