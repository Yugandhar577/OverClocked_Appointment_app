"""organizations and user.organization_id

Revision ID: 002
Revises: 001
Create Date: 2026-05-02
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


# Backend note: Applies forward-only database schema changes for this migration revision.
def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if not insp.has_table("organizations"):
        op.create_table(
            "organizations",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("domain", sa.String(length=120), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
            sa.Column("admin_report_notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_organizations_domain", "organizations", ["domain"], unique=True)
    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "organization_id" not in user_cols:
        op.add_column("users", sa.Column("organization_id", UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            "fk_users_organization_id",
            "users",
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="SET NULL",
        )


# Backend note: Reverses this migration revision when Alembic is asked to step backward.
def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    user_cols = {c["name"] for c in insp.get_columns("users")}
    if "organization_id" in user_cols:
        for fk in insp.get_foreign_keys("users"):
            if fk.get("referred_table") == "organizations" and fk.get("constrained_columns") == ["organization_id"]:
                op.drop_constraint(fk["name"], "users", type_="foreignkey")
                break
        op.drop_column("users", "organization_id")
    if insp.has_table("organizations"):
        idx_names = {i["name"] for i in insp.get_indexes("organizations")}
        if "ix_organizations_domain" in idx_names:
            op.drop_index("ix_organizations_domain", table_name="organizations")
        op.drop_table("organizations")
