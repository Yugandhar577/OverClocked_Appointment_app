from decimal import Decimal
from typing import Any

import razorpay

from app.config import settings


def _client() -> razorpay.Client:
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise RuntimeError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in .env")
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


def rupees_to_paise(amount: Decimal) -> int:
    return int((amount * 100).quantize(Decimal("1")))


def create_order(
    *,
    amount_paise: int,
    currency: str,
    receipt: str,
    notes: dict[str, str] | None = None,
) -> dict[str, Any]:
    client = _client()
    rid = receipt[:40]
    payload: dict[str, Any] = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": rid,
        "payment_capture": 1,
    }
    if notes:
        payload["notes"] = notes
    order = client.order.create(payload)
    return order


def verify_payment_signature(*, order_id: str, payment_id: str, signature: str) -> None:
    client = _client()
    params = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    }
    client.utility.verify_payment_signature(params)


def fetch_payment(payment_id: str) -> dict[str, Any]:
    client = _client()
    return client.payment.fetch(payment_id)
