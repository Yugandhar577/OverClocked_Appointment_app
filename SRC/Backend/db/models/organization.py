import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from SRC.Backend.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    domain: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    admin_report_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


_DEFAULT_REMINDER_EMAIL_SUBJECT = "Reminder: {{appointment_type}} coming up"
_DEFAULT_REMINDER_EMAIL_BODY = (
    "Hi {{customer_name}},\n\n"
    "This is a reminder for your upcoming appointment:\n\n"
    "Service: {{appointment_type}}\n"
    "Date: {{appointment_date}}\n"
    "Time: {{appointment_time}}\n"
    "Venue: {{venue}}\n"
    "Confirmation: {{confirmation_code}}\n\n"
    "See you soon!\n{{organization_name}}"
)
_DEFAULT_REMINDER_SMS_BODY = (
    "Reminder: {{appointment_type}} on {{appointment_date}} at {{appointment_time}}. "
    "Code: {{confirmation_code}}"
)
_DEFAULT_BOOKING_SUBJECT = "Booking confirmed: {{appointment_type}}"
_DEFAULT_BOOKING_BODY = (
    "Hi {{customer_name}},\n\n"
    "Your booking is confirmed!\n\n"
    "Service: {{appointment_type}}\n"
    "Date: {{appointment_date}}\n"
    "Time: {{appointment_time}}\n"
    "Venue: {{venue}}\n"
    "Confirmation code: {{confirmation_code}}\n\n"
    "Thank you,\n{{organization_name}}"
)
_DEFAULT_CANCEL_SUBJECT = "Booking cancelled: {{appointment_type}}"
_DEFAULT_CANCEL_BODY = (
    "Hi {{customer_name}},\n\n"
    "Your booking ({{confirmation_code}}) for {{appointment_type}} on {{appointment_date}} "
    "has been cancelled.\n\n{{organization_name}}"
)


class OrganizationNotificationSettings(Base):
    __tablename__ = "organization_notification_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), unique=True, nullable=True
    )
    reminder_email_hours: Mapped[int | None] = mapped_column(Integer, default=24, nullable=True)
    reminder_sms_hours: Mapped[int | None] = mapped_column(Integer, default=2, nullable=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sender_name: Mapped[str] = mapped_column(String(120), default="OverClocked Appointments", nullable=False)
    reminder_email_subject: Mapped[str] = mapped_column(String(200), default=_DEFAULT_REMINDER_EMAIL_SUBJECT, nullable=False)
    reminder_email_body: Mapped[str] = mapped_column(Text, default=_DEFAULT_REMINDER_EMAIL_BODY, nullable=False)
    reminder_sms_body: Mapped[str] = mapped_column(Text, default=_DEFAULT_REMINDER_SMS_BODY, nullable=False)
    booking_confirmation_subject: Mapped[str] = mapped_column(String(200), default=_DEFAULT_BOOKING_SUBJECT, nullable=False)
    booking_confirmation_body: Mapped[str] = mapped_column(Text, default=_DEFAULT_BOOKING_BODY, nullable=False)
    cancellation_subject: Mapped[str] = mapped_column(String(200), default=_DEFAULT_CANCEL_SUBJECT, nullable=False)
    cancellation_body: Mapped[str] = mapped_column(Text, default=_DEFAULT_CANCEL_BODY, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
