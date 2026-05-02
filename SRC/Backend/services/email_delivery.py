from html import escape
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.config import Settings, get_settings
from SRC.Backend.core.time import utcnow
from SRC.Backend.db.models import Notification, User
from SRC.Backend.db.session import async_session_factory

RESEND_EMAILS_URL = "https://api.resend.com/emails"
PLACEHOLDER_RESEND_API_KEY = "re_xxxxxxxxx"


class EmailDeliveryError(RuntimeError):
    pass


def _should_send(settings: Settings) -> bool:
    return bool(settings.resend_api_key and settings.resend_api_key != PLACEHOLDER_RESEND_API_KEY)


def _html_body(body: str) -> str:
    return "<p>" + escape(body).replace("\n", "<br>") + "</p>"


async def deliver_notification(
    session: AsyncSession,
    notification_id: UUID,
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
) -> bool:
    notification = await session.get(Notification, notification_id)
    if not notification or notification.channel != "email":
        return False
    if not _should_send(settings):
        return False
    if not notification.recipient_id:
        notification.status = "failed"
        notification.error_message = "Email notification has no recipient."
        await session.commit()
        raise EmailDeliveryError(notification.error_message)

    recipient_email = await session.scalar(select(User.email).where(User.id == notification.recipient_id))
    if not recipient_email:
        notification.status = "failed"
        notification.error_message = "Email recipient was not found."
        await session.commit()
        raise EmailDeliveryError(notification.error_message)

    payload = {
        "from": settings.resend_from_email,
        "to": recipient_email,
        "subject": notification.subject or "OverClocked notification",
        "html": _html_body(notification.body),
    }

    async def send(active_client: httpx.AsyncClient) -> None:
        response = await active_client.post(
            RESEND_EMAILS_URL,
            headers={"Authorization": f"Bearer {settings.resend_api_key}"},
            json=payload,
        )
        response.raise_for_status()

    try:
        if client:
            await send(client)
        else:
            async with httpx.AsyncClient(timeout=10) as active_client:
                await send(active_client)
    except httpx.HTTPError as exc:
        notification.status = "failed"
        notification.error_message = str(exc)[:1000]
        await session.commit()
        raise EmailDeliveryError(notification.error_message) from exc

    notification.status = "sent"
    notification.sent_at = utcnow()
    notification.error_message = None
    await session.commit()
    return True


async def deliver_notification_job(
    notification_id: UUID,
    settings: Settings | None = None,
    *,
    raise_on_error: bool = False,
) -> bool:
    active_settings = settings or get_settings()
    try:
        async with async_session_factory() as session:
            return await deliver_notification(session, notification_id, active_settings)
    except EmailDeliveryError:
        if raise_on_error:
            raise
        return False
