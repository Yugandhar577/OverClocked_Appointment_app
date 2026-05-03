from collections.abc import Awaitable, Callable
from email.message import EmailMessage
from html import escape
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from SRC.Backend.config import Settings, get_settings
from SRC.Backend.core.time import utcnow
from SRC.Backend.db.models import Notification, User
from SRC.Backend.db.models.booking import Appointment

RESEND_EMAILS_URL = "https://api.resend.com/emails"
PLACEHOLDER_RESEND_API_KEY = "re_xxxxxxxxx"
SmtpSender = Callable[[EmailMessage, Settings], Awaitable[None]]


class EmailDeliveryError(RuntimeError):
    pass


def _should_send_resend(settings: Settings) -> bool:
    return bool(settings.resend_api_key and settings.resend_api_key != PLACEHOLDER_RESEND_API_KEY)


def _should_send_smtp(settings: Settings) -> bool:
    return bool(settings.smtp_host and settings.smtp_port and settings.smtp_from)


def _html_body(body: str) -> str:
    return "<p>" + escape(body).replace("\n", "<br>") + "</p>"


async def _recipient_email(session: AsyncSession, notification: Notification) -> str | None:
    # Prefer customer_email from the linked appointment (set from the email question answer).
    # Fall back to the recipient_id user's account email.
    if notification.appointment_id:
        appt = await session.get(Appointment, notification.appointment_id)
        if appt and appt.customer_email:
            return appt.customer_email

    if notification.recipient_id:
        return await session.scalar(select(User.email).where(User.id == notification.recipient_id))

    return None


async def _send_smtp(message: EmailMessage, settings: Settings) -> None:
    try:
        import aiosmtplib

        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username or None,
            password=settings.smtp_password or None,
            start_tls=settings.smtp_starttls,
        )
    except ImportError as exc:
        raise EmailDeliveryError("aiosmtplib is required for SMTP email delivery.") from exc
    except aiosmtplib.SMTPException as exc:
        raise EmailDeliveryError(str(exc)) from exc


async def deliver_notification(
    session: AsyncSession,
    notification_id: UUID,
    settings: Settings,
    *,
    client: httpx.AsyncClient | None = None,
    smtp_sender: SmtpSender | None = None,
) -> bool:
    notification = await session.get(Notification, notification_id)
    if not notification or notification.channel != "email":
        return False

    recipient_email = await _recipient_email(session, notification)
    if not recipient_email:
        notification.status = "failed"
        notification.error_message = "Email recipient could not be resolved."
        await session.commit()
        raise EmailDeliveryError(notification.error_message)

    subject = notification.subject or "OverClocked notification"

    try:
        if _should_send_resend(settings):
            payload = {
                "from": settings.resend_from_email,
                "to": recipient_email,
                "subject": subject,
                "html": _html_body(notification.body),
            }

            async def send_resend(active_client: httpx.AsyncClient) -> None:
                response = await active_client.post(
                    RESEND_EMAILS_URL,
                    headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                    json=payload,
                )
                response.raise_for_status()

            if client:
                await send_resend(client)
            else:
                async with httpx.AsyncClient(timeout=10) as active_client:
                    await send_resend(active_client)
        elif _should_send_smtp(settings):
            message = EmailMessage()
            message["From"] = settings.smtp_from
            message["To"] = recipient_email
            message["Subject"] = subject
            message.set_content(notification.body)
            message.add_alternative(_html_body(notification.body), subtype="html")
            await (smtp_sender or _send_smtp)(message, settings)
        else:
            return False
    except EmailDeliveryError as exc:
        notification.status = "failed"
        notification.error_message = str(exc)[:1000]
        await session.commit()
        raise
    except (httpx.HTTPError, OSError) as exc:
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
        from SRC.Backend.db.session import async_session_factory

        async with async_session_factory() as session:
            return await deliver_notification(session, notification_id, active_settings)
    except EmailDeliveryError:
        if raise_on_error:
            raise
        return False


async def deliver_queued_notifications_for_appointment(
    appointment_id: UUID,
    event_type: str | None = None,
    settings: Settings | None = None,
) -> int:
    active_settings = settings or get_settings()
    from SRC.Backend.db.session import async_session_factory

    async with async_session_factory() as session:
        stmt = (
            select(Notification.id)
            .where(Notification.appointment_id == appointment_id)
            .where(Notification.channel == "email")
            .where(Notification.status == "queued")
            .order_by(Notification.created_at.asc(), Notification.id.asc())
        )
        if event_type:
            stmt = stmt.where(Notification.event_type == event_type)
        notification_ids = list((await session.execute(stmt)).scalars().all())

    delivered = 0
    for notification_id in notification_ids:
        if await deliver_notification_job(notification_id, active_settings):
            delivered += 1
    return delivered


async def deliver_queued_notifications_for_recipient(
    recipient_id: UUID,
    event_type: str | None = None,
    settings: Settings | None = None,
) -> int:
    active_settings = settings or get_settings()
    from SRC.Backend.db.session import async_session_factory

    async with async_session_factory() as session:
        stmt = (
            select(Notification.id)
            .where(Notification.recipient_id == recipient_id)
            .where(Notification.channel == "email")
            .where(Notification.status == "queued")
            .order_by(Notification.created_at.asc(), Notification.id.asc())
        )
        if event_type:
            stmt = stmt.where(Notification.event_type == event_type)
        notification_ids = list((await session.execute(stmt)).scalars().all())

    delivered = 0
    for notification_id in notification_ids:
        if await deliver_notification_job(notification_id, active_settings):
            delivered += 1
    return delivered
