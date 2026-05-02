"""add organization_notification_settings table

Revision ID: 006
Revises: 005
Create Date: 2026-05-03
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if insp.has_table("organization_notification_settings"):
        return

    op.create_table(
        "organization_notification_settings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True, unique=True),
        sa.Column("reminder_email_hours", sa.Integer(), nullable=True, server_default="24"),
        sa.Column("reminder_sms_hours", sa.Integer(), nullable=True, server_default="2"),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sms_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sender_name", sa.String(120), nullable=False, server_default="OverClocked Appointments"),
        sa.Column("reminder_email_subject", sa.String(200), nullable=False, server_default="Reminder: {{appointment_type}} coming up"),
        sa.Column("reminder_email_body", sa.Text(), nullable=False, server_default=(
            "Hi {{customer_name}},\n\n"
            "This is a reminder for your upcoming appointment:\n\n"
            "Service: {{appointment_type}}\nDate: {{appointment_date}}\n"
            "Time: {{appointment_time}}\nVenue: {{venue}}\n"
            "Confirmation: {{confirmation_code}}\n\nSee you soon!\n{{organization_name}}"
        )),
        sa.Column("reminder_sms_body", sa.Text(), nullable=False, server_default=(
            "Reminder: {{appointment_type}} on {{appointment_date}} at {{appointment_time}}. "
            "Code: {{confirmation_code}}"
        )),
        sa.Column("booking_confirmation_subject", sa.String(200), nullable=False, server_default="Booking confirmed: {{appointment_type}}"),
        sa.Column("booking_confirmation_body", sa.Text(), nullable=False, server_default=(
            "Hi {{customer_name}},\n\nYour booking is confirmed!\n\n"
            "Service: {{appointment_type}}\nDate: {{appointment_date}}\n"
            "Time: {{appointment_time}}\nVenue: {{venue}}\n"
            "Confirmation code: {{confirmation_code}}\n\nThank you,\n{{organization_name}}"
        )),
        sa.Column("cancellation_subject", sa.String(200), nullable=False, server_default="Booking cancelled: {{appointment_type}}"),
        sa.Column("cancellation_body", sa.Text(), nullable=False, server_default=(
            "Hi {{customer_name}},\n\nYour booking ({{confirmation_code}}) for "
            "{{appointment_type}} on {{appointment_date}} has been cancelled.\n\n{{organization_name}}"
        )),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_org_notif_settings_org",
        "organization_notification_settings",
        ["organization_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("organization_notification_settings")
