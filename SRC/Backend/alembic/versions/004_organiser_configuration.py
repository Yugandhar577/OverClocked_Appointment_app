"""organiser configuration fields

Revision ID: 004
Revises: 003
Create Date: 2026-05-02
"""
import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def _add_column_if_missing(table: str, column: sa.Column) -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns(table)}
    if column.name not in cols:
        op.add_column(table, column)


def upgrade() -> None:
    _add_column_if_missing("appointment_types", sa.Column("starts_with", sa.String(length=20), nullable=False, server_default="date"))
    _add_column_if_missing("appointment_types", sa.Column("allow_invitations", sa.Boolean(), nullable=False, server_default=sa.true()))
    _add_column_if_missing("appointment_types", sa.Column("display_pictures", sa.Boolean(), nullable=False, server_default=sa.false()))
    _add_column_if_missing("appointment_types", sa.Column("image_url", sa.Text(), nullable=True))
    _add_column_if_missing("appointment_types", sa.Column("video_url", sa.Text(), nullable=True))
    _add_column_if_missing(
        "appointment_types",
        sa.Column("booking_email_template", sa.String(length=120), nullable=True, server_default="Appointment: Attendee Invitation"),
    )
    _add_column_if_missing(
        "appointment_types",
        sa.Column("cancellation_email_template", sa.String(length=120), nullable=True, server_default="Appointment: Appointment Canceled"),
    )
    _add_column_if_missing("appointment_types", sa.Column("reminder_email_hours", sa.Integer(), nullable=True, server_default="3"))
    _add_column_if_missing("appointment_types", sa.Column("reminder_sms_hours", sa.Integer(), nullable=True, server_default="1"))
    _add_column_if_missing("appointment_types", sa.Column("slot_interval_minutes", sa.Integer(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c["name"] for c in insp.get_columns("appointment_types")}
    for name in [
        "slot_interval_minutes",
        "reminder_sms_hours",
        "reminder_email_hours",
        "cancellation_email_template",
        "booking_email_template",
        "video_url",
        "image_url",
        "display_pictures",
        "allow_invitations",
        "starts_with",
    ]:
        if name in cols:
            op.drop_column("appointment_types", name)
