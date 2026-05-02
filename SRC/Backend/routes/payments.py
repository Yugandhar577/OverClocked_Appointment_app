import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.config import Settings, get_settings
from SRC.Backend.core.deps import get_current_user
from SRC.Backend.core.errors import NotFoundError, NotOwnerError
from SRC.Backend.core.time import utcnow
from SRC.Backend.db.models import Appointment, AppointmentType, Payment, User
from SRC.Backend.db.session import get_db
from SRC.Backend.schemas.payments import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    PaymentStatusResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from SRC.Backend.services import razorpay_service
from SRC.Backend.services.contact_format import normalize_contact_e164

router = APIRouter(prefix="/payments", tags=["payments"])


def _map_gateway_method(method: str | None) -> str:
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


def _ensure_customer(appointment: Appointment, user: User) -> None:
    roles = getattr(user, "roles_snapshot", [])
    if appointment.customer_id != user.id and "admin" not in roles:
        raise NotOwnerError()


def _env_allows_auto_mock(settings: Settings) -> bool:
    return str(settings.env).lower() in ("dev", "development", "local", "test")


def _has_razorpay_credentials(settings: Settings) -> bool:
    return bool(str(settings.razorpay_key_id or "").strip() and str(settings.razorpay_key_secret or "").strip())


def use_payment_mock(settings: Settings) -> bool:
    """True when checkout should skip Razorpay (explicit flag, or dev without keys)."""
    if settings.mock_payments:
        return True
    if not _env_allows_auto_mock(settings):
        return False
    return not _has_razorpay_credentials(settings)


