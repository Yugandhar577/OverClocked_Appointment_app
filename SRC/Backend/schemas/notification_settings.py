from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID | None
    reminder_email_hours: int | None
    reminder_sms_hours: int | None
    email_enabled: bool
    sms_enabled: bool
    sender_name: str
    reminder_email_subject: str
    reminder_email_body: str
    reminder_sms_body: str
    booking_confirmation_subject: str
    booking_confirmation_body: str
    cancellation_subject: str
    cancellation_body: str
    updated_at: datetime


class NotificationSettingsUpdate(BaseModel):
    reminder_email_hours: int | None = Field(default=None, ge=0, le=720)
    reminder_sms_hours: int | None = Field(default=None, ge=0, le=720)
    email_enabled: bool | None = None
    sms_enabled: bool | None = None
    sender_name: str | None = Field(default=None, min_length=1, max_length=120)
    reminder_email_subject: str | None = Field(default=None, min_length=1, max_length=200)
    reminder_email_body: str | None = Field(default=None, min_length=1, max_length=5000)
    reminder_sms_body: str | None = Field(default=None, max_length=480)
    booking_confirmation_subject: str | None = Field(default=None, min_length=1, max_length=200)
    booking_confirmation_body: str | None = Field(default=None, min_length=1, max_length=5000)
    cancellation_subject: str | None = Field(default=None, min_length=1, max_length=200)
    cancellation_body: str | None = Field(default=None, min_length=1, max_length=5000)
