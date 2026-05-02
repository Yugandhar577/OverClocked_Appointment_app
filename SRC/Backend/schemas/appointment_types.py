"""
Backend documentation for `schemas/appointment_types.py`.

This schema module defines request/response contracts used by FastAPI and the frontend TypeScript client.
Comments in this file are intentionally explicit because the project is used in a hackathon-style handoff.
Keep behavior changes separate from documentation-only edits so reviews can verify no runtime contract changed.
"""

from datetime import time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Backend note: Input contract used when creating a backend resource.
class AppointmentTypeCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    preset_type: str | None = "meeting"
    description: str | None = None
    duration_minutes: int = Field(gt=0, default=30)
    resource_type: str = "user"
    timezone: str = "Asia/Kolkata"
    future_days_limit: int = Field(default=30, ge=1, le=120)
    venue: str | None = None


# Backend note: Input contract used when updating a backend resource.
class AppointmentTypeUpdate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    preset_type: str | None = "meeting"
    description: str | None = None
    duration_minutes: int = Field(gt=0, default=30)
    resource_type: str = "user"
    timezone: str = "Asia/Kolkata"
    future_days_limit: int = Field(default=30, ge=1, le=120)
    venue: str | None = None
    confirmation_msg: str | None = None


# Backend note: Input contract used when updating a backend resource.
class AppointmentTypeUpdateRules(BaseModel):
    requires_confirmation: bool = False
    manage_capacity: bool = True
    is_paid: bool = False
    price: Decimal | None = None
    advance_payment_required: bool = False
    cancel_before_minutes: int | None = 60
    reschedule_before_minutes: int | None = 60
    max_per_slot: int = Field(default=1, gt=0)
    future_days_limit: int = Field(default=30, ge=1, le=120)
    assignment_method: str = "auto"


# Backend note: Input contract used when creating a backend resource.
class ResourceCreate(BaseModel):
    name: str
    resource_type: str = "human"
    capacity: int = Field(default=1, gt=0)
    timezone: str = "Asia/Kolkata"
    priority: int = 1


# Backend note: Groups related backend data or behavior for a single domain concept.
class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    resource_type: str
    capacity: int
    timezone: str
    is_active: bool


# Backend note: Groups related backend data or behavior for a single domain concept.
class WorkingHourIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    resource_id: UUID | None = None


# Backend note: Groups related backend data or behavior for a single domain concept.
class WorkingHourOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    day_of_week: int
    start_time: time
    end_time: time
    resource_id: UUID | None = None


# Backend note: Groups related backend data or behavior for a single domain concept.
class QuestionIn(BaseModel):
    label: str
    question_type: str = "text"
    required: bool = False
    options: list[str] | None = None


# Backend note: Groups related backend data or behavior for a single domain concept.
class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_text: str
    answer_type: str
    options: list[str] | dict | None
    is_mandatory: bool
    display_order: int


# Backend note: Groups related backend data or behavior for a single domain concept.
class AppointmentTypeListItem(BaseModel):
    id: UUID
    title: str
    duration_minutes: int
    is_paid: bool
    price: Decimal | None
    organiser_name: str
    preset_type: str | None = None


# Backend note: Groups related backend data or behavior for a single domain concept.
class AppointmentTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organiser_id: UUID
    title: str
    description: str | None
    duration_minutes: int
    timezone: str
    preset_type: str | None
    resource_type: str
    assignment_method: str
    is_published: bool
    share_token: str | None
    is_paid: bool
    price: Decimal | None
    currency: str
    requires_confirmation: bool
    manage_capacity: bool
    max_capacity: int | None
    future_days_limit: int
    allow_cancel: bool
    cancel_before_minutes: int | None
    allow_reschedule: bool
    reschedule_before_minutes: int | None
    venue: str | None
    confirmation_msg: str | None


# Backend note: Groups related backend data or behavior for a single domain concept.
class AppointmentTypeDetail(AppointmentTypeOut):
    resources: list[ResourceOut] = []
    questions: list[QuestionOut] = []
    working_hours: list[WorkingHourOut] = []


# Backend note: Groups related backend data or behavior for a single domain concept.
class ShareLinkOut(BaseModel):
    url: str


# Backend note: Groups related backend data or behavior for a single domain concept.
class PublishOut(BaseModel):
    id: UUID
    is_published: bool
    slots_generated: int
