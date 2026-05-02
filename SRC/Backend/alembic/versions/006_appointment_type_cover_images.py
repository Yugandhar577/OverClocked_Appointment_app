"""Add lightweight appointment type image metadata.

Revision ID: 006
Revises: 005
Create Date: 2026-05-02
"""

from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


# Backend note: Applies forward-only database schema changes for this migration revision.
def upgrade() -> None:
    op.execute("ALTER TABLE appointment_types ADD COLUMN IF NOT EXISTS cover_image_compressed TEXT")
    op.execute("ALTER TABLE appointment_types ADD COLUMN IF NOT EXISTS cover_image_cache_key VARCHAR(120)")


# Backend note: Reverses this migration revision when Alembic is asked to step backward.
def downgrade() -> None:
    op.execute("ALTER TABLE appointment_types DROP COLUMN IF EXISTS cover_image_cache_key")
    op.execute("ALTER TABLE appointment_types DROP COLUMN IF EXISTS cover_image_compressed")
