import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Minimal users row so appointments.customer_id and organiser FKs match the design doc."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    timezone: Mapped[str] = mapped_column(String(60), nullable=False, server_default="UTC")
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    profile_photo: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    appointment_types: Mapped[list["AppointmentType"]] = relationship(back_populates="organiser")


class AppointmentType(Base):
    """Subset of appointment_types including is_paid / price / currency for checkout."""

    __tablename__ = "appointment_types"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    organiser_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="30")
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(5), nullable=False, server_default="INR")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    organiser: Mapped["User"] = relationship(back_populates="appointment_types")
    slots: Mapped[list["GeneratedSlot"]] = relationship(back_populates="appointment_type")


class GeneratedSlot(Base):
    """Minimal generated_slots for appointment.slot_id FK."""

    __tablename__ = "generated_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    appointment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointment_types.id", ondelete="CASCADE"), nullable=False
    )
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    booked_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    source: Mapped[str] = mapped_column(String(20), nullable=False, server_default="weekly")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    appointment_type: Mapped["AppointmentType"] = relationship(back_populates="slots")


class Appointment(Base):
    """Minimal appointments row; payments.appointment_id is UNIQUE (1:1)."""

    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    appointment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointment_types.id"), nullable=False
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generated_slots.id"), nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    people_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    payment: Mapped[Optional["Payment"]] = relationship(back_populates="appointment", uselist=False)


class Payment(Base):
    """
    Table 16: payments — aligned with appointment_db_design.docx (Razorpay fields in metadata / gateway ref).
    """

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False, unique=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(5), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False, server_default="unknown")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="initiated")
    payment_gateway_ref: Mapped[Optional[str]] = mapped_column(String(200))
    payment_gateway: Mapped[Optional[str]] = mapped_column(String(50))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    refund_ref: Mapped[Optional[str]] = mapped_column(String(200))
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    appointment: Mapped["Appointment"] = relationship(back_populates="payment")
