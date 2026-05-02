from datetime import time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AppointmentTypeCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    preset_type: str | None = "meeting"
    description: str | None = None
    duration_minutes: int = Field(gt=0, default=30)
    resource_type: str = "user"
    timezone: str = "Asia/Kolkata"
    future_days_limit: int = Field(default=30, ge=1, le=120)
    venue: str | None = None


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


class ResourceCreate(BaseModel):
    name: str
    resource_type: str = "human"
    capacity: int = Field(default=1, gt=0)
    timezone: str = "Asia/Kolkata"
    priority: int = 1


class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    resource_type: str
    capacity: int
    timezone: str
    is_active: bool


class WorkingHourIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    resource_id: UUID | None = None


class WorkingHourOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    day_of_week: int
    start_time: time
    end_time: time
    resource_id: UUID | None = None


class QuestionIn(BaseModel):
    label: str
    question_type: str = "text"
    required: bool = False
    options: list[str] | None = None


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question_text: str
    answer_type: str
    options: list[str] | dict | None
    is_mandatory: bool
    display_order: int


class AppointmentTypeListItem(BaseModel):
    id: UUID
    title: str
    duration_minutes: int
    is_paid: bool
    price: Decimal | None
    organiser_name: str
    preset_type: str | None = None


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


class AppointmentTypeDetail(AppointmentTypeOut):
    resources: list[ResourceOut] = []
    questions: list[QuestionOut] = []
    working_hours: list[WorkingHourOut] = []


class ShareLinkOut(BaseModel):
    url: str


class PublishOut(BaseModel):
    id: UUID
    is_published: bool
    slots_generated: int
