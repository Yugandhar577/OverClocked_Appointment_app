import logging
from email.message import EmailMessage

import aiosmtplib

from SRC.Backend.config import get_settings

logger = logging.getLogger(__name__)


async def send(*, to: str, subject: str, body: str) -> None:
    settings = get_settings()
    msg = EmailMessage()
    msg["From"] = f"{settings.smtp_sender_name} <{settings.smtp_from}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    smtp_kwargs: dict = {
        "hostname": settings.smtp_host,
        "port": settings.smtp_port,
    }
    if settings.smtp_use_tls:
        smtp_kwargs["use_tls"] = True

    async with aiosmtplib.SMTP(**smtp_kwargs) as smtp:
        if settings.smtp_username:
            await smtp.login(settings.smtp_username, settings.smtp_password)
        await smtp.send_message(msg)

    logger.info("Email sent to %s subject=%r", to, subject)
