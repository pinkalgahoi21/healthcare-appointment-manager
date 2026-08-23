"""Add doctor calendar credentials and Google Calendar sync tracking.

Revision ID: 20260824_06
Revises: 20260824_05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260824_06"
down_revision = "20260824_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    op.create_table(
        "doctor_calendar_credentials",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("doctor_id", uuid, nullable=False, unique=True),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=False),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("calendar_id", sa.String(255), nullable=False, server_default="primary"),
        sa.Column("is_connected", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_doctor_calendar_credentials_id", "doctor_calendar_credentials", ["id"])
    op.create_index("ix_doctor_calendar_credentials_doctor_id", "doctor_calendar_credentials", ["doctor_id"])

    op.create_table(
        "google_calendar_syncs",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("appointment_id", uuid, nullable=False, unique=True),
        sa.Column("doctor_id", uuid, nullable=False),
        sa.Column("google_event_id", sa.String(255), nullable=True),
        sa.Column("calendar_id", sa.String(255), nullable=False, server_default="primary"),
        sa.Column("sync_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_google_calendar_syncs_id", "google_calendar_syncs", ["id"])
    op.create_index("ix_google_calendar_syncs_appointment_id", "google_calendar_syncs", ["appointment_id"])
    op.create_index("ix_google_calendar_syncs_doctor_id", "google_calendar_syncs", ["doctor_id"])
    op.create_index("ix_google_calendar_syncs_google_event_id", "google_calendar_syncs", ["google_event_id"])
    op.create_index("ix_google_calendar_syncs_sync_status", "google_calendar_syncs", ["sync_status"])


def downgrade() -> None:
    op.drop_index("ix_google_calendar_syncs_sync_status", table_name="google_calendar_syncs")
    op.drop_index("ix_google_calendar_syncs_google_event_id", table_name="google_calendar_syncs")
    op.drop_index("ix_google_calendar_syncs_doctor_id", table_name="google_calendar_syncs")
    op.drop_index("ix_google_calendar_syncs_appointment_id", table_name="google_calendar_syncs")
    op.drop_index("ix_google_calendar_syncs_id", table_name="google_calendar_syncs")
    op.drop_table("google_calendar_syncs")

    op.drop_index("ix_doctor_calendar_credentials_doctor_id", table_name="doctor_calendar_credentials")
    op.drop_index("ix_doctor_calendar_credentials_id", table_name="doctor_calendar_credentials")
    op.drop_table("doctor_calendar_credentials")
