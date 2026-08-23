import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Uuid
from sqlalchemy.orm import relationship
from app.database import Base


class AppointmentStatus(str, enum.Enum):
    HELD = "held"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED_REQUIRED = "rescheduled_required"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    patient_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(Uuid(as_uuid=True), ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    # PostgreSQL enforces uniqueness only for active appointments through the
    # partial index in migration 20260823_02. Historical cancellations must be
    # able to reference the original slot without blocking a later booking.
    slot_id = Column(Uuid(as_uuid=True), ForeignKey("appointment_slots.id", ondelete="RESTRICT"), nullable=False, index=True)

    status = Column(String(30), default=AppointmentStatus.HELD.value, nullable=False, index=True)
    chief_complaint = Column(Text, nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # Timestamps
    booked_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="appointments")
    doctor = relationship("DoctorProfile", backref="appointments")
    slot = relationship("AppointmentSlot", backref="appointments")

    def __repr__(self) -> str:
        return f"<Appointment {self.id} Patient={self.patient_id} Doctor={self.doctor_id} Status={self.status}>"
