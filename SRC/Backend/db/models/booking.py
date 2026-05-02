import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from SRC.Backend.db.base import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("appointment_types.id"), nullable=False)
    slot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("generated_slots.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("resources.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    people_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    guest_names: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rescheduled_from: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("appointments.id"))
    confirmation_code: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    customer_full_name: Mapped[str | None] = mapped_column(String(150))
    customer_email: Mapped[str | None] = mapped_column(String(255))
    customer_phone: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'cancelled', 'completed', 'rescheduled', 'no_show')",
            name="ck_appointments_status",
        ),
        CheckConstraint("people_count > 0", name="ck_appointments_people_count_positive"),
    )


class AppointmentAnswer(Base):
    __tablename__ = "appointment_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"))
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("appointment_questions.id"))
    answer_text: Mapped[str | None] = mapped_column(Text)
    answer_json: Mapped[dict | list | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SlotCapacityLog(Base):
    __tablename__ = "slot_capacity_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("generated_slots.id"), nullable=False)
    appointment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False)
    delta: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    new_count: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (CheckConstraint("delta <> 0", name="ck_slot_capacity_log_delta_nonzero"),)
