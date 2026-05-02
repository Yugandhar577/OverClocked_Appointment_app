"""initial appointment schema

Revision ID: 001
Revises:
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa

from SRC.Backend.db.models import Base

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    Base.metadata.create_all(bind=bind)
    op.create_index("idx_users_email", "users", ["email"], unique=True)
    op.create_index(
        "idx_generated_slots_lookup",
        "generated_slots",
        ["appointment_type_id", "start_datetime", "resource_id"],
        postgresql_where=sa.text("is_blocked = FALSE"),
    )
    op.create_index(
        "idx_slots_type_datetime",
        "generated_slots",
        ["appointment_type_id", "start_datetime"],
        postgresql_where=sa.text("is_blocked = FALSE"),
    )
    op.execute("CREATE INDEX idx_appt_customer ON appointments (customer_id, status, created_at DESC)")
    op.create_index("idx_appt_type", "appointments", ["appointment_type_id", "status"])
    op.create_index(
        "idx_otp_user",
        "otp_verifications",
        ["user_id", "otp_type"],
        postgresql_where=sa.text("is_used = FALSE"),
    )
    op.create_index(
        "idx_notif_queued",
        "notifications",
        ["status", "created_at"],
        postgresql_where=sa.text("status = 'queued'"),
    )
    op.create_index("idx_payment_appointment", "payments", ["appointment_id"], unique=True)
    op.create_index("idx_answers_json", "appointment_answers", ["answer_json"], postgresql_using="gin")
    op.execute("CREATE INDEX idx_audit_entity ON audit_logs (entity_type, entity_id, created_at DESC)")


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
