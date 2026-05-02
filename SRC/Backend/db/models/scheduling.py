import uuid
from datetime import datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from SRC.Backend.db.base import Base


class AppointmentType(Base):
    __tablename__ = "appointment_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organiser_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    timezone: Mapped[str] = mapped_column(String(60), default="UTC", nullable=False)
    slot_type: Mapped[str] = mapped_column(String(20), default="weekly", nullable=False)
    assignment_method: Mapped[str] = mapped_column(String(20), default="auto", nullable=False)
    resource_type: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    preset_type: Mapped[str | None] = mapped_column(String(50))
    starts_with: Mapped[str] = mapped_column(String(20), default="date", nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(5), default="INR", nullable=False)
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manage_capacity: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_invitations: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_pictures: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_capacity: Mapped[int | None] = mapped_column(Integer)
    pre_booking_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    future_days_limit: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    allow_cancel: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cancel_before_minutes: Mapped[int | None] = mapped_column(Integer)
    allow_reschedule: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reschedule_before_minutes: Mapped[int | None] = mapped_column(Integer)
    venue: Mapped[str | None] = mapped_column(Text)
    confirmation_msg: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    video_url: Mapped[str | None] = mapped_column(Text)
    booking_email_template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mail_templates.id"))
    cancellation_email_template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mail_templates.id"))
    reminder_email_template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mail_templates.id"))
    reminder_sms_template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("mail_templates.id"))
    slot_interval_minutes: Mapped[int | None] = mapped_column(Integer)
    padding_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="ck_appointment_types_duration_positive"),
        CheckConstraint("max_capacity IS NULL OR max_capacity > 0", name="ck_appointment_types_capacity_positive"),
    )


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organiser_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)
    user_ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    timezone: Mapped[str] = mapped_column(String(60), default="UTC", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (CheckConstraint("capacity > 0", name="ck_resources_capacity_positive"),)


class AppointmentTypeResource(Base):
    __tablename__ = "appointment_type_resources"

    appointment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointment_types.id", ondelete="CASCADE"),
        primary_key=True,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
        primary_key=True,
    )
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class BookingRule(Base):
    __tablename__ = "booking_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointment_types.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    max_bookings_per_slot: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    allow_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_guests: Mapped[int | None] = mapped_column(Integer)
    reminder_hours: Mapped[int | None] = mapped_column(Integer)
    slot_creation_method: Mapped[str] = mapped_column(String(20), default="auto", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AppointmentQuestion(Base):
    __tablename__ = "appointment_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointment_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_type: Mapped[str] = mapped_column(String(20), nullable=False)
    options: Mapped[dict | list | None] = mapped_column(JSONB)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class WorkingHour(Base):
    __tablename__ = "working_hours"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointment_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("resources.id"))
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_working_hours_day"),
        CheckConstraint("end_time > start_time", name="ck_working_hours_time_order"),
    )


class FlexibleSlot(Base):
    __tablename__ = "flexible_slots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointment_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("resources.id"))
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        CheckConstraint("end_datetime > start_datetime", name="ck_flexible_slots_time_order"),
        CheckConstraint("max_capacity > 0", name="ck_flexible_slots_capacity_positive"),
    )


class GeneratedSlot(Base):
    __tablename__ = "generated_slots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointment_types.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("resources.id"))
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    booked_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="weekly", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("appointment_type_id", "resource_id", "start_datetime", name="uq_generated_slot_type_resource_start"),
        CheckConstraint("end_datetime > start_datetime", name="ck_generated_slots_time_order"),
        CheckConstraint("max_capacity > 0", name="ck_generated_slots_capacity_positive"),
        CheckConstraint("booked_count >= 0", name="ck_generated_slots_booked_nonnegative"),
    )
