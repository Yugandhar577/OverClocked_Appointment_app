from uuid import uuid4

import pytest

from SRC.Backend.config import Settings
from SRC.Backend.db.models import Notification
from SRC.Backend.db.models.booking import Appointment
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


class FakeSmtpSender:
    def __init__(self) -> None:
        self.message = None
        self.settings = None

    async def __call__(self, message, settings) -> None:
        self.message = message
        self.settings = settings


class FakeSession:
    def __init__(
        self,
        notification: Notification,
        recipient_email: str | None = None,
        appointment: Appointment | None = None,
    ) -> None:
        self.notification = notification
        self.recipient_email = recipient_email
        self.appointment = appointment
        self.commits = 0

    async def get(self, model, item_id):
        if model is Notification and item_id == self.notification.id:
            return self.notification
        if model is Appointment and self.appointment and item_id == self.appointment.id:
            return self.appointment
        return None

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


@pytest.mark.asyncio
async def test_deliver_notification_sends_smtp_to_appointment_customer_email():
    appointment = Appointment(
        id=uuid4(),
        customer_email="form-customer@example.com",
    )
    notification = Notification(
        id=uuid4(),
        appointment_id=appointment.id,
        recipient_id=uuid4(),
        channel="email",
        event_type="booking_confirmed",
        subject="Booking confirmed",
        body="Your appointment is confirmed.",
        status="queued",
    )
    session = FakeSession(notification, recipient_email="account@example.com", appointment=appointment)
    smtp_sender = FakeSmtpSender()
    settings = Settings(smtp_host="mailhog", smtp_port=1025, smtp_from="noreply@appointments.local")

    delivered = await deliver_notification(session, notification.id, settings, smtp_sender=smtp_sender)

    assert delivered is True
    assert session.commits == 1
    assert notification.status == "sent"
    assert smtp_sender.settings is settings
    assert smtp_sender.message["From"] == "noreply@appointments.local"
    assert smtp_sender.message["To"] == "form-customer@example.com"
    assert smtp_sender.message["Subject"] == "Booking confirmed"
    assert smtp_sender.message.get_body(("html",)).get_content().strip() == "<p>Your appointment is confirmed.</p>"


@pytest.mark.asyncio
async def test_deliver_notification_smtp_falls_back_to_recipient_account_email():
    notification = Notification(
        id=uuid4(),
        recipient_id=uuid4(),
        channel="email",
        event_type="booking_confirmed",
        subject="Booking confirmed",
        body="Your appointment is confirmed.",
        status="queued",
    )
    session = FakeSession(notification, recipient_email="account@example.com")
    smtp_sender = FakeSmtpSender()
    settings = Settings(smtp_host="mailhog", smtp_port=1025, smtp_from="noreply@appointments.local")

    delivered = await deliver_notification(session, notification.id, settings, smtp_sender=smtp_sender)

    assert delivered is True
    assert notification.status == "sent"
    assert smtp_sender.message["To"] == "account@example.com"
