import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import relationship
from app.database import Base


class SlotStatus(str, enum.Enum):
    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"
    UNAVAILABLE = "unavailable"


class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    doctor_id = Column(Uuid(as_uuid=True), ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    slot_date = Column(Date, nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default=SlotStatus.AVAILABLE.value, nullable=False, index=True)

    # Hold tracking — null when not held/booked
    held_by_user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    held_until = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("doctor_id", "slot_date", "start_time", name="uq_doctor_slot_datetime"),
    )

    doctor = relationship("DoctorProfile", backref="slots")

    def __repr__(self) -> str:
        return f"<AppointmentSlot {self.id} Doctor={self.doctor_id} Date={self.slot_date} Status={self.status}>"
