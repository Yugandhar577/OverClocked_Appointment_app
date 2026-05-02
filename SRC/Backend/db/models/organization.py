import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
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

