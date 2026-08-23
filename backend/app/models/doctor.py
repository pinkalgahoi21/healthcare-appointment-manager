import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Numeric, Text, Boolean, DateTime, Time, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import relationship
from app.database import Base


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialization = Column(String(100), nullable=False, index=True)
    bio = Column(Text, nullable=True)
    slot_duration_minutes = Column(Integer, default=30, nullable=False)
    consultation_fee = Column(Numeric(10, 2), default=0.00, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", backref="doctor_profile", lazy="joined")
    working_hours = relationship("DoctorWorkingHours", back_populates="doctor", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:
        return f"<DoctorProfile {self.id} ({self.specialization})>"


class DoctorWorkingHours(Base):
    __tablename__ = "doctor_working_hours"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    doctor_id = Column(Uuid(as_uuid=True), ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday .. 6=Sunday or 0=Sunday .. 6=Saturday (0-6)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("doctor_id", "day_of_week", "start_time", name="uq_doctor_day_start_time"),
    )

    doctor = relationship("DoctorProfile", back_populates="working_hours")

    def __repr__(self) -> str:
        return f"<DoctorWorkingHours Day {self.day_of_week}: {self.start_time}-{self.end_time}>"
