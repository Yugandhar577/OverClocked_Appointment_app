from datetime import datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from SRC.Backend.schemas.reminders import ReminderOut


class AppointmentTypeCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    preset_type: str | None = "meeting"
    description: str | None = None
    duration_minutes: int = Field(gt=0, default=30)
    resource_type: str = "user"
    timezone: str = "Asia/Kolkata"
    future_days_limit: int = Field(default=30, ge=1, le=120)
    venue: str | None = None
    image_url: str | None = None
    video_url: str | None = None


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
    image_url: str | None = None
    video_url: str | None = None
    booking_email_template_id: UUID | None = None
    cancellation_email_template_id: UUID | None = None
    reminder_email_template_id: UUID | None = None
    reminder_sms_template_id: UUID | None = None


class AppointmentTypeUpdateRules(BaseModel):
    requires_confirmation: bool = False
    manage_capacity: bool = True
    allow_invitations: bool = True
    display_pictures: bool = False
    is_paid: bool = False
    price: Decimal | None = None
    advance_payment_required: bool = False
    cancel_before_minutes: int | None = 60
    reschedule_before_minutes: int | None = 60
    max_per_slot: int = Field(default=1, gt=0)
    future_days_limit: int = Field(default=30, ge=1, le=120)
    assignment_method: str = "auto"
    starts_with: str = "date"
    slot_type: str = "weekly"
    slot_interval_minutes: int | None = Field(default=None, ge=5, le=1440)


class ResourceCreate(BaseModel):
    id: UUID | None = None
    name: str
    resource_type: str = "human"
    capacity: int = Field(default=1, gt=0)
    timezone: str = "Asia/Kolkata"
    priority: int = 1
    user_ref_id: UUID | None = None


class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    resource_type: str
    capacity: int
    timezone: str
    is_active: bool
    user_ref_id: UUID | None = None


class ResourceCandidateOut(BaseModel):
    id: UUID
    name: str
    resource_type: str
    capacity: int = 1
    email: str | None = None
    user_ref_id: UUID | None = None


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
    allow_invitations: bool
    display_pictures: bool
    max_capacity: int | None
    future_days_limit: int
    starts_with: str
    allow_cancel: bool
    cancel_before_minutes: int | None
    allow_reschedule: bool
    reschedule_before_minutes: int | None
    venue: str | None
    confirmation_msg: str | None
    image_url: str | None
    video_url: str | None
    booking_email_template_id: UUID | None
    cancellation_email_template_id: UUID | None
    reminder_email_template_id: UUID | None
    reminder_sms_template_id: UUID | None
    slot_interval_minutes: int | None


class AppointmentTypeDetail(AppointmentTypeOut):
    resources: list[ResourceOut] = []
    questions: list[QuestionOut] = []
    working_hours: list[WorkingHourOut] = []
    reminders: list[ReminderOut] = []


class ShareLinkOut(BaseModel):
    url: str


class PublishOut(BaseModel):
    id: UUID
    is_published: bool
    slots_generated: int


class ActivityOut(BaseModel):
    id: UUID
    action: str
    actor_name: str | None = None
    message: str | None = None
    created_at: datetime


class ActivityCreate(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
