"""advanced usp modules

Revision ID: 003
Revises: 002
Create Date: 2026-05-02
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def _has_table(insp: sa.Inspector, name: str) -> bool:
    return insp.has_table(name)


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if _has_table(insp, "appointments"):
        op.drop_constraint("ck_appointments_status", "appointments", type_="check")
        op.create_check_constraint(
            "ck_appointments_status",
            "appointments",
            "status IN ('pending', 'confirmed', 'cancelled', 'completed', 'rescheduled', 'no_show')",
        )

    if not _has_table(insp, "feature_flag_overrides"):
        op.create_table(
            "feature_flag_overrides",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("flag_key", sa.String(80), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("flag_key", name="uq_feature_flag_overrides_flag_key"),
        )

    if not _has_table(insp, "waitlist_entries"):
        op.create_table(
            "waitlist_entries",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("appointment_type_id", UUID(as_uuid=True), sa.ForeignKey("appointment_types.id"), nullable=False),
            sa.Column("slot_id", UUID(as_uuid=True), sa.ForeignKey("generated_slots.id"), nullable=True),
            sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="waiting"),
            sa.Column("offer_mode", sa.String(20), nullable=False, server_default="sequential"),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("offered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("idx_waitlist_lookup", "waitlist_entries", ["appointment_type_id", "slot_id", "status", "priority"])
        op.create_index("idx_waitlist_customer", "waitlist_entries", ["customer_id", "status"])

    if not _has_table(insp, "booking_cart_quotes"):
        op.create_table(
            "booking_cart_quotes",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("items", JSONB(), nullable=False),
            sa.Column("total_duration_minutes", sa.Integer(), nullable=False),
            sa.Column("total_price", sa.Numeric(10, 2), nullable=True),
            sa.Column("currency", sa.String(5), nullable=False, server_default="INR"),
            sa.Column("status", sa.String(20), nullable=False, server_default="quoted"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if not _has_table(insp, "recurring_series"):
        op.create_table(
            "recurring_series",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("appointment_type_id", UUID(as_uuid=True), sa.ForeignKey("appointment_types.id"), nullable=False),
            sa.Column("recurrence_type", sa.String(20), nullable=False),
            sa.Column("recurrence_config", JSONB(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if not _has_table(insp, "packages"):
        op.create_table(
            "packages",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("name", sa.String(160), nullable=False),
            sa.Column("appointment_type_id", UUID(as_uuid=True), sa.ForeignKey("appointment_types.id"), nullable=True),
            sa.Column("session_count", sa.Integer(), nullable=False),
            sa.Column("price", sa.Numeric(10, 2), nullable=False),
            sa.Column("currency", sa.String(5), nullable=False, server_default="INR"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if not _has_table(insp, "customer_package_balances"):
        op.create_table(
            "customer_package_balances",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("package_id", UUID(as_uuid=True), sa.ForeignKey("packages.id"), nullable=False),
            sa.Column("remaining_sessions", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if not _has_table(insp, "cancellation_policies"):
        op.create_table(
            "cancellation_policies",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("appointment_type_id", UUID(as_uuid=True), sa.ForeignKey("appointment_types.id"), nullable=True),
            sa.Column("name", sa.String(160), nullable=False),
            sa.Column("late_cancel_deadline_minutes", sa.Integer(), nullable=False, server_default="1440"),
            sa.Column("late_cancel_fee", sa.Numeric(10, 2), nullable=True),
            sa.Column("deposit_percent", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    if not _has_table(insp, "pricing_rules"):
        op.create_table(
            "pricing_rules",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("appointment_type_id", UUID(as_uuid=True), sa.ForeignKey("appointment_types.id"), nullable=True),
            sa.Column("name", sa.String(160), nullable=False),
            sa.Column("rule_type", sa.String(40), nullable=False),
            sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
            sa.Column("adjustment_type", sa.String(20), nullable=False, server_default="fixed"),
            sa.Column("adjustment_value", sa.Numeric(10, 2), nullable=False),
            sa.Column("conditions", JSONB(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("idx_pricing_rules_lookup", "pricing_rules", ["appointment_type_id", "is_active", "priority"])

    if not _has_table(insp, "theme_settings"):
        op.create_table(
            "theme_settings",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
            sa.Column("name", sa.String(120), nullable=False, server_default="Odoo Default"),
            sa.Column("settings", JSONB(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("organization_id", "name", name="uq_theme_settings_org_name"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for table in [
        "theme_settings",
        "pricing_rules",
        "cancellation_policies",
        "customer_package_balances",
        "packages",
        "recurring_series",
        "booking_cart_quotes",
        "waitlist_entries",
        "feature_flag_overrides",
    ]:
        if insp.has_table(table):
            op.drop_table(table)

    if insp.has_table("appointments"):
        op.drop_constraint("ck_appointments_status", "appointments", type_="check")
        op.create_check_constraint(
            "ck_appointments_status",
            "appointments",
            "status IN ('pending', 'confirmed', 'cancelled', 'completed', 'rescheduled')",
        )
