"""Add notifications and medication reminders.

Revision ID: 20260824_05
Revises: 20260824_04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260824_05"
down_revision = "20260824_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    op.create_table("notifications", sa.Column("id", uuid, primary_key=True), sa.Column("user_id", uuid, nullable=False), sa.Column("type", sa.String(100), nullable=False), sa.Column("title", sa.String(200), nullable=False), sa.Column("body", sa.Text(), nullable=False), sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column("read_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"))
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_table("medication_reminders", sa.Column("id", uuid, primary_key=True), sa.Column("patient_id", uuid, nullable=False), sa.Column("prescription_id", uuid, nullable=False), sa.Column("schedule", postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column("next_reminder_at", sa.DateTime(timezone=True)), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["prescription_id"], ["prescriptions.id"], ondelete="CASCADE"))
    op.create_index("ix_medication_reminders_patient_id", "medication_reminders", ["patient_id"])
    op.create_index("ix_medication_reminders_prescription_id", "medication_reminders", ["prescription_id"])
    op.create_index("ix_medication_reminders_next_reminder_at", "medication_reminders", ["next_reminder_at"])


def downgrade() -> None:
    op.drop_index("ix_medication_reminders_next_reminder_at", table_name="medication_reminders"); op.drop_index("ix_medication_reminders_prescription_id", table_name="medication_reminders"); op.drop_index("ix_medication_reminders_patient_id", table_name="medication_reminders"); op.drop_table("medication_reminders")
    op.drop_index("ix_notifications_user_id", table_name="notifications"); op.drop_table("notifications")