@router.post("/initiate", response_model=InitiatePaymentResponse)
async def initiate_payment(
    body: InitiatePaymentRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> InitiatePaymentResponse:
    mock = use_payment_mock(settings)
    if not mock and not _has_razorpay_credentials(settings):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway is not configured (set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET, or run in dev without keys for a local demo checkout).",
        )

    appointment = await session.get(Appointment, body.appointment_id)
    if not appointment:
        raise NotFoundError("appointment")
    _ensure_customer(appointment, current_user)

    appt_type = await session.get(AppointmentType, appointment.appointment_type_id)
    if not appt_type or not appt_type.is_paid or appt_type.price is None:
        raise HTTPException(status_code=400, detail="Appointment type is not configured for paid checkout")

    existing = await session.scalar(select(Payment).where(Payment.appointment_id == appointment.id))
    if existing and existing.status == "success":
        raise HTTPException(status_code=400, detail="Payment already completed for this appointment")

    amount: Decimal = appt_type.price
    currency = appt_type.currency.upper()
    amount_paise = razorpay_service.rupees_to_paise(amount)
    receipt = f"rcpt_{str(appointment.id).replace('-', '')}"[:40]
    checkout_amount_paise = amount_paise
    checkout_currency = currency

    if mock:
        order_id = f"mock_{uuid.uuid4().hex}"
        meta = {
            "razorpay_order_id": order_id,
            "receipt": receipt,
            "mock_checkout": True,
        }
    else:
        try:
            order = await asyncio.to_thread(
                lambda: razorpay_service.create_order(
                    amount_paise=amount_paise,
                    currency=currency,
                    receipt=receipt,
                    notes={
                        "appointment_id": str(appointment.id),
                        "appointment_type_id": str(appointment.appointment_type_id),
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Could not create Razorpay order: {exc}") from exc

        order_id = order["id"]
        # Use Razorpay's order payload for checkout so amount/currency cannot drift from the order.
        checkout_amount_paise = int(order["amount"])
        checkout_currency = str(order.get("currency") or currency).upper()
        meta = {
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
        existing.gateway_metadata = meta
        session.add(existing)
    else:
        pay = Payment(
            appointment_id=appointment.id,
            amount=amount,
            currency=currency,
            status="initiated",
            payment_method="razorpay",
            payment_gateway="razorpay",
            gateway_metadata=meta,
        )
        session.add(pay)
    await session.commit()

    customer = await session.get(User, appointment.customer_id)
    prefill_contact = normalize_contact_e164(customer.phone if customer else None)

    return InitiatePaymentResponse(
        key_id=settings.razorpay_key_id or "rzp_test_not_used",
        order_id=order_id,
        amount_paise=checkout_amount_paise,
        currency=checkout_currency,
        appointment_id=appointment.id,
        description=appt_type.title,
        customer_email=customer.email if customer else None,
        customer_contact=customer.phone if customer else None,
        prefill_name=customer.full_name if customer else None,
        prefill_contact=prefill_contact,
        display_config=None,
        mock_checkout=mock,
    )


def _complete_payment_success(
    payment: Payment,
    appointment: Appointment,
    *,
    razorpay_payment_id: str,
    razorpay_order_id: str,
    payment_method: str,
    verify_extra: dict[str, Any],
) -> None:
    now = datetime.now(timezone.utc)
    payment.status = "success"
    payment.payment_gateway_ref = razorpay_payment_id
    payment.payment_method = payment_method
    payment.paid_at = now
    merged = dict(payment.gateway_metadata or {})
    merged["razorpay_order_id"] = razorpay_order_id
    merged.update(verify_extra)
    payment.gateway_metadata = merged
    appointment.status = "confirmed"
    appointment.confirmed_at = utcnow()


@router.post("/verify", response_model=VerifyPaymentResponse)
async def verify_payment(
    body: VerifyPaymentRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> VerifyPaymentResponse:
    appointment = await session.get(Appointment, body.appointment_id)
    if not appointment:
        raise NotFoundError("appointment")
    _ensure_customer(appointment, current_user)

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

    stored = (payment.gateway_metadata or {}).get("razorpay_order_id")
    if stored and str(stored) != str(body.razorpay_order_id):
        raise HTTPException(
            status_code=400,
            detail="Payment does not match the latest checkout session. Close any old Razorpay tab and try again.",
        )

    meta = payment.gateway_metadata or {}
    is_mock_session = bool(meta.get("mock_checkout")) and str(body.razorpay_order_id).startswith("mock_")

    if is_mock_session and use_payment_mock(settings):
        _complete_payment_success(
            payment,
            appointment,
            razorpay_payment_id=body.razorpay_payment_id,
            razorpay_order_id=body.razorpay_order_id,
            payment_method="mock",
            verify_extra={"verify_response": {"mock": True}},
        )
        session.add_all([payment, appointment])
        await session.commit()
        await session.refresh(payment)
        return VerifyPaymentResponse(
            payment_id=payment.id,
            status=payment.status,
            razorpay_payment_id=body.razorpay_payment_id,
            appointment_status=appointment.status,
        )

    try:
        await asyncio.to_thread(
            lambda: razorpay_service.verify_payment_signature(
                order_id=body.razorpay_order_id,
                payment_id=body.razorpay_payment_id,
                signature=body.razorpay_signature,
            )
        )
    except Exception as exc:  # noqa: BLE001
        payment.status = "failed"
        merged = dict(payment.gateway_metadata or {})
        merged["verify_error"] = str(exc)
        payment.gateway_metadata = merged
        session.add(payment)
        await session.commit()
        raise HTTPException(status_code=400, detail=f"Signature verification failed: {exc}") from exc

    remote: dict[str, Any] = {}
    try:
        remote = await asyncio.to_thread(lambda: razorpay_service.fetch_payment(body.razorpay_payment_id))
    except Exception:
        remote = {}

    method = _map_gateway_method(remote.get("method") if isinstance(remote, dict) else None)
    _complete_payment_success(
        payment,
        appointment,
        razorpay_payment_id=body.razorpay_payment_id,
        razorpay_order_id=body.razorpay_order_id,
        payment_method=method,
        verify_extra={"verify_response": remote},
    )
    session.add_all([payment, appointment])
    await session.commit()
    await session.refresh(payment)

    return VerifyPaymentResponse(
        payment_id=payment.id,
        status=payment.status,
        razorpay_payment_id=body.razorpay_payment_id,
        appointment_status=appointment.status,
    )


@router.get("/status/{appointment_id}", response_model=PaymentStatusResponse)
async def payment_status(
    appointment_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaymentStatusResponse:
    appointment = await session.get(Appointment, appointment_id)
    if not appointment:
        raise NotFoundError("appointment")
    _ensure_customer(appointment, current_user)

    payment = await session.scalar(select(Payment).where(Payment.appointment_id == appointment_id))
    if not payment:
        return PaymentStatusResponse(appointment_id=appointment_id, payment_status=None)
    meta = payment.gateway_metadata or {}
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
