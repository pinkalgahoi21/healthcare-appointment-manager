from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class SymptomsRequest(BaseModel):
    symptoms: str = Field(min_length=1, max_length=5000)


class PreVisitSummaryResponse(BaseModel):
    urgency: str
    chief_complaint: str
    suggested_questions: list[str]
    source: str
    disclaimer: str


class PostVisitRequest(BaseModel):
    follow_up_instructions: str = Field(min_length=1, max_length=5000)


class PostVisitSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    appointment_id: UUID
    content: dict[str, Any]
    is_published: bool


class ReminderCreate(BaseModel):
    prescription_id: UUID
    schedule: dict[str, Any]
    next_reminder_at: Optional[datetime] = None


class ReminderResponse(ReminderCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    is_active: bool


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    type: str
    title: str
    body: str
    data: dict[str, Any]
    read_at: Optional[datetime]
    created_at: datetime
