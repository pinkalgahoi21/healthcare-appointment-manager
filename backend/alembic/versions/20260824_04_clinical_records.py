"""Add clinical notes, prescriptions, and post-visit summaries.

Revision ID: 20260824_04
Revises: 20260824_03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260824_04"
down_revision = "20260824_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    op.create_table("clinical_notes", sa.Column("id", uuid, primary_key=True), sa.Column("appointment_id", uuid, nullable=False, unique=True), sa.Column("doctor_id", uuid, nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"))
    op.create_index("ix_clinical_notes_appointment_id", "clinical_notes", ["appointment_id"])
    op.create_index("ix_clinical_notes_doctor_id", "clinical_notes", ["doctor_id"])
    op.create_table("prescriptions", sa.Column("id", uuid, primary_key=True), sa.Column("appointment_id", uuid, nullable=False), sa.Column("patient_id", uuid, nullable=False), sa.Column("doctor_id", uuid, nullable=False), sa.Column("medication_name", sa.String(200), nullable=False), sa.Column("dosage", sa.String(100), nullable=False), sa.Column("frequency", sa.String(100), nullable=False), sa.Column("instructions", sa.Text()), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"))
    op.create_index("ix_prescriptions_appointment_id", "prescriptions", ["appointment_id"])
    op.create_index("ix_prescriptions_patient_id", "prescriptions", ["patient_id"])
    op.create_index("ix_prescriptions_doctor_id", "prescriptions", ["doctor_id"])
    op.create_table("post_visit_summaries", sa.Column("id", uuid, primary_key=True), sa.Column("appointment_id", uuid, nullable=False, unique=True), sa.Column("doctor_id", uuid, nullable=False), sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False), sa.Column("is_published", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"))
    op.create_index("ix_post_visit_summaries_appointment_id", "post_visit_summaries", ["appointment_id"])


def downgrade() -> None:
    op.drop_index("ix_post_visit_summaries_appointment_id", table_name="post_visit_summaries"); op.drop_table("post_visit_summaries")
    op.drop_index("ix_prescriptions_doctor_id", table_name="prescriptions"); op.drop_index("ix_prescriptions_patient_id", table_name="prescriptions"); op.drop_index("ix_prescriptions_appointment_id", table_name="prescriptions"); op.drop_table("prescriptions")
    op.drop_index("ix_clinical_notes_doctor_id", table_name="clinical_notes"); op.drop_index("ix_clinical_notes_appointment_id", table_name="clinical_notes"); op.drop_table("clinical_notes")
