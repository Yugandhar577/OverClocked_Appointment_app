from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MailTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID | None
    template_type: str
    name: str
    subject: str | None
    body_html: str
    description: str | None
    is_system_default: bool
    can_edit: bool
    updated_at: datetime


class MailTemplateCreate(BaseModel):
    template_type: str = Field(pattern="^(booking_confirmation|cancellation|reminder_email|reminder_sms)$")
    name: str = Field(min_length=1, max_length=200)
    subject: str | None = Field(default=None, max_length=300)
    body_html: str = Field(min_length=1, max_length=50000)
    description: str | None = Field(default=None, max_length=1000)


class MailTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    subject: str | None = Field(default=None, max_length=300)
    body_html: str | None = Field(default=None, min_length=1, max_length=50000)
    description: str | None = Field(default=None, max_length=1000)


class MailTemplatePreviewRequest(BaseModel):
    sample_appointment_id: UUID | None = None


class MailTemplatePreviewResponse(BaseModel):
    subject: str | None
    body_html: str
