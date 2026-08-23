import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Uuid
from sqlalchemy.orm import relationship
from app.database import Base


class CalendarSyncStatus(str, enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DoctorCalendarCredential(Base):
    """Stores Google OAuth 2.0 credentials for synchronized doctor calendars."""

    __tablename__ = "doctor_calendar_credentials"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    doctor_id = Column(Uuid(as_uuid=True), ForeignKey("doctor_profiles.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    calendar_id = Column(String(255), default="primary", nullable=False)
    is_connected = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    doctor = relationship("DoctorProfile", backref="calendar_credential")


class GoogleCalendarSync(Base):
    """Tracks appointment synchronization state with Google Calendar API."""

    __tablename__ = "google_calendar_syncs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    appointment_id = Column(Uuid(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    doctor_id = Column(Uuid(as_uuid=True), ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    google_event_id = Column(String(255), nullable=True, index=True)
    calendar_id = Column(String(255), default="primary", nullable=False)
    sync_status = Column(String(30), default=CalendarSyncStatus.PENDING.value, nullable=False, index=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    appointment = relationship("Appointment", backref="calendar_sync")
    doctor = relationship("DoctorProfile", backref="calendar_syncs")
