from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
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

router = APIRouter(tags=["bookings"])


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


@router.post("/bookings", response_model=BookingCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(require_role("customer", "admin")),
    session: AsyncSession = Depends(get_db),
):
    appointment, slot, appointment_type, organiser_name = await booking_service.create(session, payload, current_user)
    return BookingCreateResponse(
        booking_id=appointment.id,
        status=appointment.status,
        confirmation_code=appointment.confirmation_code,
        slot_start=slot.start_datetime,
        slot_end=slot.end_datetime,
        venue=appointment_type.venue,
        organiser_name=organiser_name,
        payment_required=appointment_type.is_paid,
        payment_url=f"/mock-payments/{appointment.id}" if appointment_type.is_paid else None,
    )


@router.get("/bookings/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await booking_service.get_booking_detail(session, booking_id, current_user)


@router.patch("/bookings/{booking_id}/cancel", response_model=BookingOut)
async def cancel_booking(
    booking_id: UUID,
    payload: CancelRequest | None = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    appointment = await booking_service.cancel(session, booking_id, current_user, payload.reason if payload else None)
    return await booking_service.get_booking_detail(session, appointment.id, current_user)


@router.patch("/bookings/{booking_id}/reschedule", response_model=RescheduleResponse)
async def reschedule_booking(
    booking_id: UUID,
    payload: RescheduleRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    old, new = await booking_service.reschedule(session, booking_id, payload.new_slot_id, current_user)
    return RescheduleResponse(old_id=old.id, new_id=new.id)


@router.patch("/bookings/{booking_id}/confirm", response_model=BookingOut)
async def confirm_booking(
    booking_id: UUID,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    appointment = await booking_service.confirm(session, booking_id, current_user)
    return await booking_service.get_booking_detail(session, appointment.id, current_user)


@router.get("/me/appointments", response_model=Paginated)
async def my_appointments(
    status: str | None = Query(default=None),
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    items, total = await booking_service.list_for_customer(session, current_user, status, page, page_size)
    return Paginated(items=[BookingOut.model_validate(item).model_dump(mode="json") for item in items], total=total, page=page, page_size=page_size)


@router.get("/organiser/bookings", response_model=Paginated)
async def organiser_bookings(
    appointment_type_id: UUID | None = None,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
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


@router.patch("/organiser/bookings/{booking_id}/cancel", response_model=BookingOut)
async def organiser_cancel_booking(
    booking_id: UUID,
    payload: CancelRequest | None = None,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    appointment = await booking_service.cancel(session, booking_id, current_user, payload.reason if payload else None, bypass_window=True)
    return await booking_service.get_booking_detail(session, appointment.id, current_user)


@router.get("/organiser/calendar")
async def organiser_calendar(
    view: str = "week",
    start: datetime | None = None,
    current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    items, _total = await booking_service.list_for_organiser(session, current_user, None, None, None, None, 1, 200)
    return {"view": view, "start": start, "items": items}
