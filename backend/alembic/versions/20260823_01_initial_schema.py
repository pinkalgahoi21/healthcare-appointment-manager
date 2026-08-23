"""Create the initial healthcare appointment schema.

Revision ID: 20260823_01
Revises:
Create Date: 2026-08-23

This migration is intentionally an exact baseline for the existing SQLAlchemy
models.  Future application changes must be introduced in new migrations; the
application must not rely on ``Base.metadata.create_all`` in production.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260823_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)

    op.create_table(
        "users",
        sa.Column("id", uuid, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "doctor_profiles",
        sa.Column("id", uuid, nullable=False),
        sa.Column("user_id", uuid, nullable=False),
        sa.Column("specialization", sa.String(length=100), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("slot_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("consultation_fee", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_doctor_profiles_id", "doctor_profiles", ["id"])
    op.create_index("ix_doctor_profiles_specialization", "doctor_profiles", ["specialization"])

    op.create_table(
        "doctor_working_hours",
        sa.Column("id", uuid, nullable=False),
        sa.Column("doctor_id", uuid, nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doctor_id", "day_of_week", "start_time", name="uq_doctor_day_start_time"),
    )
    op.create_index("ix_doctor_working_hours_id", "doctor_working_hours", ["id"])
    op.create_index("ix_doctor_working_hours_doctor_id", "doctor_working_hours", ["doctor_id"])

    op.create_table(
        "doctor_leave",
        sa.Column("id", uuid, nullable=False),
        sa.Column("doctor_id", uuid, nullable=False),
        sa.Column("leave_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doctor_leave_id", "doctor_leave", ["id"])
    op.create_index("ix_doctor_leave_doctor_id", "doctor_leave", ["doctor_id"])
    op.create_index("ix_doctor_leave_leave_date", "doctor_leave", ["leave_date"])
    op.create_index("ix_doctor_leave_status", "doctor_leave", ["status"])

    op.create_table(
        "appointment_slots",
        sa.Column("id", uuid, nullable=False),
        sa.Column("doctor_id", uuid, nullable=False),
        sa.Column("slot_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("held_by_user_id", uuid, nullable=True),
        sa.Column("held_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["held_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doctor_id", "slot_date", "start_time", name="uq_doctor_slot_datetime"),
    )
    op.create_index("ix_appointment_slots_id", "appointment_slots", ["id"])
    op.create_index("ix_appointment_slots_doctor_id", "appointment_slots", ["doctor_id"])
    op.create_index("ix_appointment_slots_slot_date", "appointment_slots", ["slot_date"])
    op.create_index("ix_appointment_slots_status", "appointment_slots", ["status"])
    op.create_index("ix_appointment_slots_held_by_user_id", "appointment_slots", ["held_by_user_id"])

    op.create_table(
        "appointments",
        sa.Column("id", uuid, nullable=False),
        sa.Column("patient_id", uuid, nullable=False),
        sa.Column("doctor_id", uuid, nullable=False),
        sa.Column("slot_id", uuid, nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("chief_complaint", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("booked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["slot_id"], ["appointment_slots.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slot_id"),
    )
    op.create_index("ix_appointments_id", "appointments", ["id"])
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
    op.create_index("ix_appointments_status", "appointments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_appointments_status", table_name="appointments")
    op.drop_index("ix_appointments_doctor_id", table_name="appointments")
    op.drop_index("ix_appointments_patient_id", table_name="appointments")
    op.drop_index("ix_appointments_id", table_name="appointments")
    op.drop_table("appointments")
    op.drop_index("ix_appointment_slots_held_by_user_id", table_name="appointment_slots")
    op.drop_index("ix_appointment_slots_status", table_name="appointment_slots")
    op.drop_index("ix_appointment_slots_slot_date", table_name="appointment_slots")
    op.drop_index("ix_appointment_slots_doctor_id", table_name="appointment_slots")
    op.drop_index("ix_appointment_slots_id", table_name="appointment_slots")
    op.drop_table("appointment_slots")
    op.drop_index("ix_doctor_leave_status", table_name="doctor_leave")
    op.drop_index("ix_doctor_leave_leave_date", table_name="doctor_leave")
    op.drop_index("ix_doctor_leave_doctor_id", table_name="doctor_leave")
    op.drop_index("ix_doctor_leave_id", table_name="doctor_leave")
    op.drop_table("doctor_leave")
    op.drop_index("ix_doctor_working_hours_doctor_id", table_name="doctor_working_hours")
    op.drop_index("ix_doctor_working_hours_id", table_name="doctor_working_hours")
    op.drop_table("doctor_working_hours")
    op.drop_index("ix_doctor_profiles_specialization", table_name="doctor_profiles")
    op.drop_index("ix_doctor_profiles_id", table_name="doctor_profiles")
    op.drop_table("doctor_profiles")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
