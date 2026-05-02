"""
Backend documentation for `schemas/advanced.py`.

This schema module defines request/response contracts used by FastAPI and the frontend TypeScript client.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Backend note: Groups related backend data or behavior for a single domain concept.
class FeatureFlagsOut(BaseModel):
    flags: dict[str, bool]


# Backend note: Input contract used when creating a backend resource.
class WaitlistCreate(BaseModel):
    appointment_type_id: UUID
    slot_id: UUID | None = None
    notes: str | None = None


# Backend note: Groups related backend data or behavior for a single domain concept.
class WaitlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    appointment_type_id: UUID
    slot_id: UUID | None
    customer_id: UUID
    status: str
    offer_mode: str
    priority: int
    expires_at: datetime | None
    created_at: datetime


# Backend note: Groups related backend data or behavior for a single domain concept.
class CartItem(BaseModel):
    appointment_type_id: UUID
    duration_minutes: int = Field(gt=0)
    price: Decimal | None = None
    resource_id: UUID | None = None


# Backend note: Input contract used when creating a backend resource.
class CartQuoteCreate(BaseModel):
    items: list[CartItem]
    currency: str = "INR"


# Backend note: Groups related backend data or behavior for a single domain concept.
class CartQuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    items: list | dict
    total_duration_minutes: int
    total_price: Decimal | None
    currency: str
    status: str
    created_at: datetime


# Backend note: API request contract accepted from the frontend.
class PricingEstimateRequest(BaseModel):
    appointment_type_id: UUID
    duration_minutes: int | None = None
    base_price: Decimal | None = None
    context: dict | None = None


# Backend note: Groups related backend data or behavior for a single domain concept.
class PricingEstimateOut(BaseModel):
    base_price: Decimal
    total_price: Decimal
    currency: str = "INR"
    breakdown: list[dict]


# Backend note: Groups related backend data or behavior for a single domain concept.
class ThemeSettingsPayload(BaseModel):
    name: str = "Odoo Default"
    settings: dict


# Backend note: Groups related backend data or behavior for a single domain concept.
class ThemeSettingsOut(BaseModel):
    id: UUID | None = None
    name: str
    settings: dict
    is_default: bool = False


# Backend note: Input contract used when creating a backend resource.
class ManualBookingCreate(BaseModel):
    customer_id: UUID
    appointment_type_id: UUID
    slot_id: UUID
    people_count: int = Field(default=1, gt=0)
    resource_id: UUID | None = None
    payment_status: str | None = None
    internal_notes: str | None = None


# Backend note: Input contract used when creating a backend resource.
class PackageCreate(BaseModel):
    name: str
    appointment_type_id: UUID | None = None
    session_count: int = Field(gt=0)
    price: Decimal = Field(ge=0)
    currency: str = "INR"


# Backend note: Groups related backend data or behavior for a single domain concept.
class PackageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    appointment_type_id: UUID | None
    session_count: int
    price: Decimal
    currency: str
    is_active: bool


# Backend note: Groups related backend data or behavior for a single domain concept.
class AnalyticsOut(BaseModel):
    total_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    no_shows: int
    waitlist_conversion_rate: float
    most_booked_services: list[dict]
    peak_booking_hours: list[dict]
    staff_utilization: list[dict]
