"""
Backend documentation for `routes/advanced.py`.

This route module keeps HTTP concerns thin: validate inputs, call service-layer logic, and return typed API responses.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.core.deps import get_current_user, require_role
from SRC.Backend.db.models import User
from SRC.Backend.db.session import get_db
from SRC.Backend.schemas.advanced import (
    AnalyticsOut,
    CartQuoteCreate,
    CartQuoteOut,
    FeatureFlagsOut,
    ManualBookingCreate,
    PackageCreate,
    PackageOut,
    PricingEstimateOut,
    PricingEstimateRequest,
    ThemeSettingsOut,
    ThemeSettingsPayload,
    WaitlistCreate,
    WaitlistOut,
)
from SRC.Backend.schemas.bookings import BookingCreate, BookingCreateResponse
from SRC.Backend.services import advanced_service, booking_service

router = APIRouter(tags=["advanced"])


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/features", response_model=FeatureFlagsOut)
async def features():
    return FeatureFlagsOut(flags=advanced_service.feature_flags())


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/integrations/google-calendar/connect")
async def google_calendar_connect():
    return {
        "provider": "google_calendar",
        "status": "not_configured",
        "auth_url": "https://calendar.google.com/calendar/u/0/r",
    }


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/waitlist", response_model=WaitlistOut, status_code=status.HTTP_201_CREATED)
async def join_waitlist(
    payload: WaitlistCreate,
    current_user: User = Depends(require_role("customer", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await advanced_service.join_waitlist(
        session,
        appointment_type_id=payload.appointment_type_id,
        slot_id=payload.slot_id,
        customer=current_user,
        notes=payload.notes,
    )


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/admin/waitlist", response_model=list[WaitlistOut])
async def admin_waitlist(
    _current_user: User = Depends(require_role("organiser", "admin")),
    session: AsyncSession = Depends(get_db),
):
    return await advanced_service.list_waitlist(session)


# Backend note: Creates a new domain record after validation and keeps side effects scoped to this workflow.
@router.post("/booking-cart/quote", response_model=CartQuoteOut, status_code=status.HTTP_201_CREATED)
async def create_cart_quote(
    payload: CartQuoteCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await advanced_service.create_cart_quote(
        session,
        items=[item.model_dump(mode="json") for item in payload.items],
        customer=current_user,
        currency=payload.currency,
    )


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/pricing/estimate", response_model=PricingEstimateOut)
async def pricing_estimate(
    payload: PricingEstimateRequest,
    session: AsyncSession = Depends(get_db),
):
    return await advanced_service.estimate_price(
        session,
        appointment_type_id=payload.appointment_type_id,
        duration_minutes=payload.duration_minutes,
        base_price=payload.base_price,
    )


# Backend note: Reads data and shapes it for the caller without mutating booking state unless noted by the implementation.
@router.get("/theme", response_model=ThemeSettingsOut)
async def get_theme(session: AsyncSession = Depends(get_db)):
    return await advanced_service.active_theme(session)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.put("/admin/theme", response_model=ThemeSettingsOut)
async def save_theme(
    payload: ThemeSettingsPayload,
    _current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    theme = await advanced_service.save_theme(session, name=payload.name, settings=payload.settings)
    return {"id": theme.id, "name": theme.name, "settings": theme.settings, "is_default": False}


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/admin/theme/reset", response_model=ThemeSettingsOut)
async def reset_theme(
    _current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    return await advanced_service.reset_theme(session)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.post("/admin/manual-bookings", response_model=BookingCreateResponse, status_code=status.HTTP_201_CREATED)
async def manual_booking(
    payload: ManualBookingCreate,
    _current_user: User = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_db),
):
    customer = User(id=payload.customer_id, full_name="Manual booking customer", email="", password_hash="")
    booking_payload = BookingCreate(
        appointment_type_id=payload.appointment_type_id,
        slot_id=payload.slot_id,
        resource_id=payload.resource_id,
        people_count=payload.people_count,
        customer_info=None,
        answers=[],
    )
    appointment, slot, appointment_type, organiser_name = await booking_service.create(session, booking_payload, customer)
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


# Backend note: Creates a new domain record after validation and keeps side effects scoped to this workflow.
@router.post("/admin/packages", response_model=PackageOut, status_code=status.HTTP_201_CREATED)
async def create_package(
    payload: PackageCreate,
    _current_user: User = Depends(require_role("admin", "organiser")),
    session: AsyncSession = Depends(get_db),
):
    return await advanced_service.create_package(session, payload)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/packages", response_model=list[PackageOut])
async def packages(session: AsyncSession = Depends(get_db)):
    return await advanced_service.list_packages(session)


# Backend note: Coordinates a focused piece of backend logic used by routes, services, jobs, or tests.
@router.get("/admin/analytics", response_model=AnalyticsOut)
async def analytics(
    _current_user: User = Depends(require_role("admin", "organiser")),
    session: AsyncSession = Depends(get_db),
):
    return await advanced_service.analytics(session)
