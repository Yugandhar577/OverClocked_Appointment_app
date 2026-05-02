from uuid import uuid4

import pytest

from SRC.Backend.config import Settings
from SRC.Backend.db.models import Notification
from SRC.Backend.services.email_delivery import RESEND_EMAILS_URL, deliver_notification


class FakeResponse:
    def raise_for_status(self) -> None:
        return None


class FakeClient:
    def __init__(self) -> None:
        self.request = None

    async def post(self, url, *, headers, json):
        self.request = {"url": url, "headers": headers, "json": json}
        return FakeResponse()


class FakeSession:
    def __init__(self, notification: Notification, recipient_email: str) -> None:
        self.notification = notification
        self.recipient_email = recipient_email
        self.commits = 0

    async def get(self, _model, notification_id):
        return self.notification if notification_id == self.notification.id else None

    async def scalar(self, _statement):
        return self.recipient_email

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.asyncio
async def test_deliver_notification_sends_resend_email_and_marks_sent():
    notification = Notification(
        id=uuid4(),
        recipient_id=uuid4(),
        channel="email",
        event_type="email_verify",
        subject="Your verification code",
        body="Your OverClocked verification code is 123456.",
        status="queued",
    )
    session = FakeSession(notification, "customer@example.com")
    client = FakeClient()
    settings = Settings(resend_api_key="re_test_key", resend_from_email="onboarding@resend.dev")

    delivered = await deliver_notification(session, notification.id, settings, client=client)

    assert delivered is True
    assert session.commits == 1
    assert notification.status == "sent"
    assert notification.sent_at is not None
    assert notification.error_message is None
    assert client.request == {
        "url": RESEND_EMAILS_URL,
        "headers": {"Authorization": "Bearer re_test_key"},
        "json": {
            "from": "onboarding@resend.dev",
            "to": "customer@example.com",
            "subject": "Your verification code",
            "html": "<p>Your OverClocked verification code is 123456.</p>",
        },
    }
