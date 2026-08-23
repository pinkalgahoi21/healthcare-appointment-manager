"""Add auditable slot holds and allow rebooking after cancellation.

Revision ID: 20260823_02
Revises: 20260823_01
Create Date: 2026-08-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260823_02"
down_revision = "20260823_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    op.create_table(
        "slot_holds",
        sa.Column("id", uuid, nullable=False),
        sa.Column("slot_id", uuid, nullable=False),
        sa.Column("patient_id", uuid, nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["slot_id"], ["appointment_slots.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_slot_holds_id", "slot_holds", ["id"])
    op.create_index("ix_slot_holds_slot_id", "slot_holds", ["slot_id"])
    op.create_index("ix_slot_holds_patient_id", "slot_holds", ["patient_id"])
    op.create_index("ix_slot_holds_status", "slot_holds", ["status"])
    op.create_index("ix_slot_holds_expires_at", "slot_holds", ["expires_at"])
    op.create_index(
        "uq_slot_holds_active_slot",
        "slot_holds",
        ["slot_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.drop_constraint("appointments_slot_id_key", "appointments", type_="unique")
    op.create_index(
        "uq_appointments_active_slot",
        "appointments",
        ["slot_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('held', 'confirmed')"),
    )
    op.create_index("ix_appointments_slot_id", "appointments", ["slot_id"])


def downgrade() -> None:
    op.drop_index("ix_appointments_slot_id", table_name="appointments")
    op.drop_index("uq_appointments_active_slot", table_name="appointments")
    op.create_unique_constraint("appointments_slot_id_key", "appointments", ["slot_id"])
    op.drop_index("ix_slot_holds_expires_at", table_name="slot_holds")
    op.drop_index("ix_slot_holds_status", table_name="slot_holds")
    op.drop_index("ix_slot_holds_patient_id", table_name="slot_holds")
    op.drop_index("ix_slot_holds_slot_id", table_name="slot_holds")
    op.drop_index("ix_slot_holds_id", table_name="slot_holds")
    op.drop_table("slot_holds")
