"""Fix foreign key cascade constraint on appointment_answers.question_id.

Revision ID: 007
Revises: 006
Create Date: 2026-05-03
"""

from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


# Backend note: Applies forward-only database schema changes for this migration revision.
def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE appointment_answers
        DROP CONSTRAINT IF EXISTS appointment_answers_question_id_fkey,
        ADD CONSTRAINT appointment_answers_question_id_fkey
            FOREIGN KEY (question_id)
            REFERENCES appointment_questions(id)
            ON DELETE CASCADE
        """
    )


# Backend note: Reverses this migration revision when Alembic is asked to step backward.
def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE appointment_answers
        DROP CONSTRAINT IF EXISTS appointment_answers_question_id_fkey,
        ADD CONSTRAINT appointment_answers_question_id_fkey
            FOREIGN KEY (question_id)
            REFERENCES appointment_questions(id)
        """
    )
