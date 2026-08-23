from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.appointment import AppointmentStatus
from app.models.slot_hold import SlotHoldStatus
from app.schemas.slot import SlotResponse


class HoldSlotRequest(BaseModel):
    slot_id: UUID
    chief_complaint: Optional[str] = None


class ConfirmAppointmentRequest(BaseModel):
    chief_complaint: Optional[str] = None


class SlotHoldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slot_id: UUID
    patient_id: UUID
    status: SlotHoldStatus
    expires_at: datetime
    created_at: datetime


class CancelAppointmentRequest(BaseModel):
    reason: Optional[str] = None


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    doctor_id: UUID
    slot_id: UUID
    status: AppointmentStatus
    chief_complaint: Optional[str] = None
    cancellation_reason: Optional[str] = None
    booked_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
