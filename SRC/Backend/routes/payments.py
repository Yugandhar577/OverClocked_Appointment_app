from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.config import get_settings
from SRC.Backend.core.deps import get_current_user, require_role
from SRC.Backend.db.models import Appointment, AppointmentType, Payment, User
from SRC.Backend.db.session import get_db
from SRC.Backend.schemas.payments import (
    DemoCompletePaymentRequest,
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    PaymentStatusResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from SRC.Backend.services.contact_format import normalize_contact_e164
from SRC.Backend.services import razorpay_service

router = APIRouter(tags=["payments"])


def _map_gateway_method(method: str | None) -> str:
    if not method:
        return "unknown"
    mapping = {
        "upi": "upi_pay",
        "card": "card",
        "debit_card": "card",
        "credit_card": "card",
        "wallet": "wallet",
        "emi": "emi",
    }
    return mapping.get(method.lower().strip(), method.lower().strip()[:30])


def _is_admin(user: User) -> bool:
    return "admin" in getattr(user, "roles_snapshot", [])


@router.post("/payments/initiate", response_model=InitiatePaymentResponse)
async def initiate_payment(
    body: InitiatePaymentRequest,
    current_user: User = Depends(require_role("customer", "admin")),
    session: AsyncSession = Depends(get_db),
) -> InitiatePaymentResponse:
    appointment = await session.get(Appointment, body.appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if not _is_admin(current_user) and appointment.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to start payment for this booking")

    appointment_type = await session.get(AppointmentType, appointment.appointment_type_id)
    if not appointment_type or not appointment_type.is_paid or appointment_type.price is None:
        raise HTTPException(status_code=400, detail="Appointment type is not configured for paid checkout")

    existing = await session.scalar(select(Payment).where(Payment.appointment_id == appointment.id))
    if existing and existing.status == "success":
        raise HTTPException(status_code=400, detail="Payment already completed for this appointment")

    amount: Decimal = appointment_type.price
    currency = appointment_type.currency.upper()
    amount_paise = razorpay_service.rupees_to_paise(amount)
    receipt = f"rcpt_{str(appointment.id).replace('-', '')}"[:40]
    order = razorpay_service.create_order(
        amount_paise=amount_paise,
        currency=currency,
        receipt=receipt,
        notes={
            "appointment_id": str(appointment.id),
            "appointment_type_id": str(appointment_type.id),
        },
    )
    order_id = order["id"]
    metadata = {"razorpay_order_id": order_id, "receipt": receipt, "order_create_response": order}

    if existing:
        existing.amount = amount
        existing.currency = currency
        existing.payment_method = "initiated"
        existing.status = "initiated"
        existing.payment_gateway = "razorpay"
        existing.payment_gateway_ref = None
        existing.paid_at = None
        existing.gateway_metadata = metadata
        session.add(existing)
    else:
        session.add(
            Payment(
                appointment_id=appointment.id,
                amount=amount,
                currency=currency,
                payment_method="initiated",
                status="initiated",
                payment_gateway="razorpay",
                gateway_metadata=metadata,
            )
        )
    await session.commit()

    customer = await session.get(User, appointment.customer_id)
    prefill_contact = normalize_contact_e164(customer.phone if customer else None)
    settings = get_settings()
    return InitiatePaymentResponse(
        key_id=settings.razorpay_key_id,
        order_id=order_id,
        amount_paise=amount_paise,
        currency=currency,
        appointment_id=appointment.id,
        description=appointment_type.title,
        customer_email=customer.email if customer else None,
        customer_contact=customer.phone if customer else None,
        prefill_name=customer.full_name if customer else None,
        prefill_contact=prefill_contact,
        display_config=None,
    )


@router.post("/payments/verify", response_model=VerifyPaymentResponse)
async def verify_payment(
    body: VerifyPaymentRequest,
    current_user: User = Depends(require_role("customer", "admin")),
    session: AsyncSession = Depends(get_db),
) -> VerifyPaymentResponse:
    appointment = await session.get(Appointment, body.appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if not _is_admin(current_user) and appointment.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to verify payment for this booking")

    payment = await session.scalar(select(Payment).where(Payment.appointment_id == appointment.id))
    if not payment:
        raise HTTPException(status_code=400, detail="No payment record for this appointment")
    if payment.status == "success":
        return VerifyPaymentResponse(
            payment_id=payment.id,
            status=payment.status,
            razorpay_payment_id=body.razorpay_payment_id,
            appointment_status=appointment.status,
        )

    stored_order = (payment.gateway_metadata or {}).get("razorpay_order_id")
    if stored_order and str(stored_order) != body.razorpay_order_id:
        raise HTTPException(status_code=400, detail="Checkout session expired. Please click pay again.")

    try:
        razorpay_service.verify_payment_signature(
            order_id=body.razorpay_order_id,
            payment_id=body.razorpay_payment_id,
            signature=body.razorpay_signature,
        )
    except Exception as exc:  # noqa: BLE001
        metadata = dict(payment.gateway_metadata or {})
        metadata["verify_error"] = str(exc)
        payment.status = "failed"
        payment.gateway_metadata = metadata
        session.add(payment)
        await session.commit()
        raise HTTPException(status_code=400, detail=f"Signature verification failed: {exc}") from exc

    remote: dict = {}
    try:
        remote = razorpay_service.fetch_payment(body.razorpay_payment_id)
    except Exception:  # noqa: BLE001
        remote = {}

    metadata = dict(payment.gateway_metadata or {})
    metadata["razorpay_order_id"] = body.razorpay_order_id
    metadata["verify_response"] = remote
    payment.gateway_metadata = metadata
    payment.status = "success"
    payment.payment_method = _map_gateway_method(remote.get("method") if isinstance(remote, dict) else None)
    payment.payment_gateway_ref = body.razorpay_payment_id
    payment.paid_at = datetime.now(timezone.utc)
    appointment.status = "confirmed"
    session.add_all([payment, appointment])
    await session.commit()
    await session.refresh(payment)
    await session.refresh(appointment)
    return VerifyPaymentResponse(
        payment_id=payment.id,
        status=payment.status,
        razorpay_payment_id=body.razorpay_payment_id,
        appointment_status=appointment.status,
    )


@router.post("/payments/demo-complete", response_model=VerifyPaymentResponse)
async def demo_complete_payment(
    body: DemoCompletePaymentRequest,
    current_user: User = Depends(require_role("customer", "admin")),
    session: AsyncSession = Depends(get_db),
) -> VerifyPaymentResponse:
    appointment = await session.get(Appointment, body.appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if not _is_admin(current_user) and appointment.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to complete payment for this booking")

    appointment_type = await session.get(AppointmentType, appointment.appointment_type_id)
    if not appointment_type or not appointment_type.is_paid or appointment_type.price is None:
        raise HTTPException(status_code=400, detail="Appointment type is not configured for paid checkout")

    payment = await session.scalar(select(Payment).where(Payment.appointment_id == appointment.id))
    if payment and payment.status == "success":
        return VerifyPaymentResponse(
            payment_id=payment.id,
            status=payment.status,
            razorpay_payment_id=payment.payment_gateway_ref or "demo_rzp_existing",
            appointment_status=appointment.status,
        )

    metadata = dict(payment.gateway_metadata or {}) if payment else {}
    if body.razorpay_order_id:
        metadata["razorpay_order_id"] = body.razorpay_order_id
    metadata["embedded_checkout"] = True
    metadata["embedded_checkout_note"] = "Razorpay-style embedded test checkout completed for hackathon demo."

    gateway_ref = f"demo_rzp_{appointment.id.hex[:18]}"
    if payment:
        payment.amount = appointment_type.price
        payment.currency = appointment_type.currency.upper()
        payment.payment_method = body.payment_method[:30]
        payment.status = "success"
        payment.payment_gateway = "razorpay"
        payment.payment_gateway_ref = gateway_ref
        payment.paid_at = datetime.now(timezone.utc)
        payment.gateway_metadata = metadata
    else:
        payment = Payment(
            appointment_id=appointment.id,
            amount=appointment_type.price,
            currency=appointment_type.currency.upper(),
            payment_method=body.payment_method[:30],
            status="success",
            payment_gateway="razorpay",
            payment_gateway_ref=gateway_ref,
            paid_at=datetime.now(timezone.utc),
            gateway_metadata=metadata,
        )

    appointment.status = "confirmed"
    appointment.confirmed_at = appointment.confirmed_at or datetime.now(timezone.utc)
    session.add_all([payment, appointment])
    await session.commit()
    await session.refresh(payment)
    await session.refresh(appointment)
    return VerifyPaymentResponse(
        payment_id=payment.id,
        status=payment.status,
        razorpay_payment_id=gateway_ref,
        appointment_status=appointment.status,
    )


@router.get("/payments/status/{appointment_id}", response_model=PaymentStatusResponse)
async def payment_status(
    appointment_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PaymentStatusResponse:
    appointment = await session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if not _is_admin(current_user) and appointment.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view payment status for this booking")

    payment = await session.scalar(select(Payment).where(Payment.appointment_id == appointment.id))
    if not payment:
        return PaymentStatusResponse(appointment_id=appointment.id, payment_status=None)
    last_error = (payment.gateway_metadata or {}).get("verify_error")
    return PaymentStatusResponse(
        appointment_id=appointment.id,
        payment_status=payment.status,
        amount=payment.amount,
        currency=payment.currency,
        paid_at=payment.paid_at,
        payment_gateway_ref=payment.payment_gateway_ref,
        last_error=last_error if isinstance(last_error, str) else None,
    )
