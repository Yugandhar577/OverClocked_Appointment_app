from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Appointment, AppointmentType, Payment, User
from app.schemas import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    PaymentStatusResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from app.config import settings
from app.contact_format import normalize_contact_e164
from app.services import razorpay_service

router = APIRouter(prefix="/payments", tags=["payments"])

# Pass `display_config=null` from the API so the browser omits `options.config` entirely.
# Razorpay then uses Dashboard + default checkout (UPI, cards, netbanking, wallets, etc.).
# Custom blocks previously hid UPI and restricted issuers, which broke UPI and many test payments.
# To customise again, see: https://razorpay.com/docs/payments/payment-gateway/web-integration/standard/configure-payment-methods/


def _map_gateway_method(method: Optional[str]) -> str:
    if not method:
        return "unknown"
    m = method.lower().strip()
    if m == "upi":
        return "upi_pay"
    if m in ("card", "debit_card", "credit_card"):
        return "card"
    if m == "wallet":
        return "wallet"
    if m == "emi":
        return "emi"
    if len(m) > 30:
        return m[:30]
    return m


@router.post("/initiate", response_model=InitiatePaymentResponse)
def initiate_payment(body: InitiatePaymentRequest, db: Session = Depends(get_db)) -> InitiatePaymentResponse:
    appointment = db.get(Appointment, body.appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appt_type = db.get(AppointmentType, appointment.appointment_type_id)
    if not appt_type or not appt_type.is_paid or appt_type.price is None:
        raise HTTPException(status_code=400, detail="Appointment type is not configured for paid checkout")

    existing = db.scalar(select(Payment).where(Payment.appointment_id == appointment.id))
    if existing and existing.status == "success":
        raise HTTPException(status_code=400, detail="Payment already completed for this appointment")

    amount: Decimal = appt_type.price
    currency = appt_type.currency.upper()
    amount_paise = razorpay_service.rupees_to_paise(amount)
    receipt = f"rcpt_{str(appointment.id).replace('-', '')}"[:40]

    order = razorpay_service.create_order(
        amount_paise=amount_paise,
        currency=currency,
        receipt=receipt,
        notes={
            "appointment_id": str(appointment.id),
            "appointment_type_id": str(appointment.appointment_type_id),
        },
    )
    order_id = order["id"]

    meta: dict[str, Any] = {
        "razorpay_order_id": order_id,
        "receipt": receipt,
        "order_create_response": order,
    }

    if existing:
        existing.amount = amount
        existing.currency = currency
        existing.status = "initiated"
        existing.payment_gateway = "razorpay"
        existing.payment_gateway_ref = None
        existing.paid_at = None
        existing.metadata_ = meta
        db.add(existing)
    else:
        pay = Payment(
            appointment_id=appointment.id,
            amount=amount,
            currency=currency,
            status="initiated",
            payment_gateway="razorpay",
            metadata_=meta,
        )
        db.add(pay)
    db.commit()

    customer = db.get(User, appointment.customer_id)
    prefill_contact = normalize_contact_e164(customer.phone if customer else None)

    return InitiatePaymentResponse(
        key_id=settings.razorpay_key_id,
        order_id=order_id,
        amount_paise=amount_paise,
        currency=currency,
        appointment_id=appointment.id,
        description=appt_type.title,
        customer_email=customer.email if customer else None,
        customer_contact=customer.phone if customer else None,
        prefill_name=customer.full_name if customer else None,
        prefill_contact=prefill_contact,
        display_config=None,
    )


@router.post("/verify", response_model=VerifyPaymentResponse)
def verify_payment(body: VerifyPaymentRequest, db: Session = Depends(get_db)) -> VerifyPaymentResponse:
    appointment = db.get(Appointment, body.appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    payment = db.scalar(select(Payment).where(Payment.appointment_id == appointment.id))
    if not payment:
        raise HTTPException(status_code=400, detail="No payment record for this appointment")

    if payment.status == "success":
        return VerifyPaymentResponse(
            payment_id=payment.id,
            status=payment.status,
            razorpay_payment_id=body.razorpay_payment_id,
            appointment_status=appointment.status,
        )

    stored = (payment.metadata_ or {}).get("razorpay_order_id")
    if stored and str(stored) != str(body.razorpay_order_id):
        raise HTTPException(
            status_code=400,
            detail="Payment does not match the latest checkout session. Close any old Razorpay tab and click Pay again.",
        )

    try:
        razorpay_service.verify_payment_signature(
            order_id=body.razorpay_order_id,
            payment_id=body.razorpay_payment_id,
            signature=body.razorpay_signature,
        )
    except Exception as exc:  # noqa: BLE001 — Razorpay SDK raises generic errors
        payment.status = "failed"
        merged = dict(payment.metadata_ or {})
        merged["verify_error"] = str(exc)
        payment.metadata_ = merged
        db.add(payment)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Signature verification failed: {exc}") from exc

    remote: dict[str, Any] = {}
    try:
        remote = razorpay_service.fetch_payment(body.razorpay_payment_id)
    except Exception:
        remote = {}

    method = _map_gateway_method(remote.get("method") if isinstance(remote, dict) else None)
    now = datetime.now(timezone.utc)
    payment.status = "success"
    payment.payment_gateway_ref = body.razorpay_payment_id
    payment.payment_method = method
    payment.paid_at = now
    merged = dict(payment.metadata_ or {})
    merged["razorpay_order_id"] = body.razorpay_order_id
    merged["verify_response"] = remote
    payment.metadata_ = merged

    appointment.status = "confirmed"
    db.add_all([payment, appointment])
    db.commit()
    db.refresh(payment)

    return VerifyPaymentResponse(
        payment_id=payment.id,
        status=payment.status,
        razorpay_payment_id=body.razorpay_payment_id,
        appointment_status=appointment.status,
    )


@router.get("/status/{appointment_id}", response_model=PaymentStatusResponse)
def payment_status(appointment_id: UUID, db: Session = Depends(get_db)) -> PaymentStatusResponse:
    payment = db.scalar(select(Payment).where(Payment.appointment_id == appointment_id))
    if not payment:
        return PaymentStatusResponse(appointment_id=appointment_id, payment_status=None)
    meta = payment.metadata_ or {}
    err = meta.get("verify_error") if isinstance(meta.get("verify_error"), str) else None
    return PaymentStatusResponse(
        appointment_id=appointment_id,
        payment_status=payment.status,
        amount=payment.amount,
        currency=payment.currency,
        paid_at=payment.paid_at,
        payment_gateway_ref=payment.payment_gateway_ref,
        last_error=err,
    )
