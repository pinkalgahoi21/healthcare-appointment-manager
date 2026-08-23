import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import relationship

from app.database import Base


class SlotHoldStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"
    CONVERTED = "converted"


class SlotHold(Base):
    """Auditable, short-lived reservation for an appointment slot."""

    __tablename__ = "slot_holds"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    slot_id = Column(Uuid(as_uuid=True), ForeignKey("appointment_slots.id", ondelete="RESTRICT"), nullable=False, index=True)
    patient_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=SlotHoldStatus.ACTIVE.value, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    slot = relationship("AppointmentSlot", backref="holds")
    patient = relationship("User", backref="slot_holds")
