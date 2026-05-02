from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class DemoSeedResponse(BaseModel):
    organiser_id: UUID
    customer_id: UUID
    appointment_type_id: UUID
    slot_id: UUID
    appointment_id: UUID
    message: str


class InitiatePaymentRequest(BaseModel):
    appointment_id: UUID


class InitiatePaymentResponse(BaseModel):
    key_id: str
    order_id: str
    amount_paise: int
    currency: str
    appointment_id: UUID
    description: str
    customer_email: Optional[str] = None
    customer_contact: Optional[str] = None
    prefill_name: Optional[str] = None
    prefill_contact: str
    display_config: Optional[dict[str, Any]] = None


class VerifyPaymentRequest(BaseModel):
    appointment_id: UUID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

    @field_validator("razorpay_order_id", "razorpay_payment_id", "razorpay_signature")
    @classmethod
    def strip_non_empty(cls, v: str) -> str:
        s = (v or "").strip()
        if not s:
            raise ValueError("must not be empty")
        return s


class VerifyPaymentResponse(BaseModel):
    payment_id: UUID
    status: str
    razorpay_payment_id: str
    appointment_status: str


class PaymentStatusResponse(BaseModel):
    appointment_id: UUID
    payment_status: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    paid_at: Optional[datetime] = None
    payment_gateway_ref: Optional[str] = None
    last_error: Optional[str] = None
