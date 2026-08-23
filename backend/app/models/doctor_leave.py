import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import relationship
from app.database import Base


class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    CANCELLED = "cancelled"


class DoctorLeave(Base):
    __tablename__ = "doctor_leave"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    doctor_id = Column(Uuid(as_uuid=True), ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True)
    reason = Column(String(255), nullable=True)
    status = Column(String(20), default=LeaveStatus.APPROVED.value, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    doctor = relationship("DoctorProfile", backref="leaves")

    def __repr__(self) -> str:
        return f"<DoctorLeave Doctor={self.doctor_id} From={self.leave_date} To={self.end_date} Status={self.status}>"
