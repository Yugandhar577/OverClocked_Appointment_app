"""mail templates and appointment type reminders

Revision ID: 007
Revises: 006
Create Date: 2026-05-03
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None

BOOKING_SUBJECT = "Booking confirmed: {{appointment_type}}"
BOOKING_BODY = (
    "Hi {{customer_name}},\n\n"
    "Your booking is confirmed!\n\n"
    "Service: {{appointment_type}}\n"
    "Date: {{appointment_date}}\n"
    "Time: {{appointment_time}}\n"
    "Venue: {{venue}}\n"
    "Confirmation code: {{confirmation_code}}\n\n"
    "Thank you,\n{{organization_name}}"
)
CANCEL_SUBJECT = "Booking cancelled: {{appointment_type}}"
CANCEL_BODY = (
    "Hi {{customer_name}},\n\n"
    "Your booking ({{confirmation_code}}) for {{appointment_type}} on {{appointment_date}} "
    "has been cancelled.\n\n{{organization_name}}"
)
REMINDER_EMAIL_SUBJECT = "Reminder: {{appointment_type}} coming up"
REMINDER_EMAIL_BODY = (
    "Hi {{customer_name}},\n\n"
    "This is a reminder for your upcoming appointment:\n\n"
    "Service: {{appointment_type}}\n"
    "Date: {{appointment_date}}\n"
    "Time: {{appointment_time}}\n"
    "Venue: {{venue}}\n"
    "Confirmation: {{confirmation_code}}\n\n"
    "See you soon!\n{{organization_name}}"
)
REMINDER_SMS_BODY = (
    "Reminder: {{appointment_type}} on {{appointment_date}} at {{appointment_time}}. "
    "Code: {{confirmation_code}}"
)


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def _add_column_if_missing(table: str, column: sa.Column) -> None:
    if column.name not in _columns(table):
        op.add_column(table, column)


def _drop_column_if_exists(table: str, column_name: str) -> None:
    if column_name in _columns(table):
        op.drop_column(table, column_name)


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("mail_templates"):
        op.create_table(
            "mail_templates",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
            sa.Column("template_type", sa.String(40), nullable=False),
            sa.Column("name", sa.String(200), nullable=False),
            sa.Column("subject", sa.String(300), nullable=True),
            sa.Column("body_html", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_system_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint(
                "template_type IN ('booking_confirmation', 'cancellation', 'reminder_email', 'reminder_sms')",
                name="ck_mail_templates_type",
            ),
        )
    existing_indexes = {idx["name"] for idx in insp.get_indexes("mail_templates")} if insp.has_table("mail_templates") else set()
    if "uq_mail_templates_org_name" not in existing_indexes:
        op.create_index(
            "uq_mail_templates_org_name",
            "mail_templates",
            ["organization_id", "name"],
            unique=True,
            postgresql_where=sa.text("organization_id IS NOT NULL"),
        )
    if "idx_mail_templates_type" not in existing_indexes:
        op.create_index("idx_mail_templates_type", "mail_templates", ["template_type"])

    if not insp.has_table("appointment_type_reminders"):
        op.create_table(
            "appointment_type_reminders",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column(
                "appointment_type_id",
                UUID(as_uuid=True),
                sa.ForeignKey("appointment_types.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("channel", sa.String(10), nullable=False),
            sa.Column("hours_before", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint("channel IN ('email', 'sms')", name="ck_appointment_type_reminders_channel"),
            sa.CheckConstraint("hours_before >= 0 AND hours_before <= 720", name="ck_appointment_type_reminders_hours"),
            sa.UniqueConstraint("appointment_type_id", "channel", "hours_before", name="uq_type_reminder_channel_hours"),
        )

    _add_column_if_missing(
        "appointment_types",
        sa.Column("booking_email_template_id", UUID(as_uuid=True), sa.ForeignKey("mail_templates.id"), nullable=True),
    )
    _add_column_if_missing(
        "appointment_types",
        sa.Column("cancellation_email_template_id", UUID(as_uuid=True), sa.ForeignKey("mail_templates.id"), nullable=True),
    )
    _add_column_if_missing(
        "appointment_types",
        sa.Column("reminder_email_template_id", UUID(as_uuid=True), sa.ForeignKey("mail_templates.id"), nullable=True),
    )
    _add_column_if_missing(
        "appointment_types",
        sa.Column("reminder_sms_template_id", UUID(as_uuid=True), sa.ForeignKey("mail_templates.id"), nullable=True),
    )

    defaults = [
        ("booking_confirmation", "Booking Confirmation", BOOKING_SUBJECT, BOOKING_BODY, "Default booking confirmation email."),
        ("cancellation", "Cancellation", CANCEL_SUBJECT, CANCEL_BODY, "Default cancellation email."),
        ("reminder_email", "Reminder Email", REMINDER_EMAIL_SUBJECT, REMINDER_EMAIL_BODY, "Default email reminder."),
        ("reminder_sms", "Reminder SMS", None, REMINDER_SMS_BODY, "Default SMS reminder."),
    ]
    for template_type, name, subject, body, description in defaults:
        exists = bind.execute(
            sa.text(
                "SELECT id FROM mail_templates "
                "WHERE organization_id IS NULL AND template_type = :template_type AND is_system_default = true"
            ),
            {"template_type": template_type},
        ).first()
        if not exists:
            bind.execute(
                sa.text(
                    "INSERT INTO mail_templates "
                    "(organization_id, template_type, name, subject, body_html, description, is_system_default) "
                    "VALUES (NULL, :template_type, :name, :subject, :body_html, :description, true)"
                ),
                {
                    "template_type": template_type,
                    "name": name,
                    "subject": subject,
                    "body_html": body,
                    "description": description,
                },
            )

    bind.execute(
        sa.text(
            """
            UPDATE appointment_types
            SET booking_email_template_id = (
                    SELECT id FROM mail_templates
                    WHERE organization_id IS NULL AND template_type = 'booking_confirmation'
                    ORDER BY created_at ASC LIMIT 1
                ),
                cancellation_email_template_id = (
                    SELECT id FROM mail_templates
                    WHERE organization_id IS NULL AND template_type = 'cancellation'
                    ORDER BY created_at ASC LIMIT 1
                ),
                reminder_email_template_id = (
                    SELECT id FROM mail_templates
                    WHERE organization_id IS NULL AND template_type = 'reminder_email'
                    ORDER BY created_at ASC LIMIT 1
                ),
                reminder_sms_template_id = (
                    SELECT id FROM mail_templates
                    WHERE organization_id IS NULL AND template_type = 'reminder_sms'
                    ORDER BY created_at ASC LIMIT 1
                )
            WHERE booking_email_template_id IS NULL
               OR cancellation_email_template_id IS NULL
               OR reminder_email_template_id IS NULL
               OR reminder_sms_template_id IS NULL
            """
        )
    )

    if "reminder_email_hours" in _columns("appointment_types"):
        bind.execute(
            sa.text(
                """
                INSERT INTO appointment_type_reminders (appointment_type_id, channel, hours_before)
                SELECT id, 'email', COALESCE(reminder_email_hours, 24)
                FROM appointment_types
                WHERE COALESCE(reminder_email_hours, 24) BETWEEN 0 AND 720
                ON CONFLICT (appointment_type_id, channel, hours_before) DO NOTHING
                """
            )
        )
    else:
        bind.execute(
            sa.text(
                """
                INSERT INTO appointment_type_reminders (appointment_type_id, channel, hours_before)
                SELECT id, 'email', 24 FROM appointment_types
                ON CONFLICT (appointment_type_id, channel, hours_before) DO NOTHING
                """
            )
        )
    if "reminder_sms_hours" in _columns("appointment_types"):
        bind.execute(
            sa.text(
                """
                INSERT INTO appointment_type_reminders (appointment_type_id, channel, hours_before)
                SELECT id, 'sms', COALESCE(reminder_sms_hours, 2)
                FROM appointment_types
                WHERE COALESCE(reminder_sms_hours, 2) BETWEEN 0 AND 720
                ON CONFLICT (appointment_type_id, channel, hours_before) DO NOTHING
                """
            )
        )
    else:
        bind.execute(
            sa.text(
                """
                INSERT INTO appointment_type_reminders (appointment_type_id, channel, hours_before)
                SELECT id, 'sms', 2 FROM appointment_types
                ON CONFLICT (appointment_type_id, channel, hours_before) DO NOTHING
                """
            )
        )

    for col in [
        "booking_email_template",
        "cancellation_email_template",
        "reminder_email_hours",
        "reminder_sms_hours",
    ]:
        _drop_column_if_exists("appointment_types", col)

    if insp.has_table("organization_notification_settings"):
        op.drop_table("organization_notification_settings")


def downgrade() -> None:
    _add_column_if_missing(
        "appointment_types",
        sa.Column("booking_email_template", sa.String(length=120), nullable=True, server_default="Appointment: Attendee Invitation"),
    )
    _add_column_if_missing(
        "appointment_types",
        sa.Column("cancellation_email_template", sa.String(length=120), nullable=True, server_default="Appointment: Appointment Canceled"),
    )
    _add_column_if_missing("appointment_types", sa.Column("reminder_email_hours", sa.Integer(), nullable=True, server_default="24"))
    _add_column_if_missing("appointment_types", sa.Column("reminder_sms_hours", sa.Integer(), nullable=True, server_default="2"))
    for col in [
        "reminder_sms_template_id",
        "reminder_email_template_id",
        "cancellation_email_template_id",
        "booking_email_template_id",
    ]:
        _drop_column_if_exists("appointment_types", col)
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if insp.has_table("appointment_type_reminders"):
        op.drop_table("appointment_type_reminders")
    if insp.has_table("mail_templates"):
        op.drop_index("idx_mail_templates_type", table_name="mail_templates")
        op.drop_index("uq_mail_templates_org_name", table_name="mail_templates")
        op.drop_table("mail_templates")
