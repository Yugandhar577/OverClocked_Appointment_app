import logging

import httpx

from SRC.Backend.config import get_settings

logger = logging.getLogger(__name__)


async def send(*, to: str, body: str) -> None:
    settings = get_settings()
    if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_from_number:
        raise RuntimeError("sms provider not configured")

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            url,
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            data={
                "From": settings.twilio_from_number,
                "To": to,
                "Body": body,
            },
        )

    if response.status_code not in (200, 201):
        raise RuntimeError(f"Twilio error {response.status_code}: {response.text[:200]}")

    logger.info("SMS sent to %s", to)
