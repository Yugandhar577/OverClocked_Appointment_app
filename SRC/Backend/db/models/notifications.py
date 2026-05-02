import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from SRC.Backend.db.base import Base


class MailTemplate(Base):
    __tablename__ = "mail_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    template_type: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(300))
    body_html: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_system_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "template_type IN ('booking_confirmation', 'cancellation', 'reminder_email', 'reminder_sms')",
            name="ck_mail_templates_type",
        ),
    )


class AppointmentTypeReminder(Base):
    __tablename__ = "appointment_type_reminders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointment_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(String(10), nullable=False)
    hours_before: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("channel IN ('email', 'sms')", name="ck_appointment_type_reminders_channel"),
        CheckConstraint("hours_before >= 0 AND hours_before <= 720", name="ck_appointment_type_reminders_hours"),
        UniqueConstraint("appointment_type_id", "channel", "hours_before", name="uq_type_reminder_channel_hours"),
    )
