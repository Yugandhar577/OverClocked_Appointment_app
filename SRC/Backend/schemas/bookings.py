"""
Backend documentation for `schemas/bookings.py`.

This schema module defines request/response contracts used by FastAPI and the frontend TypeScript client.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

import re
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PHONE_RE = re.compile(r"^[\d\s+\-()\[\]]{7,20}$")


# Backend note: Groups related backend data or behavior for a single domain concept.
class AvailabilitySlot(BaseModel):
    slot_id: UUID
    start_datetime: datetime
    end_datetime: datetime
    remaining_capacity: int
    max_capacity: int
    resource_id: UUID | None
    status: str = "available"
    is_waitlist_reserved: bool = False


# Backend note: Groups related backend data or behavior for a single domain concept.
class IntakeAnswerIn(BaseModel):
    question_id: UUID
    value: str | int | bool | list[str] | dict


# Backend note: Groups related backend data or behavior for a single domain concept.
class CustomerInfoIn(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, v: object) -> object:
        if isinstance(v, str):
            v = v.strip()
            if v and len(v) < 2:
                raise ValueError("Full name must be at least 2 characters")
            if len(v) > 150:
                raise ValueError("Full name must be at most 150 characters")
        return v or None

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: object) -> object:
        if isinstance(v, str):
            v = v.strip()
            if v and not _EMAIL_RE.match(v):
                raise ValueError("Enter a valid email address")
        return v or None

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: object) -> object:
        if isinstance(v, str):
            v = v.strip()
            if v and not _PHONE_RE.match(v):
                raise ValueError("Enter a valid phone number (7–20 digits, spaces, +, -, ( ) allowed)")
        return v or None


# Backend note: Input contract used when creating a backend resource.
class BookingCreate(BaseModel):
    appointment_type_id: UUID
    slot_id: UUID
    resource_id: UUID | None = None
    people_count: int = Field(default=1, gt=0)
    answers: list[IntakeAnswerIn] = []
    customer_info: CustomerInfoIn | None = None


# Backend note: Input contract used when creating a backend resource.
class BookingCreateResponse(BaseModel):
    booking_id: UUID
    status: str
    confirmation_code: str
    slot_start: datetime
    slot_end: datetime
    venue: str | None
    organiser_name: str
    payment_required: bool
    payment_url: str | None = None


# Backend note: Groups related backend data or behavior for a single domain concept.
class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    appointment_type_id: UUID
    slot_id: UUID
    customer_id: UUID
    resource_id: UUID | None
    status: str
    people_count: int
    confirmation_code: str
    created_at: datetime
    updated_at: datetime
    slot_start: datetime | None = None
    slot_end: datetime | None = None
    appointment_title: str | None = None
    venue: str | None = None


# Backend note: API request contract accepted from the frontend.
class CancelRequest(BaseModel):
    reason: str | None = None


# Backend note: API request contract accepted from the frontend.
class RescheduleRequest(BaseModel):
    new_slot_id: UUID


# Backend note: API response contract sent back to the frontend.
class RescheduleResponse(BaseModel):
    old_id: UUID
    new_id: UUID


# Backend note: Groups related backend data or behavior for a single domain concept.
class AvailabilityQuery(BaseModel):
    appointment_type_id: UUID
    resource_id: UUID | None = None
    date: date
    tz_offset_minutes: int = 0
