from decimal import Decimal
from typing import Any

import razorpay

from SRC.Backend.config import get_settings


def _client() -> razorpay.Client:
    settings = get_settings()
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise RuntimeError("Razorpay keys are not configured.")
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


def rupees_to_paise(amount: Decimal) -> int:
    return int((amount * 100).quantize(Decimal("1")))


def create_order(*, amount_paise: int, currency: str, receipt: str, notes: dict[str, str] | None = None) -> dict[str, Any]:
    client = _client()
    payload: dict[str, Any] = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": receipt[:40],
        "payment_capture": 1,
    }
    if notes:
        payload["notes"] = notes
    return client.order.create(payload)


def verify_payment_signature(*, order_id: str, payment_id: str, signature: str) -> None:
    client = _client()
    client.utility.verify_payment_signature(
        {
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        }
    )


def fetch_payment(payment_id: str) -> dict[str, Any]:
    client = _client()
    return client.payment.fetch(payment_id)
