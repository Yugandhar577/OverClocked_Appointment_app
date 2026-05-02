from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class InitiatePaymentRequest(BaseModel):
    appointment_id: UUID


class InitiatePaymentResponse(BaseModel):
    key_id: str
    order_id: str
    amount_paise: int
    currency: str
    appointment_id: UUID
    description: str
    customer_email: str | None = None
    customer_contact: str | None = None
    prefill_name: str | None = None
    prefill_contact: str
    display_config: dict[str, Any] | None = None
    mock_checkout: bool = False


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


class DemoCompletePaymentRequest(BaseModel):
    appointment_id: UUID
    razorpay_order_id: str | None = None
    payment_method: str = Field(default="upi_pay", max_length=30)


class VerifyPaymentResponse(BaseModel):
    payment_id: UUID
    status: str
    razorpay_payment_id: str
    appointment_status: str


class PaymentStatusResponse(BaseModel):
    appointment_id: UUID
    payment_status: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    paid_at: datetime | None = None
    payment_gateway_ref: str | None = None
    last_error: str | None = None
