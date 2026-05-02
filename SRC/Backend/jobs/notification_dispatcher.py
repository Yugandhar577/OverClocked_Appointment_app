import logging

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from SRC.Backend.core.time import utcnow
from SRC.Backend.db.models import Notification, User
from SRC.Backend.db.session import async_session_factory
from SRC.Backend.services import email_sender, sms_sender

logger = logging.getLogger(__name__)

_BATCH_SIZE = 50


async def dispatch_queued_notifications() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            rows = (
                await session.execute(
                    select(Notification, User)
                    .join(User, User.id == Notification.recipient_id)
                    .where(Notification.status == "queued")
                    .limit(_BATCH_SIZE)
                    .with_for_update(skip_locked=True)
                )
            ).all()

            sent = failed = 0
            for notification, user in rows:
                try:
                    if notification.channel == "email":
                        await email_sender.send(
                            to=user.email,
                            subject=notification.subject or "(no subject)",
                            body=notification.body,
                        )
                    elif notification.channel == "sms":
                        if not user.phone:
                            raise RuntimeError("recipient has no phone number on file")
                        await sms_sender.send(to=user.phone, body=notification.body)
                    else:
                        raise RuntimeError(f"unknown channel: {notification.channel}")

                    notification.status = "sent"
                    notification.sent_at = utcnow()
                    sent += 1
                except Exception as exc:
                    notification.status = "failed"
                    notification.error_message = str(exc)[:500]
                    failed += 1
                    logger.warning(
                        "notification_dispatcher: failed id=%s channel=%s error=%s",
                        notification.id,
                        notification.channel,
                        exc,
                    )

            if sent or failed:
                logger.info("notification_dispatcher: sent=%d failed=%d", sent, failed)
