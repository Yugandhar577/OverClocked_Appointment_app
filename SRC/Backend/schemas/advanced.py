from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeatureFlagsOut(BaseModel):
    flags: dict[str, bool]


class WaitlistCreate(BaseModel):
    appointment_type_id: UUID
    slot_id: UUID | None = None
    notes: str | None = None


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


class CartItem(BaseModel):
    appointment_type_id: UUID
    duration_minutes: int = Field(gt=0)
    price: Decimal | None = None
    resource_id: UUID | None = None


class CartQuoteCreate(BaseModel):
    items: list[CartItem]
    currency: str = "INR"


class CartQuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    items: list | dict
    total_duration_minutes: int
    total_price: Decimal | None
    currency: str
    status: str
    created_at: datetime


class PricingEstimateRequest(BaseModel):
    appointment_type_id: UUID
    duration_minutes: int | None = None
    base_price: Decimal | None = None
    context: dict | None = None


class PricingEstimateOut(BaseModel):
    base_price: Decimal
    total_price: Decimal
    currency: str = "INR"
    breakdown: list[dict]


class ThemeSettingsPayload(BaseModel):
    name: str = "Odoo Default"
    settings: dict


class ThemeSettingsOut(BaseModel):
    id: UUID | None = None
    name: str
    settings: dict
    is_default: bool = False


class ManualBookingCreate(BaseModel):
    customer_id: UUID
    appointment_type_id: UUID
    slot_id: UUID
    people_count: int = Field(default=1, gt=0)
    resource_id: UUID | None = None
    payment_status: str | None = None
    internal_notes: str | None = None


class PackageCreate(BaseModel):
    name: str
    appointment_type_id: UUID | None = None
    session_count: int = Field(gt=0)
    price: Decimal = Field(ge=0)
    currency: str = "INR"


class PackageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    appointment_type_id: UUID | None
    session_count: int
    price: Decimal
    currency: str
    is_active: bool


class AnalyticsOut(BaseModel):
    total_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    no_shows: int
    waitlist_conversion_rate: float
    most_booked_services: list[dict]
    peak_booking_hours: list[dict]
    staff_utilization: list[dict]
