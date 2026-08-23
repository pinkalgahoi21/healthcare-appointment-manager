from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from app.models.appointment_slot import SlotStatus


class SlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    slot_date: date
    start_time: datetime
    end_time: datetime
    status: SlotStatus


class DoctorAvailabilityResponse(BaseModel):
    doctor_id: UUID
    date: date
    slot_duration_minutes: int
    is_on_leave: bool = False
    leave_reason: Optional[str] = None
    slots: List[SlotResponse] = []


class SlotGenerateRequest(BaseModel):
    start_date: date
    end_date: Optional[date] = None
